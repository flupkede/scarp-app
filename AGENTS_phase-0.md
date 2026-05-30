# Phase 0 — Foundation

**Status:** 🟠 Important
**Priority:** Phase 0
**Spec:** Section 4 of `AGENTS.md`
**Owner:** OpenCode (`@ZAI Coder` for scaffolding, `@Reviewer` before commit)
**Branch:** `features/phase-0-foundation`
**Working directory:** `C:\WorkArea\AI\scarp\`

---

## 1. Goal

Bring an empty workstation to the state where both backend (FastAPI) and frontend (SvelteKit + Skeleton v4 + MapLibre) boot successfully on localhost, with the repo published publicly on GitHub.

No business logic. No data. No styling beyond defaults. Just scaffolding that compiles and runs.

## 2. Pre-flight checks

Before executing, verify on the host machine:

| Tool | Required version | Verify command |
|---|---|---|
| Git | any recent | `git --version` |
| Python | 3.12.x or 3.14.x (system) | `python --version` |
| `uv` | latest | `uv --version` |
| Node | 20.x or 22.x | `node --version` |
| pnpm | 9.x or later | `pnpm --version` |
| GitHub CLI | latest | `gh --version` |

System Python version does not matter — uv pins the backend venv to 3.12. Do not substitute `npm` for `pnpm`.

## 3. Concrete steps

Execute in this order. Each step is independent; one failure should not skip later steps without explicit decision.

### 3.1 Create the GitHub repository

Note: `gh` does not allow `--license` together with `--source`. The LICENSE file is already present locally and will be committed.

```powershell
cd C:\WorkArea\AI\scarp
git init -b main
gh repo create flupkede/scarp --public --source=. --description "Prioritization tool for landslide monitoring placement in Alaska."
```

### 3.2 (Skipped — repo created in place via --source=. above)

### 3.3 Add `.gitignore`

Create `.gitignore` at repo root with these entries:

```
# Python
__pycache__/
*.py[cod]
.venv/
.pytest_cache/
.ruff_cache/
.mypy_cache/
*.egg-info/
dist/
build/

# Node / SvelteKit
node_modules/
.svelte-kit/
.vite/

# Data — raw downloads stay local
data/raw/
*.tif
*.tiff
*.shp
*.shx
*.dbf
*.prj
*.cpg
*.pbf
*.gpkg

# Allow processed outputs (small enough to commit)
!data/processed/

# Local config
.env
.env.local
*.local

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
```

### 3.4 README

The README.md already exists at `C:\WorkArea\AI\scarp\README.md` — do not overwrite it.

### 3.5 Backend scaffolding

```powershell
cd C:\WorkArea\AI\scarp
mkdir backend
cd backend
uv init --package scarp --python 3.12
uv python pin 3.12
```

Edit `backend/pyproject.toml`. Replace the auto-generated `[project]` section with:

```toml
[project]
name = "scarp"
version = "0.1.0"
description = "Backend API for Scarp"
requires-python = ">=3.12,<3.15"
dependencies = [
  "fastapi>=0.136",
  "uvicorn[standard]>=0.34",
  "geopandas>=1.1",
  "rasterio>=1.5",
  "shapely>=2.1",
  "pyproj>=3.7",
  "httpx>=0.27",
  "anthropic>=0.85",
  "pydantic>=2.11",
  "pydantic-settings>=2.6",
  "python-multipart>=0.0.12",
  "typer>=0.13",
]

[dependency-groups]
dev = [
  "pytest>=8.3",
  "ruff>=0.11",
  "mypy>=1.13",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM", "RUF"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/scarp"]
