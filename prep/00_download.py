#!/usr/bin/env python3
"""Scarp — Idempotent data downloader.

Downloads all 8 dataset categories to data/raw/ with SHA-256 verification.
Re-runs are fast: existing files with matching checksums are skipped.

Usage:
    cd C:/WorkArea/AI/scarp
    uv run --project prep python prep/00_download.py
"""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = REPO_ROOT / "data" / "raw"
MANIFEST_PATH = DATA_RAW / "MANIFEST.json"

TIMEOUT = 60.0
CHUNK_SIZE = 8192
TILE_MIN_BYTES = 1_000_000  # skip DEM tiles < 1 MB (corrupt stubs)

# ---------------------------------------------------------------------------
# Dataset definitions
# ---------------------------------------------------------------------------
DATASETS: list[dict] = [
    # 2.1 DGGS Landslide Inventory
    {
        "name": "dggs_inventory",
        "url": (
            "https://dggs.alaska.gov/webpubs/data/"
            "dds023_landslide_inventory_db_02_Sep_2025.zip"
        ),
        "output": "dggs/inventory.geojson",
        "transform": "dggs_inventory",
    },
    # 2.2 USGS n10 Susceptibility Raster (PRIMARY)
    {
        "name": "usgs_n10",
        "url": (
            "https://prod-is-usgs-sb-prod-publish.s3.amazonaws.com/"
            "65ccea5bd34ef4b119cb3bac/n10_ak.tif"
        ),
        "output": "usgs_susc/n10_ak.tif",
    },
    # 2.4 OSM Alaska extract
    {
        "name": "osm_alaska",
        "url": (
            "https://download.geofabrik.de/"
            "north-america/us/alaska-latest.osm.pbf"
        ),
        "output": "osm/alaska-latest.osm.pbf",
    },
    # 2.5 AEC stations (FDSN text)
    {
        "name": "aec_stations",
        "url": (
            "https://service.iris.edu/fdsnws/station/1/"
            "query?network=AK&format=text"
        ),
        "output": "stations/aec_stations_raw.txt",
        "transform": "aec_stations",
    },
    # 2.6 USFS Tongass landslide areas
    {
        "name": "usfs_tongass",
        "url": (
            "https://apps.fs.usda.gov/arcx/rest/services/"
            "EDW/EDW_TongassLandslide_01/MapServer/1"
        ),
        "output": "usfs/tongass_slides.geojson",
        "transform": "usfs_tongass",
    },
    # 2.7 USGS news-reported slides CSV
    {
        "name": "usgs_news_csv",
        "url": (
            "https://www.sciencebase.gov/catalog/file/get/"
            "67d45f8ad34e1acf3979d7ab"
            "?name=SEAK_News_Reported_Landslides.csv"
        ),
        "output": "usgs/seak_news_slides.csv",
    },
]

# 2.4 DEM tiles — queried dynamically from TNM API
DEM_BBOXES = [
    (-138, 55, -130, 60),       # Southeast Alaska
    (-150, 60, -148, 61.5),     # Prince William Sound
    (-142, 59, -138, 61.5),     # Yakutat/Glacier Bay
]

TNM_API = "https://tnmaccess.nationalmap.gov/api/v1/products"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {}


def save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")


