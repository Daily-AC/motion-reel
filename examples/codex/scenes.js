// Original scene design. Codex's actual cloud contour carries the opening and closing.
// Every scene is draw(g, u, t, shot): u is its own clock (0 at the cut), t the film time, shot its project.json entry.
const TAU=Math.PI*2;
const smooth=x=>{x=clamp(x);return x*x*(3-2*x)};
const QOUT=x=>1-Math.pow(1-clamp(x),4);
function rect2(g,x,y,w,h,col,r=0){g.fillStyle=col;g.beginPath();g.roundRect(x,y,w,h,r);g.fill()}
function disk(g,x,y,r,col){if(r<=0)return;g.fillStyle=col;g.beginPath();g.arc(x,y,r,0,TAU);g.fill()}
function segline(g,x,y,X,Y,col,w=2){g.strokeStyle=col;g.lineWidth=w;g.beginPath();g.moveTo(x,y);g.lineTo(X,Y);g.stroke()}
function type(g,s,x,y,sz,col=PAPER,weight=850,align='center',ls=-.055){
  g.fillStyle=col;g.font=F(weight,sz);g.textAlign=align;g.textBaseline='alphabetic';textLS(g,s,x,y,sz*ls);
}
function caption(g,s,x,y,sz=48,col=PAPER,align='left'){
  g.font=F(600,sz);g.textAlign=align;g.fillStyle=col;g.fillText(s,x,y);
}
function local(g,x,y,scale,ang,fn){g.save();g.translate(x,y);g.rotate(ang);g.scale(scale,scale);fn();g.restore()}
function alpha(g,a,fn){g.save();g.globalAlpha*=clamp(a);fn();g.restore()}
function rotateP(v,ax=0,ay=0,az=0){
  let [x,y,z]=v, c=Math.cos(ax),s=Math.sin(ax),Y=y*c-z*s,Z=y*s+z*c;y=Y;z=Z;
  c=Math.cos(ay);s=Math.sin(ay);let X=x*c+z*s;Z=-x*s+z*c;x=X;z=Z;
  c=Math.cos(az);s=Math.sin(az);return [x*c-y*s,x*s+y*c,z];
}
function projectP(v,opt={}){
  const [x,y,z]=rotateP(v,opt.ax||0,opt.ay||0,opt.az||0),dist=opt.dist||1500;
  const f=opt.f||1400,den=Math.max(120,dist+z),ss=f/den*(opt.scale||1);
  return [(opt.cx??W/2)+x*ss,(opt.cy??H/2)-y*ss,z,ss];
}
function face(g,vs,color,opt,edges=false){
  const ps=vs.map(v=>projectP(v,opt));g.beginPath();ps.forEach((p,i)=>i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1]));g.closePath();g.fillStyle=color;g.fill();
  if(edges){g.strokeStyle=color;g.lineWidth=.65;g.stroke()}
}
function normal(vs){
  const a=vs[1].map((v,i)=>v-vs[0][i]),b=vs[2].map((v,i)=>v-vs[0][i]);
  const n=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],len=Math.hypot(...n)||1;return n.map(v=>v/len);
}
function lit(base,n){
  const d=Math.max(0,n[0]*-.36+n[1]*.66+n[2]*-.65),spec=Math.pow(Math.max(0,n[0]*-.30+n[1]*.45-n[2]*.84),22)*.20;
  return `rgb(${base.map(v=>Math.round(clamp(v*(.43+d*.59)+255*spec,0,255))).join(',')})`;
}
function mesh(g,faces,opt){
  const list=faces.map(f=>({vs:f.vs,base:f.base,twoSided:f.twoSided,z:f.vs.reduce((a,v)=>a+rotateP(v,opt.ax,opt.ay,opt.az)[2],0)/f.vs.length}));
  list.sort((a,b)=>b.z-a.z);
  for(const f of list){const ns=normal(f.vs),rn=rotateP(ns,opt.ax,opt.ay,opt.az),ln=f.twoSided&&rn[2]>0?rn.map(v=>-v):rn;face(g,f.vs,lit(f.base,ln),opt,true)}
}
function boxFaces(x,y,z,sx,sy,sz,base,arr){
  const a=x-sx/2,b=x+sx/2,c=y-sy/2,d=y+sy/2,e=z-sz/2,f=z+sz/2;
  arr.push({vs:[[a,c,e],[a,d,e],[b,d,e],[b,c,e]],base},
    {vs:[[a,d,e],[a,d,f],[b,d,f],[b,d,e]],base},
    {vs:[[b,c,e],[b,d,e],[b,d,f],[b,c,f]],base},
    {vs:[[a,c,f],[a,d,f],[a,d,e],[a,c,e]],base},
    {vs:[[a,c,f],[a,c,e],[b,c,e],[b,c,f]],base},
    {vs:[[b,c,f],[b,d,f],[a,d,f],[a,c,f]],base});
}
function prismBar(cx,cy,len,thick,angle,z,depth,base,arr){
  const cs=Math.cos(angle),sn=Math.sin(angle),corners=[[-len/2,-thick/2],[-len/2,thick/2],[len/2,thick/2],[len/2,-thick/2]];
  const verts=corners.map(([x,y])=>[cx+x*cs-y*sn,cy+x*sn+y*cs]);
  arr.push({vs:verts.map(([x,y])=>[x,y,z-depth/2]),base});
  for(let i=0;i<4;i++){let j=(i+1)%4;arr.push({vs:[[...verts[i],z-depth/2],[...verts[j],z-depth/2],[...verts[j],z+depth/2],[...verts[i],z+depth/2]],base});}
}
// Build the bevel and sidewall once. Coordinates come directly from Codex's SVG.
const CODEX_SIDE_FACES=[];
const CODEX_RIM_LEVELS=[[.977,-62],[.992,-58],[1,-44],[1,35],[.98,49]];
for(let k=0;k<CODEX_RIM_LEVELS.length-1;k++){
  const [s0,z0]=CODEX_RIM_LEVELS[k],[s1,z1]=CODEX_RIM_LEVELS[k+1],ring=CODEX_CONTOURS[0];
  for(let i=0;i<ring.length;i++){
    const a=ring[i],b=ring[(i+1)%ring.length],y=(a[1]+b[1])/2;
    const base=k<2?[132+25*y/312,146+14*y/312,255]:[58+20*y/312,72+24*y/312,192+22*y/312];
    CODEX_SIDE_FACES.push({vs:[[a[0]*s0,a[1]*s0,z0],[b[0]*s0,b[1]*s0,z0],[b[0]*s1,b[1]*s1,z1],[a[0]*s1,a[1]*s1,z1]],base,twoSided:true});
  }
}
function contourPath(g,ring,opt,scale=1,z=-62){
  g.beginPath();ring.forEach((v,i)=>{const p=projectP([v[0]*scale,v[1]*scale,z],opt);i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1])});g.closePath();
}
function markMesh(g,opt){
  mesh(g,CODEX_SIDE_FACES,opt);
  const top=projectP([0,320,-62],opt),bottom=projectP([0,-320,-62],opt);
  const gradient=g.createLinearGradient(top[0],top[1],bottom[0],bottom[1]);
  gradient.addColorStop(0,'#aaa0ff');gradient.addColorStop(.28,'#8083fa');gradient.addColorStop(.64,'#4c65f6');gradient.addColorStop(1,'#333dfa');
  contourPath(g,CODEX_CONTOURS[0],opt,.977,-62);g.fillStyle=gradient;g.fill();
  // Broad studio reflection is clipped to the original contour.
  g.save();contourPath(g,CODEX_CONTOURS[0],opt,.977,-62);g.clip();
  const hp=projectP([-145,260,-65],opt),radius=480*(opt.scale||1);
  const glow=g.createRadialGradient(hp[0],hp[1],0,hp[0],hp[1],Math.max(.01,radius));
  glow.addColorStop(0,'rgba(255,255,255,.33)');glow.addColorStop(1,'rgba(255,255,255,0)');g.fillStyle=glow;g.fill();g.restore();
  // The white prompt is a shallow raised inlay, with its exact rounded contours.
  for(let j=1;j<CODEX_CONTOURS.length;j++){
    const ring=CODEX_CONTOURS[j],fs=[];
    for(let i=0;i<ring.length;i++){const a=ring[i],b=ring[(i+1)%ring.length];fs.push({vs:[[...a,-62],[...b,-62],[...b,-74],[...a,-74]],base:[186,199,252],twoSided:true});}
    mesh(g,fs,opt);contourPath(g,ring,opt,1,-74);g.fillStyle='#fafbff';g.fill();
  }
}
function waveRing(g,x,y,r,col,progress,w=2){
  g.save();g.strokeStyle=col;g.lineWidth=w;g.beginPath();g.ellipse(x,y,r,r*.37,-.22,0,TAU*clamp(progress));g.stroke();g.restore();
}

