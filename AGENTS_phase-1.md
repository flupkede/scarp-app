# Phase 1 — Data acquisition (refined, verified URLs)

**Status:** 🟢 Ready to execute
**Spec:** Section 5 of `AGENTS.md`
**Owner:** OpenCode (`@ZAI Coder` for bulk, `@Reviewer` before commit)
**Working directory:** `C:\WorkArea\AI\scarp\`

---

## 1. Goal

Download all 8 dataset categories to `data/raw/` with SHA-256 verification and an idempotent runner. Total raw data ~11 GB.

This phase has been executed before — all URLs below are **verified working** (May 2026).

## 2. Verified working endpoints

### 2.1 DGGS Landslide Inventory

**Source:** Alaska DGGS DDS 23 (Sept 2025 release)
**URL:** `https://dggs.alaska.gov/webpubs/data/dds023_landslide_inventory_db_02_Sep_2025.zip`
**Output:** `data/raw/dggs/inventory.geojson`
**Size:** ~21 MB after conversion

**Known gotcha — nested zip:**
The downloaded zip contains another zip inside. Extract the outer, find the inner `.zip`, extract that too. Look for `.gdb` directory (file geodatabase), fall back to `.gpkg` or `.shp`. Read with `geopandas.read_file()` and write to GeoJSON.

```
download zip → extract → find inner zip → extract inner → find .gdb → read with geopandas → write GeoJSON
```

Expected feature count: 6000+ landslides.

### 2.2 USGS n10 Susceptibility Raster (PRIMARY)

**Source:** USGS n10 — Mirus et al. 2024, "A 10-m resolution landslide susceptibility map of Alaska"
**Paper:** DOI: 10.1029/2024AV001214
**Data DOI:** 10.5066/P13KAGU3
**ScienceBase item:** `65ccea5bd34ef4b119cb3bac`
**Direct S3 URL:** `https://prod-is-usgs-sb-prod-publish.s3.amazonaws.com/65ccea5bd34ef4b119cb3bac/n10_ak.tif`
**Output:** `data/raw/usgs_susc/n10_ak.tif`
**Size:** ~168 MB

**Why this replaces DGGS susceptibility:**
- USGS n10 covers 100% of Alaska land area (0% NODATA), 90m resolution, values 0-81 (count of susceptible 10m cells per 90m cell)
- DGGS MapServer raster has 88.6% NODATA — entire fjord coastlines are masked as water, missing Tracy Arm, Lituya Bay, Taan Fiord, Barry Arm
- At Barry Arm: DGGS=6/10, USGS n10=79/81 (98%)
- At Tracy Arm: DGGS=NODATA, USGS n10=81/81 (100%)

**Format:** GeoTIFF, EPSG:3338, int32, nodata=2147483647 (2^31 - 1)

### 2.3 DGGS Susceptibility Raster (DEPRECATED — kept as fallback only)

**Source:** DGGS PIR 2025-3 — Deep-Seated Landslide Susceptibility
**MapServer:** `https://geoportal.dggs.dnr.alaska.gov/arcgis/rest/services/Alaska_Deep_Seated_Landslide_Susceptibility/MapServer`
**Output:** `data/raw/dggs/susceptibility.tif`
**Size:** ~67 MB

No longer used in scoring pipeline. Download is optional — USGS n10 is the primary source.

**Known gotcha — MapServer returns PNG, must georeference to GeoTIFF:**

1. GET `{MapServer}?f=json` → extract `fullExtent` (in EPSG:3338)
2. GET `{MapServer}/export?bbox={xmin},{ymin},{xmax},{ymax}&bboxSR=3338&imageSR=3338&size=4096,4096&format=png&f=image` → returns PNG
3. Use rasterio to wrap the PNG as a GeoTIFF with the extent as the geotransform and EPSG:3338 as CRS

### 2.4 USGS 3DEP DEM tiles (extended coverage)

**Source:** USGS TNM (The National Map) S3 bucket
**Query API:** `https://tnmaccess.nationalmap.gov/api/v1/products`
**Direct S3 base:** `https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/historical/`

**Two bbox queries required:**

1. **Southeast Alaska:** `bbox=-138,55,-130,60` — ~26 tiles
2. **Southcentral/Prince William Sound:** `bbox=-150,60,-148,61.5` — ~8 tiles
3. **Yakutat/Glacier Bay:** `bbox=-142,59,-138,61.5` — ~14 tiles

**Query parameters:**
- `datasets`: "National Elevation Dataset (NED) 1/3 arc-second"
- Filter: keep only tiles in bounds, skip tiles <1 MB (incomplete stubs)

**Expected output:** ~63 tiles, total ~10.5 GB. Tile naming pattern: `USGS_13_n{lat}w{lon}_{YYYYMMDD}.tif`

**Why extended:** The scoring pipeline covers SE Alaska + Southcentral AK (Prince William Sound, Turnagain Arm, Kenai Peninsula). The original SE-only bbox excluded DEM data for Barry Arm, Icy Bay, and Anchorage area. Extended coverage ensures slope/fjord_wall signals work statewide.

**Known gotchas:**
- Some tiles have both historical (2016) and current (2022/2025) versions — keep the latest
- 14/40 tiles in the original bbox were corrupt stubs (~64KB) from incomplete downloads — skip via size check (>1 MB minimum)
- TNM API returns intermittent 504s — retry with exponential backoff

