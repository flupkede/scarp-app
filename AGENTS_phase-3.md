# Phase 3 — Backend API (refined v2 — provider-agnostic)

**Status:** 🟢 Ready — replaces AGENTS_phase-3.md
**Spec:** Section 7 of `AGENTS.md`
**Owner:** OpenCode (`@ZAI Coder`)
**Working directory:** `C:\WorkArea\AI\scarp\backend\`

> **Action:** delete `AGENTS_phase-3.md` (has duplicate content from a failed edit) and rename this file to `AGENTS_phase-3.md`.

---

## 1. Goal

FastAPI service that serves the precomputed GeoJSON from `data/processed/` plus a natural-language search endpoint powered by an OpenAI-compatible LLM.

**Key insight: runtime backend does NOT need geopandas or rasterio.** The heavy spatial libs only run in `prep/`. The runtime serves JSON files. Keep dependencies slim — this enables easy Azure deployment.

## 2. Slim runtime dependencies

```toml
[project]
name = "scarp"
version = "0.1.0"
requires-python = ">=3.12,<3.15"
dependencies = [
  "fastapi>=0.136",
  "uvicorn[standard]>=0.34",
  "httpx>=0.27",
  "openai>=1.50",
  "pydantic>=2.11",
  "pydantic-settings>=2.6",
  "shapely>=2.1",
]

[dependency-groups]
dev = [
  "pytest>=8.3",
  "ruff>=0.11",
]
```

Note: **no geopandas, no rasterio, no anthropic SDK.** Provider-agnostic via OpenAI SDK pointed at any OpenAI-compatible endpoint.

## 3. File layout

```
backend/
├── pyproject.toml
├── src/scarp/
│   ├── __init__.py
│   ├── config.py
│   └── api/
│       ├── __init__.py
│       ├── main.py
│       ├── schemas.py
│       ├── zones.py
│       ├── layers.py
│       └── search.py
└── tests/
```

## 4. Endpoints

### 4.1 `GET /health`

```json
{"status":"ok","version":"0.1.0","zones_loaded":74,"llm_provider":"deepinfra","llm_model":"zai-org/GLM-4.7-Flash"}
```

Include `llm_provider` + `llm_model` — the AI judge sees the provider choice immediately.

### 4.2 `GET /api/zones`

Query params: `limit`, `min_score`, `bbox`. Returns FeatureCollection.

### 4.3 `GET /api/zones/{id}`

Single Feature with full component breakdown + `nearby_slides_count`.

### 4.4 `GET /api/zones/{id}/nearby_slides`

Known slides within 20km of zone centroid.

### 4.5 `GET /api/layers/slides`

`data/processed/slides.geojson` — decimated to ~2000 features.

### 4.6 `GET /api/layers/stations`

`data/processed/stations.geojson` directly.

### 4.7 `POST /api/search` — provider-agnostic LLM

Body: `{"query": "high-risk zones near cruise ship routes"}`

**Default: DeepInfra + GLM 4.7 Flash.**
- Base URL: `https://api.deepinfra.com/v1/openai`
- Model: `zai-org/GLM-4.7-Flash` (30B-A3B MoE, open-weight)
- Cost: ~$0.05/M input, ~$0.20/M output — much cheaper than Claude Sonnet
- Tool calling: native via OpenAI Functions

**Implementation:**

```python
from openai import OpenAI
from .config import settings

client = OpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
)

SYSTEM_PROMPT = """You filter landslide priority zones for Alaska.

Each zone has:
- rank (1=highest risk), score, area_ha, n_cells
- components: susceptibility, slope_pct, proximity, exposure, coverage
- centroid lon/lat
- nearby_slides_count

Call the filter_zones tool with appropriate parameters.
Briefly explain (1-2 sentences) what you filtered for.
"""

response = client.chat.completions.create(
    model=settings.llm_model,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query[:500]},
    ],
    tools=[{
        "type": "function",
        "function": {
            "name": "filter_zones",
            "description": "Filter zones based on criteria",
            "parameters": {
                "type": "object",
                "properties": {
                    "min_score": {"type": "number"},
                    "max_rank": {"type": "integer"},
                    "min_exposure": {"type": "number"},
                    "near_lat": {"type": "number"},
                    "near_lon": {"type": "number"},
                    "max_distance_km": {"type": "number"},
                    "top_n": {"type": "integer"},
                },
            },
        },
    }],
    temperature=0.3,
    max_tokens=512,
)
```