// V4: one family of reflected light, paths and echoes inhabits the existing scenes.
const CREATIVE_STRING='NF3SQU86SFW7L6L2NXKGDXZX47SA8ZFUUVXXB7C6ZE6TVGN3';
const SPICE_SEED=[...CREATIVE_STRING].reduce((h,ch)=>Math.imul(h^ch.charCodeAt(0),16777619)>>>0,2166136261);
const spiceRandom=mulberry32(SPICE_SEED);
const ORBIT_BITS=Array.from({length:14},()=>({phase:spiceRandom()*TAU,rad:590+spiceRandom()*190,z:spiceRandom()*120-60,size:10+spiceRandom()*17}));
function pool(g,x,y,rx,ry,col,opacity=1){
  g.save();g.translate(x,y);g.scale(1,ry/rx);g.globalAlpha*=opacity;
  const p=g.createRadialGradient(0,0,0,0,0,rx);p.addColorStop(0,col);p.addColorStop(.45,col.replace(/,[\d.]+\)$/,',0.12)'));p.addColorStop(1,'rgba(60,85,180,0)');
  g.fillStyle=p;g.beginPath();g.arc(0,0,rx,0,TAU);g.fill();g.restore();
}
function lightPath(g,points,t,opacity=.6,width=2){
  if(points.length<2)return;
  g.save();g.globalAlpha*=opacity;g.lineJoin='round';g.lineCap='round';
  const draw=(pts,w,col)=>{g.strokeStyle=col;g.lineWidth=w;g.beginPath();pts.forEach((p,i)=>i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1]));g.stroke()};
  draw(points,width,'rgba(138,163,255,.35)');
  const p=fract(t/(BAR*1.5)),at=Math.floor(p*(points.length-1));const trail=points.slice(Math.max(0,at-15),at+1);
  if(trail.length>1){draw(trail,width+9,'rgba(138,163,255,.08)');draw(trail,width+2,'rgba(162,183,255,.65)');draw(trail,width,'#eef2ff')}
  const q=points[at];disk(g,q[0],q[1],4.2,'#f5f7ff');g.restore();
}
function orbitalWorld(g,t){
  pool(g,1125,667,860,350,'rgba(73,89,227,.34)');
  pool(g,1140,900,740,105,'rgba(116,147,255,.49)');
  const opt={ax:1.07,ay:-.12,az:-.12,dist:2000,f:1900,cx:1110,cy:602};
  for(let k=0;k<4;k++){
    const ps=[];for(let i=0;i<=120;i++){const a=i/120*TAU,r=595+k*39;ps.push(projectP([Math.cos(a)*r,Math.sin(a)*r,-k*19],opt))}
    lightPath(g,ps,t+k*.53,k===1?.7:.34,k===1?1.8:1.1);
  }
  const fs=[];
  ORBIT_BITS.forEach((b,i)=>{const a=b.phase+t*.21,p=rotateP([Math.cos(a)*b.rad,Math.sin(a)*b.rad,b.z],1.07,-.12,-.12);boxFaces(p[0],p[1],p[2],b.size,b.size,b.size,[85,103,186],fs)});
  alpha(g,.68,()=>mesh(g,fs,{ax:0,ay:0,az:0,dist:2000,f:1900,cx:1110,cy:602}));
}
function ribbonWorld(g,u,t){
  const power=1-smooth(seg(u,1.43,BAR));
  pool(g,995+Math.sin(u*2)*110,620,880,425,'rgba(51,65,168,.31)',power);
  pool(g,1050,883,570,115,'rgba(117,140,255,.34)',power);
  // A distant wire echo comes from the same surface as the hero, not unrelated ornament.
  const opt={ax:.48+u*.45,ay:-.36+u*.34,az:-.25+u*.37,scale:1.74,dist:2100,f:1900,cx:1050,cy:557};
  alpha(g,power,()=>{
    for(const v of [-128,-74,0,74,128]){const ps=[];for(let i=0;i<=120;i++)ps.push(projectP(ribbonPoint(i/120*TAU,v,u),opt));lightPath(g,ps,t+v*.009,v===0?.3:.17,1.2)}
    // Wide light spill gives the opening in the loop a farther spatial layer.
    const ps=[];for(let i=0;i<=120;i++){const x=-150+i/120*2230,y=714+Math.sin(i/120*TAU+u*.55)*144;ps.push([x,y])}lightPath(g,ps,t,.50,1.45);
  });
}
function architecturalWorld(g,opt,u,t){
  pool(g,1050,753,930,267,'rgba(50,77,180,.30)');
  g.save();
  for(let z=-600;z<=700;z+=70){const a=projectP([-1100,-270,z],opt),b=projectP([1100,-270,z],opt);alpha(g,.23*(1-Math.abs(z)/1200),()=>segline(g,a[0],a[1],b[0],b[1],'#7e92d2',1.2));}
  for(let x=-1120;x<=1120;x+=80){const a=projectP([x,-270,-600],opt),b=projectP([x,-270,700],opt);alpha(g,.17,()=>segline(g,a[0],a[1],b[0],b[1],'#7e92d2',1.2));}
  g.restore();
  const ps=[];for(let i=0;i<=140;i++){const x=-1150+i/140*2300;ps.push(projectP([x,-258,170+Math.sin(x*.003+u)*105],opt))}lightPath(g,ps,t,.9,2.1);
  const scaffold=[];
  for(let i=0;i<12;i++){
    const side=i%2?-1:1,x=side*(700+(i%3)*100),y=-250+(1-smooth(seg(u,.1+i*.04,1.25)))*(140+i*15),z=-320+(i%4)*190;
    boxFaces(x,y,z,24+i%3*9,24+i%3*9,24+i%3*9,[78,99,183],scaffold);
  }
  alpha(g,.65,()=>mesh(g,scaffold,opt));
}
function panelShadow(g,vs,opt){
  const ps=vs.map(v=>projectP(v,opt));g.save();g.globalAlpha=.13;g.filter='blur(19px)';g.fillStyle='#263f84';g.beginPath();ps.forEach((p,i)=>i?g.lineTo(p[0]+24,p[1]+33):g.moveTo(p[0]+24,p[1]+33));g.closePath();g.fill();g.restore();
  const back=vs.map(v=>[v[0]*1.007,v[1]*1.007,v[2]+18]);face(g,back,'#8394ce',opt,true);
}

