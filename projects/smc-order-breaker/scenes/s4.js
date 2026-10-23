// Scene s4 — Comparison: Order Block = potential ENTRY vs Breaker Block =
// potential REVERSAL. Two floating white 3D cards stacked vertically, each
// with a coloured header, a mini 3D chart and a big kinetic word + 3D icon.
// See docs/STORYBOARD.md (s4). Pure function of time: every animated
// property is set from t on every update.

// ---- mini chart data (chart units; candle i at x = i + 0.5)
// Top card: downtrend, LAST down candle (#2) = order block, impulse up that
// breaks structure (#4 closes above #0's high), pullback taps the zone (#6),
// reaction up (#7-8).
const OB_DATA = [
  { o: 7.0, h: 7.3, l: 5.8, c: 6.0 },
  { o: 6.0, h: 6.2, l: 4.6, c: 4.8 },
  { o: 4.8, h: 5.0, l: 3.4, c: 3.6 }, // ORDER BLOCK (last red before impulse)
  { o: 3.6, h: 6.4, l: 3.5, c: 6.2 },
  { o: 6.2, h: 8.6, l: 6.0, c: 8.4 }, // breaks structure
  { o: 8.4, h: 8.6, l: 6.8, c: 7.0 },
  { o: 7.0, h: 7.2, l: 4.7, c: 5.3 }, // taps the zone
  { o: 5.3, h: 7.6, l: 5.1, c: 7.4 }, // reaction
  { o: 7.4, h: 9.8, l: 7.2, c: 9.6 },
];
const OB_ZONE = { x0: 2.15, x1: 9.0, y0: 3.4, y1: 5.0 };
// Bottom card: an order block forms (#1) and works once, then FAILS: #6
// closes through it, the zone flips to resistance, #8 retests it from below
// and is rejected (long upper wick), #9-10 drop.
const BB_DATA = [
  { o: 7.6, h: 7.9, l: 6.4, c: 6.6 },
  { o: 6.6, h: 6.9, l: 5.4, c: 5.6 }, // order block
  { o: 5.6, h: 8.2, l: 5.5, c: 8.0 },
  { o: 8.0, h: 9.6, l: 7.8, c: 9.4 }, // breaks structure
  { o: 9.4, h: 9.5, l: 7.6, c: 7.8 },
  { o: 7.8, h: 8.0, l: 6.2, c: 6.4 }, // back into the zone
  { o: 6.4, h: 6.6, l: 3.6, c: 3.9 }, // FAIL: closes through the zone
  { o: 3.9, h: 5.1, l: 3.7, c: 4.9 }, // retrace up
  { o: 5.0, h: 6.3, l: 4.4, c: 4.5 }, // REJECTION: wick into the zone from below
  { o: 4.5, h: 4.7, l: 2.6, c: 2.8 },
  { o: 2.8, h: 3.0, l: 1.2, c: 1.4 },
];
const BB_ZONE = { x0: 1.15, x1: 11.0, y0: 5.4, y1: 6.9 };

// ---- layout (world units; final framing width 13.5 => ~80 px / unit)
const CARD_W = 10.8, CARD_H = 6.2, CARD_D = 0.22, CARD_Z = 0.6;
const TOP_Y = 3.55, BOT_Y = -3.55;      // card centres (gap 0.9 for the VS badge)
const SURF = CARD_D + 0.06;             // card top surface (local z)
const COL_X = 2.85;                     // right column centre (icon + word)

// target icon parts (100x100 viewBox, from ICON3D.target, split so the rings can lock on separately)
const SVG_RING_OUT = '<svg viewBox="0 0 100 100"><path fill-rule="evenodd" d="M50 4a46 46 0 1 1 0 92 46 46 0 1 1 0-92Zm0 11a35 35 0 1 0 0 70 35 35 0 1 0 0-70Z"/></svg>';
const SVG_RING_IN = '<svg viewBox="0 0 100 100"><path fill-rule="evenodd" d="M50 27a23 23 0 1 1 0 46 23 23 0 1 1 0-46Zm0 11a12 12 0 1 0 0 24 12 12 0 1 0 0-24Z"/></svg>';
const SVG_DOT = '<svg viewBox="0 0 100 100"><path d="M50 44a6 6 0 1 1 0 12 6 6 0 1 1 0-12Z"/></svg>';
const SVG_TICKS = '<svg viewBox="0 0 100 100"><path d="M46 0h8v16h-8Z"/><path d="M46 84h8v16h-8Z"/><path d="M0 46h16v8H0Z"/><path d="M84 46h16v8H84Z"/></svg>';

