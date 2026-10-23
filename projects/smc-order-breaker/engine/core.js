// Engine core: renderer, the graph-paper world, lights, camera rig, post FX
// and the scene timeline. renderFrame(t) draws the frame at time t (seconds)
// from scratch, so frames can be rendered in any order and in parallel.

import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import * as A from './anim.js';

export { THREE };
export const W = 1080, H = 1920;
export const GRID = 1; // one graph-paper cell = one world unit

// ---------------------------------------------------------------- renderer
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1);
renderer.setSize(W, H);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping; // keeps the paper pure white
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.VSMShadowMap;
document.getElementById('stage').appendChild(renderer.domElement);

export const scene = new THREE.Scene();
scene.background = new THREE.Color('#ffffff');
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.42;

// ---------------------------------------------------------------- paper
function gridTexture() {
  const S = 1024, cells = 8, step = S / cells;
  const c = document.createElement('canvas');
  c.width = c.height = S;
  const g = c.getContext('2d');
  g.fillStyle = '#ffffff';
  g.fillRect(0, 0, S, S);
  // faint paper fibre so large flat areas never look digital
  const rnd = A.rng(7);
  for (let i = 0; i < 9000; i++) {
    const v = 236 + Math.floor(rnd() * 14);
    g.fillStyle = `rgba(${v},${v},${v + 3},${0.05 + rnd() * 0.05})`;
    g.fillRect(rnd() * S, rnd() * S, 1 + rnd() * 2, 1);
  }
  g.strokeStyle = '#c3c8d0';
  g.lineWidth = 4;
  for (let i = 0; i <= cells; i++) {
    const p = i * step;
    g.beginPath(); g.moveTo(p, 0); g.lineTo(p, S); g.stroke();
    g.beginPath(); g.moveTo(0, p); g.lineTo(S, p); g.stroke();
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = renderer.capabilities.getMaxAnisotropy();
  t.colorSpace = THREE.SRGBColorSpace;
  t.generateMipmaps = true;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  return t;
}
const PAPER = 640; // world units square
const paperTex = gridTexture();
paperTex.repeat.set(PAPER / 8, PAPER / 8); // grid lines land on integer coordinates
export const paper = new THREE.Mesh(
  new THREE.PlaneGeometry(PAPER, PAPER),
  new THREE.MeshBasicMaterial({ map: paperTex })
);
scene.add(paper);
const shadowCatcher = new THREE.Mesh(
  new THREE.PlaneGeometry(PAPER, PAPER),
  new THREE.ShadowMaterial({ color: '#141b28', opacity: 0.3, depthWrite: false })
);
shadowCatcher.position.z = 0.002;
shadowCatcher.receiveShadow = true;
scene.add(shadowCatcher);

// ---------------------------------------------------------------- lights
const hemi = new THREE.HemisphereLight('#ffffff', '#c9d0db', 0.95);
scene.add(hemi);
const key = new THREE.DirectionalLight('#ffffff', 2.7);
key.castShadow = true;
key.shadow.mapSize.set(2048, 2048);
key.shadow.radius = 9;
key.shadow.blurSamples = 16;
key.shadow.bias = -0.0004;
const sc = key.shadow.camera;
sc.left = -16; sc.right = 16; sc.top = 22; sc.bottom = -22; sc.near = 1; sc.far = 80;
scene.add(key, key.target);
const rim = new THREE.DirectionalLight('#fff6ec', 0.9);
scene.add(rim, rim.target);
export const lights = { hemi, key, rim, shadow: shadowCatcher };
const KEY_OFFSET = new THREE.Vector3(-6, 9, 12);
const RIM_OFFSET = new THREE.Vector3(10, 6, 8);

// ---------------------------------------------------------------- camera
export const camera = new THREE.PerspectiveCamera(28, W / H, 0.5, 600);
const camState = {};
function camDefaults() {
  Object.assign(camState, { pos: [0, 0, 48], target: [0, 0, 0], fov: 28, roll: 0 });
}
// Distance at which `width` world units of paper fill the frame horizontally.
export function distForWidth(width, fov = camState.fov) {
  const tv = Math.tan(THREE.MathUtils.degToRad(fov) / 2);
  return width / 2 / (tv * (W / H));
}
export const cam = {
  // Direct placement.
  set({ pos, target, fov, roll } = {}) {
    if (pos) camState.pos = pos;
    if (target) camState.target = target;
    if (fov !== undefined) camState.fov = fov;
    if (roll !== undefined) camState.roll = roll;
  },
  // Frame `width` units of paper centred on (cx, cy). pitch tilts the camera
  // to look up the paper (degrees, + looks from below), yaw swings it
  // sideways, roll rotates the frame, dolly multiplies the distance.
  frame({ cx = 0, cy = 0, width = 13.5, pitch = 0, yaw = 0, roll = 0, fov = 28, dolly = 1, tz = 0 } = {}) {
    camState.fov = fov;
    const d = distForWidth(width, fov) * dolly;
    const p = THREE.MathUtils.degToRad(pitch), y = THREE.MathUtils.degToRad(yaw);
    camState.target = [cx, cy, tz];
    camState.pos = [cx + d * Math.sin(y) * Math.cos(p), cy - d * Math.sin(p), tz + d * Math.cos(y) * Math.cos(p)];
    camState.roll = roll;
  },
  get state() { return camState; },
};

function applyCamera(t) {
  const [px, py, pz] = camState.pos, [tx, ty, tz] = camState.target;
  // handheld-style shake, deterministic in t
  const s = fx.shake;
  const sx = s ? A.noise1(t * 17, 1) * s : 0, sy = s ? A.noise1(t * 19, 2) * s : 0, sr = s ? A.noise1(t * 13, 3) * s * 0.6 : 0;
  camera.fov = camState.fov;
  camera.position.set(px + sx, py + sy, pz);
  camera.up.set(0, 1, 0);
  camera.lookAt(tx + sx, ty + sy, tz);
  camera.rotateZ(THREE.MathUtils.degToRad(camState.roll + sr * 2));
  camera.updateProjectionMatrix();
  camera.updateMatrixWorld();
  // the key light follows what the camera looks at so shadows stay sharp
  const tgt = new THREE.Vector3(tx, ty, 0);
  key.target.position.copy(tgt);
  key.position.copy(tgt).add(KEY_OFFSET);
  rim.target.position.copy(tgt);
  rim.position.copy(tgt).add(RIM_OFFSET);
}

let curT = 0;
// World position -> pixel position on the 1080x1920 frame. Uses the camera
// as set so far this frame, so call it after setting the camera.
export function toScreen(v) {
  applyCamera(curT);
  const p = (v.isVector3 ? v.clone() : new THREE.Vector3(...v)).project(camera);
  return { x: (p.x * 0.5 + 0.5) * W, y: (-p.y * 0.5 + 0.5) * H, z: p.z };
}
// Pixel size of one world unit at a world position (for sizing DOM labels).
export function unitPx(v) {
  const a = toScreen(v), b = toScreen(v.isVector3 ? v.clone().add(new THREE.Vector3(1, 0, 0)) : [v[0] + 1, v[1], v[2]]);
  return Math.hypot(b.x - a.x, b.y - a.y);
}

// Pixel (x, y) -> the world point it shows on the plane z = const.
export function screenToWorld(x, y, z = 0) {
  applyCamera(curT);
  const ndc = new THREE.Vector3((x / W) * 2 - 1, -(y / H) * 2 + 1, 0.5).unproject(camera);
  const dir = ndc.sub(camera.position).normalize();
  const k = (z - camera.position.z) / dir.z;
  return camera.position.clone().add(dir.multiplyScalar(k));
}
// Pin a 3D object to a screen position: place it on the plane z under
// pixel (x, y) and scale it so `worldHeight` units look `heightPx` tall.
// It stays a real lit 3D object (shading, shadow) while the camera moves.
export function pin(obj, { x = 540, y = 470, z = 0.6, heightPx = 118, worldHeight = 1, scale = 1 } = {}) {
  const p = screenToWorld(x, y, z);
  obj.position.copy(p);
  const upx = unitPx(p);
  obj.scale.setScalar(Math.max(1e-4, (heightPx / (worldHeight * upx)) * scale));
  return p;
}

// ---------------------------------------------------------------- post FX
const FinalShader = {
  uniforms: {
    tDiffuse: { value: null },
    uZoom: { value: 0 }, uZoomC: { value: new THREE.Vector2(0.5, 0.5) },
    uDir: { value: new THREE.Vector2(0, 0) },
    uCA: { value: 0 },
    uFlash: { value: 0 }, uFlashColor: { value: new THREE.Color('#ffffff') },
    uVig: { value: 0.16 }, uContrast: { value: 1.04 }, uSat: { value: 1.06 }, uExposure: { value: 1.0 },
    uFade: { value: 0 }, uFadeColor: { value: new THREE.Color('#ffffff') },
  },
  vertexShader: /* glsl */ `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: /* glsl */ `
    uniform sampler2D tDiffuse; uniform float uZoom; uniform vec2 uZoomC; uniform vec2 uDir; uniform float uCA;
    uniform float uFlash; uniform vec3 uFlashColor; uniform float uVig; uniform float uContrast; uniform float uSat;
    uniform float uExposure; uniform float uFade; uniform vec3 uFadeColor; varying vec2 vUv;
    vec3 tap(vec2 uv, vec2 ca){ return vec3(texture2D(tDiffuse, uv + ca).r, texture2D(tDiffuse, uv).g, texture2D(tDiffuse, uv - ca).b); }
    void main(){
      vec2 uv = vUv;
      vec2 ca = (uv - 0.5) * uCA * 0.012;
      vec3 col;
      if (uZoom + length(uDir) < 0.0005) {
        col = uCA > 0.0001 ? tap(uv, ca) : texture2D(tDiffuse, uv).rgb;
      } else {
        col = vec3(0.0);
        vec2 toC = uZoomC - uv;
        for (int i = 0; i < 28; i++) {
          float f = float(i) / 27.0;
          vec2 o = toC * uZoom * f + uDir * (f - 0.5);
          col += tap(uv + o, ca * (1.0 + f));
        }
        col /= 28.0;
      }
      col *= uExposure;
      col = (col - 0.5) * uContrast + 0.5;
      float l = dot(col, vec3(0.2126, 0.7152, 0.0722));
      col = mix(vec3(l), col, uSat);
      vec2 q = uv - 0.5; q.x *= 0.9;
      col *= 1.0 - uVig * smoothstep(0.25, 0.85, length(q) * 1.25);
      col = mix(col, uFlashColor, clamp(uFlash, 0.0, 1.0));
      col = mix(col, uFadeColor, clamp(uFade, 0.0, 1.0));
      gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
    }`,
};

const rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 });
const composer = new EffectComposer(renderer, rt);
composer.setPixelRatio(1);
composer.setSize(W, H);
composer.addPass(new RenderPass(scene, camera));
const bokeh = new BokehPass(scene, camera, { focus: 48, aperture: 0.0006, maxblur: 0.008 });
bokeh.enabled = false;
composer.addPass(bokeh);
composer.addPass(new OutputPass());
const finalPass = new ShaderPass(FinalShader);
composer.addPass(finalPass);

// Per-frame FX state. Scenes write to it; it is reset before every frame.
export const fx = {};
function fxDefaults() {
  Object.assign(fx, {
    zoom: 0, zoomC: [0.5, 0.5], dir: [0, 0], ca: 0, flash: 0, flashColor: '#ffffff',
    vignette: 0.16, contrast: 1.04, saturation: 1.06, exposure: 1.0, fade: 0, fadeColor: '#ffffff',
    shake: 0, overlayBlur: 0, overlayScale: 1,
    dof: null, // { focus: distance, aperture, maxblur }
  });
}
function applyFx() {
  const u = finalPass.uniforms;
  u.uZoom.value = fx.zoom; u.uZoomC.value.set(...fx.zoomC);
  u.uDir.value.set(...fx.dir); u.uCA.value = fx.ca;
  u.uFlash.value = fx.flash; u.uFlashColor.value.set(fx.flashColor);
  u.uVig.value = fx.vignette; u.uContrast.value = fx.contrast; u.uSat.value = fx.saturation;
  u.uExposure.value = fx.exposure; u.uFade.value = fx.fade; u.uFadeColor.value.set(fx.fadeColor);
  if (fx.dof) {
    bokeh.enabled = true;
    bokeh.uniforms.focus.value = fx.dof.focus;
    bokeh.uniforms.aperture.value = fx.dof.aperture ?? 0.0006;
    bokeh.uniforms.maxblur.value = fx.dof.maxblur ?? 0.008;
  } else bokeh.enabled = false;
  const ov = document.getElementById('overlay');
  const blur = fx.overlayBlur + fx.zoom * 40 + Math.hypot(...fx.dir) * 120;
  ov.style.filter = blur > 0.05 ? `blur(${blur.toFixed(2)}px)` : 'none';
  ov.style.transform = fx.overlayScale !== 1 ? `scale(${fx.overlayScale})` : 'none';
  ov.style.opacity = String(1 - Math.min(1, fx.fade));
}

// Transitions between scenes, applied on top of whatever scenes set.
//   zoom: radial blur punching in, peaking at `at`
//   whip: directional blur, dir = [x, y] in uv units at peak
const transitions = [];
export function addTransition(tr) { transitions.push(tr); }
function applyTransitions(t) {
  for (const tr of transitions) {
    const dur = tr.dur ?? 0.36;
    const k = A.pulse(t, tr.at, dur);
    if (k <= 0) continue;
    const s = tr.strength ?? 1;
    if (tr.kind === 'whip') {
      const d = tr.dir ?? [0.16, 0];
      fx.dir = [fx.dir[0] + d[0] * k * s, fx.dir[1] + d[1] * k * s];
    } else {
      fx.zoom += 0.22 * k * s;
      if (tr.center) fx.zoomC = tr.center;
    }
    fx.ca += 1.6 * k * s;
    fx.flash = Math.max(fx.flash, (tr.flash ?? 0.12) * k);
  }
}

// ---------------------------------------------------------------- timeline
const scenes = [];
const overlayRoot = document.getElementById('overlay');
let words = [];
export function setWords(w) { words = w; }
const norm = (s) => s.toLowerCase().replace(/[^a-z]/g, '');
// Start time of the nth (1-based) occurrence of a script word.
export function wt(word, nth = 1, which = 'start') {
  const k = norm(word);
  let n = 0;
  for (const w of words) if (norm(w.word) === k && ++n === nth) return w[which];
  throw new Error(`word not found: ${word} #${nth}`);
}
export function getWords() { return words; }

export function addScene(def) { scenes.push(def); }

export async function initScenes(ctxBase) {
  for (const s of scenes) {
    s.group = new THREE.Group();
    s.group.name = s.id;
    scene.add(s.group);
    s.dom = document.createElement('div');
    s.dom.className = 'scene-layer';
    s.dom.dataset.scene = s.id;
    overlayRoot.appendChild(s.dom);
    s.ctx = { ...ctxBase, group: s.group, dom: s.dom, start: s.start, end: s.end };
    if (s.init) await s.init(s.ctx);
  }
}

export function renderFrame(t) {
  curT = t;
  fxDefaults();
  camDefaults();
  // Scenes run in order; later scenes (e.g. captions) draw over earlier ones.
  for (const s of scenes) {
    const active = t >= s.start && t < s.end;
    s.group.visible = active;
    s.dom.style.display = active ? 'block' : 'none';
    if (active && s.update) s.update(t, t - s.start, s.ctx);
  }
  applyTransitions(t);
  applyCamera(t);
  applyFx();
  composer.render();
  return true;
}

export { renderer, composer };