// 0. A real 3D solid, already large and complete on frame zero.
function S0(g,u){
  bg(g,INK);
  orbitalWorld(g,u);
  const pull=E.ioC(seg(u,.05,.62)),spin=smooth(seg(u,.62,1.30));
  const opt={ax:-.18+Math.sin(u*2)*.09,ay:lerp(-.65,.24,pull)+spin*.28,az:lerp(-.22,.08,pull),scale:lerp(1.60,1.04,pull),dist:1700,f:1420,cx:1100,cy:570};
  markMesh(g,opt);
  type(g,BRAND.name,102,285,157,PAPER,880,'left');
  caption(g,BRAND.opening[0],110,801,54);caption(g,BRAND.opening[1],110,872,54);
  const p=E.inC(seg(u,1.50,BAR));
  if(p>0){g.save();g.translate(W/2,H/2);g.rotate(lerp(-.20,0,p));rect2(g,-W,-50-p*900,W*2,100+p*1800,ACCENT);g.restore();}
}

// 1. The word is a moving material: letters compress, expand and open a physical portal.
function S1(g,u,t,shot){
  const {word,portal,left,right}=shot.copy;bg(g,PAPER);
  const open=E.outE(seg(u,0,.23));rect2(g,0,0,W,H*(1-open),ACCENT);
  const size=480,weights=[...word].map((_,i)=>Math.round(840-660*Math.pow(Math.sin(Math.PI*seg(u,.40+i*.12,1.10+i*.12)),2)));
  const widths=weights.map((w,i)=>{g.font=F(w,size);return g.measureText(word[i]).width-size*.03});const total=widths.reduce((a,b)=>a+b,0),start=(W-total)/2;
  const zoom=1+E.inE(seg(u,1.35,BAR))*18,ox=start+widths.slice(0,portal).reduce((a,b)=>a+b,0)+widths[portal]*.49,oy=H/2;
  g.save();g.translate(W/2,H/2);g.scale(zoom,zoom);g.translate(-ox,-oy);
  let x=start;
  for(let i=0;i<word.length;i++){
    const en=E.outE(seg(u,i*.055,.37+i*.055)),dy=(i%2?1:-1)*(1-en)*420;
    const xs=1+.13*Math.sin(u*8-i*.9)*Math.exp(-u*.8);
    local(g,x+widths[i]/2,696+dy,1,Math.sin(u*5-i)*.028,()=>{g.scale(xs,1/xs);type(g,word[i],0,0,size,INK,weights[i]);});x+=widths[i];
  }
  // The inside of O is the next scene's black space.
  if(u>1.23){const q=smooth(seg(u,1.23,1.48));disk(g,ox,oy,76*q,INK)}
  g.restore();
  // Reveal the next physical ring inside the aperture before the last dark frame.
  if(u>1.72)alpha(g,smooth(seg(u,1.72,BAR)),()=>ribbon(g,0,0));
  if(u<1.30){caption(g,left,115,914,44,INK);caption(g,right,1805,914,44,INK,'right');}
}

