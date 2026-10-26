// Deterministic animation helpers. Everything is a pure function of time,
// so any frame can be rendered on its own, in any order.

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const invLerp = (a, b, x) => (x - a) / (b - a);
// 0..1 progress of t between a and b.
export const prog = (t, a, b) => clamp((t - a) / (b - a));
export const smooth = (x) => x * x * (3 - 2 * x);
export const smoother = (x) => x * x * x * (x * (x * 6 - 15) + 10);
export const remap = (x, a, b, c, d) => c + (d - c) * clamp((x - a) / (b - a));
export const fract = (x) => x - Math.floor(x);
export const deg = (r) => (r * 180) / Math.PI;
export const rad = (d) => (d * Math.PI) / 180;
export const mix = (a, b, t) => (Array.isArray(a) ? a.map((v, i) => lerp(v, b[i], t)) : lerp(a, b, t));
// Interpolate in log space (altitudes, distances, zoom factors: constant perceived speed).
export const logLerp = (a, b, t) => Math.exp(lerp(Math.log(a), Math.log(b), t));
// Frames -> seconds at the delivery rate.
export const FPS = 30;
export const f = (n, fps = FPS) => n / fps;
// Vertical field of view (degrees) of a full-frame lens of `mm` on a 16:9 crop (20.25 mm tall).
export const fovFromMM = (mm) => (2 * Math.atan(20.25 / 2 / mm) * 180) / Math.PI;

const c1 = 1.70158, c3 = c1 + 1;
export const E = {
  linear: (x) => x,
  inQuad: (x) => x * x,
  outQuad: (x) => 1 - (1 - x) * (1 - x),
  inOutQuad: (x) => (x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2),
  inCubic: (x) => x * x * x,
  outCubic: (x) => 1 - Math.pow(1 - x, 3),
  inOutCubic: (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
  inQuart: (x) => x ** 4,
  outQuart: (x) => 1 - Math.pow(1 - x, 4),
  inOutQuart: (x) => (x < 0.5 ? 8 * x ** 4 : 1 - Math.pow(-2 * x + 2, 4) / 2),
  outQuint: (x) => 1 - Math.pow(1 - x, 5),
  inOutQuint: (x) => (x < 0.5 ? 16 * x ** 5 : 1 - Math.pow(-2 * x + 2, 5) / 2),
  inExpo: (x) => (x === 0 ? 0 : Math.pow(2, 10 * x - 10)),
  outExpo: (x) => (x === 1 ? 1 : 1 - Math.pow(2, -10 * x)),
  inOutExpo: (x) =>
    x === 0 ? 0 : x === 1 ? 1 : x < 0.5 ? Math.pow(2, 20 * x - 10) / 2 : (2 - Math.pow(2, -20 * x + 10)) / 2,
  inSine: (x) => 1 - Math.cos((x * Math.PI) / 2),
  outSine: (x) => Math.sin((x * Math.PI) / 2),
  inOutSine: (x) => -(Math.cos(Math.PI * x) - 1) / 2,
  inCirc: (x) => 1 - Math.sqrt(1 - x * x),
  outCirc: (x) => Math.sqrt(1 - (x - 1) * (x - 1)),
  inBack: (x) => c3 * x * x * x - c1 * x * x,
  outBack: (x) => 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2),
  outElastic: (x) =>
    x === 0 ? 0 : x === 1 ? 1 : Math.pow(2, -10 * x) * Math.sin((x * 10 - 0.75) * ((2 * Math.PI) / 3)) + 1,
  // Style-bible names
  glide: (x) => -(Math.cos(Math.PI * x) - 1) / 2,
  settle: (x) => (x === 1 ? 1 : 1 - Math.pow(2, -10 * x)),
  commit: (x) => x * x * x,
  sweep: (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
};
// CSS cubic-bezier as an easing function (for matching DOM timing curves).
export function bezier(x1, y1, x2, y2) {
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
  const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  const sx = (t) => ((ax * t + bx) * t + cx) * t, sy = (t) => ((ay * t + by) * t + cy) * t;
  const dx = (t) => (3 * ax * t + 2 * bx) * t + cx;
  return (x) => {
    if (x <= 0) return 0; if (x >= 1) return 1;
    let t = x;
    for (let i = 0; i < 8; i++) { const e = sx(t) - x; const d = dx(t); if (Math.abs(e) < 1e-6 || Math.abs(d) < 1e-6) break; t -= e / d; }
    return sy(clamp(t));
  };
}

// Eased progress of t between a and b.
export const ease = (t, a, b, fn = E.outCubic) => fn(prog(t, a, b));

// Keyframes: kf(t, [[t0, v0], [t1, v1, easeFn], ...]). The ease on a key
// shapes the segment arriving at it. Values may be numbers or arrays.
export function kf(t, keys) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    const [t1, v1, fn = E.inOutCubic] = keys[i];
    const [t0, v0] = keys[i - 1];
    if (t <= t1) {
      const p = fn(prog(t, t0, t1));
      if (Array.isArray(v0)) return v0.map((a, j) => lerp(a, v1[j], p));
      return lerp(v0, v1, p);
    }
  }
  return keys[keys.length - 1][1];
}
// Keyframes interpolated in log space (positive values only).
export function kfLog(t, keys) {
  return Math.exp(kf(t, keys.map(([tt, v, fn]) => [tt, Math.log(v), fn])));
}

