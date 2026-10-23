// Scene s3 (11.70-18.00): the order block FAILS, flips its role in 3D
// (support -> resistance) and becomes 2. BREAKER BLOCK.
// Pure function of time: every animated property is set on every update.
// See docs/STORYBOARD.md (s3) for the beat sheet.
import { CANDLES, ZONE, ZONE_X1_S3, X } from './story-data.js';

const ZX0 = ZONE.x0, ZX1 = ZONE_X1_S3, ZY0 = ZONE.y0, ZY1 = ZONE.y1;
const ZYM = (ZY0 + ZY1) / 2, ZH = ZY1 - ZY0;
const PIV = 0.14;          // flip axis height above the paper (mid-slab)
const LIFT = 1.2;          // how far the zone rises off the paper to flip
const GREY = '#8d949f';    // drained, failed zone
const TITLE_PIN = { x: 540, y: 470, z: 0.6, heightPx: 118 };

// deterministic hash in [0, 1)
const hash = (n) => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
// symmetric ease with a small wind-up and overshoot (value 0.5 at x = 0.5)
function inOutBack(x, s = 0.9) {
  const c2 = s * 1.525;
  return x < 0.5
    ? (Math.pow(2 * x, 2) * ((c2 + 1) * 2 * x - c2)) / 2
    : (Math.pow(2 * x - 2, 2) * ((c2 + 1) * (x * 2 - 2) + c2) + 2) / 2;
}

const RES_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h18"/><path d="M12 8.5V21"/><path d="M7 16l5 5 5-5"/></svg>';