// 2. Two-sided sculptural ribbon: a circle becomes a twisted, breathing Möbius loop.
function ribbonPoint(a,v,u){
  const twist=lerp(0,3,smooth(seg(u,.16,1.21))),R=285+Math.sin(u*4)*13;
  const r=R+v*Math.cos(twist*a/2+u*.7),lift=v*Math.sin(twist*a/2+u*.7);
  return [Math.cos(a)*r,Math.sin(a)*r,lift+Math.sin(a*3+u*4)*26];
}
function ribbon(g,u,explode=0){
  const faces=[],n=128,lanes=4;
  const point=(a,v)=>ribbonPoint(a,v,u);
  for(let i=0;i<n;i++)for(let j=0;j<lanes;j++){
    const a=i/n*TAU,b=(i+1)/n*TAU,v0=-95+j/lanes*190,v1=-95+(j+1)/lanes*190;
    let vs=[point(a,v0),point(a,v1),point(b,v1),point(b,v0)];
    const impulse=explode*(.45+.55*Math.sin(i*13.2+j*4)**2);
    vs=vs.map(v=>v.map((x,k)=>x*(1+impulse*3)+[Math.cos(a),Math.sin(a),Math.sin(i*1.7)][k]*impulse*390));
    faces.push({vs,base:j===0||j===3?RGB.accent:RGB.paper,twoSided:true});
  }
  mesh(g,faces,{ax:.48+u*.45,ay:-.36+u*.34,az:-.25+u*.37,scale:1.17+Math.sin(u*3)*.13+explode*.9,dist:1700,f:1800});
}
function S2(g,u,t,shot){
  bg(g,INK);const handoff=smooth(seg(u,1.53,BAR));
  ribbonWorld(g,u,t);
  alpha(g,1-handoff,()=>ribbon(g,u,0));
  if(handoff>0)alpha(g,handoff,()=>{for(let i=0;i<NPART;i++){const p=particles[i],q=projectP(ribbonPoint(p.phase,(p.r-.5)*190,u),{ax:.48+u*.45,ay:-.36+u*.34,az:-.25+u*.37,scale:1.17+Math.sin(u*3)*.13,dist:1700,f:1800});rect2(g,q[0]-1.5,q[1]-1.5,3,3,i%11===0?ACCENT:PAPER)}});
  alpha(g,1-handoff,()=>type(g,shot.copy.title,105,191,64,PAPER,760,'left'));
}

