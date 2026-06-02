#!/usr/bin/env python3
"""Scarp — 90m scoring pipeline with candidate selection.

Reads all intermediate layers, computes weighted-additive score on a 90m grid,
selects up to 120 candidate sensor locations with regional fairness.

Usage:
    cd C:/WorkArea/AI/scarp
    uv run --project prep python prep/50_score_zones.py
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize, shapes
from rasterio.transform import from_bounds
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import Point, shape, mapping

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROC = REPO_ROOT / "data" / "processed"
INTERMEDIATE = DATA_PROC / "intermediate"

# ---------------------------------------------------------------------------
# Configuration (proven, do not deviate)
# ---------------------------------------------------------------------------
TARGET_CRS = "EPSG:3338"
CELL_SIZE = 90
COARSE_CELL_SIZE = 500
RELIEF_SIZE = 11  # cells at 90m ≈ 1km window

PROXIMITY_DECAY_KM = 5.0
COVERAGE_BUFFER_M = 15_000
COASTAL_MAX_DIST_KM = 15.0
NEIGHBORHOOD_SIZE = 45  # cells at 90m ≈ 4km
MAX_CANDIDATES = 120
INFLUENCE_RADIUS_M = 3000
N10_NODATA = 2147483647
SE_BOUNDS_3338 = (-250000, 300000, 1226203, 1559983)

# Weighted-additive weights (sum 1.0)
W_SUSC = 0.25
W_FJORD = 0.25
W_PROX = 0.20
W_VOLUME = 0.10
W_EXPO = 0.10
W_GAP = 0.10

# Tiled local maxima
TILE_SIZE = 2000
TILE_OVERLAP = 60

# Regional fairness
REGIONS = [
    {"name": "Anchorage/Kenai/PWS", "bounds_lon": (-150, -147), "bounds_lat": (60, 61.5)},
    {"name": "Columbia Glacier", "bounds_lon": (-148, -146), "bounds_lat": (60.5, 61.5)},
    {"name": "Yakutat/Glacier Bay", "bounds_lon": (-142, -137), "bounds_lat": (58, 60.5)},
    {"name": "Haines/Skagway", "bounds_lon": (-137, -135), "bounds_lat": (59, 60)},
    {"name": "Tracy Arm/SE fjords", "bounds_lon": (-135, -133), "bounds_lat": (57, 58.5)},
    {"name": "Juneau corridor", "bounds_lon": (-136, -133.5), "bounds_lat": (58, 59)},
    {"name": "Sitka/Baranof", "bounds_lon": (-136, -134), "bounds_lat": (56.5, 58)},
    {"name": "Ketchikan/SE tip", "bounds_lon": (-134, -130), "bounds_lat": (55, 57)},
]

# Gate checks
GATE_SITES = [
    ("Seward", 60.10, -149.44, 5),
    ("Glacier Bay", 58.75, -136.50, 10),
    ("Surprise Inlet", 60.13, -148.84, 15),
    ("Lituya Bay", 58.66, -137.57, 10),
    ("Taan Fiord", 60.14, -141.22, 20),
    ("Barry Arm", 61.13, -148.18, 35),
    ("Tracy Arm", 57.80, -133.55, 25),
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in km."""
    from math import radians, sin, cos, sqrt, asin
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    earth_radius_km = 6371.0
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return earth_radius_km * 2 * asin(sqrt(min(1.0, a)))


def find_region(lat: float, lon: float) -> str:
    """Assign a point to a named region."""
    for r in REGIONS:
        lon0, lon1 = r["bounds_lon"]
        lat0, lat1 = r["bounds_lat"]
        if lon0 <= lon <= lon1 and lat0 <= lat <= lat1:
            return r["name"]
    return "Other"


