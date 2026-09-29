# Release validation

Observed on2026-09-29. These results support the package's stated scope; they do not guarantee equal aesthetic results from every agent, model or brief.

## Starter and package

The public initializer created an isolated NOVA project, with no dependency on the film's private workspace. Its actual browser pipeline rendered15.000seconds,1920×1080,60fps and900 decoded frames using16 temporal samples. The supplied verifier reported no technical errors or near-black warnings. Encoded audio measured−14.05LUFS /−3.78dBTP; source/encoded alignment was checked. See [starter evidence](validation/starter.json).

The Codex example initializer separately compiled and rendered representative opening/closing frames using its preserved geometry and local macOS typography. The original accepted Codex film is distributed as the case-study media; that original artifact had its own native4K render and independent visual reviews.

The Codex skill validator accepted the entrypoint. `npx skills add . --list` discovered exactly one skill. Bundle tests exercised deterministic idea seeds, successful project compilation, refusal to overwrite existing work, rejection of fractional-frame timing, and presence of licensed fonts. Python and JavaScript syntax checks passed.

Reference environment: macOS on Apple Silicon, Chrome, Node25.6.1 and FFmpeg8.1.2. CI's Ubuntu job runs package checks only; it is not a Linux GPU-render claim. No native Windows rendering was performed.

## Independent forward test

A fresh agent received only the skill and this new request: a15-second fictional precision-camera reel for EMBER, warm amber/ivory/near-black, “Find your focus,” original instrumental sound, no narration. Its working area was isolated; it had no parent film history or source and no network or paid services.

It authored six original shots at96BPM, a mechanical aperture/lens identity and a new felt-key-inspired score. It changed the visual subject and narrative rather than renaming the starter. Actual delivery:15.000seconds,1920×1080,60fps,900 decoded frames;−14.00LUFS /−3.67dBTP;0ms measured audio offset. See [encoded contact sheet](validation/ember-contact.png), [technical evidence](validation/ember.json) and [test film](https://github.com/Daily-AC/motion-reel/releases/download/v0.1.0/ember-forward-test.mp4).

A second reviewing agent found two mark/title overlaps. The author fixed them; an independent20fps recheck confirmed both resolved. A source archive was extracted into a fresh directory and actually rebuilt to a checked frame. The reviewer also noted that the focus-detail payoff could be richer; this remains an editorial limitation. No audience test or subjective audio listening was performed.

## Changes supported by the test

The test exposed the exact engine locations that must change when moving away from eight shots. The instructions now name those locations. Obsolete demo comments were removed, and font paths in the skill versus generated projects are explicitly distinguished.

Both this test and the starter emitted a non-fatal FFmpeg raw-packet-size warning before rendering. The cause was not diagnosed; full decode, count, timing and sampled image checks passed. The production guide records this without hiding the diagnostic.

The strongest established result is transfer of the workflow to a different subject and rhythm with a working file, editable source and review loop. It is not a universal claim of equal taste or a benchmark comparison between models.
