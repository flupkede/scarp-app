# Phase 4 — Frontend (refined, with visual direction)

**Status:** 🟢 Ready
**Spec:** Section 8 of `AGENTS.md` + visual direction in section 11a
**Owner:** OpenCode (`@ZAI Coder`)
**Working directory:** `C:\WorkArea\AI\scarp\frontend\`

---

## 1. Goal

A Svelte 5 + SvelteKit application with a **field tool aesthetic** that opens with a dramatic splash screen, then becomes an interactive map of priority zones for landslide monitoring placement.

This is the demo. The frontend IS what the jury sees.

## 2. Visual direction (locked)

| Element | Choice |
|---|---|
| Overall feel | Scientific field tool — clean, honest, unambiguous |
| Basemap | Topographic with contours (NOT generic dark) |
| Candidate symbols | **Target** (concentric rings + center dot), white/black with contrast outline |
| Station symbols | **Filled circle**, blue/cyan (cool = infrastructure, not hazard) |
| Risk zone (influence area) | Filled polygon/circle, rank gradient: red (top) → orange → amber → yellow |
| Data-gap overlay | Grey diagonal hatch, ~30% opacity — reads as "no data" NOT "low risk" |
| Background | Off-white paper `#faf7f2` for panels, deep navy `#0f172a` for map overlay edges |
| Headers | Serif (Fraunces) |
| Body | Sans (Inter) |

**Four visually distinct elements, each carrying one meaning:**

| Element | Symbol | Color | Meaning |
|---|---|---|---|
| Recommended sensor placement | Target (concentric rings + dot) | White/black + outline | Refined exact spot — "place here" |
| Existing monitoring station | Filled circle | Blue/cyan | Already monitored — "watched" |
| Risk zone (influence area) | Filled polygon | Rank gradient (red→amber) | Dangerous + unmonitored area |
| Data-gap area | Diagonal hatch | Grey, ~30% opacity | "We're blind here" — NOT low risk |

**Symbol design rules:**
- **Target for recommendations:** small and exact. Concentric rings read as "zoomed-in exact location." Center dot = the refined coordinate.
- **Contrast outline mandatory:** target sits ON TOP of red/orange zone fills. White or black fill with thin contrasting stroke so it reads on any background.
- **Circle vs target:** fundamentally different shapes, so existing-vs-recommended is clear even without legend. Cool blue circle = installed; sharp target = proposed.
- **Grey hatch, never solid grey:** solid grey could be misread as "low risk." Diagonal hatch reads as "no data." Label explicitly in legend.

## 3. Stack

```json
{
  "dependencies": {
    "@sveltejs/kit": "^2.x",
    "svelte": "^5.x",
    "maplibre-gl": "^4.x",
    "@types/geojson": "^7946"
  },
  "devDependencies": {
    "tailwindcss": "^3.4",
    "@tailwindcss/typography": "^0.5"
  }
}
```

Use **Skeleton v4** for component foundations + svar-skeleton tokens for styling consistency.

## 4. Component tree

```
src/
├── app.html                        # Google Fonts link, no DOCTYPE customization
├── app.css                         # Tailwind + custom CSS variables
├── routes/
│   ├── +layout.svelte              # global layout, font loading
│   ├── +page.svelte                # main map view with splash
│   └── about/+page.svelte          # Hig story + credits + methodology
└── lib/
    ├── api.ts                      # typed fetch client
    ├── stores/
    │   └── zones.svelte.ts         # $state runes store
    ├── components/
    │   ├── Splash.svelte           # dramatic opening screen
    │   ├── Map.svelte              # MapLibre wrapper
    │   ├── PriorityList.svelte     # sidebar top 10
    │   ├── ZoneDetail.svelte       # slide-in panel
    │   ├── LayerToggle.svelte      # layer checkboxes
    │   └── SearchBar.svelte        # NL query input
    └── assets/
        ├── splash-tracy-arm.jpg    # USGS public domain photo
        └── icons/                  # SVG icons if needed
```

## 5. Splash screen (the wow opening)

**File:** `lib/components/Splash.svelte`

**Behavior:**
- Fades in on load over 0.5s
- Stays visible 3 seconds OR until user clicks anywhere
- Fades out over 1s to reveal the map underneath

**Visual structure:**

