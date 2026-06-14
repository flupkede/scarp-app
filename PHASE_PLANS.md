# Scarp — Detailed Per-Phase Implementation Plans

> Actionable breakdown of the phases in [`ROADMAP.md`](./ROADMAP.md). Each phase
> lists goal, prerequisites, staged tasks (with target files), deliverables,
> validation, and honest dependencies. **Phase 1 is fully detailed (we start
> here); later phases are detailed as far as current knowledge allows — some
> steps are blocked on data we don't have yet (flagged ⛔).**
>
> Engineering conventions: `uv run --project {prep|glacier}` for Python; `pnpm`
> for frontend. Validate Python with `ruff check` + `python -m py_compile` +
> `pytest`; frontend with `svelte-check` + `pnpm build`. No hardcoded config
> strings (see global standards). Commit per stage; review per commit.

---

## Phase 0 — Base + reframe

**Docs ✅ done.** ROADMAP.md + AGENTS.md reframe committed; Scarp confirmed as the
modernized base (Hig inventory + survey circles already ingested).

**Execution ⏳ TODO — make the reframe real in the live product** (the decision is
in the docs, but the app still presents the score as if authoritative). Small:
- **Frontend honesty**: in `ZoneDetail.svelte` + the score legend, label the score
  an **"uncalibrated heuristic"** (not a probability); add a short tooltip/note.
- **Methodology / About page**: state the probability-not-susceptibility direction
  and that current ranks are provisional/uncalibrated.
- **API meta**: add a `calibration: "uncalibrated_heuristic"` flag to `meta.json` /
  the zones response so consumers can't mistake it for a probability.

Validation: `svelte-check` + `pnpm build`; backend `pytest`. One stage, one commit.

> Manual ice-front mapping (Phase 1 Stage 1.6) is documented for Filip in
> [`handmatig_ijsfront_intekenen.md`](./handmatig_ijsfront_intekenen.md).

---

## Phase 1 — ITS_LIVE exploration + instrument shell  *(START HERE)*

**Goal.** Deliver Hig's homework: *explore ITS_LIVE and produce interesting
outputs to get hooks in the data*, plus the **instrument shell** needed to
look at the ice (multi-temporal imagery + layer control), and the **hand-mapped
ice-front ground truth** that Phase 2 will verify automation against.

**Prerequisites (have).** ITS_LIVE ingestion (`glacier/10_extract.py`,
`--from-parquet` cache), `data/processed/glacier_velocity.geojson`, the existing
MapLibre map (`frontend/src/lib/components/Map.svelte`), the story-page swipe
slider pattern (`frontend/src/routes/story/+page.svelte`).

**Key clarification.** ITS_LIVE = *velocity*, not *ice-front position*. Retreat
data does not exist; we begin creating it by hand here (ground truth only).

**Progress (branch `feature/phase1-itslive`):**
- ✅ Stage 1.0 — lw raster wired (`prep/00_download.py`)
- ✅ Stage 1.1 — `glacier/15_explore.py` analytics (annual/seasonal/trend/episodes/gaps)
- ⏭️ Stage 1.2 — **de-scoped**: `glacier/20_visualize.py` already produces velocity
  time-series + sawtooth figures; the new `glacier_exploration.json` + episode
  markers are the substantive outputs. Revisit only if Hig wants exploration-driven figures.
- ✅ Stage 1.3 — API endpoints (`/api/layers/glacier_episodes`, `/glacier_timeseries`)
- ⬜ Stage 1.4 — instrument shell: basemap switcher + opacity (frontend) — NEXT
- ⬜ Stage 1.5 — before/after swipe + velocity chart (frontend)
- ✅ Stage 1.6 — ice-front ground-truth scaffolding + validator (`glacier/17_icefront_check.py`)

### Stage 1.1 — ITS_LIVE exploration analytics (Python)
- New `glacier/15_explore.py` (reads the cached time-series parquet, no network).
- Compute per glacier of interest (start: Tracy Arm, Barry Arm, Columbia, +top
  candidate-adjacent glaciers):
  - seasonal component + deseasonalized long-term trend,
  - **acceleration/deceleration episodes** ("sawtooth") with date + magnitude,
  - **data-gap detection** (coverage ending early = candidate retreat signal),
  - robust summary stats (already partly in `compute_summary`).
- Config constants → `glacier/config.py` (no literals in logic: glacier IDs,
  thresholds, window sizes, the target glacier list).
