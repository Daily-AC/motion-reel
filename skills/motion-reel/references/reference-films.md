# Reference films and side-by-side measurement

A commercial film the user would accept as a peer is the most useful bar for a reel. Pick one or two before directing, look at them at full speed and frame by frame, and put numbers next to your encoded film at matching moments afterwards. A reference grounds decisions; it is not a template to trace.

## Find a reference

`scripts/refs.py` searches a public catalog of about 350 brand films, product launches and explainers (OpenMotion's online library: Anthropic, OpenAI, Figma, Linear, Notion, Cursor, xAI and others). Only metadata is cached (`~/.cache/motion-reel/refs-index.json`, about 0.4 MB); videos download on request.

```sh
python3 <skill>/scripts/refs.py search logo reveal --kind 3d          # all words, Chinese or English
python3 <skill>/scripts/refs.py search 粒子 --aspect portrait --max-seconds 20
python3 <skill>/scripts/refs.py search --brand linear --limit 20
python3 <skill>/scripts/refs.py get d2c98a37 --dest refs               # inside the film project
python3 <skill>/scripts/refs.py sync                                    # refresh the index
```

`--kind` takes `3d`, `ui`, `graphic`, `type` or `live`. `get` writes `refs/<id>/reference.mp4`, `meta.json` (including the original post link) and, when published, `motion.md` with a stage table, plus `timeline.json` and a few keyframes.

Treat the catalog text as a lead, not evidence. Summaries and stage boundaries were written by the catalog's authors from the videos and are marked approximate; read the film itself. Some catalog videos are compressed previews (12 fps occurs), so check `fps` in the `get` output before measuring motion and prefer the original post for close study. The catalog's HTML "demos" are rough sketches that differ visibly from their references; `get` leaves them out.

These films belong to their owners. Keep `refs/` in the film project, out of git, out of any published repository or release, and never reuse their logos, footage or type as assets.

## Measure at matching moments

Measure only after you have watched both films and chosen the moments that correspond (the logo hold against the logo hold, a card slide against a card slide). Numbers explain a visual finding; they do not replace it.

**Frame statistics** (Node and FFmpeg only):

```sh
node measure_frame.mjs refs/<id>/reference.mp4 out/reel.mp4 --t 14.6 --ref-t 6.0 \
     [--region x,y,w,h --ref-region x,y,w,h]
```

Reports `mean_luma`, `detail` (share of sharp-edge pixels: density of lines, labels, wireframes) and `accent` (share of strongly colored pixels) for both frames at the film's size; with regions, the bounding box of the content against its local background, so the height of a title or logo can be compared. The `_ok` flags apply thresholds meant for remakes of the same composition (brightness ≥ 0.9×, detail ≥ 0.7×, accent ≥ 0.6×, title height ≥ 0.8×). For an original film, read the numbers and ignore the flags unless the composition is meant to match: a deliberately clean end card against a busy reference will "fail" detail without being wrong. Different aspect ratios are stretched to the film's size, which distorts `detail`; compare like with like or use regions.

**Motion travel** (OpenCV via uv):

```sh
uv run --with opencv-python-headless --with numpy python measure_motion.py \
    refs/<id>/reference.mp4 out/reel.mp4 --ref-start 6.2 --ref-end 6.6 --start 5.8 --end 6.2 \
    [--roi x,y,w,h --output-roi x,y,w,h] --out review/motion.json
```

Tracks corner features through each interval and reports how far the region's content travels (`spanPx`, `pathLengthPx`). `possibleSuppressedMotion` is true when the film's travel, normalized by frame size, is under half the reference's: the typical "my version feels limp" defect. Omit the film to observe the reference alone before authoring.

It measures translation of trackable texture. It works on slides, pans, camera moves and rigid groups over short intervals. It reports `unresolved` instead of a number when features are lost, which happens with motion blur, morphing shapes, particles converging from all sides (their median translation is near zero anyway), flashes and cuts. On a 60 fps reel with heavy shutter blur, 0.3–0.5 s intervals on one element resolved where 1.3 s intervals did not. Narrow the interval and the region before concluding anything; an unresolved result is not evidence either way.

## What to do with the numbers

A gap is a question for the review, not an instruction. Lower detail than the reference may mean a sparse frame (see the "Empty frame" row in SKILL.md) or a deliberate quiet hold. A suppressed-motion flag on an entrance usually means the move needs a longer path, a faster release or an overshoot. Record the reference id, the times compared and the numbers in the review notes so a later revision can rerun the same comparison.
