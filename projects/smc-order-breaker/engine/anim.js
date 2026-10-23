// Deterministic animation helpers. Everything is a pure function of time,
// so any frame can be rendered on its own, in any order.

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const invLerp = (a, b, x) => (x - a) / (b - a);
// 0..1 progress of t between a and b.
export const prog = (t, a, b) => clamp((t - a) / (b - a));
export const smooth = (x) => x * x * (3 - 2 * x);

const c1 = 1.70158, c3 = c1 + 1;
export const E = {
  linear: (x) => x,
  inQuad: (x) => x * x,
  outQuad: (x) => 1 - (1 - x) * (1 - x),
  inOutQuad: (x) => (x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2),
  inCubic: (x) => x * x * x,
  outCubic: (x) => 1 - Math.pow(1 - x, 3),
  inOutCubic: (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
  outQuart: (x) => 1 - Math.pow(1 - x, 4),
  inOutQuart: (x) => (x < 0.5 ? 8 * x ** 4 : 1 - Math.pow(-2 * x + 2, 4) / 2),
  outQuint: (x) => 1 - Math.pow(1 - x, 5),
  inExpo: (x) => (x === 0 ? 0 : Math.pow(2, 10 * x - 10)),
  outExpo: (x) => (x === 1 ? 1 : 1 - Math.pow(2, -10 * x)),
  inOutExpo: (x) =>
    x === 0 ? 0 : x === 1 ? 1 : x < 0.5 ? Math.pow(2, 20 * x - 10) / 2 : (2 - Math.pow(2, -20 * x + 10)) / 2,
  inSine: (x) => 1 - Math.cos((x * Math.PI) / 2),
  outSine: (x) => Math.sin((x * Math.PI) / 2),
  inOutSine: (x) => -(Math.cos(Math.PI * x) - 1) / 2,
  inBack: (x) => c3 * x * x * x - c1 * x * x,
  outBack: (x) => 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2),
  outBackSoft: (x) => {
    const s = 1.2, k = s + 1;
    return 1 + k * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2);
  },
  outElastic: (x) =>
    x === 0 ? 0 : x === 1 ? 1 : Math.pow(2, -10 * x) * Math.sin((x * 10 - 0.75) * ((2 * Math.PI) / 3)) + 1,
};

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

// Window: 0 outside [a, b], eased in over fadeIn and out over fadeOut.
export function window(t, a, b, fadeIn = 0.2, fadeOut = 0.2, fn = E.inOutSine) {
  if (t < a || t > b) return 0;
  const i = fadeIn > 0 ? fn(prog(t, a, a + fadeIn)) : 1;
  const o = fadeOut > 0 ? 1 - fn(prog(t, b - fadeOut, b)) : 1;
  return Math.min(i, o);
}

export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function hash(n) {
  const s = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return s - Math.floor(s);
}
// Smooth value noise in [-1, 1].
export function noise1(x, seed = 0) {
  const i = Math.floor(x), f = x - i;
  const a = hash(i + seed * 57.0), b = hash(i + 1 + seed * 57.0);
  return (lerp(a, b, smooth(f)) - 0.5) * 2;
}
