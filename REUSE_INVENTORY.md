# REUSE_INVENTORY.md — Wat hergebruiken we zaterdag?

> Gegenereerd 2026-05-29. Alles hieronder leeft in `C:\WorkArea\AI\scarp`.

**Zaterdag-regel:** verse publieke repo, code **herbouwen op de specs**, geen code-copy.
Afgeleide **data/outputs** mogen wél mee — dat is geen code. Dit bestand zegt per item:
**HERGEBRUIK** (kopiëren), **HERBOUW** (vanaf spec), of **LOKAAL/HERDOWNLOAD** (nooit committen).

---

## 1. Het berekende 90m-grid — KLAAR, niet opnieuw rekenen

`data/processed/meta.json` bevestigt de bevroren run:
- cell_size: **90 m** · grid **16402 × 13999** = **229.611.598 cellen**
- gewichten: susc 0.25 · fjord_wall 0.25 · prox 0.20 · slope 0.10 · expo 0.10 · gap 0.10
- neighborhood 45 cellen (4.0 km) · **120 kandidaten** · rekentijd **547.9 s (~9 min)**

→ **HERGEBRUIK.** De scoring is af. Output staat in `data/processed/`. Niet herrekenen tenzij je puristisch wilt zijn (dan ~9 min via `50_score_zones.py`).

## 2. `data/processed/` — HERGEBRUIK (kopiëren naar verse repo)

De kaart-deliverables, klein genoeg om te committen:

| Bestand | Grootte | Wat |
|---|---|---|
| `candidates_influence.geojson` | 0.37 MB | **Kernoutput**: ~120 gescoorde kandidaten + influence |
| `slides.geojson` | 6.77 MB | Aardverschuiving-features op de kaart |
| `zones.geojson` | 0.04 MB | Regiozones (regionale fairness) |
| `zones_top10.json` | 0.005 MB | Top-10 zones |
| `stations.geojson` | 0.06 MB | Monitoringstations (blauwe cirkels) |
| `meta.json` | <0.01 MB | Grid-parameters/gewichten — audit trail |

## 3. `data/processed/intermediate/` — REGENEREERBAAR, NIET committen (~370 MB)

Pipeline-scratch, wordt door de prep-scripts opnieuw aangemaakt:
`coastline_seak_3338.geojson` (125 MB) · `steep_slopes_3338.geojson` (86 MB) ·
`tongass_3338.geojson` (53 MB) · `inventory_3338.geojson` (22 MB) ·
`all_slides_3338.geojson` (10 MB) · `coastline_seak.geojson` (76 MB) ·
`exposure_3338.tif` (1.3 MB) · `coverage_mask_3338.tif` (0.7 MB) · `usgs_slides_3338.geojson`, `stations_3338.geojson`

## 4. `data/raw/` — LOKAAL / HERDOWNLOAD, nooit committen (**12.4 GB**)

| Map | Grootte | Bron |
|---|---|---|
| `dem/` | **11.4 GB** | DEM-tiles — de long-pole, herdownload via `00_download.py` |
| `usgs_susc/` | 756 MB | **Primaire** susceptibility (Belair et al. 2024, DOI 10.5066/P13KAGU3) |
| `osm/` | 143 MB | OpenStreetMap (kustlijn/exposure) |
| `dggs/` | 89 MB | DGGS susceptibility — **DEPRECATED, fallback only** |
| `usfs/` | 48 MB | Tongass / US Forest Service |
| `usgs/`, `stations/` | <1 MB | USGS slides-inventory, stations |

`raw/MANIFEST.json` documenteert de bronnen → mee in de repo (klein, geen data).

## 5. Code — HERBOUW vanaf de specs (geen copy)

- `prep/` → run-order: `00_download` → `10_normalize` → `20_slope` → `30_exposure` → `40_monitoring_mask` → `50_score_zones`
- `backend/src/` (FastAPI)
- `frontend/src/` (Svelte/SvelteKit)

Specs als rebuild-bron: `C:\WorkArea\AI\scarp-plans\production\` (fase 1-5).

## Zaterdag, concreet

1. Verse repo + `.gitignore` die `data/raw/` én `data/processed/intermediate/` uitsluit.
2. Kopieer de 6 kleine deliverables uit `data/processed/` (sectie 2) in de nieuwe repo — dan staat het 90m-resultaat er meteen, zonder herrekenen.
3. Herbouw code vanaf de specs.
4. **Padcheck:** frontend/backend laden de geojson via een **relatief** repo-pad, niet `C:\WorkArea\...`. Absolute paden werken lokaal maar breken de Azure-deploy om 15:00 — Azure heeft die C-schijf niet.
