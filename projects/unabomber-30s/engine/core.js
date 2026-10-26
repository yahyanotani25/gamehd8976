// Engine core: renderer, the cinematic void world, lights, camera rig, the
// scene timeline, transitions and the per-frame render. renderFrame(t) draws
// the frame at time t (seconds) from scratch, so frames can be rendered in
// any order and in parallel browsers.

import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import * as A from './anim.js';
import * as post from './post.js';
import * as media from './media.js';
import * as domtex from './domtex.js';

export { THREE };
export const W = 1920, H = 1080;
export const GLOW_LAYER = 10;

// ---------------------------------------------------------------- renderer
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance', alpha: false });
renderer.setPixelRatio(1);
renderer.setSize(W, H);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping; // tone mapping happens in post (fx.tonemap)
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.getElementById('stage').appendChild(renderer.domElement);
media.setAnisotropy(Math.min(8, renderer.capabilities.getMaxAnisotropy()));
post.init(renderer);

export const scene = new THREE.Scene();
const pmrem = new THREE.PMREMGenerator(renderer);
const envTex = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environment = envTex;

// World render target: linear HDR, 4x MSAA, with a depth texture for DOF.
const rtWorld = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4, depthBuffer: true, depthTexture: new THREE.DepthTexture(W, H, THREE.UnsignedIntType) });
const rtWorld2 = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4, depthBuffer: true });

// Screen-space scene (lens flares, screen glows): orthographic, pixel units,
// x right, y up from the bottom. kit helpers take top-left pixel coordinates.
export const hud = new THREE.Scene();
const hudCam = new THREE.OrthographicCamera(0, W, H, 0, -1000, 1000);

// ---------------------------------------------------------------- lights
const hemi = new THREE.HemisphereLight('#9fb2c0', '#0b0c0e', 0.6);
const key = new THREE.DirectionalLight('#ffe6c8', 2.2);
const rim = new THREE.DirectionalLight('#8fb3c9', 1.1);
key.shadow.mapSize.set(2048, 2048);
key.shadow.bias = -0.0004;
key.shadow.normalBias = 0.02;
key.shadow.radius = 4;
scene.add(hemi, key, key.target, rim, rim.target);
export const lights = { hemi, key, rim, follow: true, keyOffset: new THREE.Vector3(-6, 9, 10), rimOffset: new THREE.Vector3(9, 5, -8), shadowBox: 20 };
function lightDefaults() {
  hemi.color.set('#9fb2c0'); hemi.groundColor.set('#0b0c0e'); hemi.intensity = 0.6;
  key.color.set('#ffe6c8'); key.intensity = 2.2; key.castShadow = false;
  rim.color.set('#8fb3c9'); rim.intensity = 1.1;
  lights.follow = true;
  lights.keyOffset.set(-6, 9, 10); lights.rimOffset.set(9, 5, -8); lights.shadowBox = 20;
}

