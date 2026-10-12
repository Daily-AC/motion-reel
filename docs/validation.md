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
