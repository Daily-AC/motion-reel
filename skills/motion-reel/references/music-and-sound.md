# Music and sound

## Contents
- Choose the sound source
- Lock the film to a track
- Place sound effects
- Prove the sound without hearing it

## Choose the sound source

`project.json` → `sound` combines up to three sources:

- `synth: true` — the template's offline score. Picture and sound come from one grid, so hits land exactly and nothing needs a license. It is generic electronic sound; agents cannot judge whether it fits.
- `music` — one licensed track: a file the user supplies, or a track whose license covers the destination. Record where it came from and its license. Free stock libraries differ: Mixkit's music license, for example, allows web and social video but not TV/radio broadcast, games or CD/DVD. Read the live license page; a license does not stop a platform's copyright matcher from flagging a well-known track.
- `library` + per-shot `sfx` — sound-effect files, one per cut or big move.

Default to the synthesized score when the brief says nothing about music. When the brief asks for real music and none is supplied, choose a free-license track whose terms cover the destination, and state the choice and its license in the delivery. Ask only when the destination's licensing is unclear.

Never copy third-party music or sound-effect files into this toolkit or a public repository. Pixabay and Mixkit terms forbid redistributing their files as standalone assets; using them inside a rendered film is the permitted use. Keep them in the film project, which is not published with the toolkit.

## Lock the film to a track

```sh
cp ~/Downloads/track.mp3 audio/track.mp3
uv run --with librosa --with matplotlib python beats.py audio/track.mp3
```

`beats.py` decodes with FFmpeg (the renderer's decoder, so analysis and mix share one timebase), runs librosa's beat tracker, then re-measures the grid against the track's kicks. It picks attacks from the <120 Hz band, times each by the broadband attack just before it, and solves tempo and phase directly from those attacks. It prints the tempo, the kick-to-grid error of librosa's beats versus the final grid, warnings, and candidate start points (the loudest windows and the strongest rises) that fit the film's beat count.

Open `review/beats.png` before trusting the numbers. Each panel is the <120 Hz waveform and envelope. Green lines are the final grid (thick = beat one), red dashed lines are librosa's beats, black triangles are detected attacks. Green lines should sit at the start of the kick blobs. When they do not:

| Plot shows | Rerun with |
|---|---|
| Grid on the bass or snare, kicks between the lines | `--anchor <track time of a kick on beat one>` |
| Kicks on every other line, track feels twice as fast | `--double` |
| Kicks twice per grid step | `--halve` |
| Beat one on the wrong beat of the bar | `--anchor <time of beat one>` |

Then lock the film:

```sh
uv run --with librosa --with matplotlib python beats.py audio/track.mp3 --start 88.18 --apply
```

`--apply` snaps the start to the nearest beat one, writes the measured `bpm` (kept unrounded) and `sound.music` with `start`, `gain`, `fadeOut`, and turns `synth` off so its drums do not fight the track. It sets `sceneBpm` to the previous tempo, so the scenes keep their choreography and stretch to the track's tempo. Fill `sound.music.source` and `license`; `build.py` refuses unledgered audio. A track must cover `start + duration`.

Why not trust librosa's beats directly: on 20 synthetic 60 s tracks with known kicks (four-on-the-floor, loud off-beat hats and bass, bass as loud as the kick, half-time kicks; 96–140 BPM), raw librosa beats had a median error of 23–288 ms, because its tempo is quantized by its analysis hop (up to 2.6% off here) and it can lock onto the off-beat. Refitting librosa's beats to a constant tempo keeps that tempo error; the refit grid's median error was 84–152 ms whenever the tempo was off. The kick-locked grid had a median error of 0.3 ms on 19 of 20 tracks; the 20th was a half-time pattern read at half tempo, also 0.3 ms after `--double`. On the template's dense synthesized score it was 28 ms. On a real 130 BPM house track, a film cut on librosa's grid had sound leading the picture by 33 ms at the first cut and 139 ms at the last; the kick-locked film stayed within 20 ms. Known limits: syncopated hip-hop kicks and beatless ambient tracks need `--anchor` or have no kick grid at all (the script warns); half-time kick patterns can read as half tempo (it warns below 75 BPM).

## Place sound effects

```json
"sound": {"synth": false, "music": {...},
  "library": {"whoosh": {"file": "sfx/whoosh.mp3", "source": "...", "license": "..."}}},
"shots": [{"scene": "build", "beats": 4, "sfx": [{"name": "whoosh", "gain": -8}, {"name": "pop", "beat": 1.5, "gain": -10}]}]
```

A cue lands at its shot's start plus `beat` beats. By default (`"align": "peak"`) the file's loudest moment lands on the cue, so a whoosh swells into the cut and an impact hits on it; `"align": "start"` places the file's first sample there instead. Use the project's existing effects first; whoosh for movement, pop for something appearing, click for a click, typing for typing, an impact for a landing. Effects sit above the music but not on every beat. Under a mastered track, start around −8 dB for whooshes, −6 to −4 dB for impacts and −10 dB for small pops, then check the loudest moments in `verify.py`'s report.

The mixer has no voice-over ducking. A narrated film needs a separate mixing step in which the voice is loudest and the music drops under it.

## Prove the sound without hearing it

Agents cannot hear. Measure the delivered MP4, then hand a person exact timestamps:

- `verify.py` measures integrated loudness and true peak on the encoded AAC (target about −14 LUFS, at most −1 dBTP), and mono fold-down: `loss_db` (0 for identical channels, about 3 for uncorrelated, more for cancellation) plus 400 ms L/R correlation windows. A phone speaker or a mono Bluetooth speaker plays the fold-down.
- For every cut it finds the actual picture change and the steepest <120 Hz onset near it, and reports `offset_ms` (positive = sound first). It errors when sound leads picture by more than 45 ms or trails by more than 125 ms (ITU-R BT.1359 detectability). A cut without a low-band hit is reported as `no_onset`, not as an error. A cue where no picture changes (a shot boundary inside one continuous move) is reported as `no_picture_change` and not checked: there is nothing for the sound to land on.
- `audio_gates.py` finds drones the loudness checks cannot hear: `uv run --with numpy --with scipy python audio_gates.py out/reel.mp4`. It fails a single pitch in 150–400 Hz held longer than 20 s (or 60% of the film), and a pitch in 40–150 Hz held longer than 8 s within 10 dB of the loudest component (a repeated note counts as held). It also prints each shot's share of power in four bands and flags 60–250 Hz above 70%. Run it on synthesized scores and licensed tracks alike. Calibration, on three scores only, so the thresholds are provisional: a rejected score held D4 for its whole 30.7 s and D2 for 14.3 s (its owner heard "low, harsh noise"); the same score without its sub oscillator still held D4 for 30.7 s and D3 for 10.3 s (heard as "a low drone under the whole film"); an accepted lo-fi jazz score peaked at 17.9 s on F#4 and 7.5 s on E2. A check that every 12 s contains a 0.4 s rest did not separate them (the accepted score failed it) and is not a gate.
- It names five listening timestamps: the loudest moment, the worst mono window, the cut with the largest offset, the opening second and the ending. Give these to the user; never describe the sound as good.
- `review.py --cues` draws, for every cut and effect, the frame before, the frame after and the waveform (full band and <120 Hz) around the cue.
