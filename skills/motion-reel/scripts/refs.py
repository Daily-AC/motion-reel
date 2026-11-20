#!/usr/bin/env python3
"""Search a public catalog of commercial motion films and download a reference into a film project.

The catalog is OpenMotion's online template library (about 350 brand films, product launches and
explainers from companies such as Anthropic, OpenAI, Figma, Linear and Notion). Its descriptions and
stage timings were written by the catalog's authors from the videos and are approximate. Only metadata
is cached; the videos stay with their owners and are downloaded on request for private study.

  python3 refs.py sync                           # fetch or refresh the index
  python3 refs.py search logo reveal --kind 3D   # all words must match; falls back to any word
  python3 refs.py show 0053d84c                  # full record and links
  python3 refs.py get 0053d84c --dest refs       # reference.mp4 + motion.md + meta.json
"""
from pathlib import Path
import argparse, http.client, io, json, os, shutil, subprocess, sys, time, urllib.error, urllib.request, zipfile

CATALOG_POINTER = 'https://raw.githubusercontent.com/nexu-io/openmotion/main/library/templates/catalog/catalog.json'
CATALOG_FALLBACK = 'https://r.open-design.ai/resources/1500c9af-186b-457f-b74d-a58113f657d8/channels/default/main.json'
CACHE = Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache') / 'motion-reel'
INDEX = CACHE / 'refs-index.json'
KINDS = {'3d': '三维动效', 'ui': '界面动效', 'graphic': '图形动效', 'type': '文字动效', 'live': '实拍剪辑'}


class DownloadError(Exception):
    pass


def fetch(url, timeout=60, attempts=4):
    """Download with retries: catalog hosts drop TLS connections now and then, and a second try usually works."""
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'motion-reel-refs'})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code < 500 or attempt == attempts - 1:
                raise DownloadError(f'{url}: HTTP {error.code}') from None
        except (OSError, http.client.HTTPException) as error:  # SSL, connection reset, timeout, truncated body
            if attempt == attempts - 1:
                reason = str(getattr(error, 'reason', None) or error) or type(error).__name__
                raise DownloadError(f'{url}: {reason} ({attempts} attempts)') from None
        time.sleep(.5 * 2 ** attempt)


def sync(url=None):
    if not url:
        try:
            url = json.loads(fetch(CATALOG_POINTER, attempts=1))['source']['url']
        except Exception as error:  # the pointer is a convenience; the published channel is the data
            print(f'catalog pointer unavailable ({error}); using the known channel', file=sys.stderr)
            url = CATALOG_FALLBACK
    data = json.loads(fetch(url, timeout=180))
    content = data['content']
    zh = {t['templateId']: t for t in content.get('zh-CN', {}).get('templates', [])}
    en = {t['templateId']: t for t in content.get('en', {}).get('templates', [])}
    entries = []
    for tid in sorted(set(zh) | set(en)):
        a, b = zh.get(tid, {}), en.get(tid, {})
        oa, ob = a.get('original', {}), b.get('original', {})
        base = a or b
        o = oa or ob
        entries.append({
            'id': tid, 'order': base.get('sortOrder'), 'brand': base.get('brand') or '',
            'name': oa.get('templateName') or '', 'name_en': ob.get('templateName') or '',
            'summary': oa.get('summary') or '', 'summary_en': ob.get('summary') or '',
            'style': oa.get('styleDescription') or '', 'style_en': ob.get('styleDescription') or '',
            'use': oa.get('promotionalUseCases') or '', 'use_en': ob.get('promotionalUseCases') or '',
            'kind': oa.get('visualPresentation') or '', 'kind_en': ob.get('visualPresentation') or '',
            'tags': o.get('motionTags') or '', 'industries': base.get('industries') or [],
            'colors': base.get('colors') or [], 'author': o.get('author') or '',
            'seconds': float(o.get('durationSeconds') or 0), 'width': base.get('width'), 'height': base.get('height'),
            'video': o.get('sourceVideoUrl') or base.get('previewUrl'), 'motion_doc': base.get('motionDocumentUrl'),
            'original': o.get('sourceUrl') or '', 'editable': bool(base.get('indexUrl') or base.get('projectFileUrl')),
        })
    CACHE.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps({'source': url, 'version': data.get('version'), 'synced': time.strftime('%Y-%m-%d'),
                                 'entries': entries}, ensure_ascii=False))
    print(f'{len(entries)} references indexed from catalog {data.get("version")} -> {INDEX}')


def load():
    if not INDEX.exists():
        sync()
    return json.loads(INDEX.read_text())


def handle(entry):
    tid = entry['id']
    return tid[7:15] if tid.startswith('motion-') else tid


def aspect(entry):
    w, h = entry.get('width') or 0, entry.get('height') or 0
    if not w or not h:
        return '?'
    return 'square' if abs(w - h) / max(w, h) < .05 else ('landscape' if w > h else 'portrait')


def haystack(entry):
    fields = [entry[k] for k in ('name', 'name_en', 'brand', 'summary', 'summary_en', 'style', 'style_en',
                                  'use', 'use_en', 'kind', 'kind_en', 'tags', 'author')]
    return ' '.join(fields + entry['industries'] + entry['colors']).lower()


