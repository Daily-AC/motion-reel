# Explainers from real content

A short explainer makes one thing understood: a flow, a change, a feature. It is built only from the user's material (README, landing page, onboarding, release notes, benchmarks, a report, data, screenshots), and every word and number on screen can be traced to it.

## Contents
- Mine the material
- Write a storyboard per idea
- Build it
- Review it

## Mine the material

When the user names the subject, skip to the storyboard. When they ask what in a project is worth animating, read its README, landing page, quick-start or onboarding flow, recent release notes or changelog, benchmarks and any charts, plus anything attached. Look for three kinds of material:

1. **A flow one screenshot cannot explain**: the steps a new user takes, a request moving through a system.
2. **A change that falls flat as a bare number**: new versus old speed, size, cost or accuracy, where motion makes the difference felt (a progress bar that takes the measured time).
3. **The latest release's feature most worth showing**.

If a kind has no real material, say so; do not stretch a different comparison to fill it. When two sources disagree on a number, show both with their citations and let the user decide. Do not use a claim the project itself has not verified (for example, a figure missing from its own verified-claims list).

## Write a storyboard per idea

For each idea state who it is for, where it will play (README autoplay, social post, all-hands, vertical feed), how long it runs, the aspect ratio, and whether it must work muted. Then a table:

| Scene | Seconds | On screen (exact words, numbers, screenshots) | Source |
|---|---|---|---|
| S1 hook | 0–3 | "Your agent reads Twitter. It still can't read WeChat." | `README.md:9` — "Your agent reads Twitter. It still can't read WeChat. omnireach fixes that." |

Quote the source text exactly with `path:line`. Rank the ideas by usefulness to the user and present them. The subject is the user's choice; once they pick, build without further approval rounds.

## Build it

- One storyboard row is one shot in `project.json`. For a muted explainer set `bpm` and `sceneBpm` to 60, so `beats` are seconds and a storyboard duration is copied directly, and set `"sound": {"synth": false}` for a silent file. Cut to a track's grid only when the film has music.
- Set `"hud": null` on every shot unless the HUD's brand line and shot label are themselves sourced words the viewer should read.
- Put every on-screen string in the shot's `copy`. Add `facts` and `factsRoot` (the source project's directory, relative to project.json):

  ```json
  "factsRoot": "../my-project",
  "facts": [{"text": "2.7x", "source": "docs/benchmarks/read-path.md:15", "quote": "cold Playwright retrieval took **2.7x** the omnireach MCP time"}]
  ```

  `build.py` then refuses to build when a quote is not on its cited line(s) (`path:a-b` for a range) or in the cited commit message (`git:<rev>`, read from `factsRoot`'s repository), or when any number on screen is absent from every quote. A number the user dictates (“change this to 18%”) is a fact with `"source": "user"` and their words as the quote. The check covers numbers only; compare every on-screen phrase with its storyboard quote yourself.
- Screenshots and frames are real: extract a frame from a recording (`ffmpeg -ss 12.4 -i demo.gif -frames:v 1 assets/search.png`), load it in `prepare()`, draw it with `drawImage` at or below its native size, and crop to the region the viewer must read. Never redraw a UI from memory.
- Hold text long enough to read. Subtitle practice of about 15–17 characters per second is a starting check; the final number or claim of a scene needs the longest hold. When a fixed duration cannot hold its words, cut words or lengthen the scene, and tell the user which.
- Animated numbers and bars use real ratios. A counting number reads the frame's own clock, `Math.max(0,(TF-shot.start)*shot.rate)`, not the subframe `u`, or motion blur ghosts its digits; the final frame shows the exact sourced value.
- Later edits stay local: “slow down the second scene” is that shot's `beats`; “change this number” is its `copy` plus its fact.

## Review it

Decode one frame per second from the delivered MP4 and read every word and number against the storyboard and facts. Add 15–20 fps strips for any motion that carries meaning (a bar racing, a step being checked). Then follow review.md.
