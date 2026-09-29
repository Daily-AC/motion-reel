"""Meaningful packaging checks. Real rendering and visual review remain separate."""
from pathlib import Path
import json,subprocess,tempfile,unittest,sys
ROOT=Path(__file__).resolve().parents[1];SKILL=ROOT/'skills/motion-reel'
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
   cfg=json.loads((dest/'project.json').read_text());cfg['bpm']=130;(dest/'project.json').write_text(json.dumps(cfg))
   r=subprocess.run([sys.executable,str(dest/'build.py')],capture_output=True);self.assertNotEqual(r.returncode,0)
 def test_licenses_and_asset_resolution(self):
  for p in ['LICENSE','assets/fonts/Inter-OFL.txt','assets/fonts/JetBrainsMono-OFL.txt','assets/fonts/InterVariable.woff2','assets/fonts/JetBrainsMono-Regular.ttf']:
   self.assertTrue((SKILL/p).is_file(),p);self.assertGreater((SKILL/p).stat().st_size,100)
if __name__=='__main__':unittest.main()
