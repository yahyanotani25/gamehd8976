// Reusable 3D building blocks. Every object exposes setters that take
// progress values, so scenes stay pure functions of time: call the setters
// every frame with values computed from t.

import { THREE } from './core.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';
import { TTFLoader } from 'three/addons/loaders/TTFLoader.js';
import { SVGLoader } from 'three/addons/loaders/SVGLoader.js';
import { Font } from 'three/addons/loaders/FontLoader.js';
import * as A from './anim.js';

export const PAL = {
  paper: '#ffffff',
  red: '#f5222d', redDeep: '#b80f1c',
  green: '#0bb04a', greenDeep: '#087f35',
  maroon: '#5e0f1a', maroonSide: '#2c0509',
  ink: '#15171c', inkSoft: '#3a3f4a',
  gold: '#ffb21a', goldDeep: '#c27800',
  navy: '#142a57', blue: '#2f6bff',
  zoneGreen: '#12b856', zoneRed: '#ff3340',
};

const col = (c) => (c instanceof THREE.Color ? c.clone() : new THREE.Color(c));

// ---------------------------------------------------------------- materials
export function glossy(color, { rough = 0.3, clearcoat = 1, emissive = 0.14, metal = 0 } = {}) {
  const c = col(color);
  return new THREE.MeshPhysicalMaterial({
    color: c, roughness: rough, metalness: metal, clearcoat, clearcoatRoughness: 0.12,
    emissive: c, emissiveIntensity: emissive, transparent: true, opacity: 1,
  });
}
export function matte(color, { rough = 0.8, emissive = 0 } = {}) {
  const c = col(color);
  return new THREE.MeshStandardMaterial({ color: c, roughness: rough, emissive: c, emissiveIntensity: emissive, transparent: true });
}
function setOpacity(obj, a) {
  obj.traverse((o) => {
    if (!o.material) return;
    for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
      m.opacity = a * (m.userData.baseOpacity ?? 1);
      m.depthWrite = a > 0.98 && m.userData.depthWrite !== false;
    }
  });
  obj.visible = a > 0.001;
}
export { setOpacity };
function shadows(obj, cast = true) { obj.traverse((o) => { if (o.isMesh) { o.castShadow = cast; } }); return obj; }

// ---------------------------------------------------------------- textures
const texCache = {};
// Soft radial blob, white with alpha; tint it with material.color.
export function radialTexture() {
  if (texCache.radial) return texCache.radial;
  const c = document.createElement('canvas'); c.width = c.height = 256;
  const g = c.getContext('2d');
  const gr = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  gr.addColorStop(0, 'rgba(255,255,255,1)');
  gr.addColorStop(0.35, 'rgba(255,255,255,0.55)');
  gr.addColorStop(0.7, 'rgba(255,255,255,0.12)');
  gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 256, 256);
  return (texCache.radial = new THREE.CanvasTexture(c));
}
// Soft-edged rectangle (for coloured light pools on the paper).
export function softRectTexture() {
  if (texCache.softRect) return texCache.softRect;
  const S = 256, c = document.createElement('canvas'); c.width = c.height = S;
  const g = c.getContext('2d');
  g.filter = 'blur(28px)';
  g.fillStyle = '#fff'; g.fillRect(56, 56, S - 112, S - 112);
  return (texCache.softRect = new THREE.CanvasTexture(c));
}
// Diagonal hatch for zones.
export function hatchTexture() {
  if (texCache.hatch) return texCache.hatch;
  const S = 128, c = document.createElement('canvas'); c.width = c.height = S;
  const g = c.getContext('2d');
  g.strokeStyle = 'rgba(255,255,255,1)'; g.lineWidth = 14;
  for (let i = -S; i <= 2 * S; i += 42) { g.beginPath(); g.moveTo(i, S); g.lineTo(i + S, 0); g.stroke(); }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return (texCache.hatch = t);
}

