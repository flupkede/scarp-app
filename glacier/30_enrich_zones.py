#!/usr/bin/env python3
"""Scarp Glacier - Phase 3: enrich Scarp candidate zones with glacier context.

Joins ITS_LIVE velocity data (glacier/data/processed/velocity_summary.geojson)
onto the 120 Scarp candidate zones (data/processed/zones.geojson) and derives,
per zone, a set of glacier-dynamics parameters that feed both the scoring engine
(prep/50_score_zones.py, via the active-ice point set) and the frontend
zone-detail panel.

Per-zone fields produced:
  - has_velocity_data        : did this zone's own location yield ITS_LIVE data?
  - glacier_v_mean / v_max   : velocity at the zone itself (m/yr), null if none
  - glacier_v_trend          : velocity trend at the zone (m/yr per year)
  - glacier_obs_count        : ITS_LIVE observations at the zone
  - nearest_named_glacier    : closest named glacier of interest
  - dist_to_named_glacier_km : distance to that named glacier
  - nearest_active_ice       : closest "active ice" summary point (flow proxy)
  - dist_to_active_ice_km    : distance to nearest active ice (terminus proxy)
  - glacier_proximity        : exp(-dist/decay), 0..1 - spatial influence
  - glacier_dynamics         : normalised |trend| of nearest active ice, 0..1
  - glacier_signal           : proximity * (0.5 + 0.5*dynamics), 0..1

Outputs:
  - glacier/data/processed/zones_glacier_enriched.geojson  (full features)
  - glacier/data/processed/zone_glacier_params.json        (compact id -> params)

Usage:
    cd C:/WorkArea/AI/scarp
    uv run --project glacier python glacier/30_enrich_zones.py
"""

import json
import math
import sys
from math import asin, cos, radians, sin, sqrt

import geopandas as gpd

from config import (
    ACTIVE_ICE_V_THRESHOLD_M_YR,
    DATA_PROCESSED,
    GLACIER_DYNAMICS_FULLSCALE_TREND,
    GLACIER_POINTS_OF_INTEREST,
    GLACIER_PROXIMITY_DECAY_KM,
    SCARP_DATA,
    VELOCITY_SUMMARY_FILE,
    ZONE_GLACIER_PARAMS_FILE,
    ZONES_ENRICHED_FILE,
)

NAMED_GLACIER_LABELS = {label for _, _, label in GLACIER_POINTS_OF_INTEREST}


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Great-circle distance in km between two WGS84 points."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    earth_radius_km = 6371.0
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return earth_radius_km * 2 * asin(sqrt(min(1.0, a)))


def load_zones() -> dict:
    """Load the Scarp candidate zones FeatureCollection."""
    zones_path = SCARP_DATA / "zones.geojson"
    if not zones_path.exists():
        print(f"Error: {zones_path} not found - run prep/50_score_zones.py first.")
        sys.exit(1)
    with open(zones_path) as f:
        return json.load(f)


def load_summary() -> gpd.GeoDataFrame:
    """Load the ITS_LIVE per-point velocity summary."""
    summary_path = DATA_PROCESSED / VELOCITY_SUMMARY_FILE
    if not summary_path.exists():
        print(f"Error: {summary_path} not found - run glacier/10_extract.py first.")
        sys.exit(1)
    return gpd.read_file(summary_path)


def build_point_lookups(summary: gpd.GeoDataFrame) -> tuple[dict, list[dict], list[dict]]:
    """Return (by_id, named_glaciers, active_ice_points) from the summary.

    - by_id: {point_id: row dict} for direct zone self-joins
    - named_glaciers: rows for the named glaciers of interest
    - active_ice_points: rows whose mean velocity marks them as flowing ice
    """
    by_id: dict = {}
    named: list[dict] = []
    active: list[dict] = []
    for _, row in summary.iterrows():
        rec = {
            "point_id": row["point_id"],
            "lon": float(row["lon"]),
            "lat": float(row["lat"]),
            "v_mean": float(row["v_mean"]),
            "v_max": float(row["v_max"]),
            "v_trend": float(row["v_trend_m_yr_per_year"]),
            "obs_count": int(row["obs_count"]),
        }
        by_id[rec["point_id"]] = rec
        if rec["point_id"] in NAMED_GLACIER_LABELS:
            named.append(rec)
        if rec["v_mean"] >= ACTIVE_ICE_V_THRESHOLD_M_YR:
            active.append(rec)
    return by_id, named, active


def nearest(lon: float, lat: float, points: list[dict]) -> tuple[dict | None, float]:
    """Nearest point (by haversine) and its distance in km; (None, inf) if empty."""
    best = None
    best_d = float("inf")
    for p in points:
        d = haversine_km(lon, lat, p["lon"], p["lat"])
        if d < best_d:
            best_d = d
            best = p
    return best, best_d


