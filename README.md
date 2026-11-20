# Motion Reel

**A reusable agent skill for directing, drawing and scoring short motion reels in code.**

[中文](README.zh-CN.md) · [Skill](skills/motion-reel/SKILL.md) · [Creative method](skills/motion-reel/references/creative-direction.md) · [Case study](skills/motion-reel/references/case-study.md)

[![Codex case-study poster](docs/codex-poster.jpg)](https://github.com/Daily-AC/motion-reel/releases/download/v0.1.0/codex-showcase.mp4)

[▶ Watch the 15-second Codex case study](https://github.com/Daily-AC/motion-reel/releases/download/v0.1.0/codex-showcase.mp4)

This package came out of an iterated film, not a prompt collection. The initial cut was technically valid but too static; the next had sufficient movement but felt sparse. The accepted result kept its motion and gained a coherent palette, spatial response and selective detail. A flat reflection was removed after it failed in motion. Those decisions are part of the skill.

## Install

```sh
npx skills add Daily-AC/motion-reel --skill motion-reel -g
```

Or clone this repository and ask an agent to read `skills/motion-reel/SKILL.md`. The main instructions use ordinary files and local commands; `agents/openai.yaml` adds optional Codex UI metadata. No proprietary agent API is required.

Example request:

> Use $motion-reel to make a 15-second launch film for a fictional precision camera brand. Warm amber, ivory and near-black. The message is “Find your focus.” Give it original instrumental sound and an actual MP4.

## What is included

- A concise directing skill, with separate guides for composition, production and review.
- An editable 15-second starter with 3D shapes, kinetic type, particles, spatial interfaces and original synthesized audio.
- Linear-light temporal sampling, a shared beat grid, seeded geometry and a deterministic frame-capture pipeline.
- three.js scenes beside Canvas2D ones on the same timeline. Each subframe jitters shutter time, lens and light, so motion blur, depth of field, antialiasing and soft shadows come from one accumulator; a per-shot lens rig, screen close-ups that keep designed colors, and portrait framing derived from the landscape storyboard. three.js r186 is vendored; nothing to install.
- Guides for short-video feeds (an authored vertical cut, the hook, safe zones, covers) and the rendering pitfalls earlier films ran into.
- One `project.json` for copy, shot order, shot length and sound: “slow down the second shot” or “change this word” is a one-field edit, and every cut, impact and score cue follows.
- Licensed music: `beats.py` measures a track's grid against its kicks (librosa alone can lock onto the off-beat or drift), and the renderer places the track and ledgered sound-effect files sample-accurately.
- Short explainers from a project's real content: a method for finding what is worth animating, storyboards with `path:line` sources, and a build check that refuses on-screen numbers without a quoted source.
- Portable project scaffolding, dependency checks, encoded-output verification (including mono fold-down, per-cut sound sync and five timestamps for a person to audition) and motion-strip generation.
- Reference films: `refs.py` searches a public catalog of about 350 commercial brand films and launches and downloads one into the project for study; `measure_frame.mjs` and `measure_motion.py` (adapted from OpenMotion, Apache-2.0) put brightness, detail, accent, title height and motion travel side by side at matching moments.
- A random-string association tool, used as a source of ideas rather than a quality metric.
- Licensed bundled fonts, an original generic symbol, and a separately credited Codex example.

## Try the starter without an agent

Requirements: Node.js 22+, Python 3.10+, FFmpeg/ffprobe and Chrome/Chromium with WebGL2 float targets. Set `CHROME_PATH` if automatic discovery fails. Pillow is only needed for contact sheets, and librosa (through `uv run --with librosa --with matplotlib`) only for `beats.py`.

```sh
git clone https://github.com/Daily-AC/motion-reel.git
cd motion-reel
python3 skills/motion-reel/scripts/new_project.py ./work/nova --brand NOVA
cd work/nova
node render.mjs doctor
node render.mjs stills 0,0.8,4.6,8.6,10.6,14.3 --samples 8
node render.mjs render --out out/nova.mp4 --samples 16
python3 verify.py out/nova.mp4
uv run --with pillow python review.py out/nova.mp4 --strip 7.65:9.20:20
```

A mixed 2D/three.js example: `python3 examples/desk/create.py ./work/desk`, then render it the same way.

Use `--scale 2` for a native 4K master. `node render.mjs preview` serves a silent interactive preview; stop it when finished. Generated projects are self-contained and contain the source, fonts and tools needed to rebuild.

The starter is a vocabulary, not an eight-shot mandate. Change the subject's argument, relevant behavior, identity and handoffs. Recompose for portrait. Merely changing a name or adding more particles is not the method.

## Evidence and limits

See [validation](docs/validation.md) for the exact real runs performed for this release. macOS/Chrome is the tested reference environment. Linux/Windows browser discovery exists, but is not presented as a tested rendering guarantee. CJK and other writing systems need suitable fonts and fresh layout checks.

Technical validity, visual acceptance and audience response are separate. The included film received positive feedback reported by its creator; this does not establish that every agent or prompt will produce equivalent taste. Sound is measured for loudness, peaks, mono fold-down and cut timing; no measurement replaces listening, and the original case did not receive subjective listening review.

## License and credits

Code and original guidance: [MIT](LICENSE). Fonts and third-party material retain their own licenses; see [THIRD_PARTY.md](THIRD_PARTY.md). Codex/OpenAI marks in the case study are not covered as original toolkit branding and do not imply endorsement.

Created by Daily-AC with Claude and Codex. The rendering foundation came from an earlier local code-motion workflow; this skill distills the later film's art direction, review and portability work. [Lemo-Opuscar](https://github.com/lemomo-ai/lemo-opuscar) was related inspiration; its 39-style catalog is not bundled here.
