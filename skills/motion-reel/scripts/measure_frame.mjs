#!/usr/bin/env node
// Adapted from OpenMotion (github.com/nexu-io/openmotion, skills/openmotion-recreate/scripts/measure_frame.mjs
// at 2ca4b97), Apache License 2.0, see APACHE-2.0.txt. Changes: "remix" renamed "film", FFmpeg found
// through FFMPEG_PATH/FFPROBE_PATH or PATH instead of OpenMotion's bundled runtime, remake thresholds
// (the _ok flags) printed only with --remake, and a --pairs batch mode.
// Compare a reference frame and a film frame with numbers.
//
// Both frames are scaled to the same size so pixel values compare directly.
//
// Whole frame (always reported):
//   mean_luma   average brightness 0-255
//   detail      share of pixels on a sharp edge (lines, labels, wireframes);
//               a lower value means a sparser or blurrier picture
//   accent      share of strongly coloured pixels (brand-colour lines, fills)
//
// Region (with --region): the box around the content that differs from the
// region's background, whichever is lighter or darker. For one line of text its
// height is roughly the cap/ascender height; for a logo it is the logo height.
// A box that touches the region edge usually means the region is too small or
// the content is clipped; touching the frame edge means it is cut off.
//
// With --remake, the _ok flags apply thresholds for a remake of the same composition
// (brightness >= 0.9x, detail >= 0.7x, accent >= 0.6x, region height >= 0.8x).
//
// Usage:
//   node measure_frame.mjs REF FILM --t 12.0 [--ref-t 12.4]
//   node measure_frame.mjs REF FILM --frame 360 [--ref-frame 372]
//        [--region x,y,w,h] [--ref-region x,y,w,h]
//        [--size 1920x1080] [--threshold 60] [--remake]
//   node measure_frame.mjs REF FILM --pairs moments.json [--size ...] [--threshold ...] [--remake]
// A pairs file is a JSON list; each entry takes the per-moment options above as keys
// ("t" or "frame", "ref-t" or "ref-frame", "region", "ref-region") plus an optional
// "label", and the output is a list with one result per entry.
// Times are in seconds; regions are in pixels of --size (default: film size).
// Frame indices are zero-based decoded video frames. Use them for short events
// whose exact frame could be skipped by a rounded seek time.
// ffmpeg/ffprobe: FFMPEG_PATH / FFPROBE_PATH when set, then PATH. No npm dependencies.
import { spawnSync } from 'node:child_process';
import { parseArgs } from 'node:util';
import { readFileSync } from 'node:fs';

const ffmpeg = process.env.FFMPEG_PATH || 'ffmpeg';
const ffprobe = process.env.FFPROBE_PATH || 'ffprobe';

function fail(message) {
  console.error(message);
  process.exit(1);
}

function run(command, args) {
  const result = spawnSync(command, args, { maxBuffer: 1 << 30 });
  if (result.error?.code === 'ENOENT') fail(`${command} not found: install FFmpeg or set FFMPEG_PATH/FFPROBE_PATH`);
  if (result.error) fail(`${command}: ${result.error.message}`);
  if (result.status !== 0) fail(`${command} failed: ${result.stderr.toString().trim()}`);
  return result.stdout;
}

