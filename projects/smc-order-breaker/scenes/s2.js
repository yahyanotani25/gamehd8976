// Scene s2 — "1. ORDER BLOCK" (2.45–11.70). See docs/STORYBOARD.md.
//
// Beats: title types in, candles 0–4 pop, the highlight box draws around the
// order block (candle 4, the last down candle before the impulse), impulse
// candles 5–7 break structure, the zone grows out of candle 4, institutions
// (3D bank) drop in and stream orders into the zone, ENTRY, pullback 8–10,
// candle 11 taps the zone, REACTION (shockwave, candles 12–14, green arrow),
// hold, then the camera whips right into the 11.70 cut.
import { CANDLES, ZONE, ZONE_X1_S2, ZONE_X1_S3, X } from './story-data.js';

const NC = 15; // candles 0–14 belong to this scene
// the bank sits ON the zone, right of the impulse (clear of candles 5-7)
const BANK = { x: 10.5, y: 5.36, z: 0.35, size: 1.6 };
const ENTRY_AT = [8.9, 3.65, 0.45];
const TAP = [11.5, 4.05];
// reaction arrow runs up the empty space left of candles 12-14
const ARROW_FROM = [11.45, 6.1, 0.55], ARROW_TO = [13.05, 10.25, 0.55];
const REACT_AT = [11.0, 2.15, 0.4]; // pill under the zone (fills the lower main band)

// [start, duration, mode] per candle
const APPEAR = [
  [3.00, 0.30, 'pop'], [3.15, 0.30, 'pop'], [3.30, 0.30, 'pop'], [3.45, 0.30, 'pop'], [3.60, 0.30, 'pop'],
  [4.18, 0.24, 'grow'], [4.36, 0.24, 'grow'], [4.54, 0.26, 'grow'],
  [8.00, 0.30, 'pop'], [8.20, 0.30, 'pop'], [8.45, 0.30, 'pop'],
  [9.06, 0.32, 'grow'],
  [9.64, 0.28, 'grow'], [9.84, 0.28, 'grow'], [10.04, 0.30, 'grow'],
];
const TOKEN_WAVES = [6.02, 6.20, 6.40, 6.58];
const TOKENS_PER_WAVE = 6;
const TOKEN_FLIGHT = 0.42;

