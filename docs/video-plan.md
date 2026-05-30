# Scarp — YouTube demo video plan

> The YouTube URL is **mandatory** on the hackathon submission form. No video = no entry.
> This is the production plan for that video.

## Decisions (locked)

| Choice | Value |
|---|---|
| Track | BUILDERS BATTLE |
| Length | 2:00–3:00 (target **2:30**) |
| Audio | **Own voice** voice-over (recorded), light royalty-free music bed under it |
| Structure | Demo + story (hook → problem → demo → method → close) |
| Visibility | YouTube **Unlisted** (link works for judges, not indexed publicly) |

## Judging-criteria mapping (keep these in mind while scripting)

| Criterion | How the video earns it |
|---|---|
| Impact | Open with real megatsunamis (Lituya 1958, Tracy Arm 2025); state who it helps (Hig + others) |
| Replicability | Show the explainable scoring breakdown in the zone detail panel; mention open data sources |
| Creativity | The "where to put the next sensor" framing + mason-jar signature detail |
| Vibes | Own voice, warm field-tool aesthetic, the 1958 wave fact, confident close |
| Security | One line: no secrets in repo, API key via env var, no user data stored |

---

## 1. Tooling

| Job | Tool | Notes |
|---|---|---|
| Screen recording | **OBS Studio** (free) | 1920×1080, 60 fps, record app + cursor. Hide bookmarks bar, use clean browser profile. |
| Voice-over recording | **Audacity** (free) | Record narration separately from screen capture. Mono, 44.1 kHz. |
| Noise cleanup | Audacity: Noise Reduction + light Compressor + Normalize to -1 dB | Record 3s of silence first for the noise profile. |
| Editing / assembly | **DaVinci Resolve** (free) or **Shotcut** (free) | Cut screen clips to narration; add captions. |
| Music bed | YouTube Audio Library or Pixabay Music (royalty-free) | Duck to ~ -22 dB under voice. **No copyrighted tracks** (judging includes "handled like adults"). |
| Thumbnail (optional) | Canva / GIMP | Map screenshot + "Where does the next sensor go?" |

### Mic tips (own voice)
- Quiet room, soft furnishings, mic ~15 cm off-axis to avoid plosives.
- Record the **whole script in one take per section**, leave gaps; pick best takes in edit.
- Glass of water nearby, smile while talking (it audibly warms the tone).

---

## 2. Narration script (~2:30, ~330 words)

> Timestamps are targets. Bracketed `[SCREEN: …]` notes drive the shot list in §3.

**[0:00–0:18] Hook**
[SCREEN: splash — USGS Tracy Arm aerial (public domain), quote overlay, then fade to map]
> "In 1958, a landslide in Lituya Bay, Alaska, made the highest wave ever recorded — 524 metres. In August 2025, a slide in Tracy Arm came within 50 metres of beating it. Nobody saw it coming."

**[0:18–0:45] Problem**
[SCREEN: slow pan over Southeast Alaska map; known-slide markers fade in]
> "Tsunamigenic landslides in Alaska have risen roughly tenfold in a decade — glaciers retreat, permafrost thaws, rain intensifies. Detection already exists. What doesn't exist is a map of *where to look next*. Geologist Hig Higman builds 300-dollar sensors in mason jars and installs them by hand. He can't be everywhere."

**[0:45–1:00] The idea**
[SCREEN: title card "Scarp — where the next sensor goes"]
> "So we built Scarp: a prioritisation tool. Not a detector — a map that ranks where the next sensor should go."

**[1:00–1:50] Demo (the core)**
[SCREEN: live app — zones heatmap; click a top zone; detail panel opens]
> "Scarp scores every patch of Southeast Alaska on three things: susceptibility — steep slopes in weak rock near retreating glaciers; exposure — people, roads, ferries, tourism; and the coverage gap — where monitoring is missing today."
[SCREEN: zone detail panel — score breakdown components]
> "Every score is explainable. Click a zone and you see exactly why it ranks: each factor, broken out. No black box."
[SCREEN: type a natural-language search, results filter]
> "Ask it in plain language — 'high-risk zones near tourist routes with no monitoring' — and it filters the map and tells you why."

