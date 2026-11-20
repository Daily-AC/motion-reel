---
name: motion-reel
description: Direct and render polished short motion-graphics reels, brand films, kinetic showcases, short explainers and short 3D narrative films in code, with Canvas2D and three.js shots on one timeline. Use for a punchy product or identity reel; an explainer of a flow, a number change or a new feature built from a project's real content; a three.js film with a character, a lit set or depth of field; cutting a reel to a licensed music track; a vertical cut for Douyin, TikTok, Reels or Shorts; or when existing animation feels static, sparse, incoherent, or unfinished. Includes deterministic rendering, synthesized or licensed sound with measured sync, and source-checked on-screen numbers, plus a searchable catalog of commercial reference films with side-by-side frame and motion measurement. Not a live-action generator or long-form narrated-video workflow.
---

# Motion Reel

Deliver a finished film with a coherent identity, legible motion and a tested local rebuild. Use the included engine to remove rendering friction; direct the film for the user's subject rather than merely renaming its demo.

## Start from the brief

For an existing film, read its sources and accepted decisions, then change the requested dimension. Preserve approved motion when feedback concerns visual density; preserve the accepted logo when changing atmosphere. Keep previous delivered renders.

For a new film, infer sensible defaults and state the decisions that matter. Ask only about missing information that changes the result and cannot be inferred. A request for the finished video authorizes local implementation, previews and rendering; it does not authorize paid generation or publication. Do not insert mandatory approval gates when the user delegated direction.

Choose the audience, one message, duration, aspect ratio, identity and audio role. Record a short treatment. At 15 seconds, let behavior demonstrate the capability instead of squeezing in a narration-sized explanation.

For an explainer whose subject the user has not chosen (“find what in this project is worth animating”), read [explainer.md](references/explainer.md): mine the three kinds of material, propose ranked storyboards built only from real content, and let the user pick; the subject is theirs to choose. When the user names the subject, build it.

## Direct before decorating

Read [creative-direction.md](references/creative-direction.md) for substantial creation or revision. Make four decisions:

1. **A visual premise.** Name what transforms and why. “A thought becomes a constructed world” yields better decisions than “futuristic and epic.”
2. **A handoff.** For each cut, name the shape, trajectory, color or sound carried forward. Match actual boundary positions and scale; shared geometry is more reliable than similar drawings.
3. **A density rhythm.** Assign dense passages and quiet recognition moments. Sparse scenes may need their environment to respond to the subject, not particles everywhere.
4. **A return.** Let an opening element earn its place in the close. The first frame should already communicate; the last hold should stay readable.

Ground the direction in a peer: search a catalog of about 350 commercial brand films with `scripts/refs.py search <words>` and download one or two into the project with `refs.py get <id>`. Watch them before deciding the premise and handoffs; read [reference-films.md](references/reference-films.md) for search filters, rights and limits.

If ideation stalls, run `scripts/creative_seed.py`. Its random groups are associations, not instructions or quality scores. Select only associations that serve the film and record their visible consequences.

## Build from the working starter

Resolve bundled paths from this skill directory, not a hardcoded agent home or the current project.

```sh
python3 scripts/new_project.py /path/to/new-film --brand NOVA
cd /path/to/new-film
node render.mjs doctor
python3 build.py
node --check check.js
node render.mjs stills 0,0.8,4.6,8.6,10.6,14.3 --samples 8
```

The initializer copies a self-contained, editable 15-second example, fonts, renderer and verification tools. No API key or video-generation service is required. Read [production.md](references/production.md) before changing the project contract or diagnosing rendering.

