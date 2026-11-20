#!/usr/bin/env node
// Page-driven RGBA capture, owned browser lifecycle and explicit color/audio encoding.
import http from 'node:http';
import {readFileSync,writeFileSync,mkdirSync,mkdtempSync,rmSync,existsSync} from 'node:fs';
import {spawn,spawnSync} from 'node:child_process';
import {resolve,join,dirname,sep,isAbsolute} from 'node:path';
import {tmpdir} from 'node:os';
import {randomBytes} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {once} from 'node:events';
const ROOT=dirname(fileURLToPath(import.meta.url));
const raw=process.argv.slice(2),mode=raw.shift()||'render',opts={},positionals=[];
for(let i=0;i<raw.length;i++){
 const arg=raw[i];if(!arg.startsWith('--')){positionals.push(arg);continue}
 const [name,value]=arg.slice(2).split('=');if(!['out','scale','samples','browser'].includes(name))throw new Error('Unknown flag: '+arg);
 opts[name]=value??raw[++i];if(opts[name]===undefined)throw new Error('Missing value: '+arg);
}
const run=(cmd,args,extra={})=>{const r=spawnSync(cmd,args,{encoding:'utf8',...extra});if(r.error||r.status!==0)throw new Error(`${cmd} failed: ${r.error?.message||r.stderr||r.stdout}`);return r.stdout;};
function browserPath(){
 const explicit=opts.browser||process.env.CHROME_PATH;if(explicit){if(!existsSync(explicit))throw new Error('Configured browser does not exist');return explicit}
 const candidates=process.platform==='darwin'?['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','/Applications/Chromium.app/Contents/MacOS/Chromium']:process.platform==='win32'?[join(process.env.PROGRAMFILES||'C:\\Program Files','Google/Chrome/Application/chrome.exe'),join(process.env.LOCALAPPDATA||'','Google/Chrome/Application/chrome.exe')]:['/usr/bin/google-chrome','/usr/bin/google-chrome-stable','/usr/bin/chromium','/usr/bin/chromium-browser'];
 for(const p of candidates)if(existsSync(p))return p;
 throw new Error('Chrome/Chromium not found. Set CHROME_PATH or pass --browser.');
}
if(Number(process.versions.node.split('.')[0])<22)throw new Error('Node.js22+ is required');
const CHROME=browserPath();run('ffmpeg',['-version']);run('ffprobe',['-version']);
if(mode==='doctor'){console.log(JSON.stringify({ok:true,node:process.versions.node,platform:process.platform,browser:CHROME,ffmpeg:run('ffmpeg',['-version']).split('\n')[0],note:'This checks dependencies. A real still must validate WebGL2 and float targets.'},null,2));process.exit(0)}
if(!['render','stills','preview'].includes(mode))throw new Error('Use doctor, stills, render or preview');
run(process.env.PYTHON||'python3',[join(ROOT,'build.py')]);run(process.execPath,['--check',join(ROOT,'check.js')]);
const cfg=JSON.parse(readFileSync(join(ROOT,'project.json'),'utf8')),TL=JSON.parse(readFileSync(join(ROOT,'timeline.json'),'utf8'));
const scale=Number(opts.scale||1),samples=Number(opts.samples||16),duration=TL.duration,fps=cfg.fps;
if(!Number.isInteger(scale)||scale<1||scale>4||!Number.isInteger(samples)||samples<1||samples>256)throw new Error('scale must be1–4; samples1–256');
const W=cfg.width*scale,H=cfg.height*scale,frameBytes=W*H*4,expectedFrames=TL.frames;
const output=resolve(ROOT,opts.out||'out/reel.mp4');
if(!output.toLowerCase().endsWith('.mp4'))throw new Error('Output must end in .mp4');
if(mode==='stills'){const ts=(positionals[0]||'0').split(',').map(Number);if(ts.length>240||ts.some(t=>!Number.isFinite(t)||t<0||t>=duration))throw new Error('Use1–240 still times within the film duration');}
mkdirSync(dirname(output),{recursive:true});mkdirSync(join(ROOT,'review/stills'),{recursive:true});
const temp=mkdtempSync(join(tmpdir(),'motion-reel-')),profile=join(temp,'profile'),token=randomBytes(20).toString('hex');
const silent=join(temp,'silent.mp4'),rawAudio=join(temp,'audio.wav'),mixedAudio=join(temp,'mixed.wav'),normAudio=join(temp,'normalized.wav');
let chrome,encoder,encoderDone,server,closing=false,nextFrame=0,lastActivity=Date.now(),watchdog,encodedLevels;
const tempName=(s)=>s.replace(/[^a-z0-9_.-]/gi,'_');
function cleanup(){if(closing)return;closing=true;clearInterval(watchdog);chrome?.kill('SIGTERM');if(encoder&&!encoder.killed)encoder.kill('SIGTERM');server?.close();try{rmSync(temp,{recursive:true,force:true,maxRetries:5,retryDelay:100})}catch{}}
function fail(error){console.error(error.stack||String(error));cleanup();process.exitCode=1;setTimeout(()=>process.exit(1),150).unref()}
function startEncoder(){
 encoder=spawn('ffmpeg',['-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s',`${W}x${H}`,'-r',String(fps),'-i','-',
 '-vf','vflip,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv',
 '-c:v','libx264','-preset','slow','-crf','17','-profile:v','high','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv',silent],{stdio:['pipe','inherit','inherit']});
 encoder.stdin.on('error',fail);encoder.on('error',fail);encoderDone=once(encoder,'close');
}
function levels(file){const r=spawnSync('ffmpeg',['-hide_banner','-i',file,'-map','0:a','-af','loudnorm=I=-14:TP=-1:LRA=11:print_format=json','-f','null','-'],{encoding:'utf8'});if(r.status!==0)throw new Error(r.stderr);const s=r.stderr;return JSON.parse(s.slice(s.lastIndexOf('{'),s.lastIndexOf('}')+1));}
// The page posts only synthesized audio. Music and sound-effect files are placed here, sample-accurately, from timeline.json.
function mixSoundtrack(){
 const s=TL.sound,args=[],chains=[],fmt='aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo';
 if(s.synth&&!existsSync(rawAudio))throw new Error('Expected synthesized soundtrack was not posted');
 if(s.synth&&!s.music&&!s.sfx.length)return rawAudio;
 const add=(file,filters)=>{const i=chains.length;args.push('-i',file);chains.push(`[${i}:a]${fmt},${filters}[a${i}]`)};
 if(s.synth)add(rawAudio,'anull');
 if(s.music){const fade=s.music.fadeOut??0.5;add(s.music.path,`atrim=start=${s.music.start||0}:duration=${duration},asetpts=PTS-STARTPTS,volume=${s.music.gain||0}dB`+(fade>0?`,afade=t=out:st=${Math.max(0,duration-fade)}:d=${fade}`:''))}
 // A cue aligns the file's loudest moment (lead seconds in) to its beat; a whoosh swells into the cut.
 for(const c of s.sfx){const at=c.t-c.lead;add(c.path,`atrim=start=${Math.max(0,-at)},asetpts=PTS-STARTPTS,volume=${c.gain}dB,adelay=delays=${Math.round(Math.max(0,at)*48000)}S:all=1`)}
 const graph=chains.join(';')+';'+chains.map((_,i)=>`[a${i}]`).join('')+`amix=inputs=${chains.length}:normalize=0:duration=longest,apad=whole_dur=${duration},atrim=end=${duration}[mix]`;
 run('ffmpeg',['-v','error','-y',...args,'-filter_complex',graph,'-map','[mix]','-c:a','pcm_f32le','-ar','48000',mixedAudio]);
 return mixedAudio;
}
function finishFilm(){
 const sound=TL.sound,hasSound=sound.synth||!!sound.music||sound.sfx.length>0;
 if(hasSound){
  const mixed=mixSoundtrack();
  const m=levels(mixed),af=`loudnorm=I=-14:TP=-1:LRA=11:measured_I=${m.input_i}:measured_TP=${m.input_tp}:measured_LRA=${m.input_lra}:measured_thresh=${m.input_thresh}:offset=${m.target_offset}:linear=true,aresample=48000`;
  run('ffmpeg',['-v','error','-y','-i',mixed,'-af',af,'-c:a','pcm_s24le',normAudio]);
  let trim=0;
  for(let attempt=0;attempt<3;attempt++){
   run('ffmpeg',['-v','error','-y','-i',silent,'-i',normAudio,'-map','0:v','-map','1:a','-c:v','copy','-bsf:v','h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1','-af',`volume=${trim}dB`,'-c:a','aac','-b:a','256k','-t',String(duration),'-movflags','+faststart',output]);
   encodedLevels=levels(output);if(Number(encodedLevels.input_tp)<=-1.2)break;
   trim+=-1.3-Number(encodedLevels.input_tp);if(attempt===2)throw new Error('Encoded true peak remains above target');
  }
  // Retain a portable source for independent mux-timing checks.
  run('ffmpeg',['-v','error','-y','-i',mixed,'-c:a','pcm_s24le',output.replace(/\.mp4$/i,'.source.wav')]);
 }else run('ffmpeg',['-v','error','-y','-i',silent,'-c:v','copy','-an','-movflags','+faststart',output]);
 run('ffmpeg',['-v','error','-y','-ss',String(Math.max(0,duration-.30)),'-i',output,'-frames:v','1','-vf','scale=1920:-2',output.replace(/\.mp4$/i,'.poster.jpg')]);
 // Cue list and asset ledger travel with the film for verify.py / review.py and credits.
 const cues=[...TL.shots.map(s=>({t:s.start,kind:'cut',shot:s.id,label:s.label,hit:s.hit})),...sound.sfx.map(c=>({t:c.t,kind:'sfx',shot:c.shot,name:c.name}))].sort((a,b)=>a.t-b.t);
 const library=cfg.sound?.library||{},music=cfg.sound?.music;
 const assets=[...(music?[{role:'music',file:music.file,start:music.start||0,source:music.source,license:music.license}]:[]),...[...new Set(sound.sfx.map(c=>c.name))].map(n=>({role:'sfx',name:n,file:library[n].file,source:library[n].source,license:library[n].license}))];
 writeFileSync(output.replace(/\.mp4$/i,'.render.json'),JSON.stringify({width:W,height:H,fps,duration,frames:nextFrame,samples,audio:hasSound,synth:sound.synth,bpm:cfg.bpm,spb:TL.spb,maxCutLagSeconds:TL.maxCutLagSeconds,cues,assets,encodedAudio:encodedLevels||null},null,2));
 console.log(`Rendered ${output} (${duration.toFixed(3)}s / ${nextFrame} frames)`);
}
server=http.createServer(async(req,res)=>{
 try{
  const url=new URL(req.url,'http://localhost');
  if(req.method==='GET'){
   const file=resolve(ROOT,'.'+decodeURIComponent(url.pathname==='/'?'/reel.html':url.pathname));
   if(!file.startsWith(ROOT+sep)){res.writeHead(403).end();return}
   const MIME={'.html':'text/html; charset=utf-8','.js':'text/javascript','.json':'application/json','.woff2':'font/woff2','.woff':'font/woff','.ttf':'font/ttf','.otf':'font/otf','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.gif':'image/gif','.svg':'image/svg+xml'};
   const mime=MIME[file.slice(file.lastIndexOf('.')).toLowerCase()]||'application/octet-stream';
   try{res.setHeader('Content-Type',mime);res.end(readFileSync(file))}catch{res.writeHead(404).end()}return;
  }
  if(req.method!=='POST'||url.searchParams.get('token')!==token){res.writeHead(403).end();return}
  let length=0;const chunks=[];const maxBytes=Math.max(frameBytes,Math.ceil(duration*48000*8+44))+4096;
  for await(const chunk of req){length+=chunk.length;if(length>maxBytes)throw new Error('Oversized capture payload');chunks.push(chunk)}
  const body=Buffer.concat(chunks);lastActivity=Date.now();
  switch(url.pathname){
   case '/hello':{const hello=JSON.parse(body.toString());if(hello.width!==W||hello.height!==H||hello.fps!==fps||Math.abs(hello.duration-duration)>.000001)throw new Error('Page and project timing/dimensions disagree');break}
   case '/log':console.log('[page]',body.toString());break;
   case '/error':throw new Error('[page] '+body.toString());
   case '/audio':writeFileSync(rawAudio,body);break;
   case '/still':{
    if(body.length!==frameBytes)throw new Error('Wrong still byte count');
    const t=url.searchParams.get('t');run('ffmpeg',['-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s',`${W}x${H}`,'-i','-','-vf','vflip','-frames:v','1',join(ROOT,'review/stills',tempName(t)+'.png')],{input:body,maxBuffer:frameBytes+1024});break;
   }
   case '/frame':{
    if(body.length!==frameBytes||Number(url.searchParams.get('i'))!==nextFrame)throw new Error('Invalid frame size or sequence');
    if(!encoder)startEncoder();if(!encoder.stdin.write(body))await once(encoder.stdin,'drain');nextFrame++;
    if(nextFrame%120===0)console.log(`${nextFrame}/${expectedFrames} frames`);break;
   }
   case '/done':{
    if(mode==='render'){
     if(nextFrame!==expectedFrames||!encoder)throw new Error(`Expected ${expectedFrames} frames, got ${nextFrame}`);
     encoder.stdin.end();const [code]=await encoderDone;if(code!==0)throw new Error('Video encoder failed');encoder=null;finishFilm();
    }
    res.end('ok');cleanup();return;
   }
   default:res.writeHead(404).end();return;
  }
  res.end('ok');
 }catch(e){res.writeHead(500).end(String(e.message));fail(e)}
});
server.listen(0,'127.0.0.1',()=>{
 const q=new URLSearchParams({mode:mode==='render'?'render':mode==='stills'?'still':'preview',ts:positionals[0]||'0',scale,samples,sub:samples,token});
 const url=`http://127.0.0.1:${server.address().port}/reel.html?${q}`;
 if(mode==='preview'){console.log(url);return}
 const flags=['--headless=new',`--user-data-dir=${profile}`,'--no-first-run','--no-default-browser-check','--enable-gpu','--ignore-gpu-blocklist','--disable-background-timer-throttling','--disable-renderer-backgrounding','--autoplay-policy=no-user-gesture-required',`--window-size=${W},${H}`];
 if(process.platform==='darwin')flags.push('--use-angle=metal');
 chrome=spawn(CHROME,[...flags,url],{stdio:'ignore'});chrome.on('error',fail);chrome.on('exit',code=>{if(!closing)fail(new Error('Browser exited before capture finished: '+code))});
 watchdog=setInterval(()=>{if(Date.now()-lastActivity>120000)fail(new Error('Capture stalled for120seconds; inspect syntax, page errors and GPU support'))},5000);
});
process.on('SIGINT',()=>{cleanup();process.exit(130)});process.on('SIGTERM',()=>{cleanup();process.exit(143)});process.on('uncaughtException',fail);process.on('unhandledRejection',fail);
