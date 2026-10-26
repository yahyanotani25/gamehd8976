// DOM overlay: crisp 2D typography, labels and graphic lines drawn over the
// 3D frame (rasterised into the film pass each frame, see domtex.js). Like
// the 3D side, every element is fully re-specified each frame from t: build
// elements in init, call the helpers' set(...) in update. No CSS transitions
// or animations (they would not be frame-exact).
import * as A from './anim.js';
import { CSSF } from './fonts.js';
import * as TX from './textures.js';

export { CSSF };
const SVGNS = 'http://www.w3.org/2000/svg';

export function css(str) {
  const s = document.createElement('style');
  s.dataset.ov = '1';
  s.textContent = str;
  document.head.appendChild(s);
  return s;
}

export function el(parent, { tag = 'div', cls = '', html = '', text, style = {} } = {}) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text; else if (html) e.innerHTML = html;
  Object.assign(e.style, { position: 'absolute', left: '0px', top: '0px', ...style });
  parent.appendChild(e);
  return e;
}
const svgEl = (tag, attrs = {}, parent) => { const e = document.createElementNS(SVGNS, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); if (parent) parent.appendChild(e); return e; };
// Full-frame SVG layer (for lines, leaders, rings).
export function svg(parent) {
  const s = svgEl('svg', { width: 1920, height: 1080, viewBox: '0 0 1920 1080' });
  Object.assign(s.style, { position: 'absolute', left: '0px', top: '0px', overflow: 'visible' });
  parent.appendChild(s);
  return s;
}

// Position an element by its anchor (ax, ay; 0.5 = centre) at pixel (x, y).
export function place(e, { x = 960, y = 540, ax = 0.5, ay = 0.5, opacity = 1, scale = 1, sx = 1, sy = 1, rot = 0, rx = 0, ry = 0, blur = 0, persp = 0, visible = true } = {}) {
  if (!visible || opacity <= 0.001) { e.style.display = 'none'; return; }
  e.style.display = '';
  const p = persp ? `perspective(${persp}px) ` : '';
  e.style.transform = `translate(${x.toFixed(2)}px, ${y.toFixed(2)}px) translate(${-ax * 100}%, ${-ay * 100}%) ${p}rotateX(${rx}deg) rotateY(${ry}deg) rotate(${rot}deg) scale(${scale * sx}, ${scale * sy})`;
  e.style.transformOrigin = `${ax * 100}% ${ay * 100}%`;
  e.style.opacity = String(Math.min(1, opacity));
  e.style.filter = blur > 0.05 ? `blur(${blur.toFixed(2)}px)` : 'none';
}

// Split text into per-letter (or per-word) inline-block spans.
export function letters(e, text) {
  e.textContent = '';
  return [...text].map((ch) => {
    const s = document.createElement('span');
    s.textContent = ch === ' ' ? ' ' : ch;
    s.style.display = 'inline-block';
    e.appendChild(s);
    return s;
  });
}
export function words(e, text) {
  e.textContent = '';
  const parts = text.split(' ');
  return parts.map((w, i) => {
    const s = document.createElement('span');
    s.textContent = w;
    s.style.display = 'inline-block';
    e.appendChild(s);
    if (i < parts.length - 1) e.appendChild(document.createTextNode(' '));
    return s;
  });
}
// Style an inline span relative to its natural place.
export function nudge(s, { x = 0, y = 0, opacity = 1, scale = 1, rot = 0, blur = 0, sx = 1 } = {}) {
  s.style.transform = `translate(${x.toFixed(2)}px, ${y.toFixed(2)}px) rotate(${rot}deg) scale(${(scale * sx).toFixed(4)}, ${scale.toFixed(4)})`;
  s.style.opacity = String(A.clamp(opacity));
  s.style.filter = blur > 0.05 ? `blur(${blur.toFixed(2)}px)` : 'none';
}

