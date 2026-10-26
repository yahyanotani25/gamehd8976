// Post pipeline. The 3D world is rendered linear HDR; this module turns it
// into the finished frame:
//
//   world HDR ─┬─ scene-stage 2D layers (linear: leaks, footage overlays)
//              ├─ DOF (gather, half res)               fx.dof
//              ├─ bloom (global, threshold)            fx.bloom
//              ├─ glow (selective: kit.glowLayer objs) fx.glow
//              └─ halation (red-orange, threshold)     fx.halation
//   GRADE:  + light leak → exposure → tone map → sRGB → grade → LUT look(s)
//   display-stage 2D layers (dust, scratches, paper …) + the DOM overlay
//   FILM:   weave / shake / punch / lens distortion / glitch displacement →
//           zoom & directional blur + chromatic aberration → vignette →
//           flicker → flash / fade → grain → scanlines → letterbox → screen
//
// Everything is driven by the per-frame `fx` object (see core.js FX_DEFAULTS).

import * as THREE from 'three';
import { FullScreenQuad } from 'three/addons/postprocessing/Pass.js';
import * as A from './anim.js';

export const W = 1920, H = 1080;
let renderer = null;
const quad = new FullScreenQuad(null);

// ---------------------------------------------------------------- helpers
const _c = new THREE.Color();
// Display-referred (sRGB-encoded) components of a colour, 0..1, no conversion.
export function srgb(c) {
  if (Array.isArray(c)) return c;
  _c.set(c);
  return [_c.r, _c.g, _c.b].map((v) => (v <= 0.0031308 ? v * 12.92 : 1.055 * Math.pow(v, 1 / 2.4) - 0.055));
}
// Linear working-space components of a colour.
export function lin(c) {
  if (Array.isArray(c)) return c;
  _c.set(c);
  return [_c.r, _c.g, _c.b];
}
const v3 = (a) => new THREE.Vector3(a[0], a[1], a[2]);
const setV3 = (u, a) => u.value.set(a[0], a[1], a[2]);

function rt(w, h, o = {}) {
  const r = new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType, depthBuffer: false, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, generateMipmaps: false, ...o });
  r.texture.colorSpace = THREE.NoColorSpace;
  return r;
}
function pass(mat, target) {
  renderer.setRenderTarget(target);
  quad.material = mat;
  quad.render(renderer);
}

