"""Tests for Scarp API — health, zones, search shape."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Point to test data
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed"


@pytest.fixture()
def client():
    """TestClient with real data loaded."""
    from scarp.api.main import app

    # Pre-load data into app.state as lifespan would
    zones = json.loads((DATA_DIR / "zones.geojson").read_text())
    slides = json.loads((DATA_DIR / "slides.geojson").read_text())
    stations = json.loads((DATA_DIR / "stations.geojson").read_text())

    app.state.zones = zones
    app.state.slides = slides
    app.state.stations = stations
    app.state.slides_features = slides["features"]
    app.state.influence = {"type": "FeatureCollection", "features": []}
    app.state.confidence = None

    # Glacier velocity layer (published by glacier/30_enrich_zones.py)
    glacier_path = DATA_DIR / "glacier_velocity.geojson"
    app.state.glacier_velocity = (
        json.loads(glacier_path.read_text()) if glacier_path.exists() else None
    )

    return TestClient(app)


class TestHealth:
    def test_health_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "llm_provider" in data
        assert "llm_model" in data

    def test_api_health_alias(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["zones_loaded"] == 120


class TestZones:
    def test_zones_returns_feature_collection(self, client):
        r = client.get("/api/zones?limit=10")
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 10

    def test_zones_feature_shape(self, client):
        """Verify feature properties match frontend ZoneFeature interface."""
        r = client.get("/api/zones?limit=1")
        feat = r.json()["features"][0]
        props = feat["properties"]
        assert "id" in props
        assert "rank" in props
        assert "score" in props
        assert "influence_radius_km" in props
        assert "components" in props
        comp = props["components"]
        for key in (
            "susceptibility",
            "fjord_wall",
            "volume_proxy",
            "proximity",
            "exposure",
            "coverage",
            "glacier",
            "coast_dist_km",
        ):
            assert key in comp, f"Missing component: {key}"
        assert feat["geometry"]["type"] == "Point"

    def test_zones_carry_glacier_context(self, client):
        """Each zone should carry a rich glacier-context block (Phase 3/4)."""
        r = client.get("/api/zones/site-001")
        glac = r.json()["properties"].get("glacier")
        assert glac is not None, "zone missing glacier context block"
        for key in (
            "has_velocity_data",
            "nearest_active_ice",
            "dist_to_active_ice_km",
            "glacier_proximity",
            "glacier_dynamics",
            "glacier_signal",
        ):
            assert key in glac, f"Missing glacier field: {key}"

    def test_zones_min_score_filter(self, client):
        r = client.get("/api/zones?min_score=0.9")
        features = r.json()["features"]
        assert all(f["properties"]["score"] >= 0.9 for f in features)

    def test_zone_by_id(self, client):
        r = client.get("/api/zones/site-001")
        assert r.status_code == 200
        assert r.json()["properties"]["id"] == "site-001"

    def test_zone_not_found(self, client):
        r = client.get("/api/zones/nonexistent")
        assert r.status_code == 404

    def test_nearby_slides(self, client):
        r = client.get("/api/zones/site-001/nearby_slides")
        assert r.status_code == 200
        slides = r.json()
        assert isinstance(slides, list)
        if slides:
            s = slides[0]
            assert "id" in s
            assert "name" in s
            assert "source" in s
            assert "distance_km" in s
            assert "geometry" in s


class TestLayers:
    def test_slides(self, client):
        r = client.get("/api/layers/slides")
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 30000

    def test_stations(self, client):
        r = client.get("/api/layers/stations")
        assert r.status_code == 200
        data = r.json()
        assert len(data["features"]) > 0
        props = data["features"][0]["properties"]
        assert "network" in props
        assert "station_code" in props

    def test_confidence_404(self, client):
        r = client.get("/api/layers/confidence")
        assert r.status_code == 404

    def test_glacier_velocity(self, client):
        r = client.get("/api/layers/glacier_velocity")
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0
        props = data["features"][0]["properties"]
        assert "v_mean" in props
        assert "v_trend_m_yr_per_year" in props


class TestSearch:
    def test_search_returns_flat_shape(self, client):
        """Search must return {type, features, explanation} — flat, not nested."""
        r = client.post("/api/search", json={"query": "high risk near tourism"})
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "FeatureCollection"
        assert isinstance(data["features"], list)
        assert isinstance(data["explanation"], str)
        assert len(data["explanation"]) > 0