export default {
  id: 's2', start: 2.45, end: 11.70,
  cues: [
    // title types in
    { t: 2.70, sfx: 'tick' }, { t: 2.78, sfx: 'tick' }, { t: 3.06, sfx: 'tick' },
    { t: 3.38, sfx: 'shimmer', gain: -12 },               // light sweep over the title
    // candles 0–4 pop, pitch stepping down
    { t: 3.00, sfx: 'pop', pitch: 0 }, { t: 3.15, sfx: 'pop', pitch: -1 }, { t: 3.30, sfx: 'pop', pitch: -2 },
    { t: 3.45, sfx: 'pop', pitch: -3 }, { t: 3.60, sfx: 'pop', pitch: -4 },
    { t: 3.92, sfx: 'click' },                             // highlight box around candle 4
    { t: 4.18, sfx: 'grow' }, { t: 4.36, sfx: 'grow', pitch: 1 }, { t: 4.54, sfx: 'grow', pitch: 2 },
    { t: 4.62, sfx: 'blip', gain: -8 },                    // BOS line + tag
    { t: 4.80, sfx: 'swipe' },                             // zone grows out of candle 4
    { t: 5.18, sfx: 'impact', gain: -6 },                  // bank lands (soft)
    { t: 5.25, sfx: 'shimmer' },                           // INSTITUTIONS pill + light pool
    { t: 6.02, sfx: 'tick' }, { t: 6.20, sfx: 'tick', pitch: 1 },
    { t: 6.40, sfx: 'tick', pitch: 2 }, { t: 6.58, sfx: 'tick', pitch: 3 }, // order-flow waves
    { t: 6.64, sfx: 'ding' },                              // ENTRY + zone pulse
    { t: 7.42, sfx: 'swipe', gain: -9 },                   // bank + pill leave
    { t: 7.75, sfx: 'whoosh', gain: -14 },                 // camera reframes right/up
    { t: 8.00, sfx: 'pop' }, { t: 8.20, sfx: 'pop', pitch: -1 }, { t: 8.45, sfx: 'pop', pitch: -2 },
    { t: 9.06, sfx: 'grow', pitch: -3, gain: -4 },          // candle 11 drops to the zone
    { t: 9.10, sfx: 'click' },                             // wick tags the zone
    { t: 9.64, sfx: 'impact' },                            // REACTION: pulse + shockwave
    { t: 9.75, sfx: 'swipe' },                             // green arrow draws up
    { t: 9.78, sfx: 'pop', gain: -4, pitch: 2 },           // REACTION pill
    { t: 9.84, sfx: 'grow' }, { t: 10.04, sfx: 'grow', pitch: 2 },
    { t: 10.55, sfx: 'shimmer', gain: -9 },                // specular glints during the hold
    { t: 11.30, sfx: 'swipe', gain: -11 },                 // labels clear before the cut
    { t: 11.70, sfx: 'whoosh' },                           // whip right into the cut
  ],

  async init(ctx) {
    const { THREE, kit, PAL, ov, group, dom, A, wt } = ctx;
    this.T = {
      order: wt('Order'), block: wt('Block'), zone: wt('zone'), hota: wt('hota'), jahan: wt('jahan'),
      inst: wt('institutions'), market: wt('market'), entry: wt('entry'), price: wt('price'), reaction: wt('reaction'),
    };
    const T = this.T;

    // ---------------------------------------------------------- title
    this.title = kit.text3d('1. ORDER BLOCK', { font: 'bebas', size: 1, depth: 0.3, color: PAL.maroon });
    group.add(this.title.group);
    const wordIdx = [[0, 1], [2, 3, 4, 5, 6], [7, 8, 9, 10, 11]];
    const wordT = [2.70, T.order, T.block];
    this.letterT = [];
    wordIdx.forEach((idx, w) => idx.forEach((ci, j) => { this.letterT[ci] = wordT[w] + j * 0.028; }));
    this.cMaroon = new THREE.Color(PAL.maroon);
    this.cSheen = new THREE.Color('#ff9fae');

    // ---------------------------------------------------------- chart
    this.chart = kit.chart({ data: CANDLES.slice(0, NC) });
    group.add(this.chart.group);

    // highlight box around the order block (candle 4), scaled about its centre
    const c4 = CANDLES[4];
    this.boxPivot = new THREE.Group();
    this.boxPivot.position.set(X(4), (c4.h + c4.l) / 2, 0);
    this.box = kit.outlineBox({ cx: 0, cy: 0, w: 1.22, h: c4.h - c4.l + 0.62, r: 0.27, radius: 0.052 });
    this.boxPivot.add(this.box.group);
    group.add(this.boxPivot);

    // break-of-structure dashes at candle 0's high
    this.bosMat = kit.glossy(PAL.inkSoft, { emissive: 0.05, rough: 0.4 });
    const dashGeo = new THREE.BoxGeometry(0.24, 0.06, 0.05);
    this.bos = [];
    for (let x = 0.9; x < 7.0; x += 0.42) {
      const m = new THREE.Mesh(dashGeo, this.bosMat);
      m.position.set(x + 0.12, CANDLES[0].h, 0.12);
      m.castShadow = true;
      group.add(m);
      this.bos.push(m);
    }
    this.bosSparks = kit.sparks({ count: 16, color: PAL.green, size: 0.16, speed: 3.2, life: 0.55, seed: 5 });
    group.add(this.bosSparks.group);

    // ---------------------------------------------------------- zone
    // Built at s3's full length so the object matches across the cut; the
    // reveal shows only the s2 part until the last 0.3 s.
    this.zone = kit.zone({ x0: ZONE.x0, x1: ZONE_X1_S3, y0: ZONE.y0, y1: ZONE.y1, color: PAL.zoneGreen });
    group.add(this.zone.group);
    this.edgeGlow = kit.glow({ color: PAL.zoneGreen, size: 2.4, opacity: 0.6 });
    group.add(this.edgeGlow);

    // ---------------------------------------------------------- institutions
    this.bankRoot = new THREE.Group();     // position
    this.bankSquash = new THREE.Group();   // squash/stretch about the base
    this.bankSpin = new THREE.Group();     // slow turn to show depth
    this.bank = kit.svgIcon(ov.ICON3D.bank, { size: BANK.size, depth: 0.45, color: PAL.navy, bevel: 0.035 });
    this.bank.mesh.material.emissiveIntensity = 0.18;
    this.bankSpin.add(this.bank.group);
    this.bankSpin.position.y = BANK.size / 2;
    this.bankSquash.add(this.bankSpin);
    this.bankSquash.position.y = -BANK.size / 2;
    this.bankRoot.add(this.bankSquash);
    group.add(this.bankRoot);
    this.bankPool = kit.paperGlow({ color: '#2f6bff', w: 2.6, h: 1.8, opacity: 0.2 });
    this.bankPool.position.set(BANK.x + 0.2, BANK.y - 0.55, 0.006);
    group.add(this.bankPool);
    this.bankGlow = kit.glow({ color: '#4f7dff', size: 3.6, opacity: 0.3 });
    this.bankGlow.position.set(BANK.x, BANK.y, 0.3);
    group.add(this.bankGlow);
    this.bankSparks = kit.sparks({ count: 20, color: '#6f93ff', size: 0.15, speed: 3.6, life: 0.55, seed: 9, spread: Math.PI * 1.2 });
    group.add(this.bankSparks.group);

    // order-flow tokens: navy coins arcing from the bank into the zone
    const r = A.rng(42);
    const coinGeo = new THREE.CylinderGeometry(0.17, 0.17, 0.07, 28);
    coinGeo.rotateX(Math.PI / 2);
    const ringGeo = new THREE.RingGeometry(0.86, 1, 56);
    this.tokens = [];
    TOKEN_WAVES.forEach((tw, w) => {
      for (let k = 0; k < TOKENS_PER_WAVE; k++) {
        const t0 = tw + k * 0.032;
        const lx = 5.2 + ((k + 0.15 + r() * 0.7) / TOKENS_PER_WAVE) * 7.8;
        const ly = 3.25 + r() * 0.85;
        const s = new THREE.Vector3(BANK.x + (r() - 0.5) * 0.6, BANK.y + 0.15, BANK.z + 0.55);
        const e = new THREE.Vector3(lx, ly, 0.28);
        const c = new THREE.Vector3((s.x + e.x) / 2, Math.max(s.y, e.y) + 0.6 + r() * 0.5, 1.7 + r() * 0.6);
        const mat = kit.glossy(PAL.navy, { emissive: 0.25, rough: 0.22 });
        const mesh = new THREE.Mesh(coinGeo, mat);
        mesh.castShadow = true;
        group.add(mesh);
        const ringMat = new THREE.MeshBasicMaterial({ color: PAL.zoneGreen, transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.position.copy(e).setZ(0.27);
        group.add(ring);
        this.tokens.push({ t0, s, c, e, mesh, mat, ring, spin: r() * 6 });
      }
    });
    // trails: 4 dots behind each token, fading towards white
    const nT = this.tokens.length, TR = 4;
    this.trailPos = new Float32Array(nT * TR * 3);
    this.trailCol = new Float32Array(nT * TR * 3);
    const tg = new THREE.BufferGeometry();
    tg.setAttribute('position', new THREE.BufferAttribute(this.trailPos, 3));
    tg.setAttribute('color', new THREE.BufferAttribute(this.trailCol, 3));
    this.trailGeo = tg;
    this.trail = new THREE.Points(tg, new THREE.PointsMaterial({ size: 0.16, vertexColors: true, map: dotTexture(THREE), transparent: true, depthWrite: false, alphaTest: 0.01 }));
    this.trail.frustumCulled = false;
    group.add(this.trail);
    this.cNavy = new THREE.Color(PAL.navy);
    this.cGreen = new THREE.Color(PAL.zoneGreen);
    this.cWhite = new THREE.Color('#ffffff');
    this.cTmp = new THREE.Color();

    // ---------------------------------------------------------- rings + sparks
    const mkRing = (color) => {
      const m = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide });
      const mesh = new THREE.Mesh(ringGeo, m);
      group.add(mesh);
      return mesh;
    };
    this.entryRings = [mkRing(PAL.zoneGreen), mkRing(PAL.zoneGreen)];
    this.touchRing = mkRing(PAL.zoneGreen);
    this.shockRings = [mkRing(PAL.zoneGreen), mkRing(PAL.zoneGreen), mkRing('#7ef0a8')];
    this.touchSparks = kit.sparks({ count: 16, color: PAL.green, size: 0.15, speed: 2.6, life: 0.5, seed: 17 });
    this.reactSparks = kit.sparks({ count: 40, color: PAL.green, size: 0.2, speed: 5.5, life: 0.85, seed: 21, spread: Math.PI * 0.95 });
    group.add(this.touchSparks.group, this.reactSparks.group);
    this.reactPool = kit.paperGlow({ color: PAL.zoneGreen, w: 4.5, h: 3, opacity: 0.3 });
    this.reactPool.position.set(TAP[0], TAP[1], 0.006);
    group.add(this.reactPool);

    // ---------------------------------------------------------- reaction arrow
    this.arrow = kit.arrow(ARROW_FROM, ARROW_TO, { color: PAL.green, radius: 0.095, head: 0.6 });
    group.add(this.arrow.group);
    const L = Math.hypot(ARROW_TO[0] - ARROW_FROM[0], ARROW_TO[1] - ARROW_FROM[1]);
    this.arrowShaft = Math.max(0.05, 1 - (0.6 * 0.6) / L);
    this.arrowGlow = kit.glow({ color: PAL.green, size: 1.8, opacity: 0.55 });
    group.add(this.arrowGlow);

    // ---------------------------------------------------------- glints
    const star = starTexture(THREE);
    const mkGlint = (pos, size) => {
      const m = new THREE.SpriteMaterial({ map: star, color: '#ffffff', transparent: true, opacity: 0, depthWrite: false });
      const s = new THREE.Sprite(m);
      s.position.set(...pos);
      s.userData.size = size;
      group.add(s);
      return s;
    };
    const top = (i) => [X(i) + 0.22, Math.max(CANDLES[i].o, CANDLES[i].c) - 0.05, 0.72];
    this.glints = [
      [mkGlint(top(14), 0.9), 10.50], [mkGlint(top(7), 0.75), 10.62], [mkGlint(top(12), 0.7), 10.74],
      [mkGlint([ZONE.x0 + 0.25, ZONE.y1, 0.3], 0.8), 10.86], [mkGlint(top(5), 0.6), 10.98], [mkGlint(top(13), 0.7), 11.08],
    ];

    // ---------------------------------------------------------- depth dust
    this.dust = kit.dust({ count: 46, w: 34, h: 26, zMin: 1.5, zMax: 9, size: 0.09, cx: 8, cy: 7, seed: 23, opacity: 0.38 });
    group.add(this.dust.group);

    // ---------------------------------------------------------- DOM labels
    ov.css(`
      .s2-pill { font-size: 34px; padding: 15px 26px 13px; gap: 11px; }
      .s2-pill.s2-bos { font-size: 30px; padding: 12px 20px 10px; gap: 9px; letter-spacing: 0.08em; }
    `);
    this.pInst = ov.el(dom, { cls: 'pill navy s2-pill', html: ov.ICON.bank + 'INSTITUTIONS' });
    this.pEntry = ov.el(dom, { cls: 'pill green s2-pill', html: ov.ICON.target + 'ENTRY' });
    this.pReact = ov.el(dom, { cls: 'pill green s2-pill', html: ov.ICON.up + 'REACTION' });
    this.pBos = ov.el(dom, { cls: 'pill ink s2-pill s2-bos', html: ov.ICON.up + 'BOS' });
  },

  // ------------------------------------------------------------------ camera
  camera(t, ctx) {
    const { A, cam } = ctx;
    const E = A.E;
    // 0-7 form at width ~12.5-13.4; institutions at ~14.4; 0-14 at <= 16.5.
    // cy sits above the chart centre so the chart fills the main band 700-1420.
    let cx = A.kf(t, [[2.45, 3.4], [3.6, 3.75, E.outCubic], [3.92, 4.0, E.inOutSine], [4.3, 4.3, E.outCubic],
      [4.78, 4.85, E.inOutSine], [5.6, 6.7, E.inOutCubic], [7.42, 6.85, E.inOutSine], [8.2, 7.85, E.inOutCubic],
      [10.4, 7.95, E.inOutSine], [11.46, 8.2, E.inOutSine]]);
    let cy = A.kf(t, [[2.45, 7.0], [3.6, 7.05, E.outCubic], [3.92, 6.9, E.inOutSine], [4.3, 7.3, E.outCubic],
      [4.78, 7.6, E.inOutSine], [5.6, 7.65, E.inOutCubic], [7.42, 7.7, E.inOutSine], [8.2, 8.35, E.inOutCubic],
      [10.4, 8.3, E.inOutSine], [11.46, 8.2, E.inOutSine]]);
    const width = A.kf(t, [[2.45, 12.4], [3.6, 12.8, E.outCubic], [3.92, 12.45, E.inOutSine], [4.3, 12.9, E.outCubic],
      [4.78, 13.4, E.inOutSine], [5.6, 14.4, E.inOutCubic], [7.42, 14.25, E.inOutSine], [8.2, 16.5, E.inOutCubic],
      [9.6, 16.3, E.inOutSine], [10.3, 16.45, E.outCubic], [11.46, 15.9, E.inOutSine]]);
    let pitch = A.kf(t, [[2.45, -12], [5.6, -10], [8.2, -10.5], [11.46, -8.5]]) + A.noise1(t * 0.35, 11) * 0.8;
    let yaw = A.kf(t, [[2.45, -4], [5.6, 1.2], [8.2, -2], [11.46, 2]]) + A.noise1(t * 0.3, 12) * 0.9;
    let roll = A.noise1(t * 0.25, 13) * 0.35;
    // arrive still pushing in from the zoom cut, then settle
    let dolly = 1 + 0.5 * (1 - E.outExpo(A.prog(t, 2.45, 3.45)));
    dolly -= 0.035 * A.hit(t, 9.64, 0.3) + 0.015 * A.hit(t, 5.18, 0.2) + 0.01 * A.hit(t, 3.92, 0.3) + 0.02 * A.hit(t, 4.5, 0.3);
    // whip right into the cut, landing where s3 picks up (cx 15.2, cy 7.35)
    const w = A.prog(t, 11.46, 11.70) ** 3;
    cx += 7 * w; cy = A.lerp(cy, 7.35, w); yaw += 7 * w; roll -= 1.5 * w;
    cam.frame({
      cx: cx + A.noise1(t * 0.4, 14) * 0.06, cy: cy + A.noise1(t * 0.37, 15) * 0.05,
      width, pitch, yaw, roll, dolly, fov: 28,
    });
  },

  // ------------------------------------------------------------------ pills
  pill(ctx, e, t, tin, tout, pos, { ax = 0.5, ay = 0.5 } = {}) {
    const { A, ov } = ctx;
    const E = A.E;
    if (t < tin || t > tout + 0.16) { ov.place(e, { opacity: 0 }); return; }
    const p = A.prog(t, tin, tin + 0.34);
    let scale = 0.35 + 0.65 * E.outBack(p);
    let opacity = E.outCubic(A.prog(t, tin, tin + 0.12));
    let blur = 9 * (1 - E.outCubic(A.prog(t, tin, tin + 0.16)));
    const rx = 55 * (1 - E.outCubic(p));
    const y = pos.y + 16 * (1 - E.outBack(p));
    if (t > tout) {
      const q = A.prog(t, tout, tout + 0.16);
      scale *= 1 - 0.35 * E.inQuad(q); opacity *= 1 - q; blur += 14 * q;
    }
    ov.place(e, { x: pos.x, y, ax, ay, scale, opacity, blur, rx, persp: 800 });
  },

  update(t, lt, ctx) {
    const { A, fx, toScreen, ov } = ctx;
    const E = A.E, T = this.T;

    // ---------------------------------------------------------- grade + camera
    fx.contrast = 1.06; fx.saturation = 1.1; fx.vignette = 0.2;
    fx.shake = 0.05 * A.hit(t, 5.18, 0.14) + 0.11 * A.hit(t, 9.64, 0.2) + 0.025 * A.hit(t, 9.1, 0.12);
    fx.ca = 0.6 * A.hit(t, 9.64, 0.15);
    this.camera(t, ctx);

    // ---------------------------------------------------------- title
    ctx.pin(this.title.group, { x: 540, y: 470, z: 0.6, heightPx: 118, worldHeight: this.title.capH });
    const sweepOn = t > 3.36 && t < 3.98;
    const sweepX = A.lerp(-3.4, 3.4, E.inOutSine(A.prog(t, 3.36, 3.98)));
    this.title.chars.forEach((c, i) => {
      const t0 = this.letterT[i];
      const p = E.outExpo(A.prog(t, t0, t0 + 0.36));
      const a = E.outCubic(A.prog(t, t0, t0 + 0.2));
      c.holder.position.set(c.holder.userData.baseX, A.lerp(-0.1, 0, p), A.lerp(0.9, 0, p));
      c.holder.scale.setScalar(A.lerp(1.45, 1, p));
      for (const m of c.mesh.material) { m.opacity = a; m.depthWrite = a > 0.98; }
      c.mesh.visible = a > 0.001;
      const sweep = sweepOn ? Math.exp(-(((c.x - sweepX) / 0.55) ** 2)) : 0;
      const land = t >= t0 ? 0.55 * A.hit(t, t0 + 0.1, 0.22) : 0;
      const e = Math.min(1, Math.max(sweep, land));
      c.mesh.material[0].emissive.copy(this.cMaroon).lerp(this.cSheen, e);
      c.mesh.material[0].emissiveIntensity = 0.08 + 0.5 * e;
    });

    // ---------------------------------------------------------- candles
    const sweepC = A.lerp(-2, 16.5, A.prog(t, 10.45, 11.15));
    this.chart.candles.forEach((c, i) => {
      const [t0, dur, mode] = APPEAR[i];
      const p = A.prog(t, t0, t0 + dur);
      c.setAppear(p, mode);
      c.group.position.z = mode === 'pop' ? 0.7 * (1 - E.outCubic(p)) : 0;
      let g = t >= t0 ? 0.55 * A.hit(t, t0 + 0.06, 0.28) : 0;
      if (mode === 'grow' && p > 0 && p < 1) g = Math.max(g, 0.6);
      if (i === 4) g = Math.max(g, 0.9 * A.window(t, T.zone, 5.75, 0.18, 0.5));
      if (i === 11) g = Math.max(g, 0.75 * A.hit(t, 9.1, 0.4));
      if (t > 10.45 && t < 11.15) g = Math.max(g, 0.4 * Math.exp(-(((i - sweepC) / 1.3) ** 2)));
      c.setGlow(g);
    });

    // ---------------------------------------------------------- highlight box
    const bd = E.outCubic(A.prog(t, T.zone, T.zone + 0.35));
    const bf = A.prog(t, 4.86, 5.2);
    this.box.setOpacity(1 - E.inQuad(bf));
    this.box.setDraw(bd);
    const bs = 1 + 0.06 * A.pulse(t, T.zone + 0.42, 0.22) + 0.14 * E.outCubic(bf);
    this.boxPivot.scale.set(bs, bs, 1);
    this.boxPivot.visible = bd > 0.002 && bf < 1;

    // ---------------------------------------------------------- break of structure
    const bosDraw = E.outCubic(A.prog(t, 4.56, 4.78));
    const bosFade = 1 - A.prog(t, 5.45, 5.75);
    this.bos.forEach((m, k) => { m.visible = bosDraw > k / this.bos.length && bosFade > 0; });
    this.bosMat.opacity = bosFade;
    this.bosMat.depthWrite = bosFade > 0.98;
    this.bosSparks.update(t, 4.6, [X(7), CANDLES[0].h, 0.8]);

    // ---------------------------------------------------------- zone
    let xr = ZONE.x0 + (ZONE_X1_S2 - ZONE.x0) * E.outQuart(A.prog(t, T.jahan, T.jahan + 0.6));
    const ext = E.inOutCubic(A.prog(t, 11.40, 11.70));
    xr += (ZONE_X1_S3 - ZONE_X1_S2) * ext;
    const ez = A.clamp((xr - ZONE.x0) / (ZONE_X1_S3 - ZONE.x0));
    this.zone.reveal(ez <= 0 ? 0 : 1 - Math.cbrt(1 - ez));
    this.zone.hatchMat.map.repeat.x = Math.max(0.001, (xr - ZONE.x0) / 1.2);
    let zp = 0;
    for (const tk of this.tokens) zp += 0.16 * A.hit(t, tk.t0 + TOKEN_FLIGHT, 0.18);
    zp = Math.max(zp, 1.0 * A.hit(t, T.entry, 0.45));
    zp = Math.max(zp, 0.9 * A.hit(t, 9.1, 0.3) + 0.3 * A.window(t, 9.1, 9.8, 0.05, 0.25));
    zp = Math.max(zp, 1.2 * A.hit(t, T.reaction, 0.5));
    zp += 0.3 * A.pulse(t, 10.9, 0.7);
    this.zone.pulse(Math.min(1.3, zp));
    const grow = A.prog(t, T.jahan, T.jahan + 0.6);
    const eg = Math.max(Math.sin(Math.PI * grow) * (grow > 0 && grow < 1 ? 1 : 0), Math.sin(Math.PI * ext));
    this.edgeGlow.position.set(xr, (ZONE.y0 + ZONE.y1) / 2, 0.35);
    this.edgeGlow.material.opacity = 0.65 * eg;
    this.edgeGlow.visible = eg > 0.01;

    // ---------------------------------------------------------- bank (institutions)
    const tb = 5.07, tl = 5.18, tx = 7.40;
    const fall = A.prog(t, tb, tl);
    const ex = A.prog(t, tx, tx + 0.24);
    const bankOn = t >= tb && ex < 1;
    this.bankRoot.visible = bankOn;
    if (bankOn) {
      const sp = A.spring(t, tl, { freq: 3.0, damp: 0.32 });
      const squash = t < tl ? -0.6 : 1 - sp; // stretched while falling, squashed on landing
      const es = ex > 0 ? Math.max(0.0001, 1 - E.inBack(ex)) : 1;
      this.bankRoot.position.set(BANK.x, BANK.y + 3.2 * (1 - E.inQuad(fall)) + 0.7 * E.inQuad(ex), BANK.z + 1.2 * (1 - fall));
      this.bankSquash.scale.set((1 + 0.16 * squash) * es, (1 - 0.24 * squash) * es, es);
      this.bankSpin.rotation.y = 0.9 * (1 - E.outCubic(A.prog(t, tb, tl + 0.6))) + 0.24 * Math.sin((t - 5.2) * 1.5);
      this.bank.setOpacity(E.outCubic(A.prog(t, tb, tb + 0.05)));
    }
    const bankLight = A.window(t, tl - 0.02, tx + 0.22, 0.12, 0.22) * (1 + 0.8 * A.hit(t, tl, 0.3));
    this.bankPool.material.opacity = 0.2 * bankLight;
    this.bankPool.visible = bankLight > 0.01;
    this.bankGlow.material.opacity = 0.3 * bankLight;
    this.bankGlow.visible = bankLight > 0.01;
    this.bankSparks.update(t, tl, [BANK.x, BANK.y - BANK.size * 0.45, BANK.z + 0.3]);

    // ---------------------------------------------------------- order-flow tokens
    let ti = 0;
    for (const tk of this.tokens) {
      const p = A.prog(t, tk.t0, tk.t0 + TOKEN_FLIGHT);
      const on = t >= tk.t0 && p < 1;
      tk.mesh.visible = on;
      const pos = (q) => bez(tk.s, tk.c, tk.e, E.inOutQuad(q));
      if (on) {
        const P = pos(p);
        tk.mesh.position.copy(P);
        const sc = E.outBack(A.prog(p, 0, 0.25)) * (1 - E.inQuad(A.prog(p, 0.86, 1)));
        tk.mesh.scale.setScalar(Math.max(0.0001, sc));
        tk.mesh.rotation.set(0.5, tk.spin + p * 7, 0);
        this.cTmp.copy(this.cNavy).lerp(this.cGreen, E.inQuad(A.prog(p, 0.35, 1)));
        tk.mat.color.copy(this.cTmp); tk.mat.emissive.copy(this.cTmp);
      }
      for (let j = 0; j < 4; j++) {
        const q = p - 0.045 * (j + 1);
        const k = (ti * 4 + j) * 3;
        if (on && q > 0) {
          const P = pos(q);
          this.trailPos[k] = P.x; this.trailPos[k + 1] = P.y; this.trailPos[k + 2] = P.z;
        } else { this.trailPos[k] = 0; this.trailPos[k + 1] = -50; this.trailPos[k + 2] = 0; }
        this.cTmp.copy(this.cNavy).lerp(this.cGreen, A.clamp(q)).lerp(this.cWhite, 0.3 + j * 0.17);
        this.trailCol[k] = this.cTmp.r; this.trailCol[k + 1] = this.cTmp.g; this.trailCol[k + 2] = this.cTmp.b;
      }
      // landing ripple
      const rp = A.prog(t, tk.t0 + TOKEN_FLIGHT - 0.03, tk.t0 + TOKEN_FLIGHT + 0.4);
      tk.ring.visible = rp > 0 && rp < 1;
      tk.ring.scale.setScalar(0.12 + 0.75 * E.outCubic(rp));
      tk.ring.material.opacity = 0.75 * (1 - rp);
      ti++;
    }
    this.trailGeo.attributes.position.needsUpdate = true;
    this.trailGeo.attributes.color.needsUpdate = true;
    this.trail.visible = t > 6.0 && t < 7.2;

    // ---------------------------------------------------------- entry rings
    this.entryRings.forEach((m, k) => {
      const rp = A.prog(t, T.entry + k * 0.08, T.entry + k * 0.08 + 0.6);
      m.visible = rp > 0 && rp < 1;
      m.position.set(ENTRY_AT[0], ENTRY_AT[1], 0.3);
      m.scale.set(0.4 + 3.2 * E.outCubic(rp), 0.4 + 2.2 * E.outCubic(rp), 1);
      m.material.opacity = 0.8 * (1 - rp);
    });

    // ---------------------------------------------------------- touch (candle 11 tags the zone)
    {
      const rp = A.prog(t, 9.1, 9.5);
      const m = this.touchRing;
      m.visible = rp > 0 && rp < 1;
      m.position.set(TAP[0], ZONE.y1, 0.3);
      m.scale.setScalar(0.15 + 1.3 * E.outCubic(rp));
      m.material.opacity = 0.85 * (1 - rp);
      this.touchSparks.update(t, 9.1, [TAP[0], ZONE.y1, 0.6]);
    }

    // ---------------------------------------------------------- reaction
    this.shockRings.forEach((m, k) => {
      const d = [0, 0.07, 0.03][k], dur = [0.6, 0.7, 0.45][k];
      const rp = A.prog(t, T.reaction + d, T.reaction + d + dur);
      m.visible = rp > 0 && rp < 1;
      m.position.set(TAP[0], TAP[1], k === 2 ? 0.02 : 0.32);
      const s = (k === 2 ? 0.3 + 7 * E.outQuart(rp) : 0.25 + 4.6 * E.outCubic(rp));
      m.scale.set(s, s * (k === 2 ? 0.8 : 1), 1);
      m.material.opacity = (k === 2 ? 0.45 : 0.85) * (1 - rp) * (1 - rp * 0.3);
    });
    this.reactSparks.update(t, T.reaction, [TAP[0], ZONE.y1, 0.6]);
    const rpool = A.hit(t, T.reaction, 0.6);
    this.reactPool.material.opacity = 0.3 * rpool;
    this.reactPool.visible = rpool > 0.01;

    // arrow: draws up from the zone, retracts into its tip before the cut
    const ad = E.outCubic(A.prog(t, 9.70, 10.30));
    this.arrow.setDraw(ad);
    const ar = E.inOutCubic(A.prog(t, 11.24, 11.42));
    if (ar > 0) {
      this.arrow.shaft.setDraw(this.arrowShaft, Math.min(this.arrowShaft - 0.001, ar * this.arrowShaft));
      const hs = 1 - E.inBack(A.prog(t, 11.36, 11.48));
      this.arrow.head.scale.setScalar(Math.max(0.0001, hs));
      this.arrow.group.visible = hs > 0.01;
    }
    const tip = this.arrow.head.position;
    this.arrowGlow.position.set(tip.x, tip.y, tip.z + 0.2);
    const ag = (ad > 0 && ad < 1 ? 0.8 : 0) + 0.6 * A.hit(t, 10.3, 0.35);
    this.arrowGlow.material.opacity = 0.55 * Math.min(1, ag) * (1 - ar);
    this.arrowGlow.visible = this.arrowGlow.material.opacity > 0.01;

    // ---------------------------------------------------------- glints
    for (const [s, tg] of this.glints) {
      const k = A.pulse(t, tg, 0.42);
      s.visible = k > 0.01;
      s.material.opacity = 0.95 * k;
      s.material.rotation = (t - tg) * 2.2;
      const sz = s.userData.size * (0.4 + 0.6 * k);
      s.scale.set(sz, sz, 1);
    }

    this.dust.update(t);

    // ---------------------------------------------------------- DOM labels
    const sInst = toScreen([BANK.x, BANK.y + BANK.size / 2 + 0.72, BANK.z]);
    this.pill(ctx, this.pInst, t, 5.22, 7.40, sInst);
    const sEntry = toScreen(ENTRY_AT);
    this.pill(ctx, this.pEntry, t, T.entry, 11.30, sEntry);
    const sReact = toScreen(REACT_AT);
    this.pill(ctx, this.pReact, t, 9.76, 11.34, sReact);
    const sBos = toScreen([3.5, CANDLES[0].h + 0.66, 0.2]);
    this.pill(ctx, this.pBos, t, 4.62, 5.45, sBos);
  },
};

