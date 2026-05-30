# AGENTS_phase-4b — Interactive Docs / Story Page (demo presentation)

**Status:** 🟡 New — add to Saturday build after map core (SHOULD priority)
**Owner:** OpenCode
**Working directory:** `C:\WorkArea\AI\scarp\frontend\`
**Route:** `src/routes/story/+page.svelte`  (also reachable as `/story`)
**Purpose:** replaces the flat about-page stub in phase-4 section 12.
This page IS the demo presentation when screen-sharing. One URL, scroll or click through.

---

## 1. Concept

A **scrollytelling / full-screen slide deck hybrid** — each section snaps to full viewport height,
so pressing Space or scrolling advances exactly one "slide."
On screen-share it looks like a presentation. On a phone it scrolls naturally.
No PowerPoint. No PDF. A live webpage that also documents the project.

The judge gets a README link + a live URL. The story page IS the extended pitch.

---

## 2. Sections (7 slides, each full viewport height)

### Slide 0 — Cover (reuse splash assets)
- Full-bleed USGS Tracy Arm aerial photo (Cyrus Read/USGS, public domain)
- Text overlay:
  ```
  SCARP
  Mapping where the next landslide could strike —
  and where we're too blind to know.
  ```
- Bottom: "↓ scroll or press Space"
- No buttons, no nav — just the image and the hook

### Slide 1 — The Event (Tracy Arm before/after)
- Two-column layout: before image (26 Jul 2025) | after image (19 Aug 2025)
- Both from NASA Earth Observatory / Landsat 9, public domain
- Source: https://science.nasa.gov/earth/earth-observatory/tracy-arms-post-tsunami-landscape/
- Caption:
  ```
  Tracy Arm, Alaska. Left: 26 July 2025. Right: 19 August 2025.
  A mountainside collapsed into the fjord. The "bathtub ring" of
  stripped forest shows 481 metres of tsunami runup — second-highest ever recorded.
  Nobody saw it coming.
  ```
  Credit line: `Image: NASA Earth Observatory / Landsat 9 (USGS) — public domain`
- Pull quote (amber): **"If it had happened five hours later, a cruise ship would have been there."**
  — Dan Shugar, lead author, Science (2026)
- Small footnote: Shugar et al. 2026, doi:10.1126/science.aec3187

### Slide 2 — The Person (Hig)
- Left: text block. Right: optional image (Ground Truth Alaska public photo if available,
  otherwise a map of SE Alaska with Hig's ~50 monitoring sites marked as dots)
- Text:
  ```
  Bretwood "Hig" Higman is one of the few people systematically
  searching for the next collapse before it happens.

  He builds monitoring sensors in mason jars — about $300 each —
  and installs them by hand across Southeast Alaska.
  He is monitoring over 50 sites. He works alone or with one or two helpers.

  He has no map telling him where the next sensor would matter most.
  ```
- Source line: Christian Elliott, "Lessons of a landslide detective,"
  National Geographic (2026) — https://www.nationalgeographic.com/environment/article/alaska-landslides-geologist-detective
- Pull quote: **"Alaska is basically falling apart."** — Christian Elliott, NatGeo

### Slide 3 — The Gap (science says it plainly)
- Dark background (navy `#0f172a`), white text — contrast moment
- Two quote blocks side by side:

  Left:
  ```
  "...further substantiates the need for establishing broader
  and more systematic paraglacial hazard monitoring
  in a warming world."

  — Walden et al. 2025, Natural Hazards and Earth System Sciences
    Co-authored by Bretwood Higman
  ```

  Right:
  ```
  "No systematic landslide warning threshold currently exists
  at either local scales for towns within southeast Alaska
  or the regional scale for southeast Alaska as a whole,
  despite its high susceptibility to slope failures."

  — Patton et al. 2023, Natural Hazards and Earth System Sciences
  ```

- Below both quotes, centered:
  **"Two independent peer-reviewed papers. One gap. We built a first-order response."**

### Slide 4 — The Tool (live map embed)
- Full-bleed iframe (or SvelteKit component) showing the actual live Scarp map
  centered on Southeast Alaska, pre-zoomed to show ~10 target symbols
- Overlay strip at top:
  ```
  This is Scarp. Each target = a recommended sensor placement.
  Blue circles = existing monitoring stations.
  Grey hatch = where public data is too thin to rank.
  ```
- Small "open full map →" button linking to `/` (the main map page)
- This is the live demo moment when screen-sharing

### Slide 5 — The Data-Lag Finding (Tracy Arm in the rankings)
- Left panel: screenshot or live query of `/api/zones?limit=5` top results
- Right panel: text explanation
  ```
  Tracy Arm ranks 61st. Not because it's safe.

  Its geology is textbook-dangerous:
  susceptibility 1.000 · fjord-wall signal 0.881
  A perfect score on every geological indicator.

  But no public database contains the August 2025 event yet.
  The official record ends in 2024.

  We deliberately did NOT hand-edit it upward.
  A site ranking low because the data is a year behind
  is not a bug. It is the point.
  ```
- Amber highlight: **"The data lags reality. Scarp shows you where."**
- Toggle button: [Show Tracy Arm on map] → opens main map zoomed to Tracy Arm

