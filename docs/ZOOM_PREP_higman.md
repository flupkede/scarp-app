# Zoom prep — call with Hig Higman

**Time:** Thursday 9 PM Alaska = Friday 7 AM Belgium. (Proposed; any evening this/next week works.)
**Goal:** not to defend Scarp — to learn where it fits and what to build next. Listen more than pitch.

---

## The one-line framing (lead with this)

> "I read Scarp as the *screening* step — which stretch of coastline deserves a sensor or a closer look — that sits **upstream** of a classification system like Hermanns. His system starts once you already know a slope is unstable. Mine tries to find the candidates from public raster data before anyone has been there."

This positions Scarp honestly: not a rival to Hermanns, not a finished hazard model — the step before both.

## The screening → activity → classification chain

1. **Screening** (where to look?) — public raster data → **this is Scarp**
2. **Activity detection** (is it moving here?) — InSAR, or a placed sensor → **Hig's mason jars sit here**
3. **Classification** (how dangerous?) — field structural work + activity → **Hermanns**

Scarp can help decide *where Hig puts the next jar*. That's the real connection to his work — not to Hermanns' Norwegian institutional setup.
**Ask, don't assert:** "How do you decide where to place a sensor now — and is that where Scarp would be most useful?"

---

## What I took from his two papers (shows I did the reading)

- **Hermanns is site-level, field-based, expert-judgement.** Nine criteria (structure + activity), scored, summed to a 0–12 hazard score, run through a decision tree, then a risk matrix (R = PF·PP·PE·V·E). The 2013 implementation is literally an **Excel/VB6 macro**.
- **The 2026 revision** moves from a *sum* to a *product* formula (M·A·F·K·Fa·V·E·P), collapses the 3 morphology criteria into one ("Freedom"), and **adds two new variables: Volume and Permafrost.** Permafrost is strong — LURS in permafrost move 2.1× more often; ~90% correlation with the last 40 years of failures.
- **Their own honesty point:** several recent failures (Polvartinden, Brenndalsbreen, Jolegruva) were *not recognised as unstable before they failed*, off near-vertical walls. So "it must already be visibly moving" isn't reliable — a humility point that applies to both of us.

## The three improvements his work points to (concrete, from his own literature)

1. **Fix the slope double-count → volume proxy.** He's right: Mirus N10 already encodes steepness, and I had added `slope_factor` on top. The fix isn't just to delete it — it's to **replace it with height × steepness** (a mass / volume proxy, `normalize(relief) × normalize(slope)`). His 2026 paper adds *Volume* as an explicit criterion for exactly this reason: small steep banks aren't tsunamigenic; tall steep walls are. One change removes the redundancy AND adds the variable I was missing. **(Done — `slope_factor` replaced by `volume_proxy` in the scoring pipeline; data regenerated.)**
2. **Add an activity signal via InSAR.** Scarp has *no* activity input — it scores static topography only. That's why it has false positives (thousands of steep slopes, most don't move). InSAR (OPERA / Sentinel-1 / future NISAR) is the missing variable, and it's exactly what he pointed me to. This is the biggest real improvement.
3. **Permafrost as a factor.** His 2026 paper and the Magnin et al. permafrost model make this tractable from public data. Candidate for the product formula later.

---

## Questions to ask him (let HIM talk)

- "What did you mean by Hermanns 'focusing on somewhat the wrong variables'?" *(My guesses — don't state them as fact: (a) Hermanns explicitly excludes earthquake-triggered failures, but Alaska is seismic — Lituya 1958 was quake-triggered; (b) it treats the displacement wave as a secondary effect, while for you the water interaction is primary. Let him confirm or correct.)*
- "Is an InSAR-derived movement signal the most valuable thing I could add, or would you start somewhere else?"
- "For Alaska specifically — how much does the priority shift toward quake-triggered failures vs the slow-deforming ones you can monitor?"
- **The big one:** "If I turned the Hermanns classification logic into real software — not an Excel macro, but a tool where you enter field observations and it computes the hazard score and risk matrix — do you have the kind of data that would feed it? Would that save you work?"

## The "papers are only papers" insight (raise if it fits)

His whole field runs on PDFs and an Excel macro. The gap isn't the science — it's that none of it is usable software. That's where I might actually be useful: not redoing the geology, but turning the method into a tool. That's what I already did with the Mirus data. *Only say this if the conversation opens to it — don't lead with "your field has no software," it reads as arrogant.*

---

## Calibration (honest — don't oversell)

- Hermanns is a mature, operational, 15-year-refined national system tied to building codes, applied to 120+ sites. Scarp is a weekend prototype. Keep that proportion in mind.
- I'm a developer, not a geologist. Say it once, mean it, then let the work speak.
- The strongest position is "I read your papers and here's what I take from them for the next step" — not "look what I built."
- If he points out something that breaks a Scarp assumption: thank him, write it down, don't defend. That's the whole value of the call.