// A styled text element. font: a CSSF key or CSS family; size px; tracking em.
export function text(parent, str, { font = 'plex', size = 26, weight = 500, color = '#F2EFE8', tracking = 0.14, stretch, lineHeight = 1, upper = false, align = 'left', cls = '', style = {} } = {}) {
  return el(parent, {
    cls, text: upper ? str.toUpperCase() : str,
    style: {
      fontFamily: CSSF[font] ?? font, fontSize: `${size}px`, fontWeight: String(weight), color, letterSpacing: `${tracking}em`,
      lineHeight: String(lineHeight), whiteSpace: 'pre', textAlign: align, ...(stretch ? { fontStretch: stretch } : {}), ...style,
    },
  });
}

// ---------------------------------------------------------------- kinetic type
// Per-letter / per-word reveal.
//   const r = ov.reveal(dom, 'NEAR LINCOLN, MONTANA', { by: 'letter', font: 'plex', size: 26 });
//   r.set(t - t0)  (seconds since the reveal starts; negative = hidden)
// from: starting offsets per unit { y, x, opacity, blur, scale, rot } (eased to 0)
// stagger: s between units; dur: s per unit; ease; order: 'forward'|'reverse'|'center'|'random'
// tracking: [fromEm, toEm, dur] animates letter-spacing; out: { at, dur, ...from } exit
export function reveal(parent, str, o = {}) {
  const { by = 'letter', stagger = 1 / 30, dur = 0.5, ease = A.E.outExpo, order = 'forward', seed = 3 } = o;
  const from = { y: 6, x: 0, opacity: 0, blur: 0, scale: 1, rot: 0, ...(o.from || {}) };
  const e = text(parent, '', o);
  const units = by === 'word' ? words(e, o.upper ? str.toUpperCase() : str) : letters(e, o.upper ? str.toUpperCase() : str);
  const n = units.length;
  const r = A.rng(seed);
  const rank = units.map((_, i) => (order === 'reverse' ? n - 1 - i : order === 'center' ? Math.abs(i - (n - 1) / 2) : order === 'random' ? r() * n : i));
  const self = {
    el: e, units,
    // total duration of the in-animation
    get length() { return Math.max(...rank) * stagger + dur; },
    set(lt, { opacity = 1 } = {}) {
      e.style.display = lt < 0 ? 'none' : '';
      if (lt < 0) return;
      if (o.tracking) { const [a, b, d = 1] = o.tracking; e.style.letterSpacing = `${A.lerp(a, b, A.E.outCubic(A.prog(lt, 0, d)))}em`; }
      const out = o.out;
      units.forEach((s, i) => {
        let k = ease(A.prog(lt, rank[i] * stagger, rank[i] * stagger + dur));
        let st = { x: from.x * (1 - k), y: from.y * (1 - k), opacity: A.lerp(from.opacity, 1, k), blur: from.blur * (1 - k), scale: A.lerp(from.scale, 1, k), rot: from.rot * (1 - k) };
        if (out && lt > out.at) {
          const q = (out.ease ?? A.E.inCubic)(A.prog(lt, out.at + rank[i] * (out.stagger ?? 0), out.at + rank[i] * (out.stagger ?? 0) + (out.dur ?? 0.3)));
          st = { x: st.x + (out.x ?? 0) * q, y: st.y + (out.y ?? 0) * q, opacity: st.opacity * (1 - q), blur: st.blur + (out.blur ?? 0) * q, scale: st.scale * A.lerp(1, out.scale ?? 1, q), rot: st.rot };
        }
        st.opacity *= opacity;
        nudge(s, st);
      });
    },
  };
  return self;
}

// Typewriter with a blinking block cursor (style bible: 45 cps, cursor 8 f on /
// 7 f off, hidden 10 f after the last character).
//   const tw = ov.typewriter(dom, 'NO ELECTRICITY · NO RUNNING WATER', { font: 'plex', size: 20 });
//   tw.set(t - t0)
export function typewriter(parent, str, o = {}) {
  const { cps = 45, cursor = '█', cursorColor, blinkOn = 8 / 30, blinkOff = 7 / 30, hideAfter = 10 / 30, cursorScale = 0.82 } = o;
  const e = text(parent, '', o);
  const body = document.createElement('span');
  const cur = document.createElement('span');
  cur.textContent = cursor;
  Object.assign(cur.style, { display: 'inline-block', transform: `scaleY(${cursorScale})`, transformOrigin: '50% 80%', color: cursorColor ?? 'inherit', opacity: '0.8', letterSpacing: '0' });
  e.append(body, cur);
  const full = o.upper ? str.toUpperCase() : str;
  return {
    el: e, cursor: cur,
    duration: full.length / cps,
    set(lt, { opacity = 1 } = {}) {
      if (lt < 0) { e.style.display = 'none'; return; }
      e.style.display = ''; e.style.opacity = String(opacity);
      const n = A.typed(lt, 0, full.length, cps);
      body.textContent = full.slice(0, n);
      const end = full.length / cps;
      const on = lt < end ? 1 : A.blink(lt, end, blinkOn, blinkOff);
      cur.style.visibility = lt > end + hideAfter || !on ? 'hidden' : 'visible';
    },
  };
}