```

Install:

```powershell
uv sync
```

Smoke test — must print a version number:

```powershell
uv run python -c "import geopandas; print(geopandas.__version__)"
```

Create `backend/src/scarp/api/__init__.py` (empty) and `backend/src/scarp/api/main.py`:

```python
"""FastAPI entrypoint for Scarp."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Scarp API",
    version="0.1.0",
    description="Prioritization data for landslide monitoring placement in Alaska.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
```

### 3.6 Frontend scaffolding

```powershell
cd C:\WorkArea\AI\scarp
pnpm create svelte@latest frontend
```

Interactive choices: Skeleton project, TypeScript syntax, add ESLint, add Prettier, no Playwright, no Vitest.

```powershell
cd frontend
pnpm install
pnpm add maplibre-gl
pnpm add -D @types/geojson
```

Apply Skeleton v4 + Tailwind setup per Filip's `svar-skeleton` skill.

Edit `frontend/src/routes/+page.svelte` to a minimal placeholder:

```svelte
<script lang="ts">
  let mounted = $state(false);
  $effect(() => {
    mounted = true;
  });
</script>

<div class="p-8">
  <h1 class="h1">Scarp</h1>
  <p class="text-surface-500-400-token mt-4">
    Scaffolding ready. Map coming in Phase 4.
  </p>
  {#if mounted}
    <p class="text-success-500 mt-2 text-sm">✓ Svelte 5 runes working</p>
  {/if}
</div>
```

### 3.7 Placeholder directories and files

```powershell
cd C:\WorkArea\AI\scarp
mkdir prep
mkdir data
mkdir data\raw
mkdir data\processed
mkdir docs
mkdir docs\screenshots
```

Create `prep/README.md`:
```
Pipeline scripts. Run order: 00_download.py → 10_normalize.py → ... → 50_score_zones.py. See AGENTS.md Phase 1-2.
```

Create `docs/pitch.md` and `docs/slides.md` with just `# TODO` as content.

### 3.8 First commit

```powershell
git add .
git status
```

Verify: no `node_modules/`, `.venv/`, `*.tif`, or `data/raw/` in the staged list.

```powershell
git commit -m "chore(phase-0): scaffold backend + frontend"
git push -u origin main
```

## 4. Verification

Run in two separate terminals.

**Terminal 1 — backend:**

```powershell
cd C:\WorkArea\AI\scarp\backend
uv run uvicorn scarp.api.main:app --reload
```

Expected: `http://127.0.0.1:8000/health` returns `{"status":"ok","version":"0.1.0"}` and `/docs` renders OpenAPI UI.

**Terminal 2 — frontend:**

```powershell
cd C:\WorkArea\AI\scarp\frontend
pnpm dev
```

Expected: `http://localhost:5173` shows placeholder with green "✓ Svelte 5 runes working".

## 5. Definition of Done

- [ ] Repository at `github.com/flupkede/scarp`, public, MIT license committed
- [ ] `.gitignore` complete; `git status` clean after fresh boot
- [ ] `uv sync` in `backend/` succeeds with Python 3.12 venv
- [ ] `uv run python -c "import geopandas"` prints version without error
- [ ] `/health` returns 200
- [ ] `pnpm dev` shows placeholder with runes confirmation
- [ ] Initial commit pushed to `main`
- [ ] `AGENTS.md` and `AGENTS_phase-0.md` in repo

## 6. Not in scope

- Map rendering (Phase 4)
- Data downloads (Phase 1)
- Spatial logic (Phase 2)
- API endpoints beyond `/health` (Phase 3)
- Skeleton theming beyond CLI defaults
- Tests beyond booting the servers

## 7. Time estimate

| Step | Estimate |
|---|---|
| 3.1 – 3.4 (repo + git) | 15 min |
| 3.5 (backend + uv sync) | 30 min |
| 3.6 (frontend) | 25 min |
| 3.7 – 3.8 (dirs + commit) | 10 min |
| Verification + debugging | 20 min |
| **Total** | **~1.5h** |

## 8. Known risks

- **uv sync slow on first run:** geopandas + rasterio pull large C extension wheels. Allow up to 5 min, fast thereafter.
- **Python 3.12 not installed:** uv will download it automatically if missing. Requires internet access.
- **Skeleton v4 CLI questions:** default to TypeScript syntax, ESLint yes, Prettier yes, no test framework.
- **GitHub CLI auth:** run `gh auth login` if `gh repo create` fails.
- **Windows long paths:** run `git config --global core.longpaths true` if path-length errors appear.

## 9. Commit message

```
chore(phase-0): scaffold backend + frontend

- Python 3.12 venv via uv pin (geo wheels, 3.14 not yet supported)
- FastAPI 0.136 + uvicorn + geopandas 1.1 + rasterio 1.5
- SvelteKit + Skeleton v4 + Tailwind, MapLibre installed
- Placeholder directories for prep/, data/, docs/

Refs: AGENTS_phase-0.md
```

---

*When DoD checkboxes are all ticked, report back with the commit SHA and wait for go-ahead on Phase 1.*
