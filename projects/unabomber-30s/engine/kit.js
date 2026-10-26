// Reusable 3D building blocks. Every object exposes setters that take
// progress values or time, so scenes stay pure functions of time: call the
// setters every frame with values computed from t.

import * as THREE from 'three';
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';
import { TTFLoader } from 'three/addons/loaders/TTFLoader.js';
import { SVGLoader } from 'three/addons/loaders/SVGLoader.js';
import { Font } from 'three/addons/loaders/FontLoader.js';
import { RectAreaLightUniformsLib } from 'three/addons/lights/RectAreaLightUniformsLib.js';
import opentype from 'three/addons/libs/opentype.module.js';
import * as A from './anim.js';
import * as TX from './textures.js';
import { FONT3D } from './fonts.js';
import { GLOW_LAYER, W, H } from './core.js';
export { photoPlane, photoLayers, videoPlane } from './photo.js';
export { terrain, clouds, route, marker, mercator } from './terrain.js';

// Style-bible palette (docs/STYLE.md section 6).
export const PAL = {
  ink: '#0A0B0D', char: '#15181C', slate: '#2B3238', fog: '#8FA3AE', frost: '#D6DEE2', bone: '#F2EFE8',
  spruce: '#1D2A26', pine: '#3E524B', birch: '#CFC8B8', umber: '#5A3E2B', kraft: '#9C7A4E', manila: '#CDB27A',
  lamp: '#E3A04A', red: '#C8102E', redDeep: '#7A0C14', mapline: '#7FA8B5', void: '#07080a',
};

const col = (c) => (c instanceof THREE.Color ? c.clone() : new THREE.Color(c));
const lin3 = (c) => { const k = col(c); return new THREE.Vector3(k.r, k.g, k.b); };

// ---------------------------------------------------------------- materials
export function glossy(color, { rough = 0.3, clearcoat = 1, emissive = 0, metal = 0 } = {}) {
  const c = col(color);
  return new THREE.MeshPhysicalMaterial({ color: c, roughness: rough, metalness: metal, clearcoat, clearcoatRoughness: 0.12, emissive: c, emissiveIntensity: emissive, transparent: true, opacity: 1 });
}
export function matte(color, { rough = 0.85, emissive = 0 } = {}) {
  const c = col(color);
  return new THREE.MeshStandardMaterial({ color: c, roughness: rough, emissive: c, emissiveIntensity: emissive, transparent: true });
}
export function metal(color, { rough = 0.35, metalness = 0.9 } = {}) {
  return new THREE.MeshStandardMaterial({ color: col(color), roughness: rough, metalness, transparent: true });
}
// Unlit, HDR-bright colour (values > 1 bloom). Put it on the glow layer to bloom selectively.
export function emissive(color, intensity = 2) {
  return new THREE.MeshBasicMaterial({ color: col(color).multiplyScalar(intensity), transparent: true });
}
export function setOpacity(obj, a) {
  obj.traverse((o) => {
    if (!o.material) return;
    for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
      if (m.userData.baseOpacity === undefined) m.userData.baseOpacity = m.opacity;
      m.opacity = a * m.userData.baseOpacity;
      m.depthWrite = a > 0.98 && m.userData.depthWrite !== false;
    }
  });
  obj.visible = a > 0.001;
}
// Mark an object tree for the selective glow (bloom) pass (fx.glow).
export function glowLayer(obj, on = true) {
  obj.traverse((o) => (on ? o.layers.enable(GLOW_LAYER) : o.layers.disable(GLOW_LAYER)));
  return obj;
}
// Spot light (e.g. a title light sweep) with its target added; place both per frame.
export function spot({ color = PAL.lamp, intensity = 40, angle = 12, penumbra = 0.6, distance = 0, decay = 2, castShadow = false } = {}) {
  const s = new THREE.SpotLight(col(color), intensity, distance, A.rad(angle), penumbra, decay);
  s.castShadow = castShadow;
  const group = new THREE.Group(); group.add(s, s.target);
  return { group, light: s, target: s.target };
}
let rectInit = false;
// Rectangular area light (soft key for prints/titles; Standard/Physical materials only).
export function areaLight({ color = PAL.lamp, intensity = 6, w = 4, h = 2 } = {}) {
  if (!rectInit) { RectAreaLightUniformsLib.init(); rectInit = true; }
  return new THREE.RectAreaLight(col(color), intensity, w, h);
}

// ---------------------------------------------------------------- glows
// Camera-facing soft light, additive.
export function glow({ color = PAL.lamp, size = 2, intensity = 1, additive = true } = {}) {
  const m = new THREE.SpriteMaterial({ map: TX.radial(), color: col(color).multiplyScalar(intensity), transparent: true, depthWrite: false, blending: additive ? THREE.AdditiveBlending : THREE.NormalBlending });
  const s = new THREE.Sprite(m);
  s.scale.set(size, size, 1);
  s.userData.base = col(color);
  s.setIntensity = (k) => { m.color.copy(s.userData.base).multiplyScalar(k); s.visible = k > 0.0005; };
  return s;
}

