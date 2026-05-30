# Scarp — submission procedure (after deploy)

End-of-hackathon checklist to submit Scarp via the **Polaris** Discord bot, **BUILDERS BATTLE** track.

## Pre-submit checklist (do all before opening the form)

- [ ] **App deployed & live** — frontend on Azure Static Web Apps, backend on App Service; open the public URL in a fresh browser, confirm the map loads and a zone click works.
- [ ] **`/health` returns** `{"status":"ok"}` on the deployed backend.
- [ ] **README** has the live URL, a screenshot, and run instructions.
- [ ] **Repo is public** at `github.com/flupkede/scarp` (or the on-day repo) and `main` is pushed.
- [ ] **Secrets check (judging: Security)** — no API keys/`.env` committed; key is read from env var; `data/raw/` and large binaries gitignored. Quick scan: `git log -p | grep -i "api_key\|secret\|token"` returns nothing real.
- [ ] **YouTube video uploaded** (Unlisted), watch URL copied. See `docs/video-plan.md`.
- [ ] **Project description** drafted (2–4 sentences — what it does, how it works, what makes it interesting).
- [ ] (Optional) **Aikido bug report** ready if you found a security bug — boosts security score + enters the Aikido Award.

## Discord submission flow (from the onboarding PDF)

1. Open Discord → the **North Star** server.
2. Make sure your **team is created** (`/menu` → **Create Team**, or **Join Team**). Do this early, not at submit time.
3. In any channel, type **`/menu`** and hit enter.
4. Click **Submit Project** (or **Create Team** first if you haven't).
5. On "Which track are you submitting for?" choose **BUILDERS BATTLE**.
   - ⚠️ **Do not pick LOOP LEAGUE** — it has a separate flow (ask a mentor).
6. Fill the **Submit · BUILDERS BATTLE** form:

   | Field | Value | Required |
   |---|---|---|
   | Project Title | `Scarp` | ✅ |
   | YouTube URL | the Unlisted watch URL from `docs/video-plan.md` | ✅ |
   | GitHub URL | `https://github.com/flupkede/scarp` | optional |
   | Project Description | 2–4 sentences (draft below) | ✅ |
   | Aikido bug report | paste if you have one, else leave blank | optional |

7. Click **Submit**.
8. Verify with **`/menu` → My Submission** that it registered correctly.

## Draft project description (paste-ready)

> Scarp ranks where the next tsunamigenic-landslide monitoring sensor should go in Southeast Alaska. It scores every area on susceptibility (steep, weak-rock slopes near retreating glaciers), exposure (people, roads, ferries, tourism), and the current monitoring coverage gap — then explains each ranking factor by factor, no black box. Built on public USGS and Alaska DGGS data, inspired by geologist Hig Higman, who installs $300 mason-jar sensors by hand and has no map of where to place the next one.

## After submitting

- [ ] Confirm the YouTube link plays from an incognito window (Unlisted ≠ Private — Private would block judges).
- [ ] Confirm the GitHub repo is reachable while logged out.
- [ ] Leave the deployed app **running** through judging.

## On-day note (AGENTS.md §11c)

If this is the live hackathon: build in a **fresh public repo** (`gh repo create flupkede/scarp-hackathon`), no code copy-paste from the private portfolio repo — specs and verified URLs only. Commit frequently so the AI judge sees iterative progress. Update the GitHub/YouTube URLs above to match the on-day repo.
