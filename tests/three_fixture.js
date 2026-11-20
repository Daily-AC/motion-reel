// Known-answer scenes for the three.js path, used by tests/check_bundle.py in place of a project's scenes.js.
// Each shot's copy carries the parameters. Units: world units; the camera looks down -z unless stated.
function solid2d(g, u, t, shot) { g.fillStyle = shot.copy.color; g.fillRect(-200, -200, W + 400, H + 400); }

async function solid3d(THREE) {
  const scene = new THREE.Scene(), color = new THREE.Color();
  return { scene, rig: () => ({ position: [0, 0, 5], target: [0, 0, 0], fov: 30 }),
    update(u, t, shot) { scene.background = color.set(shot.copy.color); } };
}

// A static lit set: soft shadows from the light sample, depth of field from the lens sample.
async function lit(THREE, renderer) {
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
  const scene = new THREE.Scene(); scene.background = new THREE.Color('#1c2030');
  const std = (color, roughness) => new THREE.MeshStandardMaterial({ color, roughness });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), std('#b4b8c4', 0.8));
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true;
  const box = new THREE.Mesh(new THREE.BoxGeometry(2, 2, 2), std('#e0603a', 0.5));
  box.position.set(-1.7, 1, 0); box.rotation.y = 0.5; box.castShadow = box.receiveShadow = true;
  const ball = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 24), std('#4a7cf0', 0.3));
  ball.position.set(1.7, 1, 0.6); ball.castShadow = true;
  const key = new THREE.DirectionalLight('#ffffff', 2.4); key.castShadow = true; key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -8, right: 8, top: 8, bottom: -8, near: 1, far: 30 });
  scene.add(floor, box, ball, key, key.target, new THREE.HemisphereLight('#c8d0ff', '#302820', 0.7));
  return { scene,
    rig: () => ({ position: [0, 4, 9], target: [0, 1, 0], focus: [1.7, 1, 0.6], aperture: 0.15, fov: 32 }),
    update(u, t, shot, smp) { key.position.set(4 + smp.light[0] * 0.9, 9, 3 + smp.light[1] * 0.9); } };
}

// A flat light card crossing the frame at copy.speed units per second; it is centred at scene time copy.at.
async function mover(THREE) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color('#404040');
  const card = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.MeshBasicMaterial({ color: '#e0e0e0' }));
  scene.add(card);
  return { scene, rig: () => ({ position: [0, 0, 10], target: [0, 0, 0], fov: 30 }),
    update(u, t, shot) { card.position.x = shot.copy.speed * (u - shot.copy.at); } };
}

// Two checkered cards of equal screen size: near (left, depth 10) and far (right, depth 30, three times larger).
async function dof(THREE) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color('#808080');
  const c = document.createElement('canvas'); c.width = c.height = 192; const g = c.getContext('2d');
  for (let y = 0; y < 32; y++) for (let x = 0; x < 32; x++) { g.fillStyle = (x + y) % 2 ? '#f0f0f0' : '#202020'; g.fillRect(x * 6, y * 6, 6, 6); }
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.generateMipmaps = false; tex.minFilter = THREE.LinearFilter;
  const mat = new THREE.MeshBasicMaterial({ map: tex });
  const near = new THREE.Mesh(new THREE.PlaneGeometry(3.6, 3.6), mat); near.position.set(-2.4, 0, -10);
  const far = new THREE.Mesh(new THREE.PlaneGeometry(10.8, 10.8), mat); far.position.set(7.2, 0, -30);
  scene.add(near, far);
  return { scene, rig: (u, t, shot) => ({ position: [0, 0, 0], target: [0, 0, -1], focus: [0, 0, -shot.copy.focus], aperture: shot.copy.aperture, fov: 30 }) };
}

// A small unlit disc of radiance copy.level on a dark field (linear 0.02), with bloom copy.bloom above threshold 1.
async function glow(THREE) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0.02, 0.02, 0.02);
  const disc = new THREE.Mesh(new THREE.CircleGeometry(0.2, 64), new THREE.MeshBasicMaterial({ color: new THREE.Color() }));
  scene.add(disc);
  return { scene, rig: (u, t, shot) => ({ position: [0, 0, 10], target: [0, 0, 0], fov: 30, bloom: shot.copy.bloom, bloomThreshold: 1 }),
    update(u, t, shot) { disc.material.color.setRGB(shot.copy.level, shot.copy.level, shot.copy.level, THREE.LinearSRGBColorSpace); } };
}

const SCENE_LIBRARY = { solid2d: { draw: solid2d, beats: 2 }, solid3d: { three: solid3d, beats: 2 }, lit: { three: lit, beats: 2 }, mover: { three: mover, beats: 2 }, dof: { three: dof, beats: 2 }, glow: { three: glow, beats: 2 } };
