# Glacier Hazard Project — Agent Reference

> *Probabilistic landslide hazard assessment for Southeast Alaska, driven by glacier dynamics.*

**Origin:** Hig × Filip call, June 5 2026 (~67 min) + Hig follow-up email
**Collaborators:** Bretwood "Hig" Higman (field geologist, landslide science), Filip (Scarp architect), Ollie Korup (Potsdam, Bayesian stats — to be looped in)
**Domain:** landslidescience.org
**Hig's repo:** GitHub (Claude Code sole contributor, Hig doesn't look at code)
**Parent project:** Scarp (github.com/flupkede/scarp-app) — this extends Scarp's deterministic scoring toward probabilistic hazard assessment

---

## Core Vision

Replace qualitative susceptibility maps with **actual probabilities + uncertainty ranges**.
Philosophy: "worse data → bigger uncertainty" is honest and still useful.
Calibrate against Hig's 120-event inventory (paper submitted).

**Approach:** Build a rubric of risk factors → statistically calibrate with known events → output probabilities with uncertainty. Too many parameters for classical stats → **Bayesian** (Ollie Korup to advise).

---

## Risk Factor Rubric (from Hig's email, prioritized)

### 1. Glacier Dynamics and Change — START HERE

The dominant risk factor for tsunamigenic landslides in SE Alaska.

**Key concepts:**
- **Episodic retreat:** Glaciers stabilize at constrictions/shallow points, then break free and retreat in episodes
- **Double retreat:** Glacier was at A, retreated to stable B, then retreated again to C → slopes between B and C are newly exposed and high risk
- **Buttressing:** Glacier presses against slopes; retreat removes lateral support AND exposes undercut slopes
- **Probability cone:** Risk declines with distance from retreating glacier front

**Data sources:**
- **ITS_LIVE** (NASA, public, already processed) — glacier velocity time series
  - Shows sawtooth acceleration patterns correlating with retreat
  - Ice velocity data ends when glacier retreats past a point → can itself detect retreat
  - Some noise issues but overall good
- **Glacier thinning data** — separate from velocity, also public

**Parameters per slope (from Hig's email):**
- Ice face proximity over time
- Episodic retreat characterization (detect episodes from velocity/extent data)
- Has glacier reached minimum since 1850? (binary, requires hand-mapping)
- Thinning parameter
- Flow properties: velocity, curvature
- "Glacier reach" concept (section of glacier influencing a given slope)

**Hig's assignment:** "Explore the ITS_LIVE data. Build tools to ingest and visualize it. Produce outputs that show the data in interesting ways."

**Status (done):** ITS_LIVE ingestion + visualization shipped (`glacier/00–20`). Per-zone
glacier context extracted (`glacier/30_enrich_zones.py`) and wired into Scarp as a
scoring signal (`glacier/40_rerank_zones.py`, W_GLACIER=0.15), the API
(`/api/layers/glacier_velocity` + per-zone glacier block), and the frontend (zone-detail
panel + optional velocity layer). Robust velocity-trend regression (fixed a 1000× unit
bug). **Still open:** episodic-retreat detection, post-1850-minimum flag, thinning data,
glacier-reach segmentation, and the full Bayesian probabilistic model (Korup).

### 2. Topography

- Slope, relief, aspect, convexity
- USGS 90m product may suffice, or rebuild own
- Already partially implemented in Scarp (slope from DEM, relief from DEM)

### 3. Rock Type (lower priority)

- DGGS analysis, RockD, AK Faults and Folds
- Key idea: assume similar rock = similar failure patterns (different from USGS/DGGS approach)

### 4. Permafrost

- Gruber 2012 dataset — dated, coarse resolution hides topographic variability
- Hig has a method to deal with coarse resolution (TBD)

### 5. Landslides as Risk Factor

- Both slow (m/yr) and catastrophic events
- Probability cone declining with distance from known events
- Could integrate other factors into "closeness" (same glacier, same rock type)
- InSAR + feature tracking may soon detect slow slides

---

## Calibration Dataset

Hig's inventory: 120+ landslides since 2012, paper just submitted.
- Red = slow (m/yr)
- Dark blue = catastrophic + recent
- Size cutoff ~1M m³
- This IS the calibration dataset for the probabilistic model

---

## Key Case Studies

- **Barry Arm:** Three slopes started moving simultaneously after glacier retreat. Already monitored → ranks low on Scarp but high for understanding mechanism
- **Tracy Arm (2024 tsunami):** Same double-retreat pattern. Sawtooth velocity acceleration in ITS_LIVE data
- **Seldovia (Hig's hometown):** Published hazard assessment assumes extreme scenario (~1 in 100,000/yr) but never states probability. Motivates probabilistic approach

---

## Collaboration Notes

- **Hig:** Field season = summer → slower responses. Welcomes criticism.
- **Ollie Korup (Potsdam):** Bayesian statistics expert. To be looped in for calibration framework.
- **Scarp integration:** Probabilistic outputs should eventually feed back into the ranked map. But focus on hazard first — vulnerability is straightforward ("if probability is high near cruise ships, we know it's scary")

---

## Execution Rules

- One branch per major component
- ITS_LIVE ingestion tool is the first concrete deliverable
- Follow Scarp coding standards (no hardcoded strings, config classes, fail-fast)
- Python 3.12, GeoPandas, rasterio stack (same as Scarp prep/)