// Mask wipe on any element: p 0 hidden -> 1 shown, along dir, with a soft edge (px).
export function wipe(e, p, { dir = 'right', feather = 40 } = {}) {
  const ang = { right: 90, left: 270, down: 180, up: 0 }[dir] ?? dir;
  if (p >= 1) { e.style.webkitMaskImage = e.style.maskImage = 'none'; return; }
  const span = 100 + (feather / 10);
  const a = A.lerp(-feather / 10, 100, p), b = a + feather / 10;
  const g = `linear-gradient(${ang}deg, #000 ${(a / span) * 100}%, transparent ${(b / span) * 100}%)`;
  e.style.webkitMaskImage = e.style.maskImage = g;
}

// Redaction bar that slides on and off: set(on, off) — the bar covers the span
// [off, on] of its width (0..1). Slide on L->R: on 0->1; slide off L->R: off 0->1.
export function redact(parent, { x = 0, y = 0, w = 300, h = 40, color = '#0A0B0D', under = '#7A0C14', ink = true, rot = 0 } = {}) {
  const box = el(parent, { style: { left: `${x}px`, top: `${y}px`, width: `${w}px`, height: `${h}px`, transform: `rotate(${rot}deg)` } });
  const bar = el(box, { style: { width: '100%', height: '100%', background: color, boxShadow: `0 ${Math.max(1, h * 0.06)}px 0 ${under}` } });
  if (ink) { const m = `url(${TX.inkCSS({ density: 0.97, seed: 12 })})`; bar.style.webkitMaskImage = bar.style.maskImage = m; bar.style.webkitMaskSize = bar.style.maskSize = '256px 256px'; }
  return {
    el: box, bar,
    set(on, off = 0) {
      on = A.clamp(on); off = A.clamp(off);
      box.style.display = on - off > 0.001 ? '' : 'none';
      bar.style.clipPath = `inset(0 ${((1 - on) * 100).toFixed(3)}% 0 ${(off * 100).toFixed(3)}%)`;
    },
  };
}

// Underline / strike-through drawn across a text element (absolute-positioned):
//   const u = ov.rule(textEl, { kind: 'strike', color, thickness }); u.set(p)
export function rule(textEl, { kind = 'underline', color = '#C8102E', thickness = 2, offset = 0.12, from = 'left' } = {}) {
  const top = kind === 'strike' ? `calc(52% - ${thickness / 2}px)` : `calc(100% + ${offset}em)`;
  const r = el(textEl, { style: { left: '0px', top, width: '100%', height: `${thickness}px`, background: color, transformOrigin: from === 'left' ? '0 50%' : '100% 50%' } });
  return { el: r, set(p, off = 0) { r.style.display = p - off > 0.001 ? '' : 'none'; r.style.clipPath = `inset(0 ${((1 - A.clamp(p)) * 100).toFixed(2)}% 0 ${(A.clamp(off) * 100).toFixed(2)}%)`; } };
}

