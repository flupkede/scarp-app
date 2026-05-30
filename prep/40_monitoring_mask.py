#!/usr/bin/env python3
"""Scarp — Compute ramped monitoring coverage mask.

Reads station locations, computes distance from each cell to nearest station,
and creates a ramped coverage mask (1.0 at station → 0.0 at 15km).

Usage:
    cd C:/WorkArea/AI/scarp
    uv run --project prep python prep/40_monitoring_mask.py
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from scipy.ndimage import distance_transform_edt

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PROC = REPO_ROOT / "data" / "processed"
INTERMEDIATE = DATA_PROC / "intermediate"

TARGET_CRS = "EPSG:3338"
CELL_SIZE = 500
COVERAGE_BUFFER_M = 15_000  # 15km ramp
SE_BOUNDS_3338 = (-250000, 300000, 1226203, 1559983)


def main() -> None:
    print("=== 40_monitoring_mask ===")

    stations_path = INTERMEDIATE / "stations_3338.geojson"
    if not stations_path.exists():
        print(f"  ✗ {stations_path} not found (run 10_normalize first)")
        return

    stations = gpd.read_file(stations_path)
    print(f"  Loaded {len(stations)} stations")

    # Build grid
    xmin, ymin, xmax, ymax = SE_BOUNDS_3338
    cols = int((xmax - xmin) / CELL_SIZE)
    rows = int((ymax - ymin) / CELL_SIZE)
    transform = from_bounds(xmin, ymin, xmax, ymax, cols, rows)

    # Rasterize station locations to binary mask
    station_mask = np.zeros((rows, cols), dtype=bool)
    for _, row in stations.iterrows():
        geom = row.geometry
        if geom is None:
            continue
        x, y = geom.x, geom.y
        col = int((x - xmin) / CELL_SIZE)
        row_idx = int((ymax - y) / CELL_SIZE)
        if 0 <= row_idx < rows and 0 <= col < cols:
            station_mask[row_idx, col] = True

    # Distance transform: distance from each cell to nearest station (in cells)
    dist_cells = distance_transform_edt(~station_mask)

    # Convert to meters
    dist_m = dist_cells * CELL_SIZE

    # Ramped coverage: 1.0 at station → linear decay → 0.0 at COVERAGE_BUFFER_M
    coverage = np.clip(1.0 - dist_m / COVERAGE_BUFFER_M, 0.0, 1.0)

    # Write output
    INTERMEDIATE.mkdir(parents=True, exist_ok=True)
    out_path = INTERMEDIATE / "coverage_mask_3338.tif"

    with rasterio.open(
        out_path,
        "w",
        driver="GTiff",
        height=rows,
        width=cols,
        count=1,
        dtype="float32",
        crs=TARGET_CRS,
        transform=transform,
        nodata=-1,
    ) as dst:
        dst.write(coverage.astype(np.float32), 1)

    covered_pct = (coverage > 0).sum() / coverage.size * 100
    mean_cov = coverage[coverage > 0].mean() if (coverage > 0).any() else 0
    print(f"  ✓ coverage_mask_3338: {cols}×{rows} cells → {out_path.name}")
    print(f"    {covered_pct:.1f}% of area has some coverage (mean={mean_cov:.2f})")
    print("\n=== Done ===")


if __name__ == "__main__":
    main()
