#!/usr/bin/env python3
"""Measure a music track's beat grid against its kicks, then (optionally) lock the film to it.

  uv run --with librosa --with matplotlib python beats.py audio/track.mp3
  uv run --with librosa --with matplotlib python beats.py audio/track.mp3 --start 31.2 --apply

librosa's tracker can lock onto the off-beat or lag the attack. The grid is therefore refit to
constant tempo and phase-corrected against the steepest rises of the <120 Hz band (the kicks),
and the plot shows both grids over that band so a person can confirm it.
"""
from pathlib import Path
import argparse, json, math, subprocess, sys
import numpy as np
try:
 import librosa
 from scipy.signal import butter, find_peaks, sosfiltfilt
except ImportError:raise SystemExit('Requires librosa: uv run --with librosa --with matplotlib python beats.py ...')

SR=22050;HOP=512
def decode(path):
 """Decode with ffmpeg, the same decoder the renderer uses, so analysis and mix share one timebase."""
 raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-ac','1','-ar',str(SR),'-f','f32le','-'])
 return np.frombuffer(raw,dtype='<f4').astype(np.float64)

def fit_grid(times,period):
 """Least-squares constant-tempo grid t = phase + period*k through beat times, rejecting outliers."""
 times=np.asarray(times,float);phase=times[0];keep=np.ones(len(times),bool)
 for _ in range(4):
  k=np.round((times-phase)/period)
  A=np.vstack([np.ones(len(k)),k]).T
  (phase,period),*_=np.linalg.lstsq(A[keep],times[keep],rcond=None)
  resid=times-(phase+period*k);keep=np.abs(resid)<period*.2
  if keep.sum()<4:break
 return float(phase),float(period)

def grid_points(phase,period,duration):
 first=phase-math.floor(phase/period)*period
 return first+period*np.arange(int((duration-first)/period)+1)

class Kicks:
 """Kicks are picked from the <120 Hz band (steepest rises of its zero-phase envelope), then timed by the
 broadband attack just before: a kick that sweeps down from 150-300 Hz reaches the low band 10-40 ms late."""
 def __init__(self,y):
  low=sosfiltfilt(butter(4,120,'low',fs=SR,output='sos'),y)
  env=sosfiltfilt(butter(2,40,'low',fs=SR,output='sos'),np.abs(low))
  self.low=low;self.env=env;self.slope=np.gradient(env)*SR
  rise=np.maximum(self.slope,0);idx,_=find_peaks(rise,distance=int(.1*SR));h=rise[idx]
  keep=h>.3*np.percentile(h,95) if len(h) else np.zeros(0,bool)
  full=np.gradient(sosfiltfilt(butter(2,100,'low',fs=SR,output='sos'),np.abs(y)))
  def attack(i):a=max(0,i-int(.06*SR));b=min(len(full),i+int(.01*SR));return (a+int(np.argmax(full[a:b])))/SR
  self.t=np.array([attack(i) for i in idx[keep]]);self.w=h[keep]**2   # energy-like weight: kicks outvote softer bass and tom attacks

def refine(t,phase,period):
 """Least-squares tempo and phase through the attacks within an eighth of a beat of the grid."""
 for _ in range(3):
  k=np.round((t-phase)/period);keep=np.abs(t-(phase+period*k))<period/8
  if keep.sum()<8:break
  (phase,period),*_=np.linalg.lstsq(np.vstack([np.ones(int(keep.sum())),k[keep]]).T,t[keep],rcond=None)
 return float(phase),float(period)

def lock(t,w,period0):
 """Tempo and phase that make the kick attacks most coherent, searched within ±3% of librosa's tempo.
 The half-beat harmonic keeps the tempo measurable when kicks and an off-beat bass split the weight;
 the heavier of the two half-beat clusters becomes the beat (rival = lighter/heavier).
 Then refined through the attacks near the grid."""
 P=period0*np.linspace(.97,1.03,1201);E=np.exp(2j*np.pi*t[None,:]/P[:,None]);W=float(w.sum())
 z1=(w*E).sum(1)/W;z2=(w*E*E).sum(1)/W
 i=int(np.argmax(np.abs(z1)+np.abs(z2)));period=float(P[i])
 half=float(np.angle(z2[i])/(4*np.pi)*period)%(period/2)
 def weight(ph):frac=((t-ph)/period)%1;return float(w[np.minimum(frac,1-frac)<.125].sum())
 a,b=weight(half),weight(half+period/2);phase=half if a>=b else half+period/2;rival=min(a,b)/max(a,b,1e-12)
 phase,period=refine(t,phase,period)
 return phase,period,float(max(abs(z1[i]),abs(z2[i]))),rival

