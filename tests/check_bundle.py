"""Meaningful packaging checks. Real rendering and visual review remain separate."""
from pathlib import Path
import json,subprocess,tempfile,unittest,sys
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
 def test_frame_measure_known_answer(self):
  # A gray field with a white box: mean luma and box height have known values, and a shorter box must fail height.
  with tempfile.TemporaryDirectory() as tmp:
   def clip(name,gray,h):subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i',f'color=0x{gray:02x}{gray:02x}{gray:02x}:s=640x360:r=30:d=1','-vf',f'drawbox=x=100:y=100:w=300:h={h}:color=white:t=fill','-c:v','libx264','-crf','12','-pix_fmt','yuv420p',str(Path(tmp)/name)],check=True)
   clip('ref.mp4',128,100);clip('film.mp4',64,70)
   out=json.loads(subprocess.check_output(['node',str(SKILL/'scripts/measure_frame.mjs'),str(Path(tmp)/'ref.mp4'),str(Path(tmp)/'film.mp4'),'--t','0.5','--region','50,50,400,250']))
   self.assertAlmostEqual(out['ref']['mean_luma'],128*(1-30000/230400)+255*30000/230400,delta=1.5);self.assertFalse(out['brightness_ok'])
   self.assertEqual(out['ref']['region']['height_px'],100);self.assertEqual(out['film']['region']['height_px'],70);self.assertFalse(out['height_ok'])
 @unittest.skipUnless(__import__('shutil').which('ffmpeg') and __import__('shutil').which('uv'),'needs ffmpeg and uv')
 def test_motion_measure_known_answer(self):
  # A textured block travels 240 px in the reference; the film repeats it later (no flag) or travels 90 px (flagged).
  with tempfile.TemporaryDirectory() as tmp:
   t=Path(tmp);subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=120x120','-frames:v','1',str(t/'tex.png')],check=True)
   def clip(name,x):subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=black:s=640x360:r=30:d=5','-loop','1','-framerate','30','-i',str(t/'tex.png'),'-filter_complex',f"[0][1]overlay=x='{x}':y=120:shortest=1",'-c:v','libx264','-crf','12','-pix_fmt','yuv420p',str(t/name)],check=True)
   clip('ref.mp4','if(lt(t,1),40,if(lt(t,2),40+240*(t-1),280))');clip('same.mp4','if(lt(t,3),40,if(lt(t,4),40+240*(t-3),280))');clip('weak.mp4','if(lt(t,3),40,if(lt(t,4),40+90*(t-3),130))')
   def run(film):return subprocess.run(['uv','run','-q','--with','opencv-python-headless','--with','numpy','python',str(SKILL/'scripts/measure_motion.py'),str(t/'ref.mp4'),str(t/film),'--ref-start','1','--ref-end','2','--start','3','--end','4','--out',str(t/'m.json')],capture_output=True,text=True)
   r=run('same.mp4');self.assertEqual(r.returncode,0,r.stderr);d=json.loads(r.stdout)
   self.assertAlmostEqual(d['referenceSpanPx'][0],240,delta=2);self.assertAlmostEqual(d['outputSpanPx'][0],240,delta=2);self.assertFalse(d['possibleSuppressedMotion'])
   r=run('weak.mp4');self.assertEqual(r.returncode,2);d=json.loads(r.stdout);self.assertAlmostEqual(d['outputSpanPx'][0],90,delta=2);self.assertTrue(d['possibleSuppressedMotion'])
 def test_new_project_carries_reference_tools(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=new_film(tmp)
   for name in ['measure_frame.mjs','measure_motion.py','APACHE-2.0.txt']:self.assertTrue((dest/name).is_file(),name)
   self.assertIn('refs/',(dest/'.gitignore').read_text())
 def test_licenses_and_asset_resolution(self):
  for p in ['LICENSE','assets/fonts/Inter-OFL.txt','assets/fonts/JetBrainsMono-OFL.txt','assets/fonts/InterVariable.woff2','assets/fonts/JetBrainsMono-Regular.ttf']:
   self.assertTrue((SKILL/p).is_file(),p);self.assertGreater((SKILL/p).stat().st_size,100)
if __name__=='__main__':unittest.main()
