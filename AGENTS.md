# Scarp — Project Plan

> *A scarp is the steep face left behind when ground gives way. We're mapping where the next one might appear.*

**Repo:** github.com/flupkede/scarp (public, MIT)
**Owner:** Filip (architect + reviewer), OpenCode (executor)
**Language:** English (code, comments, docs)

---

## 0. Story & rationale (DO NOT SKIP — context for the executor agent)

Bretwood "Hig" Higman is an independent PhD geologist in Seldovia, Alaska. He has spent the past decade documenting tsunamigenic landslides in Alaska's fjords — deep-seated bedrock slides that, when they fail catastrophically, generate megatsunamis. In 1958, a slide in Lituya Bay produced the highest wave ever recorded on Earth (1,720 ft runup). In 2015 the Taan Fiord slide ran water 600 ft up a slope and stripped forest from eight square miles. In 2024-2025, slides in Surprise Inlet, Kenai Fjords, and Tracy Arm all generated tsunamis — none were on any state or federal watchlist.

Hig's key insight, since the Barry Arm discovery in 2020 that triggered the U.S. National Landslide Preparedness Act: **nobody is systematically looking for the next one.** Tsunamigenic landslides in Alaska have increased roughly tenfold over the past decade as glacial de-buttressing, permafrost thaw, and intensified rainfall combine.

Hig builds his own $300 monitoring sensors in mason jars and installs them by hand. He works alone or with one or two helpers. He cannot be everywhere.

**This project builds the tool that helps Hig (and others like him) decide where to place the next sensor.** It is not a landslide detector. Detection already exists (NASA LHASA, TerraTrack, USGS LASER). What does not exist is a **prioritization tool** that combines:
- Susceptibility (steep slopes near retreating glaciers in weak rock)
- Exposure (people, roads, tourism, marine traffic)
- Coverage gap (where is monitoring currently absent?)

Output: a ranked map of "next sensor goes here" zones, with explainable scoring.

**Pitch in one sentence:** "Hig has $300 mason jar sensors and no map of where to put them next. We built it."

Source article: *Lessons of a landslide detective* by Christian Elliott, National Geographic, June 2026 issue (published online 15 May 2026).

---

## 1. Tech stack — locked in

| Layer | Choice | Why |
|---|---|---|
| Backend language | Python 3.12 (pinned) | Geo wheels not yet available for 3.14 on PyPI |
| Package manager | `uv` | Fast, lockfile, system Python stays 3.14 |
| Geo processing | GeoPandas 1.1.3, rasterio 1.5.0, shapely 2.1.x, pyproj 3.7+ | Latest stable, all have 3.12 wheels |
| API framework | FastAPI 0.136.x + uvicorn | Async, OpenAPI, Filip's default |
| Frontend | Svelte 5 (runes) + SvelteKit | Filip's default, fits svar-skeleton skill |
| UI kit | Skeleton v4 + Tailwind | Existing Filip workflow |
| Map | MapLibre GL JS | Free, no Mapbox token, WebGL vector tiles |
| AI layer | OpenAI-compatible API (default: GLM 4.7 Flash via DeepInfra) | Open-weight, ~7x cheaper than Claude Sonnet, provider-swappable via env var |
| CI | None for now | Time is the constraint |
| Deploy | Azure Static Web Apps (frontend) + App Service (backend) | Avoid deploy risk on the day |

**Explicitly NOT used:**
- Jupyter notebooks (application form preferred)
- Vector DB (overkill for structured numeric features; revisit in Phase 6 only)
- Mapbox (token + billing risk)
- Docker (deploy complexity not needed for local demo)

---

## 2. Data sources — verified URLs

### Primary
| Dataset | Source | URL | Format | Size estimate |
|---|---|---|---|---|
| Alaska Landslide Inventory (DDS 23) | DGGS, Sept 2025 | https://dggs.alaska.gov/pubs/id/31697 | Shapefile + DB | ~50 MB |
| AK Inventory Web Layer (ArcGIS Online) | State of Alaska GIS | https://gis.data.alaska.gov/maps/e2232dad29af403793f688fb10abf6d8 | GeoJSON via REST | ~20 MB |
| Deep-seated landslide susceptibility (PIR 2025-3) | DGGS, 2025 | https://doi.org/10.14509/31691 | Raster, 1:3,750,000 | ~100 MB |
| News-reported slide impacts SEAK 1990-2024 | USGS, May 2025 | https://www.usgs.gov/data/news-reported-landslide-impacts-southeast-alaska-1990-2024 | CSV (162 events) | <1 MB |
| Tongass Landslide Areas | USFS, 2024 | https://agdatacommons.nal.usda.gov/articles/dataset/25972363 | Feature Layer | ~30 MB |

