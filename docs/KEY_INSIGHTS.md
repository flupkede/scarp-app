# Key insights to lock into the plans (so they aren't lost)

These emerged during the Friday scoring work and are NOT yet in the production specs or README. They are among the strongest parts of the pitch. Add them.

---

## INSIGHT 1 — "Dangerous vs. dangerous-AND-ignored" (the strongest differentiator)

The model deliberately does NOT rank already-monitored sites highly. Barry Arm — the slide that triggered the U.S. National Landslide Preparedness Act — sits at ~rank 45, not the top, because it already has a seismic station 1.3km away.

This is correct behavior, and it is the core of the pitch:

> Scarp doesn't find dangerous places. It finds places that are dangerous AND nobody is watching. Barry Arm is dangerous — but it's already monitored, so it drops down the list. The whole point is to find the next gap, not to re-confirm what we already watch.

This distinguishes Scarp from every generic "risk map" — those show danger; Scarp shows the *monitoring gap*, which is the actual decision Hig faces.

**Where to add:**
- PROJECT_RATIONALE.md — as a named insight
- README — in the "Why this is new" section, as a concrete example
- Pitch script — this is a candidate for the closing or a mid-demo "aha" moment

## INSIGHT 2 — The fjord_wall signal (why the model is geographically smart)

The model distinguishes a steep fjord cliff that drops into deep water (tsunamigenic) from a flat populated shore like Anchorage (not tsunamigenic). The fjord_wall signal = local relief × proximity to water. This is why the top 10 are real fjord walls (Turnagain Arm, Portage, Whittier, Sitka) and Anchorage suburbs correctly dropped out entirely.

> Early versions ranked Anchorage suburbs at the top — because they have the most buildings. That's wrong: a tsunamigenic slide needs a steep wall into deep water, not population. Adding a fjord-wall signal (steepness × water proximity) fixed it. Now the top sites are genuine fjord cliffs that are unmonitored.

**Where to add:** README "How it works", PROJECT_RATIONALE methodology, pitch (the "I caught my own model being wrong and fixed it" angle shows rigor).

## INSIGHT 3 — The data-source detective work (USGS n10 vs DGGS)

The standard statewide DGGS susceptibility raster (900m) marks the narrow fjords — exactly where these slides happen — as NODATA (88.6% of the area). Switched to the USGS n10 model (90m, Mirus et al. 2024) which actually covers the fjord walls. This is a data-judgment story that signals maturity.

**Where to add:** README "How it works" (one line), PROJECT_RATIONALE.

## INSIGHT 4 — Honest data limits as a second finding

The data-confidence layer measures how many public inputs are actually present across the region. The result: the famous, well-studied sites (Lituya Bay, Taan Fiord, Tracy Arm) are well-covered — but roughly three-quarters of the SE Alaska land area is data-limited. The grey overlay shows where a low score means "not enough data to judge," not "low risk." The well-known fjords are the exceptions; the unstudied slopes between them are where the public record runs thin. This is the second finding, and it aligns with the Walden/Patton papers calling for better systematic data.

**Where to add:** already in ADDITION_confidence_layer.md; ensure it also lands in README "Honest limitations" and the pitch.

---

## Action for the production specs

1. Add INSIGHT 1 and 2 to `production/AGENTS_phase-2.md` as "design rationale" notes so the Saturday build reproduces this behavior (fjord_wall signal, coverage penalty) and the team understands WHY.
2. Update `README_plan.md` to explicitly include the "dangerous vs dangerous-and-ignored" framing in the "Why this is new" section and as a pitch beat.
3. Add INSIGHT 1-4 to `PROJECT_RATIONALE.md` under a new "Key findings from development" section.