def load_n10(transform, rows, cols):
    """Load and resample USGS n10 susceptibility to 90m grid."""
    print("  Loading USGS n10 susceptibility ...")
    n10_path = DATA_RAW / "usgs_susc" / "n10_ak.tif"
    if not n10_path.exists():
        print("    ✗ n10 not found!")
        return np.zeros((rows, cols), dtype=np.float32), np.zeros((rows, cols), dtype=bool)

    with rasterio.open(n10_path) as src:
        n10 = np.zeros((rows, cols), dtype=np.float32)
        reproject(
            source=rasterio.band(src, 1),
            destination=n10,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=TARGET_CRS,
            resampling=Resampling.nearest,  # NOT average!
        )

    valid = (n10 > 0) & (n10 != N10_NODATA) & ~np.isnan(n10)
    suscept_norm = np.where(valid, np.clip(n10 / 81.0, 0, 1), 0).astype(np.float32)
    print(f"    {valid.sum():,} valid cells, max={n10[valid].max() if valid.any() else 0}")
    return suscept_norm, valid


def load_dem_and_relief(transform, rows, cols):
    """Load DEM tiles, resample to 90m, compute local relief."""
    print("  Loading DEM tiles and computing relief ...")
    dem_dir = DATA_RAW / "dem"
    if not dem_dir.exists():
        print("    ✗ No DEM directory!")
        return np.zeros((rows, cols), dtype=np.float32), np.zeros((rows, cols), dtype=bool)

    # Accumulate max elevation across tiles
    elevation = np.zeros((rows, cols), dtype=np.float32)
    dem_filled = np.zeros((rows, cols), dtype=bool)

    tiles = sorted(dem_dir.glob("*.tif"))
    tiles = [t for t in tiles if t.stat().st_size > 1_000_000]
    print(f"    Processing {len(tiles)} tiles ...")

    for i, tile in enumerate(tiles):
        try:
            with rasterio.open(tile) as src:
                tile_data = np.full((rows, cols), -9999.0, dtype=np.float32)
                reproject(
                    source=rasterio.band(src, 1),
                    destination=tile_data,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=TARGET_CRS,
                    resampling=Resampling.bilinear,
                )
            valid = tile_data > -9998
            dem_filled |= valid
            elevation = np.where(valid, np.maximum(elevation, tile_data), elevation)
        except Exception as e:
            print(f"    ✗ {tile.name}: {e}")
        if (i + 1) % 10 == 0:
            print(f"    ...{i + 1}/{len(tiles)} tiles")

    # Compute local relief (max - min in 11-cell window ≈ 1km)
    from scipy.ndimage import maximum_filter, minimum_filter
    relief = maximum_filter(elevation, size=RELIEF_SIZE) - \
             minimum_filter(elevation, size=RELIEF_SIZE)
    relief[~dem_filled] = 0

    print(f"    DEM coverage: {dem_filled.sum():,} cells ({dem_filled.mean() * 100:.1f}%)")
    return relief, dem_filled, elevation


def load_relief_normalized(transform, rows, cols):
    """Load relief from 25_relief.py output and normalize 0-1.

    Returns (relief_norm, relief_valid). Slope computation and the final
    volume_proxy product (relief_norm × slope_norm) happen in main() to
    avoid loading the DEM twice.
    """
    print("  Loading relief raster (25_relief.py output) ...")

    # --- Load relief raster from 25_relief.py ---
    relief_path = INTERMEDIATE / "relief_3338.tif"
    if not relief_path.exists():
        print("    ✗ relief_3338.tif not found (run 25_relief first)")
        return np.zeros((rows, cols), dtype=np.float32), np.zeros((rows, cols), dtype=bool)

    with rasterio.open(relief_path) as src:
        relief = np.zeros((rows, cols), dtype=np.float32)
        reproject(
            source=rasterio.band(src, 1),
            destination=relief,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=TARGET_CRS,
            resampling=Resampling.bilinear,
        )
    relief_valid = relief > 0
    print(f"    Relief: {relief_valid.sum():,} valid cells, "
          f"range 0–{relief[relief_valid].max():.0f} m")

    # Normalise relief 0-1
    relief_max = relief[relief_valid].max() if relief_valid.any() else 1.0
    relief_norm = np.where(relief_valid, relief / max(relief_max, 1e-9), 0).astype(np.float32)

    # --- Compute slope from the in-memory elevation grid ---
    # (already loaded by load_dem_and_relief above — we need elevation as arg)
    # Since elevation is computed inside load_dem_and_relief and returned,
    # we compute slope here using the same grid parameters.
    # To avoid loading DEM twice, slope is computed inline in main() below.
    # This function returns the relief part; main() combines with slope.
    return relief_norm, relief_valid