// ---------------------------------------------------------------- glows
// Camera-facing soft light. Normal blending, so it reads on white paper.
export function glow({ color = PAL.green, size = 2, opacity = 0.5 } = {}) {
  const m = new THREE.SpriteMaterial({ map: radialTexture(), color: col(color), transparent: true, opacity, depthWrite: false });
  m.userData.baseOpacity = opacity;
  const s = new THREE.Sprite(m);
  s.scale.set(size, size, 1);
  return s;
}
// Coloured light pool lying on the paper (z just above it).
export function paperGlow({ color = PAL.green, w = 3, h = 3, opacity = 0.35 } = {}) {
  const m = new THREE.MeshBasicMaterial({ map: softRectTexture(), color: col(color), transparent: true, opacity, depthWrite: false });
  m.userData.baseOpacity = opacity; m.userData.depthWrite = false;
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), m);
  mesh.scale.set(w * 1.6, h * 1.6, 1);
  mesh.position.z = 0.006;
  mesh.renderOrder = -1;
  return mesh;
}

// ---------------------------------------------------------------- candles
// One OHLC candle centred at x. The group's origin is the candle's mid
// price so pop-in scaling grows from the centre, like the reference.
export function candle({ o, h, l, c, x = 0, width = 0.62, depth = 0.62, color, z = 0 }) {
  const up = c >= o;
  const base = col(color ?? (up ? PAL.green : PAL.red));
  const top = Math.max(o, c), bot = Math.min(o, c);
  const bh = Math.max(top - bot, 0.08);
  const mid = (h + l) / 2;
  const group = new THREE.Group();
  group.position.set(x, mid, z);
  const mat = glossy(base);
  const wickMat = glossy(base.clone().multiplyScalar(0.92), { emissive: 0.1 });
  const body = new THREE.Mesh(new RoundedBoxGeometry(width, bh, depth, 3, Math.min(0.07, bh / 2 - 0.005)), mat);
  body.position.set(0, (top + bot) / 2 - mid, depth / 2 + 0.02);
  const wick = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, Math.max(h - l, 0.01), 12), wickMat);
  wick.position.set(0, 0, depth / 2 + 0.02);
  group.add(wick, body);
  shadows(group);
  const halo = paperGlow({ color: base, w: width * 2.2, h: h - l + 1.2, opacity: 0 });
  halo.position.set(0, 0, 0.006 - z);
  group.add(halo);
  const self = {
    group, body, wick, mat, wickMat, halo, o, h, l, c, x, top, bot, mid, up, width, depth,
    // p: 0 hidden -> 1 fully formed. 'pop' scales up from the centre with
    // overshoot (reference style); 'grow' forms like a live candle from the
    // open price.
    setAppear(p, mode = 'pop') {
      group.visible = p > 0.0005;
      if (!group.visible) return;
      if (mode === 'grow') {
        const g = A.E.outCubic(A.clamp(p * 1.15));
        const cc = A.lerp(o, c, g);
        const bt = Math.max(o, cc), bb = Math.min(o, cc);
        body.scale.set(1, Math.max(0.02, (bt - bb) / bh), 1);
        body.position.y = (bt + bb) / 2 - mid;
        const wl = A.lerp(Math.min(o, cc), l, g), wh = A.lerp(Math.max(o, cc), h, g);
        wick.scale.set(1, Math.max(0.01, (wh - wl) / Math.max(h - l, 0.01)), 1);
        wick.position.y = (wh + wl) / 2 - mid;
        group.scale.setScalar(A.lerp(0.7, 1, A.E.outBack(A.clamp(p * 1.6))));
      } else {
        body.scale.set(1, 1, 1); body.position.y = (top + bot) / 2 - mid;
        wick.scale.set(1, 1, 1); wick.position.y = 0;
        const s = A.E.outBack(p);
        group.scale.set(s, s, s);
      }
    },
    // 0..1 highlight: brighter and a coloured light pool on the paper.
    setGlow(a) {
      mat.emissiveIntensity = 0.14 + a * 0.45;
      halo.material.opacity = 0.42 * a;
      halo.visible = a > 0.001;
    },
    setOpacity(a) { setOpacity(body, a); setOpacity(wick, a); },
    setColor(c2) { const cc = col(c2); mat.color.copy(cc); mat.emissive.copy(cc); wickMat.color.copy(cc).multiplyScalar(0.92); wickMat.emissive.copy(cc); halo.material.color.copy(cc); },
  };
  self.setGlow(0);
  return self;
}

