"""Shared geospatial utilities."""

from __future__ import annotations

import math


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Haversine distance in km between two lon/lat points."""
    earth_radius_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return earth_radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
