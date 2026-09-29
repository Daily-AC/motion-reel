#!/usr/bin/env python3
"""Decode labelled contact sheets or motion strips from the actual MP4."""
from pathlib import Path
import argparse,io,json,subprocess
try:from PIL import Image,ImageDraw,ImageFont
except ImportError:raise SystemExit('Pillow is required: uv run --with pillow python review.py ...')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('video',type=Path);g=p.add_mutually_exclusive_group();g.add_argument('--times');g.add_argument('--strip',help='start:end:samples-per-second');p.add_argument('--output',type=Path);a=p.parse_args()
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',str(a.video)]));duration=float(info['format']['duration'])
if a.strip:
 start,end,rate=map(float,a.strip.split(':'))
 if rate<=0 or end<=start:raise SystemExit('Strip requires start<end and positive rate')
 times=[start+i/rate for i in range(int((end-start)*rate)+1)]
elif a.times:times=list(map(float,a.times.split(',')))
else:times=[i*duration/11 for i in range(11)]+[max(0,duration-1/60)]
if not times or len(times)>240 or min(times)<0 or max(times)>=duration:raise SystemExit('Use1–240 timestamps inside the video duration')
width=480 if not a.strip else 320;cols=4 if not a.strip else 5
images=[]
for t in times:
 data=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(a.video),'-frames:v','1','-vf',f'scale={width}:-2','-f','image2pipe','-vcodec','png','-']);images.append(Image.open(io.BytesIO(data)).convert('RGB'))
height=images[0].height;sheet=Image.new('RGB',(cols*width,((len(images)+cols-1)//cols)*(height+30)),(25,29,39));draw=ImageDraw.Draw(sheet)
font_path=Path(__file__).resolve().parent/'fonts/JetBrainsMono-Regular.ttf'
try:font=ImageFont.truetype(str(font_path),16)
except OSError:font=ImageFont.load_default()
for i,(t,image) in enumerate(zip(times,images)):
 x=i%cols*width;y=i//cols*(height+30);sheet.paste(image,(x,y));draw.text((x+9,y+height+6),f'{t:.3f}s',fill='white',font=font)
out=a.output or Path('review')/(a.video.stem+('-strip.png' if a.strip else '-contact.png'));out.parent.mkdir(parents=True,exist_ok=True);sheet.save(out);print(out)
