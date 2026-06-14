# Scarp — Research Roadmap & Collaboration Brief

> The scientific plan for evolving Scarp from a *susceptibility heatmap* into a
> **calibrated landslide-likelihood tool** for SE Alaska, built in collaboration
> with geologist Bretwood "Hig" Higman. This is the capture-everything companion
> to `AGENTS.md` (which stays the project/engineering reference).
>
> **Sources:** email thread (Filip ↔ Hig, Jun 2026) + the 2026-06-05 Zoom call.
> Nothing here is implemented yet unless a phase says so.

---

## 1. Collaboration context

| Who | Role | Notes |
|---|---|---|
| **Hig** (Bretwood Higman) | Domain expert, inventory owner | Independent geologist. Summer field season starting → expect **slow async responses**. Invites blunt criticism of his code. |
| **Ollie Korup** (Potsdam) | Bayesian/statistics validator | Loop in *"once we have a bit more to show"*. Closer to Filip (EU) than Hig. Not needed to start — needed to validate before any claims. |
| **Jane** (Switzerland) | Co-author, 8-landslide ITS_LIVE paper | On parental leave. Has a Portage-glacier paper coming. → **obtain & read her paper.** |
| **Filip** | Builder | Developer, not geologist. Wants to build what genuinely helps Hig, guided by the science. |

### Repos & data (local)
- **Hig's app** (Django inventory viewer): `C:\WorkArea\AI\landslidescience`. Public GitHub URL TBD. Self-described "vibe-coded", sole contributor Claude Code.
- **Scarp** (our base): this repo.
- **Hig's inventory export**: `C:\WorkArea\AI\landslide_eval\landslidescience_inventory_260613` — already ingested → `hig_landslides` / `hig_polygons` / `hig_survey_circles`.

### Strategy (locked)
> Build the **modernized base in Scarp**. Absorb as much of Hig's functionality as
> possible (his data + filters + viewer features), modernized, and implement the
> mail+call roadmap — approximating current functionality on **both** sides. Intent
> is to **converge toward landslidescience.org later**. Do **NOT** fork/branch onto
> Hig's repo now.

---

## 2. The reframe: probability, not susceptibility

Hig's core scientific stance (repeated, emphatic) — this is Scarp's north star:

- Susceptibility maps (incl. USGS) are **qualitative** and refuse to commit to a
  probability. A "60" means nothing. *"What's the probability a slope with
  susceptibility X fails? Oh, we aren't doing probabilities."*
