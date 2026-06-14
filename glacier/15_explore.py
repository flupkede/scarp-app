#!/usr/bin/env python
"""Scarp Glacier — Phase 1 ITS_LIVE exploration analytics.

Reads the cached velocity time-series parquet (no network) and produces
"interesting outputs to get hooks in the data" (per Hig): per-point annual
velocity series, a seasonal climatology, a robust linear trend, sawtooth
acceleration/deceleration episodes, and coverage-gap / retreat-tail flags.

Outputs:
  glacier/data/processed/glacier_exploration.json   full per-point analytics
  data/processed/glacier_timeseries.json            light per-point series (charts)
  data/processed/glacier_episodes.geojson           episode markers (map layer)

Run:
  uv run --project glacier python glacier/15_explore.py
"""

from __future__ import annotations

import json
import sys

import pandas as pd

from _trend import linear_velocity_trend
from config import (
    DATA_PROCESSED,
    EXPLORE_EPISODE_DELTA_M_YR,
    EXPLORE_GAP_YEARS,
    EXPLORE_MIN_OBS_PER_YEAR,
    EXPLORE_RETREAT_TAIL_YEARS,
    GLACIER_EPISODES_LAYER_FILE,
    GLACIER_EXPLORATION_FILE,
    GLACIER_POINTS_OF_INTEREST,
    GLACIER_TIMESERIES_LAYER_FILE,
    SCARP_DATA,
    VELOCITY_TIMESERIES_FILE,
)

# Named glaciers of interest (point_id == label in the parquet).
NAMED_GLACIERS = {label for _lon, _lat, label in GLACIER_POINTS_OF_INTEREST}


def _annual_series(group: pd.DataFrame) -> list[dict]:
    """Annual-median velocity series (noise-robust). One entry per year with
    at least EXPLORE_MIN_OBS_PER_YEAR observations."""
    g = group.dropna(subset=["v"]).copy()
    g["year"] = pd.to_datetime(g["mid_date"], errors="coerce").dt.year
    g = g.dropna(subset=["year"])
    out: list[dict] = []
    for year, yg in g.groupby("year"):
        if len(yg) < EXPLORE_MIN_OBS_PER_YEAR:
            continue
        out.append(
            {
                "year": int(year),
                "v_median": round(float(yg["v"].median()), 1),
                "n": int(len(yg)),
            }
        )
    out.sort(key=lambda r: r["year"])
    return out


def _seasonal(group: pd.DataFrame) -> dict[str, float]:
    """Monthly velocity climatology (1..12 → mean v). Surfaces the seasonal
    signal Hig pointed out in the live demo."""
    g = group.dropna(subset=["v"]).copy()
    g["month"] = pd.to_datetime(g["mid_date"], errors="coerce").dt.month
    g = g.dropna(subset=["month"])
    return {
        str(int(m)): round(float(mg["v"].mean()), 1)
        for m, mg in g.groupby("month")
    }


def _episodes(annual: list[dict]) -> list[dict]:
    """Year-over-year jumps in annual-median velocity exceeding the episode
    threshold — the accelerate/decelerate sawtooth tied to retreat episodes."""
    eps: list[dict] = []
    for prev, cur in zip(annual, annual[1:]):
        delta = cur["v_median"] - prev["v_median"]
        if abs(delta) >= EXPLORE_EPISODE_DELTA_M_YR:
            eps.append(
                {
                    "year": cur["year"],
                    "delta_v": round(delta, 1),
                    "direction": "accelerate" if delta > 0 else "decelerate",
                }
            )
    return eps


def _coverage(group: pd.DataFrame, dataset_end_year: int) -> dict:
    """Coverage span, gaps, and a retreat-tail flag (coverage ending well before
    the dataset-wide latest observation = candidate retreat past the point)."""
    dates = pd.to_datetime(group["mid_date"], errors="coerce").dropna().sort_values()
    if dates.empty:
        return {"date_start": None, "date_end": None, "gaps": [], "retreat_tail": False}
    gaps: list[dict] = []
    prev = None
    for d in dates:
        if prev is not None:
            gap_years = (d - prev).days / 365.25
            if gap_years >= EXPLORE_GAP_YEARS:
                gaps.append(
                    {
                        "from": str(prev)[:10],
                        "to": str(d)[:10],
                        "years": round(float(gap_years), 1),
                    }
                )
        prev = d
    end_year = int(dates.max().year)
    retreat_tail = (dataset_end_year - end_year) >= EXPLORE_RETREAT_TAIL_YEARS
    return {
        "date_start": str(dates.min())[:10],
        "date_end": str(dates.max())[:10],
        "gaps": gaps,
        "retreat_tail": bool(retreat_tail),
    }


