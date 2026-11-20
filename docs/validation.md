# Release validation

Observed on 2026-09-29. These results support the package's stated scope; they do not guarantee equal aesthetic results from every agent, model or brief.

## Starter and package

The public initializer created an isolated NOVA project, with no dependency on the film's private workspace. Its actual browser pipeline rendered15.000 seconds, 1920×1080, 60 fps and900 decoded frames using 16 temporal samples. The supplied verifier reported no technical errors or near-black warnings. Encoded audio measured−14.05 LUFS /−3.78 dBTP; source/encoded alignment was checked. See [starter evidence](validation/starter.json).

The Codex example initializer separately compiled and rendered representative opening/closing frames using its preserved geometry and local macOS typography. The original accepted Codex film is distributed as the case-study media; that original artifact had its own native 4K render and independent visual reviews.

The Codex skill validator accepted the entrypoint. `npx skills add . --list` discovered exactly one skill. Bundle tests exercised deterministic idea seeds, successful project compilation, refusal to overwrite existing work, rejection of fractional-frame timing, and presence of licensed fonts. Python and JavaScript syntax checks passed.

Reference environment: macOS on Apple Silicon, Chrome, Node 25.6.1 and FFmpeg 8.1.2. CI's Ubuntu job runs package checks only; it is not a Linux GPU-render claim. No native Windows rendering was performed.

## Independent forward test

A fresh agent received only the skill and this new request: a 15-second fictional precision-camera reel for EMBER, warm amber/ivory/near-black, “Find your focus,” original instrumental sound, no narration. Its working area was isolated; it had no parent film history or source and no network or paid services.