export default {
  id: 's3', start: 11.70, end: 18.00,
  // SFX cue sheet (t = when the visual event lands).
  cues: [
    { t: 12.00, sfx: 'pop', pitch: 0 },            // candle 15 returns
    { t: 12.18, sfx: 'pop', pitch: -1 },           // candle 16
    { t: 12.36, sfx: 'pop', pitch: -2 },           // candle 17 reaches the zone
    { t: 12.74, sfx: 'boom' },                     // candle 18 smashes the zone
    { t: 12.74, sfx: 'crack' },                    // zone cracks
    { t: 12.80, sfx: 'drone', gain: -4, dur: 3.7 },// tension bed: fail -> breaker reveal
    { t: 12.82, sfx: 'stamp' },                    // FAILED stamp lands
    { t: 12.90, sfx: 'blip', gain: -10, pitch: -5 }, // zone glitch flicker
    { t: 13.05, sfx: 'pop', pitch: -4 },           // candle 19 continues down
    { t: 13.64, sfx: 'swipe', gain: -14 },         // FAILED leaves
    { t: 13.84, sfx: 'pop', pitch: 3 },            // SUPPORT pill
    { t: 13.92, sfx: 'tick', gain: -8 },           // support chevrons pop up
    { t: 14.00, sfx: 'pop', pitch: 1 },            // candle 20 retrace
    { t: 14.32, sfx: 'swipe', gain: -10, pitch: 4 }, // zone lifts off the paper
    { t: 14.50, sfx: 'flip' },                     // 3D flip
    { t: 14.72, sfx: 'click' },                    // SUPPORT -> RESISTANCE
    { t: 15.07, sfx: 'impact', gain: -6 },         // red zone lands
    { t: 15.20, sfx: 'pop', pitch: 2 },            // candle 21
    { t: 16.06, sfx: 'grow', gain: -6, pitch: 3 }, // candle 22 rallies into the zone
    { t: 16.20, sfx: 'click' },                    // rejected from below
    { t: 16.20, sfx: 'impact', gain: -12 },        // zone pulse / ring
    { t: 16.24, sfx: 'tick', gain: -6 },           // highlight box draws on candle 22
    { t: 16.46, sfx: 'impact' },                   // title morph
    { t: 16.46, sfx: 'shimmer' },
    { t: 16.60, sfx: 'grow', pitch: -2 },          // candle 23
    { t: 16.65, sfx: 'swipe' },                    // red arrow draws down
    { t: 16.84, sfx: 'grow', pitch: -4 },          // candle 24
    { t: 17.10, sfx: 'grow', pitch: -6 },          // candle 25
    { t: 17.12, sfx: 'pop', gain: -3, pitch: -2 }, // BREAKER BLOCK pill
    { t: 17.14, sfx: 'shimmer', gain: -10 },       // light sweep along the zone
    { t: 18.00, sfx: 'riser', gain: -6 },          // push into the cut (peaks at the cut)
    { t: 18.00, sfx: 'whoosh' },
  ],

  init(ctx) {
    const { THREE, kit, PAL, ov, A, group, dom } = ctx;
    const w = ctx.wt;
    this.T = {
      c15: w('Jab') - 0.06, c16: w('yeh') - 0.06, c17: w('block', 2),
      fail: w('fail'), c19: w('ho') + 0.05,
      support: w('aur'), c20: w('apna') - 0.14,
      role: w('role'), reverse: w('reverse'), flipEnd: w('role') + 0.557,
      c21: w('kar') + 0.10,
      c22: w('toh'), reject: w('yeh', 2) + 0.02,
      morph: w('Breaker'),
      c23: w('Breaker') + 0.14, c24: w('Block', 3), c25: w('ban'),
      pill: w('ban'),
    };
    const T = this.T;
    T.c18 = T.fail - 0.14;
    T.stamp = T.fail + 0.08;
    T.land = T.flipEnd + 0.07;

    ov.css(`
      .s3-stamp { font-size: 46px; padding: 20px 34px 18px; gap: 16px;
        box-shadow: 0 0 0 5px rgba(255,255,255,0.97), 0 0 0 10px #d3101b, 0 22px 44px rgba(120,6,12,0.38); }
      .s3-ring { width: 260px; height: 260px; border-radius: 50%; border: 7px solid #ff3340; box-sizing: border-box; }
      .s3-res-tag { font-size: 30px; padding: 13px 22px 12px; gap: 10px; }
    `);

    // ------------------------------------------------------------ chart
    this.chart = kit.chart({ data: CANDLES, x0: 0.5, step: 1 });
    group.add(this.chart.group);
    // live-formation helper body for candle 22's rally (green while above the open)
    this.ghost = kit.candle({ o: 2.4, h: 3.8, l: 2.4, c: 3.8, x: X(22), color: PAL.green });
    this.ghost.wick.visible = false;
    group.add(this.ghost.group);

    // ------------------------------------------------------------ zone flip rig
    // lift (z) -> pivot (flip axis at the zone's centre line) -> two faces:
    // the green order-block face on top, a red breaker face underneath.
    const zArgs = { x0: ZX0, x1: ZX1, y0: ZY0, y1: ZY1 };
    this.zG = kit.zone({ ...zArgs, color: PAL.zoneGreen });
    this.zR = kit.zone({ ...zArgs, color: PAL.zoneRed });
    this.lift = new THREE.Group();
    this.pivot = new THREE.Group();
    this.pivot.position.set(ZX0, ZYM, PIV);
    this.lift.add(this.pivot);
    this.pivot.add(this.zG.group, this.zR.group);
    this.zG.group.position.set(0, 0, -PIV);
    this.zR.group.position.set(0, 0, PIV);
    this.zR.group.rotation.x = Math.PI;
    group.add(this.lift);

    // chevrons on each face: up on the support face, down on the resistance face
    const cw = 0.5, ch = 0.26, th = 0.12, slope = ch / (cw / 2);
    const cs = new THREE.Shape();
    cs.moveTo(-cw / 2, -ch / 2); cs.lineTo(0, ch / 2); cs.lineTo(cw / 2, -ch / 2);
    cs.lineTo(cw / 2 - th, -ch / 2); cs.lineTo(0, ch / 2 - th * slope); cs.lineTo(-cw / 2 + th, -ch / 2); cs.closePath();
    const chevGeo = new THREE.ExtrudeGeometry(cs, { depth: 0.05, bevelEnabled: true, bevelThickness: 0.012, bevelSize: 0.01, bevelSegments: 1 });
    const CHEV_X = [14.3, 16.3, 20.6, 24.2, 26.0];
    const mkChevrons = (parent, color, dir) => {
      const mat = kit.glossy(color, { emissive: 0.35, rough: 0.2 });
      const list = CHEV_X.map((x) => {
        const g = new THREE.Group();
        for (const dy of [-0.13, 0.13]) {
          const m = new THREE.Mesh(chevGeo, mat);
          m.position.y = dy * dir;
          m.rotation.z = dir > 0 ? 0 : Math.PI;
          m.castShadow = true;
          g.add(m);
        }
        g.position.set(x - ZX0, 0, 0.2);
        g.userData.x = x;
        parent.add(g);
        return g;
      });
      return { mat, list };
    };
    this.chevUp = mkChevrons(this.zG.group, PAL.green, 1);
    this.chevDn = mkChevrons(this.zR.group, PAL.red, -1);

    // cracks radiating from candle 18's impact, on the green face
    const rc = A.rng(1807);
    this.cracks = [];
    const ox = X(18) - ZX0;
    const crackDirs = [0.08, -0.22, 0.45, Math.PI - 0.12, Math.PI + 0.3, Math.PI - 0.55, 1.25, -1.35, 0.9, Math.PI + 0.85];
    crackDirs.forEach((a0, k) => {
      const pts = [[ox + (rc() - 0.5) * 0.12, (rc() - 0.5) * 0.2, 0.24]];
      const len = k < 6 ? 1.6 + rc() * 2.2 : 0.5 + rc() * 0.5;
      let L = 0, a = a0, x = pts[0][0], y = pts[0][1];
      while (L < len) {
        const seg = 0.18 + rc() * 0.34;
        a = a0 + (rc() - 0.5) * 0.9;
        x += Math.cos(a) * seg; y += Math.sin(a) * seg;
        if (Math.abs(y) > ZH / 2 - 0.1) { y = Math.sign(y) * (ZH / 2 - 0.1); pts.push([x, y, 0.24]); break; }
        pts.push([x, y, 0.24]);
        L += seg;
      }
      const s = kit.stroke(pts, { color: '#1b1f27', radius: k < 6 ? 0.03 : 0.022 });
      s.delay = k < 6 ? k * 0.008 : 0.03 + (k - 6) * 0.012;
      this.zG.group.add(s.group);
      this.cracks.push(s);
    });

    // glass shards thrown out of the zone at the impact
    const rs = A.rng(4242);
    this.shardMat = kit.glossy(PAL.zoneGreen, { emissive: 0.35, rough: 0.12 });
    const shardGeo = new THREE.BoxGeometry(1, 1, 1);
    this.shards = [];
    for (let i = 0; i < 26; i++) {
      const m = new THREE.Mesh(shardGeo, this.shardMat);
      m.castShadow = true;
      const side = i % 2 ? 1 : -1;
      const ang = (side > 0 ? 0.25 : Math.PI - 0.25) + (rs() - 0.5) * 1.5;
      const sp = 2.2 + rs() * 4.8;
      this.shards.push({
        m, ox: X(18) + (rs() - 0.5) * 0.5, oy: ZYM + (rs() - 0.5) * 1.1,
        vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp + 1.2, vz: 1.5 + rs() * 4.5,
        wx: (rs() - 0.5) * 22, wy: (rs() - 0.5) * 22, wz: (rs() - 0.5) * 22,
        sx: 0.1 + rs() * 0.22, sy: 0.07 + rs() * 0.15, sz: 0.04 + rs() * 0.05, life: 0.55 + rs() * 0.5,
      });
      group.add(m);
    }

    // digital glitch slices over the zone right after the fail
    this.glitch = [];
    const gcol = [PAL.zoneRed, PAL.zoneGreen, '#ffffff', PAL.zoneRed, '#ffffff', PAL.zoneGreen, '#ffffff'];
    for (let i = 0; i < gcol.length; i++) {
      const mat = new THREE.MeshBasicMaterial({ color: gcol[i], transparent: true, opacity: 0.65, depthWrite: false });
      const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat);
      m.renderOrder = 3;
      group.add(m);
      this.glitch.push(m);
    }

    // shockwave rings lying on the paper
    const mkRing = (color) => {
      const mat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0, depthWrite: false });
      const m = new THREE.Mesh(new THREE.RingGeometry(0.88, 1, 96), mat);
      group.add(m);
      return m;
    };
    this.ringFail = mkRing(PAL.zoneRed);
    this.ringFail2 = mkRing(PAL.red);
    this.ringReject = mkRing(PAL.zoneRed);

    // light pools and glows
    this.poolFail = kit.paperGlow({ color: PAL.red, w: 3.2, h: 3.2, opacity: 0.55 });
    this.poolFail.position.set(X(18), ZYM, 0.006);
    this.poolLand = kit.paperGlow({ color: PAL.zoneRed, w: ZX1 - 10, h: 2.4, opacity: 0.5 });
    this.poolLand.position.set((10 + ZX1) / 2, ZYM, 0.006);
    this.poolReject = kit.paperGlow({ color: PAL.red, w: 2.2, h: 2.4, opacity: 0.5 });
    this.poolReject.position.set(X(22), 3.4, 0.006);
    this.poolBreaker = kit.paperGlow({ color: PAL.zoneRed, w: 7, h: 6, opacity: 0.35 });
    this.poolBreaker.position.set(24.2, 1.2, 0.006);
    group.add(this.poolFail, this.poolLand, this.poolReject, this.poolBreaker);
    this.glowFail = kit.glow({ color: '#ff3b47', size: 3.2, opacity: 0.75 });
    this.glowTip = kit.glow({ color: '#ff2a36', size: 1.5, opacity: 0.8 });
    this.glowReject = kit.glow({ color: '#ff3b47', size: 1.8, opacity: 0.7 });
    this.sweepA = kit.glow({ color: '#ff7a82', size: 1.5, opacity: 0.85 });
    this.sweepB = kit.glow({ color: '#ff7a82', size: 1.5, opacity: 0.85 });
    group.add(this.glowFail, this.glowTip, this.glowReject, this.sweepA, this.sweepB);

    this.sparksFail = kit.sparks({ count: 48, color: PAL.red, size: 0.22, speed: 7.5, life: 0.75, seed: 31 });
    this.sparksFail2 = kit.sparks({ count: 26, color: PAL.ink, size: 0.12, speed: 5.5, life: 0.6, seed: 37 });
    this.sparksReject = kit.sparks({ count: 26, color: PAL.red, size: 0.17, speed: 4.2, life: 0.55, seed: 41, dir: -Math.PI / 2, spread: 2.4 });
    this.sparksLand = kit.sparks({ count: 30, color: PAL.zoneRed, size: 0.15, speed: 3.5, life: 0.5, seed: 43, spread: Math.PI * 2 });
    group.add(this.sparksFail.group, this.sparksFail2.group, this.sparksReject.group, this.sparksLand.group);

    // highlight box on the rejection candle (reference style) and the red arrow
    this.box = kit.outlineBox({ cx: X(22), cy: 2.9, w: 1.22, h: 2.5, r: 0.26, z: 0.8 });
    this.arrow = kit.arrow([24.25, 2.6, 0.4], [26.45, -1.55, 0.4], { color: PAL.red, radius: 0.095, head: 0.6, bend: 0.28 });
    group.add(this.box.group, this.arrow.group);

    this.dust = kit.dust({ count: 46, w: 34, h: 28, cx: 20, cy: 4, zMin: 1.8, zMax: 11, size: 0.13, seed: 33, opacity: 0.45 });
    group.add(this.dust.group);

    // ------------------------------------------------------------ titles
    const tOpts = { font: 'bebas', size: 1, depth: 0.3, color: PAL.maroon };
    this.titleA = kit.text3d('1. ORDER BLOCK', tOpts);
    this.titleB = kit.text3d('2. BREAKER BLOCK', tOpts);
    group.add(this.titleA.group, this.titleB.group);
    const pxPerUnit = TITLE_PIN.heightPx / this.titleA.capH;
    this.kB = Math.min(1, 880 / (this.titleB.width * pxPerUnit)); // keep the longer title inside x 70-1010
    const a = this.titleA.chars, b = this.titleB.chars;
    this.mA = { digit: a[0], dot: a[1], order: a.slice(2, 7), block: a.slice(7) };
    this.mB = { digit: b[0], dot: b[1], breaker: b.slice(2, 9), block: b.slice(9) };
    this.cMaroon = new THREE.Color(PAL.maroon);
    this.cRed = new THREE.Color(PAL.red);
    this.cGreen = new THREE.Color(PAL.zoneGreen);
    this.cZRed = new THREE.Color(PAL.zoneRed);
    this.cGrey = new THREE.Color(GREY);
    this.cWhite = new THREE.Color('#ffffff');
    this.tmpC = new THREE.Color();
    this.tmpC2 = new THREE.Color();

    // ------------------------------------------------------------ pills
    this.pFail = ov.el(dom, { cls: 'pill red s3-stamp', html: ov.ICON.x + 'FAILED' });
    this.ringEl = ov.el(dom, { cls: 's3-ring' });
    this.pSup = ov.el(dom, { cls: 'pill green', html: ov.ICON.shield + 'SUPPORT' });
    this.pRes = ov.el(dom, { cls: 'pill red', html: RES_ICON + 'RESISTANCE' });
    this.pBrk = ov.el(dom, { cls: 'pill red', html: ov.ICON.reverse + 'BREAKER BLOCK' });
    this.pw = {};
    for (const [k, e] of Object.entries({ fail: this.pFail, sup: this.pSup, res: this.pRes, brk: this.pBrk })) this.pw[k] = e.offsetWidth || 400;
  },

  update(t, lt, ctx) {
    const { A, cam, fx, PAL, ov, THREE, toScreen } = ctx;
    const E = A.E, T = this.T;

    // ============================================================ camera
    const arrive = E.outExpo(A.prog(t, 11.70, 12.40));
    const flipWin = A.window(t, T.role - 0.2, T.land + 0.45, 0.35, 0.5);
    // frames candles ~11-26; pulls back and follows the drop after the morph so
    // candles 23-25 fit above the caption band while candle 14 stays under the title
    let cx = A.lerp(16.2, 18.7, arrive)
      + A.kf(t, [[12.4, 0], [16.4, 0.3, E.inOutSine], [17.45, 1.3, E.inOutCubic], [18, 1.4, E.outSine]]);
    let cy = A.kf(t, [[11.7, 7.2], [12.4, 6.85, E.outCubic], [13.2, 6.5, E.inOutSine], [16.4, 6.4, E.inOutSine],
      [17.45, 5.4, E.inOutCubic], [18, 5.3, E.outSine]]);
    const width = A.kf(t, [[11.7, 15.2], [12.4, 15.9, E.outCubic], [16.4, 15.7, E.inOutSine], [17.45, 17.8, E.inOutCubic], [18, 17.7, E.outSine]]);
    cx += A.noise1(t * 0.45, 3) * 0.12;
    cy += A.noise1(t * 0.4, 4) * 0.1 - 0.16 * A.hit(t, T.fail, 0.3);
    const pitch = -10 + A.noise1(t * 0.3, 5) * 1.3 - 6 * flipWin;
    const yaw = 4 + A.noise1(t * 0.27, 6) * 1.6 + 4 * flipWin;
    const roll = A.noise1(t * 0.22, 7) * 0.35 + 0.9 * A.hit(t, T.fail, 0.25) * Math.sin((t - T.fail) * 40);
    const push = A.lerp(1, 0.82, E.inCubic(A.prog(t, 17.78, 18.0)));
    const dolly = (1 - 0.04 * A.hit(t, T.fail, 0.3) - 0.015 * A.hit(t, T.reject, 0.2) - 0.02 * A.hit(t, T.morph, 0.25)) * push;
    cam.frame({ cx, cy, width, pitch, yaw, roll, dolly });

    // ============================================================ candles
    const ch = this.chart, C = ch.candles;
    const times = CANDLES.map((_, i) => (i <= 14 ? -1 : undefined));
    const pops = { 15: T.c15, 16: T.c16, 17: T.c17, 19: T.c19, 20: T.c20, 21: T.c21 };
    for (const [i, t0] of Object.entries(pops)) times[i] = t0;
    ch.animate(t, times, { dur: 0.26, mode: 'pop' });
    C.forEach((c, i) => c.setGlow(pops[i] !== undefined ? 0.8 * A.hit(t, pops[i] + 0.08, 0.3) : 0));
    for (const [i, t0] of [[23, T.c23], [24, T.c24], [25, T.c25]]) {
      C[i].setAppear(A.prog(t, t0, t0 + 0.24), 'grow');
      C[i].setGlow(0.9 * A.hit(t, t0 + 0.12, 0.35));
    }
    // candle 18: creeps to the zone, then smashes through it
    const c18 = C[18];
    const p18 = A.kf(t, [[T.c18, 5.2], [T.c18 + 0.035, 5.4, E.outQuad], [T.fail - 0.02, 4.5, E.inOutSine], [T.fail + 0.06, 1.2, E.inQuad], [T.fail + 0.15, 1.5, E.outCubic]]);
    if (t >= T.c18) {
      const hi = t < T.c18 + 0.035 ? Math.max(5.2, p18) : 5.4;
      const lo = t < T.fail + 0.06 ? Math.min(5.2, p18) : 1.2;
      this.form(c18, p18, hi, lo, E.outBack(A.prog(t, T.c18, T.c18 + 0.08)) * 0.3 + 0.7);
      c18.setGlow(Math.max(0.5 * A.window(t, T.c18, T.fail + 0.1, 0.05, 0.05), A.hit(t, T.fail, 0.45)));
    } else c18.group.visible = false;
    // candle 22: rallies up into the zone (green), rejected (turns red), long upper wick
    const c22 = C[22], g22 = this.ghost;
    const p22 = A.kf(t, [[T.c22, 2.4], [T.reject, 3.8, E.outCubic], [T.reject + 0.09, 2.0, E.inOutQuad], [T.reject + 0.18, 2.1, E.outQuad]]);
    if (t >= T.c22) {
      const hi = t < T.reject ? Math.max(2.4, p22) : 3.8;
      const lo = t < T.reject ? 2.4 : (t < T.reject + 0.09 ? Math.min(2.4, p22) : 2.0);
      const s22 = 0.75 + 0.25 * E.outBack(A.prog(t, T.c22, T.c22 + 0.1));
      this.form(c22, p22, hi, lo, s22);
      c22.body.visible = p22 < 2.4 - 0.005;
      g22.group.visible = p22 > 2.4 + 0.005;
      if (g22.group.visible) this.form(g22, p22, p22, 2.4, s22);
      g22.wick.visible = false;
      c22.setGlow(0.9 * A.hit(t, T.reject, 0.45));
      g22.setGlow(0.5 * A.window(t, T.c22, T.reject, 0.05, 0.02));
    } else { c22.group.visible = false; g22.group.visible = false; }

    // ============================================================ zone
    const fpg = A.prog(t, T.role, T.flipEnd);
    const ang = Math.PI * inOutBack(fpg, 0.9);
    this.pivot.rotation.x = ang;
    const liftZ = A.kf(t, [[T.role - 0.16, 0], [T.role + 0.08, LIFT, E.outCubic], [T.flipEnd - 0.06, LIFT], [T.land, 0, E.inQuad]]);
    this.lift.position.z = liftZ;
    const liftK = liftZ / LIFT;
    const face = A.clamp((ang / Math.PI - 0.45) / 0.1); // 0 green face up .. 1 red face up
    // glitch envelope and stepped randomness (30 Hz)
    const gEnv = A.window(t, T.fail - 0.005, T.fail + 0.36, 0.01, 0.14);
    const step = Math.floor(t * 30);
    // green / failed face
    const drain = A.ease(t, T.fail + 0.05, T.fail + 0.62, E.inOutSine);
    const supK = A.ease(t, T.support, T.support + 0.35);
    const zc = this.tmpC.copy(this.cGreen).lerp(this.cGrey, drain).lerp(this.cGreen, 0.22 * supK);
    if (gEnv > 0.05) {
      const hv = hash(step * 1.7 + 3);
      if (hv > 0.62) zc.copy(this.cZRed); else if (hv > 0.45) zc.copy(this.cWhite).lerp(this.cGreen, 0.3);
    }
    this.zG.setColor(zc);
    const aG = (1 - 0.12 * drain) * (1 - face);
    this.zoneState(this.zG, aG, 0.9 * A.hit(t, T.fail, 0.18) + 0.25 * A.hit(t, T.support + 0.05, 0.35), 1 - liftK);
    this.zG.group.position.set(gEnv > 0.05 ? (hash(step * 2.3 + 11) - 0.5) * 0.3 * gEnv : 0, gEnv > 0.05 ? (hash(step * 3.1 + 5) - 0.5) * 0.12 * gEnv : 0, -PIV);
    // red / breaker face
    const breath = 0.08 + 0.06 * Math.sin(t * 5.2);
    const rPulse = Math.max(A.hit(t, T.land, 0.35), A.hit(t, T.reject, 0.3), 0.7 * A.hit(t, T.pill + 0.02, 0.35)) + breath * face;
    this.zR.setColor(this.cZRed);
    this.zoneState(this.zR, face, rPulse, 1 - liftK);
    // chevrons
    this.chevUp.list.forEach((g, i) => {
      const p = A.prog(t, T.support + 0.06 + i * 0.045, T.support + 0.34 + i * 0.045);
      const s = E.outBack(p);
      g.visible = p > 0 && aG > 0.01;
      g.scale.setScalar(Math.max(1e-4, s));
      g.position.y = 0.05 * Math.sin((t - i * 0.12) * 7.5) * p;
    });
    this.chevUp.mat.opacity = Math.min(1, aG * 1.1);
    this.chevUp.mat.emissiveIntensity = 0.35 + 0.4 * A.hit(t, T.support + 0.3, 0.3);
    this.chevDn.list.forEach((g, i) => {
      g.visible = face > 0.01;
      g.scale.setScalar(1 + 0.25 * A.hit(t, T.reject + i * 0.02, 0.25));
      g.position.y = -0.05 * Math.sin((t - i * 0.12) * 7.5);
    });
    this.chevDn.mat.opacity = face;
    this.chevDn.mat.emissiveIntensity = 0.35 + 0.5 * rPulse;
    // cracks
    this.cracks.forEach((s) => {
      s.setDraw(E.outExpo(A.prog(t, T.fail - 0.01 + s.delay, T.fail + 0.16 + s.delay)));
      s.setOpacity(aG > 0.01 ? Math.min(1, aG * 1.2) : 0);
    });
    // light sweeps along the red rails when it lands / is named
    const sw = Math.max(A.prog(t, T.land, T.land + 0.55) * (t < T.land + 0.55 ? 1 : 0), 0);
    const sw2 = A.prog(t, T.pill, T.pill + 0.6) * (t < T.pill + 0.6 ? 1 : 0);
    const sp = sw > 0 ? sw : sw2;
    const sx = A.lerp(11, ZX1, E.inOutSine(sp));
    const sa = sp > 0 ? Math.sin(sp * Math.PI) : 0;
    this.sweepA.position.set(sx, ZY1, 0.32); this.sweepB.position.set(sx, ZY0, 0.32);
    this.sweepA.material.opacity = this.sweepB.material.opacity = 0.85 * sa;
    this.sweepA.visible = this.sweepB.visible = sa > 0.01;

    // ============================================================ fail FX
    const tf = t - T.fail;
    // shards
    this.shards.forEach((s) => {
      const v = tf > 0 && tf < s.life;
      s.m.visible = v;
      if (!v) return;
      const d = (1 - Math.exp(-tf * 3)) / 3;
      s.m.position.set(s.ox + s.vx * d, s.oy + s.vy * d - 4.5 * tf * tf, Math.max(0.05, 0.25 + s.vz * d - 3.5 * tf * tf));
      s.m.rotation.set(s.wx * tf, s.wy * tf, s.wz * tf);
      const k = 1 - A.prog(tf, s.life * 0.6, s.life);
      s.m.scale.set(s.sx * k, s.sy * k, s.sz * k);
    });
    this.shardMat.opacity = 0.85 * (1 - A.prog(tf, 0.5, 1.05));
    // glitch slices
    this.glitch.forEach((m, i) => {
      const h1 = hash(step * 7.3 + i * 3.1);
      const vis = gEnv > 0.05 && h1 > 0.3;
      m.visible = vis;
      if (!vis) return;
      const w = 1 + hash(step * 2.1 + i * 9.7) * 5.5, h = 0.05 + hash(step * 4.9 + i) * 0.26;
      m.position.set(12.5 + hash(step * 5.3 + i * 1.3) * 14, ZY0 + hash(step * 6.1 + i * 2.9) * ZH, 0.4);
      m.scale.set(w, h, 1);
      m.material.opacity = 0.7 * gEnv;
    });
    // rings, pools, glows, sparks
    this.ringAt(this.ringFail, tf, 0.55, [X(18), ZYM, 0.03], 0.4, 5.2, 0.9);
    this.ringAt(this.ringFail2, tf - 0.07, 0.5, [X(18), ZYM, 0.03], 0.3, 3.4, 0.6);
    this.ringAt(this.ringReject, t - T.reject, 0.45, [X(22), 3.8, 0.05], 0.15, 1.9, 0.8);
    this.poolFail.material.opacity = 0.55 * A.hit(t, T.fail, 0.5);
    this.poolFail.visible = this.poolFail.material.opacity > 0.002;
    this.glowFail.position.set(X(18), ZY1 - 0.2, 0.9);
    this.glowFail.material.opacity = 0.75 * A.hit(t, T.fail, 0.22);
    this.glowFail.scale.setScalar(2.4 + 3 * A.prog(tf, 0, 0.3));
    this.glowFail.visible = this.glowFail.material.opacity > 0.002;
    this.glowTip.position.set(X(18), p18, 0.85);
    this.glowTip.material.opacity = 0.8 * A.window(t, T.c18 + 0.02, T.fail + 0.14, 0.04, 0.08);
    this.glowTip.visible = this.glowTip.material.opacity > 0.002;
    this.poolLand.material.opacity = 0.5 * A.hit(t, T.land, 0.5) + 0.12 * A.hit(t, T.pill, 0.5);
    this.poolLand.visible = this.poolLand.material.opacity > 0.002;
    this.poolReject.material.opacity = 0.55 * A.hit(t, T.reject, 0.45);
    this.poolReject.visible = this.poolReject.material.opacity > 0.002;
    this.poolBreaker.material.opacity = 0.3 * A.ease(t, T.c23, T.c25 + 0.4) * (1 + 0.4 * A.hit(t, T.pill, 0.4));
    this.poolBreaker.visible = this.poolBreaker.material.opacity > 0.002;
    this.glowReject.position.set(X(22), 3.8, 0.8);
    this.glowReject.material.opacity = 0.7 * A.hit(t, T.reject, 0.22);
    this.glowReject.visible = this.glowReject.material.opacity > 0.002;
    this.sparksFail.update(t, T.fail, [X(18), ZY1, 0.4]);
    this.sparksFail2.update(t, T.fail + 0.01, [X(18), ZYM, 0.35]);
    this.sparksReject.update(t, T.reject, [X(22), 3.8, 0.5]);
    this.sparksLand.update(t, T.land, [21.5, ZY0, 0.2]);

    // box + arrow
    const boxP = E.outCubic(A.prog(t, T.reject + 0.04, T.reject + 0.38));
    this.box.setDraw(boxP);
    this.box.setOpacity(boxP > 0 ? 1 : 0);
    this.arrow.setDraw(E.outCubic(A.prog(t, T.c23 + 0.02, T.c23 + 0.7)));
    this.arrow.mat.emissiveIntensity = 0.2 + 0.5 * A.hit(t, T.c23 + 0.7, 0.3);
    this.dust.update(t);

    // ============================================================ post FX
    fx.shake = 0.24 * A.hit(t, T.fail, 0.2) + 0.05 * A.hit(t, T.land, 0.12) + 0.04 * A.hit(t, T.reject, 0.12) + 0.06 * A.hit(t, T.morph, 0.14);
    fx.flash = 0.24 * A.hit(t, T.fail, 0.09, 0.015);
    fx.flashColor = '#ff2b36';
    fx.ca = 2.1 * A.hit(t, T.fail, 0.16) + 0.8 * gEnv + 0.8 * A.hit(t, T.morph, 0.15);
    const imp = toScreen([X(18), ZYM, 0.3]);
    fx.zoom = 0.05 * A.hit(t, T.fail, 0.12);
    fx.zoomC = [imp.x / 1080, 1 - imp.y / 1920];
    fx.dir = [0, 0.016 * A.pulse(t, T.fail + 0.015, 0.08)];
    const mood = A.window(t, T.fail + 0.05, T.flipEnd, 0.4, 0.35);
    fx.saturation = 1.06 - 0.14 * mood;
    fx.vignette = 0.16 + 0.1 * mood + 0.04 * A.hit(t, T.fail, 0.3);
    fx.contrast = 1.04 + 0.03 * mood;

    // ============================================================ title
    this.updateTitle(t, ctx, step);

    // ============================================================ pills
    const pill = (e, key, anchor, tin, tout, o = {}) => {
      const st = this.pillState(t, tin, tout, o);
      if (st.opacity <= 0.001) { e.style.display = 'none'; return; }
      const p = toScreen(anchor);
      const s = st.scale * (o.scale ?? 1) / push;
      let x = p.x;
      const half = (this.pw[key] * s) / 2;
      x = Math.min(x, 945 - half); x = Math.max(x, 80 + half);
      ov.place(e, { x, y: p.y, opacity: st.opacity, scale: s, blur: st.blur, rot: o.rot ?? 0, rx: o.rx ?? 0, persp: o.rx ? 900 : 0 });
    };
    // FAILED stamp: slams down from big, squashes, holds, leaves
    {
      const tin = T.stamp - 0.07;
      const p = A.prog(t, tin, T.stamp);
      const land = A.hit(t, T.stamp, 0.12);
      const outQ = A.prog(t, 13.62, 13.74);
      const sc = (t < T.stamp ? A.lerp(2.0, 1, E.inQuad(p)) : 1 - 0.08 * land * Math.cos((t - T.stamp) * 30)) * (1 + 0.2 * outQ);
      const op = Math.min(1, p * 2.5) * (1 - outQ);
      const pa = toScreen([21.9, ZYM, 0.45]);
      if (op > 0.001) ov.place(this.pFail, { x: Math.min(pa.x, 945 - this.pw.fail / 2), y: pa.y, opacity: op, scale: sc / push, rot: -7 + 3 * (1 - p), blur: (1 - p) * 9 + outQ * 12 });
      else this.pFail.style.display = 'none';
      const rp = A.prog(t, T.stamp, T.stamp + 0.4);
      if (rp > 0 && rp < 1) ov.place(this.ringEl, { x: Math.min(pa.x, 945 - this.pw.fail / 2), y: pa.y, opacity: 0.8 * (1 - rp), scale: 0.6 + 1.6 * E.outCubic(rp), sy: 0.55 });
      else this.ringEl.style.display = 'none';
    }
    // SUPPORT -> flips over -> RESISTANCE -> rises to a tag when BREAKER BLOCK lands
    const supAnchor = [23.05, ZY1 + 0.98, 0.5];
    const flipOut = A.prog(t, T.reverse - 0.15, T.reverse);
    const flipIn = A.prog(t, T.reverse, T.reverse + 0.2);
    pill(this.pSup, 'sup', supAnchor, T.support, T.reverse + 0.5, { rx: 90 * E.inQuad(flipOut), hideAfter: T.reverse });
    if (t >= T.reverse) this.pSup.style.display = 'none';
    const resUp = E.outCubic(A.prog(t, T.pill - 0.04, T.pill + 0.26));
    const resAnchor = [23.05, ZY1 + 0.98 + 1.1 * resUp, 0.5];
    const resKick = 1 + 0.14 * A.hit(t, T.reject, 0.18);
    if (t >= T.reverse) pill(this.pRes, 'res', resAnchor, T.reverse - 1, 99, { rx: -90 * (1 - E.outBack(flipIn)), scale: resKick * A.lerp(1, 0.72, resUp) });
    else this.pRes.style.display = 'none';
    pill(this.pBrk, 'brk', [23.05, ZY1 + 0.98, 0.5], T.pill, 99, { scale: 0.92 });
  },

  // ---------------------------------------------------------------- helpers
  // Shape a candle mid-formation: body from the open to `cur`, wick lo..hi.
  form(cd, cur, hi, lo, scale = 1) {
    cd.group.visible = true;
    cd.group.scale.setScalar(scale);
    const bh = Math.max(cd.top - cd.bot, 0.08);
    const bt = Math.max(cd.o, cur), bb = Math.min(cd.o, cur);
    cd.body.visible = true;
    cd.body.scale.set(1, Math.max(0.02, (bt - bb) / bh), 1);
    cd.body.position.y = (bt + bb) / 2 - cd.mid;
    const span = Math.max(cd.h - cd.l, 0.01);
    cd.wick.visible = hi - lo > 0.01;
    cd.wick.scale.set(1, Math.max(0.01, (hi - lo) / span), 1);
    cd.wick.position.y = (hi + lo) / 2 - cd.mid;
  },
  // Zone opacity / pulse / paper-pool in the right order (setOpacity resets materials).
  zoneState(z, alpha, pulse, poolK) {
    z.reveal(1);
    z.setOpacity(alpha);
    z.pulse(pulse);
    z.slabMat.opacity *= alpha;
    z.pool.material.opacity *= alpha * poolK;
    z.group.visible = alpha > 0.001;
  },
  ringAt(m, x, life, pos, s0, s1, a0) {
    const v = x > 0 && x < life;
    m.visible = v;
    if (!v) return;
    const k = x / life;
    m.position.set(pos[0], pos[1], pos[2]);
    m.scale.setScalar(s0 + (s1 - s0) * (1 - Math.pow(1 - k, 3)));
    m.material.opacity = a0 * (1 - k) * (1 - k);
  },
  // Pill pop-in (overshoot, from blur) and quick scale/blur exit.
  pillState(t, tin, tout, { inDur = 0.3, outDur = 0.13 } = {}) {
    const p = (t - tin) / inDur;
    if (p <= 0) return { opacity: 0, scale: 0, blur: 0 };
    const q = Math.min(1, Math.max(0, (t - tout) / outDur));
    const pc = Math.min(1, p);
    const c1 = 1.9, c3 = c1 + 1;
    const ob = 1 + c3 * Math.pow(pc - 1, 3) + c1 * Math.pow(pc - 1, 2);
    return { opacity: Math.min(1, pc * 3.5) * (1 - q), scale: (0.4 + 0.6 * ob) * (1 + 0.2 * q), blur: Math.max(0, 1 - pc * 2.2) * 10 + q * 12 };
  },
  setLetter(c, { dx = 0, dy = 0, dz = 0, rx = 0, ry = 0, rz = 0, s = 1, a = 1, em = 0.08, x } = {}) {
    const h = c.holder;
    h.position.set((x ?? h.userData.baseX) + dx, dy, dz);
    h.rotation.set(rx, ry, rz);
    h.scale.setScalar(Math.max(1e-4, s));
    h.visible = a > 0.002;
    for (const m of c.mesh.material) { m.opacity = a; m.depthWrite = a > 0.98; }
    c.mesh.material[0].emissiveIntensity = em;
  },
  letterColor(c, col) {
    c.mesh.material[0].color.copy(col); c.mesh.material[0].emissive.copy(col);
    c.mesh.material[1].color.copy(col).multiplyScalar(0.45);
  },
  updateTitle(t, ctx, step) {
    const { A } = ctx; const E = A.E, T = this.T;
    const M = T.morph;
    // settle to the longer title's scale just before the new glyphs arrive, so
    // "2. BREAKER BLOCK" never exceeds x 70-1010 mid-morph
    const mk = E.inOutCubic(A.prog(t, M - 0.22, M + 0.06));
    const sc = A.lerp(1, this.kB, mk) * (1 + 0.05 * A.hit(t, M + 0.02, 0.16));
    ctx.pin(this.titleA.group, { ...TITLE_PIN, worldHeight: this.titleA.capH, scale: sc });
    ctx.pin(this.titleB.group, { ...TITLE_PIN, worldHeight: this.titleB.capH, scale: sc });
    // fail: shake, glitch jitter and a red tint
    const sh = A.hit(t, T.fail, 0.3);
    const gEnv = A.window(t, T.fail - 0.005, T.fail + 0.3, 0.01, 0.12);
    const tint = A.kf(t, [[T.fail - 0.02, 0], [T.fail + 0.03, 1, E.outQuad], [T.fail + 0.35, 1], [T.fail + 0.85, 0, E.inOutSine]]);
    const base = this.tmpC2.copy(this.cMaroon).lerp(this.cRed, tint * 0.85);
    const shx = A.noise1(t * 55, 9) * 0.09 * sh, shy = A.noise1(t * 61, 10) * 0.06 * sh;
    // light sweep across the new title after the morph
    const swp = A.prog(t, M + 0.12, M + 0.7);
    const half = this.titleB.width / 2 + 0.8;
    const sweepX = A.lerp(-half, half, E.inOutSine(swp));
    const sweepA = swp > 0 && swp < 1 ? 1 : 0;
    const em = (x) => 0.08 + 0.9 * sweepA * Math.exp(-Math.pow((x - sweepX) / 0.55, 2));
    const jit = (i) => (gEnv > 0.05 ? { dx: (hash(step * 3.3 + i) - 0.5) * 0.12 * gEnv, dy: (hash(step * 5.1 + i * 2) - 0.5) * 0.09 * gEnv } : { dx: 0, dy: 0 });
    const a = this.mA, b = this.mB;
    const D2R = Math.PI / 180;
    // digit: split-flap flip 1 -> 2
    {
      const p = A.prog(t, M - 0.02, M + 0.12);
      const j = jit(0);
      this.letterColor(a.digit, base);
      this.setLetter(a.digit, { dx: j.dx + shx, dy: j.dy + shy + 0.12 * p, rx: 90 * D2R * E.inQuad(p), a: 1 - A.prog(p, 0.7, 1) });
      const q = A.prog(t, M + 0.08, M + 0.38);
      this.letterColor(b.digit, this.tmpC.copy(this.cRed).lerp(this.cMaroon, A.prog(t, M + 0.25, M + 0.7)));
      this.setLetter(b.digit, { rx: -95 * D2R * (1 - E.outBack(q)), a: Math.min(1, q * 4), em: em(b.digit.x) });
    }
    // dot and BLOCK glide from the old layout to the new one (shared glyphs)
    const glide = (ca, cb, d, i) => {
      const e = E.outExpo(A.prog(t, M + d, M + d + 0.42));
      const j = jit(i);
      this.letterColor(ca, base);
      const x = A.lerp(ca.holder.userData.baseX, cb.holder.userData.baseX, e);
      this.setLetter(ca, { x, dx: j.dx + shx, dy: j.dy + shy + 0.07 * Math.sin(Math.PI * e), a: 1, em: em(x) });
      this.setLetter(cb, { a: 0 });
    };
    glide(a.dot, b.dot, 0, 1);
    a.block.forEach((c, i) => glide(c, b.block[i], 0.02 + (4 - i) * 0.018, 7 + i));
    // ORDER scatters out
    a.order.forEach((c, i) => {
      const d = M + i * 0.022;
      const p = A.prog(t, d, d + 0.26);
      const e = E.outCubic(p);
      const j = jit(2 + i);
      this.letterColor(c, base);
      this.setLetter(c, {
        dx: j.dx + shx + (i - 2) * 0.14 * e, dy: j.dy + shy + 0.6 * e + (hash(i + 1) - 0.5) * 0.3 * e, dz: 1.0 * e,
        rx: 75 * D2R * e, rz: (hash(i + 5) - 0.5) * 60 * D2R * e, s: 1 - 0.45 * e, a: 1 - A.prog(p, 0.2, 0.8),
      });
    });
    // BREAKER flips in, red-hot, cooling to maroon
    b.breaker.forEach((c, i) => {
      const d = M + 0.07 + i * 0.032;
      const q = A.prog(t, d, d + 0.3);
      const e = E.outBack(q);
      this.letterColor(c, this.tmpC.copy(this.cRed).lerp(this.cMaroon, A.prog(t, d + 0.15, d + 0.65)));
      this.setLetter(c, { dy: -0.3 * (1 - E.outCubic(q)), rx: -100 * D2R * (1 - e), s: 0.6 + 0.4 * e, a: Math.min(1, q * 3.5), em: em(c.x) });
    });
  },
};
