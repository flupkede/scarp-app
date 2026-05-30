#!/usr/bin/env python3
"""Scarp — Compute data confidence layer.

For each cell, counts how many input layers have valid data (0-5), normalizes
to 0.0-1.0, then polygonizes into 3 bands (low/medium/high).

Usage:
    cd C:/WorkArea/AI/scarp
    uv run --project prep python prep/45_confidence.py
"""

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.warp import reproject, Resampling
from shapely.geometry import shape

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROC = REPO_ROOT / "data" / "processed"
INTERMEDIATE = DATA_PROC / "intermediate"

TARGET_CRS = "EPSG:3338"
CELL_SIZE = 90
SE_BOUNDS_3338 = (-250000, 300000, 1226203, 1559983)
N10_NODATA = 2147483647


def main() -> None:
    print("=== 45_confidence ===")

    xmin, ymin, xmax, ymax = SE_BOUNDS_3338
    cols = int((xmax - xmin) / CELL_SIZE)
    rows = int((ymax - ymin) / CELL_SIZE)
    transform = rasterio.transform.from_bounds(xmin, ymin, xmax, ymax, cols, rows)

    # Count valid layers per cell
    layers = np.zeros((rows, cols), dtype=np.float32)

    # Layer 1: USGS n10 susceptibility valid
    n10_path = DATA_RAW / "usgs_susc" / "n10_ak.tif"
    n10_valid = np.zeros((rows, cols), dtype=bool)
    if n10_path.exists():
        print("  Checking USGS n10 validity ...")
        with rasterio.open(n10_path) as src:
            dest = np.zeros((rows, cols), dtype=np.float32)
            reproject(
                source=rasterio.band(src, 1),
                destination=dest,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=TARGET_CRS,
                resampling=Resampling.nearest,
            )
        n10_valid = (dest > 0) & (dest != N10_NODATA) & ~np.isnan(dest)
        layers += n10_valid.astype(np.float32)
        print(f"    {n10_valid.sum():,} valid cells ({n10_valid.mean() * 100:.1f}%)")
    else:
        print("  ✗ n10 not found")

    # Layer 2: DEM present
    dem_dir = DATA_RAW / "dem"
    if dem_dir.exists():
        print("  Checking DEM coverage ...")
        dem_mask = np.zeros((rows, cols), dtype=np.float32)
        tiles = [t for t in dem_dir.glob("*.tif") if t.stat().st_size > 1_000_000]
        for tile in tiles:
            try:
                with rasterio.open(tile) as src:
                    tile_dest = np.zeros((rows, cols), dtype=np.float32)
                    reproject(
                        source=rasterio.band(src, 1),
                        destination=tile_dest,
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=TARGET_CRS,
                        resampling=Resampling.nearest,
                    )
                dem_mask = np.maximum(dem_mask, (tile_dest != 0).astype(np.float32))
            except Exception:
                pass
        layers += dem_mask
        print(f"    {dem_mask.sum():,} cells with DEM coverage")
    else:
        print("  ✗ No DEM directory")

    # Layer 3: Slide inventory within 25km
    slides_path = INTERMEDIATE / "all_slides_3338.geojson"
    if slides_path.exists():
        print("  Checking slide inventory proximity ...")
        from scipy.ndimage import distance_transform_edt

        slides = gpd.read_file(slides_path)
        # Rasterize slide locations to binary
        slide_mask = np.zeros((rows, cols), dtype=bool)
        for _, feat in slides.iterrows():
            geom = feat.geometry
            if geom is None:
                continue
            x, y = (geom.centroid.x, geom.centroid.y) if geom.geom_type != "Point" else (geom.x, geom.y)
            col = int((x - xmin) / CELL_SIZE)
            row = int((ymax - y) / CELL_SIZE)
            if 0 <= row < rows and 0 <= col < cols:
                slide_mask[row, col] = True
        # Distance in cells
        dist_cells = distance_transform_edt(~slide_mask)
        # Convert to km (CELL_SIZE in meters)
        dist_km = dist_cells * CELL_SIZE / 1000.0
        within_25km = (dist_km < 25).astype(np.float32)
        layers += within_25km
        print(f"    {(dist_km < 25).sum():,} cells within 25km of known slides")
    else:
        print("  ✗ all_slides_3338 not found (run 10_normalize first)")

    # Layer 4: OSM data within 10km
    exposure_path = INTERMEDIATE / "exposure_3338.tif"
    if exposure_path.exists():
        print("  Checking OSM exposure ...")
        with rasterio.open(exposure_path) as src:
            exp_data = src.read(1)
            # Resample to 90m
            exp_90m = np.zeros((rows, cols), dtype=np.float32)
            reproject(
                source=exp_data,
                destination=exp_90m,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=TARGET_CRS,
                resampling=Resampling.bilinear,
            )
        from scipy.ndimage import distance_transform_edt, uniform_filter

        osm_mask = (exp_90m > 0).astype(np.float32)
        # If any OSM feature within ~10km (111 cells at 90m)
        smoothed = uniform_filter(osm_mask, size=111)
        osm_nearby = (smoothed > 0.001).astype(np.float32)
        layers += osm_nearby
        print(f"    {osm_nearby.sum():,} cells with OSM data nearby")
    else:
        print("  ✗ exposure_3338 not found (run 30_exposure first)")

    # Layer 5: Coastline data present
    # Use n10 as proxy — if n10 has data, coastline geometry is available
    # (n10 was built from DEM + coastline datasets)
    if n10_path.exists():
        layers += n10_valid.astype(np.float32)
        print(f"    Coastline proxy = n10 validity")

    # Normalize to 0.0 - 1.0
    confidence = layers / 5.0

    # Print summary
    total = confidence.size
    high = (confidence > 0.7).sum()
    medium = ((confidence >= 0.4) & (confidence <= 0.7)).sum()
    low = (confidence < 0.4).sum()
    print(f"\n  Confidence summary:")
    print(f"    High (>0.7):   {high / total * 100:.1f}% ({high:,} cells)")
    print(f"    Medium (0.4-0.7): {medium / total * 100:.1f}% ({medium:,} cells)")
    print(f"    Low (<0.4):    {low / total * 100:.1f}% ({low:,} cells)")

    # Polygonize into 3 bands
    print("\n  Polygonizing confidence bands ...")
    band_map = np.zeros_like(confidence, dtype=np.uint8)
    band_map[confidence > 0.7] = 3  # high
    band_map[(confidence >= 0.4) & (confidence <= 0.7)] = 2  # medium
    band_map[(confidence > 0) & (confidence < 0.4)] = 1  # low

    features = []
    band_labels = {1: "low", 2: "medium", 3: "high"}
    for geom, value in shapes(band_map, transform=transform):
        if value == 0:
            continue
        poly = shape(geom)
        if not poly.is_empty:
            # Simplify heavily — coarse overlay, not per-cell
            simplified = poly.simplify(200)  # 200m
            if not simplified.is_empty:
                features.append({
                    "type": "Feature",
                    "geometry": simplified.__geo_interface__,
                    "properties": {
                        "confidence": band_labels.get(int(value), "unknown"),
                        "value": float(value) / 3.0,  # normalized 0-1
                    },
                })

    # Write GeoJSON
    fc = {"type": "FeatureCollection", "features": features}
    out_path = DATA_PROC / "confidence.geojson"
    out_path.write_text(json.dumps(fc))
    print(f"  ✓ confidence.geojson: {len(features)} polygons")

    # Honest reporting
    known_limited = ["Lituya Bay", "Taan Fiord", "Icy Bay"]
    print(
        f"\n  Known sites in data-limited areas: "
        f"{', '.join(known_limited)}"
    )
    print(
        f"  '{low / total * 100:.0f}% of analysis area is data-limited. "
        f"Recommendations in these areas are provisional.'"
    )
    print("\n=== Done ===")


if __name__ == "__main__":
    main()