// Rubber stamp that slams in, with an ink texture.
//   const s = ov.stamp(dom, 'UNABOM', { color: '#C8102E', size: 64, rot: -6 }); s.place({x, y}); s.set(t - tHit)
// set() returns the impact (1 on the hit, decaying) to drive fx.shake/punch.
export function stamp(parent, str, { font = 'courier', size = 64, weight = 700, color = '#C8102E', border = 4, rot = -5, pad = '0.12em 0.35em', density = 0.82, seed = 31, from = 1.7, dur = 0.12 } = {}) {
  const e = el(parent, { text: str, style: { fontFamily: CSSF[font] ?? font, fontSize: `${size}px`, fontWeight: String(weight), color, border: `${border}px solid ${color}`, padding: pad, letterSpacing: '0.06em', whiteSpace: 'pre', borderRadius: '4px', lineHeight: '1' } });
  const m = `url(${TX.inkCSS({ density, seed })})`;
  e.style.webkitMaskImage = e.style.maskImage = m;
  e.style.webkitMaskSize = e.style.maskSize = '256px 256px';
  let pos = { x: 960, y: 540 };
  return {
    el: e,
    place(p) { pos = { ...pos, ...p }; },
    set(lt, { opacity = 1 } = {}) {
      if (lt < -dur) { e.style.display = 'none'; return 0; }
      const k = A.E.inQuad(A.prog(lt, -dur, 0));
      place(e, { x: pos.x, y: pos.y, rot, scale: A.lerp(from, 1, k), opacity: opacity * A.lerp(0, 1, A.prog(lt, -dur, -dur * 0.4)), blur: (1 - k) * 6 });
      return A.hit(lt, 0, 0.12, 0.001);
    },
  };
}

// Number counter. roll: true = odometer digits rolling vertically.
//   const c = ov.counter(dom, { from: 0, to: 1996, pad: 4, font: 'plex', size: 40 }); c.set(p)
export function counter(parent, { from = 0, to = 100, decimals = 0, prefix = '', suffix = '', pad = 0, roll = true, sep = '', ...style } = {}) {
  const e = text(parent, '', style);
  const fmt = (v) => { let s = Math.abs(v).toFixed(decimals); if (pad) s = s.padStart(pad + (decimals ? decimals + 1 : 0), '0'); if (sep) s = s.replace(/\B(?=(\d{3})+(?!\d))/g, sep); return (v < 0 ? '-' : '') + s; };
  const len = Math.max(fmt(from).length, fmt(to).length);
  const digits = [];
  if (roll) {
    if (prefix) e.appendChild(document.createTextNode(prefix));
    for (let i = 0; i < len; i++) {
      const box = document.createElement('span');
      Object.assign(box.style, { display: 'inline-block', height: '1em', overflow: 'hidden', verticalAlign: 'top', lineHeight: '1' });
      const col = document.createElement('span');
      Object.assign(col.style, { display: 'inline-block', lineHeight: '1' });
      col.innerHTML = '0<br>1<br>2<br>3<br>4<br>5<br>6<br>7<br>8<br>9<br>0';
      box.appendChild(col); e.appendChild(box);
      digits.push({ box, col });
    }
    if (suffix) e.appendChild(document.createTextNode(suffix));
  }
  return {
    el: e,
    set(p) {
      const v = A.lerp(from, to, A.clamp(p));
      if (!roll) { e.textContent = prefix + fmt(Number(v.toFixed(decimals))) + suffix; return; }
      // each digit place rolls continuously with its share of the value
      const scale = Math.pow(10, decimals);
      const iv = Math.abs(v) * scale;
      for (let i = 0; i < len; i++) {
        const place10 = Math.pow(10, len - 1 - i);
        let d = (iv / place10) % 10;
        const lower = iv % place10;
        // only roll during the last unit of the lower places (odometer feel)
        const frac = place10 > 1 ? A.clamp((lower - (place10 - 1)) / 1) : d - Math.floor(d);
        d = Math.floor(d) + (place10 > 1 ? frac : d - Math.floor(d));
        digits[i].col.style.transform = `translateY(${(-d).toFixed(4)}em)`;
      }
    },
  };
}

