# Review the encoded result

## Two different gates

Run `verify.py` for dimensions, decoded frame count, duration, FPS, color metadata and encoded audio measurements. Near-black/low-variation intervals are reported as diagnostic candidates: an intentional color wipe or quiet hold is not automatically a defect. Expected values come from `project.json` and the render metadata, not from assumptions about every movie being 15 seconds.

Technical success means the requested signals survived the pipeline. It does not prove that the movie is compelling or even that all its text is readable.

For the creative pass, inspect a full-film contact sheet and representative action strips at 15–20 fps. Decode them from the final MP4. A screenshot of the authoring page cannot expose all encoding, muxing or cut-boundary defects.

## Practical commands

```sh
python3 verify.py out/reel.mp4
uv run --with pillow python review.py out/reel.mp4 --times 0,0.8,4.6,8.6,10.6,14.98
uv run --with pillow python review.py out/reel.mp4 --strip 7.65:9.20:20
```

Choose times from the film's actual structure. Inspect the first and last decoded frame. At uncertain cuts, inspect two frames on each side at the output FPS. When an effect seems weak, temporarily make that effect conspicuous or compare enabled/disabled output; do not keep increasing arbitrary parameters without establishing whether it renders.

## Questions that change the edit

- Is there one readable focal action in each shot?
- Does it keep changing meaningfully, or settle into a slide after its entrance?
- Can the viewer follow the thing carried through each cut?
- Does the world respond through light, shadow, material or movement?
- Do new details support the subject or compete with it?
- Are the opening and closing identities complete and correctly drawn?
- Does the close remain readable long enough to register?
- Is a reflection, shadow or trail actually tied to the geometry it purports to follow?

Do not demand maximum density everywhere. Typography and the final identity often need more space than the construction or burst passage. Avoid assigning a single “quality score” to these questions.

## Independent review handoff

When delegation is available and allowed, give a reviewer:

1. The user brief and accepted constraints.
2. One fixed encoded file and its intended audience.
3. The specific uncertainty, if this is a narrow revision.
4. A separate directory for evidence.

Ask for observable findings with timestamps and a small set of prioritized changes. Do not tell it which result to approve. Keep its input artifact unchanged during review. A reviewing agent can assess composition and visible motion; do not imply it heard audio unless it actually had that capability and did so.

If the sole change was removing an incorrect reflection, recheck that interval. Do not reopen every earlier accepted decision. If the user says motion is good but the frame feels sparse, review hierarchy and spatial relationships before inventing a new animation system.

## Sound evidence

Measure both integrated loudness and true peak after AAC encoding. A waveform or spectrogram can locate cues but cannot establish musical taste. Timing comparison against a reference WAV can reveal mux delay; a correct duration alone cannot.

Use a human or audio-capable reviewer when available. Otherwise state that sound was measured but not listened to; let the user audition it. Never call a score “listening-reviewed” based only on RMS or a transcript.

## Delivery record

Keep the final MP4, poster, source/rebuild command, technical JSON, and the few images that explain meaningful review findings. Record rejected tricks when they teach a transferable decision. Remove duplicate temporary renders and browser profiles owned by the task. Preserve prior user-delivered versions.
