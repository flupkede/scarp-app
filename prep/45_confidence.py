#!/usr/bin/env python3
"""Scarp — Compute data-confidence layer on the COARSE 500m grid.

For each 500m cell, counts how many of 5 input layers have valid data,
normalises to 0.0–1.0, bands into low / medium / high, polygonises,
dissolves into a few big polygons, and reprojects to EPSG:4326.

Usage:
    cd C:/WorkArea/AI/scarp
    uv run --project prep python prep/45_confidence.py
    uv run --project prep python prep/45_confidence.py --force
"""

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize, shapes
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROC = REPO_ROOT / "data" / "processed"
INTERMEDIATE = DATA_PROC / "intermediate"

# ---------------------------------------------------------------------------
# Configuration — mirrors 50_score_zones.py exactly
# ---------------------------------------------------------------------------
TARGET_CRS = "EPSG:3338"
COARSE_CELL_SIZE = 500  # 500m — NOT 90m; this is a soft overlay
SE_BOUNDS_3338 = (-250000, 300000, 1226203, 1559983)
N10_NODATA = 2147483647

# Band thresholds
LOW_MAX = 0.4
HIGH_MIN = 0.7

# Geometry simplification tolerance (metres, in 3338)
# 5km for a coarse overlay — keeps file size small
SIMPLIFY_TOL = 5000

# Known sites for honest reporting (name, lon, lat)
KNOWN_SITES = [
    ("Lituya Bay", -137.57, 58.66),
    ("Taan Fiord", -141.22, 60.14),
    ("Tracy Arm", -133.55, 57.80),
    ("Barry Arm", -148.18, 61.13),
]


