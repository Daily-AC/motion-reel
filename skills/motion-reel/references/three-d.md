# three.js scenes

Use a three.js scene when a shot needs real volume: a character performing, a lit set with shadows, a camera moving through space, depth of field, a product turning under light. Keep Canvas2D for type, flat graphics and diagrams. Both kinds mix freely in one film and share everything else: the shot list and timeline, `HITS` (shake and chromatic aberration), frame-center cut selection, shutter sampling, post, capture, sound and verification. A working mixed film, the desk example, is in the source repository at https://github.com/Daily-AC/motion-reel/tree/main/examples/desk; its `scenes.js` shows every part of this page.

## The contract

```js
async function desk(THREE, renderer) {          // once, after fonts and prepare(); may await loads and imports
  renderer.shadowMap.enabled = true;            // renderer settings are shared by every three.js scene in the film
  const scene = new THREE.Scene(); scene.background = new THREE.Color(INK);
  // ... build meshes, lights, canvas textures
  return {
    scene,
    rig(u, t, shot) { return { position, target, fov, focus, aperture, exposure, shoulder, vw, near, far, up }; },
    update(u, t, shot, sample, camera) { /* every subframe: pose everything from time, jitter the key light */ },
    frame(u, t, shot) { /* optional, once per frame at its center time: redraw screen textures and numbers */ },
    overlay(g, u, t, shot) { /* optional 2D drawn over the shot once per frame, after tone mapping */ },
  };
}
const SCENE_LIBRARY = { title: { draw: title, beats: 4 }, screen: { three: desk, beats: 2 }, react: { three: desk, beats: 4 } };
```

A library entry has `draw` (Canvas2D) or `three` (setup), never both. Entries that name the same setup function share one set, so two framings of a set can have different native lengths. `u`, `t` and `shot` mean what they mean for 2D scenes; `THREE` is also available as a global after setup. Modules can be split out and loaded with `await import('./src/stage.js')`: the page's import map resolves `three` to the vendored build in `vendor/three/`, so every module sees the same instance. To use an addon, copy its file from the same three.js release into `vendor/three/addons/` and import `three/addons/...`.

The engine loads three.js only when a shot uses it; a 2D-only film is unaffected.

### What happens to each frame

1. `shotAt(frameCenter)` picks the shot. Every subframe of the frame belongs to it.
2. `frame()` runs once. The rig at the frame center supplies `exposure` and `shoulder`.
3. For each of N subframes: shutter time `t` (180°, as in 2D), the rig at `t`, a `sample` = `{index, count, jitter, lens, light}`, impact shake from `HITS`. The engine aims the camera (below), calls `update()`, renders the scene into a half-float target and adds `1/N` of its linear radiance to the same RGBA16F accumulator Canvas2D shots use.
4. Post: chromatic aberration from `HITS`, `× exposure`, optional highlight shoulder, sRGB encode, the overlay (HUD and `overlay()`), vignette, grain.

One loop therefore jitters four things at once: shutter time (motion blur), the lens sample (depth of field), the subpixel offset (antialiasing) and the light sample (soft shadows). `sample.lens` and `sample.light` are points in the unit disk, permuted so they do not follow shutter time and centered so their average is the pinhole, point-light frame. With `count = 1` all are zero.

## The rig: one lens per shot

`rig(u, t, shot)` returns the shot's lens as data. Branch on `shot.scene` or `shot.copy` to give each shot its own framing.