// Frozen particle seeds and text targets; no per-frame random state.
const maskCanvas=document.createElement('canvas');maskCanvas.width=1200;maskCanvas.height=310;
const maskCtx=maskCanvas.getContext('2d');maskCtx.fillStyle='#fff';maskCtx.font='900 290px system-ui';maskCtx.textAlign='center';maskCtx.fillText(copyFor('possibility').target,600,260);
const maskData=maskCtx.getImageData(0,0,1200,310).data;
const textDots=[],voxelDots=[],RND=mulberry32(7711);
for(let y=8;y<300;y+=7)for(let x=8;x<1192;x+=7)if(maskData[(y*1200+x)*4+3]>180)textDots.push([x-600,155-y,0]);
for(let y=16;y<292;y+=22)for(let x=16;x<1180;x+=22)if(maskData[(y*1200+x)*4+3]>180)voxelDots.push([x-600,155-y,0]);
const NPART=4096;
const particles=Array.from({length:NPART},(_,i)=>{
  const zz=1-2*(i+.5)/NPART,rr=Math.sqrt(1-zz*zz),a=i*2.399963229728653;
  return {unit:[Math.cos(a)*rr,Math.sin(a)*rr,zz],r:RND(),phase:RND()*TAU,target:textDots[Math.floor(i/NPART*textDots.length)]};
});
function particlePosition(p,i,u){
  const burst=E.outC(seg(u,0,.35)),contract=E.ioC(seg(u,.24,.85)),form=E.ioC(seg(u,.90,1.65));
  const r=lerp(180,850+p.r*850,burst),a=p.phase+u*(1.2+p.r*.8),z=(fract(p.r-u*.51)*2-1)*970;
  const ring=ribbonPoint(p.phase,(p.r-.5)*190,BAR),start=p.unit.map((v,k)=>lerp(ring[k],v*r,burst)),helix=[Math.cos(a)*(210+70*Math.sin(z*.006+u*5)),Math.sin(a)*(210+70*Math.sin(z*.006+u*5)),z];
  return start.map((v,k)=>lerp(lerp(v,helix[k],contract),p.target[k],form));
}
function S3(g,u,t,shot){
  bg(g,INK);
  pool(g,1030,570,760,480,'rgba(48,65,168,.19)',1-smooth(seg(u,.9,1.65)));
  const turn=E.ioC(seg(u,0,1.68));
  const opt={ax:lerp(.48+BAR*.45,-.08,turn),ay:lerp(-.36+BAR*.34,.10,turn),az:lerp(-.25+BAR*.37,0,turn),dist:lerp(1700,1500,turn),f:lerp(1800,1500,turn),scale:lerp(1.17+Math.sin(BAR*3)*.13,1.16,turn)};
  const draw=[];for(let i=0;i<NPART;i++){const p=particles[i],v=particlePosition(p,i,u),q=projectP(v,opt),old=projectP(particlePosition(p,i,Math.max(0,u-.013)),opt);if(q[0]<-80||q[0]>W+80||q[1]<-80||q[1]>H+80)continue;draw.push({q,old,i})}
  draw.sort((a,b)=>b.q[2]-a.q[2]);
  for(const {q,old,i} of draw){g.globalAlpha=clamp(.6+(1200-q[2])/3000,.22,1);g.fillStyle=i%11===0?ACCENT:PAPER;
    const r=clamp(q[3]*(i%11===0?2.7:1.6),.7,5);g.fillRect(q[0]-r,q[1]-r,r*2,r*2);
    if(u<1.0){g.strokeStyle=i%11===0?ACCENT:PAPER;g.lineWidth=r;g.beginPath();g.moveTo(old[0],old[1]);g.lineTo(q[0],q[1]);g.stroke()}}
  g.globalAlpha=1;
  alpha(g,smooth(seg(u,1.25,1.6)),()=>caption(g,shot.copy.caption,W/2,897,51,PAPER,'center'));
}