def main() -> None:
    force = "--force" in sys.argv
    out_path = DATA_PROC / "confidence.geojson"

    # Guard: skip if output exists (unless --force)
    if out_path.exists() and not force:
        print(f"=== 45_confidence: {out_path.name} exists (use --force to rebuild) ===")
        return

    print("=== 45_confidence (500m coarse grid) ===\n")

    xmin, ymin, xmax, ymax = SE_BOUNDS_3338
    cols = int((xmax - xmin) / COARSE_CELL_SIZE)
    rows = int((ymax - ymin) / COARSE_CELL_SIZE)
    transform = from_bounds(xmin, ymin, xmax, ymax, cols, rows)
    print(f"  Grid: {cols} x {rows} = {cols * rows:,} cells at {COARSE_CELL_SIZE}m\n")

    # Accumulator: count of valid layers per cell
    valid_count = np.zeros((rows, cols), dtype=np.uint8)

    # ------------------------------------------------------------------
    # 1. susceptibility_valid: n10_ak.tif resampled to 500m
    # ------------------------------------------------------------------
    print("  [1/5] USGS n10 susceptibility ...")
    n10_path = DATA_RAW / "usgs_susc" / "n10_ak.tif"
    n10_valid = np.zeros((rows, cols), dtype=bool)
    if n10_path.exists():
        with rasterio.open(n10_path) as src:
            dest = np.full((rows, cols), N10_NODATA, dtype=np.float32)
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
        valid_count += n10_valid.astype(np.uint8)
        print(f"    {n10_valid.sum():,} valid cells ({n10_valid.mean() * 100:.1f}%)")
    else:
        print("    n10_ak.tif not found")

    # ------------------------------------------------------------------
    # 2. dem_present: any DEM tile covers the cell
    # ------------------------------------------------------------------
    print("  [2/5] DEM coverage ...")
    dem_dir = DATA_RAW / "dem"
    dem_filled = np.zeros((rows, cols), dtype=bool)
    if dem_dir.exists():
        tiles = sorted(t for t in dem_dir.glob("*.tif") if t.stat().st_size > 1_000_000)
        print(f"    {len(tiles)} tiles to process")
        for i, tile in enumerate(tiles):
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
                dem_filled |= tile_dest != 0
            except Exception as e:
                print(f"    skip {tile.name}: {e}")
            if (i + 1) % 10 == 0:
                print(f"    ...{i + 1}/{len(tiles)} tiles")
        valid_count += dem_filled.astype(np.uint8)
        print(f"    {dem_filled.sum():,} cells with DEM ({dem_filled.mean() * 100:.1f}%)")
    else:
        print("    No DEM directory")

    # ------------------------------------------------------------------
    # 3. slide_inventory_within_25km
    # ------------------------------------------------------------------
    print("  [3/5] Slide inventory proximity ...")
    slides_path = INTERMEDIATE / "all_slides_3338.geojson"
    if slides_path.exists():
        from scipy.ndimage import distance_transform_edt

        slides = gpd.read_file(slides_path)
        shapes_list = [
            (geom, 1) for geom in slides.geometry if geom is not None and not geom.is_empty
        ]
        if shapes_list:
            slide_mask = rasterize(
                shapes_list,
                out_shape=(rows, cols),
                transform=transform,
                fill=0,
                dtype="uint8",
            )
            dist_cells = distance_transform_edt(slide_mask == 0)
            dist_km = dist_cells * COARSE_CELL_SIZE / 1000.0
            within_25km = dist_km <= 25.0
            valid_count += within_25km.astype(np.uint8)
            print(f"    {within_25km.sum():,} cells within 25km of known slides")
        else:
            print("    No slide geometries to rasterize")
    else:
        print("    all_slides_3338.geojson not found")

    # ------------------------------------------------------------------
    # 4. osm_present_within_10km (exposure_3338.tif as proxy)
    # ------------------------------------------------------------------
    print("  [4/5] OSM data proximity (exposure proxy) ...")
    exposure_path = INTERMEDIATE / "exposure_3338.tif"
    if exposure_path.exists():
        from scipy.ndimage import distance_transform_edt

        with rasterio.open(exposure_path) as src:
            exp_500m = np.zeros((rows, cols), dtype=np.float32)
            reproject(
                source=rasterio.band(src, 1),
                destination=exp_500m,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=TARGET_CRS,
                resampling=Resampling.bilinear,
            )
        osm_mask = exp_500m > 0
        # Dilate: distance from any OSM feature
        dist_cells = distance_transform_edt(~osm_mask)
        dist_km = dist_cells * COARSE_CELL_SIZE / 1000.0
        osm_nearby = dist_km <= 10.0
        valid_count += osm_nearby.astype(np.uint8)
        print(f"    {osm_nearby.sum():,} cells within 10km of OSM features")
    else:
        print("    exposure_3338.tif not found")

    # ------------------------------------------------------------------
    # 5. coastline_present: coastline_seak_3338.geojson buffered 50km
    # ------------------------------------------------------------------
    print("  [5/5] Coastline proximity ...")
    coastline_path = INTERMEDIATE / "coastline_seak_3338.geojson"
    if coastline_path.exists():
        from scipy.ndimage import distance_transform_edt

        coast_gdf = gpd.read_file(coastline_path)
        coast_shapes = [
            (geom, 1) for geom in coast_gdf.geometry if geom is not None and not geom.is_empty
        ]
        if coast_shapes:
            coast_mask = rasterize(
                coast_shapes,
                out_shape=(rows, cols),
                transform=transform,
                fill=0,
                dtype="uint8",
            )
            dist_cells = distance_transform_edt(coast_mask == 0)
            dist_km = dist_cells * COARSE_CELL_SIZE / 1000.0
            coast_nearby = dist_km <= 50.0
            valid_count += coast_nearby.astype(np.uint8)
            print(f"    {coast_nearby.sum():,} cells within 50km of coastline")
        else:
            print("    No coastline geometries")
    else:
        print("    coastline_seak_3338.geojson not found — using n10 as fallback")
        # Fallback: n10 validity as coastline proxy
        if n10_valid.any():
            valid_count += n10_valid.astype(np.uint8)
            print(f"    Coastline proxy = n10 validity ({n10_valid.sum():,} cells)")
        else:
            print("    No coastline data available")

    # ------------------------------------------------------------------
    # Confidence = count / 5.0
    # ------------------------------------------------------------------
    confidence = valid_count.astype(np.float32) / 5.0

    # ------------------------------------------------------------------
    # LAND MASK — we only search for landslides on land / fjord walls,
    # NOT in the open ocean.  Without this, low-data cells over the
    # Bering Sea get a "low confidence" band and the hatch overlay ends
    # up floating in open water (which is nonsensical — there is nothing
    # to monitor there).  A cell is part of the study area only if it has
    # terrain data: DEM coverage OR USGS susceptibility validity.  Open
    # sea has neither.  The land mask is dilated by a few cells so the
    # immediate fjord-coast zone is retained.
    # ------------------------------------------------------------------
    print("\n  Applying land mask (n10 terrain coverage) ...")
    from scipy.ndimage import binary_dilation

    # NOTE: dem_filled is unreliable as a land mask — reproject fills the
    # whole destination grid so it reads ~100%.  The USGS n10 susceptibility
    # raster, by contrast, only has valid values over actual Alaska terrain
    # (~17% of the bounding box), so it is the honest "is this land?" signal.
    land_mask = n10_valid
    # Dilate ~5 cells (= 2.5 km at 500m) so the coastal fjord strip the
    # sites actually sit on is kept, without bleeding far out to sea.
    land_mask = binary_dilation(land_mask, iterations=5)
    confidence[~land_mask] = -1.0  # sentinel: outside study area → no band
    print(
        f"    {land_mask.sum():,} land cells ({land_mask.mean() * 100:.1f}%); "
        f"{(~land_mask).sum():,} sea/out-of-area cells masked out"
    )

    # Percentages reported over LAND cells only (the meaningful denominator)
    land_cells = int(land_mask.sum()) or 1
    high_pct = ((confidence > HIGH_MIN) & land_mask).sum() / land_cells * 100
    med_pct = (
        (confidence >= LOW_MAX) & (confidence <= HIGH_MIN) & land_mask
    ).sum() / land_cells * 100
    low_pct = ((confidence >= 0) & (confidence < LOW_MAX) & land_mask).sum() / land_cells * 100
    print(f"\n  Confidence bands (over land only):")
    print(f"    High   (> {HIGH_MIN}): {high_pct:.1f}%")
    print(f"    Medium ({LOW_MAX}–{HIGH_MIN}): {med_pct:.1f}%")
    print(f"    Low    (< {LOW_MAX}):  {low_pct:.1f}%")

    # ------------------------------------------------------------------
    # Polygonise per band, dissolve, simplify, reproject to 4326
    # ------------------------------------------------------------------
    print("\n  Polygonising + dissolving ...")

    # Sentinel-masked (sea / out-of-area) cells have confidence == -1.0 and
    # therefore fall into NO band — the >= 0 guards below exclude them.
    band_map = np.zeros((rows, cols), dtype=np.uint8)
    band_map[(confidence >= 0) & (confidence < LOW_MAX)] = 1   # low
    band_map[(confidence >= LOW_MAX) & (confidence <= HIGH_MIN)] = 2  # medium
    # high (>0.7) = no overlay in frontend, but we emit it for completeness
    band_map[confidence > HIGH_MIN] = 3  # high

    band_labels = {1: "low", 2: "medium", 3: "high"}
    band_min = {1: 0.0, 2: LOW_MAX, 3: HIGH_MIN}

    # Downsample band_map to 2km cells before polygonising — keeps vertices
    # manageable.  The overlay is coarse by design; 2km resolution is plenty.
    from scipy.ndimage import zoom as scipy_zoom
    DECIMATE = 8  # 500m * 8 = 4000m cells
    coarse_bands = scipy_zoom(band_map, 1.0 / DECIMATE, order=0).astype(np.uint8)
    coarse_rows, coarse_cols = coarse_bands.shape

    coarse_transform = from_bounds(xmin, ymin, xmax, ymax, coarse_cols, coarse_rows)
    print(f"    Decimated to {coarse_cols}x{coarse_rows} grid ({DECIMATE * COARSE_CELL_SIZE // 1000}km cells)")

    features = []
    for band_val in [1, 2, 3]:
        mask = coarse_bands == band_val
        if not mask.any():
            print(f"    {band_labels[band_val]}: empty, skipped")
            continue

        # Polygonise all cells in this band
        band_polys = []
        for geom, val in shapes(mask.astype(np.uint8), mask=mask, transform=coarse_transform):
            if val == 0:
                continue
            poly = shape(geom)
            if not poly.is_empty:
                band_polys.append(poly)

        if not band_polys:
            continue

        # Dissolve into one (or a few) big polygon(s)
        dissolved = unary_union(band_polys)

        # Simplify heavily — this is a coarse overlay
        simplified = dissolved.simplify(SIMPLIFY_TOL)

        if simplified.is_empty:
            continue

        features.append({
            "type": "Feature",
            "geometry": mapping(simplified),
            "properties": {
                "band": band_labels[band_val],
                "confidence_min": band_min[band_val],
            },
        })
        print(f"    {band_labels[band_val]}: dissolved, {len(features)} feature(s)")

    # Reproject to EPSG:4326 for the frontend
    print("  Reprojecting to EPSG:4326 ...")
    from pyproj import Transformer
    from shapely.ops import transform as shapely_transform

    transformer = Transformer.from_crs(TARGET_CRS, "EPSG:4326", always_xy=True)

    for feat in features:
        geom_4326 = shapely_transform(transformer.transform, shape(feat["geometry"]))
        feat["geometry"] = mapping(geom_4326)

    fc = {"type": "FeatureCollection", "features": features}
    out_path.write_text(json.dumps(fc))

    size_kb = out_path.stat().st_size / 1024
    print(f"  -> confidence.geojson: {len(features)} features, {size_kb:.0f} KB")

    # ------------------------------------------------------------------
    # Honest reporting — sample the 4 famous sites
    # ------------------------------------------------------------------
    print("\n  === HONEST REPORTING ===")

    site_bands = []
    for name, lon, lat in KNOWN_SITES:
        # Convert lon/lat -> 3338 -> pixel coords
        x3338, y3338 = Transformer.from_crs(
            "EPSG:4326", TARGET_CRS, always_xy=True
        ).transform(lon, lat)
        col = int((x3338 - xmin) / COARSE_CELL_SIZE)
        row = int((ymax - y3338) / COARSE_CELL_SIZE)
        if 0 <= row < rows and 0 <= col < cols:
            c = float(confidence[row, col])
            b = band_labels.get(int(band_map[row, col]), "none")
        else:
            c = -1.0
            b = "out_of_bounds"
        site_bands.append((name, b, c))
        print(f"    {name}: confidence={c:.2f}, band={b}")

    limited_sites = [name for name, b, _ in site_bands if b in ("low", "medium")]
    limited_str = ", ".join(limited_sites) if limited_sites else "none"

    print(
        f"\n  >> {high_pct:.0f}% high-confidence, {low_pct + med_pct:.0f}% data-limited. "
        f"Known sites in data-limited areas: [{limited_str}]"
    )
    print("\n=== Done ===")


if __name__ == "__main__":
    main()
