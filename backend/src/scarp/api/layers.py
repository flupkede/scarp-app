"""Layer endpoints — slides, stations, influence, confidence, glacier_velocity."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/layers", tags=["layers"])


@router.get("/slides")
async def get_slides(request: Request) -> dict[str, Any]:
    """Return full slides FeatureCollection from data/processed/slides.geojson."""
    return request.app.state.slides


@router.get("/stations")
async def get_stations(request: Request) -> dict[str, Any]:
    """Return stations FeatureCollection from data/processed/stations.geojson."""
    return request.app.state.stations


@router.get("/influence")
async def get_influence(request: Request) -> dict[str, Any]:
    """Return influence polygons from data/processed/candidates_influence.geojson."""
    return request.app.state.influence


@router.get("/confidence", response_model=None)
async def get_confidence(request: Request):
    """Return confidence FeatureCollection from data/processed/confidence.geojson."""
    data = request.app.state.confidence
    if data is None:
        # Graceful fallback — prep script hasn't run yet
        return JSONResponse(
            status_code=404,
            content={"detail": "Confidence layer not yet generated"},
        )
    return data


@router.get("/glacier_velocity", response_model=None)
async def get_glacier_velocity(request: Request):
    """Return ITS_LIVE glacier velocity points from data/processed/glacier_velocity.geojson.

    Each point carries v_mean / v_max / v_trend_m_yr_per_year for map styling.
    """
    data = getattr(request.app.state, "glacier_velocity", None)
    if data is None:
        # Graceful fallback — glacier pipeline hasn't run yet
        return JSONResponse(
            status_code=404,
            content={"detail": "Glacier velocity layer not yet generated"},
        )
    return data


def _optional_layer(request: Request, attr: str, label: str):
    """Serve an optional app.state layer, or 404 JSON when it isn't loaded."""
    data = getattr(request.app.state, attr, None)
    if data is None:
        return JSONResponse(
            status_code=404,
            content={"detail": f"{label} not yet generated"},
        )
    return data


@router.get("/hig_landslides", response_model=None)
async def get_hig_landslides(request: Request):
    """Hig's curated landslide inventory (centroids) — data/processed/hig_landslides.geojson."""
    return _optional_layer(request, "hig_landslides", "Hig landslide inventory")


@router.get("/hig_polygons", response_model=None)
async def get_hig_polygons(request: Request):
    """Hig's mapped slide footprints (body/source/deposit) — data/processed/hig_polygons.geojson."""
    return _optional_layer(request, "hig_polygons", "Hig landslide polygons")


@router.get("/hig_survey_circles", response_model=None)
async def get_hig_survey_circles(request: Request):
    """Hig's survey circles (where he ground-truthed) — hig_survey_circles.geojson."""
    return _optional_layer(request, "hig_survey_circles", "Hig survey circles")


@router.get("/glacier_episodes", response_model=None)
async def get_glacier_episodes(request: Request):
    """ITS_LIVE accelerate/decelerate episodes (the sawtooth) — glacier_episodes.geojson."""
    return _optional_layer(request, "glacier_episodes", "Glacier episodes layer")


@router.get("/glacier_timeseries", response_model=None)
async def get_glacier_timeseries(request: Request):
    """Per-point ITS_LIVE annual velocity series + episodes for charts — glacier_timeseries.json.

    Not a GeoJSON layer: a dict keyed by point_id (see glacier/15_explore.py).
    """
    return _optional_layer(request, "glacier_timeseries", "Glacier timeseries")