def offsets_ms(kick_t,lines):
 """Distance from each kick attack to the nearest grid line (or raw beat)."""
 if len(kick_t)==0:return {'median_abs_ms':None,'p90_abs_ms':None,'within_20ms':None}
 lines=np.sort(np.asarray(lines));i=np.searchsorted(lines,kick_t).clip(1,len(lines)-1)
 e=np.minimum(np.abs(kick_t-lines[i-1]),np.abs(kick_t-lines[i]))*1000
 return {'median_abs_ms':round(float(np.median(e)),1),'p90_abs_ms':round(float(np.percentile(e,90)),1),'within_20ms':round(float(np.mean(e<=20)),3)}

def analyze(path,film_beats=32,tempo_scale=1.0,anchor=None):
 y=decode(path);duration=len(y)/SR
 if duration<4:raise SystemExit('Track is too short to analyze')
 oenv=librosa.onset.onset_strength(y=y,sr=SR,hop_length=HOP)
 tempo,raw=librosa.beat.beat_track(onset_envelope=oenv,sr=SR,hop_length=HOP,units='time')
 raw=np.asarray(raw,float)
 if len(raw)<8:raise SystemExit('librosa found too few beats; this track may not have a steady pulse')
 period0=float(np.median(np.diff(raw)))
 phase_fit,period_fit=fit_grid(raw,period0)
 kicks=Kicks(y);warnings=[]
 raw_stats=offsets_ms(kicks.t,raw);fit_stats=offsets_ms(kicks.t,grid_points(phase_fit,period_fit,duration))
 phase,period=phase_fit,period_fit*tempo_scale;R=0.0;corrected=False;rival=0.0
 def on_grid(ph,P):f=((kicks.t-ph)/P)%1;return float(kicks.w[np.minimum(f,1-f)<.125].sum()/max(float(kicks.w.sum()),1e-12))
 if len(kicks.t)>=16:
  lp,lP,R,rv=lock(kicks.t,kicks.w,period)
  # Accept a clearly coherent lock, or a weaker one that explains the attacks at least as well as librosa's grid.
  if R>=.45 or (R>=.3 and on_grid(lp,lP)>=on_grid(phase,period)):phase,period,corrected,rival=lp,lP,True,rv
 if not corrected:warnings.append(f'No coherent kick pattern below 120 Hz ({len(kicks.t)} attacks, coherence {R:.2f}); grid is the librosa refit only. Inspect the plot.')
 if anchor is not None:phase,period=refine(kicks.t,anchor,period) if len(kicks.t)>=8 else (anchor,period)
 # An off-beat bassline can rival the kick below 120 Hz; then the heavier cluster may be the bass.
 # Two equal clusters can also mean kicks on every half beat, i.e. the tempo was halved.
 if corrected and rival>.5 and anchor is None:warnings.append(f'Strong low-band attacks also sit half a beat off the grid ({rival:.0%} of the on-grid weight: an off-beat bass, or kicks on every half beat). Confirm the black markers that are kicks sit on the green lines; if not, rerun with --anchor <time of a kick on beat one>, or --double if kicks fill every half beat.')
 grid=grid_points(phase,period,duration);final_stats=offsets_ms(kicks.t,grid)
 # Where the refit grid sits relative to the kick grid: about half a beat means the tracker took the off-beat.
 mid=grid_points(phase_fit,period_fit,duration);mid=mid[(mid>duration*.25)&(mid<duration*.75)]
 frac=((mid-phase)/period+.5)%1-.5;shift=float(np.median(frac))*period if len(mid) else 0.0
 if 60/period<75:warnings.append(f'{60/period:.1f} BPM is slow; if the track feels twice as fast (kick on 1 and 3, snare on 2 and 4), rerun with --double.')
 # Downbeat: new pitched energy (chords, bass notes above the kick) arrives on beat one of the bar.
 frames=librosa.time_to_frames(grid,sr=SR,hop_length=HOP)
 pitched=sosfiltfilt(butter(4,130,'high',fs=SR,output='sos'),y)
 chroma=np.log1p(10*librosa.feature.chroma_cqt(y=pitched,sr=SR,hop_length=HOP,fmin=librosa.note_to_hz('C3'),n_octaves=5,norm=None))
 sync=librosa.util.sync(chroma,frames,aggregate=np.mean)[:,1:len(grid)+1]
 n=min(sync.shape[1],len(grid));c=sync[:,:n]
 weight=np.r_[0,np.maximum(0,c[:,1:]-c[:,:-1]).sum(0)]
 weight=(weight-weight.mean())/(weight.std()+1e-9)
 scores=[float(weight[m::4].mean()) for m in range(4)];m=int(np.argmax(scores))
 order=sorted(scores,reverse=True)
 if anchor is not None:m=int(np.argmin(np.abs(grid-anchor)))%4
 elif order[0]-order[1]<.25:warnings.append(f'Downbeat is ambiguous (bar-phase scores {[round(s,2) for s in scores]}); confirm beat one in the plot or pass --anchor <time of beat one>.')
 downbeats=grid[m::4]
 # Candidate starts: downbeats whose following film window is loud, or that begin a rise (a drop).
 need=film_beats*period;rms=librosa.feature.rms(y=y,frame_length=2048,hop_length=HOP)[0]
 db=20*np.log10(rms+1e-9);tt=librosa.frames_to_time(np.arange(len(db)),sr=SR,hop_length=HOP)
 mean_db=lambda a,b:float(db[(tt>=a)&(tt<b)].mean()) if np.any((tt>=a)&(tt<b)) else -120.0
 cands=[{'start':round(float(d),4),'window_db':round(mean_db(d,d+need),2),'rise_db':round(mean_db(d,d+8*period)-mean_db(d-8*period,d),2) if d>=8*period else None} for d in downbeats if d+need<=duration-.05 and d>=0]
 loud=sorted(cands,key=lambda c:-c['window_db'])[:5];drops=sorted([c for c in cands if c['rise_db'] is not None],key=lambda c:-c['rise_db'])[:3]
 return {'track':str(path),'duration':round(duration,3),'film_beats':film_beats,
  'raw':{'bpm':round(60/period0,3),'librosa_tempo':round(float(np.atleast_1d(tempo)[0]),3),'beats':[round(float(x),4) for x in raw],'kick_offsets':raw_stats},
  'fit':{'phase':phase_fit,'period':period_fit,'kick_offsets':fit_stats},
  'grid':{'bpm':60/period,'spb':period,'phase':phase,'downbeat_phase':m,'first_downbeat':float(downbeats[0]),'bar_phase_scores':[round(s,3) for s in scores],'kick_offsets':final_stats},
  'correction':{'applied':corrected,'librosa_vs_kicks_ms':round(shift*1000,1),'offbeat_lock':corrected and abs(shift)>period/4,'tempo_error_pct':round((period_fit/period-1)*100,3),'coherence':round(R,3),'offbeat_rival':round(rival,3),'kick_attacks':int(len(kicks.t)),'anchor':anchor},
  'candidates':{'loudest':loud,'drops':drops},'warnings':warnings},(y,kicks,raw,grid,downbeats)