// A row of candles. data: [{o,h,l,c}] in world units (one unit = one grid
// cell). Candle i sits at x0 + i * step.
export function chart({ data, x0 = 0.5, step = 1, width = 0.62, depth = 0.62 }) {
  const group = new THREE.Group();
  const candles = data.map((d, i) => candle({ ...d, x: x0 + i * step, width, depth }));
  candles.forEach((c) => group.add(c.group));
  return {
    group, candles, data,
    x: (i) => x0 + i * step,
    // times[i]: when candle i starts to appear (undefined = hidden, -1 = already there)
    animate(t, times, { dur = 0.26, mode = 'pop' } = {}) {
      candles.forEach((c, i) => {
        const t0 = times[i];
        if (t0 === undefined || t0 === null) c.setAppear(0, mode);
        else if (t0 < 0) c.setAppear(1, mode);
        else c.setAppear(A.prog(t, t0, t0 + dur), mode);
      });
    },
  };
}

// ---------------------------------------------------------------- zones
// Order-block zone: a translucent glass slab spanning x0..x1, y0..y1 with
// solid top and bottom rails and a hatch fill.
export function zone({ x0, x1, y0, y1, color = PAL.zoneGreen, z = 0, thick = 0.16, fill = 0.2 }) {
  const w = x1 - x0, h = y1 - y0;
  const group = new THREE.Group(); // origin at the zone's left edge, vertical centre
  group.position.set(x0, (y0 + y1) / 2, z);
  const pivot = new THREE.Group(); // flips around the zone's horizontal centre line
  group.add(pivot);
  const inner = new THREE.Group(); // scaled for the left-to-right reveal
  pivot.add(inner);
  const c = col(color);
  const slabMat = new THREE.MeshPhysicalMaterial({ color: c, roughness: 0.2, clearcoat: 1, transparent: true, opacity: fill, emissive: c, emissiveIntensity: 0.25, depthWrite: false, side: THREE.DoubleSide });
  slabMat.userData.baseOpacity = fill; slabMat.userData.depthWrite = false;
  const slab = new THREE.Mesh(new THREE.BoxGeometry(1, h, thick), slabMat);
  slab.geometry.translate(0.5, 0, thick / 2 + 0.01);
  slab.scale.x = w;
  const hatchTex = hatchTexture().clone(); hatchTex.needsUpdate = true;
  hatchTex.repeat.set(w / 1.2, h / 1.2);
  const hatchMat = new THREE.MeshBasicMaterial({ map: hatchTex, color: c, transparent: true, opacity: 0.18, depthWrite: false });
  hatchMat.userData.baseOpacity = 0.18; hatchMat.userData.depthWrite = false;
  const hatch = new THREE.Mesh(new THREE.PlaneGeometry(1, h), hatchMat);
  hatch.geometry.translate(0.5, 0, thick + 0.015);
  hatch.scale.x = w;
  const railMat = glossy(c, { emissive: 0.35, rough: 0.25 });
  const railT = new THREE.Mesh(new RoundedBoxGeometry(1, 0.075, 0.12, 2, 0.03), railMat);
  railT.geometry.translate(0.5, 0, 0);
  const railB = railT.clone();
  railT.position.set(0, h / 2, thick + 0.04); railT.scale.x = w;
  railB.position.set(0, -h / 2, thick + 0.04); railB.scale.x = w;
  const edge = new THREE.Mesh(new RoundedBoxGeometry(0.11, h + 0.075, 0.14, 2, 0.04), railMat);
  edge.position.set(0, 0, thick + 0.04);
  inner.add(slab, hatch, railT, railB, edge);
  shadows(inner);
  slab.castShadow = false; hatch.castShadow = false;
  const pool = paperGlow({ color: c, w, h, opacity: 0.22 });
  pool.position.set(w / 2, 0, 0.006 - z);
  inner.add(pool);
  const self = {
    group, pivot, inner, slabMat, railMat, hatchMat, pool, x0, x1, y0, y1, w, h, color: c,
    // left-to-right growth 0..1
    reveal(p) {
      const e = A.E.outCubic(A.clamp(p));
      group.visible = p > 0.001;
      inner.scale.x = Math.max(0.0001, e);
      edge.scale.x = 1 / Math.max(0.0001, e);
    },
    setColor(c2) {
      const cc = col(c2);
      for (const m of [slabMat, railMat, hatchMat, pool.material]) { m.color.copy(cc); if (m.emissive) m.emissive.copy(cc); }
    },
    // flip around the horizontal centre line, in degrees (180 = upside down)
    flip(deg) { pivot.rotation.x = THREE.MathUtils.degToRad(deg); },
    // 0..1 brightening pulse
    pulse(a) {
      slabMat.opacity = fill * (1 + a * 1.4);
      slabMat.emissiveIntensity = 0.25 + a * 0.6;
      railMat.emissiveIntensity = 0.35 + a * 0.8;
      pool.material.opacity = 0.22 * (1 + a * 1.5);
      inner.scale.y = 1 + a * 0.06;
    },
    setOpacity(a) { setOpacity(inner, a); group.visible = a > 0.001; },
    // world position of a point given in zone-relative fractions (0..1)
    at(fx = 0.5, fy = 0.5, z2 = 0.3) { return new THREE.Vector3(x0 + w * fx, y0 + h * fy, z + z2); },
  };
  return self;
}

