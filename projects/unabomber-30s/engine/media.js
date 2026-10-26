// Image and image-sequence loading. Stills become textures once in init;
// video is a pre-extracted JPEG sequence (render/extract.sh) played
// frame-accurately: a scene asks for the frame for time t during update(),
// the engine awaits flush() before drawing, and a decode-ahead cache keeps
// the next frames ready so sequential rendering never waits on disk.
import * as THREE from 'three';

let maxAniso = 8;
export function setAnisotropy(a) { maxAniso = a; }

// ---------------------------------------------------------------- stills
const bmpCache = new Map();
// ImageBitmap, flipped for WebGL (so texture.flipY stays false), optionally
// downscaled to fit maxSize on its longer side.
export function loadBitmap(url, { maxSize = 8192, data = false, alpha = true } = {}) {
  const key = `${url}|${maxSize}|${data}`;
  if (bmpCache.has(key)) return bmpCache.get(key);
  const p = (async () => {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`image not found: ${url}`);
    const blob = await res.blob();
    const probe = await createImageBitmap(blob);
    const s = Math.min(1, maxSize / Math.max(probe.width, probe.height));
    const opts = { imageOrientation: 'flipY', premultiplyAlpha: 'none', colorSpaceConversion: data ? 'none' : 'default' };
    if (s < 1) Object.assign(opts, { resizeWidth: Math.round(probe.width * s), resizeHeight: Math.round(probe.height * s), resizeQuality: 'high' });
    probe.close();
    return createImageBitmap(blob, opts);
  })();
  bmpCache.set(key, p);
  return p;
}

function bitmapTexture(bmp, { data = false, mips = true, wrap = false } = {}) {
  const t = new THREE.Texture(bmp);
  t.flipY = false; t.userData.preFlipped = true;
  t.colorSpace = data ? THREE.NoColorSpace : THREE.SRGBColorSpace;
  t.generateMipmaps = mips;
  t.minFilter = mips ? THREE.LinearMipmapLinearFilter : THREE.LinearFilter;
  t.magFilter = THREE.LinearFilter;
  t.anisotropy = maxAniso;
  if (wrap) t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.needsUpdate = true;
  return t;
}
const texCache = new Map();
// A colour texture (sRGB) from a URL. opts: { maxSize, data (linear, no colour
// management: masks, normal maps), mips, wrap }.
export function texture(url, opts = {}) {
  const key = url + JSON.stringify(opts);
  if (!texCache.has(key)) texCache.set(key, loadBitmap(url, opts).then((b) => bitmapTexture(b, opts)));
  return texCache.get(key);
}
// Texture from a canvas (procedural images).
export function canvasTexture(canvas, { data = false, wrap = false, mips = true } = {}) {
  const t = new THREE.CanvasTexture(canvas);
  t.colorSpace = data ? THREE.NoColorSpace : THREE.SRGBColorSpace;
  t.anisotropy = maxAniso;
  t.generateMipmaps = mips;
  t.minFilter = mips ? THREE.LinearMipmapLinearFilter : THREE.LinearFilter;
  if (wrap) t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
}

// ---------------------------------------------------------------- sequences
const pending = new Set();
const sources = new Map();

class Sequence {
  constructor(dir, meta) {
    this.dir = dir.replace(/\/$/, '');
    this.meta = meta;
    this.cache = new Map(); // index -> Promise<ImageBitmap>
    this.ahead = 10;
  }
  url(i) { return `${this.dir}/${String(i + 1).padStart(5, '0')}.jpg`; }
  get(i) {
    if (!this.cache.has(i)) {
      this.cache.set(i, fetch(this.url(i)).then((r) => { if (!r.ok) throw new Error(`frame missing: ${this.url(i)}`); return r.blob(); })
        .then((b) => createImageBitmap(b, { imageOrientation: 'flipY', premultiplyAlpha: 'none' })));
    }
    return this.cache.get(i);
  }
  // keep a window around i, decode ahead in the direction of play
  prefetch(i, dir = 1) {
    for (let k = 1; k <= this.ahead; k++) { const j = i + k * dir; if (j >= 0 && j < this.meta.count) this.get(j); }
    for (const [j, p] of this.cache) {
      if (j < i - 6 || j > i + this.ahead + 6) { this.cache.delete(j); p.then((b) => b.close()).catch(() => {}); }
    }
  }
}

export async function openSequence(dir) {
  if (sources.has(dir)) return sources.get(dir);
  const p = (async () => {
    const res = await fetch(`${dir.replace(/\/$/, '')}/meta.json`);
    if (!res.ok) throw new Error(`no meta.json in ${dir} (extract the clip with render/extract.sh)`);
    return new Sequence(dir, await res.json());
  })();
  sources.set(dir, p);
  return p;
}

// A video texture over an image sequence.
//   const v = await media.video({ dir: '/out/frames/crowd', start: 5.6, speed: 1 });
//   v.show(t)   // in update(): global time t -> frame (call every frame)
// Options:
//   start   global time at which source time `in` plays (default 0)
//   in      source time (s) shown at `start` (default 0)
//   speed   playback speed (constant), or
//   remap   (lt) => source seconds; lt = t - start (use A.speedRamp for ramps)
//   freeze  [{ at, dur }]: hold the frame from global time `at` for `dur` s
//   loop    wrap around instead of holding the last frame
export async function video({ dir, start = 0, in: inPoint = 0, speed = 1, remap = null, freeze = [], loop = false, fps } = {}) {
  const seq = await openSequence(dir);
  const m = seq.meta;
  const rate = fps ?? m.fps;
  const tex = new THREE.Texture();
  tex.flipY = false; tex.userData.preFlipped = true;
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.generateMipmaps = false; tex.minFilter = THREE.LinearFilter; tex.magFilter = THREE.LinearFilter;
  tex.anisotropy = maxAniso;
  // placeholder image size for layout until the first frame lands
  tex.image = { width: m.width, height: m.height };
  let shown = -1, wanted = -1, lastIdx = -1;
  const self = {
    texture: tex, meta: m, aspect: m.width / m.height, frame: -1,
    // source time (s) for global time t
    sourceTime(t) {
      let tt = t;
      let held = 0;
      for (const fz of freeze) { if (t >= fz.at + fz.dur) held += fz.dur; else if (t > fz.at) { held += t - fz.at; } }
      tt = t - held;
      const lt = tt - start;
      return inPoint + (remap ? remap(lt) : lt * speed);
    },
    frameAt(t) {
      let i = Math.floor(self.sourceTime(t) * rate + 1e-4);
      if (loop) i = ((i % m.count) + m.count) % m.count;
      return Math.max(0, Math.min(m.count - 1, i));
    },
    // Request the frame for global time t (uploaded before the frame is drawn).
    show(t) { self.setFrame(self.frameAt(t)); },
    setFrame(i) {
      wanted = i; self.frame = i;
      if (i === shown) return;
      pending.add(self);
    },
    async _load() {
      const i = wanted;
      const bmp = await seq.get(i);
      seq.prefetch(i, lastIdx >= 0 && i < lastIdx ? -1 : 1);
      lastIdx = i;
      tex.image = bmp; tex.needsUpdate = true; shown = i;
    },
  };
  return self;
}

// Await every frame requested this frame.
export async function flush() {
  if (!pending.size) return;
  const list = [...pending];
  pending.clear();
  await Promise.all(list.map((v) => v._load()));
}
