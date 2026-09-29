# Local production contract

## Dependencies and support

Core: Node.js 22+, Python 3.10+, FFmpeg/ffprobe, and a local Chrome/Chromium executable with WebGL2 and floating-point render targets. The renderer uses Node built-ins; it does not need a package install, account or API key. Contact sheets additionally use Pillow (`uv run --with pillow python review.py ...`).

macOS/Chrome is the tested reference environment. Browser discovery includes common Linux and Windows locations, but those platforms require their own real render validation. Use `CHROME_PATH` for an explicit executable. Do not assume GPU capabilities or render speed from the operating-system name.

## Project files

- `project.json`: identity, palette, canvas, FPS and musical timing.
- `scenes.js`: pure drawing functions plus their shared geometry.
- `score.js`: score arrangement using the engine's synthesis primitives.
- `symbol.js`: sampled contours for the example's original symbol.
- `engine.html`: compositor, instrument library and page-driven capture protocol.
- `build.py`: combines those local sources into `reel.html` and `check.js`.
- `render.mjs`: local server, owned Chrome process, encoding, normalization and muxing.
- `verify.py` / `review.py`: technical evidence and actual encoded-frame inspection.

The initial example uses eight four-beat scenes. `duration = bars × 4 × 60 / bpm`, so eight bars at 128 BPM equal 15 seconds. Change musical structure and the scene selector together for another duration or shot arrangement; setting a number alone does not create a new edit. Keep an integral output frame count.

For a different shot count/order, edit the `SCENES` array, `SHOT` boundary function, `LABELS`, `HITS`, `HUD_TONE` and the closing-shot condition in `hud`, all in `engine.html`. Update each scene's local-time offset and the score's cue references too. These are ordinary editable source locations, not hidden framework state. The independent six-shot camera test exercised this path.

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

Motion blur averages radiance, not display-encoded RGB: convert to linear light, accumulate, then encode the result. The tested engine uses RGBA16F. RGBA32F with unsupported linear sampling previously produced black output on Metal. Check framebuffer completeness and shader status; browser exceptions alone miss some GPU failures.

Raw `readPixels` rows are vertically inverted. The encoder flips them, explicitly converts RGB to BT.709 limited-range YUV, and stamps color metadata into the stream. A tagged file is insufficient if the actual matrix conversion was wrong.

Use 16 samples as a useful reference setting, not a quality law. For a static diagnostic frame, changing sample count should not materially change mean brightness. For moving edges, inspect whether blur appears and whether the subject remains readable. High FPS, 4K and more samples do not fix weak direction.

## Audio and fonts

The reference score is synthesized offline at 48 kHz. Two-pass loudness normalization targets about −14 LUFS; measure the encoded AAC true peak as well, because encoding may overshoot the WAV. Preserve deliberate dynamics and report any gain adjustment.

Inter Variable and JetBrains Mono are bundled with their OFL notices. The generic example uses English. For another writing system, supply a compatible licensed font, load it before capture and inspect actual glyphs. A Latin font file does not guarantee CJK support. The Codex case study used macOS system CJK fonts; those fonts are not distributed here.

Font paths differ by context: the installed skill stores them in `assets/fonts/`; the initializer copies them into the generated project's `fonts/`. CSS in that project references the latter.

## Failure recovery

- No frames: run the syntax check, doctor, then a single still. Read the actual browser/page error before changing the animation.
- Black GPU output: check WebGL2, framebuffer completeness and shader logs; compare a simple known-color frame.
- Cut has a dark pause: inspect the last two outgoing and first two incoming frames. Check whether a mask closes too early.
- Repeated or skipped frames: fix the protocol/time driver; do not hide the error by changing reported duration.
- Slow rendering: reduce samples or scale for drafts. Do not trade away final clarity without saying so.
- Platform mismatch: use explicit browser paths and verify real output. Do not describe an untested fallback as supported.
- FFmpeg printed a packet-size probe warning in the tested environment even though full decode and frame counts passed. Preserve the diagnostic, then inspect the actual file; do not suppress failures or infer corruption from that warning alone.
