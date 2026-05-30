# SCARP — Package B: Frontend (instance 2)

> Run this in its own opencode instance. You own `frontend/`. Two other
> instances run in parallel on `main` (pipeline, backend) — they touch different
> folders, so you never conflict.

**Repo:** `C:\WorkArea\AI\scarp` → https://github.com/flupkede/scarp-app (public)
**Branch:** `main`
**Before any `gh` command:** `gh auth switch --user flupkede`
**Dev:** `cd frontend && pnpm dev` (port 11001). Build: `pnpm build` (adapter-static).

---

## Parallel rules (read first)

- You own **`frontend/`** only.
- Commit ONLY your folder: `git add frontend/`. **Never `git add -A`.**
  Never touch `prep/`, `backend/`, `data/`, or root files.
- If push is rejected: `git pull --rebase origin main` then push again.
- Commit format: `<type>(frontend): <subject>`.

---

## Current state (already built, works)

`pnpm build` is clean (SvelteKit 5 runes + adapter-static + Tailwind 3 +
MapLibre GL 4.7). Existing components under `frontend/src/`:
- `lib/api.ts` — typed client, `API_BASE = import.meta.env.VITE_PUBLIC_API_URL ?? 'http://localhost:8000'`
- `lib/stores/zones.svelte.ts` — runes store + 17-fjord centroid lookup
- `lib/components/`: `Map.svelte`, `Splash.svelte`, `PriorityList.svelte`,
  `ZoneDetail.svelte`, `LayerToggle.svelte`, `SearchBar.svelte`
- `routes/`: `+page.svelte` (map view), `+layout.svelte`, `about/+page.svelte`

**Locked visual decisions (do NOT regress):**
- Esri World Topo basemap. NOT OpenTopoMap (CORS-blocked).
- No `raster-brightness`/`raster-saturation` overrides (they dim tiles).
- Inline MapLibre paint expressions, NO helper functions (breaks TS).
- Fonts: Fraunces (serif headers) + Inter (sans UI). No mason-jar icons.
- Symbols: target (concentric rings + dot) for candidates; blue filled circle
  for stations; rank gradient red#dc2626→orange#ea580c→amber#f59e0b→yellow#fbbf24
  for influence polygons (opacity 0.35). Labels only for top 10. Pulse animation
  for top 10.
- Use `MapGeoJSONFeature` type (not Mapbox).

**Data schema (`data/processed/`, served by backend):**
- zones.geojson = 120 candidate POINTS, props `{id:'site-NNN', rank, score,
  influence_radius_km:3, components:{susceptibility, fjord_wall, slope_factor,
  proximity, exposure, coverage, coast_dist_km}}`
- candidates_influence.geojson = 120 POLYGONS · stations.geojson = 320 POINTS
- slides.geojson = 39,561 POINTS (some have 3 coords [lon,lat,elev])

---

## Your three tasks

### B.1 — Confidence layer UI (per `ADDITION_confidence_layer.md`)

The pipeline instance generates `data/processed/confidence.geojson` (3 bands:
low/medium/high). Backend serves it at `/api/layers/confidence` (graceful 404
until the file exists). Add a toggleable "Data confidence" layer:

- Fetch via `fetchConfidence()` in `api.ts`. **Handle 404 gracefully** — if
  absent, the toggle is hidden/disabled, no console errors. Copy the existing
  influence-layer fetch+fallback pattern.
- Render **low-confidence band as grey DIAGONAL HATCH ~30% opacity** — NOT solid
  grey (solid would imply "safe"). Use a MapLibre `fill-pattern` with a generated
  diagonal-line image, or a stacked semi-transparent fill + line pattern.
- Add to `LayerToggle.svelte` ("Data confidence" checkbox, default OFF).
- Legend entry: "Grey hatch = monitoring/data gap (we're blind here)".
- In `ZoneDetail.svelte`: if a candidate sits in a low-confidence band, show a
  small warning note ("This site sits in a data-limited area").

### B.2 — Story / scrollytelling route `/story` (per `AGENTS_phase-4b.md`)

New route `routes/story/+page.svelte`. 7 full-viewport slides with CSS
scroll-snap, keyboard nav (Space / ArrowDown / ArrowUp), and progress dots.
Replaces the flat about page as the narrative entry point (keep `/about` too or
link it).

Slides:
0. Cover — USGS Tracy Arm aerial (public domain), title overlay.
1. Before/after — NASA Landsat images of a slide (NASA Earth Observatory, free).
2. Hig text — who he is, mason-jar sensors, works alone.
3. Two science quotes on dark bg (Walden 2025, Patton 2023 — the "nobody is
   looking ahead" gap).
4. Live map embed (iframe or component reuse of the main map).
5. Data-lag case — Tracy Arm ranks low because the 2025 event isn't in any
   inventory yet. "A site ranking low because the data lags is not a flaw — it's
   the problem the tool exists to expose."
6. Credits — USGS, NASA, DGGS, USFS, Ground Truth Alaska. NatGeo article LINKED
   (text credit), never embedded.

**⚠️ Copyright (§11b, strict):** ONLY US-Gov/NASA public-domain imagery. NEVER
embed NatGeo photos/maps/graphics. If unsure about an image, leave a placeholder
`<div>` with the intended USGS/NASA source URL in a comment.

### B.3 — Verify

- `pnpm build` clean (no new TS errors beyond the known harmless LSP
  `adapter-static not found` notes).
- Manually click through: confidence toggle on/off (graceful when geojson
  absent), `/story` scroll + keyboard nav, top-10 still pulse, search still works.

---

## Commit

```
cd C:/WorkArea/AI/scarp
git add frontend/
git commit -m "feat(frontend): confidence layer + scrollytelling story route"
gh auth switch --user flupkede
git push origin main
```

When done, report: confidence-layer behavior when geojson present vs absent,
`/story` slide count, and `pnpm build` result.