// ---------------------------------------------------------------- lens flare (screen space)
function ringTexture() {
  return TX._ring ??= (() => {
    const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
    const gr = g.createRadialGradient(128, 128, 70, 128, 128, 128);
    gr.addColorStop(0, 'rgba(255,255,255,0)'); gr.addColorStop(0.7, 'rgba(255,255,255,0.5)'); gr.addColorStop(0.85, 'rgba(255,255,255,0.15)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = gr; g.fillRect(0, 0, 256, 256);
    const t = new THREE.CanvasTexture(c); return t;
  })();
}
function hexTexture() {
  return TX._hex ??= (() => {
    const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
    g.filter = 'blur(5px)'; g.fillStyle = 'rgba(255,255,255,0.9)'; g.beginPath();
    for (let i = 0; i < 6; i++) { const a = (i / 6) * Math.PI * 2 + Math.PI / 6; g[i ? 'lineTo' : 'moveTo'](128 + Math.cos(a) * 100, 128 + Math.sin(a) * 100); }
    g.closePath(); g.fill();
    return new THREE.CanvasTexture(c);
  })();
}
function streakTexture() {
  return TX._streak ??= (() => {
    const c = document.createElement('canvas'); c.width = 512; c.height = 64; const g = c.getContext('2d');
    const gx = g.createLinearGradient(0, 0, 512, 0);
    gx.addColorStop(0, 'rgba(255,255,255,0)'); gx.addColorStop(0.5, 'rgba(255,255,255,1)'); gx.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = gx; g.fillRect(0, 0, 512, 64);
    g.globalCompositeOperation = 'destination-in';
    const gy = g.createLinearGradient(0, 0, 0, 64);
    gy.addColorStop(0, 'rgba(0,0,0,0)'); gy.addColorStop(0.5, 'rgba(0,0,0,1)'); gy.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = gy; g.fillRect(0, 0, 512, 64);
    return new THREE.CanvasTexture(c);
  })();
}
// Anamorphic lens flare drawn in screen space (add flare.group to ctx.hud).
//   flare.set({ x, y } px (top-left origin), intensity)  — use ctx.toScreen(worldPos) for a 3D light.
export function lensFlare({ color = '#ffd2a0', streak = 1, ghosts = 6, size = 1, seed = 3, streakColor = '#9fc4ff' } = {}) {
  const group = new THREE.Group();
  const r = A.rng(seed);
  const add = (tex, c, w, h, k, a) => {
    const m = new THREE.MeshBasicMaterial({ map: tex, color: col(c), transparent: true, depthTest: false, depthWrite: false, blending: THREE.AdditiveBlending });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), m);
    mesh.scale.set(w, h, 1);
    mesh.userData = { k, a, base: col(c) };
    group.add(mesh);
    return mesh;
  };
  add(TX.radial(), color, 320 * size, 320 * size, 1, 1.0);
  add(TX.radial(), '#ffffff', 90 * size, 90 * size, 1, 1.4);
  if (streak) { add(streakTexture(), streakColor, 1500 * size * streak, 26 * size, 1, 0.7); add(streakTexture(), '#ffffff', 700 * size * streak, 6 * size, 1, 0.9); }
  const tints = ['#7fb0ff', '#ffb070', '#b0ff9a', '#ff8fb8', '#9fe7ff', '#ffd27f'];
  for (let i = 0; i < ghosts; i++) {
    const k = [0.55, 0.25, -0.15, -0.45, -0.8, -1.25, 0.05, -0.6][i % 8];
    const s = (40 + r() * 140) * size;
    add(i % 3 === 0 ? ringTexture() : hexTexture(), tints[i % tints.length], s, s, k, 0.09 + r() * 0.12);
  }
  add(ringTexture(), '#ffe8cc', 520 * size, 520 * size, 1, 0.12);
  return {
    group,
    set({ x = W / 2, y = H / 2, intensity = 1 } = {}) {
      const sx = x, sy = H - y; // hud coords: y up
      const cx = W / 2, cy = H / 2;
      const edge = 1 - A.smooth(A.clamp((Math.max(Math.abs(x - cx) / cx, Math.abs(y - cy) / cy) - 0.75) / 0.45));
      group.visible = intensity * edge > 0.002;
      for (const m of group.children) {
        const { k, a, base } = m.userData;
        m.position.set(cx + (sx - cx) * k, cy + (sy - cy) * k, 0);
        m.material.color.copy(base).multiplyScalar(a * intensity * edge);
      }
    },
  };
}

