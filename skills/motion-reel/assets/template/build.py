"""Build a standalone local composition from its editable sources.

project.json is the single source for copy, shot order, shot length (in beats) and sound.
This script derives every time from it once and writes timeline.json for the page and renderer.
"""
from pathlib import Path
from array import array
import json, math, re, subprocess, sys
from urllib.parse import quote
root=Path(__file__).resolve().parent
cfg=json.loads((root/'project.json').read_text())
def fail(message):raise SystemExit(f'project.json: {message}')
for key in ['width','height','fps','bpm']:
 if not isinstance(cfg.get(key),(int,float)) or cfg[key]<=0:fail(f'invalid {key}')
if any(int(cfg[k])!=cfg[k] for k in ['width','height','fps']):fail('canvas and fps must be integers')
if cfg['width']%2 or cfg['height']%2:fail('H.264 canvas dimensions must be even')
scene_bpm=cfg.get('sceneBpm',cfg['bpm'])
if not isinstance(scene_bpm,(int,float)) or scene_bpm<=0:fail('invalid sceneBpm')
fps=cfg['fps'];spb=60/cfg['bpm']

sound=cfg.get('sound') or {}
library=sound.get('library') or {}
def ledger(name,entry):
 if not isinstance(entry,dict):fail(f'{name} must be an object')
 for key in ['file','source','license']:
  if not isinstance(entry.get(key),str) or not entry[key].strip():fail(f'{name}.{key} is required: record where the audio came from and its license')
 path=(root/entry['file']).resolve()
 if not path.is_file():fail(f'{name}.file not found: {entry["file"]}')
 return path
