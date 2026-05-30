#!/usr/bin/env python3
"""Scarp — Compute steep slopes from DEM tiles.

Processes each DEM tile independently (memory-safe), computes slope via
numpy gradient, reclassifies >25° as steep, vectorizes to polygons.

Usage:
    cd C:/WorkArea/AI/scarp
    uv run --project prep python prep/20_slope.py
"""

from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.transform import from_bounds
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import shape, MultiPolygon
from shapely.validation import make_valid

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROC = REPO_ROOT / "data" / "processed"
INTERMEDIATE = DATA_PROC / "intermediate"

TARGET_CRS = "EPSG:3338"
SLOPE_THRESHOLD = 25.0
TILE_MIN_BYTES = 1_000_000  # skip <1MB stubs
SIMPLIFY_TOLERANCE = 50  # meters in EPSG:3338
RESAMPLE_RES = 100  # resample to 100m for slope (memory-safe)


def compute_slope(elevation: np.ndarray, cellsize: float) -> np.ndarray:
    """Compute slope in degrees using numpy gradient."""
    dy, dx = np.gradient(elevation, cellsize)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    return np.degrees(slope_rad)


def process_tile(tile_path: Path) -> list[dict]:
    """Process a single DEM tile: reproject, slope, vectorize steep areas."""
    try:
        with rasterio.open(tile_path) as src:
            if src.crs is None:
                return []

            # Calculate target transform at 100m resolution
            transform, width, height = calculate_default_transform(
                src.crs, TARGET_CRS, src.width, src.height, *src.bounds,
                resolution=RESAMPLE_RES,
            )

            # Reproject
            data = np.zeros((height, width), dtype=np.float32)
            reproject(
                source=rasterio.band(src, 1),
                destination=data,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=TARGET_CRS,
                resampling=Resampling.bilinear,
            )

            # Mask nodata
            nodata = src.nodata
            if nodata is not None and not np.isnan(nodata):
                nodata_mask = data == nodata
            else:
                nodata_mask = np.zeros_like(data, dtype=bool)

            data[nodata_mask] = 0

            # Compute slope
            slope = compute_slope(data, float(RESAMPLE_RES))

            # Reclassify: >25° = 1, else 0
            steep = (slope > SLOPE_THRESHOLD).astype(np.uint8)
            steep[nodata_mask] = 0

            if steep.sum() == 0:
                return []

            # Vectorize
            results = []
            for geom, value in shapes(steep, transform=transform):
                if value == 1:
                    poly = shape(geom)
                    if not poly.is_valid:
                        poly = make_valid(poly)
                    if not poly.is_empty:
                        simplified = poly.simplify(SIMPLIFY_TOLERANCE)
                        if not simplified.is_empty:
                            results.append({
                                "type": "Feature",
                                "geometry": simplified.__geo_interface__,
                                "properties": {"slope_class": "steep"},
                            })

            return results
    except Exception as e:
        print(f"    ✗ Error processing {tile_path.name}: {e}")
        return []


def main() -> None:
    print("=== 20_slope ===")

    dem_dir = DATA_RAW / "dem"
    if not dem_dir.exists():
        print("  ✗ No DEM directory found")
        return

    tiles = sorted(dem_dir.glob("*.tif"))
    tiles = [t for t in tiles if t.stat().st_size >= TILE_MIN_BYTES]
    print(f"  Found {len(tiles)} valid DEM tiles (>{TILE_MIN_BYTES / 1e6:.0f} MB)")

    all_features: list[dict] = []
    for i, tile in enumerate(tiles):
        feats = process_tile(tile)
        all_features.extend(feats)
        n_polys = len(feats)
        print(f"  [{i + 1}/{len(tiles)}] {tile.name}: {n_polys} steep polygons")

    if not all_features:
        print("  ✗ No steep slopes found")
        return

    # Merge overlapping polygons
    print(f"\n  Dissolving {len(all_features)} steep polygons ...")
    import json
    import geopandas as gpd

    gdf = gpd.GeoDataFrame.from_features(all_features, crs=TARGET_CRS)
    gdf["geometry"] = gdf["geometry"].apply(lambda g: make_valid(g) if g else g)
    gdf = gdf[~gdf.is_empty].copy()

    # Dissolve into single geometry, then explode
    dissolved = gdf.dissolve(by="slope_class")
    dissolved = dissolved.explode(index_parts=False)
    dissolved = dissolved.reset_index(drop=True)

    # Simplify again after dissolve
    dissolved["geometry"] = dissolved["geometry"].simplify(SIMPLIFY_TOLERANCE)
    dissolved = dissolved[~dissolved.is_empty].copy()

    INTERMEDIATE.mkdir(parents=True, exist_ok=True)
    out_path = INTERMEDIATE / "steep_slopes_3338.geojson"
    dissolved.to_file(out_path, driver="GeoJSON")

    print(f"  ✓ steep_slopes_3338: {len(dissolved)} polygons → {out_path.name}")
    print(f"  Total steep area: {dissolved.geometry.area.sum() / 1e6:.0f} km²")
    print("\n=== Done ===")


if __name__ == "__main__":
    main()