// ---------------------------------------------------------------- camera
export const camera = new THREE.PerspectiveCamera(32.3, W / H, 0.05, 20000);
const camState = {};
function camDefaults() {
  Object.assign(camState, { pos: [0, 0, 10], target: [0, 0, 0], fov: 32.3, roll: 0, near: 0.05, far: 20000, offset: null });
}
// Distance at which `width` world units fill the frame horizontally.
export function distForWidth(width, fov = camState.fov) {
  const tv = Math.tan(THREE.MathUtils.degToRad(fov) / 2);
  return width / 2 / (tv * (W / H));
}
const fovOf = (o) => (o.mm ? A.fovFromMM(o.mm) : o.fov);
export const cam = {
  // Direct placement. fov is vertical degrees; or give mm (full-frame equivalent).
  set(o = {}) {
    if (o.pos) camState.pos = [...o.pos];
    if (o.target) camState.target = [...o.target];
    const f = fovOf(o); if (f !== undefined) camState.fov = f;
    if (o.roll !== undefined) camState.roll = o.roll;
    if (o.near !== undefined) camState.near = o.near;
    if (o.far !== undefined) camState.far = o.far;
  },
  // Orbit a target: yaw (deg, around +Y; 0 = camera on +Z looking toward -Z),
  // pitch (deg, + = above looking down), dist, roll.
  orbit({ target = [0, 0, 0], dist = 10, yaw = 0, pitch = 0, roll = 0, fov, mm, near, far } = {}) {
    const y = A.rad(yaw), p = A.rad(pitch);
    camState.target = [...target];
    camState.pos = [target[0] + dist * Math.sin(y) * Math.cos(p), target[1] + dist * Math.sin(p), target[2] + dist * Math.cos(y) * Math.cos(p)];
    camState.roll = roll;
    const f = fovOf({ fov, mm }); if (f !== undefined) camState.fov = f;
    if (near !== undefined) camState.near = near;
    if (far !== undefined) camState.far = far;
  },
  // Frame `width` world units of the plane z = tz centred on (cx, cy) (the
  // photo-wall convention: pictures face +Z). pitch: + looks from below,
  // yaw swings sideways; dolly multiplies the distance (< 1 pushes in).
  frame({ cx = 0, cy = 0, width = 10, pitch = 0, yaw = 0, roll = 0, fov, mm, dolly = 1, tz = 0 } = {}) {
    const f = fovOf({ fov, mm }); if (f !== undefined) camState.fov = f;
    const d = distForWidth(width, camState.fov) * dolly;
    const p = A.rad(pitch), y = A.rad(yaw);
    camState.target = [cx, cy, tz];
    camState.pos = [cx + d * Math.sin(y) * Math.cos(p), cy - d * Math.sin(p), tz + d * Math.cos(y) * Math.cos(p)];
    camState.roll = roll;
  },
  get state() { return camState; },
};

function applyCamera(t) {
  const [px, py, pz] = camState.pos, [tx, ty, tz] = camState.target;
  camera.fov = camState.fov; camera.near = camState.near; camera.far = camState.far;
  camera.position.set(px, py, pz);
  camera.up.set(0, 1, 0);
  camera.lookAt(tx, ty, tz);
  if (fx.breathe) {
    const b = A.breath(t, fx.breathe, 5);
    camera.rotateX(A.rad(b.pitch)); camera.rotateY(A.rad(b.yaw));
    camera.rotateZ(A.rad(camState.roll + b.roll));
  } else camera.rotateZ(A.rad(camState.roll));
  camera.updateProjectionMatrix();
  camera.updateMatrixWorld();
  if (lights.follow) {
    const tgt = new THREE.Vector3(tx, ty, tz);
    key.target.position.copy(tgt); key.position.copy(tgt).add(lights.keyOffset);
    rim.target.position.copy(tgt); rim.position.copy(tgt).add(lights.rimOffset);
  }
  const sc = key.shadow.camera, b = lights.shadowBox;
  if (sc.right !== b) { sc.left = -b; sc.right = b; sc.top = b; sc.bottom = -b; sc.near = 0.5; sc.far = b * 6; sc.updateProjectionMatrix(); }
  key.target.updateMatrixWorld(); rim.target.updateMatrixWorld();
}

let curT = 0;
// World position -> pixel position (top-left origin) on the 1920x1080 frame.
// Uses the camera as set so far this frame, so call it after setting the camera.
export function toScreen(v) {
  applyCamera(curT);
  const p = (v.isVector3 ? v.clone() : new THREE.Vector3(...v)).project(camera);
  return { x: (p.x * 0.5 + 0.5) * W, y: (-p.y * 0.5 + 0.5) * H, z: p.z, visible: p.z < 1 && p.z > -1 };
}
// Pixel size of one world unit at a world position (for sizing DOM labels).
export function unitPx(v) {
  const p = v.isVector3 ? v : new THREE.Vector3(...v);
  applyCamera(curT);
  const right = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0);
  const a = toScreen(p), b = toScreen(p.clone().add(right));
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
// Pixel (x, y) -> the world point at distance `dist` from the camera along that ray.
export function screenRay(x, y, dist = 10) {
  applyCamera(curT);
  const ndc = new THREE.Vector3((x / W) * 2 - 1, -(y / H) * 2 + 1, 0.5).unproject(camera);
  const dir = ndc.sub(camera.position).normalize();
  return camera.position.clone().add(dir.multiplyScalar(dist));
}
// Pin a 3D object to a screen position: place it on the plane z under pixel
// (x, y) and scale it so `worldHeight` units look `heightPx` tall.
export function pin(obj, { x = W / 2, y = H / 2, z = 0, heightPx = 100, worldHeight = 1, scale = 1 } = {}) {
  const p = screenToWorld(x, y, z);
  obj.position.copy(p);
  const upx = unitPx(p);
  obj.scale.setScalar(Math.max(1e-4, (heightPx / (worldHeight * upx)) * scale));
  return p;
}

