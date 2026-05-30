#!/usr/bin/env python3
"""Scarp — Normalize CRS and merge slide inventories.

Reprojects all vector datasets to EPSG:3338 (Alaska Albers) and merges
DGGS inventory + USFS Tongass + USGS news CSV into a unified slide collection.

Usage:
    cd C:/WorkArea/AI/scarp
    uv run --project prep python prep/10_normalize.py
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.validation import make_valid

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROC = REPO_ROOT / "data" / "processed"
INTERMEDIATE = DATA_PROC / "intermediate"

TARGET_CRS = "EPSG:3338"


def reproject(input_path: Path, output_path: Path) -> gpd.GeoDataFrame | None:
    """Read, validate geometries, reproject to EPSG:3338, write."""
    if not input_path.exists():
        print(f"  ✗ {input_path.name} not found, skipping")
        return None
    print(f"  Reading {input_path.name} ...")
    gdf = gpd.read_file(input_path)
    print(f"    {len(gdf)} features, CRS={gdf.crs}")

    # Validate geometries
    valid_geoms = gdf["geometry"].apply(lambda g: make_valid(g) if g else g)
    gdf = gdf.set_geometry(valid_geoms)
    gdf = gdf[~gdf.is_empty & gdf.notna()].copy()

    # Reproject
    if gdf.crs and str(gdf.crs) != TARGET_CRS:
        gdf = gdf.to_crs(TARGET_CRS)
        print(f"    Reprojected to {TARGET_CRS}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver="GeoJSON")
    print(f"    → {output_path.name} ({len(gdf)} features)")
    return gdf


def main() -> None:
    print("=== 10_normalize ===")
    INTERMEDIATE.mkdir(parents=True, exist_ok=True)

    # --- DGGS inventory ---
    dggs = reproject(
        DATA_RAW / "dggs" / "inventory.geojson",
        INTERMEDIATE / "inventory_3338.geojson",
    )

    # --- USFS Tongass ---
    tongass = reproject(
        DATA_RAW / "usfs" / "tongass_slides.geojson",
        INTERMEDIATE / "tongass_3338.geojson",
    )

    # --- Stations ---
    reproject(
        DATA_RAW / "stations" / "aec_stations.geojson",
        INTERMEDIATE / "stations_3338.geojson",
    )

    # --- USGS news CSV → points → EPSG:3338 ---
    csv_path = DATA_RAW / "usgs" / "seak_news_slides.csv"
    slides_list: list[gpd.GeoDataFrame] = []

    if csv_path.exists():
        print(f"  Reading {csv_path.name} ...")
        df = pd.read_csv(csv_path)
        print(f"    {len(df)} rows")

        # Find lat/lon columns (case-insensitive)
        lat_col = next(
            (c for c in df.columns if c.lower() in ("latitude", "lat", "y")),
            None,
        )
        lon_col = next(
            (c for c in df.columns if c.lower() in ("longitude", "lon", "long", "x")),
            None,
        )
        if lat_col and lon_col:
            news_gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
                crs="EPSG:4326",
            )
            news_gdf = news_gdf.to_crs(TARGET_CRS)
            news_gdf["source"] = "usgs_news"
            slides_list.append(news_gdf)
            print(f"    → {len(news_gdf)} points reprojected")
        else:
            print(f"    ✗ Could not find lat/lon columns: {list(df.columns)}")
    else:
        print(f"  ✗ {csv_path.name} not found")

    # --- Merge all slides ---
    if dggs is not None:
        dggs["source"] = "dggs"
        slides_list.append(dggs)

    if tongass is not None:
        tongass["source"] = "tongass"
        slides_list.append(tongass)

    if not slides_list:
        print("  ✗ No slide data found at all")
        return

    all_slides = pd.concat(slides_list, ignore_index=True)
    all_slides["geometry"] = all_slides["geometry"].apply(
        lambda g: make_valid(g) if g else g
    )
    all_slides = all_slides[~all_slides.is_empty & all_slides.notna()]
    all_slides = all_slides.to_crs(TARGET_CRS)

    out_path = INTERMEDIATE / "all_slides_3338.geojson"
    all_slides.to_file(out_path, driver="GeoJSON")
    print(f"\n  ✓ all_slides_3338: {len(all_slides)} features → {out_path.name}")

    # Also export to EPSG:4326 for the backend (slides.geojson)
    slides_4326 = all_slides.to_crs("EPSG:4326")
    slides_out = DATA_PROC / "slides.geojson"
    slides_4326.to_file(slides_out, driver="GeoJSON")
    print(f"  ✓ slides.geojson (4326): {len(slides_4326)} features")

    # Stations → EPSG:4326 for backend
    stations_3338 = INTERMEDIATE / "stations_3338.geojson"
    if stations_3338.exists():
        st = gpd.read_file(stations_3338)
        st_4326 = st.to_crs("EPSG:4326")
        st_out = DATA_PROC / "stations.geojson"
        st_4326.to_file(st_out, driver="GeoJSON")
        print(f"  ✓ stations.geojson (4326): {len(st_4326)} features")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
