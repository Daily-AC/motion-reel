#!/usr/bin/env python3
"""Prepare the mixed 2D/3D example: a 2D panel, the same panel on a three.js monitor, a reaction shot, a 2D end card."""
from pathlib import Path
import argparse,json,subprocess,sys,shutil
p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent;repo=here.parents[1];dest=a.destination.resolve()
subprocess.run([sys.executable,str(repo/'skills/motion-reel/scripts/new_project.py'),str(dest),'--brand','NOVA'],check=True)
for name in ['scenes.js','score.js']:shutil.copy2(here/name,dest/name)
cfg=json.loads((dest/'project.json').read_text())
cfg.update(bpm=120,sceneBpm=120,shots=[
 {'scene':'card','beats':4,'label':'PANEL','hit':0,'hud':None,'copy':{'title':'Render the film','subtitle':'Two shots in 2D, two in three.js, one timeline.','button':'RUN','running':'RENDERING'}},
 {'scene':'screen','beats':2,'label':'SCREEN','hit':0,'hud':None},
 {'scene':'react','beats':4,'label':'REACTION','hit':8,'hud':'paper'},
 {'scene':'end','beats':4,'label':'END','hit':10,'hud':None}])
(dest/'project.json').write_text(json.dumps(cfg,indent=2)+'\n')
subprocess.run([sys.executable,str(dest/'build.py')],check=True)
print('Prepared the mixed 2D/3D example.')