// 4. The word leaves the flat page: individually articulated porcelain/green blocks.
function S4(g,u,t,shot){
  bg(g,INK);const spin=E.ioC(seg(u,.04,1.67));
  const opt={ax:lerp(-.08,.62,spin),ay:lerp(.10,-.85,spin),az:lerp(0,-.20,spin),dist:1800,f:1850,scale:1.11+smooth(seg(u,0,.48))*.27+Math.sin(u*2.4)*.09};
  architecturalWorld(g,opt,u,t);
  const fs=[];
  for(let i=0;i<voxelDots.length;i++){
    const [x,y]=voxelDots[i],r=Math.hypot(x*.6,y),pulse=Math.exp(-Math.pow((r-(u*500)%420)/85,2));
    const q=spring(Math.max(0,u-((x+600)/1200)*.19),3.7,.58);
    const depth=4+q*(52+90*pulse),z=lerp(0,42*Math.sin(x*.009+u*3),smooth(seg(u,.6,1.3)));
    boxFaces(x,y,z,19.5,19.5,depth,pulse>.46?RGB.accent:RGB.paper,fs);
  }
  mesh(g,fs,opt);
  caption(g,shot.copy.top,110,211,52);caption(g,shot.copy.bottom,1810,927,52,PAPER,'right');
  if(u>1.50){const q=E.inC(seg(u,1.50,BAR));for(let i=0;i<6;i++)rect2(g,i*W/6, i%2?H*(1-q):-H*(1-q),W/6+2,H,PAPER)}
}

