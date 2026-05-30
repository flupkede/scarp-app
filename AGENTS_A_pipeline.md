# SCARP — Package A: Pipeline (instance 1)

> Run this in its own opencode instance. You own `prep/` and write outputs to
> `data/processed/`. Two other instances run in parallel on `main` (frontend,
> backend) — they touch different folders, so you never conflict.

**Repo:** `C:\WorkArea\AI\scarp` → https://github.com/flupkede/scarp-app (public)
**Branch:** `main`
**Before any `gh` command:** `gh auth switch --user flupkede`

---

## Parallel rules (read first)

- You own **`prep/`** (write) and **`data/processed/`** (write).
- Commit ONLY your folders: `git add prep/ data/processed/ data/raw/MANIFEST.json`.
  **Never `git add -A`.** Never touch root files or `frontend/` or `backend/`.
- `data/raw/` is gitignored — commit only `MANIFEST.json` from it.
- If push is rejected: `git pull --rebase origin main` then push again.
- Commit format: `<type>(prep): <subject>`.
- Heavy steps (download, scoring) MUST run in background:
  `uv run python -u prep/<script>.py > /tmp/<name>.log 2>&1 &` then poll the log
  / output file. Never block the foreground on a 5+ minute run.

---

## Goal

Make `data/processed/` **reproducible** from raw data. The output geojsons exist
in the repo but the scripts that generate them are missing — that's the biggest
gap against the plan. Rebuild the full download + scoring pipeline from the
specs below.

**Specs (already in repo — read them fully before coding):**
- `AGENTS_phase-1.md` — data download (verified URLs, gotchas)
- `AGENTS_phase-2.md` — 90m scoring pipeline (proven config, formula, gates)
- `ADDITION_confidence_layer.md` — confidence band details
- `ADDITION_refinement_and_symbols.md` — two-stage scoring + symbol scheme

---

## ⚠️ DGGS clarification (do not get this wrong)

DGGS has TWO datasets:
- **DGGS susceptibility RASTER** = ❌ **DROPPED**. 88.6% NODATA, misses all
  fjords (Tracy Arm, Lituya Bay, Barry Arm). Replaced by **USGS n10**
  (`n10_ak.tif`, 90m, 0% NODATA, values 0-81). Do NOT use it in scoring.
  Downloading it is optional — skipping is fine.
- **DGGS landslide INVENTORY** (`inventory.geojson`) = ✅ **KEPT**. Merged with
  USFS Tongass + USGS news-CSV into `all_slides_3338` for the **proximity**
  component (W_PROX=0.20) and the confidence layer.

Primary susceptibility = **USGS n10**. Known-slides = DGGS inventory + Tongass
+ news CSV.

---

## A.1 — Download runner `prep/00_download.py`

Per `AGENTS_phase-1.md`. Idempotent: SHA-256 check → skip if file matches
manifest, else download. `httpx.Client` streaming, 60s timeout, follow
redirects, retry with exponential backoff on 504s.

8 dataset categories (~11 GB total):
1. **DGGS inventory** — nested zip (outer zip → inner zip → `.gdb`) →
   `geopandas.read_file` → `data/raw/dggs/inventory.geojson`. Expect 6000+ feats.
2. **USGS n10** susceptibility (~168 MB) — direct S3
   `https://prod-is-usgs-sb-prod-publish.s3.amazonaws.com/65ccea5bd34ef4b119cb3bac/n10_ak.tif`
   → `data/raw/usgs_susc/n10_ak.tif`. PRIMARY.
3. DGGS susceptibility raster — OPTIONAL, skip is fine.
4. **USGS 3DEP DEM tiles** (~63 tiles, ~10.5 GB) — TNM API, 3 bbox queries:
   SE `-138,55,-130,60`; PWS `-150,60,-148,61.5`; Yakutat `-142,59,-138,61.5`.
   Keep latest version per tile, skip tiles <1 MB (corrupt stubs).
5. **OSM** Alaska PBF (~143 MB) — Geofabrik
   `https://download.geofabrik.de/north-america/us/alaska-latest.osm.pbf`.
6. **AEC stations** — FDSN text
   `https://service.iris.edu/fdsnws/station/1/query?network=AK&format=text`
   → parse `|`-separated → GeoJSON Points.
7. **USFS Tongass** slides — ArcGIS MapServer, paginate (`resultOffset`, 1000/req)
   → `data/raw/usfs/tongass_slides.geojson`.