// quadratic bezier
function bez(a, b, c, q) {
  const u = 1 - q;
  return a.clone().multiplyScalar(u * u).add(b.clone().multiplyScalar(2 * u * q)).add(c.clone().multiplyScalar(q * q));
}

function dotTexture(THREE) {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d');
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.55, 'rgba(255,255,255,0.75)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
}

// four-point sparkle for specular glints
function starTexture(THREE) {
  const S = 256, c = document.createElement('canvas'); c.width = c.height = S;
  const g = c.getContext('2d');
  const gr = g.createRadialGradient(S / 2, S / 2, 0, S / 2, S / 2, S * 0.22);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.4, 'rgba(255,255,255,0.5)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, S, S);
  for (const [w, h] of [[S, 10], [10, S]]) {
    const lg = w > h ? g.createLinearGradient(0, 0, S, 0) : g.createLinearGradient(0, 0, 0, S);
    lg.addColorStop(0, 'rgba(255,255,255,0)'); lg.addColorStop(0.5, 'rgba(255,255,255,1)'); lg.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = lg;
    g.beginPath();
    if (w > h) g.ellipse(S / 2, S / 2, S / 2, 5, 0, 0, Math.PI * 2);
    else g.ellipse(S / 2, S / 2, 5, S / 2, 0, 0, Math.PI * 2);
    g.fill();
  }
  return new THREE.CanvasTexture(c);
}
