"""Pydantic schemas for Scarp API — matches frontend src/lib/api.ts exactly."""

from __future__ import annotations

from pydantic import BaseModel

# --- Components (nested inside Zone properties) ---

class ZoneComponents(BaseModel):
    susceptibility: float
    fjord_wall: float
    volume_proxy: float
    proximity: float
    exposure: float
    coverage: float
    coast_dist_km: float


class ZoneProperties(BaseModel):
    id: str
    rank: int
    score: float
    influence_radius_km: int
    components: ZoneComponents


# --- Nearby slides ---

class NearbySlide(BaseModel):
    id: int
    name: str
    source: str
    distance_km: float
    geometry: dict  # GeoJSON Point


# --- Search ---

class SearchRequest(BaseModel):
    query: str


class SearchResponse(BaseModel):
    type: str = "FeatureCollection"
    features: list[dict]
    explanation: str