function probeSize(file) {
  const line = run(ffprobe, ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', file])
    .toString().trim().split(/\r?\n/)[0];
  const [w, h] = line.split(',').map(Number);
  return [w, h];
}

function rgbFrame(file, selection, w, h) {
  const indexed = selection.frame !== undefined;
  const seek = indexed ? [] : ['-ss', String(selection.time)];
  const select = indexed ? `select=eq(n\\,${selection.frame}),` : '';
  const raw = run(ffmpeg, ['-v', 'error', ...seek, '-i', file, '-frames:v', '1',
    '-vf', `${select}scale=${w}:${h}:flags=area,format=rgb24`,
    ...(indexed ? ['-fps_mode', 'passthrough'] : []), '-f', 'rawvideo', '-']);
  const n = w * h;
  const description = indexed ? `frame ${selection.frame}` : `${selection.time}s`;
  if (raw.length < n * 3) fail(`could not decode ${description} from ${file}`);
  const gray = new Uint8Array(n);
  let chroma = 0;
  for (let i = 0; i < n; i++) {
    const r = raw[i * 3], g = raw[i * 3 + 1], b = raw[i * 3 + 2];
    gray[i] = (77 * r + 150 * g + 29 * b) >> 8;
    if (Math.max(r, g, b) - Math.min(r, g, b) > 60) chroma++;
  }
  return { gray, chroma };
}

function frameSelection(time, frame, fallback, label) {
  if (time !== undefined && frame !== undefined) fail(`Specify only one time or frame index for ${label}`);
  if (frame !== undefined) {
    const index = Number(frame);
    if (frame.trim() === '' || !Number.isSafeInteger(index) || index < 0) fail(`${label} frame index must be a nonnegative safe integer`);
    return { frame: index };
  }
  if (time !== undefined) {
    const seconds = Number(time);
    if (time.trim() === '' || !Number.isFinite(seconds) || seconds < 0) fail(`${label} time must be finite and nonnegative`);
    return { time: seconds };
  }
  return fallback;
}

const round = (value, digits) => Number(value.toFixed(digits));

function wholeFrame({ gray, chroma }, w, h) {
  let edges = 0, sum = 0;
  for (let i = 0; i < gray.length; i++) sum += gray[i];
  for (let y = 0; y < h - 1; y++) {
    for (let x = 0; x < w - 1; x++) {
      const i = y * w + x, v = gray[i];
      if (Math.abs(v - gray[i + 1]) > 24 || Math.abs(v - gray[i + w]) > 24) edges++;
    }
  }
  const n = w * h;
  return { mean_luma: round(sum / n, 1), detail: round(edges / n, 4), accent: round(chroma / n, 4) };
}

function parseRegion(name, value, w, h) {
  const parts = value.split(',').map(Number);
  if (parts.length !== 4 || !parts.every(Number.isInteger)) fail(`--${name} must be four integers x,y,w,h, got "${value}"`);
  const [x, y, rw, rh] = parts;
  if (x < 0 || y < 0 || rw < 2 || rh < 2 || x + rw > w || y + rh > h) {
    fail(`--${name} ${value} must lie inside the ${w}x${h} frame and be at least 2x2 pixels`);
  }
  return parts;
}

function regionBox(gray, w, h, [x0, y0, rw, rh], threshold) {
  const border = [];
  for (let x = x0; x < x0 + rw; x++) border.push(gray[y0 * w + x], gray[(y0 + rh - 1) * w + x]);
  for (let y = y0; y < y0 + rh; y++) border.push(gray[y * w + x0], gray[y * w + x0 + rw - 1]);
  border.sort((a, b) => a - b);
  const bg = border[Math.floor(border.length / 2)];
  let minX = Infinity, maxX = -1, minY = Infinity, maxY = -1;
  for (let y = y0; y < y0 + rh; y++) {
    for (let x = x0; x < x0 + rw; x++) {
      if (Math.abs(gray[y * w + x] - bg) >= threshold) {
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        maxY = y;
      }
    }
  }
  if (maxY < 0) return { background_luma: bg, bbox: null };
  return {
    background_luma: bg,
    bbox: [minX, minY, maxX - minX + 1, maxY - minY + 1],
    height_px: maxY - minY + 1,
    width_px: maxX - minX + 1,
    touches_region_edge: minX === x0 || minY === y0 || maxX === x0 + rw - 1 || maxY === y0 + rh - 1,
    touches_frame_edge: minX === 0 || minY === 0 || maxX === w - 1 || maxY === h - 1,
  };
}

const MOMENT = ['t', 'ref-t', 'frame', 'ref-frame', 'region', 'ref-region'];
const { values: a, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    t: { type: 'string' }, 'ref-t': { type: 'string' }, region: { type: 'string' }, 'ref-region': { type: 'string' },
    frame: { type: 'string' }, 'ref-frame': { type: 'string' }, pairs: { type: 'string' }, remake: { type: 'boolean' },
    size: { type: 'string' }, threshold: { type: 'string', default: '60' }, help: { type: 'boolean', short: 'h' },
  },
});
if (a.help || positionals.length !== 2 || (a.pairs === undefined) === (a.t === undefined && a.frame === undefined)) {
  console.log('usage: node measure_frame.mjs REF FILM (--t SECONDS | --frame INDEX) [--ref-t SECONDS | --ref-frame INDEX] [--region x,y,w,h] [--ref-region x,y,w,h] [--size WxH] [--threshold 60] [--remake]\n       node measure_frame.mjs REF FILM --pairs moments.json [--size WxH] [--threshold 60] [--remake]');
  process.exit(a.help ? 0 : 2);
}
const [refFile, filmFile] = positionals;
const [w, h] = a.size ? a.size.toLowerCase().split('x').map(Number) : probeSize(filmFile);
if (!(Number.isInteger(w) && Number.isInteger(h) && w > 0 && h > 0)) fail(`invalid frame size ${w}x${h}`);
const threshold = Number(a.threshold);

