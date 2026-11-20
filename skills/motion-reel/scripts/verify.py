#!/usr/bin/env python3
"""Validate the encoded signals; report visual candidates without pretending to grade taste."""
from pathlib import Path
from array import array
import argparse,itertools,json,math,operator,re,statistics,subprocess,sys
p=argparse.ArgumentParser(description=__doc__);p.add_argument('video',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();video=a.video.resolve()
def run(*args):return subprocess.check_output(args)
def pcm(path,af='anull',channels=1):
 x=array('f');x.frombytes(run('ffmpeg','-v','error','-i',str(path),'-vn','-af',af,'-ac',str(channels),'-ar','48000','-f','f32le','-'))
 if sys.byteorder!='little':x.byteswap()
 return x
def loudness(af='anull'):
 r=subprocess.run(['ffmpeg','-hide_banner','-i',str(video),'-map','0:a','-af',af+',loudnorm=I=-14:TP=-1:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True,check=True).stderr
 return json.loads(r[r.rfind('{'):r.rfind('}')+1])
MONO='pan=mono|c0=0.5*c0+0.5*c1';LOW='lowpass=f=120,areverse,lowpass=f=120,areverse'  # forward+backward biquad = zero-phase <120 Hz
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
report={'file':video.name,'expected':expected,'decoded_video_frames':int(v['nb_read_frames']),'errors':errors,'warnings':[],'visual_review_required':True,'listening_review':'no soundtrack to audition'}
if 'assets' in expected:
 report['assets']=expected['assets']
 for i,x in enumerate(expected['assets']):check(bool(x.get('source')) and bool(x.get('license')),f"asset {i} ({x.get('file','?')}) is missing source or license")
if expected['audio']:
 check(audio is not None,'soundtrack missing')
 if audio:
  check(audio['channels']==2 and audio['sample_rate']=='48000','audio must be stereo48kHz')
  m=loudness();report['audio']={k:float(m[k]) for k in ['input_i','input_tp','input_lra']}
  check(-15.5<=float(m['input_i'])<=-12.5,'loudness is outside reference -14LUFS range');check(float(m['input_tp'])<=-1,'AAC true peak exceeds -1dBTP')
  # BS.1770 sums channel power: L=R folds down with 0 dB loss, uncorrelated L/R with ~3 dB, so >3 dB means real cancellation.
  # A -inf mono reading is clamped to the -70 LUFS absolute gate so the loss stays a finite lower bound.
  mono_i=max(-70.0,float(loudness(MONO)['input_i']));loss=round(float(m['input_i'])-3.01-mono_i,2)
  x=pcm(video,channels=2);left,right=x[0::2],x[1::2];win=19200;windows=[]
  for i in range(0,len(left)-win+1,win//2):
   l,r=left[i:i+win],right[i:i+win];ll=sum(map(operator.mul,l,l));rr=sum(map(operator.mul,r,r))
   windows.append({'t':round(i/48000,3),'correlation':round(sum(map(operator.mul,l,r))/math.sqrt(ll*rr),3) if ll*rr else 0.0,'power':(ll+rr)/2/win})
  top=max([w['power'] for w in windows]+[0])  # near-silent: under -60 dBFS or 30 dB below the loudest window
  loud=[w for w in windows if w['power']>=max(1e-6,top*1e-3)]
  for w in windows:pw=w.pop('power');w['rms_db']=round(10*math.log10(pw),1) if pw else -120.0
  report['mono']={'stereo_i':float(m['input_i']),'mono_i':mono_i,'loss_db':loss,'min_correlation':min([w['correlation'] for w in loud],default=None),'negative_windows':[w for w in loud if w['correlation']<-.2],'window_seconds':.4,'hop_seconds':.2}
  check(loss<=3,f'mono fold-down loses {loss} dB (>3 dB: channels cancel)');check(all(w['correlation']>=-.5 for w in loud),'energetic window with L/R correlation below -0.5 (anti-phase)')
  if 1.5<loss<=3:report['warnings'].append(f'mono fold-down loses {loss} dB; check the mix on a mono speaker')
# Flat intervals need visual interpretation, not automatic rejection.
raw=run('ffmpeg','-v','error','-i',str(video),'-vf','scale=128:72','-pix_fmt','gray','-f','rawvideo','-');size=128*72;fps=expected['fps']
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
  x=pcm(path);return [math.sqrt(sum(y*y for y in x[i:i+240])/240) for i in range(0,len(x)-239,240)]
 x,y=envelope(source),envelope(video);n=min(len(x),len(y));x=x[:n];y=y[:n]
 def correlation(a,b):
  ma=sum(a)/len(a);mb=sum(b)/len(b);va=sum((v-ma)**2 for v in a);vb=sum((v-mb)**2 for v in b)
  return sum((u-ma)*(v-mb) for u,v in zip(a,b))/math.sqrt(va*vb) if va*vb else 0
 candidates=[]
 for lag in range(-8,9):
  aa,bb=(x[-lag:],y[:n+lag]) if lag<0 else (x[:n-lag],y[lag:]) if lag>0 else (x,y);candidates.append((correlation(aa,bb),lag))
 corr,lag=max(candidates);report['mux_sync']={'offset_ms':lag*5,'envelope_correlation':corr};check(abs(lag*5)<=20 and corr>.95,'source/encoded soundtrack timing differs')
if expected['audio'] and audio:
 # Cut sync from the encoded file. The visual cut is the frame within ±3 frames of the cue with the most prominent spike in
 # pixels that start changing (>4 levels at 128x72 gray after being still on the previous frame). Raw frame-difference peaks
 # land 1-3 frames off on animated transitions: an outgoing sweep or growing burst moves more pixels than the cut, but as a ramp.
 # Audio onset, from the zero-phase <120 Hz band (L+R power, so phase problems cannot hide a hit): the hit is the largest
 # linear rise of a 40 ms RMS envelope within ±spb/2 of that frame (a kick on top of a fill or sustained bass rises in energy
 # but barely in dB); it is timed by the steepest dB rise of a 10 ms RMS envelope in the 60 ms before and 10 ms after it.
 frames=len(raw)//size
 def started(k):
  if k<1 or k>=frames:return 0
  f,g,h=raw[k*size:(k+1)*size],raw[(k-1)*size:k*size],raw[max(0,k-2)*size:max(1,k-1)*size];return sum(abs(x-y)>4 and abs(y-z)<=4 for x,y,z in zip(f,g,h))
 spb=expected.get('spb') or .5;low=pcm(video,LOW,2);sq=array('d',[0.0]);sq.extend(itertools.accumulate(y*y for y in low));n=len(low)//2
 env=[math.sqrt(max(0,sq[2*min(n,i+240)]-sq[2*max(0,i-240)])/960) for i in range(0,n,48)];top=max(env,default=0)
 wide=[math.sqrt(max(0,sq[2*min(n,i+960)]-sq[2*max(0,i-960)])/3840) for i in range(0,n,48)]
 db=[20*math.log10(max(e,top*.01,1e-9)) for e in env];shift=float(audio.get('start_time') or 0)-float(v.get('start_time') or 0);cuts=[];start=None
 for cue in [c for c in expected.get('cues',[]) if c['kind']=='cut']:
  c=round(cue['t']*fps);s={k:started(k) for k in range(c-4,c+5)}
  kv=0 if c<=0 else max(range(max(1,c-3),min(frames-1,c+3)+1),key=lambda k:s[k]-max(s[k-1],s[k+1]));vc=kv/fps
  # A shot boundary inside one continuous move changes no pixels (real cuts here start 60+ of 9216 at once): nothing to sync to.
  if c>0 and s[kv]-max(s[kv-1],s[kv+1])<20:cuts.append({'cue':cue['t'],'shot':cue.get('shot'),'visual_cut':None,'audio_onset':None,'offset_ms':None,'note':'no picture change at this cue: continuous shot boundary, not checked'});continue
  lo=max(20,round((vc-spb/2-shift)*1000));hi=min(len(wide)-21,round((vc+spb/2-shift)*1000))
  k=max(range(lo,hi+1),key=lambda i:wide[i+20]-wide[i-20]) if hi>=lo else None
  j=max(range(max(3,k-60),min(len(env)-4,k+10)+1),key=lambda i:db[i+3]-db[i-3]) if k is not None else None
  # A real onset rises by at least a tenth of the loudest low-band level and peaks within 20 dB of it and above -40 dBFS RMS.
  on=j/1000+shift if j is not None and wide[k+20]-wide[k-20]>=.1*top and max(env[j:j+51])>=max(.1*top,.01) else None
  row={'cue':cue['t'],'shot':cue.get('shot'),'visual_cut':round(vc,4),'audio_onset':None if on is None else round(on,4),'offset_ms':None if on is None else round((vc-on)*1000,1)}
  # Sound cannot lead frame 0 and a hit there may be clipped, so the film-start cue is reported but not gated.
  if c<=0:start=row;continue
  cuts.append(row)
  # ITU-R BT.1359 detectability: sound >45 ms before picture or >125 ms after it.
  if on is not None:o=row['offset_ms'];check(o<=45,f"sound leads picture by {o} ms at cut {cue['t']}s (limit 45 ms)");check(o>=-125,f"sound trails picture by {-o} ms at cut {cue['t']}s (limit 125 ms)")
 offs=[abs(c['offset_ms']) for c in cuts if c['offset_ms'] is not None]
 report['cut_sync']={'sign':'positive offset_ms = picture after sound','film_start':start,'cuts':cuts,'median_abs_ms':statistics.median(offs) if offs else None,'max_abs_ms':max(offs,default=None),'no_onset':[c['cue'] for c in cuts if c['visual_cut'] is not None and c['audio_onset'] is None],'no_picture_change':[c['cue'] for c in cuts if c['visual_cut'] is None]}
 # Listening checklist: strongest candidate per concern, substituting the next one when it lands within 1 s of an earlier pick.
 r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(video),'-map','0:a','-af','ebur128=framelog=info','-f','null','-'],capture_output=True,text=True,check=True).stderr
 moments=sorted(((float(m),float(t)) for t,m in re.findall(r't:\s*([\d.]+)\s.*?M:\s*(-?[\d.]+)',r) if float(m)>-70),reverse=True)
 duration=expected['duration'];chosen={}
 for name,cands in [('opening',[(0.0,'opening second: is there sound from frame 0 with no dead air or click, and is the hook clear?')]),
  ('ending',[(max(0,duration-1.5),'final 1.5 s: does the ending resolve or fade cleanly, with no abrupt cut-off or tail click?')]),
  ('loudest',[(max(0,t-.4),f'#{i+1} loudest 400 ms (momentary {m:.1f} LUFS): clipping, crackle, pumping or audible limiting') for i,(m,t) in enumerate(moments)]),
  ('mono',[(w['t'],f"#{i+1} lowest L/R correlation ({w['correlation']:+.2f}): compare stereo with a mono speaker; elements going hollow or vanishing") for i,w in enumerate(sorted(loud,key=lambda w:w['correlation']))]),
  ('sync',[(c['cue'],f"#{i+1} largest sync offset, cut {c['shot']} at {c['offset_ms']:+.0f} ms (+ = sound first): does the hit land on the picture change?") for i,c in enumerate(sorted([c for c in cuts if c['offset_ms'] is not None],key=lambda c:-abs(c['offset_ms'])))]+[(c['cue'],f"cut {c['shot']} has no low-band onset: is there a hit, and does it land on the picture change?") for c in cuts if c['visual_cut'] is not None and c['offset_ms'] is None])]:
  chosen[name]=next((x for x in cands if all(abs(x[0]-t)>=1 for t,_ in chosen.values())),cands[0] if cands else (duration/2,f'no {name} candidate was measured: listen to the middle of the film'))
 report['listening_checklist']=[{'t':round(chosen[n][0],3),'listen_for':chosen[n][1]} for n in ['loudest','mono','sync','opening','ending']]
 report['listening_review']='NOT PERFORMED: an agent cannot hear. A human must audition the 5 listening_checklist timestamps on headphones (and once summed to mono) before sign-off; nothing here means it sounds good.'
report['technical_ok']=not errors
out=a.output or video.with_suffix('.verify.json');out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
summary={'technical_ok':report['technical_ok'],'frames':report['decoded_video_frames'],'errors':errors,'warnings':report['warnings'],'report':str(out)}
if 'mono' in report:summary['mono']={k:report['mono'][k] for k in ['loss_db','min_correlation']}|{'negative_windows':[w['t'] for w in report['mono']['negative_windows']]}
if 'cut_sync' in report:s=report['cut_sync'];summary['cut_sync']={'offsets_ms':{str(c['cue']):c['offset_ms'] if c['offset_ms'] is not None else 'no_onset' if c['visual_cut'] is not None else 'no_picture_change' for c in s['cuts']},'median_abs_ms':s['median_abs_ms'],'max_abs_ms':s['max_abs_ms'],'film_start_ms':s['film_start'] and s['film_start']['offset_ms']}
if 'listening_checklist' in report:summary['listening_checklist']=report['listening_checklist']
summary['listening_review']=report['listening_review'];print(json.dumps(summary,indent=2))
sys.exit(0 if not errors else 1)
