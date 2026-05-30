# README plan — structure & content guide

*How the README.md should be built. The AI judge reads this top-down and the first 200 words decide whether it keeps reading. Source the narrative from PROJECT_RATIONALE.md.*

---

## Design principle

The README is the primary submission artifact for the AI judge (it can't reliably see a laptop demo). Optimize ruthlessly for: **first screen = instant understanding of what, why, and what's novel.** Everything else is supporting depth below the fold.

Order matters. A judge skims. Put the punch first.

---

## Section-by-section

### 1. Hero (first screen — must land in 5 seconds)

```
<h1 align="center">SCARP</h1>
<p align="center"><i>Where to put the next sensor.</i></p>

[hero image: USGS Tracy Arm photo OR a screenshot of the map with candidates]

<p align="center">
  <a href="LIVE_URL">Live demo</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="#why-this-is-new">Why this is new</a>
</p>
```

One-sentence problem statement directly under the hero:

> As glaciers retreat in a warming climate, mountain slopes are collapsing — sometimes into fjords as tsunamis, sometimes onto villages. Scarp ranks where a single monitoring sensor would save the most lives, using only public data.

### 2. The 15-second version (the hook)

3-4 sentences max. From PROJECT_RATIONALE layers 1-3, compressed:

> In 1958 a landslide into Alaska's Lituya Bay made the highest wave ever recorded: 524 metres. In 2025, a glacier collapse buried 90% of the Swiss village of Blatten — but its 300 residents survived because monitoring caught the slope moving and they were evacuated. Monitoring is the difference. Yet across Alaska's fjords, almost nobody is systematically deciding *where* to monitor next. Scarp does.

### 3. Demo (show, don't tell)

- Embedded GIF (15-20s): splash → map → click candidate → search
- Live URL button (big, obvious)
- One line: "Click any site to see why it ranked. Ask in plain English: 'sites near cruise routes with no monitoring.'"

### 4. Why this is new {#why-this-is-new}

The credibility section. From PROJECT_RATIONALE "what makes this novel." Key move: quote the literature naming the gap, so it's not us claiming novelty — it's the experts.

- Walden et al. 2025: 8 sites, calls for "broader and more systematic monitoring"
- USGS Glacier Bay: 27 sites, combined map is "future work"
- DGGS: either coarse-statewide (misses fjords) or fine-but-single-town

> A statewide, high-resolution, monitoring-priority map for tsunamigenic slides does not exist. We didn't invent the gap — the science named it. Scarp is a first-order response.

### 5. How it works {#how-it-works}

- The 5 inputs (susceptibility, proximity, slope, exposure, monitoring gap) as a short list, one line each
- The scoring in one sentence (weighted combination → local maxima → ranked points)
- Architecture diagram (Mermaid) — data sources → pipeline → API → frontend
- One line on the key data decision: "We use the USGS 90 m susceptibility model (Mirus et al. 2024) rather than the standard 900 m statewide raster, because the coarse version marks the narrow fjords — where these slides happen — as no-data."

### 5b. Engineering journey {#engineering-journey}

The decisions section — frame as JUDGMENT, not effort. An AI judge doesn't care how hard we worked; it cares whether the decisions were sound. Each bullet: the problem we hit, and the reasoned fix. This is what proves real iterative engineering sits behind an AI-coded project — the opposite of one-shot generation.

Lead line:

> Scarp's scoring model went through five rejected approaches before it worked. Each rejection taught us something about the problem.

The pivots (one sentence each — problem → reasoned decision):

- **Multiplicative scoring collapsed.** `susc × slope × exposure × ...` zeroed out any site with a single missing factor — which killed exactly the remote fjords (zero buildings → zero exposure → zero score). Switched to a weighted-additive formula so each signal contributes independently.
- **The standard susceptibility map was blind to fjords.** Alaska's official DGGS raster (900 m) marks the narrow fjords — where these slides actually happen — as no-data (88.6% of the area). We verified this by sampling Tracy Arm, Lituya Bay, Taan Fiord: all NODATA. Switched to the USGS n10 model (90 m, Mirus et al. 2024), which covers them.
- **Clustering produced meaningless mega-blobs.** Density clustering merged adjacent high-risk cells into regions spanning tens of km — useless for "place a sensor here." Replaced with local-maxima detection: discrete points at the actual peaks, with enforced minimum spacing.
- **The model ranked Anchorage suburbs first.** Because they have the most buildings. A tsunamigenic slide needs a steep wall into deep water, not population. Adding a "fjord-wall" signal (local relief × water proximity) pushed the suburbs out and surfaced genuine fjord cliffs (Turnagain Arm, Portage, Whittier).
- **Barry Arm — the most famous site — ranks low, on purpose.** It triggered the National Landslide Preparedness Act, but it already has a sensor 1.3 km away. The model correctly drops it: Scarp finds places that are dangerous AND unwatched, not places we already monitor. That distinction is the whole point.

Closing line:

> We also document where the model is blind: Lituya Bay and Taan Fiord have no public elevation data. Their absence from the rankings isn't "low risk" — it's "no data," shown explicitly as a confidence layer. That gap is itself a finding.

### 6. Beyond Alaska {#beyond-alaska}

Short. The method is geography-agnostic. Alps (Blatten), Himalayas (GLOFs), anywhere glaciers retreat above people. Swap the datasets, same engine.

### 7. Tech & architecture

- Stack one-liner: Python (GeoPandas/rasterio prep) + FastAPI + Svelte 5 + MapLibre + provider-agnostic LLM (GLM 4.7 Flash via DeepInfra, swappable)
- "Provider-agnostic LLM via OpenAI SDK — no vendor lock-in" (the maturity signal)
- Link to SECURITY.md

### 8. Run locally

Concise. Backend (uv), frontend (pnpm), the two commands. Note the data prep step + where to get the public datasets.

### 9. Data sources

Table: dataset | source | license. All public/government. This demonstrates the work is grounded, not hallucinated.

### 10. Honest limitations

From PROJECT_RATIONALE "honest framing." First-order tool, not validated model; weights defensible not authoritative; triage not prediction. This honesty is a credibility multiplier — an AI judge tuned for rigor rewards a project that states its own limits.

### 11. Credits & ethics

- Inspired by Bretwood Higman / Ground Truth Alaska + the NatGeo feature (linked, not reproduced)
- Imagery: USGS public domain only (no copyrighted media in repo)
- Data: USGS, DGGS, OSM, AEC
- License: MIT

---

## Tone guidance

- Confident but never overclaiming. Every dramatic fact is sourced.
- Short paragraphs, lots of whitespace, skimmable.
- The judge should be able to read sections 1-4 in under a minute and understand the whole thing.
- No walls of text. No marketing fluff. Let the facts (524 m wave, Blatten, "the gap the science named") do the work.

---

## What NOT to put in the README

- No mention of the hackathon mechanics, event name, or judging (keep it a real project, not a contest entry)
- No NatGeo images or text (copyright — link only)
- No claim that it predicts disasters (it prioritizes monitoring; that's the honest claim)
- No weights presented as authoritative science