// ---------------------------------------------------------------- strokes
// A glossy 3D tube along a polyline, drawn on progressively with setDraw(p).
export function stroke(points, { color = PAL.ink, radius = 0.055, z = 0.25, material, segmentsPerUnit = 6 } = {}) {
  const pts = points.map((p) => (p.isVector3 ? p.clone() : new THREE.Vector3(p[0], p[1], p[2] ?? z)));
  const lens = [0];
  for (let i = 1; i < pts.length; i++) lens.push(lens[i - 1] + pts[i].distanceTo(pts[i - 1]));
  const L = lens[lens.length - 1];
  const mat = material ?? glossy(color, { emissive: 0.12, rough: 0.28 });
  const mesh = new THREE.Mesh(new THREE.BufferGeometry(), mat);
  mesh.castShadow = true;
  const capA = new THREE.Mesh(new THREE.SphereGeometry(radius, 16, 12), mat);
  const capB = capA.clone();
  capA.castShadow = capB.castShadow = true;
  const group = new THREE.Group();
  group.add(mesh, capA, capB);
  let lastP = -1;
  const pointAt = (d) => {
    for (let i = 1; i < pts.length; i++) {
      if (d <= lens[i] || i === pts.length - 1) {
        const f = A.clamp((d - lens[i - 1]) / Math.max(1e-6, lens[i] - lens[i - 1]));
        return { p: pts[i - 1].clone().lerp(pts[i], f), dir: pts[i].clone().sub(pts[i - 1]).normalize() };
      }
    }
  };
  const self = {
    group, mesh, mat, length: L, points: pts, pointAt,
    tip: pts[0].clone(), dir: new THREE.Vector3(1, 0, 0),
    // from/to: 0..1 along the path (to > from)
    setDraw(to, from = 0) {
      to = A.clamp(to); from = A.clamp(from);
      group.visible = to - from > 0.002;
      const key = to * 1000 + from;
      const end = pointAt(to * L), start = pointAt(from * L);
      self.tip.copy(end.p); self.dir.copy(end.dir);
      capA.position.copy(start.p); capB.position.copy(end.p);
      if (!group.visible || key === lastP) return;
      lastP = key;
      const sub = [start.p];
      for (let i = 1; i < pts.length - 1; i++) if (lens[i] > from * L && lens[i] < to * L) sub.push(pts[i]);
      sub.push(end.p);
      const path = new THREE.CurvePath();
      for (let i = 1; i < sub.length; i++) path.add(new THREE.LineCurve3(sub[i - 1], sub[i]));
      const segs = Math.max(2, Math.ceil(((to - from) * L) * segmentsPerUnit) + sub.length * 2);
      mesh.geometry.dispose();
      mesh.geometry = new THREE.TubeGeometry(path, segs, radius, 12, false);
    },
    setOpacity(a) { setOpacity(group, a); },
  };
  self.setDraw(0);
  return self;
}