// Interface textures are graphic content; their movement is full 3D perspective.
function makePanel(kind,t){
  const can=panelCanvases[kind],p=can.getContext('2d'),w=960,h=620;
  p.clearRect(0,0,w,h);rect2(p,0,0,w,h,kind===1?INK:PAPER,18);
  const dark=kind===1,fg=dark?PAPER:INK;segline(p,0,67,w,67,dark?'#444d6a':'#a2abc6',2);
  type(p,['FORM / STUDIO','BUILD / TERMINAL','MOTION / ENGINE'][kind],35,43,20,fg,650,'left',.02);
  for(let j=0;j<3;j++)disk(p,872+j*24,34,5,j===2?ACCENT:fg);
  if(kind===0){
    type(p,'Make it',50,206,101,INK,850,'left');type(p,'extraordinary.',50,310,101,INK,850,'left');
    rect2(p,50,357,188,48,INK,24);type(p,'EXPLORE',144,389,19,PAPER,650,'center',.09);
    for(let j=0;j<25;j++){
      const a=j/25*TAU+t,xx=715+Math.cos(a)*125,yy=460+Math.sin(a)*70;
      local(p,xx,yy,1,a,()=>rect2(p,-37,-12,74,24,j%3===0?ACCENT:INK,3));
    }
    segline(p,50,494,480,494,'#b8c1d9',2);type(p,'A NEW POSSIBILITY.',52,543,29,INK,550,'left',0);
  }else if(kind===1){
    const lines=['const possibility = imagine();','','for (const idea of possibility) {','  await design(idea);','  await build(idea);','  await test(idea);','}','','return makeItReal();'];
    p.textAlign='left';p.font=F(450,25,MONO);
    lines.forEach((s,i)=>{p.fillStyle=i%3===0?ACCENT:PAPER;p.fillText(s,49,129+i*45)});
    const bar=140+(Math.sin(t*3)+1)*260;rect2(p,45,550,bar,8,ACCENT,4);
  }else{
    for(let j=0;j<20;j++){
      p.strokeStyle=j%4===0?'#607ce3':'#93a2ca';p.lineWidth=j%4===0?4:2;p.beginPath();
      for(let i=0;i<=100;i++){const x=35+i/100*890,y=230+j*13+Math.sin(i*.1+j*.18+t*2)*62+Math.cos(i*.045-t*2)*40;i?p.lineTo(x,y):p.moveTo(x,y)}p.stroke();
    }
    type(p,'Ideas in motion.',45,549,69,INK,800,'left');
  }
  return can;
}
const panelCanvases=Array.from({length:3},()=>{const a=document.createElement('canvas');a.width=960;a.height=620;return a});
function texturedTriangle(g,img,src,dst){
  const [s0,s1,s2]=src,[d0,d1,d2]=dst;
  const den=s0[0]*(s1[1]-s2[1])+s1[0]*(s2[1]-s0[1])+s2[0]*(s0[1]-s1[1]);
  if(Math.abs(den)<.0001)return;
  const solve=v=>[(v[0]*(s1[1]-s2[1])+v[1]*(s2[1]-s0[1])+v[2]*(s0[1]-s1[1]))/den,(v[0]*(s2[0]-s1[0])+v[1]*(s0[0]-s2[0])+v[2]*(s1[0]-s0[0]))/den,(v[0]*(s1[0]*s2[1]-s2[0]*s1[1])+v[1]*(s2[0]*s0[1]-s0[0]*s2[1])+v[2]*(s0[0]*s1[1]-s1[0]*s0[1]))/den];
  const X=solve(dst.map(v=>v[0])),Y=solve(dst.map(v=>v[1]));
  g.save();g.beginPath();g.moveTo(...d0);g.lineTo(...d1);g.lineTo(...d2);g.closePath();g.clip();g.transform(X[0],Y[0],X[1],Y[1],X[2],Y[2]);g.drawImage(img,0,0);g.restore();
}
function texturedQuad(g,img,vs,opt){
  // Subdivision removes the diagonal perspective seam of a single affine pair.
  const n=8,m=5;
  const pos=(u,v)=>vs[0].map((_,k)=>lerp(lerp(vs[0][k],vs[1][k],u),lerp(vs[3][k],vs[2][k],u),v));
  for(let j=0;j<m;j++)for(let i=0;i<n;i++){
    const u=i/n,v=j/m,U=(i+1)/n,V=(j+1)/m,iw=img.width,ih=img.height,src=[[u*iw,v*ih],[U*iw,v*ih],[U*iw,V*ih],[u*iw,V*ih]],dst=[pos(u,v),pos(U,v),pos(U,V),pos(u,V)].map(v=>projectP(v,opt).slice(0,2));
    texturedTriangle(g,img,[src[0],src[1],src[2]],[dst[0],dst[1],dst[2]]);texturedTriangle(g,img,[src[0],src[2],src[3]],[dst[0],dst[2],dst[3]]);
  }
}
function S5(g,u,t,shot){
  bg(g,PAPER);
  pool(g,1070,885,920,210,'rgba(112,136,214,.22)');
  type(g,shot.copy.backdrop,W/2,676,400,'#dfe5f3',900);
  const progress=smooth(seg(u,.08,1.5));
  const cards=[];
  for(let i=0;i<3;i++){
    const phase=i*TAU/3+lerp(-.75,.45,progress),rad=580;
    const x=Math.sin(phase)*rad,y=Math.cos(phase+1.2)*105,z=Math.cos(phase)*340;
    const rot=lerp(-.65,.22,progress)+i*.10;
    let vs=[[-430,278,0],[430,278,0],[430,-278,0],[-430,-278,0]].map(v=>rotateP(v,.07,rot,-.08+i*.08)).map(v=>[v[0]+x,v[1]+y,v[2]+z]);
    cards.push({i,vs,z});
  }
  cards.sort((a,b)=>b.z-a.z);
  const cardOpt={ax:.03,ay:Math.sin(u*.9)*.11,az:Math.sin(u)*-.04,dist:1900,f:1600,scale:1.30};
  const ps=[];for(let i=0;i<=150;i++){const a=i/150*TAU;ps.push(projectP([Math.cos(a)*1010,Math.sin(a)*210-10,Math.sin(a)*410],cardOpt))}lightPath(g,ps,t,.8,2.2);
  cards.forEach(({i,vs})=>{panelShadow(g,vs,cardOpt);texturedQuad(g,makePanel(i,u,shot.copy.panels[i]),vs,cardOpt)});
  if(u>1.46){const q=E.inC(seg(u,1.46,BAR));g.save();g.translate(W/2,H/2);g.rotate((1-q)*-.23);rect2(g,-W*q/2,-H,W*q,H*3,INK);g.restore();}
}