export default {
  id: 's4', start: 18.00, end: 24.90,
  cues: [
    { t: 18.28, sfx: 'swipe' },                          // top card swings in
    { t: 18.58, sfx: 'tick', gain: -6 },                 // header word BLOCK
    { t: 18.50, sfx: 'pop', gain: -10, pitch: 2 },       // mini candles 0-2
    { t: 18.58, sfx: 'pop', gain: -10, pitch: 0 },
    { t: 18.66, sfx: 'pop', gain: -10, pitch: -2 },
    { t: 18.80, sfx: 'swipe', gain: -10 },               // green zone grows
    { t: 18.88, sfx: 'grow', gain: -7 },                 // impulse up
    { t: 18.98, sfx: 'grow', gain: -7, pitch: 2 },
    { t: 19.06, sfx: 'tick', gain: -6 },                 // "POTENTIAL"
    { t: 19.18, sfx: 'pop', gain: -10, pitch: -1 },      // pullback
    { t: 19.28, sfx: 'pop', gain: -10, pitch: -3 },
    { t: 19.42, sfx: 'click', gain: -4 },                // price taps the zone
    { t: 19.50, sfx: 'grow', gain: -7 },                 // reaction up
    { t: 19.60, sfx: 'grow', gain: -7, pitch: 2 },
    { t: 19.62, sfx: 'swipe', gain: -9 },                // green arrow draws up
    { t: 19.74, sfx: 'ding' },                           // ENTRY + target locks on
    { t: 19.80, sfx: 'shimmer', gain: -10 },
    { t: 20.22, sfx: 'blip' },                           // signal rings
    { t: 20.56, sfx: 'blip', gain: -8, pitch: 3 },       // second, softer signal pulse
    { t: 21.38, sfx: 'swipe' },                          // bottom card swings in
    { t: 21.50, sfx: 'pop' },                            // VS badge
    { t: 21.62, sfx: 'pop', gain: -10, pitch: 1 },       // mini candles 0-1
    { t: 21.70, sfx: 'pop', gain: -10, pitch: -1 },
    { t: 21.75, sfx: 'click' },                          // BREAKER BLOCK header
    { t: 21.80, sfx: 'swipe', gain: -10 },               // zone grows
    { t: 21.86, sfx: 'grow', gain: -8 },
    { t: 21.96, sfx: 'grow', gain: -8, pitch: 2 },
    { t: 22.05, sfx: 'pop', gain: -10, pitch: -1 },
    { t: 22.14, sfx: 'pop', gain: -10, pitch: -3 },
    { t: 22.28, sfx: 'crack', gain: -6 },                // candle smashes through the zone
    { t: 22.42, sfx: 'flip', gain: -7 },                 // zone flips to resistance
    { t: 22.62, sfx: 'pop', gain: -10, pitch: 1 },
    { t: 22.68, sfx: 'tick', gain: -6 },                 // "POTENTIAL"
    { t: 22.80, sfx: 'grow', gain: -8 },                 // retest from below
    { t: 22.98, sfx: 'click', gain: -4 },                // rejected
    { t: 23.10, sfx: 'grow', gain: -8, pitch: -3 },
    { t: 23.22, sfx: 'grow', gain: -8, pitch: -5 },
    { t: 23.29, sfx: 'impact' },                         // REVERSAL
    { t: 23.29, sfx: 'flip' },                           // swap icon flips
    { t: 23.33, sfx: 'swipe', gain: -6 },                // red arrow draws down
    { t: 24.02, sfx: 'shimmer', gain: -6 },              // light sweep across both cards
    { t: 24.90, sfx: 'riser', gain: -6 },                // push into the cut
    { t: 24.90, sfx: 'whoosh' },
  ],

  init(ctx) {
    const { THREE, kit, PAL, A, group } = ctx;
    const W = (w, n, fb) => { try { const v = ctx.wt(w, n); return Number.isFinite(v) ? v : fb; } catch { return fb; } };
    this.T = {
      order: W('Order', 2, 18.28), block: W('Block', 4, 18.58), pot1: W('potential', 1, 19.06),
      entry: W('entry', 2, 19.74), signal: W('signal', 1, 20.22), deta: W('deta', 1, 20.56),
      jabke: W('jabke', 1, 21.38), breaker: W('Breaker', 2, 21.75), block2: W('Block', 5, 22.12),
      pot2: W('potential', 2, 22.68), reversal: W('reversal', 1, 23.29), show: W('show', 1, 24.0),
    };
    // guard against a mis-counted nth occurrence
    if (Math.abs(this.T.block - 18.58) > 0.3) this.T.block = 18.58;
    if (Math.abs(this.T.block2 - 22.12) > 0.3) this.T.block2 = 22.12;

    this.sweepItems = []; // { mats, u, base } for the light sweep
    const addSweep = (mats, u, base) => this.sweepItems.push({ mats, u, base });

    const textMats = (tx) => tx.chars.map((c) => c.mesh.material[0]);

    const buildCard = (kind) => {
      const isTop = kind === 'ob';
      const accent = isTop ? PAL.green : PAL.red;
      const deep = isTop ? PAL.greenDeep : PAL.redDeep;
      const uOff = isTop ? 0 : 0.55; // sweep runs diagonally: top card first
      const root = new THREE.Group(); root.position.set(0, isTop ? TOP_Y : BOT_Y, CARD_Z);
      const hinge = new THREE.Group(); hinge.position.x = isTop ? -CARD_W / 2 : CARD_W / 2;
      const body = new THREE.Group(); body.position.x = -hinge.position.x;
      const flt = new THREE.Group();
      root.add(hinge); hinge.add(body); body.add(flt);
      group.add(root);

      const card = kit.card({ w: CARD_W, h: CARD_H, r: 0.42, depth: CARD_D });
      card.mesh.receiveShadow = true;
      flt.add(card.group);

      // coloured header bar
      const hdr = kit.card({ w: CARD_W - 0.7, h: 1.2, r: 0.3, depth: 0.1, color: accent });
      hdr.mesh.material = kit.glossy(accent, { emissive: 0.18, rough: 0.3 });
      hdr.mesh.receiveShadow = true;
      hdr.group.position.set(0, CARD_H / 2 - 0.35 - 0.6, SURF);
      flt.add(hdr.group);
      addSweep([hdr.mesh.material], 0.5 + uOff, 0.18);
      const hText = kit.text3d(isTop ? 'ORDER BLOCK' : 'BREAKER BLOCK', { font: 'bebas', size: 0.95, depth: 0.12, color: '#ffffff', side: deep, tracking: 0.06 });
      hText.group.position.set(0, hdr.group.position.y, SURF + 0.18);
      flt.add(hText.group);
      hText.chars.forEach((c) => addSweep([c.mesh.material[0]], 0.5 + c.x / CARD_W + uOff, 0.08));
      const split = isTop ? 5 : 7; // first char of the 2nd word (ORDER | BREAKER)

      // faint graph grid behind the mini chart
      const gridMat = new THREE.MeshBasicMaterial({ color: '#e7ebf2', transparent: true });
      const gx0 = -5.15, gx1 = 0.55, gy0 = -2.75, gy1 = 1.3;
      for (let y = gy0; y <= gy1 + 1e-6; y += 0.58) {
        const m = new THREE.Mesh(new THREE.PlaneGeometry(gx1 - gx0, 0.025), gridMat);
        m.position.set((gx0 + gx1) / 2, y, SURF + 0.002); flt.add(m);
      }
      for (let x = gx0; x <= gx1 + 1e-6; x += 0.58) {
        const m = new THREE.Mesh(new THREE.PlaneGeometry(0.025, gy1 - gy0), gridMat);
        m.position.set(x, (gy0 + gy1) / 2, SURF + 0.002); flt.add(m);
      }

      // mini chart
      const data = isTop ? OB_DATA : BB_DATA;
      const zd = isTop ? OB_ZONE : BB_ZONE;
      const s = isTop ? 0.58 : 0.46;
      const ymin = isTop ? 3.2 : 1.2;
      const chartG = new THREE.Group();
      chartG.scale.setScalar(s);
      chartG.position.set(-5.0, -2.65 - ymin * s, SURF + 0.01);
      flt.add(chartG);
      const ch = kit.chart({ data, x0: 0.5, step: 1 });
      chartG.add(ch.group);
      const zone = kit.zone({ ...zd, color: PAL.zoneGreen, fill: 0.34 });
      zone.hatchMat.opacity = 0.34;
      chartG.add(zone.group);
      const arrow = isTop
        ? kit.arrow([8.25, 3.9], [9.95, 7.5], { color: PAL.green, radius: 0.13, head: 0.75 })
        : kit.arrow([9.0, 6.5], [10.95, 3.35], { color: PAL.red, radius: 0.13, head: 0.75 });
      chartG.add(arrow.group);
      // tap marker on the zone (where price reacts)
      const tapPos = isTop ? [6.5, 4.75] : [8.5, 6.2];
      const tapRing = new THREE.Mesh(new THREE.RingGeometry(0.42, 0.56, 48), new THREE.MeshBasicMaterial({ color: accent, transparent: true, depthWrite: false }));
      tapRing.position.set(tapPos[0], tapPos[1], 0.9);
      chartG.add(tapRing);
      const tapGlow = kit.glow({ color: accent, size: 2.2, opacity: 0.6 });
      tapGlow.position.set(tapPos[0], tapPos[1], 0.8);
      chartG.add(tapGlow);

      // right column: icon, kicker, big word
      const iconG = new THREE.Group(); iconG.position.set(COL_X, 0.32, SURF + 0.02);
      flt.add(iconG);
      const iconShadowPad = kit.paperGlow({ color: accent, w: 1.5, h: 1.5, opacity: 0.3 });
      iconShadowPad.position.set(COL_X, 0.32, SURF + 0.004);
      flt.add(iconShadowPad);
      let icon;
      const ICS = 1.95;
      if (isTop) {
        const mk = (svg, frac, color, d) => { const ic = kit.svgIcon(svg, { size: ICS * frac, depth: d, color }); const h = new THREE.Group(); h.add(ic.group); iconG.add(h); return { ic, h }; };
        icon = {
          out: mk(SVG_RING_OUT, 92 / 100, PAL.green, 0.2),
          inn: mk(SVG_RING_IN, 46 / 100, PAL.green, 0.28),
          dot: mk(SVG_DOT, 12 / 100, PAL.ink, 0.36),
          ticks: mk(SVG_TICKS, 1.0, PAL.ink, 0.16),
        };
        for (const k of ['out', 'inn', 'dot', 'ticks']) addSweep([icon[k].ic.mesh.material], 0.5 + COL_X / CARD_W + uOff, 0.12);
      } else {
        const ic = kit.svgIcon(ctx.ov.ICON3D.swap, { size: ICS * 0.92, depth: 0.3, color: PAL.red });
        const h = new THREE.Group(); h.add(ic.group); iconG.add(h);
        icon = { swap: { ic, h } };
        addSweep([ic.mesh.material], 0.5 + COL_X / CARD_W + uOff, 0.12);
      }
      const kick = kit.text3d('POTENTIAL', { font: 'montserrat800', size: 0.34, depth: 0.05, bevel: 0.008, color: PAL.inkSoft, tracking: 0.16 });
      kick.group.position.set(COL_X, -1.08, SURF + 0.02);
      flt.add(kick.group);
      const word = kit.text3d(isTop ? 'ENTRY' : 'REVERSAL', { font: 'bebas', size: 1, depth: 0.28, color: accent, side: deep, tracking: 0.03 });
      const ws = Math.min(4.1 / word.width, 1.02 / word.capH);
      word.group.scale.setScalar(ws);
      word.group.position.set(COL_X, -2.02, SURF + 0.02);
      flt.add(word.group);
      word.chars.forEach((c) => addSweep([c.mesh.material[0]], 0.5 + (COL_X + c.x * ws) / CARD_W + uOff, 0.08));
      kick.chars.forEach((c) => addSweep([c.mesh.material[0]], 0.5 + (COL_X + c.x) / CARD_W + uOff, 0.08));

      // signal rings (top) / sparks
      const rings = [];
      if (isTop) {
        for (let i = 0; i < 3; i++) {
          const m = new THREE.Mesh(new THREE.TorusGeometry(1.0, 0.045, 10, 72), kit.glossy(PAL.green, { emissive: 0.5 }));
          m.position.set(COL_X, 0.32, SURF + 0.12);
          flt.add(m); rings.push(m);
        }
      }
      const sparks = kit.sparks({ count: 34, color: isTop ? PAL.green : PAL.red, size: 0.2, speed: 4.2, life: 0.75, seed: isTop ? 41 : 43 });
      flt.add(sparks.group);
      const pool = kit.paperGlow({ color: accent, w: CARD_W * 0.9, h: CARD_H * 0.8, opacity: 0.16 });
      pool.position.set(0, root.position.y, 0.006);
      group.add(pool);

      return { isTop, root, hinge, body, flt, card, hdr, hText, split, ch, zone, arrow, tapRing, tapGlow, iconG, iconShadowPad, icon, kick, word, rings, sparks, pool };
    };

    this.top = buildCard('ob');
    this.bot = buildCard('bb');

    // VS badge between the cards
    const vs = new THREE.Group(); vs.position.set(0, 0, 1.25);
    const spin = new THREE.Group(); vs.add(spin);
    const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.72, 0.72, 0.26, 56), kit.glossy(PAL.ink, { emissive: 0.05, rough: 0.25 }));
    disc.rotation.x = Math.PI / 2; disc.castShadow = true;
    const rim = new THREE.Mesh(new THREE.TorusGeometry(0.72, 0.07, 14, 64), kit.glossy(PAL.gold, { emissive: 0.3, rough: 0.2, metal: 0.3 }));
    rim.castShadow = true;
    const vsText = kit.text3d('VS', { font: 'bebas', size: 0.78, depth: 0.1, color: '#ffffff', side: PAL.gold, tracking: 0.04 });
    vsText.group.position.z = 0.14;
    spin.add(disc, rim, vsText.group);
    group.add(vs);
    this.vs = { vs, spin, disc, rim, vsText };
    addSweep([rim.material], 0.95, 0.3);

    // a real moving light for the 24.0 sweep (specular glints on the gloss)
    this.sweepLight = new THREE.PointLight('#ffffff', 0, 30, 1.6);
    group.add(this.sweepLight);

    this.dust = kit.dust({ count: 46, w: 16, h: 26, zMin: 2.5, zMax: 12, size: 0.13, opacity: 0.35, seed: 404, cy: 0 });
    group.add(this.dust.group);
  },

  update(t, lt, ctx) {
    const { A, cam, fx, THREE } = ctx;
    const E = A.E, T = this.T;
    const D2R = Math.PI / 180;

    // ------------------------------------------------------------ camera
    const tr = A.ease(t, 21.18, 21.78, E.inOutCubic);          // phase 1 (top card) -> both cards
    const cy0 = 1.68, cy1 = -1.25;
    let cy = A.lerp(cy0, cy1, tr);
    let width = A.lerp(12.6, 13.5, tr);
    const arrive = A.ease(t, 18.0, 18.45, E.outExpo);         // pull back out of the cut
    let dolly = A.lerp(0.74, 1.0, arrive);
    dolly *= A.kf(t, [[18.45, 1.0], [21.18, 0.968, E.inOutSine], [21.78, 1.0, E.inOutCubic], [24.0, 0.975, E.inOutSine], [24.62, 1.025, E.inOutCubic], [24.9, 0.84, E.inCubic]]);
    dolly *= 1 - 0.012 * A.hit(t, T.entry, 0.25) - 0.018 * A.hit(t, T.reversal, 0.3);
    let pitch = A.lerp(-13, -6, arrive) + A.kf(t, [[18.45, 0], [24.0, 0], [24.62, -3.5, E.inOutCubic], [24.9, -2]]);
    pitch += A.noise1(t * 0.35, 21) * 1.2;
    const yaw = A.noise1(t * 0.3, 22) * 2.2 + A.kf(t, [[18.0, -4], [18.5, 0, E.outCubic], [24.0, 0], [24.62, 2.5, E.inOutCubic]]);
    const roll = A.noise1(t * 0.27, 23) * 0.45 + A.lerp(1.5, 0, arrive);
    const cx = A.noise1(t * 0.3, 24) * 0.12;
    cy += A.noise1(t * 0.28, 25) * 0.1;
    cam.frame({ cx, cy, width, pitch, yaw, roll, dolly });

    // ------------------------------------------------------------ cards
    const cardIn = (c, t0, dir) => {
      const e = A.spring(t, t0, { freq: 1.45, damp: 0.6 });
      const vis = t >= t0;
      c.root.visible = vis;
      c.pool.visible = vis;
      if (!vis) return;
      // dir = sign of the hinge angle that lifts the free edge towards the camera;
      // keep the overshoot small so the free edge never dips into the paper
      let ang = dir * 88 * (1 - e);
      if (dir < 0) ang = Math.min(ang, 2.2); else ang = Math.max(ang, -2.2);
      c.hinge.rotation.y = ang * D2R;
      const settle = A.clamp(e);
      c.root.position.z = CARD_Z + 0.9 * (1 - settle);
      // float
      const ph = c.isTop ? 0 : 2.1;
      c.flt.position.z = 0.07 * Math.sin(t * 1.4 + ph);
      c.flt.rotation.x = (0.9 * A.noise1(t * 0.4 + ph, 31)) * D2R;
      c.flt.rotation.y = (0.9 * A.noise1(t * 0.4 + ph, 32)) * D2R;
      c.pool.material.opacity = 0.16 * A.ease(t, t0 + 0.2, t0 + 0.7);
    };
    // top card hinges from its left edge, bottom card from its right edge
    cardIn(this.top, T.order - 0.02, -1);
    cardIn(this.bot, T.jabke - 0.02, 1);

    // header letters: word 1 with its spoken word, word 2 with "Block"
    const headerIn = (c, t1, t2) => {
      c.hText.chars.forEach((ch, i) => {
        const t0 = (i < c.split ? t1 + i * 0.03 : t2 + (i - c.split) * 0.03);
        const p = A.prog(t, t0, t0 + 0.22);
        const e = E.outBack(p);
        ch.holder.position.y = -0.3 * (1 - E.outCubic(p));
        ch.holder.position.z = 0.5 * (1 - E.outCubic(p));
        ch.holder.scale.setScalar(Math.max(1e-4, A.lerp(1.35, 1, E.outCubic(p))));
        ch.holder.rotation.x = (1 - e) * 0.6;
        const a = A.clamp(p * 1.6);
        for (const m of ch.mesh.material) { m.opacity = a; m.depthWrite = a > 0.98; }
        ch.holder.visible = a > 0.001;
      });
    };
    headerIn(this.top, T.order + 0.06, T.block);
    headerIn(this.bot, T.breaker, T.block2);

    // ------------------------------------------------------------ top card content
    {
      const c = this.top;
      const tt = [18.50, 18.58, 18.66, 18.86, 18.96, 19.16, 19.26, 19.48, 19.58];
      const modes = ['pop', 'pop', 'pop', 'grow', 'grow', 'pop', 'grow', 'grow', 'grow'];
      c.ch.candles.forEach((cd, i) => {
        const dur = modes[i] === 'grow' ? 0.2 : 0.24;
        cd.setAppear(A.prog(t, tt[i], tt[i] + dur), modes[i]);
      });
      c.ch.candles[2].setGlow(0.9 * A.window(t, 18.72, 19.2, 0.08, 0.3) + 0.35 * A.window(t, 19.74, 24.9, 0.2, 0.1));
      c.zone.reveal(A.prog(t, 18.78, 19.12));
      const tap = A.hit(t, 19.40, 0.3);
      const sig = A.hit(t, T.signal, 0.35) + 0.6 * A.hit(t, T.deta, 0.3);
      c.zone.pulse(Math.min(1, tap + 0.5 * A.hit(t, T.entry, 0.4) + 0.5 * sig + 0.25 * A.window(t, 24.0, 24.7, 0.2, 0.3)));
      c.arrow.setDraw(A.ease(t, 19.6, 19.98, E.outCubic));
      // tap marker
      const tp = A.prog(t, T.entry - 0.02, T.entry + 0.5);
      c.tapRing.visible = tp > 0 && tp < 1;
      c.tapRing.scale.setScalar(A.lerp(0.5, 2.0, E.outCubic(tp)));
      c.tapRing.material.opacity = (1 - tp) * 0.9;
      c.tapGlow.material.opacity = 0.55 * (A.hit(t, 19.40, 0.35) + 0.8 * A.hit(t, T.entry, 0.5));
      c.tapGlow.visible = c.tapGlow.material.opacity > 0.005;

      // target: scanning ring from "potential", locks on at "entry"
      const I = c.icon;
      const scan = A.ease(t, T.pot1 + 0.08, T.pot1 + 0.4);
      const lock = A.prog(t, T.entry, T.entry + 0.3);
      const outS = A.lerp(A.lerp(1.9, 1.45, scan), 1, E.outBack(lock));
      I.out.h.scale.setScalar(Math.max(1e-4, outS * (0.0001 + scan)));
      I.out.h.rotation.z = A.lerp(-1.2 + (t - T.pot1) * 0.9, 0, E.outBack(lock)) * (lock < 1 ? 1 : 0);
      I.out.h.position.x = (1 - E.outCubic(lock)) * 0.25 * Math.sin((t - T.pot1) * 5.5);
      I.out.h.position.y = (1 - E.outCubic(lock)) * 0.18 * Math.cos((t - T.pot1) * 4.3);
      kit_op(I.out.ic, A.lerp(0, A.lerp(0.45, 1, E.outCubic(lock)), scan));
      const li = A.prog(t, T.entry + 0.06, T.entry + 0.3);
      I.inn.h.scale.setScalar(Math.max(1e-4, E.outBack(li)));
      kit_op(I.inn.ic, A.clamp(li * 3));
      const ld = A.prog(t, T.entry + 0.12, T.entry + 0.34);
      I.dot.h.scale.setScalar(Math.max(1e-4, E.outBack(ld) * (1 + 0.25 * A.hit(t, T.signal, 0.2))));
      kit_op(I.dot.ic, A.clamp(ld * 3));
      const lt2 = A.prog(t, T.entry + 0.02, T.entry + 0.28);
      I.ticks.h.scale.setScalar(Math.max(1e-4, A.lerp(1.7, 1, E.outExpo(lt2))));
      I.ticks.h.rotation.z = A.lerp(0.8, 0, E.outExpo(lt2));
      kit_op(I.ticks.ic, A.clamp(lt2 * 2.5));
      // whole icon: gentle 3D tilt, kick on lock and signal
      const kick = A.hit(t, T.entry + 0.05, 0.25) + 0.6 * A.hit(t, T.signal, 0.25);
      c.iconG.rotation.y = 0.25 * Math.sin(t * 1.1) * A.ease(t, T.entry + 0.3, T.entry + 1.0);
      c.iconG.rotation.x = -0.12 * Math.sin(t * 0.9 + 1);
      c.iconG.position.z = SURF + 0.02 + 0.25 * kick + 0.1 * A.window(t, T.entry, 24.9, 0.3, 0.1);
      c.iconShadowPad.material.opacity = 0.3 * scan * (0.6 + 0.6 * A.hit(t, T.entry, 0.5) + 0.4 * A.hit(t, T.signal, 0.5));
      c.iconShadowPad.visible = scan > 0.01;

      // signal rings
      c.rings.forEach((r, i) => {
        const r0 = T.signal + i * 0.13;
        const r1 = T.deta + (i - 1) * 0.12;
        const k1 = A.prog(t, r0, r0 + 0.75), k2 = i < 2 ? A.prog(t, r1, r1 + 0.7) : 0;
        const k = k1 > 0 && k1 < 1 ? k1 : k2;
        const on = (k1 > 0 && k1 < 1) || (k2 > 0 && k2 < 1);
        r.visible = on;
        if (!on) return;
        r.scale.setScalar(A.lerp(0.95, 2.05, E.outCubic(k)));
        const a = (1 - E.inQuad(k)) * (k1 > 0 && k1 < 1 ? 0.95 : 0.6);
        r.material.opacity = a; r.material.depthWrite = false;
      });
      c.sparks.update(t, T.entry + 0.04, [COL_X, 0.32, SURF + 0.6]);

      kickerIn(c.kick, t, T.pot1, A, E);
      wordIn(c.word, t, T.entry, A, E);
    }

    // ------------------------------------------------------------ bottom card content
    {
      const c = this.bot;
      const tt = [21.60, 21.68, 21.84, 21.94, 22.04, 22.12, 22.26, 22.60, 22.78, 23.08, 23.20];
      const modes = ['pop', 'pop', 'grow', 'grow', 'pop', 'pop', 'grow', 'pop', 'grow', 'grow', 'grow'];
      c.ch.candles.forEach((cd, i) => {
        const dur = i === 6 ? 0.16 : modes[i] === 'grow' ? 0.2 : 0.24;
        cd.setAppear(A.prog(t, tt[i], tt[i] + dur), modes[i]);
      });
      c.ch.candles[1].setGlow(0.7 * A.window(t, 21.78, 22.26, 0.08, 0.1));
      c.ch.candles[6].setGlow(0.9 * A.hit(t, 22.3, 0.4));
      c.ch.candles[8].setGlow(0.9 * A.hit(t, 22.98, 0.5));
      c.zone.reveal(A.prog(t, 21.78, 22.08));
      // fail -> drain -> flip to red (support becomes resistance)
      const fl = A.ease(t, 22.38, 22.72, E.inOutCubic);
      const flipDeg = 180 * fl + 8 * Math.sin(Math.PI * A.prog(t, 22.72, 22.95)) * (t < 22.95 ? 1 : 0);
      c.zone.flip(flipDeg);
      const crack = A.hit(t, 22.3, 0.12);
      const g = new THREE.Color(ctx.PAL.zoneGreen), r = new THREE.Color(ctx.PAL.zoneRed), grey = new THREE.Color('#9aa1ad');
      const drain = A.ease(t, 22.3, 22.42);
      const colr = fl < 0.5 ? g.clone().lerp(grey, drain) : grey.clone().lerp(r, A.prog(fl, 0.5, 0.8));
      c.zone.setColor(colr);
      c.zone.group.position.x = BB_ZONE.x0 + 0.12 * Math.sin(t * 90) * crack;
      // lift the slab while it flips so it never sinks into the card, and
      // keep the flipped (upside-down) slab above the card surface
      const zh = (BB_ZONE.y1 - BB_ZONE.y0) / 2;
      c.zone.group.position.z = (zh + 0.1) * Math.sin(Math.PI * fl) + 0.24 * fl;
      c.zone.pulse(Math.min(1, 0.8 * crack + A.hit(t, 22.98, 0.35) + 0.6 * A.hit(t, T.reversal, 0.4) + 0.25 * A.window(t, 24.0, 24.7, 0.2, 0.3)));
      c.arrow.setDraw(A.ease(t, T.reversal + 0.02, T.reversal + 0.42, E.outCubic));
      const tp = A.prog(t, 22.98, 23.45);
      c.tapRing.visible = tp > 0 && tp < 1;
      c.tapRing.scale.setScalar(A.lerp(0.5, 2.0, E.outCubic(tp)));
      c.tapRing.material.opacity = (1 - tp) * 0.9;
      c.tapGlow.material.opacity = 0.55 * (A.hit(t, 22.3, 0.3) + A.hit(t, 22.98, 0.4));
      c.tapGlow.visible = c.tapGlow.material.opacity > 0.005;

      // swap icon: pops in and flips on "reversal", keeps a slow 3D sway
      const S = c.icon.swap;
      const ip = A.prog(t, T.reversal - 0.04, T.reversal + 0.5);
      S.h.scale.setScalar(Math.max(1e-4, E.outBack(A.clamp(ip * 1.6))));
      S.h.rotation.y = (1 - E.outBack(ip)) * Math.PI * 2 + 0.22 * Math.sin(t * 1.2) * A.ease(t, T.reversal + 0.5, T.reversal + 1.2);
      S.h.rotation.x = -0.1 * Math.sin(t * 0.9);
      kit_op(S.ic, A.clamp(ip * 4));
      c.iconG.position.z = SURF + 0.02 + 0.3 * A.hit(t, T.reversal + 0.1, 0.3) + 0.1 * A.window(t, T.reversal, 24.9, 0.3, 0.1);
      c.iconShadowPad.material.opacity = 0.3 * A.clamp(ip * 3) * (0.6 + 0.6 * A.hit(t, T.reversal, 0.5));
      c.iconShadowPad.visible = ip > 0;
      c.sparks.update(t, T.reversal + 0.04, [COL_X, 0.32, SURF + 0.6]);

      kickerIn(c.kick, t, T.pot2, A, E);
      wordIn(c.word, t, T.reversal, A, E);
    }

    // ------------------------------------------------------------ VS badge
    {
      const V = this.vs, t0 = 21.50;
      const p = A.prog(t, t0, t0 + 0.42);
      V.vs.visible = t >= t0;
      V.vs.scale.setScalar(Math.max(1e-4, E.outBack(A.clamp(p * 1.25))));
      V.spin.rotation.y = (1 - E.outCubic(p)) * Math.PI * 1.5 + 0.15 * Math.sin(t * 1.3);
      V.vs.position.z = 1.25 + 0.08 * Math.sin(t * 1.7) + 0.3 * A.hit(t, T.reversal, 0.3);
    }

    // ------------------------------------------------------------ light sweep (24.0-24.7)
    const sw = A.lerp(-0.35, 1.6, A.ease(t, T.show, T.show + 0.75, E.inOutSine));
    const swOn = A.window(t, T.show - 0.05, T.show + 0.8, 0.1, 0.15);
    for (const it of this.sweepItems) {
      const d = (it.u - sw) / 0.11;
      const b = swOn * Math.exp(-d * d);
      for (const m of it.mats) m.emissiveIntensity = it.base + 1.05 * b;
    }
    // world-space light rides the same diagonal, top-left to bottom-right
    const lp = A.lerp(-0.35, 1.6, A.ease(t, T.show, T.show + 0.75, E.inOutSine));
    this.sweepLight.position.set(A.lerp(-7, 7, A.clamp(lp)), A.lerp(8, -8, A.clamp(lp)), 6.5);
    this.sweepLight.intensity = 6 * swOn;

    this.dust.update(t);

    // ------------------------------------------------------------ post
    fx.ca = 0.5 * A.hit(t, T.entry, 0.2) + 0.9 * A.hit(t, T.reversal, 0.25) + 0.5 * A.hit(t, 22.3, 0.15);
    fx.shake = 0.05 * A.hit(t, 22.28, 0.18) + 0.06 * A.hit(t, T.reversal, 0.2);
    fx.zoom = 0.12 * A.ease(t, 24.72, 24.9, E.inCubic);
    fx.flash = 0.05 * A.hit(t, T.reversal, 0.15);
    fx.flashColor = '#ffe5e5';
  },
};

