"""Layer endpoints — /api/layers/slides, /api/layers/stations, /api/layers/influence."""

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
