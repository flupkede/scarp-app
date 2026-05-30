# SCARP — Package C: Backend + Deploy (instance 3)

> Run this in its own opencode instance. You own `backend/` (and, in the FINAL
> deploy step only, root deploy files + `.github/`). Two other instances run in
> parallel on `main` (pipeline, frontend) — they touch different folders.

**Repo:** `C:\WorkArea\AI\scarp` → https://github.com/flupkede/scarp-app (public)
**Branch:** `main`
**Before any `gh` command:** `gh auth switch --user flupkede`
**Test:** `cd backend && uv run pytest`. Serve: `uv run uvicorn scarp.api.main:app --port 8000`.

---

## Parallel rules (read first)

- You own **`backend/`** for tasks C.1–C.2.
- Commit ONLY your folder: `git add backend/`. **Never `git add -A`.**
- **Package D (deploy) is SEQUENTIAL — do it LAST**, after the other two
  instances have pushed. D touches root files (`README.md`, `SECURITY.md`,
  `staticwebapp.config.json`, `.github/`). Coordinate: only start D once A and B
  report done, to avoid root-file races.
- If push is rejected: `git pull --rebase origin main` then push again.
- Commit format: `<type>(backend): <subject>` / `<type>(deploy): <subject>`.

---

## Current state (already built, works)

`uv run pytest` = 12/12 pass. Slim FastAPI service under `backend/src/scarp/`:
- `config.py` — pydantic-settings. `llm_base_url='https://api.deepinfra.com/v1/openai'`,
  `llm_model='zai-org/GLM-4.7-Flash'`, API-key fallback
  DEEPINFRA_API_KEY→OPENAI_API_KEY→ANTHROPIC_API_KEY. `CORS_ORIGINS` parsed from
  comma-sep string (never `*`). `data_dir` resolves to repo `data/processed`.
- `api/main.py` — lifespan loads zones/slides/stations/influence geojson into
  `app.state`; strict CORS allowlist; security-headers middleware; `/health` +
  `/api/health` (dynamic `zones_loaded`).
- `api/zones.py` — GET `/api/zones` (limit/min_score/bbox), `/{id}`,
  `/{id}/nearby_slides` (haversine ≤20km, `coords[0],coords[1]` for 3-elem Points).
- `api/layers.py` — `/slides`, `/stations`, `/influence`, `/confidence`
  (graceful 404 when file absent).
- `api/search.py` — POST `/api/search`, OpenAI SDK → DeepInfra, `FILTER_TOOL`
  function schema, fallback never 500s, FLAT `{type,features,explanation}`.
- `tests/test_api.py` — 12 tests.

**Slim deps (keep slim):** fastapi, uvicorn[standard], shapely, httpx,
openai>=1.50, pydantic, pydantic-settings, python-multipart. Dev: pytest,
pytest-asyncio, ruff. `asyncio_mode='auto'`. NO geopandas/rasterio/anthropic.

---

## C.1 — Fix the one ruff error

`backend/src/scarp/api/search.py:251` is too long (E501):
```python
explanation = explanation or f"Filtered by: {json.dumps(args)}. Showing {len(filtered)} sites."
```
Wrap it across two lines. Then verify:
```
cd backend
uv run ruff check .     # must be: All checks passed!
uv run pytest           # must stay 12/12
```

## C.2 — Optional hardening (non-blocking, only if time)

- Wire `schemas.py` Pydantic models as `response_model` on the zone endpoints.
- De-duplicate the haversine helper (copied in `zones.py` + `search.py`) into a
  shared `scarp/geo.py`.
- Keep `.env` gitignored. Never commit a real API key. Confirm `.env.example`
  has placeholders only.

**Commit C.1 (+C.2):**
```
cd C:/WorkArea/AI/scarp
git add backend/
git commit -m "fix(backend): resolve ruff E501 in search.py"
gh auth switch --user flupkede
git push origin main
```

---

## Package D — Deploy + pitch (SEQUENTIAL, LAST)

Per `AGENTS_phase-5.md` + `INFRA_PLAN.md`. Do this only after A and B have pushed.

**Architecture:** Azure Static Web App (frontend, `adapter-static`) + App Service
B1 Python 3.12 (backend, gunicorn + uvicorn worker). SWA proxies only `/api/*` →
backend routes already carry the `/api/` prefix, so this matches.

### D.1 — `staticwebapp.config.json` (repo root)
Route `/api/*` to the backend App Service; SPA fallback `/*` → `/index.html`;
set security headers. Per INFRA_PLAN.md §SWA.

### D.2 — Backend startup for App Service
Add a startup command / `gunicorn` config: 
`gunicorn scarp.api.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000`.
Add `gunicorn` to backend deps (App-Service-only; keep dev slim if preferred via
an optional group). Document required App Settings: `DEEPINFRA_API_KEY`,
`CORS_ALLOW_ORIGINS` (include the SWA prod URL), `DATA_DIR`.

### D.3 — CI/CD `.github/workflows/azure-deploy.yml`
Two jobs: build+deploy SvelteKit to SWA (`Azure/static-web-apps-deploy`), and
deploy backend to App Service (`azure/webapps-deploy`). Document the secrets
needed (`AZURE_STATIC_WEB_APPS_API_TOKEN`, publish profile). If CI is risky on
the day, provide equivalent `az` CLI commands in a `docs/DEPLOY.md` as fallback.

### D.4 — `SECURITY.md` (repo root)
Per phase-5: no secrets in repo, strict CORS allowlist, security headers, LLM
key via App Settings only, responsible-disclosure contact.

### D.5 — Final `README.md` (repo root, per `docs/README_plan.md`)
Hero (SCARP title + live demo link), 15-sec hook, demo GIF placeholder,
"Why this is new" (Walden 2025 + Patton 2023 quotes), "How it works" (5 inputs,
scoring, **Mermaid architecture diagram**, USGS n10 vs DGGS), "Engineering
journey" (5 pivots: multiplicative→additive, DGGS→USGS n10, clustering→local
maxima, Anchorage→fjord wall, Barry-Arm-correct-behavior), "Beyond Alaska",
tech stack, run-locally, data-sources table, honest limitations, credits.
**No copyrighted media** (§11b) — NatGeo article LINKED only.

**Commit D:**
```
cd C:/WorkArea/AI/scarp
git add staticwebapp.config.json SECURITY.md README.md .github/ docs/ backend/
git commit -m "feat(deploy): Azure SWA + App Service config, security, final README"
gh auth switch --user flupkede
git push origin main
```

When done, report: ruff/pytest result for C.1, and which deploy files were
created for D.