// ---------------------------------------------------------------- lines & markers
// Label leader: dot at (x0, y0), line to (x1, y1) (optional elbow), label at the end.
//   const L = ov.leader(dom, { label: 'HELENA · 40 MI' }); L.set({ x0, y0, x1, y1, p, labelP })
export function leader(parent, { label = '', color = '#7FA8B5', width = 1.5, opacity = 0.7, dot = 3, font = 'plex', size = 18, textColor = '#8FA3AE', tracking = 0.12, gap = 10, elbow = 0 } = {}) {
  const s = svg(parent);
  const line = svgEl('polyline', { fill: 'none', stroke: color, 'stroke-width': width, 'stroke-opacity': opacity, 'stroke-linecap': 'square' }, s);
  const c = svgEl('circle', { r: dot, fill: color }, s);
  const lab = label ? text(parent, label, { font, size, color: textColor, tracking }) : null;
  return {
    svg: s, label: lab,
    set({ x0, y0, x1, y1, p = 1, labelP = p >= 1 ? 1 : 0, opacity: op = 1 }) {
      s.style.display = op > 0.001 && p > 0 ? '' : 'none';
      s.style.opacity = String(op);
      const pts = elbow ? [[x0, y0], [x0 + (x1 - x0) * elbow, y1], [x1, y1]] : [[x0, y0], [x1, y1]];
      // draw progress along the polyline
      const L = pts.slice(1).reduce((acc, q, i) => acc + Math.hypot(q[0] - pts[i][0], q[1] - pts[i][1]), 0);
      let rem = L * A.clamp(p);
      const out = [pts[0]];
      for (let i = 1; i < pts.length && rem > 0; i++) {
        const sl = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
        const f = Math.min(1, rem / Math.max(1e-6, sl));
        out.push([A.lerp(pts[i - 1][0], pts[i][0], f), A.lerp(pts[i - 1][1], pts[i][1], f)]);
        rem -= sl;
      }
      line.setAttribute('points', out.map((q) => q.map((v) => v.toFixed(2)).join(',')).join(' '));
      c.setAttribute('cx', x0); c.setAttribute('cy', y0);
      if (lab) {
        const right = x1 >= x0;
        place(lab, { x: x1 + (right ? gap : -gap), y: y1, ax: right ? 0 : 1, ay: 0.5, opacity: op * labelP, blur: (1 - labelP) * 4 });
      }
    },
  };
}
// Architectural dimension line with end ticks and a centred label.
//   const d = ov.dimension(dom, { label: '10 FT' }); d.set({ x0, y0, x1, y1, p, labelP })
export function dimension(parent, { label = '', color = '#F2EFE8', width = 2, opacity = 0.85, tick = 12, font = 'plex', size = 20, tracking = 0.1, offset = 18 } = {}) {
  const s = svg(parent);
  const g = svgEl('g', { stroke: color, 'stroke-width': width, 'stroke-opacity': opacity, 'stroke-linecap': 'butt' }, s);
  const main = svgEl('line', {}, g), t0 = svgEl('line', {}, g), t1 = svgEl('line', {}, g);
  const lab = label ? text(parent, label, { font, size, color, tracking }) : null;
  return {
    svg: s, label: lab,
    set({ x0, y0, x1, y1, p = 1, labelP = p >= 1 ? 1 : 0, opacity: op = 1 }) {
      s.style.display = op > 0.001 && p > 0 ? '' : 'none';
      s.style.opacity = String(op);
      const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, k = A.clamp(p) / 2;
      const ax = A.lerp(cx, x0, k * 2), ay = A.lerp(cy, y0, k * 2), bx = A.lerp(cx, x1, k * 2), by = A.lerp(cy, y1, k * 2);
      const set = (e, a, b, c, d) => { e.setAttribute('x1', a); e.setAttribute('y1', b); e.setAttribute('x2', c); e.setAttribute('y2', d); };
      set(main, ax, ay, bx, by);
      const L = Math.hypot(x1 - x0, y1 - y0) || 1, nx = -(y1 - y0) / L, ny = (x1 - x0) / L; // normal
      const tx = (nx - (x1 - x0) / L) * tick / 2 * 0.7071, ty = (ny - (y1 - y0) / L) * tick / 2 * 0.7071; // 45-degree architectural tick
      const show = p >= 0.999 ? 1 : 0;
      set(t0, x0 - tx * show, y0 - ty * show, x0 + tx * show, y0 + ty * show);
      set(t1, x1 - tx * show, y1 - ty * show, x1 + tx * show, y1 + ty * show);
      if (lab) {
        const ang = Math.atan2(y1 - y0, x1 - x0) * 180 / Math.PI;
        const a2 = ang > 90 || ang < -90 ? ang + 180 : ang;
        place(lab, { x: cx + nx * offset * -1, y: cy + ny * offset * -1, rot: a2, opacity: op * labelP, blur: (1 - labelP) * 3 });
      }
    },
  };
}
// Map pin dot with a thin ring and expanding radius rings (pixel-exact).
//   const m = ov.marker(dom, {}); m.set({ x, y, opacity, pulse: t - t0 })
export function marker(parent, { color = '#C8102E', ring = '#F2EFE8', size = 6, ringWidth = 1, rings = 3, ringColor = '#7FA8B5', ringMax = 220, ringStagger = 0.2, ringDur = 0.8, ringOpacity = 0.6, ringWidth2 = 1.5 } = {}) {
  const s = svg(parent);
  const circles = [];
  for (let i = 0; i < rings; i++) circles.push(svgEl('circle', { fill: 'none', stroke: ringColor, 'stroke-width': ringWidth2 }, s));
  const outer = svgEl('circle', { r: size / 2 + ringWidth, fill: 'none', stroke: ring, 'stroke-width': ringWidth }, s);
  const dot = svgEl('circle', { r: size / 2, fill: color }, s);
  return {
    svg: s,
    set({ x, y, opacity = 1, pulse = null }) {
      s.style.display = opacity > 0.001 ? '' : 'none';
      s.style.opacity = String(opacity);
      for (const e of [outer, dot]) { e.setAttribute('cx', x); e.setAttribute('cy', y); }
      circles.forEach((c, i) => {
        const p = pulse === null ? 0 : A.prog(pulse - i * ringStagger, 0, ringDur);
        c.setAttribute('cx', x); c.setAttribute('cy', y);
        c.setAttribute('r', (A.E.outExpo(p) * ringMax).toFixed(2));
        c.setAttribute('stroke-opacity', (p > 0 && p < 1 ? ringOpacity * (1 - A.E.inQuad(p)) : 0).toFixed(3));
      });
    },
  };
}
// A drawable SVG polyline/path in pixels: set(p) draws it on.
export function path(parent, d, { color = '#F2EFE8', width = 2, opacity = 1, cap = 'round', dash } = {}) {
  const s = svg(parent);
  const pth = svgEl('path', { d, fill: 'none', stroke: color, 'stroke-width': width, 'stroke-opacity': opacity, 'stroke-linecap': cap }, s);
  const L = pth.getTotalLength ? pth.getTotalLength() : 1000;
  return {
    svg: s, path: pth, length: L,
    set(p, { opacity: op = 1 } = {}) {
      s.style.display = p > 0 && op > 0 ? '' : 'none';
      s.style.opacity = String(op);
      pth.setAttribute('stroke-dasharray', dash ?? `${L} ${L}`);
      pth.setAttribute('stroke-dashoffset', String(L * (1 - A.clamp(p))));
    },
  };
}