// fade an svgIcon (handles depthWrite for clean transparency)
function kit_op(ic, a) {
  ic.mesh.material.opacity = a;
  ic.mesh.material.depthWrite = a > 0.98;
  ic.group.visible = a > 0.001;
}

// small "POTENTIAL" kicker: letters slide up and fade in, quick stagger
function kickerIn(tx, t, t0, A, E) {
  tx.chars.forEach((c, i) => {
    const p = A.prog(t, t0 + i * 0.022, t0 + i * 0.022 + 0.24);
    c.holder.position.y = -0.22 * (1 - E.outCubic(p));
    const a = A.clamp(p * 1.5);
    for (const m of c.mesh.material) { m.opacity = a; m.depthWrite = a > 0.98; }
    c.holder.visible = a > 0.001;
  });
}

// big word: letters drop from in front of the card with overshoot
function wordIn(tx, t, t0, A, E) {
  tx.chars.forEach((c, i) => {
    const s0 = t0 + i * 0.035;
    const p = A.prog(t, s0, s0 + 0.3);
    const e = E.outBack(p);
    c.holder.position.z = 2.2 * (1 - E.outCubic(p));
    c.holder.position.y = 0.25 * (1 - E.outCubic(p));
    c.holder.scale.setScalar(Math.max(1e-4, A.lerp(1.6, 1, e)));
    c.holder.rotation.x = -0.5 * (1 - E.outCubic(p));
    // tiny settle bounce per letter
    c.holder.position.y += 0.06 * Math.sin(A.clamp((t - s0 - 0.3) / 0.25) * Math.PI) * (t > s0 + 0.3 ? 1 : 0);
    const a = A.clamp(p * 2.2);
    for (const m of c.mesh.material) { m.opacity = a; m.depthWrite = a > 0.98; }
    c.holder.visible = a > 0.001;
  });
}