// ---------------------------------------------------------------- per-frame fx
export const FX_DEFAULTS = {
  // world
  bg: '#07080a',            // colour, or [top, bottom] gradient
  bgPool: null,             // { color, x, y (0..1, y down), radius, amount }: soft light pool on the void
  fog: null,                // { color, density } (exp2) or { color, near, far } (linear)
  env: 0.25,                // environment reflections (metals)
  // camera
  breathe: 0,               // handheld rotation noise (1 = style-bible amount)
  shake: 0, shakeHz: 18,    // screen shake amplitude in px
  punch: 1,                 // scale punch-in (1.04 = 4 %)
  dof: null,                // { focus: world distance, blur: px at infinity, maxBlur: px }
  subframes: 1, shutter: 1 / 120, // motion-blur sub-frame accumulation
  // light (linear HDR)
  exposure: 0,              // stops
  tonemap: 'agx',           // 'agx' | 'aces' | 'neutral' | 'none'
  agxPunch: 0,
  bloom: { amount: 0, threshold: 1.0, radius: 0.5 },
  glow: { amount: 0.35, threshold: 0.8, radius: 0.55 },     // selective: kit.glowLayer objects
  halation: { amount: 0.1, threshold: 0.82, radius: 18, tint: '#FF5A2A' },
  leak: { amount: 0, color: '#E3A04A', side: 'left', pos: 0.5, width: 0.3, seed: 1 },
  // grade (display)
  grade: { lift: [0, 0, 0], gamma: [1, 1, 1], gain: [1, 1, 1], temp: 0, tint: 0, sat: 1, vibrance: 0, contrast: 1, pivot: 0.435, curve: 0,
    shadows: null, shadowsAmount: 0.25, highlights: null, highlightsAmount: 0.25, balance: 0.5, blacks: 0, whites: 1 },
  look: null,               // 'name' | { a, b, mix, amount }
  // film (whole frame incl. DOM)
  ca: 0.4, distort: 0,
  zoom: 0, zoomC: [0.5, 0.5], dir: [0, 0],
  weave: 1, weaveT: null,
  vignette: 0.18, vignetteRound: 0.35,
  grain: { amount: 1, size: 1.4, chroma: 0.2, floor: 0.35 }, grainFps: 30,
  flicker: 0, glitch: 0, scanlines: 0,
  flash: 0, flashColor: '#ffffff', fade: 0, fadeColor: '#000000',
  bars: 0, barsAspect: 2.39, barsColor: '#000000',
  layers: [],               // 2D layers for this frame (see docs/ENGINE.md)
  domOpacity: 1,
};
export const fx = {};
function fxDefaults() {
  for (const k of Object.keys(fx)) delete fx[k];
  Object.assign(fx, structuredClone(FX_DEFAULTS));
  fx.set = setFx;
}
// Deep-merge helper: fx.set({ grade: { sat: 0.8 }, bars: 1 })
function setFx(o) {
  const merge = (dst, src) => {
    for (const [k, v] of Object.entries(src)) {
      if (v && typeof v === 'object' && !Array.isArray(v) && dst[k] && typeof dst[k] === 'object' && !Array.isArray(dst[k]) && !v.isTexture) merge(dst[k], v);
      else dst[k] = v;
    }
  };
  merge(fx, o);
  return fx;
}
function snapshotFx() {
  const o = {};
  for (const [k, v] of Object.entries(fx)) if (k !== 'set') o[k] = k === 'layers' ? [...v] : (v && typeof v === 'object' && !Array.isArray(v) ? { ...v } : v);
  return o;
}
// Interpolate two fx snapshots (for dissolves between passes).
function lerpFx(a, b, k) {
  const out = {};
  const lv = (x, y) => {
    if (typeof x === 'number' && typeof y === 'number') return A.lerp(x, y, k);
    if (Array.isArray(x) && Array.isArray(y) && x.length === y.length && x.every((v) => typeof v === 'number')) return x.map((v, i) => A.lerp(v, y[i], k));
    if (x && y && typeof x === 'object' && typeof y === 'object' && !Array.isArray(x)) { const o = {}; for (const kk of new Set([...Object.keys(x), ...Object.keys(y)])) o[kk] = lv(x[kk], y[kk]); return o; }
    return k < 0.5 ? x : y;
  };
  for (const kk of new Set([...Object.keys(a), ...Object.keys(b)])) out[kk] = lv(a[kk], b[kk]);
  out.layers = [...(a.layers || []).map((L) => ({ ...L, opacity: (L.opacity ?? 1) * (1 - k) })), ...(b.layers || []).map((L) => ({ ...L, opacity: (L.opacity ?? 1) * k }))];
  const la = typeof a.look === 'string' ? a.look : null, lb = typeof b.look === 'string' ? b.look : null;
  if (la && lb && la !== lb) out.look = { a: la, b: lb, mix: k };
  else if (la && !b.look) out.look = { a: la, amount: 1 - k };
  else if (lb && !a.look) out.look = { a: lb, amount: k };
  out.dof = k < 0.5 ? a.dof : b.dof;
  return out;
}

