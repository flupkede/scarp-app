# Phase 0 — Fixup: update deps + Python 3.12 pin

**Status:** 🟠 Important
**Priority:** Phase 0 fixup
**Owner:** OpenCode (`@ZAI Coder`)
**Working directory:** `C:\WorkArea\AI\scarp\`

---

## 1. Context

Phase 0 scaffold was already executed. The backend and frontend directories exist.
This fixup updates `pyproject.toml` to latest verified versions and pins the backend venv to Python 3.12,
because geo wheels (geopandas, rasterio) are not yet available on PyPI for Python 3.14.

## 2. Steps

### 2.1 Pin Python 3.12 for the backend venv

```powershell
cd C:\WorkArea\AI\scarp\backend
uv python pin 3.12
```

### 2.2 Update pyproject.toml

`C:\WorkArea\AI\scarp\backend\pyproject.toml` has already been updated by Claude via Filesystem MCP.
Verify it contains `requires-python = ">=3.12,<3.15"` and `fastapi>=0.136`. If it does, skip to 2.3.

### 2.3 Sync with upgraded packages

```powershell
cd C:\WorkArea\AI\scarp\backend
uv sync --upgrade
```

### 2.4 Smoke test

```powershell
uv run python -c "import geopandas, rasterio, fastapi; print(geopandas.__version__, rasterio.__version__, fastapi.__version__)"
```

Expected: three version numbers printed, no import errors.

### 2.5 Remove temp file

```powershell
del C:\WorkArea\AI\scarp\_timetemp.md
```

### 2.6 Commit

```powershell
cd C:\WorkArea\AI\scarp
git add -A
git commit -m "chore(phase-0): update deps to latest, pin Python 3.12"
git push -u origin main
```

## 3. Definition of Done

- [ ] `backend/.python-version` contains `3.12`
- [ ] `uv run python --version` in backend prints `3.12.x`
- [ ] Smoke test prints three version numbers without errors
- [ ] `_timetemp.md` deleted
- [ ] Commit pushed to main

## 4. Not in scope

- Any backend or frontend logic changes
- Frontend changes
- Data downloads

---

*Report back with commit SHA when done.*
