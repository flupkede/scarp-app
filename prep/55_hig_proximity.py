#!/usr/bin/env python3
"""Scarp — recompute the proximity scoring component from Hig's curated inventory.

The base scoring raster (prep/50_score_zones.py) computes `proximity` =
exp(-distance_to_nearest_known_slide / 5 km) from the public DGGS/USFS/USGS
inventory. Hig's expert-curated inventory (data/processed/hig_landslides.geojson)
is the better ground truth, so this step REPLACES each candidate's proximity
component with exp(-distance_to_nearest_Hig_slide / 5 km), computed pointwise —
which is faithful to what the raster would produce at the candidate cell.

It rewrites data/processed/zones.geojson with the new proximity component and a
`nearest_hig_slide_km` / `nearest_hig_slide` annotation per zone. It does NOT
recompute score or rank — run glacier/40_rerank_zones.py afterwards to finalise
the glacier-aware score and ranking from the updated components.

Pipeline order: 50_score_zones -> 05_hig_inventory -> 55_hig_proximity ->
glacier/40_rerank_zones.

Usage:
    cd C:/WorkArea/AI/scarp
    uv run --project prep python prep/55_hig_proximity.py
"""

import json
import sys
from math import asin, cos, exp, radians, sin, sqrt
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PROC = REPO_ROOT / "data" / "processed"

ZONES_FILE = "zones.geojson"
HIG_LANDSLIDES_FILE = "hig_landslides.geojson"

# Mirrors PROXIMITY_DECAY_KM in prep/50_score_zones.py (the raster proximity).
PROXIMITY_DECAY_KM = 5.0
# Only events meeting the inventory size threshold count as proximity analogs.
REQUIRE_SIZE_INCLUSION = True


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Great-circle distance in km between two WGS84 points."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    earth_radius_km = 6371.0
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return earth_radius_km * 2 * asin(sqrt(min(1.0, a)))


def load_json(path: Path) -> dict:
    if not path.exists():
        print(f"Error: {path} not found.")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def slide_points(fc: dict) -> list[tuple[float, float, str]]:
    """Extract (lon, lat, name) for Hig slides used as proximity analogs."""
    pts = []
    for feat in fc["features"]:
        props = feat.get("properties", {})
        if REQUIRE_SIZE_INCLUSION and not props.get("size_inclusion"):
            continue
        geom = feat.get("geometry")
        if not geom or geom.get("type") != "Point":
            continue
        lon, lat = geom["coordinates"][0], geom["coordinates"][1]
        name = props.get("unique_name") or f"slide-{props.get('id')}"
        pts.append((float(lon), float(lat), name))
    return pts


def main() -> None:
    print("=" * 60)
    print("Scarp — Hig-inventory proximity (replace scoring basis)")
    print("=" * 60)

    zones = load_json(DATA_PROC / ZONES_FILE)
    slides = slide_points(load_json(DATA_PROC / HIG_LANDSLIDES_FILE))
    if not slides:
        print("Error: no usable Hig slide points (size-included Points).")
        sys.exit(1)
    print(f"  Zones: {len(zones['features'])}  |  Hig slides (analogs): {len(slides)}")

    for feat in zones["features"]:
        lon, lat = feat["geometry"]["coordinates"][0], feat["geometry"]["coordinates"][1]
        best_d = float("inf")
        best_name = None
        for slon, slat, sname in slides:
            d = haversine_km(lon, lat, slon, slat)
            if d < best_d:
                best_d = d
                best_name = sname
        proximity = exp(-best_d / PROXIMITY_DECAY_KM)
        props = feat["properties"]
        props["components"]["proximity"] = round(proximity, 3)
        props["nearest_hig_slide_km"] = round(best_d, 1)
        props["nearest_hig_slide"] = best_name

    (DATA_PROC / ZONES_FILE).write_text(json.dumps(zones), encoding="utf-8")
    print(f"  [ok] {ZONES_FILE}: proximity replaced with Hig-inventory basis")

    # Report the closest and farthest candidates to curated failures
    ranked = sorted(
        zones["features"], key=lambda f: f["properties"]["nearest_hig_slide_km"]
    )
    print("\n  Closest 5 candidates to a curated Hig slide:")
    for f in ranked[:5]:
        p = f["properties"]
        print(
            f"    {p['id']:10s}  {p['nearest_hig_slide_km']:6.1f} km  "
            f"prox={p['components']['proximity']:.3f}  near={p['nearest_hig_slide']}"
        )
    print("\n  Farthest 3 (low proximity — may be unsurveyed):")
    for f in ranked[-3:]:
        p = f["properties"]
        print(
            f"    {p['id']:10s}  {p['nearest_hig_slide_km']:6.1f} km  "
            f"prox={p['components']['proximity']:.3f}"
        )

    print("\nDone. Next: glacier/40_rerank_zones.py to finalise score + rank.")


if __name__ == "__main__":
    main()