// ---------------------------------------------------------------- god rays
// Volumetric light shafts: additive cards around the beam axis, turned toward
// the camera, with drifting streaks. update(t) every frame.
export function godRays({ origin = [0, 6, 0], dir = [0.25, -1, 0.1], length = 14, spread = 3, width = 0.6, count = 7, color = PAL.lamp, intensity = 0.5, seed = 1, speed = 0.12 } = {}) {
  const group = new THREE.Group();
  const r = A.rng(seed);
  const base = new THREE.Vector3(...dir).normalize();
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute([0, -1, 0, 1, -1, 0, 1, 1, 0, 0, 1, 0], 3));
  geo.setIndex([0, 1, 2, 0, 2, 3]);
  const mats = [];
  for (let i = 0; i < count; i++) {
    const off = new THREE.Vector3((r() - 0.5), (r() - 0.5), (r() - 0.5)).multiplyScalar((spread / length) * 1.2);
    const axis = base.clone().add(off).normalize();
    const m = new THREE.ShaderMaterial({
      uniforms: { uO: { value: new THREE.Vector3(...origin) }, uAxis: { value: axis }, uLen: { value: length * (0.75 + r() * 0.5) }, uW0: { value: width * (0.3 + r() * 0.4) }, uW1: { value: width * (1.2 + r() * 2.2) },
        uColor: { value: lin3(color) }, uI: { value: intensity * (0.4 + r() * 0.6) / Math.sqrt(count) * 2 }, uTime: { value: 0 }, uSeed: { value: r() * 100 }, uSpeed: { value: speed } },
      vertexShader: `uniform vec3 uO, uAxis; uniform float uLen, uW0, uW1; varying vec2 vC; varying float vFacing;
        void main(){
          vec3 camL = (inverse(modelMatrix) * vec4(cameraPosition, 1.0)).xyz;
          vec3 p = uO + uAxis * position.x * uLen;
          vec3 toCam = normalize(camL - p);
          vec3 side = normalize(cross(uAxis, toCam));
          p += side * position.y * mix(uW0, uW1, position.x);
          vC = position.xy; vFacing = 1.0 - abs(dot(uAxis, toCam));
          gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
        }`,
      fragmentShader: `uniform vec3 uColor; uniform float uI, uTime, uSeed, uSpeed; varying vec2 vC; varying float vFacing;
        float h(float n){ return fract(sin(n) * 43758.5453); }
        float vn(vec2 p){ vec2 i = floor(p), f = fract(p); f = f*f*(3.0-2.0*f); float a = h(i.x + i.y*57.0), b = h(i.x+1.0 + i.y*57.0), c = h(i.x + (i.y+1.0)*57.0), d = h(i.x+1.0 + (i.y+1.0)*57.0); return mix(mix(a,b,f.x), mix(c,d,f.x), f.y); }
        void main(){
          float across = exp(-vC.y * vC.y * 2.6);
          float along = smoothstep(0.0, 0.12, vC.x) * pow(1.0 - vC.x, 1.6);
          float n = vn(vec2(vC.y * 4.0 + uSeed, vC.x * 1.5 - uTime * uSpeed)) * 0.6 + vn(vec2(vC.y * 11.0 - uSeed, vC.x * 3.0 + uTime * uSpeed * 0.7)) * 0.4;
          float a = across * along * (0.45 + 0.8 * n) * uI * smoothstep(0.0, 0.25, vFacing);
          gl_FragColor = vec4(uColor * a, 1.0);
        }`,
      transparent: true, depthWrite: false, side: THREE.DoubleSide,
      blending: THREE.CustomBlending, blendEquation: THREE.AddEquation, blendSrc: THREE.OneFactor, blendDst: THREE.OneFactor,
    });
    const mesh = new THREE.Mesh(geo, m);
    mesh.frustumCulled = false;
    group.add(mesh); mats.push(m);
  }
  const baseI = mats.map((m) => m.uniforms.uI.value);
  return {
    group,
    update(t) { mats.forEach((m) => { m.uniforms.uTime.value = t; }); },
    setIntensity(k) { mats.forEach((m, i) => { m.uniforms.uI.value = baseI[i] * k; }); group.visible = k > 0.001; },
    setOrigin(o2) { mats.forEach((m) => m.uniforms.uO.value.set(...o2)); },
  };
}