- Outputs to `data/processed/`:
  - `glacier_timeseries.json` (per-glacier series for charting),
  - `glacier_episodes.geojson` (acceleration events as points/segments),
  - extend `glacier_velocity.geojson` only if needed.

### Stage 1.2 — Exploration figures (the "interesting outputs")
- New `glacier/16_figures.py` → matplotlib static plots to `docs/figures/glacier/`:
  velocity-over-time per glacier, sawtooth annotated, data-gap-as-retreat marked.
- Purpose: shareable artifacts for Hig; not wired into the app.

### Stage 1.3 — Backend endpoints
- `backend/src/scarp/api/layers.py`: add `/api/layers/glacier_episodes`
  (via the existing `_optional_layer` helper) and `/api/glacier/timeseries`
  (serves `glacier_timeseries.json`; graceful 404 if absent).
- `backend/src/scarp/api/main.py`: load new artifacts into `app.state`.
- `backend/tests/test_api.py`: fixtures + count/shape assertions.

### Stage 1.4 — Instrument shell: basemap switcher + layer/opacity control
- Port Hig's `basemaps.js` registry → `frontend/src/lib/basemaps.ts` (allowed
  sources ONLY): USGS Topo, USGS Imagery, ESRI Topo (current default),
  **Sentinel-2 cloudless (EOX)**, **AHAP 1978–86 historical (Alaska)**, USGS
  historical topo. No ESRI/Maxar imagery for public deploy (license).
