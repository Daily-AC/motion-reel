# From a brief to a coherent reel

## Make an argument with motion

Write one sentence about the viewer's change of understanding. Then assign behavior to it. A developer tool might turn one prompt into structure and then a usable artifact; an audio product might turn a vibration into a material surface. A generic showcase can be an exploration of form, but still needs a progression.

For each proposed shot, record: focal object, its action, the reason for that action, camera behavior, sound cue, and the outgoing handoff. Remove shots that merely repeat a capability word without adding visual information. Do not add a dashboard because the subject is software if a transformation communicates more clearly.

The included eight-shot example is a vocabulary demonstration: an identity object, variable typography, a deforming ribbon, particles, an extruded word, interface planes, elastic type and a closing lockup. Reuse its mechanisms; invent the appropriate progression for the new subject.

## Choreograph inside the shot

An entrance followed by a static hold is still mostly a static slide. Use a legible action with preparation, release and response. Preparation can be brief: a contraction before an explosion, a camera hesitation before a plunge, or a stretched spring before its return. Give the released energy somewhere to go.

Vary motion grammar. Useful contrasts include rigid versus elastic, orbital versus linear, clustered versus dispersed, front view versus oblique volume, and dense movement versus a stable identity hold. Avoid applying the same ease-out tween to every object.

Give each shot one or two craft details that show the hand of a motion designer: a spring curve with visible overshoot, area-preserving squash and stretch, onion-skin trails, an animator's spacing dots, selection handles on a shape, glyph metrics drawn beside type. More than two per shot compete with the action.

Plan at least one meaningful change of viewing scale when the brief wants impact. A camera can enter a letter counter, reveal a structure from a close-up, or pass through a particle field. The endpoint must be recognizable; motion blur cannot rescue an unreadable action.

## Build the film on the beat grid

Derive the duration from tempo and bars rather than picking seconds: 128 BPM × 8 bars is exactly 15 s. A useful default is one shot per bar, cut on the downbeat, with in-shot events on beats, half-beats or sixteenths. The shot list's `beats` field encodes this; a licensed track supplies its own grid (music-and-sound.md).

## Open finished, close on the opening

Frame 0 is a finished picture: it is the poster in a feed and the first impression everywhere else. Do not grow it from black or type it on at the very start; begin from a complete state and move from there, for example pulling back from a close-up. Have sound at frame 0 too. Let the opening element pay off at the end (a ball knocked away in the first shot returns to become the logo), which is what viewers remember.

## Treat cuts as relationships

Hand every cut over through one element: a line that opens into the next frame, a camera that flies into a letter's counter, an array that floods the frame, particles that settle into a grid. The element can be as plain as a shared position or color across a hard cut; a pause on empty black carries nothing.

A cut can be a change in material rather than a change in subject: outline to ribbon, ribbon samples to particles, particles to solid blocks. Share the points and camera at the boundary whenever practical. Similar silhouettes created independently tend to jump.

Specify the incoming and outgoing screen position, extent, orientation and background. Inspect the encoded frames on both sides. A wipe that becomes opaque early creates a pause even if each isolated shot looks correct. Reveal enough of the next object before a portal closes to prevent a blank beat when that serves the shot.

Hard cuts are valid. Do not force a complicated morph onto every transition. Maintain enough visual or rhythmic information for the viewer to follow the film.

## Add density where it has a cause

Build a hierarchy: one focal action; a supporting spatial layer; optional foreground interaction. Let extra layers respond to the focal object through movement, light, occlusion or shared geometry.

| Sparse situation | Motivated addition | Common failure |
|---|---|---|
| A floating identity object | A light pool, orbital path, a few related pieces | Random stars, identical orbit rings, decorative UI ticks |
| A sculptural loop on black | A farther wire echo, light visible through its opening | A competing second hero or broad undirected glow |
| An extruded word with no setting | Construction plane, subtle grid, small joining blocks | A rigid text reflection while the subject deforms |
| White cards on white | Soft shadows, a visible back edge, a connecting path | More cards until none can be read |
| A dense particle burst | A clear target and a quieter recovery | Adding further texture to an already saturated shot |

Keep some negative space. Typography needs room to establish scale; the closing mark needs a recognition hold. The target is a deliberate density rhythm, not equal occupancy in every frame.

## Give the film one identity

Derive colors and shape language from verified brand assets when present. Use one accent color. When a brand's logo appears, switch the whole film's palette to the brand's: a correct logo pasted into an unrelated palette can still feel unofficial. Use a small material family: for example porcelain faces, blue-lit edges and a dark reflective setting. Use local, licensed fonts with appropriate weights; test actual strings and scripts.

Use one recurring motif to link scenes: a line, orbit, aperture, shard, light or tone. Its role may evolve. It should carry attention or meaning, not merely recur as a watermark.

Preserve a logo's outline and negative space when making it 3D. Sample an actual vector or use the provided asset as a texture; do not redraw a famous mark from memory. Depth, bevel, light and rotation can be creative without changing identity.

## Use randomness as an ideation tool

`creative_seed.py` groups a string, combines neighboring fragments and hashes them into a small form/action vocabulary. A fragment such as “orbit × illuminate” can suggest a moving highlight; “thread × gather” can suggest a line resolving under the final mark.

Generate alternatives, choose a few, and describe their visible jobs. Reject associations that do not serve the brief. Never animate the seed itself simply because it exists, unless randomness is the film's actual subject. Keep the chosen seed so the exercise can be reproduced; all production motion must still be deterministic.

## Sound is part of the choreography

Use a shared event table for the important impacts. A recurring three-note motif can return in different timbres while the visual motif changes material. Leave space before a major arrival. A full-volume hit on every beat makes the climax less distinct.

Use the supplied instruments as primitives, not a mandatory genre. A film may need restrained sound design, licensed music, recorded audio, or silence. Honor the brief, licensing and the user's spending authorization.
