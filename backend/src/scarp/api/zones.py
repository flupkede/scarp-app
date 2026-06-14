"""Zone endpoints — /api/zones, /api/zones/{id}, /api/zones/{id}/nearby_slides."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from ..config import CALIBRATION_STATUS
from ..geo import haversine_km
from .schemas import NearbySlide

router = APIRouter(prefix="/api/zones", tags=["zones"])


def _zones_data(request: Request) -> dict:
    """Get zones FeatureCollection from app state."""
    return request.app.state.zones


def _slides_data(request: Request) -> list[dict]:
    """Get slides features list from app state."""
    return request.app.state.slides_features



@router.get("")
async def get_zones(
    request: Request,
    limit: int = 120,
    min_score: float | None = None,
    bbox: str | None = None,
) -> dict[str, Any]:
    """
    Return FeatureCollection of candidate site POINTS.
    Matches frontend ZoneCollection type.
    """
    data = _zones_data(request)
    features = list(data["features"])

    # Filter by min_score
    if min_score is not None:
        features = [f for f in features if f["properties"]["score"] >= min_score]

    # Filter by bbox (xmin,ymin,xmax,ymax)
    if bbox:
        parts = [float(x) for x in bbox.split(",")]
        if len(parts) == 4:
            xmin, ymin, xmax, ymax = parts
            features = [
                f
                for f in features
                if xmin <= f["geometry"]["coordinates"][0] <= xmax
                and ymin <= f["geometry"]["coordinates"][1] <= ymax
            ]

    # Sort by rank, then limit
    features.sort(key=lambda f: f["properties"]["rank"])
    features = features[:limit]

    # `calibration` flags that score/rank are an uncalibrated heuristic, not a
    # probability (see ROADMAP.md). Extra top-level key is ignored by the
    # structural ZoneCollection type on the frontend.
    return {
        "type": "FeatureCollection",
        "features": features,
        "calibration": CALIBRATION_STATUS,
    }


@router.get("/{zone_id}")
async def get_zone_by_id(request: Request, zone_id: str) -> dict[str, Any]:
    """Return a single zone Feature by ID."""
    data = _zones_data(request)
    for feature in data["features"]:
        if feature["properties"]["id"] == zone_id:
            return feature
    raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")


@router.get("/{zone_id}/nearby_slides", response_model=list[NearbySlide])
async def get_nearby_slides(request: Request, zone_id: str) -> list[dict]:
    """
    Return known slides within 20km of the zone centroid.
    Matches frontend NearbySlide[] type: {id, name, source, distance_km, geometry}.
    """
    data = _zones_data(request)
    slides = _slides_data(request)

    # Find zone centroid
    zone_feature = None
    for f in data["features"]:
        if f["properties"]["id"] == zone_id:
            zone_feature = f
            break

    if zone_feature is None:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")

    lon, lat = zone_feature["geometry"]["coordinates"]
    max_dist_km = 20.0

    nearby: list[dict] = []
    for slide in slides:
        coords = slide["geometry"]["coordinates"]
        s_lon, s_lat = coords[0], coords[1]
        dist = haversine_km(lon, lat, s_lon, s_lat)
        if dist <= max_dist_km:
            nearby.append({
                "id": slide["properties"]["id"],
                "name": slide["properties"]["name"],
                "source": slide["properties"]["source"],
                "distance_km": round(dist, 1),
                "geometry": slide["geometry"],
            })

    # Sort by distance
    nearby.sort(key=lambda s: s["distance_km"])
    return nearby
