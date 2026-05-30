<h1 align="center">SCARP</h1>
<p align="center"><i>Where to put the next sensor.</i></p>

<p align="center">
  <a href="https://scarp.dsoft.services">Live demo</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="#why-this-is-new">Why this is new</a> ·
  <a href="#run-locally">Run locally</a>
</p>

---

As glaciers retreat in a warming climate, mountain slopes are collapsing — sometimes into fjords as tsunamis, sometimes onto villages. Scarp ranks where a single monitoring sensor would save the most lives, using only public data.

---

## The 15-second version

In 1958 a landslide into Alaska's Lituya Bay made the highest wave ever recorded: 524 metres. In 2025, a glacier collapse buried 90% of the Swiss village of Blatten — but its 300 residents survived because monitoring caught the slope moving and they were evacuated in time. **Monitoring is the difference.** Yet across Alaska's fjords, almost nobody is systematically deciding *where* to monitor next.

Independent geologist Bretwood "Hig" Higman builds his own low-cost sensors and installs them by hand, alone. He has no map telling him where the next one matters most. Scarp builds that map.

---

## Demo

> Click any site to see why it ranked. Ask in plain English: *"sites near cruise routes with no monitoring"* or *"highest exposure in Turnagain Arm"*.

*→ [Open the live demo](https://scarp.dsoft.services) — click any zone to see its breakdown, or type a plain-English query.*

---

## Why this is new {#why-this-is-new}

A statewide, high-resolution, monitoring-priority map for tsunamigenic slides in Southeast Alaska does not exist. We didn't invent the gap — the science named it:

> **Walden et al. 2025** (*Natural Hazards and Earth System Sciences*, doi:10.5194/nhess-25-2045-2025) — co-authored by Higman himself — "further substantiate[s] the need for establishing **broader and more systematic paraglacial hazard monitoring** in a warming world." The study examined just 8 landslides.

> **Patton et al. 2023** (*NHESS*, doi:10.5194/nhess-23-3261-2023) — "**no systematic landslide warning threshold currently exists** at either local scales for towns within southeast Alaska or the regional scale."

Scarp is a first-order response to a gap that two peer-reviewed papers named independently.

The honest precision: individual sites *are* monitored (Barry Arm since 2020, Sitka's rainfall system). The gap is the *triage step* — which of the thousands of unwatched slopes deserves the next sensor? That question has no systematic answer. Until now.

---

## How it works {#how-it-works}

Five public datasets, one ranked list:

| Signal | Dataset | What it captures |
|--------|---------|-----------------|
| **Susceptibility** | USGS 90 m model (Mirus et al. 2024) | Terrain stability from DEM physics |
| **Proximity** | DGGS landslide inventory (~40 k features) | Distance to known past failures |
| **Slope** | USGS 3DEP 10 m DEM | Steep faces most likely to release |
| **Exposure** | OpenStreetMap Alaska | Buildings, roads, ferry routes, tourism |
| **Monitoring gap** | Alaska Earthquake Center station network | Where sensors are *absent* |

Scoring: a weighted-additive formula (no signal zeros out others) → local-maxima detection → top 120 ranked points. Each point carries a score breakdown and the set of known slides within 20 km.

The natural-language search (`POST /api/search`) routes your query through an LLM (GLM 4.7 Flash via DeepInfra) which calls a `filter_zones` tool and returns a filtered subset with an explanation.

### Architecture

```mermaid
graph LR
    subgraph "Data Sources (public)"
        A[USGS 90m DEM\nSusceptibility]
        B[DGGS Inventory\n~40k slides]
        C[OSM Alaska\nExposure]
        D[AEC Stations\nMonitoring gap]
    end

    subgraph "Prep pipeline (one-shot)"
        E[00_download.py]
        F[10_normalize.py\nEPSG:3338]
        G[20_slope.py]
        H[50_score_zones.py\nLocal maxima]
    end

    subgraph "Backend (FastAPI)"
        I[/api/zones]
        J[/api/search\nLLM tool call]
        K[/api/layers]
    end

    subgraph "Frontend (SvelteKit + MapLibre)"
        L[Map + heatmap]
        M[Priority list]
        N[Search bar]
    end

    A & B & C & D --> E --> F --> G --> H
    H --> |zones.geojson| I & J & K
    I --> L
    J --> N
    K --> L
    M --> L
```

### Key data decision

We use the USGS 90 m susceptibility model (Mirus et al. 2024) rather than the standard DGGS statewide raster, because the coarse 900 m version marks the narrow fjords — where these slides actually happen — as `NODATA`. Tracy Arm, Lituya Bay, Taan Fiord: all `NODATA` in the official raster. The USGS model covers them.

---

## Engineering journey

Scarp's scoring model went through five rejected approaches before it worked. Each rejection taught us something about the problem.

- **Multiplicative scoring collapsed.** `susc × slope × exposure × …` zeroed out any site with a single missing factor — killing exactly the remote fjords (zero buildings → zero exposure → zero score). Switched to weighted-additive so each signal contributes independently.

- **The standard susceptibility map was blind to fjords.** Alaska's official DGGS raster (900 m) marks the narrow fjords as `NODATA` — 88.6% of Southeast Alaska's high-risk area. Verified by sampling Tracy Arm, Lituya Bay, Taan Fiord: all `NODATA`. Switched to USGS n10 (90 m, Mirus et al. 2024), which covers them.

- **Clustering produced meaningless mega-blobs.** Density clustering merged adjacent high-risk cells into regions spanning tens of km — useless for "place a sensor here." Replaced with local-maxima detection: discrete points at the actual peaks, with enforced minimum spacing.

- **The model ranked Anchorage suburbs first.** Because they have the most buildings. A tsunamigenic slide needs a steep wall into deep water, not population density. Adding a "fjord-wall" signal (local relief × water proximity) pushed the suburbs out and surfaced genuine fjord cliffs (Turnagain Arm, Portage, Whittier).

- **Barry Arm — the most famous site — ranks low, on purpose.** It triggered the National Landslide Preparedness Act, but it already has a sensor 1.3 km away. The model correctly deprioritizes it: Scarp finds places that are dangerous *and* unwatched, not places we already monitor. That distinction is the whole point.

We also document where the model is blind: Lituya Bay and Taan Fiord have no public elevation data. Their absence from the rankings isn't "low risk" — it's "no data," shown explicitly as a confidence layer.

---

## Beyond Alaska

The method is geography-agnostic. The same glacier-retreat → debuttress → failure mechanism drives risk in the Alps (Blatten, 2025), the Himalayas, Patagonia, Norway's fjords. Swap the input datasets — same scoring engine, same output format. The only Alaska-specific component is the DGGS inventory; everything else is a global methodology.

---

## Tech stack

- **Data prep:** Python 3.12, GeoPandas, rasterio, numpy, shapely, pyproj
- **Backend:** FastAPI + uvicorn/gunicorn, provider-agnostic LLM via OpenAI SDK
- **Frontend:** SvelteKit 5 (runes) + MapLibre GL JS + Skeleton v4 + Tailwind
- **Deploy:** Azure Static Web App (frontend) + App Service B1 Linux (backend)
- **LLM:** GLM 4.7 Flash via DeepInfra — no vendor lock-in, swappable via `LLM_BASE_URL` env var

See [SECURITY.md](./SECURITY.md) for the security posture (strict CORS, Key Vault for API keys, no secrets in repo).

---

## Run locally {#run-locally}

**Requirements:** Python 3.12, [uv](https://github.com/astral-sh/uv), Node 22, pnpm

```bash
# 1. Clone
git clone https://github.com/flupkede/scarp-app.git
cd scarp-app

# 2. Backend
cd backend
cp .env.example .env          # fill in DEEPINFRA_API_KEY (or leave blank for offline mode)
uv sync
uv run uvicorn scarp.api.main:app --port 8000 --reload

# 3. Frontend (separate terminal)
cd frontend
pnpm install
pnpm dev                      # → http://localhost:5173
```

The processed GeoJSON data (`data/processed/`) is committed to the repo — no download needed for the API to serve zones.

**Re-run the data pipeline** (optional — raw data ~12 GB, download takes 30-60 min):
```bash
cd prep
uv run python 00_download.py
uv run python 10_normalize.py
uv run python 20_slope.py
uv run python 30_exposure.py
uv run python 40_monitoring_mask.py
uv run python 50_score_zones.py
```

---

## Data sources

| Dataset | Source | License |
|---------|--------|---------|
| Landslide susceptibility (90 m) | USGS (Mirus et al. 2024) | Public domain |
| Alaska landslide inventory (~40 k) | DGGS DDS 23, Sept 2025 | CC0 |
| USGS 3DEP DEM (10 m) | USGS National Map | Public domain |
| News-reported slides SEAK 1990-2024 | USGS data release, May 2025 | Public domain |
| OpenStreetMap Alaska | Geofabrik extract | ODbL |
| Seismic station network | Alaska Earthquake Center | Public |
| Tracy Arm reference imagery | USGS, 2025 | Public domain |

---

## Honest limitations

- **Not a validated hazard model.** Weights are defensible, not authoritative. This is a first-order triage tool, not a substitute for on-the-ground geological assessment.
- **Lituya Bay and Taan Fiord are blind spots.** Public elevation data does not cover these fjords. Their absence from the rankings means "no data," not "low risk."
- **Exposure is coarse.** OSM building/road density is a proxy; actual population at risk requires census data not used here.
- **Coverage mask is sparse.** AEC seismic stations detect earthquakes, not slope deformation directly. Purpose-built tiltmeters and GPS would give a better coverage picture.
- **Southeast Alaska only.** The DGGS inventory covers more of Alaska but processing was scoped to the highest-risk fjord region.

---

## Credits

- Inspired by the work of [Bretwood "Hig" Higman](https://groundtruthalaska.org/landslides) and Ground Truth Alaska
- Story context: National Geographic, *"Lessons of a landslide detective"*, June 2026 issue (linked; no NatGeo images in this repo)
- Data: USGS, DGGS, OSM contributors, Alaska Earthquake Center
- Imagery: USGS public domain only ([Tracy Arm 2025](https://www.usgs.gov/media/images/2025-tracy-arm-landslide-and-tsunami-trimline))
- License: [MIT](./LICENSE)
