#!/usr/bin/env python3
"""Scarp Glacier — Extract velocity time series for SE Alaska.

Reads the ITS_LIVE data cube catalog, extracts velocity time series at:
  1. All 120 Scarp candidate zone points
  2. 10 named glacier points of interest

Outputs:
  - velocity_timeseries.parquet — full time series for every point
  - velocity_summary.geojson   — summary stats per point (for mapping)

Usage:
    cd C:/WorkArea/AI/scarp
    uv run --project glacier python glacier/10_extract.py
"""

import json
import sys

import geopandas as gpd
import httpx
import numpy as np
import pandas as pd
import pyproj
import xarray as xr
from shapely.geometry import Point, shape

from _trend import linear_velocity_trend
from config import (
    CUBE_EPSG,
    DATA_PROCESSED,
    DATA_RAW,
    GLACIER_POINTS_OF_INTEREST,
    ITS_LIVE_CATALOG_URL,
    MIN_VELOCITY_OBSERVATIONS,
    SCARP_DATA,
    SE_ALASKA_BBOX_WGS84,
    VELOCITY_OUTLIER_THRESHOLD_M_YR,
    VELOCITY_SUMMARY_FILE,
    VELOCITY_TIMESERIES_FILE,
)

# ---------------------------------------------------------------------------
# Ensure output dirs exist
# ---------------------------------------------------------------------------
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)


def load_catalog() -> dict:
    """Load or download the ITS_LIVE data cube catalog."""
    catalog_path = DATA_RAW / "catalog_v02.json"
    if catalog_path.exists():
        print(f"Loading cached catalog from {catalog_path}")
        with open(catalog_path) as f:
            return json.load(f)

    print(f"Downloading catalog from {ITS_LIVE_CATALOG_URL} ...")
    resp = httpx.get(ITS_LIVE_CATALOG_URL, timeout=60.0)
    resp.raise_for_status()
    catalog = resp.json()
    with open(catalog_path, "w") as f:
        json.dump(catalog, f)
    print(f"  Cached to {catalog_path}")
    return catalog


def build_point_index(catalog: dict) -> list[dict]:
    """Build a spatial index of catalog cubes for point lookup.

    Returns list of {geometry, zarr_url, epsg, granule_count}.
    """
    from shapely.geometry import box

    region = box(*SE_ALASKA_BBOX_WGS84)
    cubes = []
    for feature in catalog.get("features", []):
        geom = shape(feature["geometry"])
        if geom.intersects(region):
            props = feature["properties"]
            cubes.append(
                {
                    "geometry": geom,
                    "zarr_url": props["zarr_url"],
                    "epsg": props.get("epsg", CUBE_EPSG),
                    "granule_count": props.get("granule_count", 0),
                }
            )
    print(f"  {len(cubes)} cubes cover SE Alaska")
    return cubes


def find_cube_for_point(
    lon: float, lat: float, cubes: list[dict]
) -> dict | None:
    """Find the first cube that contains a given WGS84 point."""
    pt = Point(lon, lat)
    for cube in cubes:
        if cube["geometry"].contains(pt):
            return cube
    return None


def group_points_by_cube(
    points: list[tuple[float, float, str]], cubes: list[dict]
) -> dict[str, list[tuple[float, float, str]]]:
    """Group points by the Zarr cube they fall into.

    Returns {zarr_url: [(lon, lat, point_id), ...]}
    """
    groups: dict[str, list[tuple[float, float, str]]] = {}
    for lon, lat, pid in points:
        cube = find_cube_for_point(lon, lat, cubes)
        if cube:
            url = cube["zarr_url"]
            if url not in groups:
                groups[url] = []
            groups[url].append((lon, lat, pid))
    return groups