| Field | Meaning |
|---|---|
| `position`, `target`, `up` | Camera and look-at point; `up` defaults to `[0,1,0]`. |
| `fov` | Vertical field of view, in degrees, of a 16:9 frame. |
| `focus` | Point in focus (default `target`). The focus plane is perpendicular to the view at its depth. |
| `aperture` | Lens radius in scene units (default 0, pinhole). A point at depth z, focused at d, blurs over a circle of radius `aperture · |1/z − 1/d| · (H/2)/tan(fov/2)` pixels. |
| `exposure` | Multiplies linear radiance before encoding (default 1). |
| `shoulder` | `true` rolls highlights off with Khronos PBR Neutral's shoulder (no toe): linear values below 0.76 pass unchanged. Default clips like a 2D shot. |
| `vw` | On a canvas narrower than 16:9, the share of the 16:9 width the shot keeps (default 0.62); the frame grows taller instead. |
| `near`, `far` | Depth range (default 0.1–1000). Tighten it for wide shots of close surfaces. |

Helpers for common framings:

- `frameRect(center, normal, width, fov)`: a screen close-up. The rectangle `width` wide fills the frame width, straight on; it returns `vw: 1` so a portrait cut keeps whole lines of text.
- `reactRig(subject, facing, angle, dist, height, fov)`: a reaction shot from `angle` radians off the direction the subject faces (yaw, 0 = +z), `dist` away and `height` up, aimed and focused at the subject.

Spread them and override: `{ ...frameRect(c, n, 48), exposure: 1, near: 5 }`. Interpolate two rigs field by field for pushes and pull-backs. A shot can follow a moving subject because the rig receives time.

Aim apertures by scale: in a scene measured in centimeters, around 0.3–0.6 for a character close-up and 0.05–0.1 for a screen close-up worked in delivered films. Large apertures with few samples show the discrete copies; raise samples before judging the blur.

## Light and shadow

Move the key light by `sample.light × radius` in `update()`; the average of N shadow maps is a soft shadow with a penumbra set by the radius. Keep the pattern fixed per subframe index: a pattern re-randomized every frame makes bokeh and penumbrae boil at the frame rate, and the encoder spends its bitrate on that noise.

Physically based lights in three.js use physical units (candela for spot and point lights, inverse-square falloff). In a scene built in centimeters a desk lamp needs tens of thousands; tune by looking at an exposure-1 still, not by raising `exposure` to hide a dim set.

## Exposure, highlights and designed colors

Three.js output is linear radiance, so lights can exceed 1. By default the post clips at 1 like a Canvas2D shot, which keeps designed colors exact: a solid `#0050FF` background renders as `0,80,255`. Set `shoulder: true` for lit sets with hot highlights (emissive cores, lamps, speculars); it compresses only the top of the range, but it also shifts bright design colors (pure blue came out `33,82,241`). Give a screen close-up its own `exposure: 1` without the shoulder so its UI matches the design; give the room shots their own exposure. In the desk example the frames either side of a 2D-to-3D match cut differ by under half a code value on the paper, card and accent colors.

The engine does not add bloom. Bloom on emitters is a large part of some 3D looks: in a measured port it accounted for about a fifth of the mean brightness (see docs/validation.md).

## Screens and interfaces as textures

Draw the interface on a 2D canvas and map it onto the screen mesh with an unlit material: `new THREE.CanvasTexture(canvas)` with `colorSpace = THREE.SRGBColorSpace`, redrawn in `frame()` and flagged `needsUpdate`. Size the canvas at its design size × `SCALE` so a 4K close-up stays sharp, and keep layout coordinates fixed with `g.setTransform(SCALE, 0, 0, SCALE, 0, 0)`. Draw it with the same function a 2D shot uses and the cut between them can be a match cut.

When the screen shows a real tool (a terminal, a CLI, an editor), capture its actual output instead of drawing it from memory: run the program in a pseudo-terminal and replay the ANSI stream through a terminal emulator library such as pyte to get the real glyphs, colors, prompts and spacing. Remembered UIs get symbols and formatting wrong in ways viewers who use the tool notice.

## Timeline as data

Write the performance as tables, not per-frame code paths:

