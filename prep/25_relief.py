#!/usr/bin/env python3
"""Scarp — Compute local vertical relief from DEM tiles.

Produces a relief raster (focal max − focal min over a ~500m window)
in EPSG:3338 at ~100m resolution. This relief layer is used by the
volume-proxy scoring component (relief × steepness → failure-mass proxy).

Usage:
    cd C:/WorkArea/AI/scarp
    uv run --project prep python prep/25_relief.py
"""

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import calculate_default_transform, reproject, Resampling
from scipy.ndimage import maximum_filter, minimum_filter

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROC = REPO_ROOT / "data" / "processed"
INTERMEDIATE = DATA_PROC / "intermediate"

TARGET_CRS = "EPSG:3338"
TARGET_RES = 100          # metres — same as 20_slope.py
TILE_MIN_BYTES = 1_000_000  # skip <1 MB stubs
RELIEF_WINDOW_M = 500     # window extent for focal range (~scale of a landslide)

# Derived: window size in grid cells
RELIEF_WINDOW_CELLS = max(1, round(RELIEF_WINDOW_M / TARGET_RES))
# Use odd size so the window is centred
if RELIEF_WINDOW_CELLS % 2 == 0:
    RELIEF_WINDOW_CELLS += 1


def merge_reprojected_tiles() -> tuple[np.ndarray, rasterio.Affine, np.ndarray]:
    """Merge all DEM tiles into a single EPSG:3338 array at TARGET_RES.

    Returns (elevation, transform, nodata_mask).
    """
    dem_dir = DATA_RAW / "dem"
    if not dem_dir.exists():
        raise FileNotFoundError(f"No DEM directory: {dem_dir}")

    tiles = sorted(dem_dir.glob("*.tif"))
    tiles = [t for t in tiles if t.stat().st_size >= TILE_MIN_BYTES]
    print(f"  Found {len(tiles)} valid DEM tiles (>{TILE_MIN_BYTES / 1e6:.0f} MB)")

    # First pass: determine union bounds at TARGET_RES
    all_bounds = []
    for tile in tiles:
        try:
            with rasterio.open(tile) as src:
                if src.crs is None:
                    continue
                t, w, h = calculate_default_transform(
                    src.crs, TARGET_CRS, src.width, src.height, *src.bounds,
                    resolution=TARGET_RES,
                )
                all_bounds.append((
                    t.c,                              # xmin
                    t.f + t.e * h,                    # ymin
                    t.c + t.a * w,                    # xmax
                    t.f,                              # ymax
                ))
        except Exception as e:
            print(f"    ✗ {tile.name}: {e}")

    if not all_bounds:
        raise RuntimeError("No valid tiles after filtering")

    xmin = min(b[0] for b in all_bounds)
    ymin = min(b[1] for b in all_bounds)
    xmax = max(b[2] for b in all_bounds)
    ymax = max(b[3] for b in all_bounds)

    cols = int(round((xmax - xmin) / TARGET_RES))
    rows = int(round((ymax - ymin) / TARGET_RES))
    transform = from_bounds(xmin, ymin, xmax, ymax, cols, rows)

    print(f"  Mosaic: {cols}×{rows} cells at {TARGET_RES}m "
          f"({cols * rows / 1e6:.1f}M cells)")

    # Second pass: accumulate max elevation (handle overlaps)
    elevation = np.full((rows, cols), np.nan, dtype=np.float32)
    filled = np.zeros((rows, cols), dtype=bool)

    for i, tile in enumerate(tiles):
        try:
            with rasterio.open(tile) as src:
                tile_data = np.full((rows, cols), np.nan, dtype=np.float32)
                reproject(
                    source=rasterio.band(src, 1),
                    destination=tile_data,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=TARGET_CRS,
                    resampling=Resampling.bilinear,
                )
                # Handle source nodata value (e.g. USGS 3DEP uses -999999)
                nodata_val = src.nodata
                if nodata_val is not None and not np.isnan(nodata_val):
                    tile_data[tile_data == nodata_val] = np.nan
            # Identify valid (non-NaN) pixels
            valid = ~np.isnan(tile_data)
            # Take max where overlapping
            elevation = np.where(
                valid & ~filled,
                tile_data,
                np.where(valid & filled, np.maximum(elevation, tile_data), elevation),
            )
            filled |= valid
        except Exception as e:
            print(f"    ✗ {tile.name}: {e}")
        if (i + 1) % 10 == 0:
            print(f"    ...{i + 1}/{len(tiles)} tiles")

    print(f"  DEM coverage: {filled.sum():,} cells ({filled.mean() * 100:.1f}%)")

    # Replace unfilled with NaN for nodata
    nodata_mask = ~filled
    elevation[nodata_mask] = np.nan

    return elevation, transform, nodata_mask


def compute_relief(elevation: np.ndarray) -> np.ndarray:
    """Local vertical relief = focal max − focal min over RELIEF_WINDOW_CELLS.

    NODATA cells are excluded from the focal operation (treated as NaN).
    """
    # Work with NaN-safe approach: replace NaN with -inf for max, +inf for min,
    # then mask afterwards
    elev_clean = elevation.copy()
    nodata = np.isnan(elev_clean)

    # For maximum filter: NaN → -inf so they never win
    elev_for_max = np.where(nodata, -np.inf, elev_clean)
    local_max = maximum_filter(elev_for_max, size=RELIEF_WINDOW_CELLS, mode='nearest')

    # For minimum filter: NaN → +inf so they never win
    elev_for_min = np.where(nodata, np.inf, elev_clean)
    local_min = minimum_filter(elev_for_min, size=RELIEF_WINDOW_CELLS, mode='nearest')

    relief = local_max - local_min

    # Where any input was NaN, relief is undefined
    relief[nodata] = np.nan

    # Clamp negative values (shouldn't happen, but guard)
    relief = np.clip(relief, 0, None)

    return relief.astype(np.float32)


def main() -> None:
    print("=== 25_relief ===\n")

    elevation, transform, nodata_mask = merge_reprojected_tiles()

    print(f"\n  Computing relief (window={RELIEF_WINDOW_CELLS} cells ≈ "
          f"{RELIEF_WINDOW_CELLS * TARGET_RES}m) ...")
    relief = compute_relief(elevation)

    valid = ~np.isnan(relief)
    if valid.any():
        print(f"    Relief range: {relief[valid].min():.0f} – {relief[valid].max():.0f} m")
        print(f"    Relief mean:  {relief[valid].mean():.0f} m")
        print(f"    Relief std:   {relief[valid].std():.0f} m")
    else:
        print("    ✗ No valid relief values!")
        return

    # Write GeoTIFF
    INTERMEDIATE.mkdir(parents=True, exist_ok=True)
    out_path = INTERMEDIATE / "relief_3338.tif"

    profile = {
        "driver": "GTiff",
        "width": relief.shape[1],
        "height": relief.shape[0],
        "count": 1,
        "dtype": "float32",
        "crs": TARGET_CRS,
        "transform": transform,
        "nodata": float(np.nan),
        "compress": "deflate",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
    }

    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(relief, 1)

    print(f"\n  ✓ relief_3338.tif → {out_path}")
    print(f"    ({out_path.stat().st_size / 1e6:.1f} MB)")
    print("\n=== Done ===")


if __name__ == "__main__":
    main()