function measure(m) {
  const filmSelection = frameSelection(m.t, m.frame, undefined, 'film');
  const refSelection = frameSelection(m['ref-t'], m['ref-frame'], filmSelection, 'reference');
  const refFrame = rgbFrame(refFile, refSelection, w, h), filmFrame = rgbFrame(filmFile, filmSelection, w, h);
  const ref = wholeFrame(refFrame, w, h), film = wholeFrame(filmFrame, w, h);
  const out = {
    size: [w, h], ref_t: refSelection.time ?? null, film_t: filmSelection.time ?? null,
    ref_frame: refSelection.frame, film_frame: filmSelection.frame, ref, film,
  };
  if (a.remake) Object.assign(out, {
    brightness_ok: film.mean_luma >= ref.mean_luma * 0.9,
    detail_ok: film.detail >= ref.detail * 0.7,
    accent_ok: ref.accent < 0.002 || film.accent >= ref.accent * 0.6,
  });
  if (m.region || m['ref-region']) {
    const filmRegion = parseRegion('region', m.region || m['ref-region'], w, h);
    const refRegion = parseRegion('ref-region', m['ref-region'] || m.region, w, h);
    ref.region = regionBox(refFrame.gray, w, h, refRegion, threshold);
    film.region = regionBox(filmFrame.gray, w, h, filmRegion, threshold);
    // An element that cannot be found must never read as a pass: a missing film
    // element fails, and an empty reference region means the measurement is blocked.
    if (!ref.region.bbox) {
      out.region_status = 'blocked';
      out.region_error = 'no content in the reference region; choose a region around the reference element and measure again';
      out.clipped = null;
    } else if (!film.region.bbox) {
      out.region_status = 'failed';
      out.region_error = 'no content in the film region; the element is missing or the region is wrong';
      out.clipped = null;
    } else {
      out.region_status = 'measured';
      out.height_ratio = round(film.region.height_px / ref.region.height_px, 2);
      out.clipped = film.region.touches_frame_edge;
    }
    if (a.remake) out.height_ok = out.region_status === 'measured' && out.height_ratio >= 0.8;
  }
  return out;
}

if (a.pairs === undefined) console.log(JSON.stringify(measure(a), null, 2));
else {
  let pairs;
  try { pairs = JSON.parse(readFileSync(a.pairs, 'utf8')); } catch (e) { fail(`--pairs ${a.pairs}: ${e.message}`); }
  if (!Array.isArray(pairs) || !pairs.length) fail('--pairs must hold a non-empty JSON list of moments');
  const results = pairs.map((p, i) => {
    if (!p || typeof p !== 'object' || Array.isArray(p)) fail(`--pairs entry ${i} must be an object`);
    const unknown = Object.keys(p).filter(k => k !== 'label' && !MOMENT.includes(k));
    if (unknown.length) fail(`--pairs entry ${i}: unknown key ${unknown.join(', ')} (use ${MOMENT.join(', ')}, label)`);
    if (p.t === undefined && p.frame === undefined) fail(`--pairs entry ${i} needs "t" or "frame"`);
    const m = Object.fromEntries(MOMENT.filter(k => p[k] !== undefined && p[k] !== null).map(k => [k, String(p[k])]));
    return { ...(p.label !== undefined ? { label: p.label } : {}), ...measure(m) };
  });
  console.log(JSON.stringify(results, null, 2));
}