- `project.json` is the single source for copy, shot order, shot length (`beats`), cut impacts (`hit`), HUD labels, font files (`fonts`, each with its license) and sound. `build.py` derives every time into `timeline.json`; a new shot list needs no engine edits. Author scenes in `scenes.js` as `draw(g, u, t, shot)` registered in `SCENE_LIBRARY`, and the synthesized score in `score.js` with cues as `SHOT('id')`. “Slow down the second shot” or “change this word” is a one-field edit in project.json.
- Change the demo's visual argument and relevant shot behavior for a new subject. Eight shots, blue and 128 BPM are examples, not requirements.
- Use actual logo assets for an existing brand. Preserve silhouette and internal spacing while adding depth. Never present the starter's original generic symbol as an official logo.
- Keep scene state a pure function of time. Seed randomness at initialization. Do not integrate from prior frames or fetch assets during capture.
- Select the shot from the frame-center time. All shutter samples of that frame belong to that shot. The compositor averages samples in linear light in an RGBA32F accumulator (RGBA16F, with a line in the render log, where the browser cannot blend float32 targets).
- Share impact timing between sound and movement. Use a sonic motif sparingly. Loudness checks cannot judge musical taste.
- For a licensed track, read [music-and-sound.md](references/music-and-sound.md). `beats.py` measures the grid against the track's kicks and writes `bpm` and `sound.music`; sound effects are ledgered files in `sound.library`. Look at the beat plot before trusting the grid.
- When a shot needs volume, a performing character, real light and shadow or depth of field, make it a three.js scene (`{three: setup, beats}`) and read [three-d.md](references/three-d.md). It mixes with Canvas2D shots in one film and shares the timeline, cuts, shutter, post and capture; a per-shot rig sets lens, focus, aperture and exposure.
- Recompose for another aspect ratio; a landscape crop is not an authored portrait cut. For Douyin, TikTok, Reels or Shorts, read [feed-publishing.md](references/feed-publishing.md): hook, safe zones, frame 0 as the cover.

## Iterate on the actual defect

| Feedback | Inspect | Useful change |
|---|---|---|
| Weak motion | Full action at 15–20 fps, not only its midpoint | Preparation, fast release, overshoot, scale change or spatial reconstruction |
| Empty frame | How the surroundings respond to the subject | Motivated light, shadow, far wire echo, construction plane or linked secondary pieces |
| Incoherent film | Palette, material, repeated motifs, cut endpoints | Carry one family of shapes/light/sound and the real brand identity |
| Clutter | Competing focal points and illegible copy | Remove the least meaningful layer; keep type and the close clear |
| Wrong-looking effect | Moving strip and the effect's source | Repair the relationship or delete the effect; a fake reflection can be worse than none |

Read [case-study.md](references/case-study.md) for demonstrated revisions and rejected approaches. Do not turn one successful film into a fixed recipe for every subject.

## Render, inspect, deliver

```sh
node render.mjs render --out out/reel.mp4 --samples 16
python3 verify.py out/reel.mp4
uv run --with pillow python review.py out/reel.mp4 --times 0,0.8,4.6,8.6,10.6,14.98
uv run --with pillow python review.py out/reel.mp4 --strip 7.65:9.20:20
uv run --with pillow python review.py out/reel.mp4 --cues
```

Read [review.md](references/review.md) for encoded-frame checks, motion strips, audio evidence and review handoffs. When a reference film was chosen, pick matching moments on a gridded sheet (`refs.py frames`), compare them with `node measure_frame.mjs` (brightness, detail, accent, title height) and `measure_motion.py` (travel, flags limp or excessive motion); both are in the project and explained in reference-films.md. `verify.py` also measures mono fold-down and each cut against its sound onset, and names five timestamps for a person to audition; `audio_gates.py` catches a held drone in the score (music-and-sound.md). Use `--scale 2` for a native 4K master when needed, after the direction survives review.

Separate **technical validity**, **visual acceptance**, and **audience response**. None proves the others. Do not claim aesthetic quality from frame counts or an agent's score.

For a substantial film, use an independent reviewing agent when available and allowed by the host. Give it the brief and fixed encoded artifact, not the desired verdict. Otherwise perform an explicit second review and disclose that it was not independent. Fix specific findings and recheck changed intervals rather than endlessly rescanning unchanged work.

Deliver the playable MP4, source/rebuild command and a useful poster. Report actual duration, material limits, and whether sound was only measured or also heard; when it was not heard, hand over the five listening timestamps. Publish within the user's authorization. Read [credits-and-assets.md](references/credits-and-assets.md) before sharing third-party assets.
