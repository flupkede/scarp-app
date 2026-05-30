# Scarp — Project Rationale & Vision

*The "why" behind the project. Source material for the README, the pitch, and the about page. Every factual claim here is verifiable — see sources at the bottom.*

---

## One-line essence

Scarp finds the places where a single, cheap monitoring sensor would matter most — in a warming world where retreating glaciers are turning mountain slopes into killers, and almost nobody is systematically looking for the next collapse before it happens.

---

## The problem, in three layers

### Layer 1 — The slopes are failing, and it's accelerating

As glaciers retreat, the valley walls they used to support lose their buttress. Meltwater seeps into the freshly exposed rock. Permafrost that held slopes together thaws. The result: large, deep-seated landslides that were rare are becoming common. Alaska accounts for roughly a quarter of global glacier mass loss this century despite holding only ~12% of the world's glacier volume. It is a hotspot, and the rate of large slope failures there has risen sharply over the past decade.

### Layer 2 — When these slopes hit water, the slide becomes a wave

A landslide on a dry hillside is a local tragedy. A landslide that drops into a fjord, lake, or inlet displaces water and becomes a tsunami that can travel kilometres and strike communities far from the slide itself.

- **1958, Lituya Bay, Alaska:** a rock slide into the bay generated the highest wave ever recorded on Earth — 524 m of runup.
- **2015, Taan Fiord, Alaska:** a slide sent water 193 m up the opposite slope and stripped forest from eight square miles.
- **2020, Barry Arm, Alaska:** a citizen scientist spotted a 455-million-cubic-metre slow-moving slope above a fjord. Modeling suggested a collapse could produce a 300 m runup near local communities. The discovery triggered the U.S. National Landslide Preparedness Act response and a multi-agency monitoring program.
- **2024-2025, Alaska:** slides in Surprise Inlet, Kenai Fjords, and Tracy Arm all generated tsunamis — **none were on any state or federal watchlist.**

### Layer 3 — Almost nobody is looking ahead

The recurring pattern in the science: these slopes are studied **after** they fail. The 2020 Barry Arm discovery — by a citizen scientist, not an agency — is the canonical example of how a catastrophic hazard sat unwatched until someone happened to look.

Independent geologist Bretwood "Hig" Higman is one of the few systematically searching for the next one. He builds his own low-cost monitoring sensors (on the order of a few hundred dollars each) and installs them by hand. He works alone or with one or two helpers. He cannot be everywhere. **He has no map telling him where the next sensor would matter most.**

---

## What Scarp does

Scarp combines public datasets to rank candidate locations for monitoring sensor placement across Southeast Alaska:

- **Susceptibility** — where the terrain is steep and prone to failure (USGS high-resolution 90 m model, Mirus et al. 2024)
- **Proximity to known slides** — places near documented failures (DGGS landslide inventory, ~40,000 features)
- **Slope** — the actual steep faces, from a 10 m digital elevation model
- **Exposure** — people, roads, ferry routes, tourism in the danger zone below (OpenStreetMap)
- **Monitoring gap** — where there is currently NO sensor coverage (Alaska Earthquake Center stations)

The output is not a heat map of "danger everywhere." It is a short, ranked list of specific points: *here is where to hang the next jar, and here is why.*

---

## What makes this genuinely novel

This is the core of the pitch, and it is verifiable, not marketing:

**A statewide, systematic monitoring-priority method for tsunamigenic/paraglacial slides in Southeast Alaska does not exist.**

The scientific record says so directly — these are the exact, verified quotes:

- **Walden et al. 2025** (NHESS, vol. 25, pp. 2045-2073, doi:10.5194/nhess-25-2045-2025) — co-authored by Bretwood Higman himself. The abstract states the work "further substantiate[s] the need for establishing broader and more systematic paraglacial hazard monitoring in a warming world." The study examined just **8 landslides**.

- **Patton et al. 2023** (NHESS, vol. 23, pp. 3261-3284) — states plainly that "no systematic landslide warning threshold currently exists at either local scales for towns within southeast Alaska or the regional scale for southeast Alaska as a whole, despite its high susceptibility to slope failures."

Two independent peer-reviewed papers, one with Higman as author, both naming the same gap: there is no systematic, regional approach to prioritizing where to watch.

**The honest precision of the claim (important — do not overclaim):**

The gap is NOT "nobody monitors anything." Individual sites ARE monitored — Barry Arm has had instruments since 2020, and a December 2025 study (Davy et al., Seismological Research Letters, doi:10.1785/0220250205) even found new seismic precursor signals there. Sitka has a rainfall warning system.

