// Mixed 2D/3D example. The 2D panel is drawn by one function; the 3D monitor shows the same function as a texture,
// so the cut from shot 1 to shot 2 is a match cut and the screen close-up keeps the designed colors.
// Scene clocks run at the project tempo, so u is seconds since the cut.
const TAU = Math.PI * 2, PRESS = 1.5, RUN = 1.2;              // the button is pressed at 1.5 s; the render bar fills in 1.2 s
const ease = x => { x = clamp(x); return x * x * (3 - 2 * x); };

// The UI, in 1920×1080 design units. t is film time, so the bar keeps running across the cut.
function panel(g, t) {
  g.fillStyle = PAPER; g.fillRect(-200, -200, 2320, 1480);
  rrect(g, 330, 170, 1260, 740, 40); g.fillStyle = '#FFFFFF'; g.fill();
  g.textAlign = 'left'; g.fillStyle = INK; g.font = F(800, 76); g.fillText(copyFor('card').title, 420, 330);
  g.fillStyle = mix(RGB.ink, RGB.paper, 0.5); g.font = F(500, 34); g.fillText(copyFor('card').subtitle, 422, 392);
  const p = clamp((TF - PRESS) / RUN);                         // whole-frame time: a number drawn from subframe time would ghost
  rrect(g, 420, 560, 1080, 20, 10); g.fillStyle = '#E2E6F1'; g.fill();
  if (p > 0) { rrect(g, 420, 560, 1080 * ease(p), 20, 10); g.fillStyle = ACCENT; g.fill(); }
  g.fillStyle = INK; g.font = F(650, 30, MONO); g.textAlign = 'right'; g.fillText(`${Math.round(100 * ease(p))}%`, 1500, 640);
  // button: a spring squash on the press, color settles to ink when the job runs
  const k = t < PRESS - 0.12 ? 0 : t < PRESS ? (t - PRESS + 0.12) / 0.12 : 1 - spring(t - PRESS, 4, 0.35);
  const s = 1 - 0.08 * clamp(k, -1, 1);
  g.save(); g.translate(1360, 780); g.scale(s, s);
  rrect(g, -140, -52, 280, 104, 52); g.fillStyle = t < PRESS ? ACCENT : mix(RGB.accent, RGB.ink, 0.85); g.fill();
  g.fillStyle = '#FFFFFF'; g.font = F(800, 38); g.textAlign = 'center'; g.fillText(t < PRESS ? copyFor('card').button : copyFor('card').running, 0, 13);
  g.restore();
}

function card(g, u, t) {                                        // shot 1: the panel itself, frame 0 is already finished
  panel(g, t);
  // pointer travels to the button and clicks on the press
  const a = E.outC(clamp(u / (PRESS - 0.2)));
  const x = lerp(1180, 1395, a), y = lerp(980, 800, a);
  g.save(); g.translate(x, y); g.fillStyle = INK; g.beginPath(); g.moveTo(0, 0); g.lineTo(0, 44); g.lineTo(12, 33); g.lineTo(21, 52); g.lineTo(29, 48); g.lineTo(20, 30); g.lineTo(36, 30); g.closePath(); g.fill(); g.restore();
}

// The character's timeline is data: each hop takes off at u (scene seconds), moves dx, rises h and stays `air` s in the air.
// Squash and stretch come from these displacements; the score reads the same table for the landings.
const HOPS = [{ u: 0.42, dx: 0, h: 2.2, air: 0.18 }, { u: 0.78, dx: -2.5, h: 3.4, air: 0.24 }, { u: 1.2, dx: 0, h: 2.2, air: 0.18 }];
const HOME = [27, 0, 12];
function pip(u) {                                               // → position, vertical scale (area-preserving), hop count
  let x = HOME[0], y = 0, sy = 1;
  for (const h of HOPS) {
    const a = (u - h.u) / h.air;
    if (a < 0) { const c = (u - h.u + 0.1) / 0.1; if (c > 0) sy += 0.14 * ease((c - 0.6) / 0.4) - 0.18 * Math.sin(Math.PI * c); break; } // crouch, then spring up
    if (a < 1) { x += h.dx * a; y = 4 * h.h * a * (1 - a); sy += 0.14 * Math.abs(1 - 2 * a); break; }         // stretch with vertical speed
    x += h.dx; const d = u - h.u - h.air; sy += Math.exp(-d * 14) * (0.14 * Math.cos(d * 38) - 0.3 * Math.sin(d * 38)); // landing squash, continuous at contact
  }
  return { position: [x, y, HOME[2]], sy };
}
// Keyframe channels: [u, value] pairs eased between keys. Yaw turns from the screen to the camera; eyes blink.
const channel = (keys, u) => { let i = 0; while (i + 1 < keys.length && u >= keys[i + 1][0]) i++; const [u0, v0] = keys[i], [u1, v1] = keys[Math.min(i + 1, keys.length - 1)]; return u1 === u0 ? v0 : lerp(v0, v1, ease((u - u0) / (u1 - u0))); };
const FACE_SCREEN = Math.atan2(-HOME[0], -HOME[2]);
const YAW = [[0, FACE_SCREEN], [0.7, FACE_SCREEN], [1.0, FACE_SCREEN - 1.05]];   // turns to the camera after the second hop
const BLINK = [[0, 1], [0.2, 1], [0.24, 0.1], [0.3, 1]];

