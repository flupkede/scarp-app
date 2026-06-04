# Zoom prep — call with Hig (simple version)

**Time:** Thursday 9 PM Alaska = Friday 7 AM Belgium.
**Goal:** I'm not here to defend Scarp. I'm here to learn where it fits and what to build next. Listen more, talk less.

## My one line (start with this)

"I see Scarp as the first step: it scans the coast and says where to look. It comes *before* a system like Hermanns, which only starts once you already know a slope is moving. Scarp tries to find the spots from public map data, before anyone has been there."

## The chain (my simple picture)

1. **Where do we look?** -> public map data -> that's Scarp.
2. **Is it moving here?** -> InSAR or a sensor -> that's where your mason jars sit.
3. **How dangerous is it?** -> fieldwork + movement -> that's Hermanns.

Ask him: "How do you decide where to put the next sensor now? Is that where Scarp could help?"

## What I learned from your two papers (shows I read them)

Say it simply:
- "Your system works site by site, in the field, with expert judgement. You score a slope on a set of criteria and that gives a hazard number and a risk level."
- "Your new 2026 version adds two things I liked: **volume** (how big the slope is) and **permafrost**. The permafrost one looked strong, slopes in permafrost fail much more often."
- "One honest point I took from you: some slopes failed without ever looking unstable first. So 'it must already be moving' is not safe to assume. That's a humility point for me too."

## The three things your work tells me to fix (say in plain words)

1. **The slope double-count.** "You're right, I counted slope twice. The fix is not just to delete it. I replaced it with height × steepness — so a tall steep wall scores high and a small steep bank does not. That removes the double-count and adds the size signal I was missing." (Done — implemented as `volume_proxy` in the scoring pipeline, data regenerated.)
2. **Add movement data (InSAR).** "Right now Scarp only looks at the shape of the land, not whether it moves. That's why it has false alarms. Adding InSAR (OPERA, Sentinel-1, later NISAR) is the biggest real improvement, and it's what you pointed me to."
3. **Permafrost later.** "Your 2026 paper and the public permafrost data make this doable. Something for later."

## Questions to ask him (let HIM talk)

- "What did you mean when you said Hermanns might focus on the wrong variables?" (Don't guess out loud. Let him explain.)
- "Is movement data from InSAR the best thing I could add, or would you start somewhere else?"
- "For Alaska, how much does it matter that some failures are triggered by earthquakes?" (Lituya 1958 was a quake.)
- **Save for later in the call:** "If I turned your method into real software, where you enter field notes and it gives you the hazard score, would that save you work?"

## Keep me honest (don't oversell)

- His system is 15 years old, national, tied to building codes, used on 120+ sites. Scarp is a weekend prototype. Keep that in mind.
- I'm a developer, not a geologist. Say it once, then let the work speak.
- If he breaks one of my assumptions: say thanks, write it down, don't argue. That's the whole point of the call.
- Don't say "your field has no software." Too arrogant. Only go there if *he* opens that door.