```
┌────────────────────────────────────────────┐
│  [USGS aerial photo — full bleed]         │
│                                            │
│  [dark gradient overlay bottom 40%]       │
│                                            │
│                                            │
│    SCARP                                  │  ← weighty serif, 5rem, white
│                                            │
│    In 1958, Lituya Bay saw the highest    │  ← serif italic, 1.5rem
│    wave ever recorded — 524 meters.       │
│    In August 2025, Tracy Arm came         │
│    within 50 meters of that record.       │
│                                            │
│    Nobody saw it coming.                  │  ← bold, amber #f59e0b
│                                            │
│    [tap to continue]                      │  ← small caps, opacity 0.6
│                                            │
└────────────────────────────────────────────┘
   Photo: USGS, Public Domain                 ← bottom-left, tiny
```

**Asset:** download the USGS photo on the day from:
- `https://www.usgs.gov/media/images/2025-tracy-arm-landslide-and-tsunami-trimline`
- Save as `frontend/static/splash-tracy-arm.jpg`
- Resize/compress to ~800KB (web-optimized)

**Skip button:** `?nosplash=1` query param skips it for dev work.

**Accessibility:** `prefers-reduced-motion` → no fade animation, just immediate display + dismiss button.

## 6. Map (`Map.svelte`)

**Tile provider — USE ESRI WORLD TOPO (verified working, no key, no CORS issues).**

⚠️ Lesson learned: OpenTopoMap tiles (tile-a/b/c.opentopomap.org) get blocked by CORS or rate-limited from the browser context — the map came up BLACK with no basemap. Do not use OpenTopoMap.

**Working source (verified):**
```js
// Esri World Topo — no API key, reliable CDN, coastline + contours + water
{
  type: 'raster',
  tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}'],
  tileSize: 256,
  attribution: 'Tiles © Esri'
}
```

⚠️ Do NOT apply `raster-brightness-max` or `raster-saturation` paint overrides — they dimmed the tiles to near-invisible. Leave the raster paint default.

**Fallback if Esri is slow:** CartoDB Voyager `https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png` (coastline + labels, no key).

**Layers (in z-order, bottom to top):**

1. Basemap (topo tiles)
2. `confidence-low` — fill layer from `/api/layers/confidence`, grey diagonal hatch pattern, low-confidence polygons only, opacity ~30%. **Must read as "no data" not "low risk".**
3. `confidence-medium` — fill layer, very faint, medium-confidence polygons
4. `slides-layer` — circle markers, GeoJSON source `/api/layers/slides`, color `#1f2937` opacity 0.4, radius 3
5. `zones-fill` — polygon fill (influence circles), source `/api/zones`, fill color by rank gradient (amber → red), opacity 0.35
6. `zones-outline` — polygon outline, same source, color `#7c2d12`, width 1
7. `zones-pulse` — symbol layer for top 10 zones only, pulsing circle animation
8. `stations-layer` — **filled circle**, blue/cyan `#3b82f6`, radius 5, source `/api/layers/stations` — reads as "infrastructure" not hazard
9. `candidates-target` — **target symbol** (concentric circles + center dot) for each candidate point, white fill with dark outline, source `/api/zones` geometry (points)
10. `zones-label` — text labels, source **`zones-top10`** (NOT full zones source) so only top 10 zones are labeled

**Required map controls:**
- `map.addControl(new maplibregl.NavigationControl(), 'top-right')` — zoom +/- buttons
- Legend box (bottom-left, `pointer-events: none`):
  ```
  SENSOR PLACEMENT
    ⊕  Recommended site (target symbol)
    ●  Existing monitoring (blue circle)

  RISK (unmonitored)
    red → amber  highest → lower priority

    ▨  Data-limited — not assessed (grey hatch)
  ```

**Initial view:** `center: [-135, 57], zoom: 5` (Southeast Alaska).

**Interactions:**
- Click on candidate target → `store.selectZone(id)` + map.flyTo candidate point at zoom 9
- Hover on influence circle → tooltip with rank + score
- Click on slide marker → small popup with source info
- Click on station circle → small popup with station code
- **Candidate in/near low-confidence zone → detail panel shows:** "Note: data coverage here is limited — treat this ranking as provisional."

**Zone fill color by rank — INLINE the expression, do NOT use a helper function.**

