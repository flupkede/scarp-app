#!/usr/bin/env python3
"""Scarp — Compute human exposure layer from OSM data.

Parses Alaska PBF for buildings, roads, and tourism POIs, then creates
a 500m exposure raster with log-weighted values.

Uses osmium Python bindings (NOT pyrosm — Windows wheel issues).

Usage:
    cd C:/WorkArea/AI/scarp
    uv run --project prep python prep/30_exposure.py
"""

import json
from pathlib import Path

import numpy as np
import osmium
import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import transform_bounds
from scipy.ndimage import uniform_filter
from shapely.geometry import Point, LineString, shape, mapping

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROC = REPO_ROOT / "data" / "processed"
INTERMEDIATE = DATA_PROC / "intermediate"

TARGET_CRS = "EPSG:3338"
CELL_SIZE = 500  # coarse grid for exposure

# Analysis bounds (EPSG:3338)
SE_BOUNDS_3338 = (-250000, 300000, 1226203, 1559983)

ROAD_TYPES = {"trunk", "primary", "secondary", "tertiary", "residential"}


class OSMFeatureHandler(osmium.SimpleHandler):
    """Extract buildings, roads, and tourism POIs from PBF."""

    def __init__(self) -> None:
        super().__init__()
        self.buildings: list[tuple[float, float]] = []  # (lon, lat)
        self.road_segments: list[tuple[float, float, float, float]] = []  # lon1,lat1,lon2,lat2
        self.tourism_pois: list[tuple[float, float]] = []  # (lon, lat)

    def node(self, n: osmium.osm.Node) -> None:
        tags = {k: v for k, v in n.tags}
        if "building" in tags:
            self.buildings.append((n.lon, n.lat))
        if "tourism" in tags:
            self.tourism_pois.append((n.lon, n.lat))
        if tags.get("amenity") == "ferry_terminal":
            self.tourism_pois.append((n.lon, n.lat))
        if tags.get("aeroway") == "aerodrome":
            self.tourism_pois.append((n.lon, n.lat))

    def way(self, w: osmium.osm.Way) -> None:
        tags = {k: v for k, v in w.tags}
        highway = tags.get("highway", "")
        if highway in ROAD_TYPES:
            nodes = [(n.lon, n.lat) for n in w.nodes]
            for i in range(len(nodes) - 1):
                self.road_segments.append(
                    (nodes[i][0], nodes[i][1], nodes[i + 1][0], nodes[i + 1][1])
                )


def main() -> None:
    print("=== 30_exposure ===")

    pbf_path = DATA_RAW / "osm" / "alaska-latest.osm.pbf"
    if not pbf_path.exists():
        print(f"  ✗ {pbf_path} not found")
        return

    # Parse OSM
    print(f"  Parsing {pbf_path.name} (this takes ~1 min) ...")
    handler = OSMFeatureHandler()
    handler.apply_file(str(pbf_path), locations=True)

    n_buildings = len(handler.buildings)
    n_roads = len(handler.road_segments)
    n_tourism = len(handler.tourism_pois)
    print(f"  Buildings: {n_buildings:,}")
    print(f"  Road segments: {n_roads:,}")
    print(f"  Tourism POIs: {n_tourism:,}")

    if n_buildings + n_roads + n_tourism == 0:
        print("  ✗ No OSM features found")
        return

    # Project to EPSG:3338
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)

    # Build grid
    xmin, ymin, xmax, ymax = SE_BOUNDS_3338
    cols = int((xmax - xmin) / CELL_SIZE)
    rows = int((ymax - ymin) / CELL_SIZE)
    transform = from_bounds(xmin, ymin, xmax, ymax, cols, rows)

    buildings_grid = np.zeros((rows, cols), dtype=np.float32)
    roads_grid = np.zeros((rows, cols), dtype=np.float32)
    tourism_grid = np.zeros((rows, cols), dtype=np.float32)

    def lonlat_to_cell(lon: float, lat: float) -> tuple[int, int]:
        x, y = transformer.transform(lon, lat)
        col = int((x - xmin) / CELL_SIZE)
        row = int((ymax - y) / CELL_SIZE)
        return row, col

    # Bin buildings
    for lon, lat in handler.buildings:
        r, c = lonlat_to_cell(lon, lat)
        if 0 <= r < rows and 0 <= c < cols:
            buildings_grid[r, c] += 1

    # Bin roads (length per cell)
    for lon1, lat1, lon2, lat2 in handler.road_segments:
        x1, y1 = transformer.transform(lon1, lat1)
        x2, y2 = transformer.transform(lon2, lat2)
        seg_len_m = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        seg_len_km = seg_len_m / 1000.0
        r, c = lonlat_to_cell(lon1, lat1)
        if 0 <= r < rows and 0 <= c < cols:
            roads_grid[r, c] += seg_len_km

    # Bin tourism
    for lon, lat in handler.tourism_pois:
        r, c = lonlat_to_cell(lon, lat)
        if 0 <= r < rows and 0 <= c < cols:
            tourism_grid[r, c] = 1

    # Compute exposure value per cell
    exposure = (
        np.log1p(buildings_grid)
        + 2 * np.log1p(roads_grid)
        + 5 * tourism_grid
    )

    # Radius-smooth with uniform filter
    # size=41 at 500m ≈ 20.5 km radius
    kernel_size = 41
    exposure_smooth = uniform_filter(exposure, size=kernel_size)

    # Write output
    INTERMEDIATE.mkdir(parents=True, exist_ok=True)
    out_path = INTERMEDIATE / "exposure_3338.tif"

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
        nodata=0,
    ) as dst:
        dst.write(exposure_smooth, 1)

    print(f"  ✓ exposure_3338: {cols}×{rows} cells → {out_path.name}")
    print(f"    Max exposure: {exposure_smooth.max():.2f}")
    print(f"    Cells with exposure > 0: {(exposure_smooth > 0).sum():,}")
    print("\n=== Done ===")


if __name__ == "__main__":
    main()
