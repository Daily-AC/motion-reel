# Local production contract

## Dependencies and support

Core: Node.js 22+, Python 3.10+, FFmpeg/ffprobe, and a local Chrome/Chromium executable with WebGL2 and floating-point render targets. The renderer uses Node built-ins; it does not need a package install, account or API key. three.js r186 is vendored in `vendor/three/` (MIT) and loaded only by films with a three.js scene. Contact sheets additionally use Pillow (`uv run --with pillow python review.py ...`); beat analysis uses librosa and matplotlib (`uv run --with librosa --with matplotlib python beats.py ...`).

macOS/Chrome is the tested reference environment. Browser discovery includes common Linux and Windows locations, but those platforms require their own real render validation. Use `CHROME_PATH` for an explicit executable. Do not assume GPU capabilities or render speed from the operating-system name.

## Project files

- `project.json`: identity, palette, canvas, FPS, tempo, the shot list with all on-screen copy, font files and sound.
- `scenes.js`: scenes registered by name in `SCENE_LIBRARY`: Canvas2D drawing functions and three.js sets, plus their shared geometry.
- `score.js`: synthesized score arrangement using the engine's synthesis primitives.
- `symbol.js`: sampled contours for the example's original symbol.
- `engine.html`: compositor, three.js bridge, instrument library and page-driven capture protocol. It has no film-specific timing.
- `vendor/three/`: the three.js module build and its license.
- `build.py`: validates project.json, derives `timeline.json` and combines the sources into `reel.html` and `check.js`.
- `render.mjs`: local server, owned Chrome process, encoding, sound mixing, normalization and muxing.
- `beats.py`: measures a music track's beat grid and writes it into project.json (see music-and-sound.md).
- `verify.py` / `review.py`: technical and sound evidence, and actual encoded-frame inspection.

## The shot list is the timeline

Each entry of `shots` is `{scene, beats, label, hit, hud, copy, sfx}`; `id` defaults to `scene` and must be unique when a scene repeats. `beats` is real musical length at `bpm`; shots start where the previous one ends. Film duration is the beat total, rounded to whole frames. `hit` drives camera shake, chromatic aberration and the template's cut impact; `hud` is `"paper"`, `"ink"` or `null` (hidden). Every word a scene draws lives in its shot's `copy` or in the top-level brand fields, so a copy change never touches code.

A scene is `draw(g, u, t, shot)`. `u` is its own clock: 0 at the cut, reaching its native length (`SCENE_LIBRARY[name].beats × BEAT`) at the next cut. `t` is film time, for ambient motion that should continue across cuts. `BEAT`/`BAR` are the scene clock, set by `sceneBpm` (the tempo the scenes were choreographed at); `SPB` is real seconds per beat. Giving a shot more beats stretches its scene uniformly, so its handoff still completes at the cut. Integer multiples keep in-scene beat events on the beat; a shot stretched by a fraction keeps its cut on the beat but not its interior accents. When the music's tempo differs from `sceneBpm`, every scene stretches by the same ratio.

A scene can instead be a three.js set, `{three: setup, beats}`, whose setup returns the scene, a lens rig and per-subframe posing; read [three-d.md](three-d.md). It shares the timeline, cuts, shutter, post and capture with Canvas2D shots.

`TF` is the frame-center time. Anything that must not ghost under motion blur, above all numbers drawn on screen, reads `TF` (for a shot's own clock, `Math.max(0,(TF-shot.start)*shot.rate)`), not the subframe time.

Score cues use `SHOT('id')` (seconds) and the shot's `startBeat`; they follow reordering and stretching. Scenes that share material across shots (the template's particle word) read it with `copyFor(sceneName)`.

A cut appears on the first frame at or after its beat, so picture can trail the beat by up to one frame (16.7 ms at 60 fps); build.py prints the worst case. Sound leading picture by that much is inside the ITU-R BT.1359 detectability limit (45 ms).

Scenes may define `async function prepare()`; it runs once after fonts load and before any frame. Load images there (`const img=new Image();img.src='assets/x.png';await img.decode()`), never during capture. The renderer serves project files with image and font MIME types.

Canvas text does not wrap. `wrapText(ctx, s, maxWidth)` returns lines for the current `ctx.font`, breaking at spaces and between CJK characters, never starting a line with closing punctuation.

The default is landscape. New aspect ratios need authored layouts, not only changed dimensions. Test text fit, important subject bounds and platform-safe regions in the actual target canvas.

## Commands

```sh
node render.mjs doctor
python3 build.py
node --check check.js
node render.mjs stills 0,0.8,4.6,8.6,10.6,14.98 --samples 8
node render.mjs render --out out/reel.mp4 --samples 16
node render.mjs render --out out/reel-4k.mp4 --scale 2 --samples 16
node render.mjs preview
```

Preview is silent and uses fewer shutter samples. Its wall clock is only for interactive playback. Production captures deterministic times. Stop the preview process when finished. The server binds to localhost, chooses an available port and uses a temporary browser profile; never close unrelated browsers to fix a rendering failure.

The renderer saves a metadata file next to the MP4, including dimensions, duration, samples and measured sound levels. It rejects wrong frame sizes and non-sequential frames, surfaces page failures, and stops a stalled job instead of silently hanging.

## Rendering invariants

All scene state comes from `(time, frameCenterTime)`. Frozen seeded geometry is allowed; prior-frame accumulation, unseeded random calls, hover state and render-time network access are not. The compositor chooses the shot from the frame center so shutter sampling cannot blend across a hard cut. Clamp negative local time near a cut.