// Arrow from `from` to `to` ([x,y] or [x,y,z]); setDraw(p) grows it and the
// head rides the tip.
export function arrow(from, to, { color = PAL.green, radius = 0.085, head = 0.5, z = 0.3, bend = 0 } = {}) {
  const a = new THREE.Vector3(from[0], from[1], from[2] ?? z), b = new THREE.Vector3(to[0], to[1], to[2] ?? z);
  const pts = [];
  const n = bend ? 16 : 1;
  const perp = new THREE.Vector3(-(b.y - a.y), b.x - a.x, 0).normalize();
  for (let i = 0; i <= n; i++) {
    const f = i / n;
    const p = a.clone().lerp(b, f).add(perp.clone().multiplyScalar(Math.sin(f * Math.PI) * bend));
    pts.push(p);
  }
  // stop the shaft where the head starts
  const L = pts.reduce((s, p, i) => (i ? s + p.distanceTo(pts[i - 1]) : 0), 0);
  const shaftFrac = Math.max(0.05, 1 - (head * 0.6) / L);
  const mat = glossy(color, { emissive: 0.2, rough: 0.25 });
  const shaft = stroke(pts, { radius, material: mat });
  const headMesh = new THREE.Mesh(new THREE.ConeGeometry(head * 0.52, head, 24), mat);
  headMesh.castShadow = true;
  const group = new THREE.Group();
  group.add(shaft.group, headMesh);
  const self = {
    group, mat, shaft, head: headMesh, from: a, to: b,
    setDraw(p) {
      p = A.clamp(p);
      shaft.setDraw(p * shaftFrac);
      const tip = shaft.pointAt(Math.min(1, p) * L);
      const hs = A.E.outBack(A.prog(p, 0.0, 0.35));
      headMesh.visible = p > 0.01;
      headMesh.scale.setScalar(Math.max(0.0001, hs));
      headMesh.position.copy(tip.p);
      headMesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), tip.dir);
      headMesh.translateY(-head * 0.5 * hs);
      group.visible = p > 0.001;
    },
    setOpacity(x) { setOpacity(group, x); },
  };
  self.setDraw(0);
  return self;
}

// Rounded-rectangle outline drawn on clockwise from the top centre, like
// the reference's highlight box around the key candle.
export function outlineBox({ cx, cy, w, h, r = 0.22, color = PAL.ink, radius = 0.05, z = 0.75 }) {
  const pts = [];
  const hw = w / 2, hh = h / 2;
  const corner = (ox, oy, a0) => { for (let i = 0; i <= 6; i++) { const a = a0 - (i / 6) * (Math.PI / 2); pts.push([ox + Math.cos(a) * r, oy + Math.sin(a) * r, z]); } };
  pts.push([cx, cy + hh, z]);
  corner(cx + hw - r, cy + hh - r, Math.PI / 2);
  corner(cx + hw - r, cy - hh + r, 0);
  corner(cx - hw + r, cy - hh + r, -Math.PI / 2);
  corner(cx - hw + r, cy + hh - r, Math.PI);
  pts.push([cx, cy + hh, z]);
  return stroke(pts, { color, radius });
}

// ---------------------------------------------------------------- text
const fonts = {};
const FONT_FILES = {
  anton: '/node_modules/@fontsource/anton/files/anton-latin-400-normal.woff',
  bebas: '/node_modules/@fontsource/bebas-neue/files/bebas-neue-latin-400-normal.woff',
  montserrat: '/node_modules/@fontsource/montserrat/files/montserrat-latin-900-normal.woff',
  montserrat800: '/node_modules/@fontsource/montserrat/files/montserrat-latin-800-normal.woff',
  oswald: '/node_modules/@fontsource/oswald/files/oswald-latin-700-normal.woff',
};
export async function loadFonts() {
  const loader = new TTFLoader();
  await Promise.all(Object.entries(FONT_FILES).map(async ([k, url]) => {
    const json = await loader.loadAsync(url);
    fonts[k] = new Font(json);
  }));
  return fonts;
}
export { fonts };