### Slide 6 — Credits & Sources
- Clean, readable, no drama
- Sections:
  1. Inspired by
     - "Lessons of a landslide detective" — Christian Elliott, NatGeo 2026
     - Bretwood Higman / Ground Truth Alaska (https://groundtruthalaska.org)
  2. Science foundation
     - Walden et al. 2025, NHESS doi:10.5194/nhess-25-2045-2025
     - Patton et al. 2023, NHESS
     - Shugar et al. 2026, Science doi:10.1126/science.aec3187 (Hig is co-author)
  3. Data sources (table)
     | Source | Used for | License |
     |---|---|---|
     | USGS Belair et al. 2024 | Susceptibility (90m) | US public domain |
     | USGS 3DEP | DEM / slope | US public domain |
     | DGGS Inventory | Known slides | Alaska public domain |
     | OpenStreetMap | Exposure | ODbL |
     | Alaska Earthquake Center | Monitoring stations | Public |
  4. Imagery
     - Tracy Arm aerial: Cyrus Read + John Lyons / USGS — public domain
     - Before/after Landsat: NASA Earth Observatory / USGS — public domain
  5. Built for North Star AI Hackathon 2026
     GitHub: github.com/flupkede/scarp
     MIT License

---

## 3. Navigation mechanics

```svelte
<!-- Keyboard + scroll snapping -->
<style>
  .story-container {
    scroll-snap-type: y mandatory;
    overflow-y: scroll;
    height: 100vh;
  }
  .slide {
    scroll-snap-align: start;
    height: 100vh;
    min-height: 100vh;
  }
</style>
```

Keyboard:
```js
window.addEventListener('keydown', (e) => {
  if (e.key === ' ' || e.key === 'ArrowDown') nextSlide();
  if (e.key === 'ArrowUp') prevSlide();
});
```

Progress dots: fixed right side, 7 dots, filled = current slide.
Click a dot → scroll to that slide.

---

## 4. Image handling

All images are US government (USGS / NASA) public domain works. Safe to bundle.

**Download on Saturday morning (before building):**

```powershell
# Tracy Arm aerial — slide 0 cover + slide 5
# From USGS: https://www.usgs.gov/programs/landslide-hazards/science/2025-tracy-arm-landslide-generated-tsunami
# Save as: frontend/static/tracy-arm-aerial.jpg  (~500KB optimized)

# Before image — slide 1 left
# From NASA: https://science.nasa.gov/earth/earth-observatory/tracy-arms-post-tsunami-landscape/
# Save as: frontend/static/tracy-arm-before.jpg  (~300KB)

# After image — slide 1 right
# Same page, post-event image
# Save as: frontend/static/tracy-arm-after.jpg   (~300KB)
```

Compress with: `ffmpeg -i tracy-arm-aerial.jpg -q:v 3 tracy-arm-aerial-web.jpg`
Or just use browser devtools to save the already-web-sized versions from NASA.

Total image budget: ~1.1MB — fine for a static web app.

---

## 5. Relationship to existing pages

| Route | What it is |
|---|---|
| `/` | Main map (the tool) |
| `/story` | This page — scrollytelling docs + demo presentation |
| `/about` | REMOVE — merge into `/story` slide 6 (credits) |

In README: link both `[Live demo](/)` and `[Story / Methodology](/story)`.
In pitch: start on `/story` slide 0, scroll through slides 0-4 live,
then switch to `/` for the interactive map moment.

---

## 6. Saturday priority

This is a **SHOULD** — not a MUST, but high value:
- The AI judge reads the README first, then opens the live URL
- If the first thing they see is the map, they need to know the story
- If the first thing they see is `/story`, the context is already set
- The slide-4 live map embed means they still interact with the tool

**If time is short:** build slides 0, 1, 3, 4, 6 only (skip 2 and 5).
That gives cover → event → gap → live map → credits. Coherent even without the Hig and data-lag slides.

**Minimum viable story page (30 min):**
- Slide 0: cover image + title
- Slide 3: the two quotes (dark bg, white text) — the scientific foundation moment
- Slide 4: live map embed
- Slide 6: credits + sources

---

## 7. Time estimate

| Step | Estimate |
|---|---|
| Route scaffold + scroll-snap CSS | 10 min |
| Slides 0 + 1 (images + layout) | 20 min |
| Slide 2 (Hig text) | 10 min |
| Slide 3 (quotes, dark bg) | 15 min |
| Slide 4 (map embed / link) | 10 min |
| Slide 5 (data-lag) | 15 min |
| Slide 6 (credits) | 15 min |
| Keyboard nav + progress dots | 15 min |
| **Total** | **~1h50** |
| **Minimum viable (slides 0,3,4,6 only)** | **~40 min** |

---

## 8. Definition of Done

- [ ] `/story` route exists and loads
- [ ] 7 slides (or minimum 4), each full viewport height, scroll-snap works
- [ ] Tracy Arm before/after images in slide 1 with correct attribution
- [ ] Two science quotes in slide 3, dark background
- [ ] Live map visible in slide 4 (iframe or component)
- [ ] Keyboard Space/ArrowDown advances slides
- [ ] Progress dots visible and clickable
- [ ] All USGS/NASA images credited as public domain
- [ ] `/about` route redirects to `/story` or is removed
- [ ] README links to `/story` as "Methodology & Story"
