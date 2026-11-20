# Mixed 2D and three.js example

Seven seconds at 120 BPM: a 2D panel, the same panel on a three.js monitor that pulls back to reveal a desk, a reaction shot of a small character, and a 2D end card. It is a working reference for the scene contract in `references/three-d.md`, not a finished brand film.

```sh
python3 examples/desk/create.py /path/to/desk-example
cd /path/to/desk-example
node render.mjs render --out out/desk.mp4 --samples 16
python3 verify.py out/desk.mp4
```

What to read in `scenes.js`:

- `panel()` draws the UI once; the 2D shot and the monitor's texture both call it, so the cut into 3D is a match cut. The screen close-up starts from `frameRect()` at exposure 1 without the highlight shoulder, and the decoded frames on either side of that cut differ by less than half a code value on the paper, card and accent colors.
- `screen` and `react` are two framings of one set: both library entries name the same `desk` setup, so it is built once.
- `HOPS` is the character's timeline. Position, squash and stretch derive from it; `score.js` reads the same table for the take-off and landing sounds.
- `YAW` and `BLINK` are keyframe channels. The reaction shot uses `reactRig()`, a shallow aperture on the face and `shoulder: true` for the lamp-lit room.
- The rig sets `near`/`far` for the wide shot. With the default 0.1–1000 range the screen and its bezel, 0.01 units apart, z-fought at 120 units away.