- Goal = an **actual annual probability with an honest, wide uncertainty band**
  (his example: 1-in-1,000/yr, band 1-in-10,000 … 1-in-100), **calibrated on the
  N≈120 inventory** (enough to calibrate; Reginald had ~4, Jane's paper 8).
- *"Coming up with a specific number, even with big uncertainties, is very
  important. Then you at least know what you're looking at."*
- USGS is a **negative example, not a foundation**: their model misses a real
  hotspot Hig mapped independently, and scores a <30° slope low that failed
  catastrophically. Keep it as *one candidate factor*, don't anchor on it.

**Consequence for Scarp:** the current weighted-additive 0–1 score with
hand-set weights is conceptually the wrong end-state. It must evolve toward a
**calibrated likelihood**. Until then, label the current ranking honestly as an
**"uncalibrated heuristic."**

---

## 3. Scientific hypotheses to test

### H1 — "Double retreat" predicts landslides (the headline bet)
- Tidewater glaciers sit for decades on **pinning points / sills**, thin, then on
  losing support → **runaway retreat**. Retreat **past a Holocene-stable point**
  (a position unoccupied for ~10,000 yr) exposes slopes buttressed + undercut for
  that whole time → primed to fail.
- **Two distinct physical roles:** (1) mechanical **buttressing/support**;
  (2) **erosion/undercutting** at the toe.
- Field evidence: Barry Arm, Tracy Arm, a 2024 slide just as the glacier retreated
  back to a point. **Opposite-valley slopes failed in quick succession** → points
  to the *glacier* (not lithology) as driver.
- Must be **shown unbiased and statistically tested** — guard against confirmation
  bias on anecdotes.

### H2 — Velocity sawtooth as a candidate standalone factor
- ITS_LIVE shows accelerate/decelerate sawtooth; accelerations coincide with rapid
  retreat. Speculation: glacier presses on a slope (Tracy Arm 90° bend); retreating
  off it → loses back-pressure → speeds up *and* stops supporting the slope. So
  **velocity acceleration may itself be a risk factor.** Put it in; let stats decide.

### H3 — Landslides as a risk factor for landslides ("probability cone")
- A known landslide raises the probability of catastrophic failure on **nearby**
  slopes: **peaks at the existing slide, declines gradually outward** (not to zero
  at an edge). Parameterized by **height + width** of the cone.
- Possible refinement: warp "closeness" by context (same glacier / same rock type
  = closer) — **anisotropic distance** (see §5).

---

## 4. Phased roadmap

### Phase 0 — Base + reframe ✅ direction set
- Scarp = modernized base. Relabel current score as **uncalibrated heuristic**;
  target = calibrated probability. (Inventory + survey circles already ingested.)

### Phase 1 — ITS_LIVE exploration + instrument shell *(the homework, START HERE)*
ITS_LIVE ingestion already exists; this phase is about **exploration depth** + the
tools to *look* at the data. Note: **ITS_LIVE = velocity, NOT ice-front/retreat.**
- Per-glacier velocity **time series**, seasonal signal, **sawtooth detection**,
  data-gap-as-retreat signal, trends — "interesting outputs to get hooks in it."
- Visuals: velocity-field layer, time-series charts, acceleration-episode markers.
- **Instrument shell** (needed to look at the ice): basemap switcher with
  **multi-temporal imagery** (USGS / Sentinel-2 / historical), before/after swipe,
  layer control. (Port of Hig's `basemaps.js` patterns to SvelteKit.)
- **By hand:** trace ice-front retreat for **Tracy Arm + Barry Arm** as ground truth.

### Phase 2 — Glacier retreat as a model input (H1 + H2)
- Ice-front position over time: **hand → automate → verify** (verify the algorithm
  reproduces the hand-mapped fronts before trusting it elsewhere).
- Detect **episodic / "double" retreat** past Holocene pinning points.
- **Glacier "reach"** segmentation → meaningful proximity (vs raw linear distance),
  both to landslides and to the glacier front.
- Velocity sawtooth as a candidate factor.
- Distance-to-ice-face (up-glacier and down-fjord); keep **buttressing vs erosion**
  as separate variables.

### Phase 3 — Modernize Hig's inventory features into the base
- **Color classes:** slow = red (≈ m/yr); catastrophic + since-2012 = dark blue;
  older = gray-blue. **Size cutoff ≈ 1M m³** (via area cutoff).
- **Filters:** class toggles, size/volume filter, **running count** of filtered set
  (Hig's app lacks the straight total — easy win).
- **N10/LW scatter** analysis: terrain density vs where landslides actually occur
  (find the off-diagonal outliers).
- Per-landslide popups with imagery (before/after; Planet/SAR where licensing
  allows — Planet Labs is proprietary, can't freely embed).
- **Faults layer** (AK Quaternary Faults & Folds, DGGS DDS 3 / Koehler).

### Phase 4 — Likelihood rubric + calibration *(science core, validate with Korup)*
- Represent each factor **spatially with uncertainty**: topography (slope, relief,
  aspect, convexity); **landslide-as-risk-factor** (probability cone, height+width);
  glacier dynamics (H1/H2); **permafrost** (Gruber 2012, mind coarse-resolution
  caveat); **rock type** (later — DGGS / RockD / faults; assume similar rock → similar
  failure).
- **Calibrate to N≈120** → real probabilities with honest uncertainty bands.
- **Bayesian / hierarchical**, strong priors, **ruthless feature parsimony**,
  **spatial cross-validation**, model selection (let stats prune e.g. velocity).
- Filip builds & runs end-to-end; **Korup reviews before any claim is published.**

### Phase 5 — Tsunami extension + vulnerability *(later)*
- **SPLASH** (Lyell SP477.1) to extend hazard over water; **100M m³ flat first-pass**.
- **Vulnerability** (hazard-first, this later): roads, **AIS ship traffic**,
  dispersed remote population. Hig recruiting economists for this side.

---

## 5. Methodology notes (glossary — agreed definitions)

- **Hand → automate → verify** — map a few cases by hand (ground truth), build the
  automation, then confirm it reproduces the hand result before trusting it broadly.
  Guards against plausible-but-systematically-wrong automation.
- **Circularity** — using the same data to both *define* a predictor and *test* it,
  so the model trivially predicts itself. Mitigate: hold-out / spatial / temporal
  splits, especially for landslide-as-risk-factor.
- **Spatial cross-validation** — split train/test by **geographic blocks**, not
  randomly, because landslide data is spatially autocorrelated. Honest estimate of
  prediction on *unseen* fjords (the screening use-case). Random CV overstates skill.
- **Isotropic → anisotropic** — start with plain Euclidean distance; add
  context-warped distance (same glacier/rock = closer) **only if** it improves
  out-of-sample fit. The data decides via model comparison, not a priori.
- **Bayesian calibration ownership** — Filip builds/runs (PyMC/Stan, hierarchical,
  priors, posteriors, spatial CV, model comparison). Korup validates priors,
  physical sense, subtle traps, and lends peer credibility.
- **Honest uncertainty** — every factor and the final probability carries an
  uncertainty band. Wide bands early are fine *if honest*. "Garbage in, garbage out"
  acknowledged explicitly.
- **Hazard first, vulnerability later** — the probabilistic-hazard path is clearer;
  vulnerability is important but deferrable.

---

## 6. Critical caveats / risks

- **Circularity** in landslide-as-risk-factor → mandatory spatial/temporal hold-out.
- **Thinning ≠ velocity.** ITS_LIVE = velocity. Thinning needs an elevation-change
  product (currency is the real question Hig raised). **Retreat data does not exist
  — we must generate it.** Hig offers his **measured-thinning dataset**.
- **Planet Labs is proprietary** → not freely embeddable. ITS_LIVE / Sentinel-2 /
  USGS are fine.
- **Overfitting / identifiability** — many correlated factors vs ~120 events. Strong
  priors + parsimony + spatial CV. This is where Korup matters.
- **Confirmation bias** — H1 rests partly on Hig's anecdotes; test it unbiased.
- **Norway stats don't transfer** — Alaska may be ~100× more failure-prone per area.
  Use Norway's numeric risk thresholds (e.g. 1-in-10,000/yr build-a-hospital line)
  as *decision anchors*, not as base rates.

---

## 7. Data inventory

### Have
- Hig inventory export (landslides / polygons / survey circles) — ingested.
- ITS_LIVE velocity (glacier pipeline). USGS n10 susceptibility. DEM, OSM buildings/
  roads, AEC seismic stations. Scarp's relief, fjord-wall, volume-proxy, confidence.

### Need / to obtain
- **Hig's measured-thinning dataset** (offered).
- A **generalized glacier-thinning product** (elevation-change; check currency).
- **Jane's 8-landslide ITS_LIVE paper** + her Portage paper.
- **AK Quaternary Faults & Folds** database (for faults layer + rock proximity).
- Hig's **public GitHub repo URL** (when he shares it — "don't post on social yet").
- Later: **AIS ship-traffic**, **DGGS rock analysis**, **RockD**, ITS_LIVE n10/lw lw-raster.

---

## 8. Open decisions / next actions

1. **Phase 1 kickoff** — ITS_LIVE exploration outputs + instrument shell, on a new
   branch. (Awaiting go.)
2. Obtain the data marked "need" above from Hig as he surfaces over the summer.
3. Confirm whether to also vendor Hig's USGS **lw** raster (he uses n10 *and* lw;
   Scarp currently only n10).
4. Korup loop-in timing: after Phase 1–2 produce something visual to show.