// ---------------------------------------------------------------- world state
const fogExp = new THREE.FogExp2('#000000', 0.01), fogLin = new THREE.Fog('#000000', 10, 100);
function applyWorld() {
  const bg = Array.isArray(fx.bg) ? null : fx.bg;
  scene.background = bg && !fx.bgPool ? new THREE.Color(bg) : null;
  if (fx.fog) {
    if (fx.fog.density !== undefined) { fogExp.color.set(fx.fog.color ?? '#07080a'); fogExp.density = fx.fog.density; scene.fog = fogExp; }
    else { fogLin.color.set(fx.fog.color ?? '#07080a'); fogLin.near = fx.fog.near ?? 10; fogLin.far = fx.fog.far ?? 100; scene.fog = fogLin; }
  } else scene.fog = null;
  scene.environmentIntensity = fx.env ?? 0.25;
}

// ---------------------------------------------------------------- timeline
const scenes = [];
const transitions = [];
const overlayRoot = document.getElementById('overlay');
let words = [];
export function setWords(w) { words = w; }
const norm = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, '');
// Time of the nth (1-based) occurrence of a script word ('start' or 'end').
export function wt(word, nth = 1, which = 'start') {
  const k = norm(word);
  let n = 0;
  for (const w of words) if (norm(w.word) === k && ++n === nth) return w[which];
  throw new Error(`word not found: ${word} #${nth}`);
}
export function getWords() { return words; }
export function addScene(def) { scenes.push(def); }
export function addTransition(tr) { transitions.push(tr); }

export async function initScenes(ctxBase) {
  for (const s of scenes) {
    s.group = new THREE.Group(); s.group.name = s.id; scene.add(s.group);
    s.hud = new THREE.Group(); s.hud.name = s.id + ':hud'; hud.add(s.hud);
    s.dom = document.createElement('div');
    s.dom.className = 'scene-layer';
    s.dom.dataset.scene = s.id;
    overlayRoot.appendChild(s.dom);
    s.ctx = { ...ctxBase, group: s.group, hud: s.hud, dom: s.dom, start: s.start, end: s.end, dur: s.end - s.start, id: s.id };
    if (s.init) await s.init(s.ctx);
  }
  // resolve automatic from/to on pass transitions
  for (const tr of transitions) {
    if (!PASS_KINDS.has(tr.kind)) continue;
    tr.from ??= scenes.find((s) => Math.abs(s.end - tr.at) < 1e-6)?.id;
    tr.to ??= scenes.find((s) => Math.abs(s.start - tr.at) < 1e-6)?.id;
  }
}

