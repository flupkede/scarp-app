# Phase 2 — Spatial processing (90m scoring pipeline)

**Status:** 🟢 Ready to execute
**Spec:** Section 6 of `AGENTS.md`
**Owner:** OpenCode (`@build` agent)
**Working directory:** `C:\WorkArea\AI\scarp\` (or fresh repo on the day)

---

## 1. Goal

From raw data in `data/raw/` produce ranked candidate sensor locations in `data/processed/zones.geojson` — up to 120 point candidates with explainable scoring, regional fairness, and per-component breakdowns.

Also produce a **data confidence raster** that distinguishes "low risk" from "unknown risk" — the project's honest second finding.

## 2. Proven configuration

```python
TARGET_CRS = "EPSG:3338"          # Alaska Albers Equal Area
CELL_SIZE = 90                     # meters — analysis grid (matches USGS n10 source)
COARSE_CELL_SIZE = 500             # meters — for distance-based layers (proximity, coverage, coast, exposure)
RELIEF_SIZE = 11                   # cells at 90m ≈ 1km window for local relief
SLOPE_THRESHOLD = 25.0             # degrees — "steep" cutoff
SIMPLIFY_TOLERANCE = 50            # meters in EPSG:3338
PROXIMITY_DECAY_KM = 5.0           # exp(-distance/5km) for inventory proximity
COVERAGE_BUFFER_M = 15_000         # 15km ramp from 1.0 at station to 0.0 at edge
COASTAL_MAX_DIST_KM = 15.0         # candidates >15km from coast are dropped
NEIGHBORHOOD_SIZE = 45             # cells at 90m ≈ 4km minimum candidate spacing
MAX_CANDIDATES = 120               # cap on output candidates
INFLUENCE_RADIUS_M = 3000          # 3km influence circle per candidate

# Southeast + Southcentral Alaska, EPSG:3338
SE_BOUNDS_3338 = (-250000, 300000, 1226203, 1559983)

# USGS n10 nodata sentinel
N10_NODATA = 2147483647

# Weighted-additive scoring weights (must sum to 1.0)
W_SUSC = 0.25   # susceptibility
W_FJORD = 0.25  # fjord wall (relief × water proximity)
W_PROX = 0.20   # proximity to known slides
W_SLOPE = 0.10  # steep slope presence
W_EXPO = 0.10   # human exposure
W_GAP = 0.10    # monitoring gap (1 - coverage)

# Tiled processing (memory safety)
TILE_SIZE = 2000   # cells per tile
TILE_OVERLAP = 60  # cells overlap for edge-safe local maxima

