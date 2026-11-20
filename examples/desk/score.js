  // Cues come from the shot list and from the scene's own event table (HOPS), so sound and motion share one source.
  const b = n => n * SPB, at = id => TIMELINE.shots[shotIndex(id)].startBeat, react = SHOTS[shotIndex('react')];
  chime(0, 523.25, .05); air(.02, .6, .12, 5200, 300);                       // sound at frame 0
  for (const [t, a] of HITS) if (t > 0) { whoosh(Math.max(0, t - .22), t, .2 + a * .01, 350, 5200); impact(t, .3 + a * .02); }
  const close = at('end');
  for (let n = 0; n < close; n++) { const t = b(n); kick(t, n % 4 === 0 ? 1 : .8); pump.gain.setValueAtTime(.25, t); pump.gain.setTargetAtTime(1, t + .014, .09); if (n % 2) clap(t, .3); hat(t + SPB * .5, .08, n % 2 === 0, .35); }
  const CH = [[174.61, 220, 261.63, 329.63], [146.83, 174.61, 220, 293.66]];
  for (let n = 0; n < close / 4; n++) for (const q of [0, 1.5, 2.75]) stab(b(4 * n + q), CH[n % 2], .045, .1, 2200);
  click(PRESS, .2); bloop(PRESS + .01, 300, 900, .16);                       // the button press
  for (let n = 0; n < 6; n++) tock(PRESS + .12 + n * RUN / 6, .05, 900 + n * 110);
  chime(PRESS + RUN, 1046.5, .06);                                          // the bar completes: the cause of the reaction
  for (const h of HOPS) { const land = react.start + (h.u + h.air) / react.rate; chirp(react.start + h.u / react.rate, 500, 900 + h.h * 120, h.air, .05); tock(land, .12, 700); }
  stab(SHOT('end'), [174.61, 220, 261.63, 349.23, 523.25], .07, .42, 2300); chime(SHOT('end') + .09, 698.46, .12); chime(SHOT('end') + .24, 880, .09);
  master.gain.setValueAtTime(.7, DUR - .3); master.gain.linearRampToValueAtTime(0, DUR);
