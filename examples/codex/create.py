#!/usr/bin/env python3
"""Prepare the Codex case study using the same public renderer and original scene sources."""
from pathlib import Path
import argparse,json,subprocess,sys,shutil
p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent;repo=here.parents[1];dest=a.destination.resolve()
subprocess.run([sys.executable,str(repo/'skills/motion-reel/scripts/new_project.py'),str(dest),'--brand','CODEX','--tagline','把想象，变成现实。'],check=True)
shutil.copy2(here/'scenes.js',dest/'scenes.js');shutil.copy2(here/'contours.js',dest/'symbol.js')
cfg=json.loads((dest/'project.json').read_text());cfg.update(displayFont='system-ui',seed='NF3SQU86SFW7L6L2NXKGDXZX47SA8ZFUUVXXB7C6ZE6TVGN3',opening=['把想象，','推向现实。'],credit='EVERY FRAME. WRITTEN BY CODEX.')
(dest/'project.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
subprocess.run([sys.executable,str(dest/'build.py')],check=True)
print('Prepared Codex case study. Its original Chinese typography requires a compatible local CJK font; macOS is the reference environment.')
