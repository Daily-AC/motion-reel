#!/usr/bin/env python3
"""Find the drones verify.py cannot hear: a pitch that never stops, a bass note that hangs.

  uv run --with numpy --with scipy python audio_gates.py out/reel.mp4

Gates (each was calibrated on a rejected and an accepted score; see references/music-and-sound.md):
  held pitch 150-400 Hz  no single pitch held longer than 20 s, or longer than 60% of the film
  held pitch 40-150 Hz   no single pitch held longer than 8 s at 10 dB or less under the loudest component
Per shot (from timeline.json next to the video's project, if present) it also prints the share of power in 20-60, 60-250,
250-2k and 2k+ Hz and flags 60-250 Hz above 70%. A pitch counts as held while a spectral peak stays on the same semitone,
standing 10 dB above its neighbours and no more than 30 dB under the frame's loudest component; gaps under 0.5 s are joined,
so a repeated note counts as held. Nothing here listens: passing is not the same as sounding good.
"""
from pathlib import Path
import argparse, json, math, subprocess, sys
try:
    import numpy as np
    from scipy import signal
except ImportError:
    raise SystemExit('Requires NumPy and SciPy: uv run --with numpy --with scipy python audio_gates.py ...')

SR = 22050
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def decode(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-vn', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def held_pitch(x, lo, hi, gap=0.5):
    """Longest run of one semitone among the spectral peaks in [lo, hi] Hz: seconds, note, start, median level vs the frame's loudest."""
    nper, hop = 16384, 2205
    f, t, Z = signal.stft(x, fs=SR, nperseg=nper, noverlap=nper - hop, boundary=None)
    D = 10 * np.log10(np.abs(Z) ** 2 + 1e-20)
    band = np.where((f >= lo) & (f <= hi))[0]
    frame_max = D.max(axis=0); floor = frame_max.max() - 60          # near-silent frames do not count
    active, levels = {}, {}
    for j in range(D.shape[1]):
        if frame_max[j] < floor: continue
        seg = D[band, j]
        for p in signal.find_peaks(seg, prominence=10)[0]:
            lvl = seg[p] - frame_max[j]
            if lvl < -30: continue
            midi = int(round(69 + 12 * math.log2(f[band[p]] / 440.0)))
            active.setdefault(midi, []).append(j); levels.setdefault(midi, []).append(lvl)
    dt = hop / SR; join = int(round(gap / dt)) + 1
    best = {'seconds': 0.0, 'note': None, 'start': None, 'rel_db': None}
    for midi, frames in active.items():
        fr = sorted(set(frames)); a = prev = fr[0]
        for k in fr[1:] + [None]:
            if k is not None and k - prev <= join: prev = k; continue
            secs = (prev - a + 1) * dt
            if secs > best['seconds']:
                best = {'seconds': round(secs, 1), 'note': NOTES[midi % 12] + str(midi // 12 - 1), 'start': round(float(t[a]), 1), 'rel_db': round(float(np.median(levels[midi])), 1)}
            if k is not None: a = prev = k
    return best


def balance(x, spans):
    f, t, Z = signal.stft(x, fs=SR, nperseg=4096, noverlap=3072, boundary=None); P = np.abs(Z) ** 2
    rows = []
    for name, a, b in spans:
        m = (t >= a) & (t < b); tot = P[f >= 20][:, m].sum()
        if tot <= 0: continue
        share = [round(100 * float(P[(f >= lo) & (f < hi)][:, m].sum() / tot), 1) for lo, hi in [(20, 60), (60, 250), (250, 2000), (2000, SR / 2)]]
        rows.append({'shot': name, 'start': a, 'end': b, '20-60': share[0], '60-250': share[1], '250-2k': share[2], '2k+': share[3], 'flag': share[1] > 70})
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('media', type=Path); p.add_argument('--timeline', type=Path, help='default: timeline.json in the project (the parent of out/)')
    a = p.parse_args()
    x = decode(a.media); dur = len(x) / SR
    mid, low = held_pitch(x, 150.0, 400.0), held_pitch(x, 40.0, 150.0)
    gates = [
        ('held pitch 150-400 Hz', mid['seconds'] <= 20 and mid['seconds'] <= 0.6 * dur, f"longest {mid['seconds']} s {mid['note']} from {mid['start']} s ({mid['rel_db']} dB under the loudest)"),
        ('held pitch 40-150 Hz', not (low['seconds'] > 8 and (low['rel_db'] if low['rel_db'] is not None else -99) > -10), f"longest {low['seconds']} s {low['note']} from {low['start']} s ({low['rel_db']} dB under the loudest)"),
    ]
    for name, ok, detail in gates: print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    tl = a.timeline or a.media.resolve().parent.parent / 'timeline.json'
    if tl.exists():
        shots = json.loads(tl.read_text()).get('shots', [])
        rows = balance(x, [(s.get('scene', s.get('id', '?')), float(s['start']), float(s['end'])) for s in shots if 'start' in s and 'end' in s])
        for r in rows: print(f"       {r['shot']:10s} {r['start']:6.2f}-{r['end']:6.2f} s  20-60 {r['20-60']:4.1f}%  60-250 {r['60-250']:4.1f}%  250-2k {r['250-2k']:4.1f}%  2k+ {r['2k+']:4.1f}%" + ('   <- 60-250 Hz above 70%' if r['flag'] else ''))
    print('Nobody has listened. These gates find drones; they cannot tell whether the score fits.')
    sys.exit(0 if all(ok for _, ok, _ in gates) else 1)


if __name__ == '__main__':
    main()
