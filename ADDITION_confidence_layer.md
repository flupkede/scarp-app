# Production addition — Data Confidence / Coverage layer

**Add to:** AGENTS_phase-2.md (compute) and AGENTS_phase-4.md (display)
**Why:** Turns the project's biggest weakness (sparse data in famous fjords like Lituya Bay) into an honest, visible second finding. Pre-empts the jury question "why isn't <famous site> in your top list?" and supports the pitch that public data is itself insufficient — exactly what the Walden 2025 / Patton 2023 papers argue.

---

## Concept

Two findings, both valuable, both shown on one map:

1. **Candidate points (red/amber):** "Place a sensor here." — where the data supports a confident recommendation.
2. **Data-confidence layer (grey gradient):** "We are blind here." — where public data is too thin to assess, so a low/absent score is NOT evidence of low risk.

The honest message: a famous site (Lituya Bay) being absent from the top list may mean the data is missing, not that the risk is low. The confidence layer shows which it is.

---

## Phase 2 — Compute the confidence raster

Add a step (e.g. `prep/45_confidence.py`, runs before scoring) producing a per-cell **data confidence** value on the same grid as the score.

### Definition (defensible, not hand-wavy)

For each analysis cell, count how many input layers have VALID data there:

```python
layers_present = (
    susceptibility_valid          # USGS n10 has a real value (>0, not nodata sentinel)
  + dem_present                   # a DEM tile covers this cell
  + slide_inventory_within_25km   # at least one inventory feature nearby
  + osm_data_present_within_10km  # any OSM features at all
  + coastline_data_present        # coastline geometry exists for this area
)
confidence = layers_present / 5.0   # 0.0 = blind, 1.0 = all inputs present
```

This measures DATA AVAILABILITY, not score. A cell can have full confidence and a low score (genuinely low risk). A cell can have low confidence with an unreliable score. The two layers answer different questions.

### Output

- `data/processed/confidence.geojson` — polygonized into 3 coarse bands:
  - low (confidence < 0.4) — "data-limited, low trust"
  - medium (0.4–0.7)
  - high (> 0.7) — "well-covered, score is trustworthy"
- Dissolve into a few big polygons so it renders as a soft overlay, not 700k cells.

### Honest reporting

When scoring runs, also print:
> "X% of the analysis area is high-confidence; Y% is data-limited. Known sites in data-limited areas: [list]."

This line goes into the README and the pitch.

---

## Phase 4 — Display the confidence layer

### Visual treatment

- A toggleable layer (default ON), below the candidate points in z-order.
- Low-confidence: light grey hatch / diagonal-line pattern, ~30% opacity — must read as "no data" not "low risk" (solid grey could be misread as a value).
- Medium: very faint.
- High-confidence: no overlay (clean basemap = "we can see here").
- Legend addition: "▨ grey hatch = data-limited; recommendations here are low-confidence."

### Interaction

- Clicking a candidate in/near a low-confidence zone shows in the detail panel: "Note: data coverage here is limited — treat this ranking as provisional."
- Optional: labelled reference pins for known sites (Lituya Bay, Taan Fiord, Tracy Arm, Barry Arm). If one falls in a grey zone, that tells the whole story visually.

### The pitch moment this enables

> "The red points are where to look. The grey is where we can't yet — including Lituya Bay, site of the tallest wave ever recorded. That grey isn't safety. It's the gap in public data. Scarp shows both where to act and where to measure first."

---

## Why this is the right call (objective)

- Defensive: answers "why isn't <famous site> in your top?" before it's asked.
- Honest: distinguishes "low risk" from "unknown" — a distinction the current map can't make.
- Scientifically aligned: Walden 2025 and Patton 2023 explicitly say systematic data/monitoring is lacking. This makes that concrete.
- Cheap: reuses data-validity checks already done during scoring; it's bookkeeping, not new data.

## What to avoid

- Do NOT make the grey layer look like a risk heatmap — it must read as "no data," use a hatch/pattern and label it explicitly.
- Do NOT conflate data confidence with prediction accuracy — the note says data coverage, not that the prediction is correct.
