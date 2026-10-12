#!/usr/bin/env python3
"""Decode labelled contact sheets, motion strips or per-cue frame/waveform rows from the actual MP4."""
from pathlib import Path
from array import array
import argparse,io,json,math,subprocess,sys
try:from PIL import Image,ImageDraw,ImageFont
except ImportError:raise SystemExit('Pillow is required: uv run --with pillow python review.py ...')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('video',type=Path);g=p.add_mutually_exclusive_group();g.add_argument('--times');g.add_argument('--strip',help='start:end:samples-per-second');g.add_argument('--cues',action='store_true',help='one row per .render.json cue: frame before, frame after, ±0.5 s waveform');p.add_argument('--output',type=Path);a=p.parse_args()
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(a.video)]));duration=float(info['format']['duration'])
def decode(t,width):
 data=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(a.video),'-frames:v','1','-vf',f'scale={width}:-2','-f','image2pipe','-vcodec','png','-']);return Image.open(io.BytesIO(data)).convert('RGB')
font_path=Path(__file__).resolve().parent/'fonts/JetBrainsMono-Regular.ttf'
try:font=ImageFont.truetype(str(font_path),16)
except OSError:font=ImageFont.load_default()
if a.cues:
 meta_path=a.video.with_suffix('.render.json')
 if not meta_path.exists():raise SystemExit('--cues needs the .render.json produced by the renderer next to the MP4')
 meta=json.loads(meta_path.read_text());fps=meta['fps'];cues=meta.get('cues') or []
 if not cues:raise SystemExit('render.json has no cues')
 def pcm(af):
  x=array('f');x.frombytes(subprocess.check_output(['ffmpeg','-v','error','-i',str(a.video),'-vn','-af',af,'-ac','1','-ar','48000','-f','f32le','-']))
  if sys.byteorder!='little':x.byteswap()
  return x
 mono='pan=mono|c0=0.5*c0+0.5*c1';full=pcm(mono);low=pcm(mono+',lowpass=f=120,areverse,lowpass=f=120,areverse');scale=max(map(abs,full),default=0) or 1
 streams={s['codec_type']:float(s.get('start_time') or 0) for s in info['streams']};shift=streams.get('audio',0)-streams.get('video',0)
 fw,ww=480,640;fh=decode(0,fw).height;rh=fh+30;sheet=Image.new('RGB',(2*fw+ww,len(cues)*rh),(25,29,39));draw=ImageDraw.Draw(sheet)
 for row,cue in enumerate(cues):
  y=row*rh;t=cue['t'];ks=[math.floor(round((t+d/fps)*fps,6)) for d in (-1,1)]
  for col,k in enumerate(ks):
   if 0<=k<meta['frames']:sheet.paste(decode(max(0,(k-.5)/fps),fw),(col*fw,y))
   else:draw.text((col*fw+9,y+fh//2),'outside the film',fill=(150,150,160),font=font)
  x0=2*fw;mid=y+fh//2;draw.rectangle([x0,y,x0+ww-1,y+fh-1],fill=(14,17,24));draw.line([x0,mid,x0+ww-1,mid],fill=(45,50,62))
  for signal,colour in [(full,(125,145,190)),(low,(255,150,60))]:
   for px in range(ww):
    i0=round((t-.5-shift+px/ww)*48000);i1=max(i0+1,round((t-.5-shift+(px+1)/ww)*48000));seg=signal[max(0,i0):max(0,min(len(signal),i1))]
    if seg:draw.line([x0+px,mid-max(seg)/scale*(fh/2-4),x0+px,mid-min(seg)/scale*(fh/2-4)],fill=colour)
  draw.line([x0+ww//2,y,x0+ww//2,y+fh-1],fill='white')
  what=cue.get('shot') if cue['kind']=='cut' else cue.get('name')
  draw.text((9,y+fh+6),f"{t:.3f}s {cue['kind']} {what}",fill='white',font=font);draw.text((fw+9,y+fh+6),f'frames {ks[0]} | {ks[1]}',fill='white',font=font)
  draw.text((x0+9,y+fh+6),'±0.5 s  full band',fill=(125,145,190),font=font);draw.text((x0+210,y+fh+6),'<120 Hz',fill=(255,150,60),font=font);draw.text((x0+300,y+fh+6),'line = cue',fill='white',font=font)
 out=a.output or Path('review')/(a.video.stem+'-cues.png');out.parent.mkdir(parents=True,exist_ok=True);sheet.save(out);print(out);sys.exit()
if a.strip:
 start,end,rate=map(float,a.strip.split(':'))
 if rate<=0 or end<=start:raise SystemExit('Strip requires start<end and positive rate')
 times=[start+i/rate for i in range(int((end-start)*rate)+1)]
elif a.times:times=list(map(float,a.times.split(',')))
else:times=[i*duration/11 for i in range(11)]+[max(0,duration-1/60)]
if not times or len(times)>240 or min(times)<0 or max(times)>=duration:raise SystemExit('Use1–240 timestamps inside the video duration')
width=480 if not a.strip else 320;cols=4 if not a.strip else 5
images=[decode(t,width) for t in times]
height=images[0].height;sheet=Image.new('RGB',(cols*width,((len(images)+cols-1)//cols)*(height+30)),(25,29,39));draw=ImageDraw.Draw(sheet)
for i,(t,image) in enumerate(zip(times,images)):
 x=i%cols*width;y=i//cols*(height+30);sheet.paste(image,(x,y));draw.text((x+9,y+height+6),f'{t:.3f}s',fill='white',font=font)
out=a.output or Path('review')/(a.video.stem+('-strip.png' if a.strip else '-contact.png'));out.parent.mkdir(parents=True,exist_ok=True);sheet.save(out);print(out)