def find(entries, key):
    key = key.lower()
    exact = [e for e in entries if handle(e) == key or e['id'] == key]
    hits = exact or [e for e in entries if key in e['id'].lower()]
    if len(hits) != 1:
        raise SystemExit(f'"{key}" matches {len(hits)} references; use a longer id from search')
    return hits[0]


def search(args):
    index = load()
    entries = index['entries']
    if args.brand:
        entries = [e for e in entries if args.brand.lower() in e['brand'].lower()]
    if args.kind:
        kind = KINDS.get(args.kind.lower(), args.kind).lower()
        entries = [e for e in entries if kind in (e['kind'] + ' ' + e['kind_en']).lower()]
    if args.aspect:
        entries = [e for e in entries if aspect(e) == args.aspect]
    if args.max_seconds:
        entries = [e for e in entries if 0 < e['seconds'] <= args.max_seconds]
    words = [w.lower() for w in args.words]
    scored = [(sum(w in haystack(e) for w in words), e) for e in entries]
    mode = 'all words'
    hits = [(s, e) for s, e in scored if s == len(words)]
    if words and not hits:
        mode = 'any word (no film matched all)'
        hits = [(s, e) for s, e in scored if s]
    hits.sort(key=lambda pair: (-pair[0], pair[1]['order'] if pair[1]['order'] is not None else 1e9))
    hits = [e for _, e in hits][:args.limit]
    if args.json:
        print(json.dumps(hits, ensure_ascii=False, indent=1))
        return
    print(f'{len(hits)} shown, matched on {mode}; index from {index["synced"]} (refresh: refs.py sync)')
    for e in hits:
        name = e['name'] or e['name_en']
        summary = (e['summary_en'] if args.en else e['summary']) or e['summary_en']
        print(f"{handle(e):<28} {e['brand'][:14]:<14} {e['seconds']:5.1f}s {aspect(e):<9} {name}")
        if summary:
            print(f"{'':<28} {summary[:110]}")


def show(args):
    print(json.dumps(find(load()['entries'], args.id), ensure_ascii=False, indent=1))


def get(args):
    entry = find(load()['entries'], args.id)
    folder = args.dest.expanduser().resolve() / handle(entry)
    folder.mkdir(parents=True, exist_ok=True)
    try:
        download(entry, folder)
    except DownloadError:
        if not any(folder.iterdir()):
            folder.rmdir()
        raise


def download(entry, folder):
    result = {'folder': str(folder)}
    video = folder / 'reference.mp4'
    if not video.exists() or video.stat().st_size == 0:
        video.write_bytes(fetch(entry['video'], timeout=300))
    result['video'] = str(video)
    doc = folder / 'motion.md'
    if entry.get('motion_doc') and not doc.exists():
        data = fetch(entry['motion_doc'])
        if data[:2] == b'PK':
            # A packaged guide: keep its notes, stage timing and keyframes. Its HTML demos are the
            # catalog's rough sketches, not the reference, so they are left out on purpose.
            with zipfile.ZipFile(io.BytesIO(data)) as package:
                for name in package.namelist():
                    if name in ('motion.md', 'timeline.json') or (name.startswith('assets/') and not name.endswith('/')):
                        target = folder / name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(package.read(name))
        else:
            doc.write_bytes(data)
    if doc.exists():
        result['motion_doc'] = str(doc)
    meta = dict(entry)
    if shutil.which('ffprobe'):
        probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                                    'stream=width,height,r_frame_rate:format=duration', '-of', 'json', str(video)]))
        stream = probe['streams'][0]
        num, den = (int(v) for v in stream['r_frame_rate'].split('/'))
        meta['fps'] = round(num / den, 3) if den else None  # of the downloaded file; some catalog videos are 12 fps previews
        result.update(width=stream['width'], height=stream['height'], fps=meta['fps'],
                      seconds=round(float(probe['format']['duration']), 3))
    (folder / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1) + '\n')
    result['original'] = entry['original'] or None
    result['note'] = 'Third-party film for private study. Keep it out of git and published material.'
    print(json.dumps(result, ensure_ascii=False, indent=1))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('sync', help='fetch or refresh the catalog index')
    p.add_argument('--url', help='published catalog JSON; default follows the OpenMotion repository pointer')
    p = sub.add_parser('search', help='find references by words and filters')
    p.add_argument('words', nargs='*')
    p.add_argument('--brand')
    p.add_argument('--kind', help='3d, ui, graphic, type, live, or a catalog label')
    p.add_argument('--aspect', choices=['landscape', 'portrait', 'square'])
    p.add_argument('--max-seconds', type=float)
    p.add_argument('--limit', type=int, default=12)
    p.add_argument('--en', action='store_true', help='print English summaries')
    p.add_argument('--json', action='store_true')
    p = sub.add_parser('show', help='print one full record')
    p.add_argument('id')
    p = sub.add_parser('get', help='download the reference video and its motion notes')
    p.add_argument('id')
    p.add_argument('--dest', type=Path, default=Path('refs'))
    args = parser.parse_args()
    try:
        if args.command == 'sync':
            sync(args.url)
        else:
            {'search': search, 'show': show, 'get': get}[args.command](args)
    except DownloadError as error:
        raise SystemExit(f'refs.py {args.command}: download failed: {error}')


if __name__ == '__main__':
    main()