def extract_batch_from_cube(
    zarr_url: str,
    cube_epsg: int,
    points: list[tuple[float, float, str]],
) -> list[pd.DataFrame]:
    """Extract velocity time series for multiple points from one Zarr cube.

    Opens the cube once, projects all points, reads all time series, then closes.
    """
    transformer = pyproj.Transformer.from_crs(
        "EPSG:4326", f"EPSG:{cube_epsg}", always_xy=True
    )

    try:
        ds = xr.open_zarr(zarr_url, decode_timedelta=True)
    except Exception as e:
        print(f"    Cannot open Zarr: {e}")
        return []

    x_dim = "x" if "x" in ds.sizes else "projection_x"
    y_dim = "y" if "y" in ds.sizes else "projection_y"
    x_vals = ds[x_dim].values
    y_vals = ds[y_dim].values

    results = []
    for lon, lat, point_id in points:
        x_proj, y_proj = transformer.transform(lon, lat)
        x_idx = int(np.abs(x_vals - x_proj).argmin())
        y_idx = int(np.abs(y_vals - y_proj).argmin())

        subset = ds.isel({x_dim: x_idx, y_dim: y_idx})

        n_times = subset.sizes.get("mid_date", 0)
        if n_times == 0:
            continue

        mid_dates = subset["mid_date"].values
        v_arr = subset["v"].values if "v" in subset.data_vars else np.full(n_times, np.nan)

        # Filter valid velocities
        valid_mask = ~np.isnan(v_arr) & (v_arr < VELOCITY_OUTLIER_THRESHOLD_M_YR)
        if valid_mask.sum() < MIN_VELOCITY_OBSERVATIONS:
            continue

        vx_arr = subset["vx"].values if "vx" in subset.data_vars else np.full(n_times, np.nan)
        vy_arr = subset["vy"].values if "vy" in subset.data_vars else np.full(n_times, np.nan)
        v_err_arr = subset["v_error"].values if "v_error" in subset.data_vars else np.full(n_times, np.nan)
        mission_arr = [str(m) for m in subset["mission_img1"].values] if "mission_img1" in subset.data_vars else ["?"] * n_times

        if "date_dt" in subset.data_vars:
            dt_days = np.array([float(td) / 1e9 / 86400 for td in subset["date_dt"].values])
        else:
            dt_days = np.full(n_times, np.nan)

        rows = []
        for i in range(n_times):
            if not valid_mask[i]:
                continue
            rows.append(
                {
                    "point_id": point_id,
                    "lon": lon,
                    "lat": lat,
                    "mid_date": str(mid_dates[i])[:10],
                    "date_dt_days": float(dt_days[i]),
                    "v": float(v_arr[i]),
                    "vx": float(vx_arr[i]) if not np.isnan(vx_arr[i]) else np.nan,
                    "vy": float(vy_arr[i]) if not np.isnan(vy_arr[i]) else np.nan,
                    "v_error": float(v_err_arr[i]) if not np.isnan(v_err_arr[i]) else np.nan,
                    "mission": mission_arr[i],
                }
            )

        if rows:
            results.append(pd.DataFrame(rows))

    ds.close()
    return results


def load_scarp_zones() -> list[tuple[float, float, str]]:
    """Load Scarp candidate zones as (lon, lat, point_id) tuples."""
    zones_path = SCARP_DATA / "zones.geojson"
    if not zones_path.exists():
        print(f"  Warning: {zones_path} not found, skipping Scarp zones")
        return []

    with open(zones_path) as f:
        zones = json.load(f)

    points = []
    for feature in zones["features"]:
        coords = feature["geometry"]["coordinates"]
        lon, lat = coords[0], coords[1]
        point_id = feature["properties"].get("id", f"zone-{len(points)}")
        points.append((lon, lat, point_id))

    print(f"  Loaded {len(points)} Scarp zones")
    return points


def main() -> None:
    print("=" * 60)
    print("Scarp Glacier — Velocity Time Series Extraction")
    print("=" * 60)
    print()

    # Step 1: Load catalog and build spatial index
    print("Loading ITS_LIVE catalog ...")
    catalog = load_catalog()
    cubes = build_point_index(catalog)

    if not cubes:
        print("No cubes found for SE Alaska")
        sys.exit(1)

    # Step 2: Collect all sample points
    print("\nCollecting sample points ...")
    all_points: list[tuple[float, float, str]] = []

    # Scarp zones
    scarp_points = load_scarp_zones()
    all_points.extend(scarp_points)

    # Named glacier POIs
    for lon, lat, label in GLACIER_POINTS_OF_INTEREST:
        all_points.append((lon, lat, label))

    print(f"  Total points: {len(all_points)}")

    # Step 3: Group points by cube and extract in batches
    print("\nGrouping points by data cube ...")
    point_groups = group_points_by_cube(all_points, cubes)
    print(f"  {len(point_groups)} unique cubes to process")
    for url, pts in point_groups.items():
        print(f"    {url[-50:]}: {len(pts)} points")

    print("\nExtracting velocity time series (batched by cube) ...")
    all_dfs: list[pd.DataFrame] = []
    success_count = 0
    no_data_count = 0
    total_points_assigned = sum(len(pts) for pts in point_groups.values())
    no_cube_count = len(all_points) - total_points_assigned

    # Build a lookup from zarr_url -> epsg
    cube_epsg_map = {c["zarr_url"]: c["epsg"] for c in cubes}

    for cube_idx, (zarr_url, pts) in enumerate(point_groups.items()):
        epsg = cube_epsg_map.get(zarr_url, CUBE_EPSG)
        print(
            f"\n  Cube {cube_idx + 1}/{len(point_groups)}: "
            f"{len(pts)} points ({zarr_url[-50:]})"
        )

        batch_dfs = extract_batch_from_cube(zarr_url, epsg, pts)

        for df in batch_dfs:
            pid = df["point_id"].iloc[0]
            v_mean = df["v"].mean()
            obs = len(df)
            if obs < MIN_VELOCITY_OBSERVATIONS:
                no_data_count += 1
                print(f"    {pid}: {obs} obs (skipped)")
                continue
            all_dfs.append(df)
            success_count += 1
            print(f"    {pid}: {obs} obs, v_mean={v_mean:.1f} m/yr")

    # Step 4: Combine and save
    if not all_dfs:
        print("\nNo velocity data extracted!")
        sys.exit(1)

    combined = pd.concat(all_dfs, ignore_index=True)
    print(f"\nCombined: {len(combined)} observations across {success_count} points")

    # Save full time series
    ts_path = DATA_PROCESSED / VELOCITY_TIMESERIES_FILE
    combined.to_parquet(ts_path, index=False)
    print(f"Saved time series -> {ts_path}")

    # Step 5: Compute summary stats per point
    summary_gdf = compute_summary(combined)

    # Print stats
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"  Points with data:  {success_count}")
    print(f"  Points no cube:    {no_cube_count}")
    print(f"  Points no data:    {no_data_count}")
    print(f"  Total observations: {len(combined)}")
    print(f"  Mean velocity:     {combined['v'].mean():.1f} m/yr")
    print(f"  Max velocity:      {combined['v'].max():.1f} m/yr")

    # Top-10 fastest points
    print("\nTop-10 fastest points:")
    for _, row in summary_gdf.nlargest(10, "v_mean").iterrows():
        print(
            f"  {row['point_id']:20s}  v_mean={row['v_mean']:8.1f}  "
            f"v_max={row['v_max']:8.1f}  trend={row['v_trend_m_yr_per_year']:+.2f}/yr"
        )

    print("\nDone. Run 20_visualize.py to generate plots and maps.")