// Speed ramp (time remap). keys: [[t, speed], ...] piecewise-linear playback
// speed over local time; returns a function lt -> source time (seconds), the
// exact integral of the speed curve. speed 0 = freeze, 1 = real time.
//   const remap = A.speedRamp([[0, 1], [0.27, 1], [0.53, 0.25]]);
export function speedRamp(keys, srcStart = 0) {
  const k = keys.map(([t, s]) => [t, s]);
  const acc = [0];
  for (let i = 1; i < k.length; i++) acc.push(acc[i - 1] + ((k[i][1] + k[i - 1][1]) / 2) * (k[i][0] - k[i - 1][0]));
  return (lt) => {
    if (lt <= k[0][0]) return srcStart + k[0][1] * (lt - k[0][0]);
    for (let i = 1; i < k.length; i++) {
      if (lt <= k[i][0]) {
        const [t0, s0] = k[i - 1], [t1, s1] = k[i];
        const x = lt - t0, a = (s1 - s0) / Math.max(1e-9, t1 - t0);
        return srcStart + acc[i - 1] + s0 * x + 0.5 * a * x * x;
      }
    }
    const [tl, sl] = k[k.length - 1];
    return srcStart + acc[k.length - 1] + sl * (lt - tl);
  };
}

// Underdamped spring step response: 0 before t0, settles to 1.
export function spring(t, t0, { freq = 2.4, damp = 0.42 } = {}) {
  const x = t - t0;
  if (x <= 0) return 0;
  const w = 2 * Math.PI * freq;
  return 1 - Math.exp(-damp * w * x) * Math.cos(w * Math.sqrt(1 - damp * damp) * x);
}

// Smooth 0 -> 1 -> 0 bump centred on `at`, lasting `dur` seconds.
export function pulse(t, at, dur) {
  const x = (t - at) / (dur / 2);
  if (Math.abs(x) >= 1) return 0;
  return 0.5 + 0.5 * Math.cos(x * Math.PI);
}

// Fast attack, exponential release: 0 before at, 1 at at, decays after.
export function hit(t, at, release = 0.25, attack = 0.03) {
  if (t < at - attack) return 0;
  if (t < at) return prog(t, at - attack, at);
  return Math.exp(-(t - at) / release);
}
// Linear decay from 1 at `at` to 0 over `dur` (with an ease), 0 outside.
export function decay(t, at, dur, fn = E.outCubic) {
  if (t < at || t > at + dur) return 0;
  return 1 - fn(prog(t, at, at + dur));
}

// Window: 0 outside [a, b], eased in over fadeIn and out over fadeOut.
export function window(t, a, b, fadeIn = 0.2, fadeOut = 0.2, fn = E.inOutSine) {
  if (t < a || t > b) return 0;
  const i = fadeIn > 0 ? fn(prog(t, a, a + fadeIn)) : 1;
  const o = fadeOut > 0 ? 1 - fn(prog(t, b - fadeOut, b)) : 1;
  return Math.min(i, o);
}
// Square on/off blink: on for `on` s, off for `off` s, starting on at t0.
export const blink = (t, t0, on, off) => (t < t0 ? 1 : ((t - t0) % (on + off)) < on ? 1 : 0);
// Per-item stagger: progress of item i of n, each lasting dur, starts spaced by gap.
export const stagger = (t, t0, i, gap, dur, fn = E.outCubic) => fn(prog(t, t0 + i * gap, t0 + i * gap + dur));

export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Stateless hash in [0, 1).
export function hash(n, seed = 0) {
  const s = Math.sin(n * 127.1 + seed * 311.7 + 74.7) * 43758.5453;
  return s - Math.floor(s);
}
// Smooth value noise in [-1, 1].
export function noise1(x, seed = 0) {
  const i = Math.floor(x), f = x - i;
  const a = hash(i, seed), b = hash(i + 1, seed);
  return (lerp(a, b, smoother(f)) - 0.5) * 2;
}
// Fractal noise, roughly in [-1, 1].
export function fbm1(x, seed = 0, oct = 3) {
  let s = 0, a = 0.5, n = 0;
  for (let i = 0; i < oct; i++) { s += a * noise1(x * (1 << i), seed + i * 13); n += a; a *= 0.5; }
  return s / n;
}
// Handheld "breathing": small smooth rotation offsets in degrees, made of two
// noise octaves (0.25 and 0.5 Hz). Returns { pitch, yaw, roll }.
export function breath(t, amp = 1, seed = 0) {
  const o = (s) => 0.7 * noise1(t * 0.25, seed + s) + 0.3 * noise1(t * 0.5, seed + s + 50);
  return { pitch: 0.12 * amp * o(1), yaw: 0.12 * amp * o(2), roll: 0.06 * amp * o(3) };
}
// Typewriter count: how many of n characters are shown at t (cps chars/second from t0).
export const typed = (t, t0, n, cps = 45) => Math.max(0, Math.min(n, Math.floor((t - t0) * cps + 1e-6)));
