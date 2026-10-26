// Procedural textures (deterministic, seeded). Built once in init; each
// returns a THREE texture. Colour textures are sRGB; masks/noise are linear.
import * as THREE from 'three';
import * as A from './anim.js';
import { canvasTexture } from './media.js';

const cache = new Map();
const memo = (key, fn) => { if (!cache.has(key)) cache.set(key, fn()); return cache.get(key); };
function canvas(w, h = w) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }

// Tileable fractal value noise, Float32Array in [0, 1].
export function fbmField(size = 512, { scale = 4, octaves = 5, seed = 1, gain = 0.5, ridge = false } = {}) {
  const out = new Float32Array(size * size);
  const r = A.rng(seed);
  const perm = new Float32Array(4096);
  for (let i = 0; i < perm.length; i++) perm[i] = r();
  const lat = (x, y, p, o) => perm[((((x % p) + p) % p) * 73 + (((y % p) + p) % p) * 151 + o * 977) & 4095];
  let norm = 0, a = 1;
  for (let o = 0; o < octaves; o++) { norm += a; a *= gain; }
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    let s = 0, amp = 1;
    for (let o = 0; o < octaves; o++) {
      const p = scale << o;
      const fx = (x / size) * p, fy = (y / size) * p;
      const ix = Math.floor(fx), iy = Math.floor(fy), tx = A.smoother(fx - ix), ty = A.smoother(fy - iy);
      const v = A.lerp(A.lerp(lat(ix, iy, p, o), lat(ix + 1, iy, p, o), tx), A.lerp(lat(ix, iy + 1, p, o), lat(ix + 1, iy + 1, p, o), tx), ty);
      s += (ridge ? 1 - Math.abs(v * 2 - 1) : v) * amp;
      amp *= gain;
    }
    out[y * size + x] = s / norm;
  }
  return out;
}
function fieldToCanvas(field, size, map = (v) => [v, v, v, 1]) {
  const c = canvas(size), g = c.getContext('2d');
  const id = g.createImageData(size, size);
  for (let i = 0; i < field.length; i++) { const [r, gg, b, a] = map(field[i], i); id.data[i * 4] = r * 255; id.data[i * 4 + 1] = gg * 255; id.data[i * 4 + 2] = b * 255; id.data[i * 4 + 3] = a * 255; }
  g.putImageData(id, 0, 0);
  return c;
}