const glyphCache = new Map();
const capCache = {};
// Extruded, bevelled 3D text with one mesh per character so letters can be
// animated individually. Origin: centre of the line (align 'center'),
// baseline at y = 0 shifted so the cap height is centred on 0.
export function text3d(str, { font = 'anton', size = 1, depth = 0.22, bevel = 0.025, color = PAL.maroon, side, align = 'center', tracking = 0.02, emissive = 0.08, rough = 0.32 } = {}) {
  const f = fonts[font];
  if (!f) throw new Error(`font not loaded: ${font}`);
  const res = f.data.resolution;
  const group = new THREE.Group();
  const chars = [];
  let x = 0;
  const front = glossy(color, { emissive, rough, clearcoat: 0.8 });
  const sideMat = glossy(side ?? col(color).multiplyScalar(0.45), { emissive: 0.02, rough: 0.5, clearcoat: 0.3 });
  if (!capCache[font]) {
    const hg = new TextGeometry('H', { font: f, size: 1, depth: 0, curveSegments: 2, bevelEnabled: false });
    hg.computeBoundingBox();
    capCache[font] = hg.boundingBox.max.y - hg.boundingBox.min.y;
    hg.dispose();
  }
  const capH = capCache[font] * size;
  for (const ch of str) {
    const g = f.data.glyphs[ch] ?? f.data.glyphs['?'];
    const adv = (g.ha / res) * size;
    if (ch !== ' ') {
      const key = `${font}|${ch}|${size}|${depth}|${bevel}`;
      let geo = glyphCache.get(key);
      if (!geo) {
        geo = new TextGeometry(ch, { font: f, size, depth, curveSegments: 6, bevelEnabled: bevel > 0, bevelThickness: bevel, bevelSize: bevel * 0.55, bevelSegments: 2 });
        geo.translate(-adv / 2, -capH / 2, 0);
        glyphCache.set(key, geo);
      }
      const mesh = new THREE.Mesh(geo, [front.clone(), sideMat.clone()]);
      mesh.castShadow = true;
      const holder = new THREE.Group(); // animate this; centred on the glyph
      holder.add(mesh);
      holder.position.x = x + adv / 2;
      holder.userData.baseX = holder.position.x;
      group.add(holder);
      chars.push({ ch, holder, mesh, x: x + adv / 2, w: adv });
    }
    x += adv + tracking * size;
  }
  const width = x - tracking * size;
  const shift = align === 'center' ? -width / 2 : align === 'right' ? -width : 0;
  for (const c of chars) { c.holder.position.x += shift; c.holder.userData.baseX = c.holder.position.x; c.x += shift; }
  return {
    group, chars, width, capH,
    setOpacity(a) { setOpacity(group, a); },
    setColor(c2, s2) { const cc = col(c2); for (const c of chars) { c.mesh.material[0].color.copy(cc); c.mesh.material[0].emissive.copy(cc); c.mesh.material[1].color.copy(s2 ? col(s2) : cc.clone().multiplyScalar(0.45)); } },
  };
}

// ---------------------------------------------------------------- icons
// Extrude an SVG (fill paths) into a 3D icon centred at the origin, `size`
// world units across its larger side.
export function svgIcon(svg, { size = 1, depth = 0.18, color = PAL.ink, bevel = 0.02 } = {}) {
  const data = new SVGLoader().parse(svg);
  const shapes = data.paths.flatMap((p) => SVGLoader.createShapes(p));
  const flat = new THREE.ShapeGeometry(shapes);
  flat.computeBoundingBox();
  const bb = flat.boundingBox;
  flat.dispose();
  const s = size / Math.max(bb.max.x - bb.min.x, bb.max.y - bb.min.y);
  const geo = new THREE.ExtrudeGeometry(shapes, { depth: depth / s, bevelEnabled: bevel > 0, bevelThickness: bevel / s, bevelSize: (bevel * 0.6) / s, bevelSegments: 2, curveSegments: 10 });
  geo.translate(-(bb.min.x + bb.max.x) / 2, -(bb.min.y + bb.max.y) / 2, 0);
  // SVG y points down: flip y, and z too so the winding stays outward
  geo.scale(s, -s, -s);
  geo.translate(0, 0, depth);
  geo.computeVertexNormals();
  const mesh = new THREE.Mesh(geo, glossy(color, { emissive: 0.12 }));
  mesh.castShadow = true;
  const group = new THREE.Group();
  group.add(mesh);
  return { group, mesh, setOpacity(a) { setOpacity(group, a); } };
}