def enrich_zone(feature: dict, by_id: dict, named: list[dict], active: list[dict]) -> dict:
    """Compute the glacier-context parameter block for one zone feature."""
    lon, lat = feature["geometry"]["coordinates"][0], feature["geometry"]["coordinates"][1]
    zone_id = feature["properties"]["id"]

    self_rec = by_id.get(zone_id)
    has_data = self_rec is not None

    near_named, d_named = nearest(lon, lat, named)
    near_ice, d_ice = nearest(lon, lat, active)

    # Spatial influence of glacier ice on this slope (0..1).
    glacier_proximity = (
        math.exp(-d_ice / GLACIER_PROXIMITY_DECAY_KM) if near_ice is not None else 0.0
    )
    # Dynamism of the nearest active ice: |trend| normalised to 0..1.
    glacier_dynamics = (
        min(abs(near_ice["v_trend"]) / GLACIER_DYNAMICS_FULLSCALE_TREND, 1.0)
        if near_ice is not None
        else 0.0
    )
    # Combined glacier signal: proximity dominates, modulated by dynamism so a
    # nearby fast-changing glacier outscores a nearby stable one.
    glacier_signal = glacier_proximity * (0.5 + 0.5 * glacier_dynamics)

    return {
        "has_velocity_data": has_data,
        "glacier_v_mean": round(self_rec["v_mean"], 2) if has_data else None,
        "glacier_v_max": round(self_rec["v_max"], 1) if has_data else None,
        "glacier_v_trend": round(self_rec["v_trend"], 3) if has_data else None,
        "glacier_obs_count": self_rec["obs_count"] if has_data else 0,
        "nearest_named_glacier": near_named["point_id"] if near_named else None,
        "dist_to_named_glacier_km": round(d_named, 1) if near_named else None,
        "nearest_active_ice": near_ice["point_id"] if near_ice else None,
        "dist_to_active_ice_km": round(d_ice, 1) if near_ice else None,
        "glacier_proximity": round(glacier_proximity, 4),
        "glacier_dynamics": round(glacier_dynamics, 4),
        "glacier_signal": round(glacier_signal, 4),
    }


def main() -> None:
    print("=" * 60)
    print("Scarp Glacier - Phase 3: Enrich Zones with Glacier Context")
    print("=" * 60)
    print()

    zones = load_zones()
    summary = load_summary()
    by_id, named, active = build_point_lookups(summary)

    print(f"  Zones:               {len(zones['features'])}")
    print(f"  Summary points:      {len(summary)}")
    print(f"  Named glaciers:      {len(named)}")
    print(f"  Active-ice points:   {len(active)} "
          f"(v_mean >= {ACTIVE_ICE_V_THRESHOLD_M_YR} m/yr)")

    if not active:
        print("  [!] No active-ice points found - glacier signal will be all zeros.")

    enriched_features = []
    params_map: dict = {}
    n_with_data = 0
    for feature in zones["features"]:
        params = enrich_zone(feature, by_id, named, active)
        if params["has_velocity_data"]:
            n_with_data += 1
        # Attach to a copy so we never mutate the source FeatureCollection.
        new_props = dict(feature["properties"])
        new_props["glacier"] = params
        enriched_features.append(
            {
                "type": "Feature",
                "geometry": feature["geometry"],
                "properties": new_props,
            }
        )
        params_map[feature["properties"]["id"]] = params

    enriched_fc = {"type": "FeatureCollection", "features": enriched_features}
    enriched_path = DATA_PROCESSED / ZONES_ENRICHED_FILE
    enriched_path.write_text(json.dumps(enriched_fc))
    print(f"\n  [ok] {ZONES_ENRICHED_FILE}: {len(enriched_features)} zones")

    params_path = DATA_PROCESSED / ZONE_GLACIER_PARAMS_FILE
    params_path.write_text(json.dumps(params_map, indent=2))
    print(f"  [ok] {ZONE_GLACIER_PARAMS_FILE}: {len(params_map)} entries")

    # --- Report ---
    print("\n" + "=" * 60)
    print("ENRICHMENT SUMMARY")
    print("=" * 60)
    print(f"  Zones with own velocity data: {n_with_data}/{len(zones['features'])}")

    ranked = sorted(
        params_map.items(), key=lambda kv: -kv[1]["glacier_signal"]
    )
    print("\n  Top-10 zones by glacier_signal:")
    for zid, p in ranked[:10]:
        print(
            f"    {zid:10s}  signal={p['glacier_signal']:.3f}  "
            f"prox={p['glacier_proximity']:.3f}  dyn={p['glacier_dynamics']:.3f}  "
            f"d_ice={p['dist_to_active_ice_km']}km  near={p['nearest_active_ice']}"
        )

    print("\nDone.")


if __name__ == "__main__":
    main()