// ---------------------------------------------------------------- fog cards
// Drifting volumetric fog / mist: noise-textured cards. billboard (default)
// faces the camera; billboard: false gives fixed planes facing +Z (a mist wall
// to fly through). update(t) every frame.
export function fogCards({ count = 10, area = [30, 4, 30], center = [0, 1, 0], size = [6, 14], color = PAL.fog, opacity = 0.22, speed = 0.08, seed = 7, fadeNear = 2.5, billboard = true, scale = 1 } = {}) {
  const group = new THREE.Group();
  const r = A.rng(seed);
  const noise = TX.noise({ size: 512, scale: 4, octaves: 5, seed: seed + 100 });
  const mats = [];
  for (let i = 0; i < count; i++) {
    const s = A.lerp(size[0], size[1], r());
    const m = new THREE.ShaderMaterial({
      uniforms: { tNoise: { value: noise }, uColor: { value: lin3(color) }, uOpacity: { value: opacity }, uTime: { value: 0 }, uSeed: { value: new THREE.Vector2(r() * 10, r() * 10) }, uSpeed: { value: speed * (0.5 + r()) }, uFadeNear: { value: fadeNear }, uScale: { value: scale }, uBill: { value: billboard ? 1 : 0 }, uSize: { value: new THREE.Vector2(s, s * (billboard ? 0.6 : 0.6)) } },
      vertexShader: `uniform float uBill; uniform vec2 uSize; varying vec2 vUv; varying float vDist;
        void main(){ vUv = uv; vec4 mv;
          if (uBill > 0.5) { mv = modelViewMatrix * vec4(0.0, 0.0, 0.0, 1.0); mv.xy += position.xy * uSize; }
          else mv = modelViewMatrix * vec4(position.xy * uSize, 0.0, 1.0);
          vDist = -mv.z; gl_Position = projectionMatrix * mv; }`,
      fragmentShader: `uniform sampler2D tNoise; uniform vec3 uColor; uniform float uOpacity, uTime, uSpeed, uFadeNear, uScale; uniform vec2 uSeed; varying vec2 vUv; varying float vDist;
        void main(){
          vec2 p = (vUv * uScale + uSeed) * 0.6;
          float n = texture2D(tNoise, p + vec2(uTime * uSpeed * 0.05, uTime * uSpeed * 0.02)).r * 0.6 + texture2D(tNoise, p * 2.3 - vec2(uTime * uSpeed * 0.04, 0.0)).r * 0.4;
          vec2 q = vUv * 2.0 - 1.0;
          float edge = 1.0 - smoothstep(0.35, 1.0, length(q));
          float a = smoothstep(0.32, 0.8, n) * edge * uOpacity * smoothstep(uFadeNear * 0.25, uFadeNear, vDist);
          gl_FragColor = vec4(uColor, a);
        }`,
      transparent: true, depthWrite: false, side: THREE.DoubleSide,
    });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), m);
    mesh.position.set(center[0] + (r() - 0.5) * area[0], center[1] + (r() - 0.5) * area[1], center[2] + (r() - 0.5) * area[2]);
    mesh.frustumCulled = false;
    mesh.userData.base = mesh.position.clone();
    mesh.userData.drift = new THREE.Vector3((r() - 0.5) * 2, 0, (r() - 0.5)).multiplyScalar(speed);
    group.add(mesh); mats.push(m);
  }
  return {
    group,
    update(t) { group.children.forEach((m, i) => { m.position.copy(m.userData.base).addScaledVector(m.userData.drift, t); mats[i].uniforms.uTime.value = t; }); },
    setOpacity(a) { mats.forEach((m) => { m.uniforms.uOpacity.value = opacity * a; }); group.visible = a > 0.001; },
  };
}
// A single mist wall (plane facing +Z) for a fly-through transition.
export const mistCard = ({ w = 20, h = 12, color = PAL.frost, opacity = 0.9, seed = 3, speed = 0.1 } = {}) => {
  const f = fogCards({ count: 1, area: [0, 0, 0], center: [0, 0, 0], size: [w, w], color, opacity, speed, seed, billboard: false, fadeNear: 0.6, scale: 1.4 });
  f.group.children[0].material.uniforms.uSize.value.set(w, h);
  return f;
};