def download_file(url: str, dest: Path, client: httpx.Client) -> None:
    """Download *url* to *dest* with streaming and retry on 504."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        try:
            with client.stream("GET", url, follow_redirects=True) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("content-length", 0))
                done = 0
                with open(dest, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=CHUNK_SIZE):
                        f.write(chunk)
                        done += len(chunk)
                        if total and done % (10 * 1024 * 1024) < CHUNK_SIZE:
                            print(f"  ...{done / 1e6:.0f}/{total / 1e6:.0f} MB")
            return
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 504 and attempt < 3:
                wait = 2 ** attempt
                print(f"  504, retrying in {wait}s ...")
                import time
                time.sleep(wait)
                continue
            raise


def is_cached(manifest: dict, name: str, path: Path) -> bool:
    if name not in manifest:
        return False
    entry = manifest[name]
    if not path.exists():
        return False
    if entry.get("sha256") and sha256_file(path) == entry["sha256"]:
        print(f"  ✓ {name} (cached)")
        return True
    return False


def record(
    manifest: dict, name: str, url: str, path: Path
) -> None:
    manifest[name] = {
        "url": url,
        "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Transform: DGGS inventory (nested zip → .gdb → GeoJSON)
# ---------------------------------------------------------------------------

def transform_dggs_inventory(raw_path: Path) -> None:
    """The downloaded zip contains another zip inside. Extract to GeoJSON."""
    import geopandas as gpd

    if raw_path.exists():
        print(f"  ✓ dggs inventory already converted ({raw_path.stat().st_size / 1e6:.1f} MB)")
        return

    zip_path = DATA_RAW / "dggs" / "_downloaded.zip"
    if not zip_path.exists():
        print("  ! DGGS zip not found, skipping conversion")
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract outer zip
        outer = Path(tmpdir) / "outer"
        outer.mkdir()
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(outer)
        # Find inner zip
        inner_zips = list(outer.rglob("*.zip"))
        if not inner_zips:
            # Maybe the .gdb is directly inside
            gdb_dirs = list(outer.rglob("*.gdb"))
            if not gdb_dirs:
                print("  ! No .gdb or inner .zip found in DGGS download")
                return
            gdb_path = str(gdb_dirs[0])
        else:
            inner_dir = Path(tmpdir) / "inner"
            inner_dir.mkdir()
            with zipfile.ZipFile(inner_zips[0]) as zf:
                zf.extractall(inner_dir)
            gdb_dirs = list(inner_dir.rglob("*.gdb"))
            if not gdb_dirs:
                # Try .gpkg or .shp
                alt = list(inner_dir.rglob("*.gpkg")) + list(inner_dir.rglob("*.shp"))
                if not alt:
                    print("  ! No geodatabase found in inner DGGS zip")
                    return
                gdb_path = str(alt[0])
            else:
                gdb_path = str(gdb_dirs[0])

        print(f"  Reading {gdb_path} ...")
        gdf = gpd.read_file(gdb_path)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        gdf.to_file(raw_path, driver="GeoJSON")
        n = len(gdf)
        print(f"  ✓ DGGS inventory: {n} features → {raw_path.name}")

    # Clean up zip
    zip_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Transform: AEC stations (FDSN text → GeoJSON)
# ---------------------------------------------------------------------------

def transform_aec_stations(raw_path: Path) -> None:
    """Parse FDSN | -separated text to GeoJSON Points."""
    import json as _json

    src = DATA_RAW / "stations" / "aec_stations_raw.txt"
    dest = DATA_RAW / "stations" / "aec_stations.geojson"
    if dest.exists():
        print(f"  ✓ AEC stations already converted ({dest.stat().st_size / 1e3:.0f} KB)")
        return
    if not src.exists():
        print("  ! AEC raw text not found")
        return

    features = []
    with open(src) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) < 5:
                continue
            net, sta, lat, lon, elev = parts[0], parts[1], parts[2], parts[3], parts[4]
            try:
                lat_f, lon_f = float(lat), float(lon)
            except ValueError:
                continue
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon_f, lat_f],
                },
                "properties": {
                    "network": net,
                    "station_code": sta,
                    "site_name": sta,
                },
            })

    fc = {"type": "FeatureCollection", "features": features}
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(_json.dumps(fc))
    print(f"  ✓ AEC stations: {len(features)} → {dest.name}")


# ---------------------------------------------------------------------------
# Transform: USFS Tongass (paginated ArcGIS query → GeoJSON)
# ---------------------------------------------------------------------------

def transform_usfs_tongass(raw_path: Path, client: httpx.Client) -> None:
    """Paginate ArcGIS MapServer → GeoJSON."""
    import json as _json

    if raw_path.exists():
        print(f"  ✓ USFS Tongass already exists ({raw_path.stat().st_size / 1e6:.1f} MB)")
        return

    base = (
        "https://apps.fs.usda.gov/arcx/rest/services/"
        "EDW/EDW_TongassLandslide_01/MapServer/1/query"
    )
    all_features: list[dict] = []
    offset = 0
    batch = 1000

    while True:
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "geojson",
            "outSR": "4326",
            "resultOffset": str(offset),
            "resultRecordCount": str(batch),
        }
        resp = client.get(base, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        feats = data.get("features", [])
        if not feats:
            break
        all_features.extend(feats)
        print(f"  USFS page offset={offset}: {len(feats)} features")
        if len(feats) < batch:
            break
        offset += batch

    fc = {"type": "FeatureCollection", "features": all_features}
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(_json.dumps(fc))
    print(f"  ✓ USFS Tongass: {len(all_features)} features → {raw_path.name}")


# ---------------------------------------------------------------------------
# DEM tiles via TNM API
# ---------------------------------------------------------------------------

def download_dem_tiles(manifest: dict, client: httpx.Client) -> None:
    """Query TNM API for DEM tiles and download each one."""
    import time

    dem_dir = DATA_RAW / "dem"
    dem_dir.mkdir(parents=True, exist_ok=True)

    # Discover tiles
    tile_urls: dict[str, str] = {}
    for bbox in DEM_BBOXES:
        params = {
            "datasets": "National Elevation Dataset (NED) 1/3 arc-second",
            "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
            "prodFormats": "GeoTIFF",
            "max": 100,
        }
        print(f"  Querying TNM API bbox={bbox} ...")
        resp = None
        for attempt in range(4):
            try:
                resp = client.get(TNM_API, params=params, timeout=TIMEOUT)
                resp.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 504 and attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                raise

        if resp is None:
            print(f"  ✗ TNM API failed for bbox={bbox}")
            continue

        items = resp.json().get("items", [])
        for item in items:
            # Find GeoTIFF download URL
            for dl in item.get("downloadUrls", {}).values():
                if isinstance(dl, str) and dl.endswith(".tif"):
                    fname = dl.split("/")[-1]
                    # Keep only latest version per tile
                    base = fname.rsplit("_", 1)[0]  # strip date suffix
                    if base not in tile_urls:
                        tile_urls[base] = dl
                    else:
                        # Keep the one with later date
                        existing = tile_urls[base].split("/")[-1]
                        if fname > existing:
                            tile_urls[base] = dl
                    break

    print(f"  Found {len(tile_urls)} unique DEM tiles")

    # Download
    for i, (base, url) in enumerate(tile_urls.items()):
        fname = url.split("/")[-1]
        dest = dem_dir / fname
        mkey = f"dem_tile_{fname}"

        if mkey in manifest and dest.exists():
            if sha256_file(dest) == manifest[mkey].get("sha256"):
                print(f"  ✓ [{i+1}/{len(tile_urls)}] {fname} (cached)")
                continue

        size_check = 0
        with client.stream("GET", url, follow_redirects=True) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            if total < TILE_MIN_BYTES:
                print(f"  ✗ [{i+1}] {fname} skipped (<1 MB stub, {total/1e6:.2f} MB)")
                continue
            with open(dest, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=CHUNK_SIZE):
                    f.write(chunk)

        if dest.stat().st_size < TILE_MIN_BYTES:
            dest.unlink()
            print(f"  ✗ [{i+1}] {fname} skipped (file <1 MB)")
            continue

        record(manifest, mkey, url, dest)
        print(f"  ✓ [{i+1}/{len(tile_urls)}] {fname} ({dest.stat().st_size / 1e6:.1f} MB)")
        time.sleep(1)  # rate-limit


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== Scarp data downloader ===")
    print(f"Repo root: {REPO_ROOT}")
    print(f"Data dir:  {DATA_RAW}")
    print()

    manifest = load_manifest()
    client = httpx.Client(timeout=TIMEOUT)

    # --- Download simple datasets ---
    for ds in DATASETS:
        dest = REPO_ROOT / ds["output"]
        print(f"[{ds['name']}]")

        if ds.get("transform") == "usfs_tongass":
            transform_usfs_tongass(dest, client)
            if dest.exists():
                record(manifest, ds["name"], ds["url"], dest)
            continue

        if ds.get("transform") == "dggs_inventory":
            # Download zip first, then transform
            zip_dest = DATA_RAW / "dggs" / "_downloaded.zip"
            if not zip_dest.exists():
                download_file(ds["url"], zip_dest, client)
            transform_dggs_inventory(dest)
            if dest.exists():
                record(manifest, ds["name"], ds["url"], dest)
            continue

        if ds.get("transform") == "aec_stations":
            # Download raw text first
            raw_dest = DATA_RAW / "stations" / "aec_stations_raw.txt"
            if not raw_dest.exists():
                download_file(ds["url"], raw_dest, client)
            transform_aec_stations(dest)
            if dest.exists():
                record(manifest, ds["name"], ds["url"], dest)
            continue

        # Simple download
        if is_cached(manifest, ds["name"], dest):
            continue
        download_file(ds["url"], dest, client)
        record(manifest, ds["name"], ds["url"], dest)
        print(f"  ✓ {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")

    # --- DEM tiles ---
    print("\n[DEM tiles]")
    download_dem_tiles(manifest, client)

    # --- Save manifest ---
    save_manifest(manifest)
    n = len(manifest)
    total_gb = sum(e["size_bytes"] for e in manifest.values()) / 1e9
    print(f"\n=== Done: {n} entries, {total_gb:.1f} GB ===")
    print(f"Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
