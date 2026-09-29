#!/usr/bin/env python3
"""Create an editable, self-contained motion project without touching agent configuration."""
from pathlib import Path
import argparse,json,shutil,subprocess,sys
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('destination',type=Path);p.add_argument('--brand',default='NOVA');p.add_argument('--tagline',default='Make the extraordinary.');p.add_argument('--seed',default='NOVA-ORBIT-THREAD-2026')
a=p.parse_args();dest=a.destination.expanduser().resolve();skill=Path(__file__).resolve().parents[1]
if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):p.error('Destination must be absent or empty')
shutil.copytree(skill/'assets/template',dest,dirs_exist_ok=True)
shutil.copy2(skill/'assets/engine.html',dest/'engine.html')
shutil.copytree(skill/'assets/fonts',dest/'fonts',dirs_exist_ok=True)
for name in ['render.mjs','verify.py','review.py']:shutil.copy2(skill/'scripts'/name,dest/name)
cfg=json.loads((dest/'project.json').read_text());cfg.update(name=a.brand,tagline=a.tagline,seed=a.seed);(dest/'project.json').write_text(json.dumps(cfg,indent=2)+'\n')
(dest/'.gitignore').write_text('out/\nreview/\nreel.html\ncheck.js\n__pycache__/\n.DS_Store\n')
(dest/'BRIEF.md').write_text(f'# {a.brand}\n\nMessage: {a.tagline}\n\nStarter: a 15-second landscape motion reel. Replace this with the actual audience, premise, visual handoffs, density rhythm and sound role before substantial creative changes.\n')
subprocess.run([sys.executable,str(dest/'build.py')],check=True)
print(f'Project ready: {dest}\nNext: node render.mjs doctor, then render representative stills.')