// ---------------------------------------------------------------- particles
// GPU particles, positions are a pure function of time (computed in the vertex
// shader). kind: 'dust' (motes), 'snow', 'embers'. Sizes in world units.
//   area [w, h, d] around center; size [min, max]; speed; wind [x, y, z] units/s;
//   focus (world distance) + bokeh (px of blur per unit defocus) for out-of-focus discs;
//   beam { origin, dir, radius, floor } lights motes only inside a shaft.
export function particles({ kind = 'dust', count = 400, area = [10, 6, 10], center = [0, 0, 0], size = [0.01, 0.03], color, opacity = 0.8, speed = 1, wind = [0, 0, 0], seed = 5, focus = 0, bokeh = 0, beam = null, additive, fadeNear = 0.3 } = {}) {
  const r = A.rng(seed);
  const pos = new Float32Array(count * 3), rnd = new Float32Array(count * 4);
  for (let i = 0; i < count; i++) {
    pos[i * 3] = (r() - 0.5) * area[0]; pos[i * 3 + 1] = (r() - 0.5) * area[1]; pos[i * 3 + 2] = (r() - 0.5) * area[2];
    for (let k = 0; k < 4; k++) rnd[i * 4 + k] = r();
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('aRnd', new THREE.BufferAttribute(rnd, 4));
  const K = { dust: 0, snow: 1, embers: 2 }[kind] ?? 0;
  const defColor = { dust: '#E8DCC0', snow: '#EEF3F5', embers: '#FF7A2A' }[kind];
  const add = additive ?? kind !== 'snow';
  const uniforms = {
    uTime: { value: 0 }, uKind: { value: K }, uBox: { value: new THREE.Vector3(...area) }, uCenter: { value: new THREE.Vector3(...center) },
    uSize: { value: new THREE.Vector2(...size) }, uColor: { value: lin3(color ?? defColor) }, uOpacity: { value: opacity }, uSpeed: { value: speed },
    uWind: { value: new THREE.Vector3(...wind) }, uFocus: { value: focus }, uBokeh: { value: bokeh }, uPx: { value: 500 }, uFadeNear: { value: fadeNear },
    uBeamO: { value: new THREE.Vector3(...(beam?.origin ?? [0, 0, 0])) }, uBeamD: { value: new THREE.Vector3(...(beam?.dir ?? [0, -1, 0])).normalize() }, uBeamR: { value: beam?.radius ?? 1 }, uBeamFloor: { value: beam?.floor ?? 0.08 }, uBeamOn: { value: beam ? 1 : 0 },
  };
  const m = new THREE.ShaderMaterial({
    uniforms,
    vertexShader: /* glsl */`
      attribute vec4 aRnd;
      uniform float uTime, uSpeed, uFocus, uBokeh, uPx, uOpacity, uFadeNear, uBeamR, uBeamFloor, uBeamOn; uniform int uKind;
      uniform vec3 uBox, uCenter, uWind, uBeamO, uBeamD; uniform vec2 uSize;
      varying float vA; varying float vSoft; varying float vLife;
      vec3 wrapBox(vec3 p){ return mod(p + uBox * 0.5, uBox) - uBox * 0.5; }
      void main(){
        float t = uTime; vec3 p = position; vec4 R = aRnd;
        vLife = 0.0;
        if (uKind == 1) {           // snow: fall, sway, wind
          p.y -= t * uSpeed * (0.35 + 0.5 * R.x);
          p.x += sin(t * (0.6 + R.y) + R.z * 6.283) * 0.25 * (0.4 + R.w);
          p.z += cos(t * (0.5 + R.x) + R.y * 6.283) * 0.2 * (0.4 + R.z);
        } else if (uKind == 2) {    // embers: rise, curl, flicker
          p.y += t * uSpeed * (0.4 + 0.8 * R.x);
          p.x += sin(t * (1.1 + R.y * 1.7) + R.z * 6.283) * 0.3 * R.w;
          p.z += cos(t * (0.9 + R.x * 1.3) + R.w * 6.283) * 0.3 * R.y;
          vLife = fract((position.y / uBox.y + 0.5) + t * uSpeed * (0.4 + 0.8 * R.x) / uBox.y);
        } else {                    // dust motes: slow brownian drift
          p += vec3(sin(t * 0.13 * (1.0 + R.x) + R.y * 6.283), sin(t * 0.11 * (1.0 + R.z) + R.w * 6.283) + t * 0.03, sin(t * 0.09 * (1.0 + R.y) + R.x * 6.283)) * 0.35 * uSpeed;
        }
        p += uWind * t;
        p = wrapBox(p);
        vec3 e = abs(p) / (uBox * 0.5);
        float edge = 1.0 - smoothstep(0.85, 1.0, max(max(e.x, e.y), e.z));
        vec3 wp = (modelMatrix * vec4(p + uCenter, 1.0)).xyz;
        vec4 mv = viewMatrix * vec4(wp, 1.0);
        float dist = max(-mv.z, 1e-3);
        float sz = mix(uSize.x, uSize.y, R.w * R.w) * uPx / dist;
        float coc = uFocus > 0.0 ? uBokeh * abs(1.0 - uFocus / dist) : 0.0;
        float tot = sz + coc;
        float a = uOpacity * edge * clamp((sz * sz + 0.25) / (tot * tot + 0.25), 0.04, 1.0);
        a *= smoothstep(uFadeNear * 0.5, uFadeNear, dist);
        if (uKind == 0) a *= 0.55 + 0.45 * sin(t * (1.0 + 2.0 * R.x) + R.y * 6.283);
        if (uKind == 2) a *= smoothstep(0.0, 0.1, vLife) * (1.0 - smoothstep(0.6, 1.0, vLife)) * (0.6 + 0.4 * sin(t * 12.0 * (0.5 + R.z) + R.x * 30.0));
        if (uBeamOn > 0.5) {
          vec3 d = wp - uBeamO; float along = dot(d, uBeamD); float rr = length(d - uBeamD * along);
          a *= mix(uBeamFloor, 1.0, (1.0 - smoothstep(uBeamR * 0.3, uBeamR, rr)) * step(0.0, along));
        }
        if (tot < 1.0) { a *= tot; tot = 1.0; }
        vA = a; vSoft = clamp(coc / max(tot, 1e-3), 0.0, 1.0);
        gl_PointSize = tot;
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: /* glsl */`
      uniform vec3 uColor; uniform int uKind; varying float vA; varying float vSoft; varying float vLife;
      void main(){
        float d = length(gl_PointCoord - 0.5) * 2.0;
        float soft = mix(0.55, 0.12, vSoft);
        float disc = 1.0 - smoothstep(1.0 - soft, 1.0, d);
        if (vSoft < 0.3) disc *= mix(1.0, exp(-d * d * 2.5), 0.6);
        vec3 c = uColor;
        if (uKind == 2) c = mix(uColor, vec3(1.0, 0.25, 0.05), vLife);
        float a = disc * vA;
        if (a < 0.002) discard;
        gl_FragColor = vec4(c * a, a);
      }`,
    transparent: true, depthWrite: false,
    blending: add ? THREE.AdditiveBlending : THREE.CustomBlending,
    blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor, blendEquation: THREE.AddEquation,
  });
  if (add) { m.blending = THREE.CustomBlending; m.blendSrc = THREE.OneFactor; m.blendDst = THREE.OneFactor; }
  const points = new THREE.Points(geo, m);
  points.frustumCulled = false;
  return {
    group: points, material: m, uniforms,
    // t: time; camera: ctx.camera (for pixel scale)
    update(t, camera) {
      uniforms.uTime.value = t;
      if (camera) uniforms.uPx.value = H / (2 * Math.tan(A.rad(camera.fov) / 2));
    },
    setOpacity(a) { uniforms.uOpacity.value = opacity * a; points.visible = a > 0.001; },
    setFocus(f, b = uniforms.uBokeh.value) { uniforms.uFocus.value = f; uniforms.uBokeh.value = b; },
  };
}
// One-shot burst of sparks from a point; update(t, t0, origin).
export function sparks({ count = 40, color = PAL.lamp, size = 0.06, speed = 4, life = 0.7, seed = 11, spread = Math.PI * 2, dir = Math.PI / 2, gravity = 1.2 } = {}) {
  const r = A.rng(seed);
  const v = [];
  for (let i = 0; i < count; i++) {
    const a = dir + (r() - 0.5) * spread, s = speed * (0.35 + r() * 0.65);
    v.push([Math.cos(a) * s, Math.sin(a) * s, (r() - 0.2) * s * 0.6, 0.6 + r() * 0.8]);
  }
  const pos = new Float32Array(count * 3);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const mat = new THREE.PointsMaterial({ map: TX.dot(), color: col(color).multiplyScalar(3), size, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
  const points = new THREE.Points(geo, mat);
  points.frustumCulled = false;
  return {
    group: points,
    update(t, t0, origin = [0, 0, 0]) {
      const x = t - t0;
      points.visible = x > 0 && x < life;
      if (!points.visible) return;
      const k = x / life;
      v.forEach(([vx, vy, vz, sl], i) => {
        const d = (1 - Math.exp(-x * 4)) / 4;
        pos[i * 3] = origin[0] + vx * d * sl; pos[i * 3 + 1] = origin[1] + vy * d * sl - gravity * x * x; pos[i * 3 + 2] = origin[2] + vz * d;
      });
      geo.attributes.position.needsUpdate = true;
      mat.opacity = (1 - k) * (1 - k);
      mat.size = size * (1 - k * 0.5);
    },
  };
}

// ---------------------------------------------------------------- 3D text
const fonts = {}, otFonts = {};
// Load 3D fonts by key (see FONT3D in fonts.js), or { key: url }.
export async function loadFonts(keys = Object.keys(FONT3D)) {
  const loader = new TTFLoader();
  const list = Array.isArray(keys) ? keys.map((k) => [k, FONT3D[k]]) : Object.entries(keys);
  await Promise.all(list.map(async ([k, url]) => {
    if (fonts[k]) return;
    if (!url) throw new Error(`unknown 3D font: ${k}`);
    const buf = await (await fetch(url)).arrayBuffer();
    fonts[k] = new Font(loader.parse(buf));
    try { otFonts[k] = opentype.parse(buf); } catch { otFonts[k] = null; }
  }));
  return fonts;
}
export { fonts };

let noiseNormal = null;
function faceNormalMap() {
  if (noiseNormal) return noiseNormal;
  const S = 256, f = TX.fbmField(S, { scale: 16, octaves: 4, seed: 77 });
  const c = document.createElement('canvas'); c.width = c.height = S;
  const g = c.getContext('2d'), id = g.createImageData(S, S);
  for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
    const dx = f[y * S + ((x + 1) % S)] - f[y * S + ((x + S - 1) % S)], dy = f[((y + 1) % S) * S + x] - f[((y + S - 1) % S) * S + x];
    const n = new THREE.Vector3(-dx * 6, -dy * 6, 1).normalize();
    const i = (y * S + x) * 4; id.data[i] = (n.x * 0.5 + 0.5) * 255; id.data[i + 1] = (n.y * 0.5 + 0.5) * 255; id.data[i + 2] = (n.z * 0.5 + 0.5) * 255; id.data[i + 3] = 255;
  }
  g.putImageData(id, 0, 0);
  noiseNormal = new THREE.CanvasTexture(c);
  noiseNormal.wrapS = noiseNormal.wrapT = THREE.RepeatWrapping;
  return noiseNormal;
}

const glyphCache = new Map();
const capCache = {};
// Extruded, bevelled 3D text, one mesh per character (animate chars[i].holder).
//   font      FONT3D key ('archivoX900' title face, 'plex500', 'courier700', ...)
//   size      em size in world units, or capHeight: cap height in world units
//   depth, bevel (world units; style bible: 0.12 and 0.015 x cap height), bevelSegments
//   tracking  em; kerning (font GPOS/kern) on by default
//   face, side  colours or materials. Defaults: matte bone face, dark metal sides
//   faceRough, faceMetal, sideRough, sideMetal, emissive (face glow intensity), noise (face normal-map strength)
//   glow      true: put the text on the selective glow layer
// Returns { group, chars: [{ ch, holder, mesh, x, w }], width, capH, faceMat, sideMat, setOpacity, setColor }
export function text3d(str, o = {}) {
  const fk = o.font ?? 'archivoX900';
  const f = fonts[fk];
  if (!f) throw new Error(`3D font not loaded: ${fk} (await kit.loadFonts(['${fk}']) in init)`);
  const ot = otFonts[fk];
  const res = f.data.resolution;
  if (!capCache[fk]) {
    const hg = new TextGeometry('H', { font: f, size: 1, depth: 0, curveSegments: 2, bevelEnabled: false });
    hg.computeBoundingBox(); capCache[fk] = hg.boundingBox.max.y - hg.boundingBox.min.y; hg.dispose();
  }
  const size = o.capHeight ? o.capHeight / capCache[fk] : o.size ?? 1;
  const capH = capCache[fk] * size;
  const depth = o.depth ?? 0.12 * capH, bevel = o.bevel ?? 0.015 * capH;
  const tracking = o.tracking ?? 0.0;
  const faceMat = o.face?.isMaterial ? o.face : new THREE.MeshPhysicalMaterial({
    color: col(o.face ?? PAL.bone), roughness: o.faceRough ?? 0.6, metalness: o.faceMetal ?? 0, transparent: true,
    emissive: col(o.face ?? PAL.bone), emissiveIntensity: o.emissive ?? 0,
    normalMap: (o.noise ?? 0.05) > 0 ? faceNormalMap() : null,
  });
  if (faceMat.normalMap) { faceMat.normalScale = new THREE.Vector2(o.noise ?? 0.05, o.noise ?? 0.05).multiplyScalar(20); faceMat.normalMap.repeat.set(1 / (capH * 1.5), 1 / (capH * 1.5)); }
  const sideMat = o.side?.isMaterial ? o.side : new THREE.MeshPhysicalMaterial({ color: col(o.side ?? PAL.char), roughness: o.sideRough ?? 0.35, metalness: o.sideMetal ?? 0.6, transparent: true });
  const group = new THREE.Group();
  const chars = [];
  let x = 0, prev = null;
  for (const ch of str) {
    const g = f.data.glyphs[ch] ?? f.data.glyphs['?'];
    let kern = 0;
    if (ot && prev && (o.kerning ?? true)) {
      try { kern = ot.getKerningValue(ot.charToGlyph(prev), ot.charToGlyph(ch)) / ot.unitsPerEm * size; } catch { kern = 0; }
    }
    x += kern;
    const adv = (g.ha / res) * size;
    if (ch !== ' ') {
      const key = `${fk}|${ch}|${size}|${depth}|${bevel}|${o.bevelSegments ?? 3}|${o.curveSegments ?? 8}`;
      let geo = glyphCache.get(key);
      if (!geo) {
        geo = new TextGeometry(ch, { font: f, size, depth, curveSegments: o.curveSegments ?? 8, bevelEnabled: bevel > 0, bevelThickness: bevel, bevelSize: bevel * 0.8, bevelSegments: o.bevelSegments ?? 3 });
        geo.translate(-adv / 2, -capH / 2, -depth / 2);
        geo.computeVertexNormals();
        glyphCache.set(key, geo);
      }
      const mesh = new THREE.Mesh(geo, [faceMat, sideMat]);
      mesh.castShadow = true; mesh.receiveShadow = true;
      const holder = new THREE.Group();
      holder.add(mesh);
      holder.position.x = x + adv / 2;
      group.add(holder);
      chars.push({ ch, holder, mesh, x: x + adv / 2, w: adv });
    }
    x += adv + tracking * size;
    prev = ch;
  }
  const width = x - tracking * size;
  const shift = o.align === 'left' ? 0 : o.align === 'right' ? -width : -width / 2;
  for (const c of chars) { c.holder.position.x += shift; c.x += shift; c.holder.userData.baseX = c.x; }
  if (o.glow) glowLayer(group);
  return {
    group, chars, width, capH, size, faceMat, sideMat,
    setOpacity(a) { faceMat.opacity = a; sideMat.opacity = a; faceMat.depthWrite = sideMat.depthWrite = a > 0.98; group.visible = a > 0.001; },
    setColor(face, side) { if (face) { faceMat.color.set(face); faceMat.emissive.set(face); } if (side) sideMat.color.set(side); },
  };
}

// ---------------------------------------------------------------- icons, cards, strokes
// Extrude an SVG (fill paths) into a 3D icon centred at the origin.
export function svgIcon(svg, { size = 1, depth = 0.18, color = PAL.bone, bevel = 0.02, material } = {}) {
  const data = new SVGLoader().parse(svg);
  const shapes = data.paths.flatMap((p) => SVGLoader.createShapes(p));
  const flat = new THREE.ShapeGeometry(shapes);
  flat.computeBoundingBox();
  const bb = flat.boundingBox; flat.dispose();
  const s = size / Math.max(bb.max.x - bb.min.x, bb.max.y - bb.min.y);
  const geo = new THREE.ExtrudeGeometry(shapes, { depth: depth / s, bevelEnabled: bevel > 0, bevelThickness: bevel / s, bevelSize: (bevel * 0.6) / s, bevelSegments: 2, curveSegments: 10 });
  geo.translate(-(bb.min.x + bb.max.x) / 2, -(bb.min.y + bb.max.y) / 2, 0);
  geo.scale(s, -s, -s); geo.translate(0, 0, depth); geo.computeVertexNormals();
  const mesh = new THREE.Mesh(geo, material ?? glossy(color));
  mesh.castShadow = true;
  const group = new THREE.Group(); group.add(mesh);
  return { group, mesh, setOpacity(a) { setOpacity(group, a); } };
}
// Rounded slab (a card, a tag, a table top).
export function card({ w = 8, h = 5, r = 0.3, depth = 0.1, color = PAL.bone, material } = {}) {
  const shape = new THREE.Shape();
  const x = -w / 2, y = -h / 2;
  shape.moveTo(x + r, y); shape.lineTo(x + w - r, y); shape.quadraticCurveTo(x + w, y, x + w, y + r);
  shape.lineTo(x + w, y + h - r); shape.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  shape.lineTo(x + r, y + h); shape.quadraticCurveTo(x, y + h, x, y + h - r);
  shape.lineTo(x, y + r); shape.quadraticCurveTo(x, y, x + r, y);
  const geo = new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: true, bevelThickness: Math.min(0.05, depth / 3), bevelSize: Math.min(0.05, r / 2), bevelSegments: 3, curveSegments: 12 });
  const mesh = new THREE.Mesh(geo, material ?? new THREE.MeshStandardMaterial({ color: col(color), roughness: 0.7, transparent: true }));
  mesh.castShadow = true; mesh.receiveShadow = true;
  const group = new THREE.Group(); group.add(mesh);
  return { group, mesh, w, h, depth, setOpacity(a) { setOpacity(group, a); } };
}
// A tube along a polyline, drawn on with setDraw(to, from).
export function stroke(points, { color = PAL.bone, radius = 0.03, material, segmentsPerUnit = 8, emissiveIntensity = 0 } = {}) {
  const pts = points.map((p) => (p.isVector3 ? p.clone() : new THREE.Vector3(p[0], p[1], p[2] ?? 0)));
  const lens = [0];
  for (let i = 1; i < pts.length; i++) lens.push(lens[i - 1] + pts[i].distanceTo(pts[i - 1]));
  const L = lens[lens.length - 1];
  const mat = material ?? (emissiveIntensity ? emissive(color, emissiveIntensity) : glossy(color, { rough: 0.4 }));
  const mesh = new THREE.Mesh(new THREE.BufferGeometry(), mat);
  mesh.castShadow = true;
  const capA = new THREE.Mesh(new THREE.SphereGeometry(radius, 12, 8), mat), capB = capA.clone();
  const group = new THREE.Group();
  group.add(mesh, capA, capB);
  let lastKey = -1;
  const pointAt = (d) => {
    for (let i = 1; i < pts.length; i++) {
      if (d <= lens[i] || i === pts.length - 1) {
        const f = A.clamp((d - lens[i - 1]) / Math.max(1e-6, lens[i] - lens[i - 1]));
        return { p: pts[i - 1].clone().lerp(pts[i], f), dir: pts[i].clone().sub(pts[i - 1]).normalize() };
      }
    }
    return { p: pts[0].clone(), dir: new THREE.Vector3(1, 0, 0) };
  };
  const self = {
    group, mesh, mat, length: L, points: pts, pointAt,
    setDraw(to, from = 0) {
      to = A.clamp(to); from = A.clamp(from);
      group.visible = to - from > 0.002;
      const end = pointAt(to * L), start = pointAt(from * L);
      capA.position.copy(start.p); capB.position.copy(end.p);
      const key = to * 1000 + from;
      if (!group.visible || key === lastKey) return;
      lastKey = key;
      const sub = [start.p];
      for (let i = 1; i < pts.length - 1; i++) if (lens[i] > from * L && lens[i] < to * L) sub.push(pts[i]);
      sub.push(end.p);
      const path = new THREE.CurvePath();
      for (let i = 1; i < sub.length; i++) path.add(new THREE.LineCurve3(sub[i - 1], sub[i]));
      mesh.geometry.dispose();
      mesh.geometry = new THREE.TubeGeometry(path, Math.max(2, Math.ceil((to - from) * L * segmentsPerUnit) + sub.length * 2), radius, 10, false);
    },
    setOpacity(a) { setOpacity(group, a); },
  };
  self.setDraw(0);
  return self;
}
// A sagging string between two points (evidence-board thread), as a stroke.
export function string(from, to, { sag = 0.15, color = PAL.red, radius = 0.008, segments = 24 } = {}) {
  const a = new THREE.Vector3(...from), b = new THREE.Vector3(...to);
  const pts = [];
  for (let i = 0; i <= segments; i++) { const f = i / segments; pts.push(a.clone().lerp(b, f).add(new THREE.Vector3(0, -Math.sin(f * Math.PI) * sag * a.distanceTo(b), 0))); }
  return stroke(pts, { color, radius, material: new THREE.MeshStandardMaterial({ color: col(color), roughness: 0.8, transparent: true }) });
}