- New `BasemapSwitcher.svelte` (dropdown/cards) → `map.setStyle()` while
  preserving data layers (re-init on `idle`, mirror Hig's pattern).
- Extend `LayerToggle.svelte` → opacity sliders on raster overlays.

### Stage 1.5 — Instrument shell: multi-temporal view + velocity chart
- `BeforeAfterSwipe.svelte` — reuse the story-page swipe slider to compare two
  imagery dates/sources at the current view.
- `VelocityChart.svelte` — small SVG line chart of a glacier's velocity series
  (with sawtooth markers) shown in the detail panel when a glacier/zone is selected.
- `frontend/src/lib/api.ts`: `fetchGlacierTimeseries`, `fetchGlacierEpisodes`.

### Stage 1.6 — Hand-mapped ice-front ground truth (scaffolding)
- `data/manual/ice_fronts/` + a documented GeoJSON schema:
  `{ glacier, date (ISO), source_imagery, geometry: LineString }`.
- `glacier/17_icefront_check.py` — validate schema, plot fronts over time per
  glacier, compute front-position change (retreat distance between dates).
- `docs/icefront-mapping.md` — instructions for the **hand** step (which imagery,
  how to digitize). ⚠️ The actual digitizing of Tracy Arm + Barry Arm fronts is a
  **human task for Filip** — I provide the schema, template, validator, and visuals.

**Deliverables.** Exploration analytics + figures; episodes/timeseries served;
basemap switcher with multi-temporal imagery; opacity control; before/after
swipe; velocity chart in detail panel; ice-front ground-truth scaffolding +
instructions.

**Validation.** Per stage: `ruff` + `py_compile` + `pytest` (Python),
`svelte-check` + `pnpm build` (frontend). Reviewer-agent review per commit.

**Dependencies / open.** None blocking to start. ⛔ Glacier-thinning overlay
deferred to Phase 2 (needs Hig's dataset). **Decided: vendor USGS `lw` raster
alongside `n10`** (Hig uses both; his geology lead) — add to `prep/00_download.py`
+ susceptibility handling as a Stage 1.0 in this phase.

---

## Phase 2 — Glacier retreat as a model input  (H1 + H2)

**Goal.** Turn glacier dynamics into calibratable inputs: ice-front retreat over
time, episodic/"double" retreat, glacier "reach" proximity, velocity sawtooth.

**Prerequisites.** Phase 1 ground-truth fronts; ITS_LIVE episodes; ⛔ thinning
dataset (Hig's measured set + a generalized elevation-change product).

### Stage 2.1 — Ice-front retreat: hand → automate → verify
- **Hand** (Phase 1 output): digitized fronts for Tracy Arm + Barry Arm.
- **Automate** `glacier/20_retreat_detect.py`: detect ice-front position over time
  from imagery + ITS_LIVE coverage extent (candidate approach: Google Earth Engine
  or local raster + edge detection — literature check first, Hig unsure what exists).
- **Verify**: run automation on the hand-mapped glaciers; compare front positions;
  only trust on un-mapped glaciers once it reproduces the hand result.

### Stage 2.2 — Episodic / "double" retreat classification
- Identify retreat past long-stable pinning points (Holocene-unoccupied positions).
- Per-glacier flag: single vs episodic vs "double" retreat; magnitude/recency.
- ⛔ LIA-minimum (since 1850) may need a fast **hand-mapping** method (binary).

### Stage 2.3 — Glacier "reach" segmentation
- Segment glaciers into reaches for meaningful proximity (vs raw linear distance),
  to both landslides and the glacier front. Reproducible, documented method.

### Stage 2.4 — Per-slope glacier variables
- distance-to-ice-face (up-glacier and down-fjord), **buttressing vs erosion** as
  separate variables, velocity sawtooth as a candidate factor (let stats prune).

**Deliverables.** Retreat layers + per-zone glacier feature set ready for Phase 4.
**Dependencies.** ⛔ thinning data currency; literature check on retreat automation.

---

## Phase 3 — Modernize Hig's inventory features into the base

**Goal.** Reproduce Hig's viewer functionality, modernized, on Scarp's inventory.

### Stage 3.1 — Class model + styling
- Color classes: **slow = red** (≈ m/yr), **catastrophic + since-2012 = dark blue**,
  **older = gray-blue**. Size cutoff ≈ **1M m³** (area-based). Derive from the
  ingested Hig fields; constants in config.

### Stage 3.2 — Filters
- Class toggles; size/volume filter (client-side MapLibre `setFilter`); **running
  count** of the filtered set (Hig's app lacks the total — easy win).
- Reuse the dual-range slider pattern (port of Hig's `_setupDual`) as a Svelte
  component — but only on **measured** fields (area, volume, year), not the score.

### Stage 3.3 — N10/LW scatter analysis
- Reproduce Hig's scatter: terrain density vs where landslides occur; surface the
  off-diagonal outliers. New analysis script + a frontend panel/figure.

### Stage 3.4 — Per-landslide popups + faults
- Popups with before/after imagery (Planet/SAR ⛔ proprietary — use allowed sources).
- **Faults layer**: AK Quaternary Faults & Folds (DGGS DDS 3 / Koehler). ⛔ obtain DB.

**Deliverables.** Feature-parity inventory viewer on Scarp's stack.

---

## Phase 4 — Likelihood rubric + Bayesian calibration  *(science core)*

**Goal.** Combine factors into a **calibrated annual probability with honest
uncertainty**, calibrated on N≈120. **Filip builds/runs; Korup validates before
any claim.**

### Stage 4.1 — Feature matrix
- Assemble per-location factors with uncertainty: topography (slope, relief,
  aspect, convexity); **landslide-as-risk-factor probability cone** (peak at known
  slide, graded falloff; params height+width; start **isotropic**); glacier
  dynamics (Phase 2); permafrost (Gruber 2012, coarse-resolution caveat); rock
  type (later).

### Stage 4.2 — Calibration model
- Hierarchical Bayesian (PyMC), strong priors, ruthless feature parsimony.
- **Spatial cross-validation** (geographic blocks) — not random splits.
- **Circularity guard**: hold out / spatial-temporal split for landslide-as-risk.
- Model selection: include candidate factors (e.g. velocity), let CV prune.

### Stage 4.3 — Outputs
- Per-location probability + uncertainty band; replace the heuristic score.
- Honest "data-limited / wide-uncertainty" surfacing (extends current confidence).
- Test isotropic vs **anisotropic** distance via out-of-sample fit (data decides).

**Dependencies.** ⛔ factors from Phases 1–3; Korup review; ⛔ rock-type data.

---

## Phase 5 — Tsunami extension + vulnerability  *(later)*

### Stage 5.1 — SPLASH
- Implement SPLASH (Lyell SP477.1) to extend hazard over water; **100M m³ flat
  first-pass** volume filter. Independent step on top of the hazard map.

### Stage 5.2 — Vulnerability  *(hazard-first; this last)*
- Beyond point communities: major roads, **AIS ship traffic** (free tier),
  dispersed remote population. Hig recruiting economists. ⛔ data sourcing.

---

## Cross-cutting notes
- Definitions for hand→auto→verify, circularity, spatial CV, isotropic→anisotropic,
  Bayesian ownership, honest uncertainty: see the glossary in `ROADMAP.md` §5.
- Each phase ships on its own branch; stages commit + reviewer-review individually.
- Re-rank composition pattern (current pipeline is memory-bound for full raster
  rebuild) still applies until Phase 4 replaces scoring with calibrated probability.