The real gap is this: **sites get monitored AFTER they are individually discovered (often by chance, as Barry Arm was in 2020). There is no systematic method to decide which of the thousands of un-watched slopes deserves a sensor next.** That triage step — "where do we look that we aren't already looking?" — is what does not exist, and what Scarp provides.

**We did not invent the gap. Two peer-reviewed papers named it. We built a first-order response.**

---

## Why this matters beyond Alaska — the climate connection

The mechanism is not Alaska-specific. It is what happens to any glaciated mountain range in a warming climate: glaciers retreat, slopes lose support, permafrost thaws, rock fails.

- **The Alps:** On 28 May 2025, the village of Blatten in Switzerland's Lötschental valley was destroyed — roughly 90% of it buried under about 3 million cubic metres of rock and glacier ice after the Birch Glacier collapsed. There was no tsunami; there didn't need to be. A mountain fell on a village. Crucially, the ~300 residents had been evacuated nine days earlier because monitoring detected the developing slope instability. Monitoring is the difference between a near-miss and a massacre. (Note: Blatten was destroyed exactly one year before this project's hackathon date.)
- **The Himalayas:** glacial-lake outburst floods and rock-ice avalanches threaten downstream valleys home to millions. The same retreat-debuttress-fail mechanism, at vastly larger human scale.
- **Patagonia, the Caucasus, New Zealand's Southern Alps, Norway's fjords:** every glaciated range with people downhill faces a version of this.

Scarp's method — combine susceptibility, slope, proximity-to-water-or-valley-floor, human exposure, and monitoring-coverage gaps to rank sensor placement — is geography-agnostic. Swap the input datasets and the same engine prioritizes monitoring sites in the Alps, the Himalayas, or anywhere a warming climate is destabilizing slopes above people. Alaska is the proving ground because the data is open and the hazard is acute. The approach travels.

---

## The honest framing (so we never overclaim)

- Scarp is a **first-order prioritization tool**, not a validated hazard model. It points attention; it does not predict.
- The scoring weights are defensible but not authoritative — a real deployment would calibrate them against expert input.
- It is built on public data with known limitations (resolution, coverage, currency).
- Its value is **triage**: turning "the whole coast is dangerous" into "look at these twenty spots first."

This honesty is a strength. It is the difference between a tool a scientist might actually use and a black box they would rightly distrust.

---

## The closing line (for the pitch)

"Hig has cheap sensors and an infinite coastline. The science says nobody has mapped where to put them. So we did. And the same map can be built for the Alps, the Himalayas, anywhere a warming world is turning mountains into hazards."

---

## Sources (all verifiable)

- Lituya Bay 1958 runup (524 m): widely documented, USGS.
- Taan Fiord 2015: Higman et al. 2018; Dufresne et al. 2018.
- Barry Arm 2020: Dai et al. 2020, *Geophysical Research Letters*, doi:10.1029/2020GL089800.
- Alaska glacier mass loss (~25% of global): Hugonnet et al. 2021.
- Paraglacial landslide acceleration, 8 sites, call for broader monitoring: Walden et al. 2025, *NHESS*, doi:10.5194/nhess-25-2045-2025.
- Glacier Bay InSAR, 27 sites, "could be combined": Kim et al. 2022, *Remote Sensing of Environment*, doi:10.1016/j.rse.2022.113231.
- USGS high-res susceptibility (90 m, used as Scarp's susceptibility input): Mirus et al. 2024, *AGU Advances*, doi:10.1029/2024AV001214; data ScienceBase doi:10.5066/P13KAGU3.
- Blatten / Birch Glacier collapse, 28 May 2025, ~90% of village, evacuation 19 May: Nature *Communications Earth & Environment* 2025, doi:10.1038/s43247-025-02994-8; contemporaneous reporting (NPR, ABC, CBS, Copernicus).
- NatGeo feature on Higman: "Lessons of a landslide detective," Christian Elliott, May/June 2026.
  URL: https://www.nationalgeographic.com/environment/article/alaska-landslides-geologist-detective
  (Interview summary, free): https://www.numlock.com/p/numlock-sunday-christian-elliot-on
- Tracy Arm megatsunami (481 m runup, 10 Aug 2025, second-highest ever recorded):
  Science paper: Shugar et al. 2026, doi:10.1126/science.aec3187 — Hig is co-author.
  NASA Earth Observatory (before/after Landsat images, free to use): https://science.nasa.gov/earth/earth-observatory/tracy-arms-post-tsunami-landscape/
  USGS dedicated page (aerial photos by Cyrus Read + John Lyons/USGS, free to use): https://www.usgs.gov/programs/landslide-hazards/science/2025-tracy-arm-landslide-generated-tsunami
  Oxford press release: https://www.ox.ac.uk/news/2026-05-05-second-largest-megatsunami-triggered-long-lived-waves-in-alaska-fjord