def compute_summary(combined: pd.DataFrame) -> gpd.GeoDataFrame:
    """Compute per-point velocity summary stats (incl. a robust linear trend).

    Writes velocity_summary.geojson and returns the GeoDataFrame. Reused by both
    a full extraction run and the `--from-parquet` regeneration path.
    """
    print("\nComputing summary statistics ...")
    summary_rows = []
    for point_id, group in combined.groupby("point_id"):
        v_clean = group["v"].dropna()
        if len(v_clean) == 0:
            continue

        lon = float(group["lon"].iloc[0])
        lat = float(group["lat"].iloc[0])
        dates = pd.to_datetime(group["mid_date"])

        summary_rows.append(
            {
                "point_id": point_id,
                "lon": lon,
                "lat": lat,
                "geometry": Point(lon, lat),
                "obs_count": len(v_clean),
                "v_mean": float(v_clean.mean()),
                "v_max": float(v_clean.max()),
                "v_std": float(v_clean.std()),
                "v_median": float(v_clean.median()),
                "date_start": str(dates.min())[:10],
                "date_end": str(dates.max())[:10],
                "date_span_years": float((dates.max() - dates.min()).days / 365.25),
                # Trend: pass aligned full-length v and dates; the trend
                # function drops NaN/NaT and sorts internally.
                "v_trend_m_yr_per_year": _compute_trend(
                    group["v"].to_numpy(), dates
                ),
            }
        )

    summary_gdf = gpd.GeoDataFrame(summary_rows, crs="EPSG:4326")
    summary_path = DATA_PROCESSED / VELOCITY_SUMMARY_FILE
    summary_gdf.to_file(summary_path, driver="GeoJSON")
    print(f"Saved summary -> {summary_path} ({len(summary_gdf)} points)")
    return summary_gdf


def regenerate_summary_from_parquet() -> gpd.GeoDataFrame:
    """Recompute velocity_summary.geojson from the cached time-series parquet.

    Avoids a full network re-extraction when only the summary/trend logic changed.
    """
    ts_path = DATA_PROCESSED / VELOCITY_TIMESERIES_FILE
    if not ts_path.exists():
        print(f"Error: {ts_path} not found — run a full extraction first.")
        sys.exit(1)
    print(f"Loading cached time series from {ts_path} ...")
    combined = pd.read_parquet(ts_path)
    print(f"  {len(combined)} observations across {combined['point_id'].nunique()} points")
    summary_gdf = compute_summary(combined)
    print("\nTop-10 fastest points:")
    for _, row in summary_gdf.nlargest(10, "v_mean").iterrows():
        print(
            f"  {row['point_id']:20s}  v_mean={row['v_mean']:8.1f}  "
            f"v_max={row['v_max']:8.1f}  trend={row['v_trend_m_yr_per_year']:+.2f}/yr"
        )
    return summary_gdf


def _compute_trend(v_values: np.ndarray, dates: pd.Series) -> float:
    """Linear velocity trend (m/yr per year).

    Thin wrapper preserving this module's (v_values, dates) call order; the
    regression itself lives in the shared glacier/_trend.py so 10_extract and
    15_explore can't drift.
    """
    return linear_velocity_trend(dates, v_values)


if __name__ == "__main__":
    if "--from-parquet" in sys.argv:
        regenerate_summary_from_parquet()
    else:
        main()
