#!/usr/bin/env python3
"""Generate reproducible form/action associations, then let the director select useful ones."""
import argparse,hashlib,json,secrets
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seed');p.add_argument('--output',type=Path);a=p.parse_args()
seed=a.seed or ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(48))
if not seed:raise SystemExit('Seed cannot be empty')
lengths=[3,5,4,7,3,6,5,4,6,5];groups=[];at=0
while at<len(seed):
 n=lengths[len(groups)%len(lengths)];groups.append(seed[at:at+n]);at+=n
forms=['thread','constellation','paper fold','lens','wave','fabric','architecture','tuning fork','particles','glyph','orbit','bridge']
actions=['weave','resonate','draw forward','fold','illuminate','gather','orbit','penetrate','branch','grow','echo','focus']
ideas=[]
for i,g in enumerate(groups):
 h=hashlib.sha256((g+groups[(i+1)%len(groups)][::-1]).encode()).digest();ideas.append({'fragment':g,'association':forms[h[0]%len(forms)]+' × '+actions[h[1]%len(actions)]})
result={'seed':seed,'algorithm':'alternating lengths, next group reversed, SHA-256 vocabulary lookup','ideas':ideas,'selection_rule':'Choose a few associations that support the brief; reject the rest. Randomness is not a quality score.'}
out=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(out)
else:print(out,end='')