def load_coast_distance(transform, rows, cols):
    """Compute distance to coastline. Uses n10 land mask as coastline proxy."""
    print("  Computing coast distance ...")
    n10_path = DATA_RAW / "usgs_susc" / "n10_ak.tif"
    if not n10_path.exists():
        print("    ✗ n10 not found for coast proxy")
        return np.zeros((rows, cols), dtype=np.float32)

    with rasterio.open(n10_path) as src:
        n10 = np.zeros((rows, cols), dtype=np.float32)
        reproject(
            source=rasterio.band(src, 1),
            destination=n10,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=TARGET_CRS,
            resampling=Resampling.nearest,
        )

    land = (n10 > 0) & (n10 != N10_NODATA) & ~np.isnan(n10)
    from scipy.ndimage import distance_transform_edt
    dist_cells = distance_transform_edt(~land)
    coast_dist_m = dist_cells * CELL_SIZE

    # For ocean cells, use distance from land
    ocean_dist = distance_transform_edt(land)
    coast_dist_m = np.where(~land, ocean_dist * CELL_SIZE, coast_dist_m)

    print(f"    Coast distance: 0-{coast_dist_m[land].max() / 1000:.0f} km")
    return coast_dist_m


def load_coarse_layer(path, transform90m, rows, cols, label):
    """Load a 500m raster and upsample to 90m via bilinear."""
    print(f"  Loading {label} ...")
    if not path.exists():
        print(f"    ✗ {path.name} not found")
        return np.zeros((rows, cols), dtype=np.float32)

    with rasterio.open(path) as src:
        data = np.zeros((rows, cols), dtype=np.float32)
        reproject(
            source=rasterio.band(src, 1),
            destination=data,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform90m,
            dst_crs=TARGET_CRS,
            resampling=Resampling.bilinear,
        )
    print(f"    Range: {data[data > 0].min():.3f} - {data.max():.3f}" if (data > 0).any() else "    All zeros")
    return data


def compute_proximity(transform, rows, cols):
    """Compute exp(-distance/5km) from known slides."""
    print("  Computing slide proximity ...")
    slides_path = INTERMEDIATE / "all_slides_3338.geojson"
    if not slides_path.exists():
        print("    ✗ all_slides_3338 not found")
        return np.zeros((rows, cols), dtype=np.float32)

    slides = gpd.read_file(slides_path)
    shapes_list = [(geom, 1.0) for geom in slides.geometry if geom is not None and not geom.is_empty]
    if not shapes_list:
        return np.zeros((rows, cols), dtype=np.float32)

    slide_mask = rasterize(
        shapes_list,
        out_shape=(rows, cols),
        transform=transform,
        fill=0,
        dtype="float32",
    )

    from scipy.ndimage import distance_transform_edt
    dist_cells = distance_transform_edt(slide_mask == 0)
    dist_km = dist_cells * CELL_SIZE / 1000.0
    proximity = np.exp(-dist_km / PROXIMITY_DECAY_KM)

    print(f"    Proximity range: {proximity.min():.3f} - {proximity.max():.3f}")
    return proximity


