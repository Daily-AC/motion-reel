"""Meaningful packaging checks. Real rendering and visual review remain separate."""
from pathlib import Path
import json,shutil,subprocess,tempfile,unittest,sys
ROOT=Path(__file__).resolve().parents[1];SKILL=ROOT/'skills/motion-reel'
def new_film(tmp):
 dest=Path(tmp)/'film';subprocess.run([sys.executable,str(SKILL/'scripts/new_project.py'),str(dest),'--brand','TEST'],check=True,capture_output=True);return dest
def build(dest,edit):
 cfg=json.loads((dest/'project.json').read_text());edit(cfg);(dest/'project.json').write_text(json.dumps(cfg,ensure_ascii=False))
 r=subprocess.run([sys.executable,str(dest/'build.py')],capture_output=True,text=True)
 return r,(json.loads((dest/'timeline.json').read_text()) if r.returncode==0 else None)
class Bundle(unittest.TestCase):
 def test_seed_reproducible(self):
  def seed(value):return subprocess.check_output([sys.executable,str(SKILL/'scripts/creative_seed.py'),'--seed',value])
  self.assertEqual(seed('ABCDEF123456'),seed('ABCDEF123456'));self.assertNotEqual(seed('ABCDEF123456'),seed('FEDCBA654321'))
 def test_project_compile_and_overwrite_guard(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp)/'film';subprocess.run([sys.executable,str(SKILL/'scripts/new_project.py'),str(dest),'--brand','TEST'],check=True,capture_output=True)
   subprocess.run(['node','--check',str(dest/'check.js')],check=True,capture_output=True)
   marker=dest/'do-not-delete';marker.write_text('keep')
   r=subprocess.run([sys.executable,str(SKILL/'scripts/new_project.py'),str(dest)],capture_output=True)
   self.assertNotEqual(r.returncode,0);self.assertEqual(marker.read_text(),'keep')
 def test_shot_beats_move_only_later_cuts(self):
  # "Slow down shot 2" is one field: earlier cuts stay, later cuts move by the added beats, the film still ends on a whole frame.
  with tempfile.TemporaryDirectory() as tmp:
   dest=new_film(tmp);_,before=build(dest,lambda c:None)
   def slow(c):c['shots'][1]['beats']=8
   r,after=build(dest,slow);self.assertEqual(r.returncode,0,r.stderr)
   spb=60/128;a=[s['start'] for s in before['shots']];b=[s['start'] for s in after['shots']]
   self.assertEqual(b[:2],a[:2]);self.assertTrue(all(abs(y-x-4*spb)<1e-9 for x,y in zip(a[2:],b[2:])))
   self.assertEqual(after['frames'],round(36*spb*60));self.assertEqual(after['shots'][-1]['end'],after['frames']/60)
 def test_measured_tempo_rounds_to_frames(self):
  # A track's measured tempo rarely gives whole frames; the film rounds and every cut lags its beat by under one frame.
  with tempfile.TemporaryDirectory() as tmp:
   dest=new_film(tmp)
   def tempo(c):c['bpm']=129.996677
   r,tl=build(dest,tempo);self.assertEqual(r.returncode,0,r.stderr)
   self.assertEqual(tl['frames'],round(32*60/129.996677*60));self.assertLess(tl['maxCutLagSeconds'],1/60)
 def test_audio_without_license_is_refused(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=new_film(tmp);(dest/'track.wav').write_bytes(b'')
   def music(c):c['sound']['music']={'file':'track.wav','source':'a friend','license':''}
   r,_=build(dest,music);self.assertNotEqual(r.returncode,0);self.assertIn('license',r.stderr)
   def sfx(c):c['sound']['music']=None;c['sound']['library']={'pop':{'file':'track.wav','license':'CC0'}};c['shots'][0]['sfx']=[{'name':'pop'}]
   r,_=build(dest,sfx);self.assertNotEqual(r.returncode,0);self.assertIn('source',r.stderr)
 def test_project_fonts_need_a_file_a_source_and_a_license(self):
  # A declared font becomes an @font-face rule in the page; a missing file or license is refused, like audio.
  with tempfile.TemporaryDirectory() as tmp:
   dest=new_film(tmp);face={'family':'Test Display','file':'fonts/InterVariable.woff2','weight':'100 900','source':'bundled Inter','license':'OFL-1.1 (fonts/Inter-OFL.txt)'}
   r,_=build(dest,lambda c:c.update(fonts=[dict(face)]));self.assertEqual(r.returncode,0,r.stderr)
   self.assertIn('@font-face{font-family:"Test Display";src:url("fonts/InterVariable.woff2");font-weight:100 900}',(dest/'reel.html').read_text())
   r,_=build(dest,lambda c:c.update(fonts=[{**face,'file':'fonts/Missing.woff2'}]));self.assertNotEqual(r.returncode,0);self.assertIn('not found',r.stderr)
   r,_=build(dest,lambda c:c.update(fonts=[{k:v for k,v in face.items() if k!='license'}]));self.assertNotEqual(r.returncode,0);self.assertIn('license',r.stderr)
   r,_=build(dest,lambda c:c.update(fonts=[{k:v for k,v in face.items() if k!='source'}]));self.assertNotEqual(r.returncode,0);self.assertIn('source',r.stderr)
 def test_numbers_on_screen_need_a_quoted_source(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=new_film(tmp);(dest/'notes.md').write_text('# Bench\nCold start took **2.7x** as long.\n')
   fact={'text':'2.7x','source':'notes.md:2','quote':'took **2.7x** as long'}
   def sourced(c):c['shots'][2]['copy']['title']='2.7x FASTER';c['facts']=[dict(fact)]
   r,_=build(dest,sourced);self.assertEqual(r.returncode,0,r.stderr)
   def unsourced(c):c['shots'][2]['copy']['title']='2.8x FASTER'
   r,_=build(dest,unsourced);self.assertNotEqual(r.returncode,0);self.assertIn('2.8',r.stderr)
   def wrong_line(c):c['shots'][2]['copy']['title']='2.7x FASTER';c['facts'][0]['source']='notes.md:1'
   r,_=build(dest,wrong_line);self.assertNotEqual(r.returncode,0);self.assertIn('not on notes.md:1',r.stderr)
 def test_reference_search_offline(self):
  # Search runs on the cached index: all words first, any word as a labelled fallback, filters narrow, ids resolve by prefix.
  def entry(i,name,kind,brand,w,h,s):return {'id':f'motion-{i}0000000-aaaa','order':int(i),'brand':brand,'name':name,'name_en':'','summary':'','summary_en':'','style':'','style_en':'','use':'','use_en':'','kind':kind,'kind_en':'','tags':'','industries':[],'colors':[],'author':'','seconds':s,'width':w,'height':h,'video':'','motion_doc':None,'original':'','editable':False}
  with tempfile.TemporaryDirectory() as tmp:
   (Path(tmp)/'motion-reel').mkdir();(Path(tmp)/'motion-reel/refs-index.json').write_text(json.dumps({'source':'fixture','synced':'today','entries':[entry('1','Logo particle reveal','三维动效','Acme',1920,1080,12),entry('2','Logo slide','界面动效','Beta',1080,1920,30),entry('3','Grid tunnel','三维动效','Acme',720,720,9)]}))
   env={**__import__('os').environ,'XDG_CACHE_HOME':tmp}
   def refs(*a):return subprocess.run([sys.executable,str(SKILL/'scripts/refs.py'),*a],capture_output=True,text=True,env=env)
   r=refs('search','logo','particle');self.assertIn('all words',r.stdout);self.assertIn('10000000',r.stdout);self.assertNotIn('20000000',r.stdout)
   r=refs('search','logo','unicorn');self.assertIn('any word',r.stdout);self.assertIn('20000000',r.stdout)
   r=refs('search','--kind','3d','--aspect','square');self.assertIn('30000000',r.stdout);self.assertNotIn('10000000',r.stdout)
   self.assertEqual(json.loads(refs('show','20000000').stdout)['brand'],'Beta');self.assertNotEqual(refs('show','motion-').returncode,0)
 @unittest.skipUnless(__import__('shutil').which('ffmpeg'),'needs ffmpeg')
 def test_reference_get_retries_and_cleans_up(self):
  # A local host that drops the first connection without a response: get retries and records the file's fps in meta.json.
  # One that always drops it: a one-line error, no traceback, and no empty refs/<id>/ folder left behind.
  import http.server,threading
  with tempfile.TemporaryDirectory() as tmp:
   t=Path(tmp);subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=64x64:r=25','-t','1','-c:v','libx264','-pix_fmt','yuv420p',str(t/'v.mp4')],check=True)
   body=(t/'v.mp4').read_bytes();drops={'/flaky.mp4':1,'/dead.mp4':10**6}
   class Host(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_GET(self):
     if drops.get(self.path,0)>0:drops[self.path]-=1;self.close_connection=True;return
     self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
   srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),Host);threading.Thread(target=srv.serve_forever,daemon=True).start()
   url=f'http://127.0.0.1:{srv.server_address[1]}'
   entry=lambda i,path:{'id':f'motion-{i}0000000-aaaa','order':1,'brand':'Acme','name':path,'video':url+path,'motion_doc':None,'original':''}
   (t/'motion-reel').mkdir();(t/'motion-reel/refs-index.json').write_text(json.dumps({'source':'fixture','synced':'today','entries':[entry('a','/flaky.mp4'),entry('b','/dead.mp4')]}))
   env={**__import__('os').environ,'XDG_CACHE_HOME':tmp,'no_proxy':'127.0.0.1','NO_PROXY':'127.0.0.1'}
   def get(i):return subprocess.run([sys.executable,str(SKILL/'scripts/refs.py'),'get',i,'--dest',str(t/'refs')],capture_output=True,text=True,env=env)
   try:
    r=get('a0000000');self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(drops['/flaky.mp4'],0)
    self.assertEqual((t/'refs/a0000000/reference.mp4').read_bytes(),body);self.assertEqual(json.loads((t/'refs/a0000000/meta.json').read_text())['fps'],25)
    r=get('b0000000');self.assertNotEqual(r.returncode,0);self.assertNotIn('Traceback',r.stderr);self.assertEqual(len(r.stderr.strip().splitlines()),1,r.stderr)
    self.assertIn('download failed',r.stderr);self.assertFalse((t/'refs/b0000000').exists());self.assertEqual(drops['/dead.mp4'],10**6-4)
   finally:srv.shutdown()
 @unittest.skipUnless(__import__('shutil').which('ffmpeg'),'needs ffmpeg')
 def test_frame_measure_known_answer(self):
  # A gray field with a white box: mean luma and box height have known values, and a shorter box must fail height.
  with tempfile.TemporaryDirectory() as tmp:
   def clip(name,gray,h):subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i',f'color=0x{gray:02x}{gray:02x}{gray:02x}:s=640x360:r=30:d=1','-vf',f'drawbox=x=100:y=100:w=300:h={h}:color=white:t=fill','-c:v','libx264','-crf','12','-pix_fmt','yuv420p',str(Path(tmp)/name)],check=True)
   clip('ref.mp4',128,100);clip('film.mp4',64,70)
   def measure(*a):return json.loads(subprocess.check_output(['node',str(SKILL/'scripts/measure_frame.mjs'),str(Path(tmp)/'ref.mp4'),str(Path(tmp)/'film.mp4'),*a]))
   out=measure('--t','0.5','--region','50,50,400,250','--remake')
   self.assertAlmostEqual(out['ref']['mean_luma'],128*(1-30000/230400)+255*30000/230400,delta=1.5);self.assertFalse(out['brightness_ok'])
   self.assertEqual(out['ref']['region']['height_px'],100);self.assertEqual(out['film']['region']['height_px'],70);self.assertFalse(out['height_ok'])
   # Remake thresholds only on request; the measurements are the same without them.
   plain=measure('--t','0.5','--region','50,50,400,250');self.assertEqual([k for k in plain if k.endswith('_ok')],[]);self.assertEqual(plain['height_ratio'],.7)
   # Several moments in one call: one result per entry, labels kept, each equal to its single-moment run.
   (Path(tmp)/'pairs.json').write_text(json.dumps([{'label':'box','t':0.5,'region':'50,50,400,250'},{'t':0.2,'ref-t':0.8}]))
   batch=measure('--pairs',str(Path(tmp)/'pairs.json'));self.assertEqual(len(batch),2);self.assertEqual(batch[0].pop('label'),'box');self.assertEqual(batch[0],plain)
   self.assertEqual(batch[1],measure('--t','0.2','--ref-t','0.8'))
 @unittest.skipUnless(__import__('shutil').which('ffmpeg') and __import__('shutil').which('uv'),'needs ffmpeg and uv')
 def test_reference_frame_sheet_grid(self):
  # A 1280x720 reference with a white box at 100,100 (300x100), gridded in 1920x1080 film pixels at 0.5 display scale: the box
  # sits at film 150,150 (450x150), which is where measure_frame.mjs finds it, and grid lines fall on multiples of 100 film px.
  with tempfile.TemporaryDirectory() as tmp:
   t=Path(tmp);folder=t/'refs/c0000000';folder.mkdir(parents=True)
   subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=0x404040:s=1280x720:r=25:d=2','-vf','drawbox=x=100:y=100:w=300:h=100:color=white:t=fill','-c:v','libx264','-crf','12','-pix_fmt','yuv420p',str(folder/'reference.mp4')],check=True)
   (t/'motion-reel').mkdir();(t/'motion-reel/refs-index.json').write_text(json.dumps({'source':'fixture','synced':'today','entries':[{'id':'motion-c0000000-aaaa','brand':'','name':'box','video':'','motion_doc':None,'original':''}]}))
   r=subprocess.run(['uv','run','-q','--with','pillow','python',str(SKILL/'scripts/refs.py'),'frames','c0000000','--times','0.5','--size','1920x1080'],cwd=t,capture_output=True,text=True,env={**__import__('os').environ,'XDG_CACHE_HOME':tmp})
   self.assertEqual(r.returncode,0,r.stderr);sheet=Path(r.stdout.strip());self.assertEqual(sheet,(folder/'frames-0.5.png').resolve())
   raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(sheet),'-f','rawvideo','-pix_fmt','gray','-']);px=lambda x,y:raw[y*960+x]
   self.assertEqual(len(raw),960*(540+28))
   self.assertGreater(px(180,120),240);self.assertLess(abs(px(420,420)-64),4)           # inside the box; plain background
   self.assertGreater(px(250,420),px(260,420)+30);self.assertGreater(px(300,420),px(250,420)+30)  # film x=500 minor, x=600 major
   box=json.loads(subprocess.check_output(['node',str(SKILL/'scripts/measure_frame.mjs'),str(folder/'reference.mp4'),str(folder/'reference.mp4'),'--t','0.5','--size','1920x1080','--region','120,120,520,220']))['ref']['region']['bbox']
   for got,want in zip(box,[150,150,450,150]):self.assertAlmostEqual(got,want,delta=2)
 @unittest.skipUnless(__import__('shutil').which('ffmpeg') and __import__('shutil').which('uv'),'needs ffmpeg and uv')
 def test_motion_measure_known_answer(self):
  # A textured block travels 240 px in the reference; the film repeats it later (no flag), travels 90 px (suppressed) or
  # 460 px right and 200 px down (2.4x the normalised travel: excess). A static reference sets no bar for excess.
  with tempfile.TemporaryDirectory() as tmp:
   t=Path(tmp);subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=120x120','-frames:v','1',str(t/'tex.png')],check=True)
   def clip(name,x,y='120'):subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=black:s=640x360:r=30:d=5','-loop','1','-framerate','30','-i',str(t/'tex.png'),'-filter_complex',f"[0][1]overlay=x='{x}':y='{y}':shortest=1",'-c:v','libx264','-crf','12','-pix_fmt','yuv420p',str(t/name)],check=True)
   clip('ref.mp4','if(lt(t,1),40,if(lt(t,2),40+240*(t-1),280))');clip('same.mp4','if(lt(t,3),40,if(lt(t,4),40+240*(t-3),280))');clip('weak.mp4','if(lt(t,3),40,if(lt(t,4),40+90*(t-3),130))')
   clip('fast.mp4','if(lt(t,3),40,if(lt(t,4),40+460*(t-3),500))','if(lt(t,3),20,if(lt(t,4),20+200*(t-3),220))');clip('still.mp4','260')
   def measure(*a):return subprocess.run(['uv','run','-q','--with','opencv-python-headless','--with','numpy','python',str(SKILL/'scripts/measure_motion.py'),*a],capture_output=True,text=True)
   def run(film,ref='ref.mp4'):return measure(str(t/ref),str(t/film),'--ref-start','1','--ref-end','2','--start','3','--end','4','--out',str(t/'m.json'))
   r=run('same.mp4');self.assertEqual(r.returncode,0,r.stderr);d=json.loads(r.stdout)
   self.assertAlmostEqual(d['referenceSpanPx'][0],240,delta=2);self.assertAlmostEqual(d['outputSpanPx'][0],240,delta=2);self.assertFalse(d['possibleSuppressedMotion']);self.assertFalse(d['possibleExcessMotion'])
   r=run('weak.mp4');self.assertEqual(r.returncode,2);d=json.loads(r.stdout);self.assertAlmostEqual(d['outputSpanPx'][0],90,delta=2);self.assertTrue(d['possibleSuppressedMotion']);self.assertFalse(d['possibleExcessMotion'])
   r=run('fast.mp4');self.assertEqual(r.returncode,2);d=json.loads(r.stdout);self.assertAlmostEqual(d['outputSpanPx'][0],460,delta=3);self.assertAlmostEqual(d['outputSpanPx'][1],200,delta=3)
   self.assertTrue(d['possibleExcessMotion']);self.assertFalse(d['possibleSuppressedMotion']);self.assertAlmostEqual(d['travelRatio'],((460/640)**2+(200/360)**2)**.5/(240/640),delta=.05)
   r=run('fast.mp4','still.mp4');self.assertEqual(r.returncode,0,r.stdout);d=json.loads(r.stdout);self.assertIsNone(d['possibleExcessMotion']);self.assertFalse(d['possibleSuppressedMotion']);self.assertIn('no bar',d['note'])
   # Reference alone, as reference-films.md shows it: only --ref-start/--ref-end, no film interval and no report file.
   r=measure(str(t/'ref.mp4'),'--ref-start','1','--ref-end','2');self.assertEqual(r.returncode,0,r.stderr);d=json.loads(r.stdout)
   self.assertAlmostEqual(d['referenceSpanPx'][0],240,delta=2);self.assertFalse(d['comparisonPerformed'])
 def test_new_project_carries_reference_tools(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=new_film(tmp)
   for name in ['measure_frame.mjs','measure_motion.py','APACHE-2.0.txt']:self.assertTrue((dest/name).is_file(),name)
   self.assertIn('refs/',(dest/'.gitignore').read_text())
 def test_licenses_and_asset_resolution(self):
  for p in ['LICENSE','assets/fonts/Inter-OFL.txt','assets/fonts/JetBrainsMono-OFL.txt','assets/fonts/InterVariable.woff2','assets/fonts/JetBrainsMono-Regular.ttf']:
   self.assertTrue((SKILL/p).is_file(),p);self.assertGreater((SKILL/p).stat().st_size,100)
def decode(path,w,h,frame=None):
 """RGB24 pixels of a PNG still or of a zero-based frame of a video, as decoded by FFmpeg."""
 sel=[] if frame is None else ['-vf',f'select=eq(n\\,{frame})','-fps_mode','passthrough']
 raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),*sel,'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
 assert len(raw)==w*h*3,(path,frame,len(raw));return raw
