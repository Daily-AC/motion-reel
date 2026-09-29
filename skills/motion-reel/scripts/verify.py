#!/usr/bin/env python3
"""Validate the encoded signals; report visual candidates without pretending to grade taste."""
from pathlib import Path
from array import array
import argparse,json,math,subprocess,sys
p=argparse.ArgumentParser(description=__doc__);p.add_argument('video',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();video=a.video.resolve()
def run(*args):return subprocess.check_output(args)
meta_path=video.with_suffix('.render.json')
if not meta_path.exists():raise SystemExit('Missing render metadata. Supply the .render.json produced by the renderer.')
expected=json.loads(meta_path.read_text());probe=json.loads(run('ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(video)))
v=next(x for x in probe['streams'] if x['codec_type']=='video');audio=next((x for x in probe['streams'] if x['codec_type']=='audio'),None)
errors=[]
def check(ok,message):
 if not ok:errors.append(message)
check([v['width'],v['height']]==[expected['width'],expected['height']],'dimensions mismatch')
num,den=map(int,v['avg_frame_rate'].split('/'));check(abs(num/den-expected['fps'])<1e-6,'fps mismatch')
check(int(v['nb_read_frames'])==expected['frames'],'decoded frame count mismatch')
check(abs(float(probe['format']['duration'])-expected['duration'])<1/expected['fps'],'duration mismatch')
check(all(v.get(x)=='bt709' for x in ['color_space','color_transfer','color_primaries']),'BT.709 metadata missing')
report={'file':video.name,'expected':expected,'decoded_video_frames':int(v['nb_read_frames']),'errors':errors,'warnings':[],'visual_review_required':True,'listening_review':'not performed by this script'}
if expected['audio']:
 check(audio is not None,'soundtrack missing')
 if audio:
  check(audio['channels']==2 and audio['sample_rate']=='48000','audio must be stereo48kHz')
  r=subprocess.run(['ffmpeg','-hide_banner','-i',str(video),'-map','0:a','-af','loudnorm=I=-14:TP=-1:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True,check=True).stderr
  m=json.loads(r[r.rfind('{'):r.rfind('}')+1]);report['audio']={k:float(m[k]) for k in ['input_i','input_tp','input_lra']}
  check(-15.5<=float(m['input_i'])<=-12.5,'loudness is outside reference -14LUFS range');check(float(m['input_tp'])<=-1,'AAC true peak exceeds -1dBTP')
# Flat intervals need visual interpretation, not automatic rejection.
raw=run('ffmpeg','-v','error','-i',str(video),'-vf','scale=128:72','-pix_fmt','gray','-f','rawvideo','-');size=128*72
check(len(raw)//size==expected['frames'],'full decode frame count mismatch')
flat=[];black=[];first_last=[]
for i in range(len(raw)//size):
 x=raw[i*size:(i+1)*size];mean=sum(x)/size;variance=sum(v*v for v in x)/size-mean*mean
 flat.append(variance<16);black.append(mean<25 and max(x)<35)
 if i in [0,len(raw)//size-1]:first_last.append({'frame':i,'mean':round(mean,3),'std':round(math.sqrt(max(0,variance)),3)})
def intervals(flags):
 spans=[];start=None
 for i,b in enumerate(flags+[False]):
  if b and start is None:start=i
  if not b and start is not None:spans.append({'start_frame':start,'end_frame_exclusive':i,'start_seconds':start/expected['fps'],'duration_seconds':(i-start)/expected['fps']});start=None
 return spans
report.update(first_last_frames=first_last,flat_intervals=intervals(flat),near_black_intervals=intervals(black))
if any(black):report['warnings'].append('Near-black frames require inspection; an intentional transition may be valid.')
source=video.with_suffix('.source.wav')
if expected['audio'] and audio and source.exists():
 def envelope(path):
  b=run('ffmpeg','-v','error','-i',str(path),'-vn','-ac','1','-ar','48000','-f','f32le','-');x=array('f');x.frombytes(b)
  if sys.byteorder!='little':x.byteswap()
  return [math.sqrt(sum(y*y for y in x[i:i+240])/240) for i in range(0,len(x)-239,240)]
 x,y=envelope(source),envelope(video);n=min(len(x),len(y));x=x[:n];y=y[:n]
 def correlation(a,b):
  ma=sum(a)/len(a);mb=sum(b)/len(b);va=sum((v-ma)**2 for v in a);vb=sum((v-mb)**2 for v in b)
  return sum((u-ma)*(v-mb) for u,v in zip(a,b))/math.sqrt(va*vb) if va*vb else 0
 candidates=[]
 for lag in range(-8,9):
  aa,bb=(x[-lag:],y[:n+lag]) if lag<0 else (x[:n-lag],y[lag:]) if lag>0 else (x,y);candidates.append((correlation(aa,bb),lag))
 corr,lag=max(candidates);report['mux_sync']={'offset_ms':lag*5,'envelope_correlation':corr};check(abs(lag*5)<=20 and corr>.95,'source/encoded soundtrack timing differs')
report['technical_ok']=not errors
out=a.output or video.with_suffix('.verify.json');out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'technical_ok':report['technical_ok'],'frames':report['decoded_video_frames'],'errors':errors,'warnings':report['warnings'],'report':str(out)},indent=2))
sys.exit(0 if not errors else 1)