async function desk(THREE, renderer) {
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
  const scene = new THREE.Scene(); scene.background = new THREE.Color(INK);
  const std = (color, roughness = 0.6, metalness = 0) => new THREE.MeshStandardMaterial({ color, roughness, metalness });
  const box = (w, h, d, m, x, y, z) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); b.position.set(x, y, z); b.castShadow = b.receiveShadow = true; scene.add(b); return b; };
  box(170, 3, 70, std('#4a5068', 0.75), 0, -1.5, 10);                                   // desk, top at y = 0
  box(50, 29, 1.6, std('#141722', 0.35), 0, 24, -0.81);                                // bezel
  box(4, 11, 2, std('#2b2f3e', 0.4), 0, 5.5, -3); box(18, 1, 10, std('#2b2f3e', 0.4), 0, 0.5, -2);
  // The screen shows the 2D panel at its 1920×1080 design size times the output scale, so a 4K close-up stays sharp.
  const ui = document.createElement('canvas'); ui.width = 1920 * SCALE; ui.height = 1080 * SCALE; const ug = ui.getContext('2d');
  const tex = new THREE.CanvasTexture(ui); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(48, 27), new THREE.MeshBasicMaterial({ map: tex })); screen.position.set(0, 24, 0.02); scene.add(screen);
  // character: an accent capsule scaled about its feet, with two eyes
  const body = new THREE.Group(), pivot = new THREE.Group();
  const capsule = new THREE.Mesh(new THREE.CapsuleGeometry(2.2, 2.2, 8, 24), std(ACCENT, 0.45)); capsule.position.y = 3.3; capsule.castShadow = true;
  const eyeMat = std(INK, 0.3), eyes = [-0.85, 0.85].map(x => { const e = new THREE.Mesh(new THREE.SphereGeometry(0.42, 16, 12), eyeMat); e.position.set(x, 4.3, 1.95); return e; });
  body.add(capsule, ...eyes); pivot.add(body); scene.add(pivot);
  const lamp = new THREE.SpotLight('#ffe6c8', 40000, 0, 0.5, 0.45, 2); lamp.castShadow = true; lamp.shadow.mapSize.set(2048, 2048); lamp.shadow.bias = -0.0004;
  lamp.target.position.set(12, 0, 6); scene.add(lamp, lamp.target, new THREE.HemisphereLight('#b9c4ff', '#20180f', 1.1));
  const head = u => { const p = pip(u).position; return [p[0], p[1] + 4.2, p[2]]; };
  return {
    scene,
    frame(u, t) { ug.setTransform(SCALE, 0, 0, SCALE, 0, 0); panel(ug, t); tex.needsUpdate = true; },
    rig(u, t, shot) {
      if (shot.scene === 'screen') {                 // starts exactly where the 2D panel was, then reveals the room
        const close = frameRect([0, 24, 0], [0, 0, 1], 48), k = E.ioC(clamp((u - 0.15) / 0.85));
        return { ...close, position: [lerp(0, 34, k), lerp(24, 34, k), lerp(close.position[2], 122, k)], target: [lerp(0, 9, k), lerp(24, 16, k), 0],
          focus: [lerp(0, HOME[0], k), lerp(24, 4, k), lerp(0, HOME[2], k)], aperture: lerp(0, 0.5, k), exposure: 1, vw: lerp(1, 0.8, k), near: 5, far: 600 };
      }
      const r = reactRig(head(u), FACE_SCREEN, -1.05, lerp(30, 26, u / 2), 2.5, 28);   // off the face, toward the screen
      return { ...r, target: [r.target[0], r.target[1] - 1.2, r.target[2]], aperture: 0.6, exposure: 1, shoulder: true, near: 2, far: 600 };
    },
    update(u, t, shot, smp) {
      lamp.position.set(-40 + smp.light[0] * 7, 72, 48 + smp.light[1] * 7);              // the light sample softens shadows
      const react = shot.scene === 'react', p = pip(react ? u : 0);
      pivot.position.set(...p.position); pivot.scale.set(1 / Math.sqrt(p.sy), p.sy, 1 / Math.sqrt(p.sy));
      pivot.rotation.y = channel(YAW, react ? u : 0);
      const blink = channel(BLINK, react ? u : 0); eyes.forEach(e => e.scale.set(1, blink, 1));
    },
  };
}

function endCard(g, u, t) {                                     // the character's accent becomes the mark beside the name
  bg(g, INK);
  const a = E.outBack(clamp(u / 0.5), 1.4);
  g.save(); g.translate(W / 2 - 300, H / 2 - 8); g.scale(1, lerp(0.7, 1, a)); rrect(g, -38, -64, 76, 128, 38); g.fillStyle = ACCENT; g.fill(); g.restore();
  g.fillStyle = PAPER; g.font = F(850, 150); g.textAlign = 'left'; textLS(g, BRAND.name, W / 2 - 220, H / 2 + 52, -5);
  g.globalAlpha = clamp((u - 0.35) / 0.4); g.font = F(500, 36); g.fillStyle = mix(RGB.paper, RGB.ink, 0.35); g.fillText(BRAND.tagline, W / 2 - 214, H / 2 + 130); g.globalAlpha = 1;
}

// screen and react are two framings of one set: they share the desk() instance.
const SCENE_LIBRARY = { card: { draw: card, beats: 4 }, screen: { three: desk, beats: 2 }, react: { three: desk, beats: 4 }, end: { draw: endCard, beats: 4 } };