def luma(raw):return [(77*raw[i]+150*raw[i+1]+29*raw[i+2])>>8 for i in range(0,len(raw),3)]
def linear(v):v/=255;return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def lap_var(y,w,x0,y0,x1,y1):
 v=[y[r*w+c-1]+y[r*w+c+1]+y[(r-1)*w+c]+y[(r+1)*w+c]-4*y[r*w+c] for r in range(y0,y1) for c in range(x0,x1)];m=sum(v)/len(v)
 return sum((a-m)**2 for a in v)/len(v)
def strays(raw,w,own,box,tol=12):
 """Pixels inside box (x0,y0,x1,y1) whose channels differ from their own shot's color by more than tol."""
 x0,y0,x1,y1=box;return sum(1 for r in range(y0,y1) for c in range(x0,x1) if max(abs(raw[(r*w+c)*3+i]-own[i]) for i in range(3))>tol)
@unittest.skipUnless(__import__('shutil').which('ffmpeg') and __import__('shutil').which('node'),'needs ffmpeg and node')
class ThreeScenes(unittest.TestCase):
 """Known answers for three.js shots, measured on the renderer's decoded output. Skips when no browser can render."""
 W,H=480,270
 @classmethod
 def project(cls,shots):
  dest=Path(cls.tmp.name)/f'film{len(list(Path(cls.tmp.name).iterdir()))}';subprocess.run([sys.executable,str(SKILL/'scripts/new_project.py'),str(dest)],check=True,capture_output=True)
  (dest/'scenes.js').write_text((ROOT/'tests/three_fixture.js').read_text())
  cfg=json.loads((dest/'project.json').read_text());cfg.update(width=cls.W,height=cls.H,fps=60,bpm=120,sceneBpm=120,shots=shots,sound={'synth':False,'music':None,'library':{}})
  (dest/'project.json').write_text(json.dumps(cfg));return dest
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();shot=lambda scene,**copy:{'scene':scene,'id':f'{scene}{len(copy)}{sorted(copy.items())}','beats':2,'hud':None,'copy':copy}
  # 0-1 s static lit set, 1-2 s moving card, 2-6 s depth of field: aperture 0 near/far focus, aperture 0.3 near/far focus
  cls.film=cls.project([shot('lit'),shot('mover',speed=71.4,at=.5)]+[shot('dof',aperture=a,focus=f) for a in (0,.3) for f in (10,30)])
  doctor=subprocess.run(['node','render.mjs','doctor'],cwd=cls.film,capture_output=True,text=True)
  if doctor.returncode:cls.tmp.cleanup();raise unittest.SkipTest('no Chrome/Chromium for rendering: '+doctor.stderr.strip()[-200:])
  cls.stills={}
  for n in (1,4,16):
   ts='0.5' if n<16 else '0.5,1.5,1.5041666666666667,2.5,3.5,4.5,5.5'
   r=subprocess.run(['node','render.mjs','stills',ts,'--samples',str(n)],cwd=cls.film,capture_output=True,text=True)
   if r.returncode and ('WebGL2 is unavailable' in r.stderr or 'Floating-point color targets' in r.stderr):cls.tmp.cleanup();raise unittest.SkipTest('browser cannot render WebGL2 float targets')
   if r.returncode:raise RuntimeError(r.stderr)
   for t in ts.split(','):cls.stills[(n,float(t))]=decode(cls.film/'review/stills'/f'{t}.png',cls.W,cls.H)
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_static_brightness_independent_of_samples(self):
  # Accumulation must average, not sum or keep the last subframe: same mean luma at 1, 4 and 16 samples (±1%).
  frames={n:self.stills[(n,.5)] for n in (1,4,16)};means={n:sum(luma(f))/(self.W*self.H) for n,f in frames.items()}
  self.assertLessEqual(max(means.values())/min(means.values()),1.01,means)
  # and the samples did change the picture (soft shadow, depth of field, antialiasing), so the check is not vacuous
  self.assertGreater(sum(abs(a-b) for a,b in zip(frames[1],frames[16]))/len(frames[1]),.5)
 def test_motion_blur_extent(self):
  # A card crossing at a known speed is smeared by speed × shutter (0.5 frame). Coverage a(x) in linear light;
  # each blurred edge is a ramp of length L with integral of a(1-a) = L/6. Measured inside the vignette-free centre.
  bg,fg=linear(64),linear(224);x0,x1,rows=150,330,range(115,156)
  def cover(raw):y=luma(raw);return [[(linear(y[r*self.W+c])-bg)/(fg-bg) for c in range(x0,x1)] for r in rows]
  a,b=cover(self.stills[(16,1.5)]),cover(self.stills[(16,1.5041666666666667)])  # a quarter frame apart
  centroid=lambda m:sum(x*v for row in m for x,v in enumerate(row))/sum(v for row in m for v in row)
  per_frame=4*(centroid(b)-centroid(a));self.assertAlmostEqual(per_frame,71.4*135/(10*0.2679491924)/60,delta=1.5)
  blur=sum(3*sum(v*(1-v) for v in row) for row in a)/len(a)
  self.assertAlmostEqual(blur/(per_frame*.5),1,delta=.15,msg=f'blur {blur:.1f}px, expected {per_frame*.5:.1f}px')
 def test_depth_of_field(self):
  # Equal-size checkered cards at depth 10 (left) and 30 (right). Sharpness = variance of the Laplacian of luma.
  def sharp(t):y=luma(self.stills[(16,t)]);return lap_var(y,self.W,50,65,190,205),lap_var(y,self.W,291,65,432,205)
  (n0,f0),(n0b,f0b),(n_near,f_near),(n_far,f_far)=map(sharp,(2.5,3.5,4.5,5.5))
  near=lambda a,b:abs(a/b-1)<=.15
  self.assertTrue(near(n0,n0b) and near(f0,f0b),'aperture 0 must not depend on focus')
  self.assertTrue(near(n_near,n0),f'in-focus near card changed: {n_near:.0f} vs {n0:.0f}');self.assertLessEqual(f_near,f0/3,f'far card not defocused: {f_near:.0f} vs {f0:.0f}')
  self.assertTrue(near(f_far,f0),f'in-focus far card changed: {f_far:.0f} vs {f0:.0f}');self.assertLessEqual(n_far,n0/3,f'near card not defocused: {n_far:.0f} vs {n0:.0f}')
 def test_bloom(self):
  # A 10 px disc at the frame centre on linear 0.02, rendered at the same times with bloom 0 and 0.3 (threshold 1). Below the
  # threshold (0.6) bloom changes nothing. Above it (8.0) the disc stays saturated while the ring 14-60 px from its centre
  # gains radiance that falls off with distance.
  frames={}
  for b in (0,.3):
   film=self.project([{'scene':'glow','id':'dim','beats':2,'hud':None,'copy':{'level':.6,'bloom':b}},{'scene':'glow','id':'hot','beats':2,'hud':None,'copy':{'level':8,'bloom':b}}])
   r=subprocess.run(['node','render.mjs','stills','0.5,1.5','--samples','16'],cwd=film,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
   for t in ('0.5','1.5'):frames[(b,t)]=decode(film/'review/stills'/f'{t}.png',self.W,self.H)
  def zones(raw):
   y=luma(raw);cx,cy=self.W//2,self.H//2;disc=[];inner=[];outer=[]
   for r in range(cy-60,cy+61):
    for c in range(cx-60,cx+61):
     d=((r-cy+.5)**2+(c-cx+.5)**2)**.5;v=y[r*self.W+c]
     if d<=7:disc.append(v)
     elif 14<=d<30:inner.append(linear(v))
     elif 30<=d<=60:outer.append(linear(v))
   return sum(disc)/len(disc),sum(inner)/len(inner),sum(outer)/len(outer)
  self.assertEqual(frames[(0,'0.5')],frames[(.3,'0.5')],'bloom changed a frame with nothing above its threshold')
  (d0,i0,o0),(d1,i1,o1)=zones(frames[(0,'1.5')]),zones(frames[(.3,'1.5')])
  self.assertAlmostEqual(d1,d0,delta=1,msg='the emitter footprint changed');self.assertAlmostEqual(i0,.02,delta=.002,msg='halo without bloom')
  # a measurable halo: the inner ring gains at least five times the background radiance, more than the outer ring gains
  self.assertGreaterEqual(i1-i0,5*.02,f'no halo: inner ring {i0:.4f} -> {i1:.4f}');self.assertGreater(i1-i0,o1-o0,'halo does not fall off')
 def test_match_cut_keeps_designed_color_at_any_sample_count(self):
  # A flat ivory 2D shot cut to a three.js background of the same color, the last 2D and first 3D frame measured as per-channel
  # means in the vignette-free centre. Half-float accumulation drifted the sides apart (0.53-0.69 code values at 16-64 samples)
  # and off the design (1.71 at 64); both sides must stay within 0.5 of #F1EDE7 and of each other at 8, 16, 32 and 64 samples.
  want=(241,237,231);film=self.project([{'scene':'solid2d','id':'2d','beats':2,'hud':None,'copy':{'color':'#F1EDE7'}},{'scene':'solid3d','id':'3d','beats':2,'hud':None,'copy':{'color':'#F1EDE7'}}])
  def centre(raw):
   x0,y0,x1,y1=180,90,300,180;rows=[raw[(r*self.W+x0)*3:(r*self.W+x1)*3] for r in range(y0,y1)]
   return [sum(sum(row[c::3]) for row in rows)/((x1-x0)*(y1-y0)) for c in range(3)]
  for n in (8,16,32,64):
   r=subprocess.run(['node','render.mjs','stills','0.9833333333333333,1','--samples',str(n)],cwd=film,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
   self.assertNotIn('RGBA16F',r.stdout,'this browser has no blendable, filterable RGBA32F target, so the engine fell back to half floats')
   a,b=(centre(decode(film/'review/stills'/f'{t}.png',self.W,self.H)) for t in ('0.9833333333333333','1'))
   for side,m in (('2D',a),('3D',b)):self.assertLessEqual(max(abs(x-w) for x,w in zip(m,want)),.5,f'{n} samples: {side} side {m} is off #F1EDE7')
   self.assertLessEqual(max(abs(x-y) for x,y in zip(a,b)),.5,f'{n} samples: the cut steps from {a} to {b}')
 def test_cuts_between_2d_and_3d_never_blend(self):
  # Cuts at 1.02 s and 2.02 s fall inside the shutters of frames 61 and 121. Every subframe of a frame belongs to the shot
  # at its centre, so frames 60-61 | 62-63 and 120-121 | 122-123 hold only their own shot's color in the encoded film.
  colors={'2d-a':(255,48,0),'3d':(0,80,255),'2d-b':(0,192,96)}
  film=self.project([{'scene':'solid2d','id':'2d-a','beats':2.04,'hud':None,'hit':10,'copy':{'color':'#FF3000'}},{'scene':'solid3d','id':'3d','beats':2,'hud':None,'hit':10,'copy':{'color':'#0050FF'}},{'scene':'solid2d','id':'2d-b','beats':2,'hud':None,'copy':{'color':'#00C060'}}])
  r=subprocess.run(['node','render.mjs','render','--out','out/cuts.mp4','--samples','16'],cwd=film,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
  self.assertEqual(subprocess.run([sys.executable,'verify.py','out/cuts.mp4'],cwd=film,capture_output=True).returncode,0)
  box=(150,70,330,200)
  for frame,own in [(60,'2d-a'),(61,'2d-a'),(62,'3d'),(63,'3d'),(120,'3d'),(121,'3d'),(122,'2d-b'),(123,'2d-b')]:
   self.assertEqual(strays(decode(film/'out/cuts.mp4',self.W,self.H,frame),self.W,colors[own],box),0,f'frame {frame} is not pure {own}')
  # the check would catch one subframe in sixteen from the other shot (blended in linear light)
  mix=lambda a,b:round(255*((15*linear(a)+linear(b))/16)**(1/2.4)) if a or b else 0
  blend=bytes(c for _ in range(self.W*self.H) for c in (mix(255,0),mix(48,80),mix(0,255)))
  self.assertGreater(strays(blend,self.W,colors['2d-a'],box),0)
@unittest.skipUnless(__import__('shutil').which('ffmpeg') and __import__('shutil').which('node'),'needs ffmpeg and node')
class Fonts(unittest.TestCase):
 def test_declared_and_bundled_fonts_load_before_frame_zero(self):
  # A copy of the bundled Inter declared as "Test Display", with displayFont set to something else (the case that used to drop
  # the Inter preload). Frame 0 draws one word in "Reel Sans", in "Test Display" and in a family that does not exist, in three
  # 90 px bands. Both real families must already be loaded: their glyph masks match each other and differ from the fallback's.
  W,H=480,270
  with tempfile.TemporaryDirectory() as tmp:
   dest=new_film(tmp);shutil.copy2(dest/'fonts/InterVariable.woff2',dest/'fonts/TestDisplay.woff2')  # its own URL, loaded on its own
   (dest/'scenes.js').write_text("""function words(g) {
  g.fillStyle = '#fff'; g.fillRect(-200, -200, W + 400, H + 400); g.fillStyle = '#000'; g.textBaseline = 'middle';
  ['"Reel Sans"', '"Test Display"', '"No Such Family"'].forEach((f, i) => { g.font = `700 44px ${f}`; g.fillText('Hamburgefonstiv', 16, 45 + 90 * i); });
}
const SCENE_LIBRARY = { words: { draw: words, beats: 2 } };
""")
   def edit(c):c.update(width=W,height=H,displayFont='serif',fonts=[{'family':'Test Display','file':'fonts/TestDisplay.woff2','weight':'100 900','source':'bundled Inter','license':'OFL-1.1'}],shots=[{'scene':'words','beats':2,'hud':None}],sound={'synth':False,'music':None,'library':{}})
   r,_=build(dest,edit);self.assertEqual(r.returncode,0,r.stderr)
   r=subprocess.run(['node','render.mjs','stills','0','--samples','1'],cwd=dest,capture_output=True,text=True)
   if r.returncode and 'WebGL2' in r.stderr+r.stdout:self.skipTest('browser cannot render')
   self.assertEqual(r.returncode,0,r.stderr)
   y=luma(decode(dest/'review/stills/0.png',W,H));band=lambda i:[v<128 for v in y[90*i*W:90*(i+1)*W]]
   inter,alias,fallback=band(0),band(1),band(2);ink=sum(inter)
   self.assertGreater(ink,1000,'no text drawn')
   self.assertLess(sum(a!=b for a,b in zip(inter,alias)),ink*.02,'"Test Display" is not the Inter file it declares')
   self.assertGreater(sum(a!=b for a,b in zip(inter,fallback)),ink*.2,'"Reel Sans" was not loaded before frame 0')
if __name__=='__main__':unittest.main()