// ---------------------------------------------------------------- cards
// Rounded white card slab (floats above the paper, casts a soft shadow).
export function card({ w = 8, h = 5, r = 0.45, depth = 0.22, color = '#ffffff' } = {}) {
  const shape = new THREE.Shape();
  const x = -w / 2, y = -h / 2;
  shape.moveTo(x + r, y); shape.lineTo(x + w - r, y); shape.quadraticCurveTo(x + w, y, x + w, y + r);
  shape.lineTo(x + w, y + h - r); shape.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  shape.lineTo(x + r, y + h); shape.quadraticCurveTo(x, y + h, x, y + h - r);
  shape.lineTo(x, y + r); shape.quadraticCurveTo(x, y, x + r, y);
  const geo = new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: true, bevelThickness: 0.05, bevelSize: 0.05, bevelSegments: 3, curveSegments: 12 });
  const mesh = new THREE.Mesh(geo, new THREE.MeshPhysicalMaterial({ color: col(color), roughness: 0.4, clearcoat: 0.6, transparent: true }));
  mesh.castShadow = true;
  const group = new THREE.Group();
  group.add(mesh);
  return { group, mesh, w, h, depth, setOpacity(a) { setOpacity(group, a); } };
}

// ---------------------------------------------------------------- particles
function dotTexture() {
  if (texCache.dot) return texCache.dot;
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d');
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.5, 'rgba(255,255,255,0.6)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  return (texCache.dot = new THREE.CanvasTexture(c));
}
// Floating specks for depth. update(t) drifts them deterministically.
export function dust({ count = 80, w = 20, h = 30, zMin = 1, zMax = 9, size = 0.12, color = '#9aa3b2', opacity = 0.5, seed = 3, cx = 0, cy = 0 } = {}) {
  const r = A.rng(seed);
  const base = [], pos = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) base.push([cx + (r() - 0.5) * w, cy + (r() - 0.5) * h, A.lerp(zMin, zMax, r()), r() * 100]);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const mat = new THREE.PointsMaterial({ map: dotTexture(), color: col(color), size, transparent: true, opacity, depthWrite: false, sizeAttenuation: true });
  mat.userData.baseOpacity = opacity;
  const points = new THREE.Points(geo, mat);
  return {
    group: points, mat,
    update(t) {
      base.forEach(([x, y, z, ph], i) => {
        pos[i * 3] = x + A.noise1(t * 0.35 + ph, 1) * 0.6;
        pos[i * 3 + 1] = y + A.noise1(t * 0.3 + ph, 2) * 0.6 + t * 0.08;
        pos[i * 3 + 2] = z;
      });
      geo.attributes.position.needsUpdate = true;
    },
    setOpacity(a) { mat.opacity = opacity * a; points.visible = a > 0.001; },
  };
}
// One-shot burst of sparks from a point; update(t, t0) where t0 is the burst time.
export function sparks({ count = 40, color = PAL.gold, size = 0.18, speed = 4, life = 0.7, seed = 11, spread = Math.PI * 2, dir = Math.PI / 2 } = {}) {
  const r = A.rng(seed);
  const v = [];
  for (let i = 0; i < count; i++) {
    const a = dir + (r() - 0.5) * spread, s = speed * (0.35 + r() * 0.65);
    v.push([Math.cos(a) * s, Math.sin(a) * s, (r() - 0.2) * s * 0.6, 0.6 + r() * 0.8]);
  }
  const pos = new Float32Array(count * 3);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const mat = new THREE.PointsMaterial({ map: dotTexture(), color: col(color), size, transparent: true, depthWrite: false });
  const points = new THREE.Points(geo, mat);
  return {
    group: points,
    update(t, t0, origin = [0, 0, 0.5]) {
      const x = t - t0;
      points.visible = x > 0 && x < life;
      if (!points.visible) return;
      const k = x / life;
      v.forEach(([vx, vy, vz, sl], i) => {
        const d = (1 - Math.exp(-x * 4)) / 4;
        pos[i * 3] = origin[0] + vx * d * sl;
        pos[i * 3 + 1] = origin[1] + vy * d * sl - 1.2 * x * x;
        pos[i * 3 + 2] = origin[2] + vz * d;
      });
      geo.attributes.position.needsUpdate = true;
      mat.opacity = (1 - k) * (1 - k);
      mat.size = size * (1 - k * 0.5);
    },
  };
}
