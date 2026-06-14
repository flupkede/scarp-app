# Manual ice-front lines (ground truth)

Hand-digitized glacier **ice-front** lines, one `LineString` per glacier per
date. These are the **ground truth** for Phase 2 retreat automation
(hand → automate → verify).

- **How to make these:** see [`../../../handmatig_ijsfront_intekenen.md`](../../../handmatig_ijsfront_intekenen.md)
  (step-by-step QGIS guide for non-geologists).
- **One file per glacier**, named like `tracy_arm.geojson`, `barry_arm.geojson`.
  Multiple features per file (one per date).
- **Schema** (each feature's properties): `glacier`, `date` (ISO `YYYY-MM-DD`),
  `source_imagery`, `confidence` (`high`/`med`/`low`), optional `notes`.
  Geometry: `LineString` in EPSG:4326.
- `_template.geojson` shows the structure. Files starting with `_` are ignored.
- **Validate / visualize:** `uv run --project glacier python glacier/17_icefront_check.py`
  — checks the schema, draws all fronts of a glacier over time, and reports the
  front-to-front retreat distance between consecutive dates.