Motion blur averages radiance, not display-encoded RGB: convert to linear light, accumulate, then encode the result. The engine accumulates in RGBA32F when the browser can blend and linearly sample float32 targets (`EXT_float_blend` and `OES_texture_float_linear`, both present in Chrome on Metal), otherwise in RGBA16F with a line in the render log. Half floats round every addition: a flat color drifted by up to 1.7 code values at 64 samples. Without `OES_texture_float_linear` a linearly sampled RGBA32F texture reads black on Metal, which is why the engine requires both before choosing it. Check framebuffer completeness and shader status; browser exceptions alone miss some GPU failures.

Raw `readPixels` rows are vertically inverted. The encoder flips them, explicitly converts RGB to BT.709 limited-range YUV, and stamps color metadata into the stream. A tagged file is insufficient if the actual matrix conversion was wrong.

A three.js shot adds each subframe's linear radiance from a half-float target to the same accumulator, then the post adds optional bloom, applies the rig's exposure and either clips (designed colors come out exact) or applies a highlight shoulder. Each subframe also gets a lens sample and a light sample for depth of field and soft shadows; three-d.md has the details and checks.

Use 16 samples as a useful reference setting, not a quality law. For a static diagnostic frame, changing sample count should not materially change mean brightness. For moving edges, inspect whether blur appears and whether the subject remains readable. High FPS, 4K and more samples do not fix weak direction.

## Audio and fonts

Sound has three optional sources in `project.json`'s `sound`: the synthesized score (`synth`), one licensed track (`music`) and sound-effect files (`library` plus per-shot `sfx` cues). `"synth": false` with no music or effects renders a silent film with no audio stream. The page renders only the synthesized part; `render.mjs` places the track and each effect sample-accurately with FFmpeg from `timeline.json`, mixes without automatic normalization, then two-pass normalizes to about −14 LUFS. It measures the encoded AAC true peak, because encoding may overshoot the WAV, and lowers the gain until it is at most −1.2 dBTP. Preserve deliberate dynamics and report any gain adjustment. `build.py` refuses a track or effect without `source` and `license`. Details and the beat-grid workflow: music-and-sound.md.

Inter Variable (`"Reel Sans"`) and JetBrains Mono are bundled with their OFL notices. The generic example uses English. For another writing system, supply a compatible licensed font and inspect actual glyphs. A Latin font file does not guarantee CJK support. `project.json`'s `displayFont` replaces the display family that `F()` uses by default (for example `"PingFang SC, system-ui"`); a system font renders only on machines that have it. The Codex case study used macOS system CJK fonts; those fonts are not distributed here.

To use a font file, put it in the project and declare it in `project.json`:

```json
"fonts": [{"family": "Noto Serif SC", "file": "fonts/NotoSerifSC-Bold.otf", "weight": 700, "license": "OFL-1.1, fonts/NotoSerifSC-OFL.txt"}]
```

`build.py` turns each entry into an `@font-face` rule. It refuses a missing file, a file outside the project folder and an entry without `license`, as it does for audio; `weight` (a number, or a range such as `"100 900"` for a variable font) and `style` are optional. The page loads every declared face, and the two bundled ones, before `prepare()` and the first frame, whatever `displayFont` names; a face that cannot load stops the render with its family name. Draw with it as `F(700, 64, '"Noto Serif SC"')`, or make it the display face with `"displayFont": "\"Noto Serif SC\", serif"`. Keep the license text beside the file, and do not commit or share a font file you have no license for.

Font paths differ by context: the installed skill stores them in `assets/fonts/`; the initializer copies them into the generated project's `fonts/`. CSS in that project references the latter.

## Failure recovery

- No frames: run the syntax check, doctor, then a single still. Read the actual browser/page error before changing the animation.
- Black GPU output: check WebGL2, framebuffer completeness and shader logs; compare a simple known-color frame.
- Cut has a dark pause: inspect the last two outgoing and first two incoming frames. Check whether a mask closes too early.
- Repeated or skipped frames: fix the protocol/time driver; do not hide the error by changing reported duration.
- Slow rendering: reduce samples or scale for drafts. Do not trade away final clarity without saying so.
- Platform mismatch: use explicit browser paths and verify real output. Do not describe an untested fallback as supported.
- FFmpeg printed a packet-size probe warning in the tested environment even though full decode and frame counts passed. Preserve the diagnostic, then inspect the actual file; do not suppress failures or infer corruption from that warning alone.

## Pitfalls

- Fonts on macOS Chrome: in canvas, `system-ui` is the variable-weight SF Pro, while `-apple-system`, `ui-monospace` and `"SF Mono"` fall back to a default face. Use a bundled font or declare a licensed file in `fonts`, and check the glyphs in a still.
- `strokeText` on a variable font draws the glyphs' internal overlapping contours. For outlined type, stroke wide and then `fillText` the interior in the base color.
- Grain costs bitrate: post grain of 0.014 at CRF 17 made a 15 s 1080p film about 15 MB. Keep grain subtle (the engine uses 0.005) and do not encode with `-tune grain`.
- When a shot zooms far in, divide line widths by the zoom factor, or a hairline (a horizon, a grid) becomes a thick banded stripe.
- Homebrew's FFmpeg build lacks the `drawtext` filter; label frames with Pillow (`review.py`) instead.
- Shell loops on macOS: `seq 1 0` counts down instead of producing nothing. Loop with `while` when the count can be zero.
