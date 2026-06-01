# Scarp — YouTube demo video plan

> The YouTube URL is **mandatory** on the hackathon submission form. No video = no entry.
> This is the production plan for that video.

## Decisions (locked)

| Choice | Value |
|---|---|
| Track | BUILDERS BATTLE |
| Length | 2:00–3:00 (target **2:30**) |
| Format | **Hybrid:** talking-head intro (you, on camera, outdoors in Ghent) → screen-share demo (voice-over) → short talking-head close |
| Intro audio | Recorded **live with the camera** — one take, NOT edited, NOT a separate voice-over. Just talk to camera. |
| Demo audio | **Separate voice-over** (Audacity) laid over OBS screen clips |
| Music bed | Light royalty-free, ducked under voice |
| Visibility | YouTube **Unlisted** (link works for judges, not indexed publicly) |

## Judging-criteria mapping (keep these in mind while scripting)

| Criterion | How the video earns it |
|---|---|
| Impact | Open with real megatsunamis (Lituya 1958 = 524 m, Tracy Arm Aug 2025 = 481 m, second-highest ever); state who it helps (Hig + others) |
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

---

### PART A — Talking-head intro (you, on camera, outdoors in Ghent)
> Record this LIVE with the camera, one take, talking to the lens. Don't edit it, don't dub over it — the slight imperfection of a real person outdoors is the point. Aim ~40–50 s. If you fluff a line, just restart the whole take; pick the best one. Phone in landscape, propped steady, sun behind YOU (not behind the camera), wind at your back.

**[0:00–0:50] Intro — to camera**
> "It's [thirty] degrees here in Ghent today — too hot for May. Exactly one year ago, that same warming collapsed a glacier onto a Swiss village called Blatten. The village was buried — but its three hundred people survived, because someone was monitoring the slope and got them out in time.
>
> Monitoring is the difference. And in Alaska, where retreating glaciers are dropping whole mountainsides into the sea, almost nobody is deciding *where* to watch next. In 1958, a slide in Lituya Bay made the highest wave ever recorded — 524 metres. Last August, Tracy Arm made the second-highest — 481 — in a fjord full of cruise ships, at half past five in the morning. Nobody saw it coming.
>
> A geologist called Hig Higman builds his own sensors, by hand, and installs them alone. He has no map telling him where the next one matters most. So I built one. It's called Scarp."

---

### PART B — Screen demo (voice-over over OBS clips)
> This part is separate voice-over (Audacity) laid over screen recordings. Calm, clear, unhurried.

**[0:50–1:05] The idea**
[SCREEN: title card / app splash → map]
> "Scarp is a prioritisation tool. Not a detector — a map that ranks where the next monitoring sensor should go."

**[1:05–1:55] Demo (the core)**
[SCREEN: live app — candidate points on the map; click a top site; detail panel opens]
> "It scores every patch of Southeast Alaska on what matters: susceptibility — steep, weak rock near retreating glaciers; a fjord-wall signal — a steep face dropping straight into deep water; exposure — people, roads, ferries, tourism; and the coverage gap — where there's no monitoring today."
[SCREEN: zone detail panel — score breakdown components]
> "Every score is explainable. Click a site and you see exactly why it ranks — each factor, broken out. No black box."
[SCREEN: type a plain-English search, results filter]
> "Ask it in plain English — 'high-risk sites near tourist routes with no monitoring' — and it filters the map and tells you why."
[SCREEN: toggle the grey data-confidence layer ON]
> "And here's the honest part. The grey shows where public data is too thin to judge — about three-quarters of the region. The famous fjords, we can see. It's everything between them we can't. That grey isn't safety — it's the gap the science says we have."

**[1:55–2:15] Validation**
[SCREEN: find Barry Arm; show it ranking low with the "already monitored" note]
> "And it's honest about what it finds. Barry Arm — the slide that triggered a federal preparedness act — ranks low, on purpose, because it already has a sensor. Scarp doesn't find dangerous places. It finds places that are dangerous *and* unwatched. That's the whole point."

---

### PART C — Talking-head close (you, on camera — optional, can also be voice-over over the repo)
**[2:15–2:30] Close**
[SCREEN: you to camera, OR mason-jar marker → GitHub repo + URL on screen]
> "Hig has cheap sensors and an infinite coastline. Now he has a map. It's open source, built entirely on public USGS and Alaska data, with no secrets in the repo. And the same method works for the Alps, the Himalayas — anywhere a warming world is turning mountains into hazards. That's Scarp."

---

## 3. Shot list (record these screen clips)

Build/deploy the app first (Phase 4 done), then capture:

1. **Splash** — load the deployed site; capture the splash → map fade (3 s).
2. **Map overview** — Southeast Alaska, zoomed to show the orange heatmap. Slow zoom-in.
3. **Known slides layer** — toggle slides markers on.
4. **Zone click** — click a #1–3 ranked zone; detail/"field notebook" panel slides in.
5. **Score breakdown** — scroll the component breakdown in the panel.
6. **Search demo** — type the plain-English query; show map filtering + explanation text.
7. **Confidence layer** — toggle the grey data-confidence overlay ON; show how much of the region is grey.
8. **Barry Arm** — find Barry Arm in the list / on the map; show it ranking low with the "already monitored" note in the detail panel.
9. **Priority list** — sidebar top-10; click an item → flyTo animation.
10. **Mason-jar markers** — toggle stations layer (signature detail).
11. **Repo shot** — GitHub repo page (github.com/flupkede/scarp-app) + the live URL (scarp.dsoft.services) in the address bar.

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
  Built for North Star AI hackathon. Live: https://scarp.dsoft.services — Open source: https://github.com/flupkede/scarp-app
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