const VS = /* glsl */`varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;
const COMMON = /* glsl */`
  const vec3 LUMA = vec3(0.2126, 0.7152, 0.0722);
  float hash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
  float hash11(float p){ p = fract(p * 0.1031); p *= p + 33.33; p *= p + p; return fract(p); }
  float vnoise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f*f*(3.0-2.0*f);
    return mix(mix(hash12(i), hash12(i+vec2(1,0)), f.x), mix(hash12(i+vec2(0,1)), hash12(i+vec2(1,1)), f.x), f.y); }
  float fbm(vec2 p){ float s = 0.0, a = 0.5; for (int i = 0; i < 4; i++){ s += a * vnoise(p); p = p * 2.03 + 17.1; a *= 0.5; } return s / 0.9375; }
  vec3 toSRGB(vec3 c){ c = max(c, 0.0); return mix(c * 12.92, 1.055 * pow(c, vec3(1.0/2.4)) - 0.055, step(0.0031308, c)); }
  vec3 toLinear(vec3 c){ return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
`;
const mat = (fs, uniforms, o = {}) => new THREE.ShaderMaterial({ vertexShader: VS, fragmentShader: COMMON + fs, uniforms, depthTest: false, depthWrite: false, toneMapped: false, ...o });

// ---------------------------------------------------------------- shaders
const copyMat = mat(`uniform sampler2D tSrc; uniform float uW; varying vec2 vUv;
  void main(){ gl_FragColor = vec4(texture2D(tSrc, vUv).rgb * uW, 1.0); }`, { tSrc: { value: null }, uW: { value: 1 } });
const accumMat = mat(`uniform sampler2D tSrc; uniform float uW; varying vec2 vUv;
  void main(){ gl_FragColor = vec4(texture2D(tSrc, vUv).rgb * uW, 1.0); }`, { tSrc: { value: null }, uW: { value: 1 } },
  { blending: THREE.CustomBlending, blendEquation: THREE.AddEquation, blendSrc: THREE.OneFactor, blendDst: THREE.OneFactor, transparent: true });

// Background: vertical gradient + optional soft light pool (linear HDR).
const bgMat = mat(`uniform vec3 uTop, uBot, uPool; uniform vec4 uPoolGeo; varying vec2 vUv;
  void main(){
    vec3 c = mix(uBot, uTop, smoothstep(0.0, 1.0, vUv.y));
    vec2 d = (vUv - uPoolGeo.xy) * vec2(${(W / H).toFixed(5)}, 1.0);
    c += uPool * exp(-dot(d, d) / max(1e-4, uPoolGeo.z * uPoolGeo.z));
    gl_FragColor = vec4(c, 1.0);
  }`, { uTop: { value: new THREE.Vector3() }, uBot: { value: new THREE.Vector3() }, uPool: { value: new THREE.Vector3() }, uPoolGeo: { value: new THREE.Vector4(0.5, 0.5, 0.4, 0) } });

// Downsample (4 bilinear taps = box) + soft-knee threshold.
const extractMat = mat(`uniform sampler2D tSrc; uniform vec2 uTexel; uniform float uThreshold, uKnee; varying vec2 vUv;
  void main(){
    vec3 c = 0.25 * (texture2D(tSrc, vUv + uTexel * vec2(-1.0,-1.0)).rgb + texture2D(tSrc, vUv + uTexel * vec2(1.0,-1.0)).rgb
                   + texture2D(tSrc, vUv + uTexel * vec2(-1.0, 1.0)).rgb + texture2D(tSrc, vUv + uTexel * vec2(1.0, 1.0)).rgb);
    c = min(c, vec3(64.0));
    float br = max(c.r, max(c.g, c.b));
    float soft = clamp(br - uThreshold + uKnee, 0.0, 2.0 * uKnee);
    soft = soft * soft / (4.0 * uKnee + 1e-5);
    float k = max(soft, br - uThreshold) / max(br, 1e-5);
    gl_FragColor = vec4(c * max(k, 0.0), 1.0);
  }`, { tSrc: { value: null }, uTexel: { value: new THREE.Vector2() }, uThreshold: { value: 1 }, uKnee: { value: 0.2 } });
const downMat = mat(`uniform sampler2D tSrc; uniform vec2 uTexel; varying vec2 vUv;
  void main(){ gl_FragColor = vec4(0.25 * (texture2D(tSrc, vUv + uTexel * vec2(-0.5,-0.5)).rgb + texture2D(tSrc, vUv + uTexel * vec2(0.5,-0.5)).rgb
    + texture2D(tSrc, vUv + uTexel * vec2(-0.5, 0.5)).rgb + texture2D(tSrc, vUv + uTexel * vec2(0.5, 0.5)).rgb), 1.0); }`,
  { tSrc: { value: null }, uTexel: { value: new THREE.Vector2() } });
// 9-tap gaussian in 5 linear fetches (sigma ~ 2 texels * spread).
const blurMat = mat(`uniform sampler2D tSrc; uniform vec2 uDir; varying vec2 vUv;
  void main(){
    vec3 c = texture2D(tSrc, vUv).rgb * 0.2270270270;
    c += (texture2D(tSrc, vUv + uDir * 1.3846153846).rgb + texture2D(tSrc, vUv - uDir * 1.3846153846).rgb) * 0.3162162162;
    c += (texture2D(tSrc, vUv + uDir * 3.2307692308).rgb + texture2D(tSrc, vUv - uDir * 3.2307692308).rgb) * 0.0702702703;
    gl_FragColor = vec4(c, 1.0);
  }`, { tSrc: { value: null }, uDir: { value: new THREE.Vector2() } });

// DOF: colour + signed circle of confusion (px, - near / + far) at half res.
const cocMat = mat(`uniform sampler2D tSrc; uniform sampler2D tDepth; uniform vec2 uTexel; uniform float uNear, uFar, uFocus, uBlur, uMaxBlur; varying vec2 vUv;
  void main(){
    vec3 c = 0.25 * (texture2D(tSrc, vUv + uTexel * vec2(-0.5,-0.5)).rgb + texture2D(tSrc, vUv + uTexel * vec2(0.5,-0.5)).rgb
                   + texture2D(tSrc, vUv + uTexel * vec2(-0.5, 0.5)).rgb + texture2D(tSrc, vUv + uTexel * vec2(0.5, 0.5)).rgb);
    float d = texture2D(tDepth, vUv).x;
    float viewZ = (uNear * uFar) / ((uFar - uNear) * d - uFar);
    float dist = max(-viewZ, 1e-3);
    float coc = clamp(uBlur * (1.0 - uFocus / dist), -uMaxBlur, uMaxBlur);
    gl_FragColor = vec4(min(c, vec3(64.0)), coc);
  }`, { tSrc: { value: null }, tDepth: { value: null }, uTexel: { value: new THREE.Vector2() }, uNear: { value: 0.1 }, uFar: { value: 1000 }, uFocus: { value: 10 }, uBlur: { value: 8 }, uMaxBlur: { value: 16 } });
const gatherMat = mat(`uniform sampler2D tSrc; uniform vec2 uPx; uniform float uMaxBlur; varying vec2 vUv;
  void main(){
    vec4 c0 = texture2D(tSrc, vUv);
    float r0 = abs(c0.a);
    vec3 acc = c0.rgb; float ws = 1.0; float nearCov = 0.0;
    for (int i = 0; i < 40; i++) {
      float fi = float(i) + 0.5;
      float rr = sqrt(fi / 40.0) * uMaxBlur;
      float a = fi * 2.39996323;
      vec4 s = texture2D(tSrc, vUv + vec2(cos(a), sin(a)) * rr * uPx);
      float sr = s.a >= 0.0 ? min(s.a, r0 + 1.0) : -s.a;
      float w = smoothstep(rr - 1.0, rr + 1.0, sr);
      if (s.a < 0.0) nearCov = max(nearCov, w * smoothstep(0.5, 2.0, -s.a));
      acc += s.rgb * w; ws += w;
    }
    gl_FragColor = vec4(acc / ws, max(smoothstep(0.6, 2.0, r0), nearCov));
  }`, { tSrc: { value: null }, uPx: { value: new THREE.Vector2(1 / W, 1 / H) }, uMaxBlur: { value: 16 } });

// Transition mix between two HDR passes.
const mixMat = mat(`uniform sampler2D tA, tB; uniform float uP, uAngle, uFeather, uNoiseScale, uSeed; uniform int uKind; uniform vec2 uCenter; uniform vec3 uDip; varying vec2 vUv;
  void main(){
    vec3 a = texture2D(tA, vUv).rgb, b = texture2D(tB, vUv).rgb;
    float k = uP;
    if (uKind == 1) { // wipe
      vec2 dir = vec2(cos(uAngle), sin(uAngle));
      vec2 p = (vUv - 0.5) * vec2(${(W / H).toFixed(5)}, 1.0);
      float ext = 0.5 * (abs(dir.x) * ${(W / H).toFixed(5)} + abs(dir.y));
      float x = dot(p, dir) / ext * 0.5 + 0.5;
      float f = uFeather + 1e-4;
      k = smoothstep(x - f, x + f, uP * (1.0 + 2.0 * f) - f);
    } else if (uKind == 2) { // iris
      vec2 p = (vUv - uCenter) * vec2(${(W / H).toFixed(5)}, 1.0);
      float r = length(p) / 1.2;
      float f = uFeather + 1e-4;
      k = 1.0 - smoothstep(uP * (1.0 + f) - f, uP * (1.0 + f), r);
    } else if (uKind == 3) { // noise / mist dissolve
      float n = fbm(vUv * vec2(${(W / H).toFixed(5)}, 1.0) * uNoiseScale + uSeed);
      float f = uFeather + 1e-4;
      k = smoothstep(n - f, n + f, uP * (1.0 + 2.0 * f) - f);
    } else if (uKind == 4) { // dip to colour
      vec3 c = uP < 0.5 ? mix(a, uDip, uP * 2.0) : mix(uDip, b, uP * 2.0 - 1.0);
      gl_FragColor = vec4(c, 1.0); return;
    }
    gl_FragColor = vec4(mix(a, b, k), 1.0);
  }`, { tA: { value: null }, tB: { value: null }, uP: { value: 0 }, uAngle: { value: 0 }, uFeather: { value: 0.1 }, uNoiseScale: { value: 3 }, uSeed: { value: 0 }, uKind: { value: 0 }, uCenter: { value: new THREE.Vector2(0.5, 0.5) }, uDip: { value: new THREE.Vector3() } });

// 2D layer composite (ping-pong). Scene stage blends in linear HDR, display
// stage in display-referred values.
const BLENDS = { normal: 0, add: 1, screen: 2, multiply: 3, overlay: 4, 'soft-light': 5, softlight: 5, lighten: 6, darken: 7, difference: 8 };
const FITS = { cover: 0, contain: 1, stretch: 2, tile: 3 };
const layerMat = mat(`
  uniform sampler2D tBase, tLayer, tMask;
  uniform int uBlend, uFit, uStage, uAlphaMode, uMaskOn, uMaskChannel, uWipeOn, uIrisOn;
  uniform float uOpacity, uFlipY, uScale, uRot, uSrgbDecoded, uInvert, uMaskInvert, uMaskThreshold, uMaskFeather, uMaskFlipY, uWipeP, uWipeAngle, uWipeFeather, uIrisFeather;
  uniform vec2 uTexSize, uOffset, uTile, uLevels;
  uniform vec3 uTint, uIris;
  varying vec2 vUv;
  float bl(float b, float s, int m){
    if (m == 4) return b < 0.5 ? 2.0 * b * s : 1.0 - 2.0 * (1.0 - b) * (1.0 - s);
    if (m == 5) { if (s <= 0.5) return b - (1.0 - 2.0 * s) * b * (1.0 - b);
      float d = b <= 0.25 ? ((16.0 * b - 12.0) * b + 4.0) * b : sqrt(b); return b + (2.0 * s - 1.0) * (d - b); }
    return s;
  }
  void main(){
    vec3 base = texture2D(tBase, vUv).rgb;
    vec2 px = vec2(vUv.x * ${W}.0, (1.0 - vUv.y) * ${H}.0);          // screen px, y down
    vec2 q = px - vec2(${W / 2}.0, ${H / 2}.0) - uOffset;
    float cr = cos(-uRot), sr = sin(-uRot);
    q = vec2(cr * q.x - sr * q.y, sr * q.x + cr * q.y) / uScale;
    vec2 st;                                                        // texture coords, y down
    float sa = ${(W / H).toFixed(6)}, ta = uTexSize.x / uTexSize.y;
    if (uFit == 3) st = (q + vec2(${W / 2}.0, ${H / 2}.0)) / uTile;
    else {
      vec2 sz = vec2(${W}.0, ${H}.0);
      if (uFit == 0) sz = ta > sa ? vec2(${H}.0 * ta, ${H}.0) : vec2(${W}.0, ${W}.0 / ta);
      if (uFit == 1) sz = ta > sa ? vec2(${W}.0, ${W}.0 / ta) : vec2(${H}.0 * ta, ${H}.0);
      st = q / sz + 0.5;
    }
    float inside = (uFit == 3) ? 1.0 : step(0.0, st.x) * step(st.x, 1.0) * step(0.0, st.y) * step(st.y, 1.0);
    vec2 tuv = vec2(st.x, uFlipY > 0.5 ? 1.0 - st.y : st.y);
    vec4 L = texture2D(tLayer, tuv);
    vec3 s = L.rgb;
    if (uStage == 1 && uSrgbDecoded > 0.5) s = toSRGB(s);
    s = clamp((s - uLevels.x) / max(1e-4, uLevels.y - uLevels.x), 0.0, 64.0);
    if (uInvert > 0.5) s = 1.0 - s;
    s *= uTint;
    float a = uAlphaMode == 0 ? L.a : uAlphaMode == 1 ? clamp(dot(s, LUMA), 0.0, 1.0) : 1.0;
    a *= uOpacity * inside;
    if (uMaskOn == 1) {
      vec2 mp = vec2(vUv.x, uMaskFlipY > 0.5 ? vUv.y : 1.0 - vUv.y);
      vec4 M = texture2D(tMask, mp);
      float m = uMaskChannel == 0 ? dot(M.rgb, LUMA) : uMaskChannel == 1 ? M.a : M.r;
      if (uMaskInvert > 0.5) m = 1.0 - m;
      if (uMaskFeather >= 0.0) m = smoothstep(uMaskThreshold - uMaskFeather - 1e-4, uMaskThreshold + uMaskFeather, m);
      a *= m;
    }
    if (uWipeOn == 1) {
      vec2 dir = vec2(cos(uWipeAngle), sin(uWipeAngle));
      vec2 p = (vUv - 0.5) * vec2(sa, 1.0);
      float ext = 0.5 * (abs(dir.x) * sa + abs(dir.y));
      float x = dot(p, dir) / ext * 0.5 + 0.5;
      float f = uWipeFeather + 1e-4;
      a *= 1.0 - smoothstep(uWipeP * (1.0 + 2.0 * f) - 2.0 * f, uWipeP * (1.0 + 2.0 * f), x);
    }
    if (uIrisOn == 1) {
      vec2 p = (vUv - vec2(uIris.x, 1.0 - uIris.y)) * vec2(sa, 1.0);
      float r = length(p) / 1.2, f = uIrisFeather + 1e-4;
      a *= 1.0 - smoothstep(uIris.z * (1.0 + f) - f, uIris.z * (1.0 + f), r);
    }
    vec3 r;
    if (uBlend == 0) r = s;
    else if (uBlend == 1) r = base + s;
    else if (uBlend == 2) r = base + s * (1.0 - clamp(base, 0.0, 1.0));
    else if (uBlend == 3) r = base * s;
    else if (uBlend == 6) r = max(base, s);
    else if (uBlend == 7) r = min(base, s);
    else if (uBlend == 8) r = abs(base - s);
    else { vec3 bc = clamp(base, 0.0, 1.0); r = vec3(bl(bc.r, s.r, uBlend), bl(bc.g, s.g, uBlend), bl(bc.b, s.b, uBlend)) + (base - bc); }
    gl_FragColor = vec4(mix(base, r, clamp(a, 0.0, 1.0)), 1.0);
  }`, {
  tBase: { value: null }, tLayer: { value: null }, tMask: { value: null },
  uBlend: { value: 0 }, uFit: { value: 0 }, uStage: { value: 1 }, uAlphaMode: { value: 0 }, uMaskOn: { value: 0 }, uMaskChannel: { value: 0 }, uWipeOn: { value: 0 }, uIrisOn: { value: 0 },
  uOpacity: { value: 1 }, uFlipY: { value: 1 }, uScale: { value: 1 }, uRot: { value: 0 }, uSrgbDecoded: { value: 1 }, uInvert: { value: 0 },
  uMaskInvert: { value: 0 }, uMaskThreshold: { value: 0.5 }, uMaskFeather: { value: -1 }, uMaskFlipY: { value: 1 },
  uWipeP: { value: 1 }, uWipeAngle: { value: 0 }, uWipeFeather: { value: 0.05 }, uIrisFeather: { value: 0.05 },
  uTexSize: { value: new THREE.Vector2(1, 1) }, uOffset: { value: new THREE.Vector2() }, uTile: { value: new THREE.Vector2(512, 512) }, uLevels: { value: new THREE.Vector2(0, 1) },
  uTint: { value: new THREE.Vector3(1, 1, 1) }, uIris: { value: new THREE.Vector3(0.5, 0.5, 1) },
});

// GRADE: HDR -> display. Tone maps from three.js (AgX after Filament/Blender,
// ACES fit by Stephen Hill, Khronos PBR Neutral).
const gradeMat = mat(`
  precision highp sampler3D;
  uniform sampler2D tScene, tDof, tB0, tB1, tB2, tB3, tG0, tG1, tG2, tG3, tH0, tH1;
  uniform float uDofOn, uBloom, uGlow, uHal, uLeak, uLeakSide, uLeakPos, uLeakSeed, uLeakWidth, uTime, uExposure, uAgxPunch;
  uniform vec4 uBloomW, uGlowW; uniform vec2 uHalW; uniform vec3 uHalTint, uLeakColor;
  uniform int uTonemap;
  uniform vec3 uWB, uLift, uGamma, uGain, uShadowTint, uHighTint;
  uniform float uContrast, uPivot, uCurve, uSat, uVib, uBalance, uBlacks, uWhites;
  uniform sampler3D tLutA, tLutB; uniform float uLutSizeA, uLutSizeB, uLookMix, uLookAmt;
  varying vec2 vUv;
  const mat3 SRGB_TO_2020 = mat3(vec3(0.6274, 0.0691, 0.0164), vec3(0.3293, 0.9195, 0.0880), vec3(0.0433, 0.0113, 0.8956));
  const mat3 R2020_TO_SRGB = mat3(vec3(1.6605, -0.1246, -0.0182), vec3(-0.5876, 1.1329, -0.1006), vec3(-0.0728, -0.0083, 1.1187));
  vec3 agxContrast(vec3 x){ vec3 x2 = x*x, x4 = x2*x2; return 15.5*x4*x2 - 40.14*x4*x + 31.96*x4 - 6.868*x2*x + 0.4298*x2 + 0.1191*x - 0.00232; }
  vec3 agx(vec3 c){
    const mat3 inset = mat3(vec3(0.856627153315983, 0.137318972929847, 0.11189821299995), vec3(0.0951212405381588, 0.761241990602591, 0.0767994186031903), vec3(0.0482516061458583, 0.101439036467562, 0.811302368396859));
    const mat3 outset = mat3(vec3(1.1271005818144368, -0.1413297634984383, -0.14132976349843826), vec3(-0.11060664309660323, 1.157823702216272, -0.11060664309660294), vec3(-0.016493938717834573, -0.016493938717834257, 1.2519364065950405));
    c = inset * (SRGB_TO_2020 * c);
    c = clamp((log2(max(c, 1e-10)) + 12.47393) / 16.5, 0.0, 1.0);
    c = agxContrast(c);
    if (uAgxPunch > 0.0) { float l = dot(c, vec3(0.2126, 0.7152, 0.0722)); c = mix(vec3(l), c, 1.0 + 0.4 * uAgxPunch); c = pow(max(c, 0.0), vec3(1.0 + 0.35 * uAgxPunch)); }
    c = outset * c;
    c = pow(max(c, 0.0), vec3(2.2));
    return clamp(R2020_TO_SRGB * c, 0.0, 1.0);
  }
  vec3 aces(vec3 c){
    const mat3 i = mat3(vec3(0.59719, 0.07600, 0.02840), vec3(0.35458, 0.90834, 0.13383), vec3(0.04823, 0.01566, 0.83777));
    const mat3 o = mat3(vec3(1.60475, -0.10208, -0.00327), vec3(-0.53108, 1.10813, -0.07276), vec3(-0.07367, -0.00605, 1.07602));
    c = i * (c / 0.6);
    vec3 a = c * (c + 0.0245786) - 0.000090537, b = c * (0.983729 * c + 0.4329510) + 0.238081;
    return clamp(o * (a / b), 0.0, 1.0);
  }
  vec3 neutral(vec3 c){
    float x = min(c.r, min(c.g, c.b)); float off = x < 0.08 ? x - 6.25 * x * x : 0.04; c -= off;
    float peak = max(c.r, max(c.g, c.b)); if (peak < 0.76) return c;
    float d = 0.24; float np = 1.0 - d * d / (peak + d - 0.76); c *= np / peak;
    float g = 1.0 - 1.0 / (0.15 * (peak - np) + 1.0); return mix(c, vec3(np), g);
  }
  vec3 lut(sampler3D t, float n, vec3 c){ return texture(t, clamp(c, 0.0, 1.0) * ((n - 1.0) / n) + 0.5 / n).rgb; }
  void main(){
    vec3 c = texture2D(tScene, vUv).rgb;
    if (uDofOn > 0.5) { vec4 d = texture2D(tDof, vUv); c = mix(c, d.rgb, d.a); }
    if (uBloom > 0.0) c += uBloom * (uBloomW.x * texture2D(tB0, vUv).rgb + uBloomW.y * texture2D(tB1, vUv).rgb + uBloomW.z * texture2D(tB2, vUv).rgb + uBloomW.w * texture2D(tB3, vUv).rgb);
    if (uGlow > 0.0) c += uGlow * (uGlowW.x * texture2D(tG0, vUv).rgb + uGlowW.y * texture2D(tG1, vUv).rgb + uGlowW.z * texture2D(tG2, vUv).rgb + uGlowW.w * texture2D(tG3, vUv).rgb);
    if (uHal > 0.0) { vec3 h = uHalW.x * texture2D(tH0, vUv).rgb + uHalW.y * texture2D(tH1, vUv).rgb; c += uHal * uHalTint * dot(h, LUMA); }
    if (uLeak > 0.0) {
      vec2 p = vUv;
      float x = uLeakSide < 0.5 ? p.x : uLeakSide < 1.5 ? 1.0 - p.x : uLeakSide < 2.5 ? 1.0 - p.y : p.y;
      float y = uLeakSide < 1.5 ? p.y : p.x;
      float n = fbm(vec2(y * 2.2 + uLeakSeed * 7.0, uTime * 0.35 + uLeakSeed));
      float band = exp(-pow((y - uLeakPos) / 0.42, 2.0));
      float k = exp(-x / max(0.02, uLeakWidth)) * (0.35 + 0.9 * n) * (0.4 + 0.6 * band);
      vec3 lc = mix(uLeakColor, vec3(1.0, 0.92, 0.8) * dot(uLeakColor, LUMA) * 1.4, exp(-x / max(0.01, uLeakWidth * 0.25)) * 0.6);
      c += lc * k * uLeak * 2.0;
    }
    c *= exp2(uExposure);
    if (uTonemap == 1) c = agx(c); else if (uTonemap == 2) c = aces(c); else if (uTonemap == 3) c = neutral(c); else c = clamp(c, 0.0, 1.0);
    c = toSRGB(c);
    // primary grade (display-referred)
    c *= uWB;
    c *= uGain;
    c += uLift * (1.0 - c);
    c = pow(max(c, 0.0), uGamma);
    c = (c - uPivot) * uContrast + uPivot;
    if (uCurve != 0.0) { vec3 cc = clamp(c, 0.0, 1.0); c = mix(c, cc * cc * (3.0 - 2.0 * cc), uCurve); }
    float l = dot(c, LUMA);
    if (uVib != 0.0) { float mx = max(c.r, max(c.g, c.b)), mn = min(c.r, min(c.g, c.b)); c = mix(vec3(l), c, 1.0 + uVib * (1.0 - (mx - mn))); }
    c = mix(vec3(l), c, uSat);
    float ws = 1.0 - smoothstep(0.0, uBalance, l), wh = smoothstep(uBalance, 1.0, l);
    c += uShadowTint * ws + uHighTint * wh;
    c = uBlacks + c * (uWhites - uBlacks);
    if (uLookAmt > 0.0) {
      vec3 cl = clamp(c, 0.0, 1.0);
      vec3 la = lut(tLutA, uLutSizeA, cl);
      if (uLookMix > 0.0) la = mix(la, lut(tLutB, uLutSizeB, cl), uLookMix);
      c = mix(c, la, uLookAmt);
    }
    gl_FragColor = vec4(c, 1.0);
  }`, {
  tScene: { value: null }, tDof: { value: null }, tB0: { value: null }, tB1: { value: null }, tB2: { value: null }, tB3: { value: null },
  tG0: { value: null }, tG1: { value: null }, tG2: { value: null }, tG3: { value: null }, tH0: { value: null }, tH1: { value: null },
  uDofOn: { value: 0 }, uBloom: { value: 0 }, uGlow: { value: 0 }, uHal: { value: 0 }, uLeak: { value: 0 }, uLeakSide: { value: 0 }, uLeakPos: { value: 0.5 }, uLeakSeed: { value: 1 }, uLeakWidth: { value: 0.3 },
  uTime: { value: 0 }, uExposure: { value: 0 }, uAgxPunch: { value: 0 },
  uBloomW: { value: new THREE.Vector4(1, 0.8, 0.6, 0.4) }, uGlowW: { value: new THREE.Vector4(1, 0.8, 0.6, 0.4) }, uHalW: { value: new THREE.Vector2(0.5, 0.5) },
  uHalTint: { value: new THREE.Vector3(1, 0.35, 0.16) }, uLeakColor: { value: new THREE.Vector3(1, 0.5, 0.2) },
  uTonemap: { value: 1 },
  uWB: { value: new THREE.Vector3(1, 1, 1) }, uLift: { value: new THREE.Vector3() }, uGamma: { value: new THREE.Vector3(1, 1, 1) }, uGain: { value: new THREE.Vector3(1, 1, 1) },
  uShadowTint: { value: new THREE.Vector3() }, uHighTint: { value: new THREE.Vector3() },
  uContrast: { value: 1 }, uPivot: { value: 0.435 }, uCurve: { value: 0 }, uSat: { value: 1 }, uVib: { value: 0 }, uBalance: { value: 0.5 }, uBlacks: { value: 0 }, uWhites: { value: 1 },
  tLutA: { value: null }, tLutB: { value: null }, uLutSizeA: { value: 2 }, uLutSizeB: { value: 2 }, uLookMix: { value: 0 }, uLookAmt: { value: 0 },
});

// FILM: lens, camera and film artefacts over the whole composite (incl. DOM).
const filmMat = mat(`
  uniform sampler2D tImage, tGrain;
  uniform vec2 uWeave, uShake, uZoomC, uDir, uGrainOff;
  uniform float uWeaveRot, uPunch, uDistort, uZoom, uCA, uVig, uVigRound, uFlicker, uGlitch, uScan, uFlash, uFade, uGrain, uGrainFloor, uGrainChroma, uGrainSize, uGrainSwap, uBarsY, uBarsX, uFrame, uTime;
  uniform vec3 uFlashColor, uFadeColor, uBarsColor;
  varying vec2 vUv;
  const vec2 RES = vec2(${W}.0, ${H}.0);
  vec3 tapCA(vec2 uv, vec2 ca){
    return vec3(texture2D(tImage, uv + ca).r, texture2D(tImage, uv).g, texture2D(tImage, uv - ca).b);
  }
  void main(){
    vec2 px = vUv * RES;
    // gate weave + shake + punch-in (about the frame centre), in pixels
    vec2 c = px - RES * 0.5;
    float cr = cos(uWeaveRot), sr = sin(uWeaveRot);
    c = vec2(cr * c.x - sr * c.y, sr * c.x + cr * c.y);
    c = c / uPunch - uWeave - uShake;
    vec2 uv = (c + RES * 0.5) / RES;
    // lens distortion (barrel for +k), normalised so the corners stay put
    if (uDistort != 0.0) {
      vec2 d = (uv - 0.5) * vec2(${(W / H).toFixed(6)}, 1.0);
      float rmax2 = ${(0.25 * (W / H) ** 2 + 0.25).toFixed(6)};
      d *= (1.0 + uDistort * dot(d, d)) / (1.0 + uDistort * rmax2);
      uv = d / vec2(${(W / H).toFixed(6)}, 1.0) + 0.5;
    }
    // glitch: band shifts + block displacement
    float glt = uGlitch;
    float split = 0.0;
    if (glt > 0.0) {
      float fr = uFrame;
      float bands = mix(8.0, 48.0, hash11(fr * 1.37));
      float band = floor(uv.y * bands);
      float hb = hash12(vec2(band, fr));
      if (hb < glt * 0.55) uv.x += (hash12(vec2(band * 3.1, fr + 7.0)) - 0.5) * 0.12 * glt;
      vec2 cell = floor(uv * vec2(24.0, 14.0) * mix(0.5, 1.6, hash11(fr * 0.71)));
      float hc = hash12(cell + fr * 13.0);
      if (hc < glt * 0.18) uv += (vec2(hash12(cell + 1.7 + fr), hash12(cell + 9.2 + fr)) - 0.5) * vec2(0.08, 0.02) * glt;
      if (hash11(fr * 2.3) < glt * 0.25) uv.y = fract(uv.y + (hash11(fr * 5.1) - 0.5) * 0.08 * glt);
      split = glt * (0.004 + 0.012 * hb);
    }
    // chromatic aberration: radial, uCA px at the frame corner
    vec2 ca = (uv - 0.5) * (uCA / 1101.45) + vec2(split, 0.0);
    vec3 col;
    float blurAmt = uZoom + length(uDir);
    if (blurAmt < 0.0005) col = (uCA + split > 0.0001) ? tapCA(uv, ca) : texture2D(tImage, uv).rgb;
    else {
      col = vec3(0.0);
      vec2 toC = uZoomC - uv;
      for (int i = 0; i < 32; i++) {
        float f = float(i) / 31.0;
        vec2 o = toC * uZoom * f + uDir * (f - 0.5);
        col += tapCA(uv + o, ca * (1.0 + f));
      }
      col /= 32.0;
    }
    // vignette (elliptical, follows the frame shape)
    if (uVig > 0.0) {
      vec2 q = (vUv - 0.5) * vec2(mix(1.0, ${(W / H).toFixed(6)}, uVigRound), 1.0) * 2.0;
      float v = smoothstep(0.35, 1.45, length(q));
      col *= 1.0 - uVig * v * (0.6 + 0.4 * v);
    }
    if (uFlicker > 0.0) col *= 1.0 + uFlicker * (0.07 * (hash11(uFrame * 0.913) * 2.0 - 1.0) + 0.03 * sin(uTime * 37.0));
    col = mix(col, uFlashColor, clamp(uFlash, 0.0, 1.0));
    col = mix(col, uFadeColor, clamp(uFade, 0.0, 1.0));
    // grain: precomputed gaussian field (1.4 px clumps), new offset per output frame, luma weighted
    if (uGrain > 0.0) {
      vec2 gp = floor(gl_FragCoord.xy * (1.4 / uGrainSize));
      if (uGrainSwap > 0.5) gp = gp.yx;
      vec4 g = (texture2D(tGrain, (gp + uGrainOff + 0.5) / 1024.0) * 255.0 - 128.0) / 32.0;
      float L = clamp(dot(clamp(col, 0.0, 1.0), LUMA), 0.0, 1.0);
      float sigma = 0.024 * uGrain * (4.0 * L * (1.0 - L) + uGrainFloor);
      vec3 n = ((1.0 - uGrainChroma) * vec3(g.a) + uGrainChroma * g.rgb) / sqrt((1.0 - uGrainChroma) * (1.0 - uGrainChroma) + uGrainChroma * uGrainChroma);
      col += sigma * n;
    }
    if (uScan > 0.0) {
      col *= 1.0 - uScan * 0.35 * (0.5 + 0.5 * sin(px.y * 3.14159265));
      col += uScan * 0.06 * smoothstep(0.0, 0.02, fract(vUv.y * 0.5 - uTime * 0.6)) * (1.0 - smoothstep(0.02, 0.06, fract(vUv.y * 0.5 - uTime * 0.6)));
    }
    // letterbox / pillarbox (pixel-exact bars)
    float yTop = ${H}.0 - px.y;
    if (yTop < uBarsY || yTop > ${H}.0 - uBarsY || px.x < uBarsX || px.x > ${W}.0 - uBarsX) col = uBarsColor;
    gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
  }`, {
  tImage: { value: null }, tGrain: { value: null },
  uWeave: { value: new THREE.Vector2() }, uShake: { value: new THREE.Vector2() }, uZoomC: { value: new THREE.Vector2(0.5, 0.5) }, uDir: { value: new THREE.Vector2() }, uGrainOff: { value: new THREE.Vector2() },
  uWeaveRot: { value: 0 }, uPunch: { value: 1 }, uDistort: { value: 0 }, uZoom: { value: 0 }, uCA: { value: 0 }, uVig: { value: 0 }, uVigRound: { value: 0.35 }, uFlicker: { value: 0 }, uGlitch: { value: 0 }, uScan: { value: 0 },
  uFlash: { value: 0 }, uFade: { value: 0 }, uGrain: { value: 0 }, uGrainFloor: { value: 0.35 }, uGrainChroma: { value: 0.2 }, uGrainSize: { value: 1.4 }, uGrainSwap: { value: 0 },
  uBarsY: { value: 0 }, uBarsX: { value: 0 }, uFrame: { value: 0 }, uTime: { value: 0 },
  uFlashColor: { value: new THREE.Vector3(1, 1, 1) }, uFadeColor: { value: new THREE.Vector3() }, uBarsColor: { value: new THREE.Vector3() },
});

// ---------------------------------------------------------------- textures
// Gaussian grain field: generated at 1/1.4 resolution and upsampled bicubically
// (tileable), so a 1:1 lookup gives ~1.4 px grain clumps. RGB = chroma, A = mono.
function makeGrainTexture(seed = 1234) {
  const S = 1024, s = Math.round(S / 1.4);
  const r = A.rng(seed);
  const gauss = () => { let u = 0, v = 0; while (u === 0) u = r(); v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
  const out = new Uint8Array(S * S * 4);
  const cub = (p0, p1, p2, p3, x) => p1 + 0.5 * x * (p2 - p0 + x * (2 * p0 - 5 * p1 + 4 * p2 - p3 + x * (3 * (p1 - p2) + p3 - p0)));
  for (let ch = 0; ch < 4; ch++) {
    const src = new Float32Array(s * s);
    for (let i = 0; i < src.length; i++) src[i] = gauss();
    const up = new Float32Array(S * S);
    const at = (x, y) => src[((y + s) % s) * s + ((x + s) % s)];
    let sum = 0, sum2 = 0;
    for (let y = 0; y < S; y++) {
      const fy = (y * s) / S, iy = Math.floor(fy), ty = fy - iy;
      for (let x = 0; x < S; x++) {
        const fx = (x * s) / S, ix = Math.floor(fx), tx = fx - ix;
        const rows = [-1, 0, 1, 2].map((dy) => cub(at(ix - 1, iy + dy), at(ix, iy + dy), at(ix + 1, iy + dy), at(ix + 2, iy + dy), tx));
        const v = cub(rows[0], rows[1], rows[2], rows[3], ty);
        up[y * S + x] = v; sum += v; sum2 += v * v;
      }
    }
    const mean = sum / up.length, sd = Math.sqrt(sum2 / up.length - mean * mean);
    for (let i = 0; i < up.length; i++) out[i * 4 + ch] = Math.max(0, Math.min(255, Math.round(128 + ((up[i] - mean) / sd) * 32)));
  }
  const t = new THREE.DataTexture(out, S, S, THREE.RGBAFormat, THREE.UnsignedByteType);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.minFilter = t.magFilter = THREE.NearestFilter;
  t.needsUpdate = true;
  return t;
}
function solidTexture(rgba = [0, 0, 0, 255]) {
  const t = new THREE.DataTexture(new Uint8Array(rgba), 1, 1);
  t.needsUpdate = true;
  return t;
}

// ---------------------------------------------------------------- LUTs / looks
const LUTS = {};
function lutTexture(data, n) {
  const t = new THREE.Data3DTexture(data, n, n, n);
  t.format = THREE.RGBAFormat; t.type = THREE.FloatType;
  t.minFilter = t.magFilter = THREE.LinearFilter;
  t.wrapS = t.wrapT = t.wrapR = THREE.ClampToEdgeWrapping;
  t.unpackAlignment = 1;
  t.needsUpdate = true;
  return t;
}
function identityLUT(n = 2) {
  const d = new Float32Array(n * n * n * 4);
  let i = 0;
  for (let b = 0; b < n; b++) for (let g = 0; g < n; g++) for (let r = 0; r < n; r++) { d[i++] = r / (n - 1); d[i++] = g / (n - 1); d[i++] = b / (n - 1); d[i++] = 1; }
  return { tex: lutTexture(d, n), size: n };
}
// Parse an Adobe/Resolve .cube 3D LUT (red varies fastest).
export function parseCube(text) {
  let n = 0, dmin = [0, 0, 0], dmax = [1, 1, 1];
  const vals = [];
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    if (/^LUT_3D_SIZE/i.test(line)) { n = parseInt(line.split(/\s+/)[1], 10); continue; }
    if (/^DOMAIN_MIN/i.test(line)) { dmin = line.split(/\s+/).slice(1).map(Number); continue; }
    if (/^DOMAIN_MAX/i.test(line)) { dmax = line.split(/\s+/).slice(1).map(Number); continue; }
    if (/^(TITLE|LUT_1D_SIZE|LUT_3D_INPUT_RANGE)/i.test(line)) { if (/^LUT_1D/i.test(line)) throw new Error('1D .cube LUTs are not supported'); continue; }
    const p = line.split(/\s+/).map(Number);
    if (p.length >= 3 && !p.slice(0, 3).some(Number.isNaN)) vals.push(p[0], p[1], p[2]);
  }
  if (!n || vals.length !== n * n * n * 3) throw new Error(`bad .cube: size ${n}, ${vals.length / 3} entries`);
  if (dmin.some((v) => v !== 0) || dmax.some((v) => v !== 1)) console.warn('.cube DOMAIN other than 0..1 is ignored');
  const d = new Float32Array(n * n * n * 4);
  for (let i = 0; i < n * n * n; i++) { d[i * 4] = vals[i * 3]; d[i * 4 + 1] = vals[i * 3 + 1]; d[i * 4 + 2] = vals[i * 3 + 2]; d[i * 4 + 3] = 1; }
  return { data: d, size: n };
}
// Load a .cube file as a named look.
export async function loadLUT(name, url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`LUT not found: ${url}`);
  const { data, size } = parseCube(await res.text());
  LUTS[name] = { tex: lutTexture(data, size), size };
  return LUTS[name];
}
// Build a named look from any function (r, g, b in 0..1 display values) -> [r, g, b].
export function makeLUT(name, fn, size = 33) {
  const d = new Float32Array(size * size * size * 4);
  let i = 0;
  for (let b = 0; b < size; b++) for (let g = 0; g < size; g++) for (let r = 0; r < size; r++) {
    const o = fn(r / (size - 1), g / (size - 1), b / (size - 1));
    d[i++] = o[0]; d[i++] = o[1]; d[i++] = o[2]; d[i++] = 1;
  }
  LUTS[name] = { tex: lutTexture(d, size), size };
  return LUTS[name];
}
export const hasLUT = (name) => !!LUTS[name];

// Grade maths shared by the live grade (GLSL) and baked looks (JS).
const LUMA = [0.2126, 0.7152, 0.0722];
const luma = (c) => c[0] * LUMA[0] + c[1] * LUMA[1] + c[2] * LUMA[2];
export function wbGains(temp = 0, tint = 0) {
  const g = [1 + 0.12 * temp + 0.05 * tint, 1 - 0.1 * tint, 1 - 0.12 * temp + 0.05 * tint];
  const l = luma(g);
  return g.map((v) => v / l);
}
function rgb2hsv([r, g, b]) {
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  let h = 0;
  if (d > 1e-6) { if (mx === r) h = ((g - b) / d) % 6; else if (mx === g) h = (b - r) / d + 2; else h = (r - g) / d + 4; h *= 60; if (h < 0) h += 360; }
  return [h, mx > 0 ? d / mx : 0, mx];
}
function hsv2rgb([h, s, v]) {
  const c = v * s, x = c * (1 - Math.abs(((h / 60) % 2) - 1)), m = v - c;
  const [r, g, b] = h < 60 ? [c, x, 0] : h < 120 ? [x, c, 0] : h < 180 ? [0, c, x] : h < 240 ? [0, x, c] : h < 300 ? [x, 0, c] : [c, 0, x];
  return [r + m, g + m, b + m];
}
const inHue = (h, a, b) => (a <= b ? h >= a && h <= b : h >= a || h <= b);
const hueWeight = (h, a, b, soft) => {
  if (inHue(h, a, b)) {
    const da = Math.min(Math.abs(h - a), 360 - Math.abs(h - a)), db = Math.min(Math.abs(h - b), 360 - Math.abs(h - b));
    return A.smooth(A.clamp(Math.min(da, db) / soft));
  }
  return 0;
};
// A look as numbers (the style bible's table) -> function used to bake a LUT.
//   { lift, gamma, gain, sat, contrast, pivot, curve, temp, tint, blacks, whites,
//     shadows: [r,g,b] tint, highlights: [r,g,b] tint, balance,
//     hue: [{ range: [50, 170], sat: 0.62, shift: -10, soft: 20 }],
//     keep: { range: [335, 25], soft: 15 }  // hue range that keeps its original saturation
//   }
export function gradeFn(p = {}) {
  const lift = p.lift ?? [0, 0, 0], gamma = p.gamma ?? [1, 1, 1], gain = p.gain ?? [1, 1, 1];
  const wb = wbGains(p.temp ?? 0, p.tint ?? 0);
  const sat = p.sat ?? 1, contrast = p.contrast ?? 1, pivot = p.pivot ?? 0.435, curve = p.curve ?? 0;
  const blacks = p.blacks ?? 0, whites = p.whites ?? 1, bal = p.balance ?? 0.5;
  const sh = p.shadows ?? [0, 0, 0], hi = p.highlights ?? [0, 0, 0];
  return (r, g, b) => {
    const orig = [r, g, b];
    let c = [r * wb[0], g * wb[1], b * wb[2]];
    c = c.map((v, i) => v * gain[i]);
    c = c.map((v, i) => v + lift[i] * (1 - v));
    c = c.map((v, i) => Math.pow(Math.max(v, 0), gamma[i]));
    c = c.map((v) => (v - pivot) * contrast + pivot);
    if (curve) c = c.map((v) => { const x = A.clamp(v); return A.lerp(v, x * x * (3 - 2 * x), curve); });
    // per-hue saturation / hue shifts
    if (p.hue) {
      const hsv = rgb2hsv(c.map((v) => A.clamp(v)));
      let sMul = 1, shift = 0;
      for (const hr of p.hue) {
        const w = hueWeight(hsv[0], hr.range[0], hr.range[1], hr.soft ?? 20);
        sMul *= A.lerp(1, hr.sat ?? 1, w); shift += (hr.shift ?? 0) * w;
      }
      const out = hsv2rgb([(hsv[0] + shift + 360) % 360, A.clamp(hsv[1] * sMul), hsv[2]]);
      c = out;
    }
    let l = luma(c);
    let s = sat;
    if (p.keep) { const w = hueWeight(rgb2hsv(orig)[0], p.keep.range[0], p.keep.range[1], p.keep.soft ?? 15); s = A.lerp(sat, 1, w); }
    c = c.map((v) => l + (v - l) * s);
    l = luma(c);
    const ws = 1 - A.smooth(A.clamp(l / bal)), wh = A.smooth(A.clamp((l - bal) / (1 - bal)));
    c = c.map((v, i) => v + sh[i] * ws + hi[i] * wh);
    return c.map((v) => blacks + v * (whites - blacks));
  };
}
export function makeLook(name, params, size = 33) { return makeLUT(name, gradeFn(params), size); }

// ---------------------------------------------------------------- state
let R = null; // render targets
let grainTex, blackTex, idLUT;
const S = { glowW: 0, stats: {} };

export function init(r) {
  renderer = r;
  const q = (d) => [Math.ceil(W / d), Math.ceil(H / d)];
  const pyr = (div) => [div, div * 2, div * 4, div * 8].map((d) => ({ a: rt(...q(d)), b: rt(...q(d)) }));
  R = {
    hdrA: rt(W, H), hdrB: rt(W, H),
    accum: rt(W, H),
    disp: rt(W, H), dispB: rt(W, H),
    bloom: pyr(4), glow: pyr(4), hal: pyr(4).slice(0, 2),
    cocH: rt(...q(2)), dofH: rt(...q(2)), mix: rt(W, H), accum2: rt(W, H),
    glowScene: new THREE.WebGLRenderTarget(...q(2), { type: THREE.HalfFloatType, depthBuffer: true }),
  };
  grainTex = makeGrainTexture();
  blackTex = solidTexture([0, 0, 0, 255]);
  idLUT = identityLUT(2);
  for (const k of ['tB0', 'tB1', 'tB2', 'tB3', 'tG0', 'tG1', 'tG2', 'tG3', 'tH0', 'tH1', 'tDof']) gradeMat.uniforms[k].value = blackTex;
  gradeMat.uniforms.tLutA.value = idLUT.tex; gradeMat.uniforms.tLutB.value = idLUT.tex;
  filmMat.uniforms.tGrain.value = grainTex;
  layerMat.uniforms.tMask.value = blackTex;
}
export const targets = () => R;

// ---------------------------------------------------------------- building blocks
export function copy(src, dst, w = 1) { copyMat.uniforms.tSrc.value = src; copyMat.uniforms.uW.value = w; pass(copyMat, dst); }
export function accumulate(src, dst, w) { accumMat.uniforms.tSrc.value = src; accumMat.uniforms.uW.value = w; renderer.autoClear = false; pass(accumMat, dst); renderer.autoClear = true; }
export function background(target, fx) {
  const bg = Array.isArray(fx.bg) ? fx.bg : [fx.bg, fx.bg];
  setV3(bgMat.uniforms.uTop, lin(bg[0])); setV3(bgMat.uniforms.uBot, lin(bg[1]));
  const p = fx.bgPool;
  if (p && p.amount > 0) { setV3(bgMat.uniforms.uPool, lin(p.color ?? '#20262b').map((v) => v * p.amount)); bgMat.uniforms.uPoolGeo.value.set(p.x ?? 0.5, 1 - (p.y ?? 0.5), p.radius ?? 0.45, 0); }
  else bgMat.uniforms.uPool.value.set(0, 0, 0);
  pass(bgMat, target);
}
export function transitionMix(texA, texB, tr, k, target) {
  const u = mixMat.uniforms;
  u.tA.value = texA; u.tB.value = texB; u.uP.value = k;
  u.uKind.value = { dissolve: 0, wipe: 1, iris: 2, noise: 3, mist: 3, dip: 4 }[tr.kind] ?? 0;
  u.uAngle.value = A.rad(tr.angle ?? 0); u.uFeather.value = tr.feather ?? (tr.kind === 'noise' || tr.kind === 'mist' ? 0.12 : 0.06);
  u.uNoiseScale.value = tr.scale ?? 2.5; u.uSeed.value = tr.seed ?? 3;
  u.uCenter.value.set(tr.center?.[0] ?? 0.5, 1 - (tr.center?.[1] ?? 0.5));
  setV3(u.uDip, lin(tr.color ?? '#000000'));
  pass(mixMat, target);
}

function blurPyramid(levels, srcTex, srcW, srcH, extract, spread = 1) {
  // level 0: extract (threshold) or plain downsample from the source
  const l0 = levels[0];
  if (extract) {
    extractMat.uniforms.tSrc.value = srcTex; extractMat.uniforms.uTexel.value.set(1 / srcW, 1 / srcH);
    extractMat.uniforms.uThreshold.value = extract.threshold; extractMat.uniforms.uKnee.value = extract.knee ?? Math.max(0.05, extract.threshold * 0.25);
    pass(extractMat, l0.a);
  }
  for (let i = 0; i < levels.length; i++) {
    const L = levels[i];
    if (i > 0) { const P = levels[i - 1]; downMat.uniforms.tSrc.value = P.a.texture; downMat.uniforms.uTexel.value.set(1 / P.a.width, 1 / P.a.height); pass(downMat, L.a); }
    const tw = 1 / L.a.width, th = 1 / L.a.height;
    blurMat.uniforms.tSrc.value = L.a.texture; blurMat.uniforms.uDir.value.set(tw * spread, 0); pass(blurMat, L.b);
    blurMat.uniforms.tSrc.value = L.b.texture; blurMat.uniforms.uDir.value.set(0, th * spread); pass(blurMat, L.a);
  }
}
const mipW = (radius, n) => { const f = [1, 0.8, 0.6, 0.4, 0.2]; return f.slice(0, n).map((v) => A.lerp(v, 1.2 - v, radius)); };

// 2D layer composite into `dst` reading `src`; returns the written target.
function drawLayer(L, srcTex, dst, stage) {
  const u = layerMat.uniforms;
  const tex = L.tex?.isTexture ? L.tex : L.tex?.texture ?? L.texture;
  if (!tex) return false;
  const img = tex.image;
  const tw = img?.videoWidth || img?.width || 1, th = img?.videoHeight || img?.height || 1;
  u.tBase.value = srcTex; u.tLayer.value = tex;
  u.uBlend.value = BLENDS[L.blend ?? 'normal'] ?? 0;
  u.uFit.value = FITS[L.fit ?? 'cover'] ?? 0;
  u.uStage.value = stage === 'scene' ? 0 : 1;
  u.uAlphaMode.value = L.alpha === 'luma' ? 1 : L.alpha === 'opaque' ? 2 : 0;
  u.uOpacity.value = L.opacity ?? 1;
  u.uFlipY.value = (tex.flipY || tex.userData?.preFlipped) ? 1 : 0;
  u.uScale.value = L.scale ?? 1;
  u.uRot.value = A.rad(L.rotate ?? 0);
  u.uSrgbDecoded.value = tex.colorSpace === THREE.SRGBColorSpace ? 1 : 0;
  u.uInvert.value = L.invert ? 1 : 0;
  u.uTexSize.value.set(tw, th);
  u.uOffset.value.set(L.offset?.[0] ?? 0, L.offset?.[1] ?? 0);
  const tile = L.tile ?? [tw, th];
  u.uTile.value.set(Array.isArray(tile) ? tile[0] : tile, Array.isArray(tile) ? tile[1] : (tile * th) / tw);
  u.uLevels.value.set(L.levels?.[0] ?? 0, L.levels?.[1] ?? 1);
  setV3(u.uTint, L.tint ? (stage === 'scene' ? lin(L.tint) : srgb(L.tint)) : [1, 1, 1]);
  if (L.mask) {
    const m = L.mask.tex?.isTexture ? L.mask.tex : L.mask.tex?.texture;
    u.uMaskOn.value = 1; u.tMask.value = m;
    u.uMaskChannel.value = L.mask.channel === 'alpha' ? 1 : L.mask.channel === 'r' ? 2 : 0;
    u.uMaskInvert.value = L.mask.invert ? 1 : 0;
    u.uMaskThreshold.value = L.mask.threshold ?? 0.5;
    u.uMaskFeather.value = L.mask.feather ?? (L.mask.threshold !== undefined ? 0.08 : -1);
    u.uMaskFlipY.value = (m.flipY || m.userData?.preFlipped) ? 1 : 0;
  } else { u.uMaskOn.value = 0; u.tMask.value = blackTex; }
  if (L.wipe) { u.uWipeOn.value = 1; u.uWipeP.value = L.wipe.p ?? 1; u.uWipeAngle.value = A.rad(L.wipe.angle ?? 0); u.uWipeFeather.value = L.wipe.feather ?? 0.05; } else u.uWipeOn.value = 0;
  if (L.iris) { u.uIrisOn.value = 1; u.uIris.value.set(L.iris.x ?? 0.5, L.iris.y ?? 0.5, L.iris.p ?? 1); u.uIrisFeather.value = L.iris.feather ?? 0.05; } else u.uIrisOn.value = 0;
  pass(layerMat, dst);
  return true;
}
function drawLayers(list, srcTex, ping, pong, stage) {
  let cur = srcTex, n = 0;
  for (const L of list) {
    if ((L.opacity ?? 1) <= 0.0005) continue;
    const dst = n % 2 === 0 ? ping : pong;
    if (drawLayer(L, cur, dst, stage)) { cur = dst.texture; n++; }
  }
  return cur;
}

// ---------------------------------------------------------------- the frame
// hdrTex: linear HDR world; depthTex/camera for DOF; glowRender(target) draws
// the glow layer (or returns false); domTex: rasterised DOM overlay or null.
export function finish({ hdrTex, depthTex, camera, fx, t, glowRender, domTex }) {
  const g = gradeMat.uniforms, f = filmMat.uniforms;
  // 1. scene-stage layers
  const layers = (fx.layers || []).filter(Boolean);
  const sceneLayers = layers.filter((L) => L.stage === 'scene');
  let hdr = hdrTex;
  if (sceneLayers.length) hdr = drawLayers(sceneLayers, hdrTex, R.hdrA, R.hdrB, 'scene');
  // 2. DOF
  g.uDofOn.value = 0;
  if (fx.dof && depthTex) {
    const d = fx.dof, cm = cocMat.uniforms;
    cm.tSrc.value = hdr; cm.tDepth.value = depthTex; cm.uTexel.value.set(1 / W, 1 / H);
    cm.uNear.value = camera.near; cm.uFar.value = camera.far; cm.uFocus.value = d.focus ?? 10;
    cm.uBlur.value = d.blur ?? 8; cm.uMaxBlur.value = Math.min(24, d.maxBlur ?? 16);
    pass(cocMat, R.cocH);
    gatherMat.uniforms.tSrc.value = R.cocH.texture; gatherMat.uniforms.uMaxBlur.value = cm.uMaxBlur.value;
    pass(gatherMat, R.dofH);
    g.tDof.value = R.dofH.texture; g.uDofOn.value = 1;
  }
  // 3. bloom (global)
  const bl = fx.bloom || {};
  g.uBloom.value = 0;
  if ((bl.amount ?? 0) > 0) {
    blurPyramid(R.bloom, hdr, W, H, { threshold: bl.threshold ?? 1, knee: bl.knee }, 1);
    const w = mipW(bl.radius ?? 0.5, 4);
    g.tB0.value = R.bloom[0].a.texture; g.tB1.value = R.bloom[1].a.texture; g.tB2.value = R.bloom[2].a.texture; g.tB3.value = R.bloom[3].a.texture;
    g.uBloomW.value.set(...w); g.uBloom.value = bl.amount;
  }
  // 4. selective glow
  const gw = fx.glow || {};
  g.uGlow.value = 0;
  if ((gw.amount ?? 0) > 0 && glowRender && glowRender(R.glowScene)) {
    blurPyramid(R.glow, R.glowScene.texture, R.glowScene.width, R.glowScene.height, { threshold: gw.threshold ?? 0.8, knee: gw.knee }, 1);
    const w = mipW(gw.radius ?? 0.55, 4);
    g.tG0.value = R.glow[0].a.texture; g.tG1.value = R.glow[1].a.texture; g.tG2.value = R.glow[2].a.texture; g.tG3.value = R.glow[3].a.texture;
    g.uGlowW.value.set(...w); g.uGlow.value = gw.amount * 1.6;
  }
  // 5. halation
  const ha = fx.halation || {};
  g.uHal.value = 0;
  if ((ha.amount ?? 0) > 0) {
    const spread = (ha.radius ?? 18) / 18;
    blurPyramid(R.hal, hdr, W, H, { threshold: ha.threshold ?? 0.82, knee: 0.08 }, spread);
    g.tH0.value = R.hal[0].a.texture; g.tH1.value = R.hal[1].a.texture;
    g.uHalW.value.set(0.55, 0.45); g.uHal.value = ha.amount * 2.0;
    setV3(g.uHalTint, lin(ha.tint ?? '#FF5A2A'));
  }
  // 6. grade
  g.tScene.value = hdr;
  const lk = fx.leak || {};
  g.uLeak.value = lk.amount ?? 0;
  if (g.uLeak.value > 0) {
    setV3(g.uLeakColor, lin(lk.color ?? '#E3A04A'));
    g.uLeakSide.value = { left: 0, right: 1, top: 2, bottom: 3 }[lk.side ?? 'left'] ?? 0;
    g.uLeakPos.value = lk.pos ?? 0.5; g.uLeakSeed.value = lk.seed ?? 1; g.uLeakWidth.value = lk.width ?? 0.3;
  }
  g.uTime.value = t;
  g.uExposure.value = fx.exposure ?? 0;
  g.uTonemap.value = { none: 0, agx: 1, aces: 2, neutral: 3 }[fx.tonemap ?? 'agx'] ?? 1;
  g.uAgxPunch.value = fx.agxPunch ?? 0;
  const gr = fx.grade || {};
  setV3(g.uWB, wbGains(gr.temp ?? 0, gr.tint ?? 0));
  setV3(g.uLift, gr.lift ?? [0, 0, 0]); setV3(g.uGamma, gr.gamma ?? [1, 1, 1]); setV3(g.uGain, gr.gain ?? [1, 1, 1]);
  g.uContrast.value = gr.contrast ?? 1; g.uPivot.value = gr.pivot ?? 0.435; g.uCurve.value = gr.curve ?? 0;
  g.uSat.value = gr.sat ?? 1; g.uVib.value = gr.vibrance ?? 0;
  g.uBalance.value = gr.balance ?? 0.5; g.uBlacks.value = gr.blacks ?? 0; g.uWhites.value = gr.whites ?? 1;
  const tintVec = (c, amt) => { if (!c || !amt) return [0, 0, 0]; const s = srgb(c); const l = luma(s); return s.map((v) => (v - l) * amt); };
  setV3(g.uShadowTint, tintVec(gr.shadows, gr.shadowsAmount ?? 0.25));
  setV3(g.uHighTint, tintVec(gr.highlights, gr.highlightsAmount ?? 0.25));
  // looks
  let look = fx.look;
  if (typeof look === 'string') look = { a: look };
  g.uLookAmt.value = 0; g.uLookMix.value = 0;
  if (look && look.a && (look.amount ?? 1) > 0) {
    const a = LUTS[look.a], b = look.b ? LUTS[look.b] : null;
    if (!a) throw new Error(`unknown look: ${look.a}`);
    g.tLutA.value = a.tex; g.uLutSizeA.value = a.size;
    if (b && (look.mix ?? 0) > 0) { g.tLutB.value = b.tex; g.uLutSizeB.value = b.size; g.uLookMix.value = look.mix; } else { g.tLutB.value = idLUT.tex; g.uLutSizeB.value = idLUT.size; }
    g.uLookAmt.value = look.amount ?? 1;
  }
  pass(gradeMat, R.disp);
  // 7. display-stage layers + DOM
  const disp = layers.filter((L) => L.stage !== 'scene').map((L, i) => ({ L, z: L.z ?? 0, i }));
  if (domTex && (fx.domOpacity ?? 1) > 0.001) disp.push({ L: { tex: domTex, blend: 'normal', opacity: fx.domOpacity ?? 1, fit: 'stretch' }, z: 100, i: 1e6 });
  disp.sort((a, b) => a.z - b.z || a.i - b.i);
  let image = R.disp.texture;
  if (disp.length) image = drawLayers(disp.map((d) => d.L), R.disp.texture, R.dispB, R.hdrA, 'display');
  // 8. film -> screen
  const frame = Math.floor(t * (fx.grainFps ?? 30) + 1e-4);
  f.tImage.value = image;
  const wt = fx.weaveT ?? t, wv = fx.weave ?? 1;
  f.uWeave.value.set(wv * 0.5 * A.noise1(wt / 1.9, 71), wv * 0.7 * A.noise1(wt / 2.3, 72));
  f.uWeaveRot.value = A.rad(wv * 0.03 * A.noise1(wt / 2.7, 73));
  const sh = fx.shake ?? 0, hz = fx.shakeHz ?? 18;
  f.uShake.value.set(sh * A.noise1(t * hz, 81), sh * A.noise1(t * hz, 82));
  f.uPunch.value = fx.punch ?? 1;
  f.uDistort.value = fx.distort ?? 0;
  f.uZoom.value = fx.zoom ?? 0; f.uZoomC.value.set(fx.zoomC?.[0] ?? 0.5, 1 - (fx.zoomC?.[1] ?? 0.5));
  f.uDir.value.set(fx.dir?.[0] ?? 0, -(fx.dir?.[1] ?? 0));
  f.uCA.value = fx.ca ?? 0;
  f.uVig.value = fx.vignette ?? 0; f.uVigRound.value = fx.vignetteRound ?? 0.35;
  f.uFlicker.value = fx.flicker ?? 0;
  f.uGlitch.value = A.clamp(fx.glitch ?? 0);
  f.uScan.value = Math.max(fx.scanlines ?? 0, (fx.glitch ?? 0) * 0.5);
  f.uFlash.value = fx.flash ?? 0; setV3(f.uFlashColor, srgb(fx.flashColor ?? '#ffffff'));
  f.uFade.value = fx.fade ?? 0; setV3(f.uFadeColor, srgb(fx.fadeColor ?? '#000000'));
  const gn = typeof fx.grain === 'number' ? { amount: fx.grain } : (fx.grain || {});
  f.uGrain.value = gn.amount ?? 0; f.uGrainFloor.value = gn.floor ?? 0.35; f.uGrainChroma.value = gn.chroma ?? 0.2; f.uGrainSize.value = gn.size ?? 1.4;
  f.uGrainOff.value.set(Math.floor(A.hash(frame, 11) * 1024), Math.floor(A.hash(frame, 12) * 1024));
  f.uGrainSwap.value = A.hash(frame, 13) > 0.5 ? 1 : 0;
  // bars: fx.bars 0..1 animates from open frame to fx.barsAspect
  const aspect = fx.barsAspect ?? 2.39, k = A.clamp(fx.bars ?? 0);
  f.uBarsY.value = aspect > W / H ? k * (H - W / aspect) / 2 : 0;
  f.uBarsX.value = aspect < W / H ? k * (W - H * aspect) / 2 : 0;
  setV3(f.uBarsColor, srgb(fx.barsColor ?? '#000000'));
  f.uFrame.value = frame; f.uTime.value = t;
  pass(filmMat, null);
}

export { LUTS, grainTex };