- **Position from displacements.** A character's path is a list of moves (hop, land, walk) with start time, distance, height and duration. Position at `u` is the sum of completed moves plus the fraction of the current one.
- **Squash and stretch derived from the moves.** Anticipation squash before take-off, stretch with vertical speed, a damped squash after landing, area-preserving (`sx = sz = 1/√sy`). Make the landing response start from the in-air value: a jump from stretched to squashed inside one shutter interval renders as two ghost copies.
- **Keyframe channels** for orientation, limbs and eyes: `[[u, value], ...]` pairs eased between keys.
- **The same event table feeds the score.** Take-offs and landings become sound cues in `score.js` (`react.start + h.u / react.rate`), so a timing change moves picture and sound together.

## Readable performance

Independent review of delivered character films kept finding the same problems; each fix below was confirmed by a recheck.

- A waving arm must stay outside the body silhouette. Move the pivot outward as it rises, sweep a wide arc and hold the wave for at least a second, or it reads as a twitch.
- Short hops: 0.15–0.25 s in the air, with grounded time between hops. Long, high airtime reads as floating.
- Show the cause before the reaction: cut to what happened (the screen, the object) and then to the face, and give the reaction at least a second.
- Contacts must touch. If the rig cannot reach, change the action (a head bump instead of a high five) and mark the contact with a small spark.
- Hold a key line until it is fully shown and readable, about 1.2 s or more.
- Separate figure from ground: a character in front of a background of its own color loses its outline.
- Two characters facing each other: cheat their bodies 35–40° toward the camera so profile limbs do not read as noses.
- Judge motion from 15–20 fps strips (`review.py --strip`). A 4 fps contact sheet hides floating and twitching.

## Vertical without a new storyboard

Compose 3D shots for 16:9. On a portrait canvas each shot keeps `vw` of the landscape width and extends height: `tan(fov'/2) = vw · tan(fov/2) · (16/9) / aspect`. Screen close-ups use `vw: 1` so whole lines stay in frame; character shots work around 0.6–0.8. Lower the look target a little for subjects near the floor so they sit mid-frame, clear of a feed's caption zone. Canvas2D shots and overlays still need their own portrait layouts; read [feed-publishing.md](feed-publishing.md).

## Cuts

Selecting the shot per subframe instead of per frame would let the second half of the shutter fall into the next shot, and the first frame after every cut would carry a ghost of the previous one. The engine selects by frame center for both kinds; keep any custom per-shot state keyed the same way. Clamp negative local time near a cut (the engine already clamps `u`).

## Checks

- Same frame at `--samples 1`, `4` and `16`: mean brightness must agree within about 1%. More samples getting darker or brighter means accumulation is broken; a common cause is a render pass that clears the accumulation target between subframes (three.js's `autoClear` does exactly that if you accumulate inside three.js yourself). In one delivered film this bug was hidden for a while by raising exposure, and depth of field and motion blur had never actually rendered.
- Make the effect conspicuous once (large aperture, fast move) and look at a decoded frame, then dial it back.
- The source repository's `tests/check_bundle.py` holds known-answer tests for this path: brightness at 1/4/16 samples, motion-blur length against speed × shutter, depth of field by Laplacian variance, and 2D/3D cuts that never blend in the encoded film.

## Pitfalls

- Set every time-dependent property in `update()` from `t`. Heavy deterministic precomputation in setup (a physics table) is fine; integrating from the previous frame is not.
- Depth precision: with `near` 0.1 a screen 0.01 units in front of its bezel z-fought at 120 units away. Set `near`/`far` per rig, or separate coplanar surfaces.
- Renderer settings such as `shadowMap.enabled` are shared by all three.js scenes in a film; set them consistently.
- 2D overlays on a 3D shot are drawn once per frame at the frame-center time, without motion blur. Animate them gently, or move fast type into a 2D shot.

Measured speed (Apple Silicon Mac, Chrome on Metal): the 7 s mixed example at 1080p and 16 samples rendered in 11 s; a set with 24,000 instanced spheres, shadows and reflections at 24 samples took about 117 ms per frame.
