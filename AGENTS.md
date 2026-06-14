# Scarp — Project Reference

> *Where to put the next sensor.* Ranked monitoring-priority map for tsunamigenic landslides in Southeast Alaska.

**Repo:** github.com/flupkede/scarp-app (public, MIT)
**Live:** scarp.dsoft.services
**Owner:** Filip (architect + reviewer), OpenCode (executor)
**Language:** English (code, comments, docs)

---

## Context

Independent geologist Bretwood "Hig" Higman builds $300 mason-jar sensors and installs them by hand in Alaska's fjords. Nobody is systematically deciding *where* to monitor next. Scarp ranks where a single sensor would save the most lives, using only public data.

Output: a ranked map of ~120 "next sensor goes here" sites, with explainable scoring (susceptibility, fjord-wall signal, exposure, monitoring gap) and an honest data-confidence layer showing where public inputs are thin (~¾ of the region).

Source: *Lessons of a landslide detective* by Christian Elliott, National Geographic, June 2026.

---

## Implemented Features

- **Data pipeline (prep/)** — 7 scripts: download → normalize EPSG:3338 → slope from DEM → relief from DEM → exposure from OSM → monitoring mask from AEC stations → weighted-additive scoring with local-maxima detection
- **Scoring engine** — weighted-additive (not multiplicative), 7 signals: susceptibility (USGS 90 m), fjord wall (relief × water proximity), volume proxy (height × steepness, replaces redundant slope), proximity to known slides (DGGS ~40k inventory), exposure (OSM buildings/roads/tourism), monitoring gap (AEC seismic stations), and **glacier dynamics** (ITS_LIVE, W_GLACIER=0.15)
- **Glacier dynamics (ITS_LIVE)** — `glacier/` pipeline ingests NASA ITS_LIVE velocity (Zarr/S3), extracts per-point time series + robust trends, enriches each candidate zone with glacier context (proximity to active ice, ice velocity, trend), and re-ranks the proven 120-candidate set with a glacier scoring signal. Served via `/api/layers/glacier_velocity` + a per-zone glacier block on `/api/zones`; shown in the zone-detail panel and an optional map velocity layer
- **Fjord-wall signal** — local relief × water proximity, prevents Anchorage suburbs from dominating
- **Data-confidence layer** — shows where public inputs are thin; grey overlay + source badges in detail panel
- **Backend API** — FastAPI: `GET /health`, `/api/zones`, `/api/zones/{id}`, `/api/layers/{slides|stations}`, `POST /api/search`
- **NL search** — LLM translates free text to filter params; deterministic Python does actual filtering. Provider-agnostic (DeepInfra/GLM default, Anthropic fallback). Graceful fallback if no API key.
- **Frontend** — SvelteKit 5 + MapLibre GL JS + Skeleton v4 + Tailwind. Candidate points, heatmap, priority list, zone detail panel, layer toggles, search bar
- **Story page** — Scrollytelling route with Tracy Arm before/after slider, Hig story, science citations
- **About page** — Credits, methodology, data sources
- **Security** — Rate limiting (slowapi, 10/min on search), strict CORS, Key Vault for API keys, no secrets in repo
- **Deploy** — Azure Static Web Apps (frontend) + App Service B1 Linux (backend). GitHub Actions CI/CD.
- **Pitch docs** — `docs/pitch.md` (walkthrough + standalone 60s), `docs/video-plan.md` (talking-head + screen-share hybrid)

---

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Python 3.12, FastAPI, uvicorn, GeoPandas, rasterio, shapely, pyproj |
| Frontend | SvelteKit 5 (runes) + MapLibre GL JS + Skeleton v4 + Tailwind |
| LLM | GLM 4.7 Flash via DeepInfra (OpenAI-compatible, swappable via `LLM_BASE_URL`) |
| Deploy | Azure SWA (frontend) + App Service B1 Linux (backend) |
| Data prep | Python 3.12, GeoPandas, rasterio, numpy, shapely, pyproj |

---

## Key decisions