def tiled_local_maxima(score, valid, tile_size, overlap, neighborhood):
    """Find local maxima in score grid using tiled processing."""
    rows, cols = score.shape
    candidates = []

    for r_start in range(0, rows, tile_size - overlap):
        for c_start in range(0, cols, tile_size - overlap):
            r_end = min(r_start + tile_size, rows)
            c_end = min(c_start + tile_size, cols)

            tile_score = score[r_start:r_end, c_start:c_end]
            tile_valid = valid[r_start:r_end, c_start:c_end]

            if tile_valid.sum() == 0:
                continue

            # Find local maxima within neighborhood
            from scipy.ndimage import maximum_filter
            local_max = maximum_filter(tile_score, size=neighborhood)
            is_max = (tile_score == local_max) & tile_valid & (tile_score > 0)

            # Get 90th percentile threshold for this tile
            if tile_valid.sum() > 100:
                threshold = np.percentile(tile_score[tile_valid], 90)
            else:
                threshold = 0

            rows_idx, cols_idx = np.where(is_max & (tile_score >= threshold))
            for lr, lc in zip(rows_idx, cols_idx):
                gr, gc = r_start + lr, c_start + lc
                candidates.append((gr, gc, float(tile_score[lr, lc])))

    # Sort by score descending
    candidates.sort(key=lambda x: -x[2])
    print(f"    Raw local maxima: {len(candidates)}")
    return candidates


def greedy_nms(candidates, grid_shape, min_dist_cells):
    """Non-maximum suppression with minimum distance constraint."""
    rows, cols = grid_shape
    taken = np.zeros((rows, cols), dtype=bool)
    result = []

    for r, c, s in candidates:
        if taken[r, c]:
            continue
        # Check neighborhood
        r0 = max(0, r - min_dist_cells)
        r1 = min(rows, r + min_dist_cells + 1)
        c0 = max(0, c - min_dist_cells)
        c1 = min(cols, c + min_dist_cells + 1)
        if taken[r0:r1, c0:c1].any():
            continue

        result.append((r, c, s))
        taken[r0:r1, c0:c1] = True

    return result


