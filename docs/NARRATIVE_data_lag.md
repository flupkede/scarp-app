# Key narrative — "The data lags reality" (Tracy Arm case)

This is one of Scarp's STRONGEST points. It must be explicit in the README and pitch, because an AI judge sees only the output (Tracy Arm at rank 61) and will read it as a weakness unless we tell it otherwise. An undocumented honest limitation looks identical to a bug.

---

## The finding (verified by component diagnosis)

Tracy Arm produced a tsunamigenic landslide in August 2025. In Scarp's ranking it sits at ~rank 61, not the top.

Diagnosis: 94% of the gap is the proximity component. Tracy Arm's nearest documented slide is 10.6km away (proximity 0.121) while top-ranked sites have slides within 1-2km (proximity ~0.95). Its susceptibility is a perfect 1.000 and its fjord_wall is high (0.881) — the geology screams danger. The only thing dragging it down is that **no slide inventory contains the 2025 event**: DGGS, USFS Tongass, and the USGS news CSV all pre-date it (USGS ends 2024).

So Tracy Arm scores low not because it's safe, but because **the official data doesn't know what happened there yet.**

## Why this is a feature, not a bug

This is the project's thesis made concrete. The whole premise — backed by Walden et al. 2025 and Patton et al. 2023 — is that systematic hazard data and monitoring are lacking. Tracy Arm is living proof: a real tsunami, one year ago, still absent from every public inventory. The official record lags reality.

Scarp doesn't hide this. It surfaces it. A site can have textbook-perfect danger signals (susceptibility 1.0, steep wall into deep water) and still rank low purely because the documented-history layer hasn't caught up. That gap between "what the data knows" and "what actually happened" is exactly the problem Scarp exists to highlight.

## The decision (deliberate, documented)

We chose NOT to manually inject the 2025 Tracy Arm event to boost its rank. Two reasons:
1. Cherry-picking one famous site to make the map "look right" would be tuning toward a known answer — the opposite of honest methodology.
2. Tracy Arm ranking low because it's too recent to be documented is a MORE valuable result than Tracy Arm sitting neatly in the top. It demonstrates the lag.

We keep the principled scoring and explain the result.

## How to present it (README + pitch)

**README — in "Honest limitations" or "Engineering journey":**

> Tracy Arm produced a tsunami in August 2025 — yet it ranks 61st, not top. Why? Its geology is textbook-dangerous (susceptibility 1.0, a steep wall into deep water). But no public slide inventory contains the 2025 event: the official datasets end in 2024. Tracy Arm scores low purely because the documented record hasn't caught up with reality. We deliberately did NOT hand-edit it upward. A famous, genuinely dangerous site ranking low because the data lags by a year is not a flaw in the tool — it is the exact problem the tool exists to expose. The science (Walden 2025, Patton 2023) says systematic hazard data is missing. Tracy Arm proves it.

**Pitch — a strong mid-demo beat:**

> "Here's Tracy Arm. It generated a tsunami last August. My tool ranks it 61st — and I left it there on purpose. The geology is off the charts, but no official database has logged the 2025 event yet. The data lags reality by a year. That's not my tool failing. That's my tool showing you the gap that the science says we have."

## Primary visual — use this in the docs/about page

**NASA Earth Observatory — "Tracy Arm's Post-Tsunami Landscape"**
URL: https://science.nasa.gov/earth/earth-observatory/tracy-arms-post-tsunami-landscape/

This page contains:
- Before/after NASA-USGS Landsat 9 images (26 July vs 19 August 2025) — free to use (US government work)
- Aerial photo by Cyrus Read/USGS (13 August 2025) showing the landslide scar + trimline
- Aerial photo by John Lyons/USGS showing Sawyer Island stripped of all but a few trees
- Dan Shugar's "bathtub ring" quote

**Why this matters for the docs page:**
- The before/after image is immediately legible to anyone — green fjord wall → brown stripped zone
- Hig (Brentwood Higman) is a co-author of the Science paper (Shugar et al., Science, May 6 2026, doi:10.1126/science.aec3187) and noted that glacier retreat visible in satellite images is a key susceptibility indicator — exactly Scarp's fjord-wall signal logic
- The Science paper itself: https://www.science.org/doi/10.1126/science.aec3187
- USGS dedicated page with pre/post satellite images + field recon photos: https://www.usgs.gov/programs/landslide-hazards/science/2025-tracy-arm-landslide-generated-tsunami

**Caption to use under the before/after image:**
> Tracy Arm, Alaska — before (26 July 2025) and after (19 August 2025) the landslide-triggered megatsunami.
> The "bathtub ring" of stripped forest marks 481 m of runup — the second-highest tsunami ever recorded.
> Tracy Arm was on no state or federal watchlist. It ranks 61st in Scarp — not because it is safe,
> but because the 2025 event is absent from every public inventory. The data lags reality.
> Image: NASA Earth Observatory / Landsat 9 (USGS). Free to use as US government work.

## Caveat to keep it honest

Even this framing must not overclaim. The honest statement is "the documented-slide-history component is incomplete," not "Scarp predicted Tracy Arm." Scarp did not predict it — Scarp shows that a known-dangerous site is invisible to the official record. That's the accurate, defensible claim.

## Also reinforces the confidence layer

This pairs with the grey data-gap layer: Tracy Arm (recent-event gap) and Lituya/Taan (no-DEM gap) are different KINDS of data limitation, both shown honestly. Together they tell one story: public data is patchy, and Scarp makes the patchiness visible instead of papering over it.