### 2.4 OSM Alaska extract

**Source:** Geofabrik direct PBF
**URL:** `https://download.geofabrik.de/north-america/us/alaska-latest.osm.pbf`
**Output:** `data/raw/osm/alaska-latest.osm.pbf`
**Size:** ~143 MB

No gotchas. Direct download.

### 2.5 Alaska Earthquake Center stations (FDSN)

**URL:** `https://service.iris.edu/fdsnws/station/1/query?network=AK&format=text`
**Output:** `data/raw/stations/aec_stations.geojson`
**Size:** ~90 KB

**Conversion:** FDSN returns a `|`-separated text file (Net|Sta|Lat|Lon|Elev|...). Parse to GeoJSON Points with the station code as `properties.code`.

### 2.6 USFS Tongass landslide areas

**Source:** USDA Forest Service ArcGIS
**MapServer:** `https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_TongassLandslide_01/MapServer/1`
**Query URL:** `{MapServer}/query?where=1=1&outFields=*&f=geojson&outSR=4326`
**Output:** `data/raw/usfs/tongass_slides.geojson`
**Size:** ~47 MB

Paginate if needed (1000 features/request, `resultOffset` parameter). Total ~2000-3000 features.

### 2.7 USGS news-reported slides CSV

**Source:** USGS ScienceBase item
**Item URL:** `https://www.sciencebase.gov/catalog/item/67d45f8ad34e1acf3979d7ab`
**Direct file URL:** `https://www.sciencebase.gov/catalog/file/get/67d45f8ad34e1acf3979d7ab?name=SEAK_News_Reported_Landslides.csv`
**Output:** `data/raw/usgs/seak_news_slides.csv`
**Size:** ~80 KB
**Validation:** 162 rows

## 3. The runner

`prep/00_download.py` should:

1. Load existing `data/raw/MANIFEST.json` if present
2. For each of the 8 datasets:
   - Check if local file exists and SHA-256 matches manifest → skip
   - Else download fresh
   - Update manifest entry
3. Save updated `data/raw/MANIFEST.json` at end

**Manifest schema per entry:**
```json
{
  "dataset_name": {
    "url": "https://...",
    "path": "data/raw/.../file.ext",
    "sha256": "abc123...",
    "size_bytes": 12345678,
    "downloaded_at": "2026-05-30T10:00:00Z"
  }
}
```

For DEM tiles, use one manifest entry per tile (key format: `dem_tile_USGS_13_n{lat}w{lon}_{date}.tif`).

**Use `httpx.Client` with streaming and progress output.** Set 60s timeout. Follow redirects.

## 4. Validation after run

```powershell
cd C:\WorkArea\AI\scarp
uv run python -c "from pathlib import Path; m = __import__('json').load(open('data/raw/MANIFEST.json')); print(f'{len(m)} entries, {sum(e[\"size_bytes\"] for e in m.values()) / 1e9:.1f} GB')"
```

Expected: ~70 entries, ~11 GB.

## 5. Definition of Done

- [ ] `data/raw/MANIFEST.json` exists with ~70 entries
- [ ] All 8 dataset categories present
- [ ] DGGS inventory: >5000 features
- [ ] USGS n10 susceptibility raster exists (~168 MB)
- [ ] DEM tiles: 50+ files in `data/raw/dem/`
- [ ] Total raw size: 10-12 GB
- [ ] Re-running `prep/00_download.py` completes in <10s (all cached)

## 6. Time estimate

| Step | Estimate |
|---|---|
| Code generation | 5 min (opencode + spec above) |
| First download run | 15-20 min (DEM is the bottleneck) |
| Validation | 2 min |
| **Total** | **~25 min** |

## 7. Risks

| Risk | Mitigation |
|---|---|
| DGGS zip URL changes after Sept 2025 release | Fall back to scraping publication page `https://dggs.alaska.gov/pubs/id/31697` for download link |
| ScienceBase item ID changes | Hardcode the verified ID `67d45f8ad34e1acf3979d7ab` — if 404, search ScienceBase API for `SEAK_News_Reported_Landslides` |
| TNM API rate limits | Sequential downloads with 1s delay between tiles |
| USFS MapServer paginates differently | Always paginate explicitly with `resultOffset`, never assume all features in one request |
| DEM total size too big for available disk | All tiles ~5 GB — verify free space before starting |

## 8. After Phase 1 — handoff to Phase 2

Phase 2 expects:
- `data/raw/usgs_susc/n10_ak.tif` — USGS n10 susceptibility, EPSG:3338, 90m, values 0-81, nodata=2147483647
- `data/raw/dggs/inventory.geojson` — points/polygons of known slides
- `data/raw/dem/*.tif` — ~63 tiles, EPSG:4269 (NAD83), covering SE + Southcentral AK
- `data/raw/osm/alaska-latest.osm.pbf` — full Alaska extract
- `data/raw/stations/aec_stations.geojson` — points
- `data/raw/usfs/tongass_slides.geojson` — polygons
- `data/raw/usgs/seak_news_slides.csv` — 162 rows with lat/lon

**Bounds for Phase 2 (EPSG:3338):** (-250000, 300000, 1226203, 1559983)
This covers SE Alaska through Anchorage/Kenai/PWS, from Lituya Bay to Turnagain Arm.

---

*This phase was successfully executed prior to event day. URLs and gotchas above are battle-tested.*