⚠️ Lesson learned: helper functions returning MapLibre expression arrays cause TypeScript reconciliation issues with strict paint types (forces `as any`) and may not resolve at the right time. Embed the expression directly in the paint object:

```js
'fill-color': [
  'case',
  ['<=', ['get', 'rank'], 10], '#dc2626',   // red — top 10
  ['<=', ['get', 'rank'], 30], '#ea580c',    // orange
  ['<=', ['get', 'rank'], 60], '#f59e0b',    // amber
  '#fbbf24'                                    // yellow — rest
]
```

Verify the `rank` property actually exists on each zone feature before relying on it.

**Pulsing animation for top 10:**

```js
let pulseSize = $state(8);
$effect(() => {
  const interval = setInterval(() => {
    pulseSize = 8 + 6 * Math.abs(Math.sin(Date.now() / 1000));
  }, 50);
  return () => clearInterval(interval);
});
```

**Zone labels — only show top 10, not all 74.**

⚠️ Lesson learned: using the full zones source with `text-allow-overlap: true` clutters the map with all 74 labels. Use the `zones-top10` source (slim, has centroids) for the label layer so only ranks 1-10 are labeled.

## 8. Sidebar — `PriorityList.svelte`

Off-white background (`#faf7f2`), serif headers.

```
┌─────────────────────────┐
│ [SearchBar]             │
│                         │
│ ─── 120 priority sites ─│
│                         │
│ #1  Score 1.000         │
│     PWS / Turnagain     │
│     [→ flyTo]           │
│                         │
│ #2  Score 0.999         │
│     Sitka area          │
│     [→ flyTo]           │
│ ...                     │
│                         │
│ [LayerToggle]           │
└─────────────────────────┘
```

For "region/area" labels: use a reverse-geocode lookup against a hardcoded list of fjords. Don't call an external geocoder — for top 10, we know the geography. Hardcode rough centroids:
- Lituya Bay
- Barry Arm
- Tracy Arm
- Portage Lake
- Pedersen Bay
- Glacier Bay
- Icy Bay
- Yakutat Bay
- ... pick closest by distance, fall back to "Lat, Lon".

## 9. Detail panel — `ZoneDetail.svelte`

Slide-in from right when a zone is selected. Field-notebook styling:
- Background: off-white paper `#faf7f2`
- Optional: subtle paper texture (radial gradient or SVG noise)
- Headers: serif italic
- Component breakdown: horizontal bar chart, hand-drawn feel (no slick gradients, use solid amber bars)

**Content:**

```
═══════════════════════════
   SITE #1 — PWS
═══════════════════════════

  Score          0.999
  Rank           1 / 120
  Influence      3 km radius

  Why this site?
  ──────────────
  ▓▓▓▓▓▓▓▓▓ Susceptibility   1.00
  ▓▓▓▓▓▓▓▓▓ Fjord wall        1.00
  ▓▓▓▓▓▓▓▓░ Proximity         0.99
  ▓▓▓▓▓▓▓▓▓ Steep slope       1.0
  ▓▓▓▓▓▓▓▓▓ Exposure          1.00
  ░░░░░░░░░ Coverage          0.00
  Coast: 0.5 km

  ⚠ Data confidence: HIGH

  Nearby known slides
  ───────────────────
  • 2024-06 Surprise Inlet (12km)
  • 1964 PWS earthquake slides (25km)
```

## 10. SearchBar — `SearchBar.svelte`

Make this visually prominent. It's the AI moment.

```
┌──────────────────────────────────────┐
│ 🔍  Ask anything...                 │
│                                      │
│ e.g. "near cruise ship routes"      │  ← placeholder
│                                      │
└──────────────────────────────────────┘
[Search]
```

After submit:
```
"AI: I filtered for zones with high tourism exposure..."  ← Claude explanation, italic
[Showing 12 zones · Clear filter]
```

## 11. Layout — `+page.svelte`

Two-column layout:

```
┌────────────────┬─────────────────────────────────┐
│                │                                 │
│   Sidebar      │   Map (with overlays)           │
│   (320px)      │   (flex-1)                      │
│                │                                 │
│                │   ┌──────────────────────────┐  │
│                │   │ Zone Detail (slides in)  │  │
│                │   └──────────────────────────┘  │
└────────────────┴─────────────────────────────────┘
```

