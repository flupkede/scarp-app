# Phase 2 + 4 addition — two-stage refinement & final visual schema

Locks in: (a) the two-stage scoring (coarse rank + fine placement), and (b) the final cartographic symbol/layer scheme. Replaces earlier mason-jar styling. "Science, not marketing."

---

## PART A — Two-stage scoring (Phase 2)

The ranking and the placement precision are TWO different problems. Solve them in two stages.

### Stage 1 — Ranking (coarse, 500m)

Determines WHICH fjord walls are priorities. Keep the proven v2 approach:
- 500m analysis grid
- weighted-additive formula: `0.25*susc + 0.25*fjord_wall + 0.20*proximity + 0.10*slope + 0.10*exposure + 0.10*(1-coverage)`
- local-maxima detection with ~10km min spacing
- coastal constraint
- susceptibility resampling: use Resampling.nearest or Resampling.max (NOT average) to preserve fjord-edge values

500m is fine for ranking — known fjords surface or not based on DATA availability, not cell size. The 90m full-grid run was tested and did NOT improve ranking (Tracy Arm got worse: 10.7km -> 19.1km). Do not use 90m for ranking.

### Stage 2 — Placement refinement (fine, per candidate only)

For EACH of the ~50 ranked candidates, refine its exact position. This is cheap (50 points, small windows — not 230M cells).

```
For each candidate point (center of its 500m cell):
    define a search window of +/- 500m around it (so ~1km box)
    within that window, read the FINE data:
      - n10 susceptibility at native 90m
      - DEM slope/relief at native 10m
    compute a local placement score = susc_90m * slope_10m (or the same
      weighted combo at fine resolution, minus the global components that
      don't vary at this scale like coverage)
    move the candidate point to the fine cell with the highest local score
    record the refined lon/lat (now ~10-90m precision instead of 500m)
```

Result: the ranking stays stable (500m), but each final point snaps to the steepest/highest-susceptibility spot on the actual wall. Hig gets meter-scale placement, not "somewhere in this 500m box."

**Pitch line this enables:** "Scarp ranks regions on a coarse grid for speed, then refines each recommendation to the exact slope cell with the highest local risk — so Hig knows not just which fjord, but which part of the wall."

**Honest limit:** susceptibility source is 90m, so susceptibility precision bottoms at 90m; slope/relief can go to 10m. Don't claim finer than the data.

---

## PART B — Final cartographic symbol & layer scheme (Phase 4)

Replaces the mason-jar idea entirely. Clean, scientific, unambiguous. Four visually distinct elements, each carrying one meaning:

| Element | Symbol | Color | Meaning |
|---|---|---|---|
| Recommended sensor placement | **Target** (concentric rings + center dot) | white or black with contrast outline | the refined exact spot — "place here" |
| Existing monitoring station | **Filled circle** | blue / cyan (cool, reads as infrastructure not hazard) | already monitored — "watched" |
| Risk zone (influence area) | filled polygon/circle | rank gradient: red (top) -> orange -> amber -> yellow | dangerous + unmonitored area |
| Data-gap area | hatch / diagonal lines | grey, ~30% opacity | "we're blind here" — NOT low risk |

### Symbol design notes

- **Target for recommendations:** small and exact — because the refinement step makes the point genuinely precise. A small target = "we know this to the meter," which is now true. Concentric rings read as "zoomed-in exact location." Center dot = the refined coordinate.
- **Contrast outline mandatory:** the target sits ON TOP of red/orange zone fills. A colored target would vanish. Use white or black fill with a thin contrasting stroke so it reads on any background (standard cartographic practice for point symbols over colored areas).
- **Circle vs target:** fundamentally different shapes (not two variants of one), so existing-vs-recommended is clear even without the legend. Cool blue circle = installed; sharp target = proposed.
- **Grey hatch, never solid grey:** solid grey could be misread as "low risk." Diagonal hatch pattern reads as "no data." Label it explicitly in the legend.

### Configurability (architecture, not a settings UI)

Put the color thresholds and palette in a config object/file, NOT hardcoded inline and NOT behind a user settings panel. This:
- lets you retune for the Alps/Himalaya extension (different thresholds) by editing one place
- is a one-line pitch point ("thresholds are configurable for other regions")
- avoids scope-creep — NO settings UI for Saturday; just clean config values

### Legend (bottom-left, must be present)

```
SENSOR PLACEMENT
  (target)  Recommended site
  (blue dot) Existing monitoring

RISK (unmonitored)
  red -> amber  highest -> lower priority

  (grey hatch) Data-limited — not assessed
```

---

## Priority order for Saturday (if time runs short)

1. MUST: risk zones (colored) + target symbols for recommendations — the core visualization
2. MUST: existing-station blue circles — the dangerous-vs-ignored story needs both visible
3. STRONG: grey data-gap hatch — the honesty layer; if time-pressed, make it a toggle and cover it verbally
4. NICE: refined placement precision visible at high zoom — if Stage 2 refinement is done, great; if not, 500m points still work
5. NOT Saturday: any settings/config UI — config values in code only

---

## What NOT to do

- No mason jar (dropped — unclear and oversized)
- No colored target (vanishes on colored zones — use white/black + outline)
- No solid grey for data gaps (reads as low-risk — use hatch + label)
- No settings UI (config in code only)
- No 90m full-grid ranking (tested, didn't help — 500m rank + per-point refinement instead)
