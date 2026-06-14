#!/usr/bin/env python
"""Scarp Glacier — validate + visualize hand-mapped ice fronts (Phase 1 Stage 1.6).

Reads the hand-digitized ice-front lines in data/manual/ice_fronts/, validates
the schema, draws all fronts of each glacier over time, and reports the
front-to-front retreat distance between consecutive dates. This is the QA tool
for the ground truth that Phase 2 retreat automation is verified against.

Run:
  uv run --project glacier python glacier/17_icefront_check.py

If no ice-front files exist yet, prints guidance and exits 0. See
handmatig_ijsfront_intekenen.md for how to create them.
"""

from __future__ import annotations

import sys

import geopandas as gpd
import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (must follow backend selection)

from config import (  # noqa: E402
    ICE_FRONT_DIR,
    ICE_FRONT_FIELDS,
    ICE_FRONT_PLOTS_DIR,
    TARGET_EPSG,
)

GUIDE = "handmatig_ijsfront_intekenen.md"


def _front_files() -> list:
    """Ice-front GeoJSON files, excluding templates (names starting with '_')."""
    if not ICE_FRONT_DIR.exists():
        return []
    return sorted(p for p in ICE_FRONT_DIR.glob("*.geojson") if not p.name.startswith("_"))


def validate_file(path) -> tuple[gpd.GeoDataFrame | None, list[str]]:
    """Load one file; return (gdf, errors). gdf is None when unreadable."""
    errors: list[str] = []
    try:
        gdf = gpd.read_file(path)
    except Exception as exc:  # noqa: BLE001 — surface any read error as a validation msg
        return None, [f"{path.name}: cannot read ({exc})"]

    missing = [f for f in ICE_FRONT_FIELDS if f not in gdf.columns]
    if missing:
        errors.append(f"{path.name}: missing field(s) {missing}")

    bad_geom = (gdf.geometry.geom_type != "LineString").sum()
    if bad_geom:
        errors.append(f"{path.name}: {bad_geom} feature(s) are not LineString")

    if "date" in gdf.columns and gdf["date"].isna().any():
        errors.append(f"{path.name}: {int(gdf['date'].isna().sum())} feature(s) missing date")

    return gdf, errors


def report_retreat(glacier: str, gdf: gpd.GeoDataFrame) -> None:
    """Print front-to-front gap (retreat proxy, metres) between consecutive dates."""
    g = gdf.sort_values("date").reset_index(drop=True)
    g_m = g.to_crs(epsg=TARGET_EPSG)
    print(f"\n  {glacier} — {len(g)} front(s):")
    prev_geom = None
    prev_date = None
    for _, row in g_m.iterrows():
        date = row.get("date", "?")
        if prev_geom is not None:
            gap_m = prev_geom.distance(row.geometry)
            print(f"    {prev_date} -> {date}:  {gap_m / 1000:.2f} km between fronts")
        else:
            print(f"    {date}:  (first front)")
        prev_geom = row.geometry
        prev_date = date


def plot_glacier(glacier: str, gdf: gpd.GeoDataFrame) -> None:
    """Draw all fronts of a glacier, coloured oldest→newest, to a PNG."""
    ICE_FRONT_PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    g = gdf.sort_values("date").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8, 8))
    n = len(g)
    cmap = plt.get_cmap("viridis")
    for i, (_, row) in enumerate(g.iterrows()):
        color = cmap(i / max(1, n - 1))
        xs, ys = row.geometry.xy
        ax.plot(xs, ys, color=color, linewidth=2, label=str(row.get("date", i)))
    ax.set_title(f"{glacier} — ice fronts over time (oldest=purple → newest=yellow)")
    ax.set_xlabel("lon")
    ax.set_ylabel("lat")
    ax.legend(fontsize=7, loc="best")
    ax.set_aspect("equal", adjustable="datalim")
    out = ICE_FRONT_PLOTS_DIR / f"icefronts_{glacier}.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"    plot -> {out}")


def main() -> None:
    print("=== Scarp Glacier — ice-front check (Phase 1 Stage 1.6) ===\n")
    files = _front_files()
    if not files:
        print(f"No ice-front files in {ICE_FRONT_DIR}.")
        print(f"Create them by hand — see {GUIDE} — then re-run.")
        sys.exit(0)

    all_errors: list[str] = []
    frames: list[gpd.GeoDataFrame] = []
    for path in files:
        gdf, errors = validate_file(path)
        all_errors.extend(errors)
        if gdf is not None and not errors:
            frames.append(gdf)
            print(f"  OK  {path.name}  ({len(gdf)} front(s))")

    if all_errors:
        print("\nValidation errors:")
        for e in all_errors:
            print(f"  ✗ {e}")

    if not frames:
        print("\nNo valid ice-front data to summarize.")
        sys.exit(1 if all_errors else 0)

    combined = gpd.GeoDataFrame(
        pd.concat(frames, ignore_index=True), crs=frames[0].crs
    )
    for glacier, group in combined.groupby("glacier"):
        report_retreat(str(glacier), group)
        plot_glacier(str(glacier), group)

    print("\nDone.")
    if all_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
