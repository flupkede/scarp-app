"""Search endpoint — POST /api/search with LLM-powered filtering.

Provider routing (via LLM_BASE_URL env var):
- "anthropic" in URL → use anthropic SDK directly (native tool_use format)
- anything else      → use openai SDK with base_url (OpenAI-compat, e.g. DeepInfra)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Request

from ..config import settings
from ..geo import haversine_km
from .ratelimit import limiter
from .schemas import SearchRequest, SearchResponse

logger = logging.getLogger("scarp.search")

router = APIRouter(prefix="/api", tags=["search"])

SYSTEM_PROMPT = """You filter landslide monitoring priority zones for Southeast Alaska.

Each zone is a candidate sensor placement site with these properties:
- id (string like "site-001")
- rank (1 = highest risk, 120 = lowest)
- score (0.0 to 1.0)
- influence_radius_km (always 3)
- components:
    - susceptibility (0-1): USGS DEM-derived slope stability
    - fjord_wall (0-1): steep terrain adjacent to deep water
    - slope_factor (0-1): steep slope presence
    - proximity (0-1): inverse distance to nearest known landslide
    - exposure (0-1): buildings, roads, tourism, marine traffic
    - coverage (0-1): existing monitoring coverage (0 = unmonitored)
    - coast_dist_km: distance to coastline

The centroid lon/lat is in the geometry.coordinates field.

Call the filter_zones tool with appropriate parameters.
Briefly explain (1-2 sentences) what you filtered for.
"""

FILTER_TOOL = {
    "type": "function",
    "function": {
        "name": "filter_zones",
        "description": "Filter and rank landslide monitoring zones based on user criteria",
        "parameters": {
            "type": "object",
            "properties": {
                "min_score": {
                    "type": "number",
                    "description": "Minimum overall score threshold (0-1)",
                },
                "max_rank": {
                    "type": "integer",
                    "description": "Maximum rank to include (e.g. 20 for top 20)",
                },
                "min_exposure": {
                    "type": "number",
                    "description": "Minimum exposure component score (0-1)",
                },
                "min_susceptibility": {
                    "type": "number",
                    "description": "Minimum susceptibility component score (0-1)",
                },
                "near_lat": {
                    "type": "number",
                    "description": "Latitude to search near",
                },
                "near_lon": {
                    "type": "number",
                    "description": "Longitude to search near",
                },
                "max_distance_km": {
                    "type": "number",
                    "description": "Max distance from near_lat/near_lon in km",
                },
                "top_n": {
                    "type": "integer",
                    "description": "Return only top N results after filtering",
                },
            },
        },
    },
}


def _apply_filters(
    features: list[dict],
    filters: dict[str, Any],
    top_n_default: int = 20,
) -> list[dict]:
    """Apply LLM-returned filter parameters to zone features."""
    result = list(features)

    if "min_score" in filters and filters["min_score"] is not None:
        result = [f for f in result if f["properties"]["score"] >= filters["min_score"]]

    if "max_rank" in filters and filters["max_rank"] is not None:
        result = [f for f in result if f["properties"]["rank"] <= filters["max_rank"]]

    if "min_exposure" in filters and filters["min_exposure"] is not None:
        result = [
            f
            for f in result
            if f["properties"]["components"]["exposure"] >= filters["min_exposure"]
        ]

    if "min_susceptibility" in filters and filters["min_susceptibility"] is not None:
        result = [
            f
            for f in result
            if f["properties"]["components"]["susceptibility"] >= filters["min_susceptibility"]
        ]

    # Geospatial proximity filter
    if all(k in filters and filters[k] is not None for k in ("near_lat", "near_lon")):
        lat = filters["near_lat"]
        lon = filters["near_lon"]
        max_dist = filters.get("max_distance_km", 50)

        def _dist(f: dict) -> float:
            flon, flat = f["geometry"]["coordinates"]
            return haversine_km(lon, lat, flon, flat)

        result = [f for f in result if _dist(f) <= max_dist]
        result.sort(key=_dist)

    # Sort by rank
    result.sort(key=lambda f: f["properties"]["rank"])

    # Limit
    top_n = filters.get("top_n", top_n_default)
    if top_n:
        result = result[:top_n]

    return result


def _fallback_search(
    features: list[dict], query: str, reason: str
) -> dict[str, Any]:
    """Graceful fallback: return top N by rank with explanation."""
    top = sorted(features, key=lambda f: f["properties"]["rank"])[:15]
    return {
        "type": "FeatureCollection",
        "features": top,
        "explanation": (
            f"LLM search unavailable ({reason}). Showing top 15 sites by rank. "
            f"Original query: '{query}'"
        ),
    }


def _call_openai_compat(query: str) -> tuple[dict, str]:
    """Call any OpenAI-compatible provider (DeepInfra, OpenRouter, etc.)."""
    from openai import OpenAI

    client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query[:500]},
        ],
        tools=[FILTER_TOOL],  # type: ignore[arg-type]
        temperature=0.3,
        max_tokens=512,
    )
    choice = response.choices[0]
    message = choice.message

    if not message.tool_calls:
        return {}, message.content or "No specific filter applied."

    args = json.loads(message.tool_calls[0].function.arguments)  # type: ignore[union-attr]
    return args, message.content or ""


def _call_anthropic(query: str) -> tuple[dict, str]:
    """Call Anthropic directly using the anthropic SDK (native tool_use format)."""
    import anthropic

    client = anthropic.Anthropic(api_key=settings.llm_api_key)

    # Anthropic tool format — same semantics, different schema key names
    tool = {
        "name": FILTER_TOOL["function"]["name"],
        "description": FILTER_TOOL["function"]["description"],
        "input_schema": FILTER_TOOL["function"]["parameters"],
    }

    response = client.messages.create(
        model=settings.llm_model,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": query[:500]}],
        tools=[tool],  # type: ignore[arg-type]
        temperature=0.3,
        max_tokens=512,
    )

    args: dict = {}
    explanation = ""
    for block in response.content:
        if block.type == "tool_use":
            args = block.input  # type: ignore[attr-defined]
        elif block.type == "text":
            explanation = block.text  # type: ignore[attr-defined]

    return args, explanation


@router.post("/search", response_model=SearchResponse)
@limiter.limit("10/minute")
async def search_zones(request: Request, body: SearchRequest) -> dict[str, Any]:
    """
    Natural-language search for zones.
    Returns FLAT FeatureCollection + explanation (matches frontend SearchResponse).
    """
    zones_data: dict = request.app.state.zones
    features: list[dict] = zones_data["features"]

    if not settings.enable_search:
        return _fallback_search(features, body.query, "search disabled")

    if not settings.llm_api_key:
        return _fallback_search(features, body.query, "no API key configured")

    try:
        use_anthropic = "anthropic" in settings.llm_base_url.lower()

        if use_anthropic:
            args, explanation = _call_anthropic(body.query)
        else:
            args, explanation = _call_openai_compat(body.query)

        filtered = _apply_filters(features, args)
        explanation = explanation or (
            f"Filtered by: {json.dumps(args)}. Showing {len(filtered)} sites."
        )

        return {
            "type": "FeatureCollection",
            "features": filtered,
            "explanation": explanation,
        }

    except Exception as e:
        logger.warning("LLM search failed: %s", e)
        return _fallback_search(features, body.query, str(e)[:100])
