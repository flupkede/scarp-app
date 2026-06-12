#!/usr/bin/env python3
"""Scarp Glacier — Explore ITS_LIVE data cubes for SE Alaska.

Uses the ITS_LIVE catalog JSON to discover data cubes covering SE Alaska,
then extracts velocity time series directly from Zarr stores via s3fs+xarray.
Reads only the nearest grid cell to each sample point (avoids the itslive
wrapper timeouts on large cubes).

Usage:
    cd C:/WorkArea/AI/scarp
    uv run --project glacier python glacier/00_explore.py
"""

import json
import sys
import time
from pathlib import Path

import httpx
import numpy as np
import pyproj
import xarray as xr
from shapely.geometry import Point, shape

from config import (
    CUBE_EPSG,
    CUBE_GRID_RESOLUTION_M,
    DATA_PROCESSED,
    DATA_RAW,
    GLACIER_POINTS_OF_INTEREST,
    ITS_LIVE_CATALOG_URL,
    SE_ALASKA_BBOX_WGS84,
    VELOCITY_OUTLIER_THRESHOLD_M_YR,
)

# ---------------------------------------------------------------------------
# Ensure output dirs exist
# ---------------------------------------------------------------------------
DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)


def download_catalog() -> dict:
    """Download the ITS_LIVE data cube catalog (GeoJSON)."""
    print(f"Downloading catalog from {ITS_LIVE_CATALOG_URL} ...")
    resp = httpx.get(ITS_LIVE_CATALOG_URL, timeout=60.0)
    resp.raise_for_status()
    catalog = resp.json()
    n_cubes = len(catalog.get("features", []))
    print(f"  Catalog contains {n_cubes} data cubes")
    return catalog


def filter_cubes_for_region(catalog: dict) -> list[dict]:
    """Filter catalog cubes that overlap the SE Alaska bbox."""
    from shapely.geometry import box

    region = box(*SE_ALASKA_BBOX_WGS84)
    matching = []

    for feature in catalog.get("features", []):
        geom = shape(feature["geometry"])
        if geom.intersects(region):
            props = feature["properties"]
            matching.append(
                {
                    "zarr_url": props["zarr_url"],
                    "epsg": props.get("epsg"),
                    "granule_count": props.get("granule_count", 0),
                    "coverage": props.get("roi_percent_coverage", 0),
                    "geometry_wkt": geom.wkt,
                }
            )

    print(f"  {len(matching)} cubes overlap SE Alaska bbox")
    return matching


def point_in_cube(lon: float, lat: float, feature: dict) -> bool:
    """Check if a WGS84 point falls inside a catalog feature's geometry."""
    geom = shape(feature["geometry"])
    return geom.contains(Point(lon, lat))


def find_cubes_for_point(
    lon: float, lat: float, catalog: dict
) -> list[dict]:
    """Find all catalog cubes that contain a given point."""
    results = []
    for feature in catalog.get("features", []):
        if point_in_cube(lon, lat, feature):
            props = feature["properties"]
            results.append(
                {
                    "zarr_url": props["zarr_url"],
                    "epsg": props.get("epsg"),
                    "granule_count": props.get("granule_count", 0),
                }
            )
    return results


def extract_point_from_cube(
    lon: float, lat: float, zarr_url: str, cube_epsg: int, label: str
) -> dict | None:
    """Extract velocity time series for a point from a single Zarr cube.

    Projects the WGS84 point to the cube's native CRS,
    finds the nearest grid cell, and reads only that time slice.

    The catalog provides HTTPS URLs — xarray opens Zarr via HTTP directly.
    """
    transformer = pyproj.Transformer.from_crs(
        "EPSG:4326", f"EPSG:{cube_epsg}", always_xy=True
    )
    x_proj, y_proj = transformer.transform(lon, lat)

    try:
        # Open Zarr store via HTTPS (catalog provides HTTP URLs)
        ds = xr.open_zarr(zarr_url, decode_timedelta=True)
    except Exception as e:
        print(f"    Cannot open Zarr store: {e}")
        return None

    # Find x/y dimension names
    x_dim = "x" if "x" in ds.dims else "projection_x"
    y_dim = "y" if "y" in ds.dims else "projection_y"

    # Find nearest grid cell
    x_vals = ds[x_dim].values
    y_vals = ds[y_dim].values
    x_idx = int(np.abs(x_vals - x_proj).argmin())
    y_idx = int(np.abs(y_vals - y_proj).argmin())

    # Read only the time series at this cell (single x, single y)
    try:
        # Use isel to select the single nearest pixel
        subset = ds.isel({x_dim: x_idx, y_dim: y_idx})

        # Extract velocity variables
        result = {
            "label": label,
            "lon": lon,
            "lat": lat,
            "x_idx": x_idx,
            "y_idx": y_idx,
            "zarr_url": zarr_url,
        }

        # mid_date is the time coordinate
        if "mid_date" in subset.coords:
            mid_dates = subset["mid_date"].values
            result["observations"] = int(len(mid_dates))
        else:
            result["observations"] = 0

        # Extract velocity magnitude (v) and components (vx, vy)
        for var_name in ["v", "vx", "vy"]:
            if var_name in subset.data_vars:
                vals = subset[var_name].values
                clean = vals[~np.isnan(vals)]
                # Cap outliers
                clean = clean[clean < VELOCITY_OUTLIER_THRESHOLD_M_YR]
                if len(clean) > 0:
                    result[f"{var_name}_mean"] = float(np.mean(clean))
                    result[f"{var_name}_max"] = float(np.max(clean))
                    result[f"{var_name}_std"] = float(np.std(clean))
                    result[f"{var_name}_count"] = int(len(clean))

        ds.close()

    except Exception as e:
        print(f"    ⚠ Read failed: {e}")
        ds.close()
        return None

    return result


