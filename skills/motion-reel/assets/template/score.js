  // Cues follow the shot list: SHOT('id') is a cut in seconds, at('id') its beat. Camera, geometry and percussion share HITS.
  const b = n => n * SPB, bar = n => n * 4 * SPB, at = id => TIMELINE.shots[shotIndex(id)].startBeat;
  impact(0, .8);air(.03,.72,.22,6200,250);
  for(const [t,a] of HITS){
    if(t>0){whoosh(Math.max(0,t-.24),t,.25+a*.009,350,5400);impact(t,.40+a*.023)}
  }
  // The groove runs until the closing lockup; the kick drops out on the beat before momentum.
  const close=at('signature'),drop=at('momentum')-1;
  for(let n=0;n<close;n++){
    const t=b(n);if(n!==drop)kick(t,n%4===0?1.0:.82);
    pump.gain.setValueAtTime(.22,t);pump.gain.setTargetAtTime(1,t+.014,.09);
    if(n%2===1)clap(t,.35);
    hat(t+SPB*.5,.1,n%2===0, .36);
    if(n>=at('transform'))hat(t+SPB*.25,.058,false,-.45);
    if(n>=at('build'))hat(t+SPB*.75,.055,false,.55);
  }
  const CH=[[174.61,207.65,261.63,349.23],[155.56,196,233.08,311.13],[138.59,174.61,207.65,277.18],[130.81,155.56,196,261.63]];
  const ROOTS=[43.65,38.89,34.65,32.7];
  for(let n=0;n<close/4;n++){
    for(const q of [.5,1.25,2.5,3.25])bass(bar(n)+b(q),ROOTS[n%4]*(q===3.25?2:1),.13,.21);
    for(const q of [0,1.5,2.75])stab(bar(n)+b(q),CH[n%4],n<2?.04:.065,.09,2000+n*250);
    for(let q=0;q<4;q++)blip(bar(n)+b(q+.25),CH[n%4][q]*2,.018,q/2-1);
  }
  riser(SHOT('possibility')-.75,SHOT('possibility'),.19);
  for(let n=0;n<8;n++)tock(SHOT('transform')+n*SPB*.5,.10,800+n*125);
  for(let n=0;n<8;n++)blip(SHOT('create')+n*SPB*.5,349.23*(1+n%3*.25),.043,n%2?-.45:.45);
  riser(SHOT('momentum'),SHOT('signature'),.18);
  for(let n=0;n<16;n++)snare(SHOT('momentum')+n*SPB*.25,.03+n*.003);
  for(let n=0;n<5;n++)tock(SHOT('signature')-.6+n*SPB*.25,.18,900+n*180);
  // Recurring glass motif belongs to the single travelling light, repeated in new materials.
  for(const start of [0,SHOT('transform'),SHOT('build')]){
    chime(start+.12,698.46,.028);chime(start+.29,830.61,.021);chime(start+.46,1046.5,.017);
  }
  for(let n=0;n<6;n++)tock(SHOT('build')+.12+n*SPB*.5,.055,1120+n*125);
  stab(SHOT('signature'),[174.61,207.65,261.63,349.23,523.25],.068,.42,2300);
  chime(SHOT('signature')+.09,698.46,.13);chime(SHOT('signature')+.24,830.61,.1);chime(SHOT('signature')+.39,1046.5,.08);
  master.gain.setValueAtTime(.7,DUR-.30);master.gain.linearRampToValueAtTime(0,DUR);