// Base styles and style-bible type presets (docs/STYLE.md section 7).
css(`
  .scene-layer { position: absolute; inset: 0; pointer-events: none; }
  .t-super { font: 500 26px ${CSSF.plex}; letter-spacing: 0.14em; color: rgba(242,239,232,0.92); white-space: pre; }
  .t-coord { font: 500 20px ${CSSF.plex}; letter-spacing: 0.14em; color: #8FA3AE; white-space: pre; }
  .t-label { font: 500 18px ${CSSF.plex}; letter-spacing: 0.12em; color: #8FA3AE; white-space: pre; }
  .t-meas { font: 500 20px ${CSSF.plex}; letter-spacing: 0.10em; color: #F2EFE8; white-space: pre; }
  .t-facts { font: 500 20px ${CSSF.plex}; letter-spacing: 0.18em; color: rgba(242,239,232,0.9); white-space: pre; }
  .t-type { font: 700 64px ${CSSF.courier}; color: #16171A; white-space: pre; }
  .t-kicker { font: 600 30px ${CSSF.plex}; letter-spacing: 0.5em; color: #C8102E; white-space: pre; }
  .t-title { font: 900 152px ${CSSF.archivoX}; letter-spacing: 0.05em; color: #F2EFE8; white-space: pre; line-height: 1; }
  .t-sub { font: 500 22px ${CSSF.plex}; letter-spacing: 0.32em; color: #8FA3AE; white-space: pre; }
`);