def extract_timeseries(
    lon: float, lat: float, label: str, catalog: dict
) -> dict:
    """Extract velocity time series for a point, trying all matching cubes."""
    print(f"  {label} ({lon:.2f}, {lat:.2f}) ...")

    cubes = find_cubes_for_point(lon, lat, catalog)
    if not cubes:
        print(f"    ❌ No cubes found for this point")
        return {
            "label": label,
            "lon": lon,
            "lat": lat,
            "observations": 0,
            "has_velocity": False,
        }

    print(f"    Found {len(cubes)} cube(s)")

    best_result = None
    best_obs = 0

    for cube_info in cubes:
        url = cube_info["zarr_url"]
        epsg = cube_info.get("epsg", CUBE_EPSG)
        granules = cube_info["granule_count"]
        print(f"    Trying cube ({granules} granules, EPSG:{epsg}) ...")

        result = extract_point_from_cube(lon, lat, url, epsg, label)
        if result is None:
            continue

        obs = result.get("observations", 0)
        if obs > best_obs:
            best_obs = obs
            best_result = result

        if obs > 0:
            break  # Found data, no need to try more cubes

    if best_result is None:
        print(f"    ❌ No data extracted")
        return {
            "label": label,
            "lon": lon,
            "lat": lat,
            "observations": 0,
            "has_velocity": False,
        }

    # Add summary info
    best_result["has_velocity"] = "v_mean" in best_result
    obs_str = f"{best_obs} obs"
    v_str = ""
    if "v_mean" in best_result:
        v_str = f", mean v = {best_result['v_mean']:.1f} m/yr"
    print(f"    ✅ {label}: {obs_str}{v_str}")

    return best_result


def main() -> None:
    print("=" * 60)
    print("Scarp Glacier — ITS_LIVE Data Exploration")
    print("=" * 60)
    print(f"Region: {SE_ALASKA_BBOX_WGS84}")
    print(f"Points: {len(GLACIER_POINTS_OF_INTEREST)}")
    print()

    # Step 1: Download catalog and filter for SE Alaska
    catalog = download_catalog()
    regional_cubes = filter_cubes_for_region(catalog)

    if not regional_cubes:
        print("❌ No data cubes found for SE Alaska region")
        sys.exit(1)

    # Save regional cube list
    cubes_path = DATA_RAW / "regional_cubes.json"
    with open(cubes_path, "w") as f:
        json.dump(regional_cubes, f, indent=2)
    print(f"  Saved regional cube list -> {cubes_path}")
    print()

    # Step 2: Extract time series at each point of interest
    print("Extracting velocity time series ...")
    summaries = {}
    for lon, lat, label in GLACIER_POINTS_OF_INTEREST:
        result = extract_timeseries(lon, lat, label, catalog)
        summaries[label] = result
        time.sleep(0.5)  # be gentle on S3

    # Save exploration results
    results_path = DATA_PROCESSED / "exploration_results.json"
    with open(results_path, "w") as f:
        json.dump(
            {
                "bbox": SE_ALASKA_BBOX_WGS84,
                "cube_count": len(regional_cubes),
                "points": summaries,
            },
            f,
            indent=2,
        )
    print(f"\nSaved exploration results → {results_path}")

    # Print summary table
    print("\n" + "=" * 60)
    print("EXPLORATION SUMMARY")
    print("=" * 60)
    has_any = False
    for label, s in summaries.items():
        obs = s.get("observations", 0)
        status = "✅ DATA" if obs > 0 else "❌ NO DATA"
        v_mean = s.get("v_mean")
        v_str = f"  v_mean={v_mean:.1f}" if v_mean else ""
        print(f"  {status}  {label:25s}  {obs:6d} obs{v_str}")
        if obs > 0:
            has_any = True

    if not has_any:
        print("\n⚠  No velocity data found at any sample point.")
        sys.exit(1)

    print(f"\n✅ Exploration complete. Run 10_extract.py for full extraction.")


if __name__ == "__main__":
    main()