### Terrain (DEM)
| Dataset | Source | URL | Notes |
|---|---|---|---|
| USGS 3DEP 1/3 arc-second | USGS TNM | https://apps.nationalmap.gov/downloader/ | ~10m resolution, tile-based |

For Southeast Alaska scope: download tiles covering 55-60°N, 130-138°W. Estimated 4-6 tiles, ~500 MB-1 GB.

### Exposure
| Dataset | Source | URL | Format |
|---|---|---|---|
| OpenStreetMap Alaska extract | Geofabrik | https://download.geofabrik.de/north-america/us/alaska.html | PBF |

### Monitoring stations (negative mask)
| Dataset | Source | URL |
|---|---|---|
| Alaska Earthquake Center stations | AEC | https://earthquake.alaska.edu/ |
| Alaska Weather Observation Network (DDS 25) | DGGS | https://dggs.alaska.gov/weatherstations/ |

### Reference (not downloaded but cited)
- NASA LHASA model — global landslide hazard, used for comparison narrative
- Sitka rainfall warning system: http://www.sitkalandslide.org
- Ground Truth Alaska (Hig's nonprofit): https://groundtruthalaska.org/landslides

---

## 3. Repository structure

```
scarp/
├── README.md
├── AGENTS.md                       # this file
├── LICENSE                         # MIT
├── .gitignore
├── .python-version                 # 3.12 (pinned — geo wheels not yet on PyPI for 3.14)
│
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── src/
│   │   └── scarp/
│   │       ├── __init__.py
│   │       ├── api/
│   │       │   ├── __init__.py
│   │       │   ├── main.py         # FastAPI app
│   │       │   ├── zones.py        # /api/zones routes
│   │       │   ├── layers.py       # /api/layers routes
│   │       │   ├── search.py       # /api/search (Claude)
│   │       │   └── schemas.py      # Pydantic models
│   │       └── config.py
│   └── tests/
│
├── prep/                           # one-shot pipeline (run once, output committed)
│   ├── 00_download.py              # idempotent downloads
│   ├── 10_normalize.py             # reproject to EPSG:3338
│   ├── 20_slope.py                 # DEM → slope polygons
│   ├── 30_exposure.py              # OSM filter + buffer
│   ├── 40_monitoring_mask.py       # stations → coverage mask
│   ├── 50_score_zones.py           # combine, score, rank
│   └── README.md                   # how to re-run
│
├── data/
│   ├── raw/                        # gitignored
│   │   ├── dggs/
│   │   ├── dem/
│   │   ├── osm/
│   │   └── stations/
│   └── processed/                  # COMMITTED — small enough
│       ├── zones.geojson           # main output, ~100 zones
│       ├── slides.geojson          # known slides for display
│       ├── stations.geojson        # monitoring stations
│       └── meta.json               # generation timestamp + checksums
│
├── frontend/
│   ├── package.json
│   ├── svelte.config.js
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── app.html
│   │   ├── app.css                 # Skeleton v4 + Tailwind
│   │   ├── routes/
│   │   │   ├── +layout.svelte
│   │   │   ├── +page.svelte        # main map view
│   │   │   └── about/+page.svelte  # story + credits
│   │   └── lib/
│   │       ├── components/
│   │       │   ├── Map.svelte
│   │       │   ├── PriorityList.svelte
│   │       │   ├── ZoneDetail.svelte
│   │       │   ├── LayerToggle.svelte
│   │       │   └── SearchBar.svelte
│   │       ├── stores/
│   │       │   └── zones.svelte.ts  # $state runes
│   │       └── api.ts               # typed fetch client
│   └── static/
│
└── docs/
    ├── pitch.md                     # 60-sec script
    ├── slides.md                    # 2 slides max
    └── screenshots/
```

---

## 4. Phase 0 — Foundation

**Goal:** Empty repo → both backend and frontend bootable.

### 0.1 Repo init
- Create `github.com/flupkede/scarp` (public, MIT, no template)
- Clone locally to `C:\WorkArea\AI\scarp`
- Add `.gitignore` covering: `.venv/`, `__pycache__/`, `node_modules/`, `data/raw/`, `*.tif`, `*.tiff`, `*.shp`, `.svelte-kit/`, `build/`, `.DS_Store`

### 0.2 Python project
- `cd backend && uv init --package scarp && uv python pin 3.12`
- Add dependencies: `uv add fastapi uvicorn[standard] geopandas rasterio shapely pyproj httpx anthropic pydantic-settings python-multipart`
- Dev dependencies: `uv add --dev pytest ruff mypy`
- Configure ruff in `pyproject.toml` (line length 100, target-version py312)
- Smoke test: `uv run python -c "import geopandas; print(geopandas.__version__)"`

### 0.3 Frontend project
- `cd frontend && pnpm create svelte@latest .` — choose Skeleton project, TypeScript yes, ESLint/Prettier yes
- Apply Skeleton v4 setup per the svar-skeleton skill (Filip already has tokens mapped)
- Install: `pnpm add maplibre-gl @types/geojson`
- Verify dev server: `pnpm dev`

### 0.4 Root-level scaffolding
- `README.md` with title, one-liner, "in progress" badge
- Empty `prep/__init__.py` and `prep/README.md`
- `docs/pitch.md` and `docs/slides.md` as empty placeholders

### 0.5 Verify
- Backend: `uv run uvicorn scarp.api.main:app --reload` returns 200 on `/health` (write minimal endpoint)
- Frontend: `pnpm dev` shows default Skeleton page on localhost:5173
- Commit: `chore: scaffold backend + frontend`

**DoD Phase 0:**
- [ ] Public repo exists on GitHub
- [ ] Both `uvicorn` and `pnpm dev` boot without error
- [ ] `/health` endpoint returns `{"status":"ok"}`
- [ ] Initial commit pushed to main

---

## 5. Phase 1 — Data acquisition

**Goal:** Raw datasets downloaded locally, idempotent re-runs.

### 1.1 DGGS inventory download
- Use the ArcGIS Online REST endpoint at `https://gis.data.alaska.gov/maps/e2232dad29af403793f688fb10abf6d8` to query FeatureServer
- Page through results (1000 records/page) → write to `data/raw/dggs/inventory.geojson`
- Fallback: download DGGS DDS 23 zip directly from the publication page
- Validate: feature count >5000 (DGGS reports 6000+ documented)

### 1.2 DGGS susceptibility raster
- Download PIR 2025-3 raster from https://doi.org/10.14509/31691 → `data/raw/dggs/susceptibility.tif`
- Validate: rasterio opens it, CRS reads correctly

### 1.3 USGS 3DEP DEM for Southeast Alaska
- Use TNM API: `https://tnmaccess.nationalmap.gov/api/v1/products`
- Bounding box: 55.0 to 60.0 N, -138.0 to -130.0 W
- Product: "National Elevation Dataset (NED) 1/3 arc-second"
- Download as GeoTIFF tiles → `data/raw/dem/`
- Validate: at least 4 tiles, total >300 MB

### 1.4 OSM Alaska extract
- Download `alaska-latest.osm.pbf` from Geofabrik → `data/raw/osm/`
- Validate file size ~150-250 MB

### 1.5 USGS news-reported slides CSV
- Direct CSV download from USGS data release → `data/raw/usgs/seak_news_slides.csv`
- Parse with pandas, validate 162 rows

### 1.6 USFS Tongass landslide areas
- Download feature layer from Ag Data Commons → `data/raw/usfs/tongass_slides.geojson`

### 1.7 Monitoring stations
- Alaska Earthquake Center via FDSN: `https://service.iris.edu/fdsnws/station/1/query?network=AK&format=text`
- Parse to GeoJSON → `data/raw/stations/aec_stations.geojson`
- DGGS weather stations from DDS 25 → `data/raw/stations/dggs_weather.geojson`

### 1.8 Idempotent runner `prep/00_download.py`
- Check: file exists + checksum matches → skip; else download
- Write `data/raw/MANIFEST.json` with sizes, checksums, timestamps
- Commit MANIFEST, not raw data

**DoD Phase 1:**
- [ ] All 7 datasets present locally with expected sizes
- [ ] `MANIFEST.json` committed
- [ ] Re-run is idempotent and fast (<5s when complete)

---

## 6. Phase 2 — Spatial processing

**Goal:** From raw data to `zones.geojson` with ranked scoring.

### 2.1 Normalize CRS (`prep/10_normalize.py`)
- Target CRS: **EPSG:3338 (Alaska Albers Equal Area)** — preserves area for scoring
- Output for frontend: EPSG:4326 (MapLibre native)
- `normalize(input_path, output_path) -> None` — reproject + clean invalid geoms
- Output to `data/processed/intermediate/`

### 2.2 Compute slope (`prep/20_slope.py`)
- Merge DEM tiles into VRT (`gdalbuildvrt` or rasterio)
- Compute slope in degrees using `richdem` or rasterio + numpy gradient
- Reclassify: cells >25° = 1, else 0
- Vectorize using `rasterio.features.shapes` → polygons, simplify 50m
- Output: `data/processed/intermediate/steep_slopes.geojson`

### 2.3 Exposure layer (`prep/30_exposure.py`)
- Extract from `.pbf` using `pyrosm` or `osmium`: buildings, roads, tourism POIs, ferry terminals
- Project to EPSG:3338
- 500m grid: `log(1 + buildings) + 2*log(1 + roads_km) + 5*(has_tourism)`
- Output: `data/processed/intermediate/exposure.tif`

### 2.4 Monitoring mask (`prep/40_monitoring_mask.py`)
- Combine AEC stations + DGGS weather stations
- Buffer each by 10 km, union → single MultiPolygon
- Rasterize to 500m grid: 1 = covered, 0 = uncovered
- Output: `data/processed/intermediate/coverage_mask.tif`

### 2.5 Score zones (`prep/50_score_zones.py`)

```
For each 500m grid cell:
    susceptibility = sample DGGS susceptibility raster
    slope_factor   = sample steep_slopes mask (binary)
    inv_proximity  = exp(-distance_to_nearest_known_slide / 5km)
    exposure       = sample exposure raster
    coverage       = sample coverage_mask

    raw_score  = susceptibility * (1 + slope_factor) * (1 + inv_proximity) * (1 + exposure)
    gap_score  = raw_score * (1 - 0.8 * coverage)

cluster cells score > 75th percentile → contiguous zones
keep top 100 zones by sum of cell scores
emit GeoJSON: id, geometry, score, rank, components
```

- Output: `data/processed/zones.geojson` (~100 zones, <5 MB)
- Also: `data/processed/zones_top10.json`, `data/processed/meta.json`

### 2.6 Sanity check
- Open in QGIS or geojson.io
- Top 10 must include zones near Barry Arm, Portage Lake, Lituya Bay

**DoD Phase 2:**
- [ ] Pipeline runs end-to-end
- [ ] `zones.geojson` has score, rank, components per zone
- [ ] Top 10 includes known high-risk areas
- [ ] All processed outputs committed

---

## 7. Phase 3 — Backend API

### 3.1 `GET /health` → `{"status":"ok","version":"0.1.0"}`
### 3.2 `GET /api/zones` — limit, min_score, bbox filter; returns FeatureCollection
### 3.3 `GET /api/zones/{id}` — full breakdown + nearby_slides within 20 km
### 3.4 `GET /api/layers/{slides|stations}` — individual layers for map display
### 3.5 `POST /api/search` — NL query → Claude API tool call → filtered FeatureCollection + explanation
### 3.6 Pydantic schemas: `Zone`, `ZoneComponents`, `SearchRequest`, `SearchResponse`
### 3.7 Tests: health, bbox filter, mocked search — `uv run pytest`

**DoD Phase 3:**
- [ ] OpenAPI docs render at `/docs`
- [ ] `pytest` passes
- [ ] `/api/zones?limit=10` returns 10 features
- [ ] Branch `features/phase-3-backend-api` pushed to origin

---

## 8. Phase 4 — Frontend

### 4.1 Dark Skeleton v4 theme, svar-skeleton tokens, header with GitHub link
### 4.2 `api.ts` — typed fetch client, `PUBLIC_API_URL` env var
### 4.3 `zones.svelte.ts` — `$state` store with `loadZones()`, `selectZone()`, `applyFilter()`
### 4.4 `Map.svelte` — MapLibre + CartoDB Dark Matter, Southeast Alaska view, zone heatmap, slide/station markers
### 4.5 `PriorityList.svelte` — sidebar top 10, click → flyTo
### 4.6 `ZoneDetail.svelte` — slide-in panel, score breakdown, nearby slides
### 4.7 `LayerToggle.svelte` — slides / stations / exposure toggles
### 4.8 `SearchBar.svelte` — NL query → `/api/search` → filter + Claude explanation
### 4.9 About page — Hig story, credits (NatGeo, DGGS, USGS, Ground Truth Alaska)

**DoD Phase 4:**
- [ ] `pnpm build && pnpm preview` succeeds
- [ ] Map loads, layers toggleable
- [ ] Zone click → detail panel
- [ ] Search returns filtered results
- [ ] Branch `features/phase-4-frontend` pushed to origin

---

## 9. Phase 5 — Pitch artifacts

### 5.1 README — hero screenshot, demo GIF, problem + solution, run instructions, credits
### 5.2 `docs/pitch.md` — 60-second script: hook (Lituya 1958) → problem (Hig + mason jars) → demo (map + search) → close
### 5.3 `docs/slides.md` — 2 slides max: problem / methodology + data sources
### 5.4 Rehearse pitch 3 times before demo day

**DoD Phase 5:**
- [ ] README has screenshot + GIF + run instructions
- [ ] Pitch timed to 60s
- [ ] Branch `features/phase-5-pitch` pushed to origin

---

## 10. Phase 6 — Stretch

- **6.1** Vector similarity — "this zone resembles Barry Arm" via cosine similarity on slide feature vectors
- **6.2** Sentinel-2 NDVI delta — vegetation disturbance as fourth scoring component
- **6.3** "Send to Hig" button — mailto prefilled with top-10 zones
- **6.4** Time slider — filter known slides by year, visualize 10x increase

---

## 11. Definition of Done

- [ ] Phase 0-5 complete
- [ ] Public repo at github.com/flupkede/scarp
- [ ] Live deploy on Azure Static Web Apps (no laptop-only demo)
- [ ] Pitch memorized

## 11a. Visual direction (locked)

- **Style:** Field tool aesthetic — feels like something Hig would use
- **Basemap:** Topographic (contours visible), not generic dark
- **Accent colors:** Warm oranges/ambers for high-risk zones, not blue
- **Typography:** Weighty serif for headers, sans for UI
- **Splash screen on load:** Full-bleed USGS Tracy Arm aerial photo (public domain), with quote overlay, 3 sec auto-fade to the map
- **Quote:** "In 1958, Lituya Bay saw the highest wave ever recorded — 524 m. In August 2025, Tracy Arm came within 50 m of that record. Nobody saw it coming."
- **Signature detail:** Mason jar SVG icon for monitoring stations on the map
- **Detail panel:** "Field notebook" feel — paper texture or off-white background, handwritten-feel section dividers

## 11b. Copyright rules (strict)

- **NEVER embed copyrighted media in the repo.** No NatGeo photos, no NatGeo maps, no Out of Eden Walk images, no NYT graphics.
- **Allowed:** US Government works (USGS, NASA, DGGS) — public domain. NatGeo article LINKED in README with credit is fine; their images downloaded into repo is not.
- **Verified safe USGS assets (all CC0):**
  - `https://www.usgs.gov/media/images/2025-tracy-arm-landslide-and-tsunami-trimline` — splash candidate
  - `https://www.usgs.gov/media/images/2025-tracy-arm-landslide-source-area-facing-northwest` — alternative
  - `https://www.usgs.gov/media/slideshows/2025-tracy-arm-landslide-field-photos` — slideshow with multiple options
- **Our own map** of Southeast Alaska from DGGS inventory + DEM = original work, no copyright issue.
- **Custom SVG illustrations** (mason jar, fjord cross-section) = OK to ship.

## 11c. On-day execution rule (ethics)

The current `C:\WorkArea\AI\scarp\` repo is **portfolio + test bed**. It is private on GitHub.

On the hackathon day:
- Start fresh — new public repo, `gh repo create flupkede/scarp-hackathon` (or similar)
- Build with opencode using the refined phase files in `C:\WorkArea\AI\scarp-plans\` as specs
- **No copy-paste of code from the private repo.** Specs and verified URLs are fine; code is not.
- Data downloads happen on the day (downloads from public sources during the event = standard practice)
- Commit frequently so the AI judge can see iterative development

---

## 12. Non-goals

- Real-time satellite detection (already exists)
- ML model training (rule-based scoring is explainable)
- User accounts, auth, persistence
- Production deployment
- Database
- Full Alaska coverage (Southeast Alaska only; statewide in Phase 6)
- Mobile app

---

## 13. Time budget

| Phase | Estimate |
|---|---|
| Phase 0 | 1.5h |
| Phase 1 | 3h |
| Phase 2 | 5h |
| Phase 3 | 3h |
| Phase 4 | 6h |
| Phase 5 | 2h |
| Phase 6 | optional |
| Demo day | 12h |

Total prep: ~20h.

---

## 14. Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| DEM download slow | Medium | Start early as background task |
| Susceptibility raster CRS issues | Medium | Phase 2.1 normalize step; test early |
| OSM extract too large for pyrosm | Low | Fall back to Overpass bbox query |
| Claude API unavailable during demo | Low | Cache last 10 results as static fallback |
| MapLibre perf with 100 zones | Low | Pre-decimate geometries if needed |
| ZBook memory pressure | Medium | Close OneDrive + VS Code Insiders during processing |
| OpenCode hits Copilot rate limit | Medium | Use Z.AI GLM 5.1 as fallback |

---

## 15. OpenCode execution

**MANDATORY: One branch per phase, commit + push at the end.**

### Branch naming
`features/phase-N-<slug>` (e.g. `features/phase-3-backend-api`)

### Per-phase workflow
1. `git checkout -b features/phase-N-<slug>`
2. Implement phase
3. `git add` + `git commit -m "<type>(phase-N): <subject>"`
4. `git push -u origin features/phase-N-<slug>`
5. Merge to main (or keep branch for review)

### Phases 0–2 already on main (done before branch policy)

### Commit conventions
`<type>(phase-N): <imperative subject>`

Types: `feat`, `fix`, `refactor`, `docs`, `chore`, `data`

### Rules
- No multi-line PowerShell
- `C:\WorkArea\AI\scarp\` paths → Filesystem MCP, not bash
- Verify technical claims via web search before answering
- **NO long-running foreground commands** (see §17)

---

## 16. OpenCode execution rules

- **NO long-running foreground bash commands.** Anything expected to take >30s (DEM processing, OSM parsing, scoring pipelines, large file downloads) MUST be run in the background with `python -u script.py > /tmp/log.txt 2>&1 &`. Check output files afterwards.
- **Self-blocking is a bug.** Running a command that takes 5+ minutes in foreground means you cannot respond to the user. ALWAYS use background (`&`) for heavy scripts.
- **Check output files, don't wait.** For heavy processing scripts, start the run, note the expected output path, and check if the file appeared rather than blocking on stdout.

---

## 17. Local dev — MANDATORY

**NEVER start uvicorn or pnpm dev directly from bash.** Always use `dev.ps1`:

```powershell
# from C:\WorkArea\AI\scarp\
.\dev.ps1 start    # starts backend :8000 + frontend :5173 (background, non-blocking)
.\dev.ps1 stop     # stops both cleanly
.\dev.ps1 status   # health check + PID info
.\dev.ps1 logs     # last 20 lines from backend/frontend logs
.\dev.ps1 restart  # stop + start
```

- `start` / `stop` are idempotent — safe to run if already running/stopped.
- Logs land in `.dev-logs/backend.log` and `.dev-logs/frontend.log`.
- From bash (inside OpenCode), invoke as: `pwsh -NonInteractive -Command "Set-Location 'C:\WorkArea\AI\scarp'; .\dev.ps1 <action>"`
- **Why:** direct `uvicorn &` leaves orphan processes; `dev.ps1` tracks PIDs and can clean them up.

---

*See git log for revision history.*
