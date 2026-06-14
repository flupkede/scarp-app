#!/usr/bin/env python3
"""Scarp — ingest Hig's Alaska Landslide Inventory export into static GeoJSON.

Reads the read-only export Hig generated from landslidescience.org
(data/raw/hig_inventory/, vendored from the landslide_eval workspace) and writes
trimmed, frontend-friendly static GeoJSON to data/processed/:

  - hig_landslides.geojson     1,464 curated landslide centroids (Point), with a
                               lean set of display/scoring properties. This is the
                               expert ground-truth set that replaces the public
                               DGGS/USFS proximity basis in scoring.
  - hig_polygons.geojson       1,789 mapped slide footprints (body/source/deposit).
  - hig_survey_circles.geojson 525 survey circles — where Hig actually looked;
                               feeds the data-confidence layer (45_confidence.py).

Source files are GeoJSON in WGS84 (EPSG:4326) per the export manifest, so no
reprojection is needed here.

Usage:
    cd C:/WorkArea/AI/scarp
    uv run --project prep python prep/05_hig_inventory.py
"""

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROC = REPO_ROOT / "data" / "processed"

# Vendored export location (raw, gitignored). Override with SCARP_HIG_INVENTORY_DIR.
HIG_SRC_DIR = Path(os.getenv("SCARP_HIG_INVENTORY_DIR", str(DATA_RAW / "hig_inventory")))

SRC_LANDSLIDES = "landslides.geojson"
SRC_POLYGONS = "landslide_polygons.geojson"
SRC_SURVEY_CIRCLES = "survey_circles.geojson"

OUT_LANDSLIDES = "hig_landslides.geojson"
OUT_POLYGONS = "hig_polygons.geojson"
OUT_SURVEY_CIRCLES = "hig_survey_circles.geojson"

# Lean property sets — keep what the map/zone-detail and scoring need, drop the
# dozens of provenance/InSAR columns that bloat the payload.
LANDSLIDE_PROPS = [
    "id",
    "unique_name",
    "landslide_type",
    "landslide_class",
    "size_inclusion",
    "volume_preferred",
    "volume_method",
    "year_text",
    "date_min",
    "date_max",
    "post_2012_activity_increase",
    "catastrophic_failure_years",
    "creep_behavior",
    "stream_damming",
]
POLYGON_PROPS = ["id", "landslide_id", "role", "is_primary", "area", "polygon_volume"]
SURVEY_CIRCLE_PROPS = ["id", "reviewed", "recent_catastrophic", "obvious_creep", "notes"]


def load_source(name: str) -> dict:
    path = HIG_SRC_DIR / name
    if not path.exists():
        print(
            f"Error: {path} not found.\n"
            f"  Copy Hig's inventory export into {HIG_SRC_DIR} (or set "
            f"SCARP_HIG_INVENTORY_DIR). Expected files: {SRC_LANDSLIDES}, "
            f"{SRC_POLYGONS}, {SRC_SURVEY_CIRCLES}."
        )
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def trim(fc: dict, keep: list[str]) -> dict:
    """Return a FeatureCollection keeping only `keep` properties per feature."""
    out_features = []
    for feat in fc["features"]:
        props = feat.get("properties", {})
        out_features.append(
            {
                "type": "Feature",
                "geometry": feat["geometry"],
                "properties": {k: props.get(k) for k in keep},
            }
        )
    return {"type": "FeatureCollection", "features": out_features}


def write_fc(fc: dict, name: str) -> None:
    path = DATA_PROC / name
    path.write_text(json.dumps(fc), encoding="utf-8")
    print(f"  [ok] {name}: {len(fc['features'])} features")


def main() -> None:
    print("=" * 60)
    print("Scarp — Ingest Hig Landslide Inventory")
    print("=" * 60)
    print(f"  Source: {HIG_SRC_DIR}\n")

    landslides = load_source(SRC_LANDSLIDES)
    polygons = load_source(SRC_POLYGONS)
    circles = load_source(SRC_SURVEY_CIRCLES)

    n_total = len(landslides["features"])
    n_incl = sum(1 for f in landslides["features"] if f["properties"].get("size_inclusion"))
    print(f"  Landslides: {n_total} ({n_incl} meet size threshold)")
    print(f"  Polygons:   {len(polygons['features'])}")
    print(f"  Survey circles: {len(circles['features'])}\n")

    write_fc(trim(landslides, LANDSLIDE_PROPS), OUT_LANDSLIDES)
    write_fc(trim(polygons, POLYGON_PROPS), OUT_POLYGONS)
    write_fc(trim(circles, SURVEY_CIRCLE_PROPS), OUT_SURVEY_CIRCLES)

    print("\nDone. Next: prep/55_hig_proximity.py (scoring) + "
          "prep/45_confidence.py --force (survey circles).")


if __name__ == "__main__":
    main()