**[1:50–2:10] Validation**
[SCREEN: top-10 list; highlight Barry Arm / Lituya / Portage]
> "Our top ranked zones land on the places experts already worry about — Barry Arm, Lituya Bay — without us hard-coding them. The method finds them on its own."

**[2:10–2:30] Close**
[SCREEN: mason-jar marker on map; then GitHub repo + URL on screen]
> "Hig has 300-dollar mason-jar sensors and no map of where to put them next. Now he does. It's open source, built on public USGS and Alaska state data, with no secrets in the repo. Scarp."

---

## 3. Shot list (record these screen clips)

Build/deploy the app first (Phase 4 done), then capture:

1. **Splash** — load the deployed site; capture the splash → map fade (3 s).
2. **Map overview** — Southeast Alaska, zoomed to show the orange heatmap. Slow zoom-in.
3. **Known slides layer** — toggle slides markers on.
4. **Zone click** — click a #1–3 ranked zone; detail/"field notebook" panel slides in.
5. **Score breakdown** — scroll the component breakdown in the panel.
6. **Search demo** — type the NL query; show map filtering + explanation text.
7. **Priority list** — sidebar top-10; click an item → flyTo animation.
8. **Mason-jar markers** — toggle stations layer (signature detail).
9. **Repo shot** — GitHub repo page + the live URL in the address bar.

Record each clip 2–3× so the editor has options. Keep the cursor calm and deliberate.

---

## 4. Production workflow

1. **Finish & deploy** the app (Phases 0–4). Video records the *deployed* site, not localhost, where possible.
2. **Record voice-over** (Audacity) → clean → export `narration.wav`.
3. **Record screen clips** (OBS) per §3 → save to `docs/video/raw/` (gitignored — large).
4. **Assemble** (Resolve/Shotcut): drop narration on track 1, sync screen clips to the script beats, add the music bed ducked under voice.
5. **Captions**: burn-in key phrases (Lituya fact, the 3 scoring factors). Helps muted autoplay + accessibility.
6. **Export**: 1080p, H.264, ~12–20 Mbps, AAC audio. File `scarp-demo.mp4`.
7. **Review** against the 5 judging criteria checklist above; re-cut if any is weak.

## 5. Upload to YouTube

- Sign in → Create → Upload video → `scarp-demo.mp4`.
- **Title:** `Scarp — where to put the next landslide sensor (hackathon demo)`
- **Visibility:** Unlisted.
- **Description:**
  ```
  Scarp ranks where the next tsunamigenic-landslide monitoring sensor should go in Southeast Alaska.
  Built for [hackathon]. Open source: https://github.com/flupkede/scarp
  Data: USGS, Alaska DGGS (public domain). Inspired by geologist Hig Higman / Ground Truth Alaska.
  ```
- Copy the watch URL → that goes in the Submit form's **YouTube URL** field.
- "Made for kids?" → **No**.

## 6. Copyright guardrails (strict — see AGENTS.md §11b)

- ✅ USGS / NASA / DGGS imagery (public domain) and your own app screen recording.
- ✅ Royalty-free music with a license that permits this use.
- ❌ No NatGeo photos/maps, no copyrighted music, no third-party video clips.
- The NatGeo article may be **linked** with credit; its media must not appear in the video.

## 7. Local asset folder (gitignored)

```
docs/video/
├── raw/            # OBS clips, Audacity projects — gitignored (large)
├── narration.wav   # cleaned voice-over
└── scarp-demo.mp4  # final export (optionally committed if < ~50 MB, else link only)
```
Add `docs/video/raw/` and `*.mp4` to `.gitignore` if not already covered.
