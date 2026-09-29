"""Build a standalone local composition from its editable sources."""
from pathlib import Path
import json, math
root=Path(__file__).resolve().parent
cfg=json.loads((root/'project.json').read_text())
for key in ['width','height','fps','bpm','bars']:
 if not isinstance(cfg.get(key),(int,float)) or cfg[key]<=0:raise SystemExit(f'Invalid {key}')
if any(int(cfg[k])!=cfg[k] for k in ['width','height','fps','bars']):raise SystemExit('Canvas, fps and bars must be integers')
if cfg['width']%2 or cfg['height']%2:raise SystemExit('H.264 canvas dimensions must be even')
frames=cfg['bars']*4*60/cfg['bpm']*cfg['fps']
if abs(frames-round(frames))>1e-6:raise SystemExit('Timing must produce an integral output frame count')
html=(root/'engine.html').read_text()
values={'CONFIG_JSON':json.dumps(cfg,ensure_ascii=True).replace('<','\\u003c'),'SYMBOL_JS':(root/'symbol.js').read_text(),'SCENES_JS':(root/'scenes.js').read_text(),'SCORE_JS':(root/'score.js').read_text()}
for name,value in values.items():
 token='{{'+name+'}}'
 if html.count(token)!=1:raise SystemExit(f'Expected exactly one {token} in engine.html')
 html=html.replace(token,value)
(root/'reel.html').write_text(html)
(root/'check.js').write_text(html.split('<script>')[1].split('</script>')[0])
print(f'Built {cfg["name"]}: {frames/cfg["fps"]:.3f}s / {round(frames)} frames')