def analyse(combined: pd.DataFrame) -> dict:
    """Per-point exploration analytics keyed by point_id."""
    end_dates = pd.to_datetime(combined["mid_date"], errors="coerce").dropna()
    dataset_end_year = int(end_dates.max().year) if not end_dates.empty else 0
    results: dict[str, dict] = {}
    for point_id, group in combined.groupby("point_id"):
        v_clean = group["v"].dropna()
        if v_clean.empty:
            continue
        annual = _annual_series(group)
        results[str(point_id)] = {
            "point_id": str(point_id),
            "lon": round(float(group["lon"].iloc[0]), 5),
            "lat": round(float(group["lat"].iloc[0]), 5),
            "is_named_glacier": str(point_id) in NAMED_GLACIERS,
            "obs_count": int(len(v_clean)),
            "v_mean": round(float(v_clean.mean()), 1),
            "v_max": round(float(v_clean.max()), 1),
            "trend_m_yr_per_year": round(
                linear_velocity_trend(group["mid_date"], group["v"].to_numpy()), 3
            ),
            "annual": annual,
            "seasonal": _seasonal(group),
            "episodes": _episodes(annual),
            "coverage": _coverage(group, dataset_end_year),
        }
    return results


def write_outputs(results: dict) -> None:
    """Write the full analytics (glacier/) + the published charts JSON and
    episode markers GeoJSON (data/processed/ for the backend)."""
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    SCARP_DATA.mkdir(parents=True, exist_ok=True)

    full_path = DATA_PROCESSED / GLACIER_EXPLORATION_FILE
    full_path.write_text(json.dumps(results, indent=2) + "\n")
    print(f"Saved full analytics -> {full_path} ({len(results)} points)")

    # Light charts payload: drop the seasonal dict to keep it small; keep the
    # annual series, trend, episodes, and coverage flags.
    light = {
        pid: {
            "point_id": r["point_id"],
            "is_named_glacier": r["is_named_glacier"],
            "v_mean": r["v_mean"],
            "trend_m_yr_per_year": r["trend_m_yr_per_year"],
            "annual": r["annual"],
            "episodes": r["episodes"],
            "retreat_tail": r["coverage"]["retreat_tail"],
        }
        for pid, r in results.items()
    }
    ts_path = SCARP_DATA / GLACIER_TIMESERIES_LAYER_FILE
    ts_path.write_text(json.dumps(light) + "\n")
    print(f"Saved charts payload -> {ts_path}")

    # Episode markers as a point GeoJSON (one feature per episode).
    features = []
    for r in results.values():
        for ep in r["episodes"]:
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
                    "properties": {
                        "point_id": r["point_id"],
                        "year": ep["year"],
                        "delta_v": ep["delta_v"],
                        "direction": ep["direction"],
                        "is_named_glacier": r["is_named_glacier"],
                    },
                }
            )
    fc = {"type": "FeatureCollection", "features": features}
    ep_path = SCARP_DATA / GLACIER_EPISODES_LAYER_FILE
    ep_path.write_text(json.dumps(fc) + "\n")
    print(f"Saved episode markers -> {ep_path} ({len(features)} episodes)")


def main() -> None:
    print("=== Scarp Glacier — ITS_LIVE exploration (Phase 1) ===\n")
    ts_path = DATA_PROCESSED / VELOCITY_TIMESERIES_FILE
    if not ts_path.exists():
        print(f"Error: {ts_path} not found — run glacier/10_extract.py first.")
        sys.exit(1)

    print(f"Loading cached time series from {ts_path} ...")
    combined = pd.read_parquet(ts_path)
    print(
        f"  {len(combined)} observations across "
        f"{combined['point_id'].nunique()} points\n"
    )

    results = analyse(combined)
    write_outputs(results)

    # Console highlights: named glaciers with episodes or retreat tails.
    print("\nNamed glaciers — episodes / retreat signal:")
    for r in results.values():
        if not r["is_named_glacier"]:
            continue
        flags = []
        if r["episodes"]:
            flags.append(f"{len(r['episodes'])} episode(s)")
        if r["coverage"]["retreat_tail"]:
            flags.append("retreat-tail")
        if r["coverage"]["gaps"]:
            flags.append(f"{len(r['coverage']['gaps'])} gap(s)")
        tag = ", ".join(flags) if flags else "—"
        print(
            f"  {r['point_id']:18s}  v_mean={r['v_mean']:8.1f}  "
            f"trend={r['trend_m_yr_per_year']:+.2f}/yr  [{tag}]"
        )


if __name__ == "__main__":
    main()