It authored six original shots at 96 BPM, a mechanical aperture/lens identity and a new felt-key-inspired score. It changed the visual subject and narrative rather than renaming the starter. Actual delivery:15.000 seconds, 1920×1080, 60 fps, 900 decoded frames;−14.00 LUFS /−3.67 dBTP;0 ms measured audio offset. See [encoded contact sheet](validation/ember-contact.png), [technical evidence](validation/ember.json) and [test film](https://github.com/Daily-AC/motion-reel/releases/download/v0.1.0/ember-forward-test.mp4).

A second reviewing agent found two mark/title overlaps. The author fixed them; an independent 20 fps recheck confirmed both resolved. A source archive was extracted into a fresh directory and actually rebuilt to a checked frame. The reviewer also noted that the focus-detail payoff could be richer; this remains an editorial limitation. No audience test or subjective audio listening was performed.

## Changes supported by the test

The test exposed the exact engine locations that must change when moving away from eight shots. The instructions now name those locations. Obsolete demo comments were removed, and font paths in the skill versus generated projects are explicitly distinguished.

Both this test and the starter emitted a non-fatal FFmpeg raw-packet-size warning before rendering. The cause was not diagnosed; full decode, count, timing and sampled image checks passed. The production guide records this without hiding the diagnostic.

The strongest established result is transfer of the workflow to a different subject and rhythm with a working file, editable source and review loop. It is not a universal claim of equal taste or a benchmark comparison between models.

## Public distribution check

The public GitHub repository was installed through `npx skills add` into a fresh project directory. The installed copy initialized a SIGNAL project and rendered opening/closing stills with its own bundled assets. Both release-video download URLs returned HTTP 200. No global agent configuration was changed for this check.

## Shot list, licensed music and explainers (2026-10-12)

Observed on macOS/Chrome, Node 22.22.0, FFmpeg 8.1.2, librosa 1.0.0. Each change was ablated: the same task with and without it, measured on decoded output. Agent arms are one run each; treat them as evidence, not statistics.

### The shot list replaced hand-timed engine code

The default starter renders identically before and after the refactor: all 900 decoded video frames have the same `framemd5`, and the synthesized soundtrack nulls to −134.9 dB against the old one (two renders of the old starter null to −134.2 dB). The Codex example's ten sampled stills are byte-identical after migration. The engine locations listed in the section above no longer need editing.

Two fresh agents received the same three requests on the starter, one with the previous skill and one with this one: double the CODE shot, remove the MOMENTUM shot, change one caption. Both ended with sound hits within 6 ms of every intended cut.

| Request | Previous skill | This skill |
|---|---|---|
| Double shot 2 | 4 files, +15/−13 lines; 9 bars at 60 fps is not a whole frame count, so it changed the film to 64 fps; 3 min 36 s | `project.json`, 1 line; 36 s |
| Remove a shot | 4 files, +17/−39; `SCENES`, `LABELS`, `HITS`, `HUD_TONE`, the HUD condition and score offsets edited by hand | 3 files, +5/−20 (shot entry, two score cues that named the shot, one wipe color); 78 s |
| Change a caption | 2 files, +2/−2, plus an unrequested HUD label change; 43 s | `project.json`, 1 line; 39 s |

### Explainers from real content

Four agents received “find what's worth turning into a short animation and show me storyboards first” for two real projects (omnireach and a private CLI), two with each skill. A separate agent scored the four answers blind, checking every on-screen number and quote against the project.

| Project | Skill | On-screen items verified at the cited place | Not found / contradicted | Rubric (10 checks) |
|---|---|---|---|---|
| omnireach | previous | 37 of 44 | 1 / 1 | 6 |
| omnireach | this | 49 of 49 | 0 / 0 | 10 |
| CLI | previous | 24 of 29 | 2 / 0 | 4 |
| CLI | this | 39 of 39 | 0 / 0 | 10 |

The previous skill's answers had stronger motion ideas but no per-scene sources, imposed its 15-second brand-reel grid, and missed the latest release in one project. The new answers surfaced conflicts between the projects' own sources (for example two different like counts) instead of choosing one. One answer exposed a figure that exists only in a commit message; `facts` now accept `git:<rev>` sources. The facts check refused a wrong number, a quote cited at the wrong line and an unknown commit, and accepted a correct `git:` citation.

### Beat grid against kicks

Ground truth: 20 synthetic 60 s tracks (96–140 BPM; four-on-the-floor, loud off-beat hats and bass, bass as loud as the kick, half-time kicks) with known kick onsets, and the starter's own score.

| Grid | Median error to the true beat |
|---|---|
| librosa `beat_track` as returned | 23–288 ms (tempo up to 2.6% off; off-beat lock on every loud-off-beat track) |
| librosa beats refit to constant tempo | 23–288 ms; 84–152 ms on the 15 tracks where librosa's tempo was 1.1–2.6% off |
| kick-locked (`beats.py`) | 0.3 ms on 19 of 20; the 20th (half-time kicks read at 70 BPM) 0.3 ms after `--double`; 28 ms on the starter's dense synthesized score |

On eight real Mixkit tracks, four with a steady kick were locked at 130.0, 124.0, 128.0 and 112.0 BPM where librosa reported 129.2, 123.0, 129.2 and 112.3; the two plots inspected by eye showed the grid on the kicks and librosa's beats drifting. A syncopated hip-hop track needed `--anchor`; an ambient track was locked with a rival-cluster warning; two tracks without a steady kick fell back to librosa with a warning.

End to end, the starter was cut to “Cat Walk” (Arulo, Mixkit): on librosa's grid, sound led picture by 33 ms at the first cut and 139 ms at the last, failing five of seven cuts; on the kick-locked grid every cut was within 20 ms, and within 24 ms with sound effects added. Effects placed by peak landed 0.0 and 1.3 ms from their cues. Music and effects were used in a render only and are not in this repository.

### Audio acceptance

Controls built from a starter render behaved as specified: right channel inverted, 14.39 dB mono loss and −0.996 correlation (error); identical channels, 0.00 dB; audio delayed 80 ms, −77 to −85 ms reported and no error; audio advanced 80 ms, +75 to +83 ms and errors on every interior cut; low band removed, `no_onset` without false errors. The first onset detector misread a kick that followed a fill as 196 ms late; it now selects the hit by energy rise and times it by the sharpest dB rise, and all controls reproduced. The starter's own score measures 0.17–0.18 dB mono loss.

A model with audio input (Gemini through a local agent CLI, no tools allowed) placed a known three-event probe in the right order and kinds but up to 2.5 s off in time. Asked blind about three soundtracks, it rated the synthesized starter score 3/5 and the licensed-track mixes 5/5 for sounding professionally produced, matched the two mixes of the same track, and said which one had layered effects (it estimated 5–7; there were 7). It also reported ducking that the mix does not contain. No person has listened to these renders.

### Same storyboard, two engines

One approved 24 s storyboard was built by separate agents with HyperFrames 0.8.149 and with this skill, then edited twice (lengthen one scene; change one phrase).

| | HyperFrames | motion-reel |
|---|---|---|
| Authoring to first render | 7 min 16 s | 6 min 22 s |
| Output | 30 fps (CLI default, no motion blur), 5.5 MB | 60 fps, 16-sample motion blur, 1.9 MB |
| Render | 20–34 s | 27–41 s |
| Lengthen scene 3 | 2 lines in one file (variable and root duration) | 1 line |
| Frames outside the edit | before: 176/180 identical, min 67.8 dB; after the shifted cut: min 48.9 dB | before: 360/360 identical; after: min 49.9 dB |

Neither contact sheet was clearly better: HyperFrames' browser layout set larger type but left the lower half of many frames empty; motion-reel's frames carried a connecting motif but its screenshot and body text were smaller. The motion-reel build found gaps that are now fixed: silent films, `hud: null` for explainers, `displayFont` for CJK, and a `wrapText` helper. HyperFrames' bundled sound effects credit Pixabay as a whole with no per-file origin, its `init` updates global agent skills unless disabled, and its telemetry is on by default. It is not added as a route in this skill.

## Reference films and side-by-side measurement (2026-11-20)

`refs.py` indexed 345 entries from the published catalog (version 0.1.0-black-friday-seo.20261119) in about 4 s; the slim index is 0.4 MB. Searches in Chinese and English, brand, kind, aspect and duration filters, and the all-words-then-any-word fallback behaved as intended on the live index. `get` downloaded two references; one guide was Markdown and one a ZIP package, both unpacked to `motion.md`. One catalog video is a 12 fps preview, which is why `get` prints the frame rate.

Known-answer checks (also in `tests/check_bundle.py`): a textured block moving 240 px measured 240.0 px in the reference and 240.0 px in a film that repeats the move two seconds later (`--ref-start`), with no flag; a film moving 90 px measured 90.0 px and was flagged as suppressed motion. A gray field with a white box gave mean luma 144.5 and 81.4 (hand calculation 144.5 and 81.4) and box heights 100 and 70 px (ratio 0.7, height check failed as intended).

On a delivered 60 fps reel with 16-sample motion blur, motion tracking resolved 0.3–0.5 s intervals (2.0–2.6 s type slide, 7.7–8.2 s camera move) and returned `unresolved` for 1.3 s intervals, a morphing panel grid and letter flashes. It did not fabricate a number in those cases. Frame statistics against a catalog end card (Claude Haiku 5.5) reported detail 0.0074 against 0.0125: correct as a measurement, but the reel's clean end card is deliberate, which is why the guide tells original films to read the numbers and not the remake thresholds.

The catalog's HTML demos for two entries were rendered at their reference keyframe times and compared side by side: both were rough compositional sketches (substituted fonts, missing glow and logos, shifted timing). `get` therefore leaves them out. The tool adaptation keeps `measure_frame.mjs` and `measure_motion.py`; OpenMotion's planar camera registration and particle-mark observer were not added because no film here needed them.

## three.js scenes on the shared timeline (2026-11-20)

Observed on an Apple M4 Pro, macOS 26.6, Chrome 157 (Metal), Node 22.23.4, FFmpeg 9.0.2, three.js r186 (npm `three@0.186.1`, integrity checked against the registry).

### Design

A three.js scene renders through a `WebGLRenderer` that shares the compositor's WebGL2 context, into a half-float target; each subframe's linear radiance goes into the same RGBA16F accumulator as Canvas2D shots. Rejected: a separate three.js canvas uploaded per subframe (8-bit, so emitters and highlights clip before motion blur averages them, plus a cross-context copy per subframe); moving the whole compositor into three.js (the 2D path would change and every 2D film would load three.js); a scene-owned camera (a lens rig as data lets the engine apply depth of field, jitter, shake and portrait framing the same way for every scene).

### 2D path unchanged

The starter's stills at 0, 0.8, 4.6, 8.6, 10.6 and 14.3 s with 8 samples are byte-identical between main and this branch. A full 16-sample render of the starter passed `verify.py` (900 frames, no errors or warnings, mono loss 0.18 dB, cuts within 5 ms of their sound).

Full renders were also compared frame by frame (`framemd5` of the decoded video) against a reference render from main, 30 renders each from main and this branch, interleaved on the same machine with the same settings. Main deviated in 7 of 30, this branch in 5 of 30. Every deviation but one is in the BUILD shot (the other is in IGNITION, on main): a few frames whose Canvas2D floor grid and lower caption rasterize slightly differently (PSNR 48.7–54.5 dB on the frames measured), after which H.264 carries the change to the next keyframe. This is pre-existing nondeterminism of Canvas2D rasterization on the GPU, not something the three.js path introduced. Stills of the same frames have been byte-identical every time.

On a portrait canvas the HUD now sits in the y ≈ 250 band that feed apps leave clear; landscape output is unchanged (the stills above were rechecked after this change).

### Known answers for the 3D path

Measured on rendered stills and an encoded film, now in `tests/check_bundle.py` (480×270; the tests skip when no browser can render WebGL2 float targets):

| Check | Result |
|---|---|
| Static lit set with depth of field and a jittered shadow-casting light: mean luma at 1, 4 and 16 samples | 122.53, 123.19, 123.08: spread 0.54% (limit 1%) |
| Card crossing at 59.96 px/frame (analytic): measured speed, blur length against speed × 0.5 frame | 60.00 px/frame; blur 30.66 px for 30.00 expected (+2.2%, limit ±15%) |
| Depth of field, Laplacian variance of near / far checkered cards | aperture 0: 11108 / 11034 focused near, 11106 / 11032 focused far. Aperture 0.3 focused near: 11106 / 819 (far 13.5× lower). Focused far: 882 / 11028 |
| 2D → 3D → 2D cuts at 1.02 s and 2.02 s, inside the shutters of frames 61 and 121 | Frames 60–61 / 62–63 and 120–121 / 122–123 hold only their own shot's color (0 pixels off by more than 12 levels); a synthetic one-subframe-in-sixteen blend is rejected by the same check |
| Bloom 0.3, threshold 1, on a 10 px disc over linear 0.02, same frame times with and without bloom | Disc at radiance 0.6: frames byte-identical. Disc at 8.0: footprint 254.97 both ways; ring 14–30 px from the centre 0.0199 → 0.4373 linear, ring 30–60 px 0.0199 → 0.1054 |

The first lens/light sample sets were Vogel spirals whose mean is off-center for small counts (0.16 of the radius at 4 samples); the brightness spread was 0.79%. Centering each set brought it to 0.54%.

Designed colors: a three.js background of `#0050FF` rendered as `0,80,255`. With the highlight shoulder always on it rendered as `33,82,241`, which is why the shoulder is opt-in per rig and the default clips like a 2D shot.

### Mixed film through the unchanged CLI

`examples/desk` (7 s, 1080p60, 16 samples: 2D panel, the panel on a three.js monitor, a reaction shot, a 2D end card) rendered in 11 s and passed `verify.py`: 420 frames, no errors or warnings, cuts 5–6 ms from their sound, mono loss 0.15 dB. Across the 2D → 3D match cut the paper, card and accent colors differ by at most 0.4 code values, and the PSNR between the last 2D and first 3D frame is 36.8 dB (neighbouring frames inside each shot: 42.6–44.0 dB, since the progress bar moves). Rendering stills exposed three defects that are now fixed in the example and described in three-d.md: the screen z-fought its bezel in the wide shot with the default 0.1 near plane, a landing squash that jumped inside one shutter interval rendered as two ghost copies, and a turn-to-camera with the wrong sign. A portrait render of the same project kept full width on the screen close-up and 0.62 of it on the reaction shots.

### Port of a delivered three.js film

Act I (2.0–12.0 s) of a 48 s three.js film with 12,000 instanced spheres, shadows, mirrored reflections and a spline camera was ported by importing its physics, stage and camera modules unchanged and replacing only its frame loop with the engine. Its 600 frames at 24 samples rendered in 70 s and passed `verify.py`. `measure_frame.mjs` against the original encoded film at matching frames:

| Original time | Original luma / detail | Port, engine post | Port, engine accumulator + the film's own post | The film's post without bloom (stills) |
|---|---|---|---|---|
| 2.50 s | 79.6 / 0.0330 | 63.0 (−20.9%) / 0.0680 (+106%) | 79.6 (0.0%) / 0.0330 (0.0%) | 62.3 (−21.7%) |
| 6.00 s | 51.8 / 0.0414 | 40.0 (−22.8%) / 0.0548 (+32%) | 51.8 (0.0%) / 0.0408 (−1.4%) | 39.5 (−23.9%) |
| 11.00 s | 34.5 / 0.0322 | 27.4 (−20.6%) / 0.0405 (+26%) | 34.5 (0.0%) / 0.0316 (−1.9%) | 27.2 (−21.2%) |

Without bloom the engine's post misses the 5% brightness and 20% detail targets. Geometry, camera, depth of field, motion blur and soft shadows match (PSNR 35.4–38.2 dB against the original once its post is applied to the engine's accumulator, against 19.5–26.3 dB with the engine's post). The whole difference was the original's bloom: its post with bloom set to 0 is as dark as the engine's, and bloom also softens every bead edge, which the detail metric counts.

The engine then gained optional bloom for three.js shots, the same dual-filter chain, set from the rig and off by default. With the engine's own post and the original's values (`bloom: 0.115, bloomThreshold: 0.88`), no tuning, the port passes at all three times:

| Original time | Original luma / detail | Port, engine post + bloom | PSNR against the original |
|---|---|---|---|
| 2.50 s | 79.6 / 0.0330 | 81.0 (+1.8%) / 0.0340 (+3.0%) | 31.4 dB |
| 6.00 s | 51.8 / 0.0414 | 52.7 (+1.7%) / 0.0411 (−0.7%) | 34.9 dB |
| 11.00 s | 34.5 / 0.0322 | 35.0 (+1.4%) / 0.0327 (+1.6%) | 36.7 dB |

The remaining 1–2% is the original's stronger vignette and shadow grade, which were not ported. Bloom off stays off: the starter's stills remain byte-identical to main, and all 420 frames of the mixed example render identically with the bloom code present and unset.

Not covered: Linux and Windows rendering of the 3D path, 4K renders of three.js shots, and any listening of the example's sound.

## Fixes from a field test (2026-11-20)

A fresh agent made a 32 s launch film with the skill and logged every point of friction. The five costliest were fixed and measured here. Observed on an Apple M4 Pro, macOS 26.6, Chrome 157 (Metal), Node 22.23.4, FFmpeg 9.0.2.

### Float32 accumulation for match cuts

The accumulator was RGBA16F, and half floats round every addition. On a flat ivory (`#F1EDE7`) 2D shot cut to a three.js background of the same color (480×270, per-channel means in the vignette-free centre of the last 2D and first 3D frame):

| Samples | RGBA16F: 2D / 3D off the design, step at the cut (stills) | Encoded step, off the design | RGBA32F: 2D / 3D off the design, step (stills) | Encoded |
|---|---|---|---|---|
| 8 | 0.23 / 0.13, 0.17 | 0.00, 0.00 | 0.00 / 0.02, 0.03 | 0.00, 0.00 |
| 16 | 0.68 / 0.26, 0.53 | 1.18, 1.87 | 0.00 / 0.02, 0.03 | 0.00, 0.00 |
| 32 | 0.88 / 0.41, 0.67 | 0.15, 2.00 | 0.00 / 0.02, 0.03 | 0.00, 0.00 |
| 64 | 1.71 / 1.02, 0.69 | 0.15, 2.00 | 0.00 / 0.02, 0.03 | 0.00, 0.00 |

The engine now accumulates in RGBA32F when the browser has `EXT_float_blend` and `OES_texture_float_linear` (Chrome on Metal has both), and otherwise falls back to RGBA16F with a line in the render log. Forcing the fallback reproduced the RGBA16F numbers above exactly and printed the line. The remaining 0.02 on the 3D side is the half-float target three.js renders into, quantized once per subframe rather than once per addition. A known-answer test in `tests/check_bundle.py` checks both sides within 0.5 code values of the design and of each other at 8, 16, 32 and 64 samples; against the previous engine it fails at 16 samples (2D side 0.68 off).

The desk example's match cut at 2.0 s (frames 119 | 120, 1080p), largest per-channel step on the paper, card and accent colors:

| Samples | RGBA16F stills | RGBA16F encoded | RGBA32F stills | RGBA32F encoded |
|---|---|---|---|---|
| 8 | 0.08 | | 0.06 | |
| 16 | 0.26 | 0.42 | 0.06 | 0.06 |
| 32 | 0.18 | | 0.06 | |
| 64 | 0.44 | 0.76 | 0.06 | 0.06 |

With RGBA16F both sides of the desk cut also darkened as samples rose: at 64 samples the paper sat up to 1.65 code values (2D) and 1.38 (3D) below its RGBA32F value. With RGBA32F every sample count gives the same means.

2D-only films are not byte-identical, and that is the fix working: half-float rounding had darkened them. On the starter's stills at 0, 0.8, 4.6, 8.6, 10.6 and 14.3 s, 3.2–12.8% of channel values changed at 8 samples and 5.9–19.5% at 16, every change exactly one code value and upward (mean +0.03 to +0.20, PSNR 55–63 dB against the previous engine); on the flat ivory shot the new value is the designed color exactly. Stills remain byte-identical from run to run. The full 16-sample starter render passed `verify.py` (900 frames, no errors or warnings). Render time, one run each: starter 35.1 s before and 37.5 s after; desk 11.0 → 11.9 s at 16 samples and 18.8 → 20.7 s at 64.

### Excess motion and reference-only measurement

Synthetic clips (640×360, 30 fps, a 120 px `testsrc2` tile on black, x264 CRF 12). Against a reference whose tile slides 240 px in one second, a film sliding 460 px right and 200 px down measured 460.0 / 200.0 px, `travelRatio` 2.42 (analytic 2.42) and `possibleExcessMotion: true`; the previous script passed it silently with exit status 0. The 240 px repeat and the 90 px film kept their earlier results (no flag; suppressed), with the excess flag false. Against a static tile the same fast film gave `possibleExcessMotion: null` and the "no bar" note. `measure_motion.py ref.mp4 --ref-start 1 --ref-end 2`, the form reference-films.md documents, measured 240.0 px; the previous script stopped with a usage error asking for `--start`, `--end` and `--out`. All of these are in `tests/check_bundle.py`.

### Project fonts

`project.json` gained `fonts: [{family, file, weight?, style?, license}]`; `build.py` writes one `@font-face` rule per entry and refuses a missing file, a file outside the project or an entry without `license`. The engine now loads every declared face before `prepare()` instead of only the mono face and the display family. Known answer, in `tests/check_bundle.py`: a copy of the bundled Inter declared as "Test Display", `displayFont` set to `serif`, frame 0 at one sample drawing the same word in "Reel Sans", "Test Display" and a family that does not exist. Both real families matched each other (glyph masks differed in under 2% of ink pixels) and differed from the fallback. With the previous preload line the same test failed: "Reel Sans" was still unloaded at frame 0 and fell back to the default serif, the field test's symptom. A font file that is not a font stopped the render with `Font "Test Display" failed to load`. The starter's stills are byte-identical with and without this change.

### Reference downloads

`refs.py get` against a local host that closes the first connection without a response: the second attempt downloaded the file intact and `meta.json` recorded `fps: 25` from the file. Against a host that always closes it: four attempts (0.5, 1 and 2 s apart), a single `refs.py get: download failed: … (4 attempts)` line, exit status 1, no traceback and no `refs/<id>/` folder; the previous script printed a traceback on the first dropped connection. Both cases are in `tests/check_bundle.py`. On the live catalog two launch films downloaded in 1.6–1.7 s each with `fps` 30.0 and 24.0 in `meta.json`, and `search model release` still fell back to any-word matches while `search 模型发布` matched launch films on all words, which is why reference-films.md now names the Chinese terms.

### Reference frames and batch measurement

`refs.py frames <id> --times …` writes one sheet of reference frames scaled to the film size (from `project.json`, or `--size`) with a grid every 100 film pixels, labelled every 200. Known answer, in `tests/check_bundle.py`: a 1280×720 reference with a white box at 100,100 (300×100) gridded at 1920×1080 shows the box at film 150,150 (450×150), grid lines at the right display columns, and `measure_frame.mjs --size 1920x1080` finds the same box within 2 px. On a live square catalog film three frames took 1.0 s; the caption states that the reference was stretched to 16:9, as the measurement stretches it.

`measure_frame.mjs --pairs` returned one result per moment, each identical to the single-moment run, with labels kept; three moments of a live reference against the desk example took 0.45 s. The `_ok` remake flags now appear only with `--remake`; the measurements (`height_ratio`, `region_status`, `clipped`) are unchanged without it.

### Held-drone gates (`audio_gates.py`)

Calibrated on three real scores: a rejected synthesized score, the same score with its sub oscillator removed (also rejected; its owner still heard "a low drone under the whole film"), and an accepted lo-fi jazz score.

| Score | Longest held pitch, 150–400 Hz | Longest held pitch, 40–150 Hz (level vs loudest) | Every 12 s has a 0.4 s rest 12 dB down |
|---|---|---|---|
| rejected | 30.7 s D4 (the whole film): fail | 14.3 s D2 (0 dB): fail | no |
| rejected, no sub | 30.7 s D4: fail | 10.3 s D3 (0 dB): fail | yes |
| accepted | 17.9 s F#4: pass | 7.5 s E2 (0 dB): pass | no |
| licensed fairy-tale track (new film) | 11.3 s G4: pass | 6.1 s G1 (−25 dB): pass | no (5–17 s) |
| synthesized score written from the section-table method (new film) | 12.1 s F#4: pass | 2.4 s G#1 (−3.5 dB): pass | yes |

The rest check did not separate accepted from rejected, so it is not a gate. With three calibration scores, the 20 s and 8 s thresholds are provisional. Known answer in `check_bundle.py`: 25 s of a steady D4 fails with 24.4 s held; a new pitch every 2 s passes. Nobody's listening has been replaced: the last two rows have not been heard by anyone yet.

### Continuous shot boundaries in `verify.py`

A film whose six shots run as one continuous move (every boundary inside a slow camera drift) changed 0 of 9,216 pixels at each cue in the 128×72 cut detector; `verify.py` still timed a "visual cut" 3 frames early and gated the music against it, which forced the score to be shifted toward invisible boundaries. Cut cues in three other films started 63–6,315 pixels at once. A cue with fewer than 20 is now reported as `no_picture_change` and not checked; the same film then reported all five boundaries that way and stayed `technical_ok`.