// Soft radial blob (white, alpha falloff). Tint with material.color.
export const radial = () => memo('radial', () => {
  const c = canvas(256), g = c.getContext('2d');
  const gr = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.25, 'rgba(255,255,255,0.6)');
  gr.addColorStop(0.6, 'rgba(255,255,255,0.14)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 256, 256);
  return canvasTexture(c, { data: true });
});
// Soft-edged rectangle (shadows, light pools).
export const softRect = (blur = 28) => memo('softRect' + blur, () => {
  const S = 256, c = canvas(S), g = c.getContext('2d');
  g.filter = `blur(${blur}px)`; g.fillStyle = '#fff'; g.fillRect(56, 56, S - 112, S - 112);
  return canvasTexture(c, { data: true });
});
// Tileable fbm noise (linear data, grey). For fog, clouds, ink masks.
export const noise = ({ size = 512, scale = 4, octaves = 5, seed = 1, ridge = false } = {}) => memo(`noise${size}|${scale}|${octaves}|${seed}|${ridge}`, () => {
  const f = fbmField(size, { scale, octaves, seed, ridge });
  return canvasTexture(fieldToCanvas(f, size), { data: true, wrap: true });
});
// Paper with fibres and mottling (sRGB colour). tone: base paper colour.
export const paper = ({ size = 1024, seed = 5, tone = '#efe9dc' } = {}) => memo(`paper${size}|${seed}|${tone}`, () => {
  const f = fbmField(size, { scale: 6, octaves: 6, seed });
  const base = new THREE.Color(tone);
  const c = fieldToCanvas(f, size, (v) => { const k = 0.92 + 0.1 * v; return [Math.min(1, base.r ** (1 / 2.2) * k), Math.min(1, base.g ** (1 / 2.2) * k), Math.min(1, base.b ** (1 / 2.2) * k), 1]; });
  const g = c.getContext('2d'), r = A.rng(seed + 1);
  for (let i = 0; i < size * 6; i++) {
    const x = r() * size, y = r() * size, len = 4 + r() * 22, a = r() * Math.PI;
    g.strokeStyle = r() < 0.5 ? `rgba(120,105,80,${0.05 + r() * 0.08})` : `rgba(255,255,250,${0.06 + r() * 0.1})`;
    g.lineWidth = 0.6 + r() * 0.8;
    g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + Math.cos(a) * len * 0.5 + (r() - 0.5) * 4, y + Math.sin(a) * len * 0.5 + (r() - 0.5) * 4, x + Math.cos(a) * len, y + Math.sin(a) * len); g.stroke();
  }
  return canvasTexture(c, { wrap: true });
});
// Film dust and hair on transparent (sRGB). Use blend 'normal' (dark) or
// 'screen' (light, set light: true). Jitter offset/rotation per frame.
export const dust = ({ w = 1920, h = 1080, seed = 9, count = 60, hairs = 4, light = false } = {}) => memo(`dust${w}|${h}|${seed}|${count}|${hairs}|${light}`, () => {
  const c = canvas(w, h), g = c.getContext('2d'), r = A.rng(seed);
  const col = (a) => (light ? `rgba(242,239,232,${a})` : `rgba(10,11,13,${a})`);
  for (let i = 0; i < count; i++) {
    const x = r() * w, y = r() * h, s = 0.8 + Math.pow(r(), 3) * 5;
    g.fillStyle = col(0.35 + r() * 0.5);
    g.beginPath();
    const n = 7; for (let k = 0; k <= n; k++) { const a = (k / n) * Math.PI * 2, rr = s * (0.6 + r() * 0.6); k ? g.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr) : g.moveTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); }
    g.fill();
  }
  for (let i = 0; i < hairs; i++) {
    let x = r() * w, y = r() * h, a = r() * Math.PI * 2;
    g.strokeStyle = col(0.5 + r() * 0.3); g.lineWidth = 0.7 + r() * 0.8;
    g.beginPath(); g.moveTo(x, y);
    for (let k = 0; k < 24; k++) { a += (r() - 0.5) * 0.6; x += Math.cos(a) * 3; y += Math.sin(a) * 3; g.lineTo(x, y); }
    g.stroke();
  }
  return canvasTexture(c, { mips: false });
});
// Vertical film scratches on transparent (light lines). Animate offset.x per frame.
export const scratches = ({ w = 1920, h = 1080, seed = 4, count = 5 } = {}) => memo(`scratch${w}|${h}|${seed}|${count}`, () => {
  const c = canvas(w, h), g = c.getContext('2d'), r = A.rng(seed);
  for (let i = 0; i < count; i++) {
    let x = r() * w;
    const y0 = r() * h * 0.3, y1 = h - r() * h * 0.3, a = 0.15 + r() * 0.35;
    g.strokeStyle = `rgba(235,232,225,${a})`; g.lineWidth = 0.6 + r() * 1.2;
    g.beginPath(); g.moveTo(x, y0);
    for (let y = y0; y < y1; y += 12) { x += (r() - 0.5) * 0.8; g.lineTo(x, y); }
    g.stroke();
  }
  return canvasTexture(c, { mips: false });
});
// Organic ink / burn mask (linear). Threshold it in a layer mask for ink reveals.
export const ink = ({ size = 1024, seed = 21 } = {}) => memo(`ink${size}|${seed}`, () => {
  const f = fbmField(size, { scale: 3, octaves: 6, seed, gain: 0.55 });
  return canvasTexture(fieldToCanvas(f, size), { data: true, wrap: true });
});
// Warm light-leak plate (sRGB) for an 'add'/'screen' layer.
export const leak = ({ w = 1920, h = 1080, seed = 2, color = '#E3A04A' } = {}) => memo(`leak${w}|${h}|${seed}|${color}`, () => {
  const c = canvas(w, h), g = c.getContext('2d'), r = A.rng(seed);
  g.fillStyle = '#000'; g.fillRect(0, 0, w, h);
  g.globalCompositeOperation = 'lighter';
  const col = new THREE.Color(color);
  const [R, G, B] = [col.r, col.g, col.b].map((v) => Math.round(255 * v ** (1 / 2.2)));
  for (let i = 0; i < 7; i++) {
    const x = -w * 0.1 + r() * w * 0.35, y = r() * h, rad = h * (0.25 + r() * 0.6);
    const gr = g.createRadialGradient(x, y, 0, x, y, rad);
    gr.addColorStop(0, `rgba(255,${Math.round(G * 0.9 + 25)},${Math.round(B * 0.7 + 20)},${0.35 + r() * 0.3})`);
    gr.addColorStop(0.4, `rgba(${R},${G},${B},${0.18 + r() * 0.15})`);
    gr.addColorStop(1, `rgba(${R},${Math.round(G * 0.4)},0,0)`);
    g.fillStyle = gr; g.fillRect(0, 0, w, h);
  }
  return canvasTexture(c, { mips: false });
});
// Linear gradient mask (linear data): white at `from`, black at `to` (0..1 along angle).
export const gradientMask = ({ w = 512, h = 512, angle = 0, from = 0, to = 1 } = {}) => memo(`grad${w}|${h}|${angle}|${from}|${to}`, () => {
  const c = canvas(w, h), g = c.getContext('2d');
  const a = A.rad(angle), cx = w / 2, cy = h / 2, L = Math.hypot(w, h) / 2;
  const gr = g.createLinearGradient(cx - Math.cos(a) * L, cy - Math.sin(a) * L, cx + Math.cos(a) * L, cy + Math.sin(a) * L);
  gr.addColorStop(from, '#fff'); gr.addColorStop(to, '#000');
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  return canvasTexture(c, { data: true, mips: false });
});
// Particle sprite: soft disc (linear alpha).
export const dot = () => memo('dot', () => {
  const c = canvas(64), g = c.getContext('2d');
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.5, 'rgba(255,255,255,0.6)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  return canvasTexture(c, { data: true });
});
// Data URL of a small ink-grain mask for CSS (stamps, typewriter ink).
export const inkCSS = ({ size = 256, seed = 31, density = 0.82 } = {}) => memo(`inkcss${size}|${seed}|${density}`, () => {
  const f = fbmField(size, { scale: 16, octaves: 3, seed, gain: 0.6 });
  const f2 = fbmField(size, { scale: 4, octaves: 3, seed: seed + 7 });
  const r = A.rng(seed);
  const c = fieldToCanvas(f, size, (v, i) => { const k = v * 0.7 + f2[i] * 0.3 + (r() - 0.5) * 0.18; const a = A.smooth(A.clamp((k - (1 - density) * 0.9) / 0.12)); return [0, 0, 0, a]; });
  return c.toDataURL('image/png');
});
