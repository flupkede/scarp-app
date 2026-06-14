"""Scarp Glacier — Constants and configuration.

No hardcoded strings in business logic — everything lives here.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
GLACIER_DIR = REPO_ROOT / "glacier"
DATA_DIR = GLACIER_DIR / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"

# Scarp processed data (from prep/)
SCARP_DATA = REPO_ROOT / "data" / "processed"

# ---------------------------------------------------------------------------
# ITS_LIVE data source
# ---------------------------------------------------------------------------
ITS_LIVE_S3_BUCKET = "its-live-data"
ITS_LIVE_S3_REGION = "us-west-2"
ITS_LIVE_DATACUBE_PREFIX = "datacubes/"
ITS_LIVE_STAC_URL = "https://stac.itslive.cloud"
ITS_LIVE_LICENSE = "CC0-1.0"

# Data cube catalog (GeoJSON FeatureCollection)
ITS_LIVE_CATALOG_URL = (
    "https://its-live-data.s3.amazonaws.com/datacubes/catalog_v02.json"
)

# Cube native CRS (all Alaska cubes use polar stereographic)
CUBE_EPSG = 3413  # NSIDC North Polar Stereographic
CUBE_GRID_RESOLUTION_M = 120

# ---------------------------------------------------------------------------
# Coordinate reference
# ---------------------------------------------------------------------------
TARGET_EPSG = 3338  # Alaska Albers (matches Scarp prep/)

# ---------------------------------------------------------------------------
# SE Alaska coverage — broader sweep for glacier analysis
# ---------------------------------------------------------------------------
SE_ALASKA_BBOX_WGS84 = (-141.0, 55.0, -129.5, 60.5)  # (west, south, east, north)

# Sub-regions matching Scarp DEM tiles (for reference)
SCARP_DEM_BBOXES = [
    (-138.0, 55.0, -130.0, 60.0),
    (-150.0, 60.0, -148.0, 61.5),
    (-142.0, 59.0, -138.0, 61.5),
]

# ---------------------------------------------------------------------------
# Known glacier case-study points (lon, lat in WGS84)
# ---------------------------------------------------------------------------
TRACY_ARM_CENTER = (-133.65, 58.45)
BARRY_ARM_CENTER = (-148.85, 61.15)

# Additional glaciers of interest (Hig's focus area)
GLACIER_POINTS_OF_INTEREST: list[tuple[float, float, str]] = [
    # (lon, lat, label)
    (-133.65, 58.45, "Tracy Arm"),
    (-148.85, 61.15, "Barry Arm"),
    (-136.40, 58.65, "Muir Inlet"),
    (-136.10, 58.50, "Taku Glacier"),
    (-135.50, 59.00, "Lamplugh Glacier"),
    (-137.20, 58.80, "Brady Glacier"),
    (-139.00, 59.50, "Malaspina Glacier"),
    (-150.00, 60.50, "Columbia Glacier"),
    (-148.00, 60.90, "College Fjord"),
    (-134.50, 58.20, "Endicott Arm"),
]

# ---------------------------------------------------------------------------
# Extraction parameters
# ---------------------------------------------------------------------------
GRID_RESOLUTION_M = 120  # ITS_LIVE native resolution
MAX_IMAGE_PAIR_DAYS = 546  # optical pairs ≤ this
MAX_SAR_PAIR_DAYS = 12  # SAR pairs ≤ this
MIN_VELOCITY_OBSERVATIONS = 5  # skip points with fewer time-series points
VELOCITY_OUTLIER_THRESHOLD_M_YR = 10000.0  # cap obvious outliers

# Velocity trend (linear regression of v vs time)
MIN_TREND_OBSERVATIONS = 10  # need enough points for a meaningful slope
MIN_TREND_SPAN_YEARS = 2.0  # need a real time baseline to regress over
SECONDS_PER_YEAR = 365.25 * 86400.0

# ---------------------------------------------------------------------------
# Zone enrichment (Phase 3) — per-Scarp-zone glacier context
# ---------------------------------------------------------------------------
# A summary point counts as "active ice" (a glacier-flow / terminus proxy) when
# its mean velocity exceeds this. Below it, motion is noise or stagnant ice.
ACTIVE_ICE_V_THRESHOLD_M_YR = 25.0
# Distance-decay length for glacier influence on a slope (km). Risk from a
# retreating/buttressing glacier declines with distance from the ice front.
GLACIER_PROXIMITY_DECAY_KM = 8.0
# Trend magnitude (|m/yr per year|) treated as full-scale glacier dynamism for
# normalising the dynamics signal to 0..1.
GLACIER_DYNAMICS_FULLSCALE_TREND = 5.0

# ---------------------------------------------------------------------------
# Output file names
# ---------------------------------------------------------------------------
VELOCITY_TIMESERIES_FILE = "velocity_timeseries.parquet"
GLACIER_CATALOG_FILE = "glacier_catalog.geojson"
VELOCITY_SUMMARY_FILE = "velocity_summary.geojson"
ZONES_ENRICHED_FILE = "zones_glacier_enriched.geojson"
ZONE_GLACIER_PARAMS_FILE = "zone_glacier_params.json"