def plot(result,data,out,start=None):
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 y,kicks,raw,grid,downbeats=data;P=result['grid']['spb'];dur=result['duration']
 first=start if start is not None else (result['candidates']['loudest'][0]['start'] if result['candidates']['loudest'] else float(downbeats[0]))
 windows=[first,max(0,dur/2-2*P),max(0,first+result['film_beats']*P-4*P)]
 fig,axes=plt.subplots(3,1,figsize=(14,9))
 for ax,a in zip(axes,windows):
  b=min(dur,a+4*4*P);i0=int(a*SR);i1=int(b*SR);t=np.arange(i0,i1)/SR
  lo=kicks.low[i0:i1];scale=np.max(np.abs(lo))+1e-9
  ax.plot(t,lo/scale,color='#9aa3b5',lw=.6);ax.plot(t,kicks.env[i0:i1]/(np.max(kicks.env[i0:i1])+1e-9),color='#28324a',lw=1)
  for x in raw[(raw>=a)&(raw<b)]:ax.axvline(x,color='#d1495b',ls='--',lw=1)
  k=kicks.t[(kicks.t>=a)&(kicks.t<b)];ax.plot(k,np.zeros(len(k))-.9,'k^',ms=5)
  for x in grid[(grid>=a)&(grid<b)]:ax.axvline(x,color='#2a9d8f',lw=2.4 if np.min(np.abs(downbeats-x))<1e-6 else 1)
  ax.set_xlim(a,b);ax.set_yticks([]);ax.set_title(f'{a:.2f}-{b:.2f}s  <120 Hz waveform and envelope.  red dashed: librosa beats   green: kick-locked grid (thick = downbeat)   black: kick attacks',fontsize=9)
 axes[-1].set_xlabel('seconds in track');fig.tight_layout();out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=110);plt.close(fig)

