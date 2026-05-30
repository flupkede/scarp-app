"""FastAPI entrypoint for Scarp — all endpoints, lifespan, security headers."""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from ..config import CORS_ORIGINS, llm_provider_label, settings
from .layers import router as layers_router
from .ratelimit import limiter
from .search import router as search_router
from .zones import router as zones_router

logger = logging.getLogger("scarp")


# ---------------------------------------------------------------------------
# Lifespan — load data files into memory on startup
# ---------------------------------------------------------------------------


def _resolve_data_dir() -> Path:
    """Resolve data directory, falling back to a relative path if needed."""
    p = settings.data_dir
    if p.is_dir():
        return p
    # Try relative to backend/
    backend_dir = Path(__file__).resolve().parent.parent.parent.parent
    fallback = backend_dir.parent / "data" / "processed"
    if fallback.is_dir():
        return fallback
    raise FileNotFoundError(f"Data directory not found: tried {p} and {fallback}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    data_dir = _resolve_data_dir()
    logger.info("Loading data from %s", data_dir)

    app.state.zones = json.loads((data_dir / "zones.geojson").read_text())
    app.state.slides = json.loads((data_dir / "slides.geojson").read_text())
    app.state.stations = json.loads((data_dir / "stations.geojson").read_text())

    # Pre-extract slides features for nearby-slides queries
    app.state.slides_features = app.state.slides["features"]

    # Load influence polygons if available
    influence_path = data_dir / "candidates_influence.geojson"
    if influence_path.exists():
        app.state.influence = json.loads(influence_path.read_text())
    else:
        app.state.influence = {"type": "FeatureCollection", "features": []}

    # Load confidence layer if available (graceful fallback — prep may not have run yet)
    confidence_path = data_dir / "confidence.geojson"
    if confidence_path.exists():
        app.state.confidence = json.loads(confidence_path.read_text())
        logger.info("Loaded confidence layer (%d features)", len(app.state.confidence["features"]))
    else:
        app.state.confidence = None
        logger.info("Confidence layer not found — serving empty")

    zones_count = len(app.state.zones["features"])
    slides_count = len(app.state.slides_features)
    stations_count = len(app.state.stations["features"])
    logger.info(
        "Loaded %d zones, %d slides, %d stations",
        zones_count,
        slides_count,
        stations_count,
    )

    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Scarp API",
    version="0.1.0",
    description="Prioritization data for landslide monitoring placement in Alaska.",
    lifespan=lifespan,
)

# Rate-limiting — attach limiter to app.state so SlowAPI can find it
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}. Try again in a minute."},
    )


# CORS — strict allowlist, never "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(zones_router)
app.include_router(layers_router)
app.include_router(search_router)


# ---------------------------------------------------------------------------
# Health endpoints (both /health and /api/health)
# ---------------------------------------------------------------------------


@app.get("/health")
@app.get("/api/health")
async def health(request: Request) -> dict[str, Any]:
    """Health check with zone count and LLM config."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "zones_loaded": len(request.app.state.zones["features"]),
        "llm_provider": llm_provider_label(),
        "llm_model": settings.llm_model,
    }