// Transitions that render the outgoing and incoming scenes as separate passes.
const PASS_KINDS = new Set(['dissolve', 'wipe', 'iris', 'noise', 'mist', 'dip']);
function activePassTransition(t) {
  for (const tr of transitions) {
    if (!PASS_KINDS.has(tr.kind) || !tr.from || !tr.to) continue;
    const d = tr.dur ?? 0.5;
    if (t > tr.at - d / 2 && t < tr.at + d / 2) {
      if (!scenes.find((s) => s.id === tr.from) || !scenes.find((s) => s.id === tr.to)) continue;
      return { tr, k: (tr.ease ?? A.E.inOutSine)(A.prog(t, tr.at - d / 2, tr.at + d / 2)) };
    }
  }
  return null;
}
// fx pulses (zoom / whip / flash / glitch / punch), added on top of the scenes.
function applyFxTransitions(t) {
  for (const tr of transitions) {
    if (PASS_KINDS.has(tr.kind)) continue;
    const dur = tr.dur ?? 0.36;
    const k = A.pulse(t, tr.at, dur);
    if (k <= 0) continue;
    const s = tr.strength ?? 1;
    if (tr.kind === 'whip') {
      const d = tr.dir ?? [0.16, 0];
      fx.dir = [fx.dir[0] + d[0] * k * s, fx.dir[1] + d[1] * k * s];
      fx.ca += 6 * k * s;
    } else if (tr.kind === 'zoom') {
      fx.zoom += 0.22 * k * s;
      if (tr.center) fx.zoomC = tr.center;
      fx.ca += 6 * k * s;
    } else if (tr.kind === 'glitch') {
      fx.glitch = Math.max(fx.glitch, k * s);
    } else if (tr.kind === 'punch') {
      fx.punch *= 1 + 0.04 * s * A.hit(t, tr.at, dur / 2);
    }
    if (tr.flash !== undefined || tr.kind === 'flash') { fx.flash = Math.max(fx.flash, (tr.flash ?? 0.6) * k); if (tr.flashColor) fx.flashColor = tr.flashColor; }
  }
}

// Run every active scene's update for time t. opts.hide: scene id not drawn
// this pass; opts.force: scene id kept active outside its span (transitions).
function runUpdates(t, opts = {}) {
  curT = t;
  fxDefaults(); camDefaults(); lightDefaults();
  for (const s of scenes) {
    let active = (t >= s.start && t < s.end) || s.id === opts.force;
    if (s.id === opts.hide) active = false;
    s.group.visible = active; s.hud.visible = active;
    s.dom.style.display = active ? 'block' : 'none';
    s.dom.style.opacity = '';
    if (active && s.update) s.update(t, t - s.start, s.ctx);
  }
  applyFxTransitions(t);
  applyCamera(t);
  applyWorld();
}

// Draw the world (background, 3D scene, HUD) into an HDR target.
function renderWorld(target) {
  renderer.setRenderTarget(target);
  if (Array.isArray(fx.bg) || fx.bgPool) {
    renderer.setClearColor(0x000000, 1); renderer.clear();
    post.background(target, fx);
    renderer.setRenderTarget(target);
    renderer.autoClear = false; renderer.clearDepth();
    renderer.render(scene, camera);
  } else {
    renderer.autoClear = true;
    renderer.render(scene, camera);
  }
  renderer.autoClear = false;
  renderer.clearDepth();
  renderer.render(hud, hudCam);
  renderer.autoClear = true;
}

// Glow layer pass for selective bloom: glow objects in colour, everything
// else as black occluders. Returns false when nothing glows.
const blackMat = new THREE.MeshBasicMaterial({ color: 0x000000 });
function renderGlow(target) {
  const glowing = [], others = [];
  scene.traverseVisible((o) => {
    if (!(o.isMesh || o.isPoints || o.isSprite || o.isLine)) return;
    (o.layers.isEnabled(GLOW_LAYER) ? glowing : others).push(o);
  });
  if (!glowing.length) return false;
  const swapped = [], hidden = [];
  for (const o of others) {
    const m = Array.isArray(o.material) ? o.material[0] : o.material;
    if (o.isPoints || o.isSprite || o.isLine || (m && m.transparent && (m.depthWrite === false || m.opacity < 0.5))) { hidden.push(o); o.visible = false; continue; }
    swapped.push([o, o.material]);
    o.material = o.userData.glowOccluder || blackMat;
  }
  const bg = scene.background, fog = scene.fog, au = renderer.shadowMap.autoUpdate;
  scene.background = new THREE.Color(0x000000); scene.fog = null; renderer.shadowMap.autoUpdate = false;
  renderer.setRenderTarget(target);
  renderer.clear();
  renderer.render(scene, camera);
  scene.background = bg; scene.fog = fog; renderer.shadowMap.autoUpdate = au;
  for (const [o, m] of swapped) o.material = m;
  for (const o of hidden) o.visible = true;
  return true;
}