def probe_duration(path):
 return float(json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',str(path)]))['format']['duration'])
def peak_offset(path):
 """Seconds from file start to its loudest 5 ms window; cues align this moment to the beat."""
 raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-ac','1','-ar','48000','-f','f32le','-']);x=array('f');x.frombytes(raw)
 if sys.byteorder!='little':x.byteswap()
 win=240;best=0;at=0
 for i in range(0,max(1,len(x)-win+1),win):
  e=sum(v*v for v in x[i:i+win])
  if e>best:best=e;at=i
 return at/48000

shots=cfg.get('shots')
if not isinstance(shots,list) or not shots:fail('shots must be a non-empty list')
timeline_shots=[];ids=set();beat=0
for i,s in enumerate(shots):
 if not isinstance(s,dict) or not isinstance(s.get('scene'),str):fail(f'shots[{i}].scene is required')
 sid=s.get('id',s['scene'])
 if sid in ids:fail(f'duplicate shot id "{sid}": give repeated scenes distinct ids')
 ids.add(sid)
 if not isinstance(s.get('beats'),(int,float)) or s['beats']<=0:fail(f'shot {sid}: beats must be positive')
 hud=s.get('hud','paper')
 if hud not in ('paper','ink',None):fail(f'shot {sid}: hud must be "paper", "ink" or null')
 timeline_shots.append({'id':sid,'scene':s['scene'],'beats':s['beats'],'startBeat':beat,'start':beat*spb,'label':s.get('label',sid.upper()),'hit':s.get('hit',0),'hud':hud,'copy':s.get('copy',{}),'sfx':s.get('sfx',[])})
 beat+=s['beats']
musical=beat*spb;frames=round(musical*fps);duration=frames/fps
for a,b in zip(timeline_shots,timeline_shots[1:]):a['end']=b['start']
timeline_shots[-1]['end']=duration
# A cut appears on the first frame at or after its beat.
cut_error=max(math.ceil(s['start']*fps-1e-9)/fps-s['start'] for s in timeline_shots)

# Explainers: with a "facts" list, every number on screen must appear in a quote that really sits at its cited line.
facts=cfg.get('facts')
if facts is not None:
 number=re.compile(r'\d(?:[\d,.]*\d)?');nums=lambda s:{n.replace(',','') for n in number.findall(s)}
 src_root=(root/cfg.get('factsRoot','.')).resolve();quoted=set()
 if not isinstance(facts,list):fail('facts must be a list of {text, source, quote}')
 for i,f in enumerate(facts):
  if not isinstance(f,dict) or not all(isinstance(f.get(k),str) and f[k].strip() for k in ['text','source','quote']):fail(f'facts[{i}] needs text, source ("path:line", "path:a-b", "git:<rev>" or "user") and quote')
  flat=lambda s:' '.join(s.split())
  if f['source'].startswith('git:'):
   # A commit message: the quote must be in `git show` of that revision in factsRoot's repository.
   r=subprocess.run(['git','-C',str(src_root),'show','-s','--format=%B',f['source'][4:]],capture_output=True,text=True)
   if r.returncode:fail(f'facts[{i}]: {f["source"]} is not a commit in {src_root}')
   text=r.stdout
  elif f['source']!='user':
   m=re.fullmatch(r'(.+):(\d+)(?:-(\d+))?',f['source'])
   if not m:fail(f'facts[{i}].source must be "path:line", "path:a-b", "git:<rev>" or "user"')
   path=(src_root/m[1]);a=int(m[2]);b=int(m[3] or m[2])
   if not path.is_file():fail(f'facts[{i}]: {m[1]} not found under {src_root}')
   text=' '.join(path.read_text(errors='replace').splitlines()[a-1:b])
  if f['source']!='user' and flat(f['quote']) not in flat(text):fail(f'facts[{i}]: the quote is not on {f["source"]}: "{f["quote"]}"')
  quoted|=nums(f['quote'])
 shown=[cfg.get(k) for k in ['name','tagline','eyebrow','credit']]+list(cfg.get('opening') or [])
 def strings(x):
  if isinstance(x,str):yield x
  elif isinstance(x,list):
   for y in x:yield from strings(y)
  elif isinstance(x,dict):
   for y in x.values():yield from strings(y)
 unsourced=sorted({(n,s) for s in [*strings(shown),*strings([t['copy'] for t in timeline_shots])] for n in nums(s) if n not in quoted})
 if unsourced:fail('numbers on screen without a quoted source in facts: '+'; '.join(f'{n} in "{s}"' for n,s in unsourced))
# Font files: each becomes an @font-face rule that the page loads before the first frame. Like audio, each needs a license.
fonts=cfg.get('fonts') or []
if not isinstance(fonts,list):fail('fonts must be a list of {family, file, license, weight?, style?}')
faces=[]
for i,f in enumerate(fonts):
 if not isinstance(f,dict):fail(f'fonts[{i}] must be an object')
 for key in ['family','file','license']:
  if not isinstance(f.get(key),str) or not f[key].strip():fail(f'fonts[{i}].{key} is required'+(': record the font\'s license' if key=='license' else ''))
 if re.search(r'["\\<>\n]',f['family']):fail(f'fonts[{i}].family must not contain quotes, backslashes, angle brackets or line breaks')
 path=(root/f['file']).resolve()
 if not path.is_file():fail(f'fonts[{i}].file not found: {f["file"]}')
 if not path.is_relative_to(root):fail(f'fonts[{i}].file must be inside the project folder, where the renderer can serve it: {f["file"]}')
 weight,style=f.get('weight'),f.get('style')
 if weight is not None and not re.fullmatch(r'\d{1,4}( \d{1,4})?',str(weight)):fail(f'fonts[{i}].weight must be a number such as 400, or a range such as "100 900" for a variable font')
 if style is not None and style not in ('normal','italic','oblique'):fail(f'fonts[{i}].style must be "normal", "italic" or "oblique"')
 faces.append(f'@font-face{{font-family:"{f["family"]}";src:url("{quote(path.relative_to(root).as_posix())}")'+(f';font-weight:{weight}' if weight is not None else '')+(f';font-style:{style}' if style else '')+'}')
music=sound.get('music')
if music is not None:
 path=ledger('sound.music',music)
 start=music.get('start',0)
 if not isinstance(start,(int,float)) or start<0:fail('sound.music.start must be a non-negative number of seconds')
 available=probe_duration(path)-start
 if available<duration-1e-3:fail(f'sound.music has {available:.3f}s after start; the film needs {duration:.3f}s')
 music={**music,'path':str(path)}
peaks={}
cues=[]
for s in timeline_shots:
 for j,c in enumerate(s['sfx']):
  name=c.get('name') if isinstance(c,dict) else None
  if name not in library:fail(f'shot {s["id"]}: sfx[{j}] names "{name}", which is not in sound.library')
  if name not in peaks:peaks[name]=(ledger(f'sound.library.{name}',library[name]),None)
  path,_=peaks[name]
  align=c.get('align','peak')
  if align not in ('peak','start'):fail(f'shot {s["id"]}: sfx[{j}].align must be "peak" or "start"')
  t=s['start']+c.get('beat',0)*spb
  if not 0<=t<duration:fail(f'shot {s["id"]}: sfx "{name}" lands at {t:.3f}s, outside the film')
  if align=='peak' and peaks[name][1] is None:peaks[name]=(path,peak_offset(path))
  cues.append({'t':t,'shot':s['id'],'name':name,'path':str(path),'gain':c.get('gain',0),'lead':peaks[name][1] if align=='peak' else 0})

timeline={'fps':fps,'spb':spb,'sceneBeat':60/scene_bpm,'beats':beat,'musicalDuration':musical,'duration':duration,'frames':frames,'maxCutLagSeconds':cut_error,'shots':timeline_shots,'sound':{'synth':sound.get('synth',True),'music':music,'sfx':cues}}
(root/'timeline.json').write_text(json.dumps(timeline,indent=1)+'\n')
html=(root/'engine.html').read_text()
values={'FONT_FACES':'\n'.join(faces),'CONFIG_JSON':json.dumps(cfg,ensure_ascii=True).replace('<','\\u003c'),'TIMELINE_JSON':json.dumps(timeline,ensure_ascii=True).replace('<','\\u003c'),'SYMBOL_JS':(root/'symbol.js').read_text(),'SCENES_JS':(root/'scenes.js').read_text(),'SCORE_JS':(root/'score.js').read_text()}
for name,value in values.items():
 token='{{'+name+'}}'
 if html.count(token)!=1:raise SystemExit(f'Expected exactly one {token} in engine.html')
 html=html.replace(token,value)
(root/'reel.html').write_text(html)
(root/'check.js').write_text(html.split('<script>')[1].split('</script>')[0])
note='' if abs(musical-duration)<1e-9 else f' (musical {musical:.4f}s rounded to whole frames)'
print(f'Built {cfg["name"]}: {duration:.3f}s / {frames} frames / {len(timeline_shots)} shots{note}; cuts lag their beats by at most {cut_error*1000:.1f} ms')