8. **USGS news CSV** (162 rows) — ScienceBase item `67d45f8ad34e1acf3979d7ab`
   → `data/raw/usgs/seak_news_slides.csv`.

Write `data/raw/MANIFEST.json` (per-entry: url, path, sha256, size_bytes,
downloaded_at). One manifest entry per DEM tile.

**Run in background** (DEM is the bottleneck, ~15-20 min first run).

---

## A.2 — Processing scripts (sequential, after download)

Per `AGENTS_phase-2.md` §3. Proven config (do not deviate):
EPSG:3338, CELL_SIZE=90, weighted-additive weights summing to 1.0
(susc .25, fjord_wall .25, proximity .20, slope .10, exposure .10, gap .10),
N10_NODATA=2147483647, bounds `(-250000, 300000, 1226203, 1559983)`.

- **`10_normalize.py`** — reproject all vectors to EPSG:3338; merge
  inventory + Tongass + news → `intermediate/all_slides_3338.geojson`.
  `shapely.validation.make_valid` on geoms.
- **`20_slope.py`** — per-DEM-tile slope (numpy gradient method, NOT richdem),
  reclassify >25°=1, vectorize with `rasterio.features.shapes`, simplify 50m
  → `intermediate/steep_slopes_3338.geojson`. Process tiles one at a time. Skip
  <1 MB tiles.
- **`30_exposure.py`** — **osmium** bindings (NOT pyrosm — Windows wheel issues).
  buildings + roads (trunk/primary/secondary/tertiary/residential) + tourism
  POIs → 500m raster `exposure = log(1+b) + 2*log(1+roads_km) + 5*has_tourism`,
  `uniform_filter(size=41)` smooth → `intermediate/exposure_3338.tif`.
- **`40_monitoring_mask.py`** — ramped coverage `clip(1 - dist_m/15000, 0, 1)`
  → `intermediate/coverage_mask_3338.tif`.
- **`45_confidence.py`** — count valid input layers per cell / 5.0 → 3 bands
  (low<0.4, medium 0.4-0.7, high>0.7), dissolve → `data/processed/confidence.geojson`.
  Print: "X% high-confidence, Y% data-limited; known sites in data-limited
  areas: Lituya Bay, Taan Fiord, Icy Bay".
- **`50_score_zones.py`** — 90m hybrid. NEAREST resampling for n10 (NOT average).
  `fjord_wall = clip(relief/500,0,1) * clip(1-coast_dist/5000,0,1)`,
  `suscept_norm = clip(n10/81,0,1)`, then weighted-additive score. Mask
  ocean/nodata. Candidate selection: 90th-pct threshold → tiled local maxima
  (45-cell ≈ 4km) → coastal filter (drop >15km from coast) → sort → cap 120 →
  regional fairness quotas (8 regions in phase-2 §2). Outputs to
  `data/processed/`: `zones.geojson`, `candidates_influence.geojson`,
  `zones_top10.json`, `slides.geojson`, `stations.geojson`, `confidence.geojson`,
  `meta.json`.

**Run scoring in background** (~13 min, DEM resampling bottleneck). Poll for
output files.

---

## A.3 — Validation gates (phase-2 §4)

- **GATE A:** candidate within — Seward <5km, Lituya Bay <10km, Surprise Inlet
  <15km, Glacier Bay <10km, Taan Fiord <20km, Barry Arm <35km, Tracy Arm <25km.
- **GATE B:** top 10 NOT all Anchorage suburbs (lat >61.2°N) — PWS fjords win.
- **GATE C:** score std > 0.05 (meaningful spread, not flat).

**Expected data limitations (NOT bugs):** Tracy Arm ranks low (2025 event not in
any inventory, proximity≈0.12). Barry Arm suppressed (monitored, station 1.3km).
Western AK data-limited.

---

## A.4 — Dead ends to avoid (phase-2 §9, all proven wrong)

DGGS-raster-as-primary · multiplicative formula · AVERAGE resampling · binary
10km buffer · sort-without-spatial-dedup · 5km coastal filter. Do not repeat.

---

## A.5 — Commit

```
cd C:/WorkArea/AI/scarp
git add prep/ data/processed/ data/raw/MANIFEST.json
git commit -m "feat(prep): reproducible download + 90m scoring pipeline"
gh auth switch --user flupkede
git push origin main
```

When done, report: which scripts created, GATE A/B/C results, and whether
`confidence.geojson` was generated.