**Provider swap (if Anthropic credits at event):**

Two env var changes, no code change:
```
LLM_BASE_URL=https://api.anthropic.com/v1/
LLM_API_KEY=sk-ant-...
LLM_MODEL=claude-haiku-4-5-20251001
```

Test the swap locally before deploying — Anthropic's OpenAI-compatibility may have minor tool-call differences.

**Response:**
```json
{
  "explanation": "I filtered for zones with high exposure to tourism POIs (proxy for cruise ship routes)...",
  "filter_applied": {"min_exposure": 0.5, "top_n": 20},
  "zones": { /* FeatureCollection */ }
}
```

## 5. Configuration (`config.py`)

```python
import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    data_dir: Path = Path("data/processed")

    llm_base_url: str = "https://api.deepinfra.com/v1/openai"
    llm_api_key: str = ""
    llm_model: str = "zai-org/GLM-4.7-Flash"

    cors_allow_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:4173",
    ]
    enable_search: bool = True

    model_config = {"env_file": ".env"}

settings = Settings()

# Pick up key from any common env var
if not settings.llm_api_key:
    settings.llm_api_key = (
        os.getenv("DEEPINFRA_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or ""
    )
```

## 6. Lifespan

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.zones = json.load(open(settings.data_dir / "zones.geojson"))
    app.state.slides = json.load(open(settings.data_dir / "slides.geojson"))
    app.state.stations = json.load(open(settings.data_dir / "stations.geojson"))
    yield
```

74 zones ~5MB — keep in memory.

## 7. Security headers + CORS

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
```

CORS strict allowlist, never `*`.

## 8. Tests

- `test_health.py`: 200 + llm_provider field
- `test_zones.py`: bbox + limit work
- `test_search.py`: mock OpenAI client, verify correct base_url + model + tool

`uv run pytest`

## 9. Definition of Done

- [ ] All endpoints respond
- [ ] `/docs` renders OpenAPI
- [ ] CORS allows frontend
- [ ] `pytest` passes
- [ ] No API key in any committed file
- [ ] `/api/search` works against live DeepInfra

## 10. Time estimate

| Step | Estimate |
|---|---|
| Code generation (opencode) | 25 min |
| Tests | 10 min |
| Verify search against DeepInfra | 15 min |
| **Total** | **~50 min** |

## 11. Risks

| Risk | Mitigation |
|---|---|
| DeepInfra rate limit during demo | Cache last 10 query results in-memory |
| GLM 4.7 Flash tool-call quality unreliable | Switch to GLM-4.7 (non-Flash 358B) — same code |
| OpenAI SDK breaking changes | Pin `openai>=1.50,<2.0` |
| Search returns weird filters | Validate tool output against Pydantic schema |
| Anthropic OpenAI-compat quirks if swapping | Test swap locally before deploy |

## 12. Pitch angle (one line in README)

> "Provider-agnostic LLM via OpenAI SDK. Default to open-weight GLM 4.7 Flash on DeepInfra (much cheaper than Claude Sonnet). Swap providers with one env var. No vendor lock-in."

AI judges notice this kind of detail as a quality signal.

## 13. Deploy notes

Azure App Service Linux Python 3.12:
```bash
az webapp up --runtime "PYTHON:3.12" --sku B1
```

App settings:
```bash
az webapp config appsettings set \
  --settings DEEPINFRA_API_KEY="..." \
             LLM_BASE_URL="https://api.deepinfra.com/v1/openai" \
             LLM_MODEL="zai-org/GLM-4.7-Flash" \
             CORS_ALLOW_ORIGINS="https://scarp-frontend.azurestaticapps.net"
```

Startup: `uvicorn scarp.api.main:app --host 0.0.0.0 --port 8000`