// One pass: updates at t (with optional motion-blur sub-frames) -> HDR texture.
async function renderPass(t, opts, target, accum) {
  runUpdates(t, opts);
  const snap = snapshotFx();
  const n = Math.max(1, Math.floor(fx.subframes || 1));
  if (n > 1) {
    const shutter = fx.shutter ?? 1 / 120;
    renderer.setRenderTarget(accum); renderer.setClearColor(0x000000, 1); renderer.clear();
    for (let i = 0; i < n; i++) {
      const ts = t + ((i + 0.5) / n - 0.5) * shutter;
      runUpdates(ts, opts);
      await media.flush();
      renderWorld(target);
      post.accumulate(target.texture, accum, 1 / n);
    }
    runUpdates(t, opts); // restore the DOM and state at t
    return { fx: snap, tex: accum.texture, depth: target.depthTexture ?? null };
  }
  await media.flush();
  renderWorld(target);
  return { fx: snap, tex: target.texture, depth: target.depthTexture ?? null };
}

const timing = { n: 0, update: 0, world: 0, dom: 0, post: 0, last: {} };
export async function renderFrame(t) {
  const T0 = performance.now();
  const R = post.targets();
  const pt = activePassTransition(t);
  let hdrTex, depthTex, fxUse;
  if (!pt) {
    const r = await renderPass(t, {}, rtWorld, R.accum);
    hdrTex = r.tex; depthTex = r.depth; fxUse = r.fx;
  } else {
    const { tr, k } = pt;
    const a = await renderPass(t, { hide: tr.to, force: tr.from }, rtWorld2, R.accum2);
    const b = await renderPass(t, { hide: tr.from, force: tr.to }, rtWorld, R.accum);
    post.transitionMix(a.tex, b.tex, tr, k, R.mix);
    hdrTex = R.mix.texture; depthTex = b.depth; fxUse = lerpFx(a.fx, b.fx, k);
    const sa = scenes.find((s) => s.id === tr.from), sb = scenes.find((s) => s.id === tr.to);
    sa.dom.style.display = 'block'; sa.dom.style.opacity = String(1 - k); sb.dom.style.opacity = String(k);
  }
  const T1 = performance.now();
  const domTex = overlayMode === 'texture' ? await domtex.capture(overlayRoot) : null;
  const T2 = performance.now();
  if (overlayMode === 'top') applyTopOverlay(fxUse);
  post.finish({ hdrTex, depthTex, camera, fx: fxUse, t, glowRender: renderGlow, domTex });
  const T3 = performance.now();
  timing.n++; timing.world += T1 - T0; timing.dom += T2 - T1; timing.post += T3 - T2;
  timing.last = { world: T1 - T0, dom: T2 - T1, post: T3 - T2 };
  return true;
}
export function stats() {
  const n = Math.max(1, timing.n);
  return { frames: timing.n, worldMs: timing.world / n, domMs: timing.dom / n, postMs: timing.post / n, last: timing.last, info: renderer.info.render, programs: renderer.info.programs?.length };
}

// Overlay mode: 'texture' (default) rasterises the DOM into the film pass;
// 'top' keeps it as live DOM above the canvas (faster, but grain, CA, blur
// and glitch then skip the type; bars, fades and weave are approximated).
let overlayMode = 'texture';
export function setOverlayMode(m) {
  overlayMode = m;
  overlayRoot.style.zIndex = m === 'top' ? '2' : '0';
}
function applyTopOverlay(f) {
  const bh = A.clamp(f.bars ?? 0) * Math.max(0, (H - W / (f.barsAspect ?? 2.39)) / 2);
  overlayRoot.style.clipPath = bh > 0 ? `inset(${bh}px 0px ${bh}px 0px)` : 'none';
  overlayRoot.style.opacity = String((1 - A.clamp(f.fade ?? 0)) * (f.domOpacity ?? 1));
  const wt = f.weaveT ?? curT, wv = f.weave ?? 1;
  overlayRoot.style.transform = `translate(${(wv * 0.5 * A.noise1(wt / 1.9, 71)).toFixed(3)}px, ${(-wv * 0.7 * A.noise1(wt / 2.3, 72)).toFixed(3)}px) scale(${f.punch ?? 1})`;
}

export function getScenes() { return scenes; }
export { renderer };