def main() -> None:
    print("=== 50_score_zones ===\n")

    xmin, ymin, xmax, ymax = SE_BOUNDS_3338
    cols = int((xmax - xmin) / CELL_SIZE)
    rows = int((ymax - ymin) / CELL_SIZE)
    transform = from_bounds(xmin, ymin, xmax, ymax, cols, rows)
    print(f"  Grid: {cols}×{rows} = {cols * rows / 1e6:.1f}M cells at {CELL_SIZE}m\n")

    # --- Load all layers ---
    suscept_norm, n10_valid = load_n10(transform, rows, cols)
    relief, dem_filled, elevation = load_dem_and_relief(transform, rows, cols)
    relief_norm, relief_valid = load_relief_normalized(transform, rows, cols)
    coast_dist_m = load_coast_distance(transform, rows, cols)
    proximity = compute_proximity(transform, rows, cols)
    coverage = load_coarse_layer(
        INTERMEDIATE / "coverage_mask_3338.tif", transform, rows, cols, "coverage"
    )
    exposure = load_coarse_layer(
        INTERMEDIATE / "exposure_3338.tif", transform, rows, cols, "exposure"
    )

    # --- Compute scoring components ---
    print("\n  Computing score ...")

    # Fjord wall: relief × water proximity (uses in-memory relief from DEM)
    fjord_wall = (
        np.clip(relief / 500.0, 0, 1)
        * np.clip(1.0 - coast_dist_m / 5000.0, 0, 1)
    )
    fjord_wall[~dem_filled] = 0

    # Compute slope from in-memory elevation for volume proxy
    dy, dx = np.gradient(elevation, float(CELL_SIZE))
    slope_deg = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))
    slope_deg[~dem_filled] = 0
    slope_valid = slope_deg > 0
    slope_max = slope_deg[slope_valid].max() if slope_valid.any() else 1.0
    slope_norm = np.where(slope_valid, slope_deg / max(slope_max, 1e-9), 0).astype(np.float32)

    # Volume proxy: normalized relief × normalized slope
    volume_proxy = (relief_norm * slope_norm).astype(np.float32)
    volume_proxy[~dem_filled] = 0
    vp_valid = volume_proxy > 0
    print(f"    Volume proxy: {vp_valid.sum():,} non-zero, "
          f"range 0–{volume_proxy[vp_valid].max():.4f}" if vp_valid.any() else
          "    Volume proxy: all zeros")

    # Valid land mask
    valid = n10_valid & dem_filled

    # Weighted-additive score (slope_factor replaced by volume_proxy)
    score = (
        W_SUSC * suscept_norm
        + W_FJORD * fjord_wall
        + W_PROX * proximity
        + W_VOLUME * volume_proxy
        + W_EXPO * exposure
        + W_GAP * (1.0 - coverage)
    )
    score[~valid] = 0

    # Normalize exposure for component reporting
    exposure_norm = np.where(exposure > 0, exposure / max(exposure.max(), 1e-9), 0)

    print(f"    Score range: {score[valid].min():.4f} - {score[valid].max():.4f}")
    print(f"    Score std: {score[valid].std():.4f}")

    # GATE C: score discrimination
    if score[valid].std() < 0.05:
        print("    ⚠ GATE C FAIL: score std < 0.05 (low discrimination)")
    else:
        print("    ✓ GATE C PASS: score std >= 0.05")

    # --- Candidate selection ---
    print("\n  Selecting candidates ...")

    # 1. Tiled local maxima
    raw_candidates = tiled_local_maxima(
        score, valid, TILE_SIZE, TILE_OVERLAP, NEIGHBORHOOD_SIZE
    )

    # 2. Greedy NMS with 4km minimum spacing
    nms_candidates = greedy_nms(raw_candidates, (rows, cols), NEIGHBORHOOD_SIZE)
    print(f"    After NMS: {len(nms_candidates)}")

    # 3. Coastal filter — drop >15km from coast
    coastal_candidates = []
    for r, c, s in nms_candidates:
        dist_km = coast_dist_m[r, c] / 1000.0
        if dist_km <= COASTAL_MAX_DIST_KM:
            coastal_candidates.append((r, c, s, dist_km))
    print(f"    After coastal filter: {len(coastal_candidates)}")

    # 4. Regional fairness
    from pyproj import Transformer
    transformer = Transformer.from_crs(TARGET_CRS, "EPSG:4326", always_xy=True)

    # Assign regions
    for i, (r, c, s, d) in enumerate(coastal_candidates):
        x = xmin + (c + 0.5) * CELL_SIZE
        y = ymax - (r + 0.5) * CELL_SIZE
        lon, lat = transformer.transform(x, y)
        coastal_candidates[i] = (r, c, s, d, lat, lon)

    # Sort by score and apply regional quotas
    coastal_candidates.sort(key=lambda x: -x[2])
    region_counts: dict[str, int] = {}
    max_per_region = max(20, MAX_CANDIDATES // len(REGIONS) + 5)
    final_candidates = []

    for r, c, s, d, lat, lon in coastal_candidates:
        region = find_region(lat, lon)
        count = region_counts.get(region, 0)
        if count < max_per_region:
            final_candidates.append((r, c, s, d, lat, lon, region))
            region_counts[region] = count + 1
        if len(final_candidates) >= MAX_CANDIDATES:
            break

    print(f"    Final candidates: {len(final_candidates)}")
    for region, count in sorted(region_counts.items()):
        print(f"      {region}: {count}")

    # --- Build output features ---
    print("\n  Building output features ...")
    features = []
    influence_features = []
    top10_features = []

    for rank, (r, c, s, coast_km, lat, lon, region) in enumerate(final_candidates, 1):
        # Get component values at this cell
        x = xmin + (c + 0.5) * CELL_SIZE
        y = ymax - (r + 0.5) * CELL_SIZE

        components = {
            "susceptibility": round(float(suscept_norm[r, c]), 3),
            "fjord_wall": round(float(fjord_wall[r, c]), 3),
            "volume_proxy": round(float(volume_proxy[r, c]), 3),
            "proximity": round(float(proximity[r, c]), 3),
            "exposure": round(float(exposure_norm[r, c]), 3),
            "coverage": round(float(coverage[r, c]), 3),
            "coast_dist_km": round(coast_km, 1),
        }

        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
            "properties": {
                "id": f"site-{rank:03d}",
                "rank": rank,
                "score": round(s, 4),
                "influence_radius_km": 3,
                "components": components,
            },
        }
        features.append(feature)

        if rank <= 10:
            top10_features.append(feature)

        # Influence circle (3km radius)
        center = Point(x, y)
        circle = center.buffer(INFLUENCE_RADIUS_M)
        # Convert to 4326 for frontend
        from shapely.ops import transform as shapely_transform
        circle_4326 = shapely_transform(transformer.transform, circle)
        influence_features.append({
            "type": "Feature",
            "geometry": mapping(circle_4326),
            "properties": feature["properties"],
        })

    # --- Write outputs ---
    print("\n  Writing outputs ...")

    # zones.geojson
    zones_fc = {"type": "FeatureCollection", "features": features}
    zones_path = DATA_PROC / "zones.geojson"
    zones_path.write_text(json.dumps(zones_fc))
    print(f"    ✓ zones.geojson: {len(features)} candidates")

    # candidates_influence.geojson
    inf_fc = {"type": "FeatureCollection", "features": influence_features}
    inf_path = DATA_PROC / "candidates_influence.geojson"
    inf_path.write_text(json.dumps(inf_fc))
    print(f"    ✓ candidates_influence.geojson: {len(influence_features)} polygons")

    # zones_top10.json
    top10_path = DATA_PROC / "zones_top10.json"
    top10_path.write_text(json.dumps(top10_features))
    print(f"    ✓ zones_top10.json: {len(top10_features)} features")

    # meta.json
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pipeline": "50_score_zones.py",
        "config": {
            "cell_size": CELL_SIZE,
            "crs": TARGET_CRS,
            "weights": {
                "susceptibility": W_SUSC, "fjord_wall": W_FJORD,
                "proximity": W_PROX, "volume_proxy": W_VOLUME,
                "exposure": W_EXPO, "gap": W_GAP,
            },
            "max_candidates": MAX_CANDIDATES,
            "influence_radius_m": INFLUENCE_RADIUS_M,
        },
        "stats": {
            "total_candidates": len(final_candidates),
            "score_range": [round(float(score[valid].min()), 4), round(float(score[valid].max()), 4)],
            "score_std": round(float(score[valid].std()), 4),
            "regions": region_counts,
        },
    }
    meta_path = DATA_PROC / "meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))
    print(f"    ✓ meta.json")

    # --- Gate checks ---
    print("\n  === GATE CHECKS ===")
    lats = [f["geometry"]["coordinates"][1] for f in features[:10]]
    lons = [f["geometry"]["coordinates"][0] for f in features[:10]]

    # GATE A: known site coverage
    for site_name, site_lat, site_lon, max_dist in GATE_SITES:
        min_dist = float("inf")
        for fl in features:
            fl_lat = fl["geometry"]["coordinates"][1]
            fl_lon = fl["geometry"]["coordinates"][0]
            d = haversine_km(site_lat, site_lon, fl_lat, fl_lon)
            min_dist = min(min_dist, d)
        status = "✓" if min_dist <= max_dist else "✗"
        print(f"    {status} {site_name}: {min_dist:.1f}km (threshold {max_dist}km)")

    # GATE B: top 10 not all Anchorage
    anchorage_count = sum(1 for lat in lats if lat > 61.2)
    gate_b = "✓" if anchorage_count < 10 else "✗"
    print(f"    {gate_b} GATE B: {anchorage_count}/10 top-10 in Anchorage area (lat>61.2)")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
