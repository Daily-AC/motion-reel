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
 def test_licenses_and_asset_resolution(self):
  for p in ['LICENSE','assets/fonts/Inter-OFL.txt','assets/fonts/JetBrainsMono-OFL.txt','assets/fonts/InterVariable.woff2','assets/fonts/JetBrainsMono-Regular.ttf']:
   self.assertTrue((SKILL/p).is_file(),p);self.assertGreater((SKILL/p).stat().st_size,100)
if __name__=='__main__':unittest.main()