- **Volume proxy replaces slope** — old `slope_factor` double-counted steepness (already in USGS susceptibility); replaced with `height × steepness` volume proxy per Higman feedback and Hermanns et al. 2026 Volume criterion
- **Weighted-additive scoring** — multiplicative zeroed out remote fjords; additive lets each signal contribute independently
- **USGS 90 m susceptibility** over DGGS 900 m — the coarse DGGS raster marks fjords (where slides happen) as NODATA
- **Local-maxima detection** over density clustering — clustering produced meaningless mega-blobs
- **Barry Arm ranks low on purpose** — it already has monitoring; Scarp finds dangerous *and unwatched* places
- **Data-confidence layer** — ~75% of SE Alaska is data-limited; showing the gap honestly is itself a finding (aligns with Walden 2025, Patton 2023)

---

## Repository structure

```
backend/          # FastAPI app (src/scarp/api/)
frontend/         # SvelteKit 5 app
prep/             # one-shot data pipeline scripts (scoring + candidate selection)
glacier/          # ITS_LIVE glacier pipeline: 00_explore → 10_extract → 20_visualize
                  #   → 30_enrich_zones → 40_rerank_zones
data/processed/   # committed GeoJSON outputs (zones, slides, stations, glacier_velocity)
docs/             # pitch, video plan, rationale
```

### Glacier pipeline order

`prep/50_score_zones.py` (selection) → `glacier/10_extract.py` (velocity at zones,
network/S3) → `glacier/30_enrich_zones.py` (per-zone glacier params + publish
velocity layer) → `glacier/40_rerank_zones.py` (glacier-aware score + rank).
`10_extract.py --from-parquet` regenerates the summary from the cached time
series without re-hitting the network.

---

## Remaining work (Phase 6 — Stretch)

- **6.1** Vector similarity — "this zone resembles Barry Arm" via cosine similarity
- **6.2** Sentinel-2 NDVI delta — vegetation disturbance as scoring component
- **6.3** "Send to Hig" button — mailto prefilled with top-10
- **6.4** Time slider — filter slides by year, visualize 10x increase

---

## Visual direction (locked)

- **Style:** Field tool aesthetic — feels like something Hig would use
- **Basemap:** Topographic (contours visible)
- **Accent colors:** Warm oranges/ambers for high-risk zones
- **Splash screen:** Full-bleed USGS Tracy Arm aerial (public domain), quote overlay, 3 sec auto-fade
- **Signature detail:** Mason jar SVG icon for monitoring stations
- **Detail panel:** "Field notebook" feel — off-white background

## Copyright rules (strict)

- **NEVER** embed copyrighted media (no NatGeo photos, no NYT graphics)
- **Allowed:** US Government works (USGS, NASA, DGGS) — public domain
- **Verified safe USGS assets:** Tracy Arm 2025 aerials (CC0)
- Custom SVG illustrations = OK to ship

---

## Local dev

**Requirements:** Python 3.12, [uv](https://github.com/astral-sh/uv), Node 22, pnpm

```bash
# Backend
cd backend && cp .env.example .env && uv sync
uv run uvicorn scarp.api.main:app --port 8000 --reload

# Frontend (separate terminal)
cd frontend && pnpm install && pnpm dev  # → localhost:5173
```

**dev.ps1 orchestrator** (mandatory — no direct uvicorn/pnpm dev from bash):
```powershell
.\dev.ps1 start|stop|status|logs|restart
```

---

## Azure deployment

- **Subscription:** `Visual Studio Professional with MSDN` (`c8438481-2fd9-4880-9bec-d8f4f426eae8`)
- **Resource group:** `scarp`
- **Static Web App:** `scarp-web` (frontend)
- **App Service:** `scarp-api` (backend, B1 Linux)
- **Before deploying:** `az account set --subscription c8438481-2fd9-4880-9bec-d8f4f426eae8`
- **Deploy command:** `.\dev.ps1 deploy` (or `deploy-fe` / `deploy-be` for individual)

---

## Execution rules

- **One branch per phase**, commit + push at end
- **Commit format:** `<type>(phase-N): <imperative subject>`
- **No long-running foreground commands** — background anything >30s
- **From bash:** invoke dev.ps1 via `pwsh -NonInteractive -Command "Set-Location 'C:\WorkArea\AI\scarp'; .\dev.ps1 <action>"`
- **Git email:** `10133533+flupkede@users.noreply.github.com` (no-reply, tied to flupkede account only)

---

## Non-goals

Real-time detection, ML training, user accounts, production deployment, database, full Alaska coverage (SE only), mobile app