On load, Splash.svelte covers everything full-screen.

## 12. About page

Tells the story. Three sections:

1. **The problem** — 3 short paragraphs: Lituya 1958 → Tracy Arm 2025 → 10x increase → Hig with mason jars (paraphrase from NatGeo article, ~150 words)
2. **The approach** — bullet list of data sources + scoring formula (high level, no math)
3. **Credits & ethics**
   - "Inspired by *Lessons of a landslide detective* by Christian Elliott, National Geographic, June 2026" → link
   - Data: DGGS, USGS, NASA Landsat, OSM
   - Imagery: USGS public domain
   - Built for North Star AI Hackathon, [date]
   - GitHub: `flupkede/scarp`

## 13. Color palette (Tailwind extend)

```js
// tailwind.config.js
theme: {
  extend: {
    colors: {
      paper: '#faf7f2',
      ink: '#1c1917',
      amber: { 500: '#f59e0b' },
      // ... existing Tailwind defaults remain
    },
    fontFamily: {
      serif: ['Fraunces', 'Georgia', 'serif'],
      sans: ['Inter', 'system-ui', 'sans-serif'],
    },
  }
}
```

Google Fonts link in `app.html`:
```html
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
```

## 14. Definition of Done

- [ ] Splash screen with USGS photo + quote shows on load, fades after 3s
- [ ] Map renders with topographic basemap (not generic dark)
- [ ] Candidate sites shown as **target symbols** (concentric circles + dot) with contrast outline
- [ ] Monitoring stations shown as **blue filled circles** (NOT mason jars)
- [ ] Influence areas (3km circles) shown with rank gradient (red→amber→yellow)
- [ ] Confidence layer toggleable: grey hatch for data-limited areas
- [ ] Top 10 candidates pulse subtly
- [ ] Click on candidate → detail panel slides in with field-notebook styling + component bars
- [ ] Data-confidence warning shown when candidate is in low-confidence area
- [ ] Search bar accepts NL query, AI explanation shown above results
- [ ] About page exists with Hig story + credits
- [ ] Tailwind + Fraunces font loaded and applied
- [ ] No copyrighted images in repo (only USGS + custom SVG)
- [ ] Mobile responsive enough that map shows on phone (not pixel-perfect required)

**Priority order if time is short:**
1. MUST: risk zones (colored) + target symbols — the core visualization
2. MUST: existing-station blue circles — the dangerous-vs-ignored story
3. STRONG: grey data-gap hatch — the honesty layer; if pressed, toggleable + verbal
4. NICE: pulsing animation, confidence warnings in detail panel

## 15. Time estimate

| Step | Estimate |
|---|---|
| Project scaffold + Tailwind | 15 min |
| Splash component | 30 min |
| Map component with basemap + layers + target symbols | 45 min |
| Confidence layer (grey hatch overlay) | 20 min |
| PriorityList sidebar | 20 min |
| ZoneDetail with field-notebook styling + confidence warning | 30 min |
| SearchBar + integration | 20 min |
| About page | 15 min |
| Polish + bug fixes | 30 min |
| **Total** | **~3.5 hours** |

## 16. What NOT to do

- **No mason jar icons** — dropped. Unclear, oversized, not cartographic. Use target symbols for candidates, blue circles for stations.
- **No colored targets** — vanish on colored zones. White/black fill + contrasting outline only.
- **No solid grey for data gaps** — reads as "low risk." Use diagonal hatch pattern + explicit label.
- **No settings UI** — config values in code only (color thresholds, region list).
- **No OpenTopoMap basemap** — CORS/rate-limited from browser, map goes black. Use Esri World Topo.
- **No `raster-brightness-max` / `raster-saturation` overrides** — dim tiles to near-invisible. Leave default.
- **No labels on all 120 candidates** — clutter. Labels only for top 10.
- **No helper functions returning MapLibre expressions** — TypeScript reconciliation issues. Inline expressions in paint objects.

## 17. Handoff to Phase 5

Phase 5 (deploy + pitch) needs:
- `pnpm build` works with no errors
- `frontend/build/` (or `.svelte-kit/output`) is a deployable static-ish bundle
- All assets in `frontend/static/` are checked in
- No references to localhost in the production code path (use env var `PUBLIC_API_URL`)