// 6. Elastic type changes its physical grammar every beat; the word breaks apart.
function S6(g,u,t,shot){
  const beat=clamp(Math.floor(u/BEAT),0,3),v=fract(u/BEAT);bg(g,beat===2?ACCENT:INK);
  const col=beat===2?INK:PAPER,word=shot.copy.words[beat],mid=(word.length-1)/2;
  const size=word.length>5?295:370;
  g.save();g.translate(W/2,H/2+90);g.rotate([-.08,.04,-.08,.055][beat]*(1+Math.sin(v*6)*.25));
  for(let j=3;j>=1;j--)alpha(g,.12/j,()=>type(g,word,-j*45*(1-v),j*35*(1-v),size,col,900));
  if(beat===0){g.scale(1+.14*Math.sin(v*Math.PI),1-.16*Math.sin(v*Math.PI));type(g,word,0,0,size,col,900);}
  if(beat===1){
    const ww=300;
    for(let j=0;j<word.length;j++){const p=spring(v-j*.035,3.8,.55);type(g,word[j],(j-mid)*ww,(1-p)*(j%2?430:-430),size,col,900);}
  }
  if(beat===2){
    for(let j=0;j<word.length;j++)local(g,(j-mid)*290+(j-mid)*190*E.inC(seg(v,.4,1)),Math.sin(j*3)*v*v*300,1,j*.13*v*v,()=>type(g,word[j],0,0,size,col,900));
  }
  if(beat===3){const q=1+.24*Math.exp(-v*5)*Math.sin(v*16);g.scale(q,1/q);type(g,word,0,0,size,col,900);}
  g.restore();
  for(let i=0;i<12;i++){let r=180+fract(v*.9+i/12)*1150;alpha(g,(1-fract(v*.9+i/12))*.21,()=>{g.strokeStyle=col;g.lineWidth=2;g.strokeRect(W/2-r,H/2-r*.52,r*2,r*1.04)});}
  if(u>BAR-.16){let q=E.inC(seg(u,BAR-.16,BAR));rect2(g,0,H*(1-q),W,H*q,PAPER)}
}

// 7. A physical arrival, then one clear second for recognition.
function S7(g,u){
  bg(g,PAPER);
  // The light gathers under the lockup and fades into a quiet final hold.
  pool(g,1020,590,860,275,'rgba(146,164,233,.16)',1-smooth(seg(u,.1,1.10))*.65);
  const snap=spring(u,3.4,.6),centerX=1100,baseline=643;
  for(let j=3;j>=1;j--)alpha(g,.10*(1-clamp(u/.55)),()=>type(g,BRAND.name,centerX+(1-snap)*j*38,baseline+(1-snap)*j*54,344,INK,900));
  local(g,centerX,baseline,1+(1-snap)*.14,(1-snap)*-.12,()=>type(g,BRAND.name,0,0,344,INK,900));
  const q=spring(Math.max(0,u-.08),3.2,.62);
  local(g,348,540,1,0,()=>{
    if(q<=0)return;
    g.save();g.globalAlpha=.11*clamp(q);g.filter='blur(12px)';g.fillStyle='#25265b';g.beginPath();g.ellipse(9,150,121*q,13*q,0,0,TAU);g.fill();g.restore();
    const opt={ax:.09,ay:lerp(-1.25,-.16,clamp(q)),az:.018,dist:1600,f:1600,scale:.44*q,cx:0,cy:0};markMesh(g,opt);
  });
  alpha(g,QOUT(seg(u,.23,.65)),()=>caption(g,BRAND.tagline,W/2,800,65,INK,'center'));
  alpha(g,QOUT(seg(u,.42,.85)),()=>{g.fillStyle='#68718c';g.font=F(500,19,MONO);g.textAlign='center';g.fillText(BRAND.credit,W/2,887)});
  const underline=QOUT(seg(u,.30,.92));
  alpha(g,.8*(1-smooth(seg(u,1.1,1.75))*.6),()=>segline(g,W/2-56,834,W/2-56+112*underline,834,ACCENT,2.5));
}

// Scene names used by project.json shots. `beats` is each scene's native length on the scene clock.
const SCENE_LIBRARY={ignition:{draw:S0,beats:4},thought:{draw:S1,beats:4},transform:{draw:S2,beats:4},possibility:{draw:S3,beats:4},build:{draw:S4,beats:4},create:{draw:S5,beats:4},momentum:{draw:S6,beats:4},signature:{draw:S7,beats:4}};