def main():
 p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
 p.add_argument('track',type=Path);p.add_argument('--project',type=Path,help='project directory (default: this script\'s directory if it holds project.json)')
 p.add_argument('--start',type=float,help='track time for film t=0; snapped to the nearest downbeat');p.add_argument('--apply',action='store_true',help='write bpm and sound.music into project.json')
 p.add_argument('--anchor',type=float,help='track time of a kick you can see on beat one; the grid and bar are rebuilt through it')
 p.add_argument('--double',action='store_true',help='the track is twice as fast as detected');p.add_argument('--halve',action='store_true',help='the track is half as fast as detected')
 p.add_argument('--json',type=Path);p.add_argument('--plot',type=Path);a=p.parse_args()
 here=Path(__file__).resolve().parent;project=(a.project or (here if (here/'project.json').exists() else Path.cwd())).resolve();cfg_path=project/'project.json'
 cfg=json.loads(cfg_path.read_text()) if cfg_path.exists() else None
 film_beats=sum(s['beats'] for s in cfg['shots']) if cfg and cfg.get('shots') else 32
 result,data=analyze(a.track.resolve(),film_beats,.5 if a.double else 2.0 if a.halve else 1.0,a.anchor)
 downbeats=data[4];start=None
 if a.start is not None:
  start=float(downbeats[int(np.argmin(np.abs(downbeats-a.start)))]);result['snapped_start']=start
 out_json=a.json or project/'review/beats.json';out_plot=a.plot or project/'review/beats.png'
 out_json.parent.mkdir(parents=True,exist_ok=True);out_json.write_text(json.dumps(result,indent=1)+'\n');plot(result,data,out_plot,start)
 g=result['grid'];c=result['correction']
 print(json.dumps({'bpm':round(g['bpm'],4),'first_downbeat':round(g['first_downbeat'],4),'kick_offset_ms':{'librosa':result['raw']['kick_offsets']['median_abs_ms'],'refit':result['fit']['kick_offsets']['median_abs_ms'],'corrected':g['kick_offsets']['median_abs_ms']},
  'correction':c,'snapped_start':result.get('snapped_start'),'loudest_starts':[x['start'] for x in result['candidates']['loudest']],'drop_starts':[x['start'] for x in result['candidates']['drops']],'warnings':result['warnings'],'json':str(out_json),'plot':str(out_plot)},indent=1))
 if a.apply:
  if cfg is None:raise SystemExit(f'--apply needs a project.json in {project}')
  if start is None:raise SystemExit('--apply needs --start (pick one from the candidates and confirm it in the plot)')
  try:rel=a.track.resolve().relative_to(project).as_posix()
  except ValueError:raise SystemExit('Copy the track into the project (for example audio/) so the film stays self-contained')
  cfg.setdefault('sceneBpm',cfg['bpm']);cfg['bpm']=round(g['bpm'],6)
  sound=cfg.setdefault('sound',{});old=sound.get('music') or {}
  sound['music']={'file':rel,'start':round(start,6),'gain':old.get('gain',0),'fadeOut':old.get('fadeOut',.5),'source':old.get('source',''),'license':old.get('license','')}
  if sound.get('synth',True):sound['synth']=False;print('sound.synth set to false: the synthesized drums would fight the track. Re-enable it for a score written to sit on top.',file=sys.stderr)
  cfg_path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
  if not sound['music']['source'] or not sound['music']['license']:print('Fill sound.music.source and sound.music.license before building; build.py refuses unledgered audio.',file=sys.stderr)
if __name__=='__main__':main()