# Regional fairness — 8-10 coastal regions for quota allocation
REGIONS = [
    {"name": "Anchorage/Kenai/PWS", "bounds_lon": (-150, -147), "bounds_lat": (60, 61.5)},
    {"name": "Columbia Glacier", "bounds_lon": (-148, -146), "bounds_lat": (60.5, 61.5)},
    {"name": "Yakutat/Glacier Bay", "bounds_lon": (-142, -137), "bounds_lat": (58, 60.5)},
    {"name": "Haines/Skagway", "bounds_lon": (-137, -135), "bounds_lat": (59, 60)},
    {"name": "Tracy Arm/SE fjords", "bounds_lon": (-135, -133), "bounds_lat": (57, 58.5)},
    {"name": "Juneau corridor", "bounds_lon": (-136, -133.5), "bounds_lat": (58, 59)},
    {"name": "Sitka/Baranof", "bounds_lon": (-136, -134), "bounds_lat": (56.5, 58)},
    {"name": "Ketchikan/SE tip", "bounds_lon": (-134, -130), "bounds_lat": (55, 57)},
]
```

**Expected outputs:**
- ~120 point candidates with 4km minimum spacing, regional fairness quotas
- Score range ~0.57-1.00 with meaningful discrimination (std ~0.09)
- Generation runs in ~9 min on a 32 GB RAM machine (DEM resampling is the bottleneck)
- Peak memory: ~8.5 GB for the full 90m grid

**Memory fallback:** If 90m grid exceeds available RAM, fall back to 100m or 150m. At 150m: 82M cells, ~3.1 GB — works on 16 GB machines. Adjust NEIGHBORHOOD_SIZE proportionally.

## 3. Pipeline scripts

Six scripts, run sequentially.

### 3.1 `prep/10_normalize.py`

**Input:** all raw vector datasets in their native CRS
**Output:** all reprojected to EPSG:3338 in `data/processed/intermediate/`

Reproject:
- `dggs/inventory.geojson` → `intermediate/inventory_3338.geojson`
- `usfs/tongass_slides.geojson` → `intermediate/tongass_3338.geojson`
- `stations/aec_stations.geojson` → `intermediate/stations_3338.geojson`
- Merge inventory + Tongass + USGS news CSV into `intermediate/all_slides_3338.geojson` (unified slide reference for proximity)

Clean invalid geoms with `shapely.validation.make_valid`.

### 3.2 `prep/20_slope.py`

**Input:** `data/raw/dem/*.tif` (~63 tiles, EPSG:4269)
**Output:** `data/processed/intermediate/steep_slopes_3338.geojson`

Process each DEM tile independently — do NOT load all into memory:

```
for each .tif in data/raw/dem/:
    skip if < 1MB (corrupt stubs from incomplete downloads)
    reproject single tile to EPSG:3338 at 100m resolution → MemoryFile
    compute slope in degrees (numpy gradient method)
    reclassify cells > 25° to 1, else 0
    vectorize the >25° mask with rasterio.features.shapes()
    simplify polygons (tolerance=50m)
    append to result list

write combined GeoJSON
```

**Method:**
```python
dy, dx = np.gradient(elevation, cellsize)
slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
slope_deg = np.degrees(slope_rad)
```

### 3.3 `prep/30_exposure.py`

**Input:** `data/raw/osm/alaska-latest.osm.pbf`
**Output:** `data/processed/intermediate/exposure_3338.tif` (500m grid)

**Use `osmium` Python bindings — NOT pyrosm.** Pyrosm has Windows wheel issues on Python 3.12+.

Extract via `osmium.SimpleHandler`:
- `building=*` → buildings
- `highway in [trunk, primary, secondary, tertiary, residential]` → roads
- `tourism=*` OR `amenity=ferry_terminal` OR `aeroway=aerodrome` → tourism POIs

Use USGS n10 bounds to determine grid extent (wider than DGGS susceptibility).

Per cell on the 500m grid:
```
exposure_value = log(1 + buildings_in_cell)
               + 2 * log(1 + roads_length_km_in_cell)
               + 5 * (has_tourism_poi_in_cell ? 1 : 0)
```

Radius-smooth with `uniform_filter(size=41)` × kernel_size² to spread sparse exposure over ~10km.

### 3.4 `prep/40_monitoring_mask.py`

**Input:** `data/processed/intermediate/stations_3338.geojson`
**Output:** `data/processed/intermediate/coverage_mask_3338.tif` (500m grid)

Ramped coverage (NOT binary):
```
load stations
for each cell, distance to nearest station in meters
coverage = clip(1.0 - dist_m / 15000, 0, 1)
```

Uses 15km ramp: 1.0 at station, linear decay to 0.0 at 15km. This penalizes dense AEC clusters less than a binary 10km buffer.

### 3.5 `prep/45_confidence.py` (NEW — data confidence layer)

**Input:** component validity masks from scoring pipeline
**Output:** `data/processed/confidence.geojson` (3-band polygon overlay)

For each analysis cell, count how many input layers have valid data:

```python
layers_present = (
    (susceptibility > 0) & (susceptibility != N10_NODATA)  # USGS n10 has a real value
  + dem_present                                             # DEM tile covers this cell
  + slide_inventory_within_25km                             # at least one inventory feature nearby
  + osm_data_present_within_10km                            # any OSM features at all
  + coastline_data_present                                  # coastline geometry exists
)
confidence = layers_present / 5.0   # 0.0 = blind, 1.0 = all inputs present
```

Polygonize into 3 bands and dissolve:
- **low** (< 0.4): "data-limited, treat scores as provisional"
- **medium** (0.4–0.7): partial data
- **high** (> 0.7): "well-covered, scores are trustworthy"

Print honest summary: "X% of analysis area is high-confidence; Y% is data-limited. Known sites in data-limited areas: [Lituya Bay, Taan Fiord, Icy Bay]."

**Pitch this enables:**
> "The red points are where to look. The grey is where we can't yet — including Lituya Bay. That grey isn't safety. It's the gap in public data."

### 3.6 `prep/50_score_zones.py` (90m scoring pipeline)

**Input:** USGS n10 susceptibility + DEM tiles + all intermediate layers
**Output:** `data/processed/zones.geojson` + `candidates_influence.geojson` + `zones_top10.json` + `meta.json`

**Architecture — hybrid fine/coarse approach:**

Fine-resolution (90m) layers — computed on the full grid:
1. **n10 susceptibility**: resample with `Resampling.nearest` (preserves source values, no dilution at fjord edges)
2. **DEM + relief**: resample tiles to 90m, compute local relief (11-cell window ≈ 1km)
3. **Steep slopes**: rasterize steep polygon GeoJSON to 90m binary mask

Coarse-resolution (500m, upsampled to 90m via bilinear) layers:
4. **Slide proximity**: `exp(-distance_km / 5.0)` from `all_slides_3338`
5. **Coast distance**: distance transform from coastline linestrings
6. **Coverage**: ramped 0-1 from station buffers
7. **Exposure**: radius-smoothed OSM features

**Scoring formula:**
```python
fjord_wall = np.clip(relief / 500.0, 0, 1) * np.clip(1.0 - coast_dist_m / 5000.0, 0, 1)
fjord_wall[~dem_filled] = 0

suscept_norm = np.clip(n10_value / 81.0, 0, 1)

score = (0.25 * suscept_norm
       + 0.25 * fjord_wall
       + 0.20 * proximity
       + 0.10 * slope
       + 0.10 * exposure
       + 0.10 * (1.0 - coverage))
score[~valid] = 0  # mask ocean/nodata
```

**Memory management:**
- Full 90m grid: 16,402×13,999 = 229.6M cells, ~8.5 GB for 10 float32 arrays
- Strategy: compute fine layers first, free DEM after relief computation, compute coarse layers on 500m grid and upsample
- For component reporting: double-load (reload source rasters for just the 50-120 top candidate cells after scoring)
- Tiled local maxima: 2000×2000 tiles with 56-cell overlap

**Candidate selection:**
1. 90th percentile threshold on scored grid
2. Tiled local maxima (45-cell = 4km neighborhood)
3. Coastal filter: drop candidates >15km from coast
4. Sort by score, cap at 120
5. Regional fairness: group candidates into 8-10 coastal regions, enforce per-region quota proportional to region's coastline length

**Output file structure:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {"type": "Point", "coordinates": [-149.703, 60.951]},
      "properties": {
        "id": "site-001",
        "rank": 1,
        "score": 0.9996,
        "influence_radius_km": 3,
        "components": {
          "susceptibility": 1.000,
          "fjord_wall": 1.000,
          "slope_factor": 1.0,
          "proximity": 0.998,
          "exposure": 1.000,
          "coverage": 0.00,
          "coast_dist_km": 0.5
        }
      }
    }
  ]
}
```

Also write `candidates_influence.geojson` (3km buffer circles around each candidate, EPSG:4326) and `meta.json`.

## 4. Sanity check after run

Check these gates:

**GATE A — Known site coverage:** Each of these known tsunamigenic sites should have a candidate within reasonable distance:

| Site | Lat | Lon | Expected distance |
|---|---|---|---|
| Seward/Resurrection Bay | 60.10 | -149.44 | <5km |
| Glacier Bay | 58.75 | -136.50 | <10km |
| Surprise Inlet | 60.13 | -148.84 | <15km |
| Lituya Bay | 58.66 | -137.57 | <10km |
| Taan Fiord | 60.14 | -141.22 | <20km |
| Barry Arm | 61.13 | -148.18 | <35km |
| Tracy Arm | 57.80 | -133.55 | <25km |

**GATE B — Anchorage suppression:** Top 10 should NOT all be in Anchorage suburbs (lat >61.2°N). PWS fjord sites should dominate.

**GATE C — Score discrimination:** Score std should be >0.05 (not flat). Top-10 should have meaningful range (not all 0.99).

**Known data limitations (expected, not bugs):**
- Tracy Arm: ranks low because the 2025 event is NOT in any inventory. Proximity=0.12. This is a data gap, not a formula bug.
- Barry Arm: suppressed by existing monitoring coverage (station 1.3km away). Correct behavior — it IS monitored.
- Western AK (Icy Bay, etc.): sparse OSM, few documented slides → low exposure + proximity. Data-limited.

## 5. Definition of Done

- [ ] All 6 prep scripts run end-to-end without errors
- [ ] `data/processed/zones.geojson` exists with ~120 point features
- [ ] Score range has meaningful spread (std > 0.05)
- [ ] GATE A: Seward <5km, Lituya Bay <10km, Surprise Inlet <15km
- [ ] GATE B: top 10 not all Anchorage suburbs
- [ ] `data/processed/confidence.geojson` exists with 3 bands
- [ ] All processed outputs committed to git

## 6. Time estimate

| Step | Estimate |
|---|---|
| `10_normalize.py` | 30s |
| `20_slope.py` | 2 min (63 DEM tiles) |
| `30_exposure.py` | 1 min (OSM parse) |
| `40_monitoring_mask.py` | 5s |
| `45_confidence.py` | 30s |
| `50_score_zones.py` | 9 min (DEM resampling bottleneck) |
| **Total pipeline** | **~13 min** |
| Code generation (opencode) | 20 min |
| Debugging + sanity check | 20 min |
| **Total phase** | **~55 min** |

## 7. Risks

| Risk | Mitigation |
|---|---|
| 90m grid exceeds RAM | Fall back to 150m (3.1 GB); adjust NEIGHBORHOOD_SIZE proportionally |
| richdem won't install on Python 3.12 Windows | Use numpy gradient method (see 3.2) |
| pyrosm fails to install | Use osmium Python bindings (`uv add osmium`) |
| DEM tiles corrupt/incomplete | Skip tiles <1 MB; retry download |
| Score too flat (std <0.05) | Susceptibility has 29% cells at 1.0 — use greedy spatial dedup with regional fairness to break ties |
| Sitka overclustering | Regional fairness quotas prevent any single region from dominating |
| Ocean cells leak into candidates | Mask via `valid = (suscept != NODATA) & (suscept > 0)` |

## 8. Handoff to Phase 3

Phase 3 backend reads:
- `data/processed/zones.geojson` — point candidates (EPSG:4326)
- `data/processed/candidates_influence.geojson` — 3km influence circles (EPSG:4326)
- `data/processed/zones_top10.json` — slim sidebar data
- `data/processed/slides.geojson` — known slides map layer (export from `all_slides_3338` reprojected to EPSG:4326)
- `data/processed/stations.geojson` — monitoring stations layer (export from stations_3338 to EPSG:4326)
- `data/processed/confidence.geojson` — data confidence overlay (3 bands)
- `data/processed/meta.json` — generation metadata

Ensure all 7 files exist before Phase 3 starts.

## 9. Dead ends to avoid (lessons from dev)

These were tried and failed during development. Do NOT repeat:

- **DGGS susceptibility as primary source**: 88.6% NODATA, missing all fjords. Use USGS n10 instead.
- **Multiplicative scoring formula** (`susc × (1+slope) × ...`): massive plateaus at susc=1.0, no discrimination. Use weighted-additive.
- **500m AVERAGE resampling for susceptibility**: dilutes fjord-edge values (Barry Arm: 79→45, 43% loss). Use NEAREST.
- **Binary 10km coverage buffer**: over-penalizes dense AEC clusters. Use 15km linear ramp.
- **Sort-and-cap without spatial dedup**: identical scores cluster (Sitka 8-pack). Use greedy NMS.
- **Simple sort + top-50**: geographic clustering (19 Juneau/Sitka, 0 elsewhere). Use regional fairness quotas.
- **5km coastal filter**: too aggressive for fjord geometry (kills valid fjord-head candidates). Use 15km.

---

*This phase was executed multiple times during development. All values above are proven working. The 90m full-grid approach with regional fairness is the production choice.*
