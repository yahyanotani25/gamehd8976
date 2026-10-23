// Scene s1 — Hook: "Smart Money Concepts ko samajhna chahte hain?" (0.00–2.45).
//
// Opens mid-motion (camera rushing back off the paper, zoom blur easing out)
// over a dimmed bullish chart rising diagonally. The 3D words SMART / MONEY /
// CONCEPTS slam down from in front of the camera onto the paper, one per
// spoken word (shake + blur pulse + shockwave ring + dust on each landing),
// a light sweep runs across them, a gold 3D "?" springs in on "hain?", and
// the camera pushes hard into the paper into the 2.45 zoom cut.

// background chart: candles 0–7 already there, 8–17 keep forming
const BG_N = 18;
const BG_X0 = -8.5;
const bgTime = (i) => (i < 8 ? -1 : 0.04 + (i - 8) * 0.2);

// word layout in world units (camera centred on (0, 0), ~80 px per unit)
const WORDS = [
  { str: 'SMART', word: 'Smart', y: 7.35, cap: 1.82, maxW: 9.6, z: 0.75, flight: 0.14, rotZ: -0.16, seed: 11 },
  { str: 'MONEY', word: 'Money', y: 4.95, cap: 1.82, maxW: 9.6, z: 0.75, flight: 0.16, rotZ: 0.14, seed: 23 },
  { str: 'CONCEPTS', word: 'Concepts', y: 2.35, cap: 2.1, maxW: 10.1, z: 0.95, flight: 0.16, rotZ: 0, seed: 37 },
];
const Q = { y: -2.55, cap: 3.15, z: 1.0 };

export default {
  id: 's1', start: 0, end: 2.45,
  cues: [
    { t: 0.10, sfx: 'whoosh' },                    // camera rushes back off the paper
    { t: 0.14, sfx: 'impact' },                    // SMART lands
    { t: 0.36, sfx: 'whoosh', gain: -14 },         // MONEY flies in
    { t: 0.48, sfx: 'impact', pitch: -1 },         // MONEY lands
    { t: 0.58, sfx: 'whoosh', gain: -14 },         // CONCEPTS flies in
    { t: 0.68, sfx: 'impact', pitch: -2 },         // CONCEPTS lands (biggest)
    { t: 0.68, sfx: 'shimmer' },                   // CONCEPTS gleam + gold sparks
    { t: 0.84, sfx: 'swipe', gain: -9 },           // gold underline draws under CONCEPTS
    { t: 1.05, sfx: 'shimmer', gain: -8 },         // light sweep across the words
    { t: 1.02, sfx: 'grow', gain: -16 },           // background candles keep forming
    { t: 1.42, sfx: 'grow', gain: -16, pitch: 1 },
    { t: 1.82, sfx: 'grow', gain: -16, pitch: 2 },
    { t: 2.02, sfx: 'pop' },                       // 3D question mark springs in
    { t: 2.05, sfx: 'blip', gain: -10, pitch: 3 }, // gold sparks around the "?"
    { t: 2.45, sfx: 'riser', gain: -4 },           // build ending at the cut
    { t: 2.45, sfx: 'whoosh' },                    // hard push into the paper, peak at the cut
  ],

  init(ctx) {
    const { kit, PAL, group, THREE, A } = ctx;
    this.T = THREE;

    // ---------------- background chart (dimmed, flat, no shadows)
    const r = A.rng(9);
    const data = [];
    let p = -11.2;
    for (let i = 0; i < BG_N; i++) {
      const red = i % 4 === 2 || i === 11;
      const o = p;
      const c = red ? o - (0.55 + r() * 0.35) : o + (1.55 + r() * 0.85);
      const h = Math.max(o, c) + 0.2 + r() * 0.35;
      const l = Math.min(o, c) - 0.2 - r() * 0.35;
      data.push({ o, h, l, c });
      p = c;
    }
    this.bg = kit.chart({ data, x0: BG_X0, step: 1.0, width: 0.6, depth: 0.3 });
    this.bg.group.traverse((o) => { if (o.isMesh) o.castShadow = false; });
    group.add(this.bg.group);
    // a soft green light pool that rides the newest forming candle
    this.pool = kit.paperGlow({ color: PAL.green, w: 2.2, h: 4, opacity: 0.22 });
    group.add(this.pool);

    // ---------------- 3D words
    this.words = WORDS.map((w, wi) => {
      const green = wi === 2;
      const tx = kit.text3d(w.str, {
        font: 'bebas', size: 2.6, depth: green ? 0.5 : 0.42, bevel: 0.035, tracking: 0.035,
        color: green ? PAL.green : PAL.maroon, side: green ? '#05592a' : PAL.maroonSide, emissive: 0.08,
      });
      const fit = Math.min(w.cap / tx.capH, w.maxW / tx.width);
      const outer = new THREE.Group();
      const inner = new THREE.Group();
      inner.scale.setScalar(fit);
      inner.add(tx.group);
      outer.add(inner);
      group.add(outer);
      const base = new THREE.Color(green ? PAL.green : PAL.maroon);
      const lit = green ? new THREE.Color('#7dffb0') : new THREE.Color('#e0384a');
      // shockwave ring on the paper
      const ring = new THREE.Mesh(
        new THREE.RingGeometry(0.93, 1.0, 96),
        new THREE.MeshBasicMaterial({ color: new THREE.Color(green ? PAL.green : PAL.ink), transparent: true, opacity: 0, depthWrite: false }),
      );
      ring.position.set(0, w.y, 0.02);
      group.add(ring);
      const sp = kit.sparks({ count: green ? 40 : 26, color: green ? PAL.gold : '#aeb5c2', size: green ? 0.24 : 0.2, speed: green ? 7 : 5.5, life: 0.6, seed: w.seed });
      group.add(sp.group);
      return { ...w, tx, outer, inner, fit, base, lit, ring, sp, L: ctx.wt(w.word), W: tx.width * fit };
    });

    // gold underline under CONCEPTS
    const cw = this.words[2];
    const uy = cw.y - cw.cap / 2 - 0.5;
    this.under = kit.stroke([[-cw.W / 2 + 0.2, uy, 0.35], [cw.W / 2 - 0.2, uy, 0.35]], { color: PAL.gold, radius: 0.075 });
    group.add(this.under.group);

    // ---------------- 3D question mark
    const q = kit.text3d('?', { font: 'bebas', size: 4, depth: 0.6, bevel: 0.05, color: PAL.gold, side: '#8a4f00', emissive: 0.12 });
    this.q = q;
    this.qFit = Q.cap / q.capH;
    this.qOuter = new THREE.Group();
    this.qInner = new THREE.Group();
    this.qInner.scale.setScalar(this.qFit);
    this.qInner.add(q.group);
    this.qOuter.add(this.qInner);
    this.qOuter.position.set(0, Q.y, Q.z);
    group.add(this.qOuter);
    this.qPool = kit.paperGlow({ color: PAL.gold, w: 2.6, h: 3.4, opacity: 0.4 });
    this.qPool.position.set(0, Q.y, 0.006);
    group.add(this.qPool);
    this.qSparks = kit.sparks({ count: 36, color: PAL.gold, size: 0.22, speed: 6.5, life: 0.7, seed: 51 });
    group.add(this.qSparks.group);
    this.qAt = ctx.wt('hain', 1);

    // ---------------- dust
    this.dust = kit.dust({ count: 70, w: 22, h: 30, zMin: 2, zMax: 16, size: 0.16, seed: 21, opacity: 0.55 });
    group.add(this.dust.group);
  },

  update(t, lt, ctx) {
    const { A, cam, fx, kit } = ctx;
    const E = A.E;
    const N = (s, f = 0.6) => A.noise1(t * f, s);

    // ---------------- camera: rush back -> slow orbit/push -> hard push
    const dolly = A.kf(t, [[0, 0.3], [0.62, 1.0, E.outCubic], [2.22, 0.9, E.inOutSine], [2.45, 0.38, E.inCubic]]);
    const pitch = A.kf(t, [[0, -22], [0.7, -10, E.outCubic], [2.22, -6.5, E.inOutSine], [2.45, -3, E.inCubic]]) + N(1, 0.5) * 1.2;
    const yaw = A.kf(t, [[0, 11], [0.7, 3.5, E.outCubic], [2.22, -3.5, E.inOutSine]]) + N(2, 0.45) * 1.2;
    const roll = A.kf(t, [[0, -7], [0.65, 0, E.outCubic]]) + N(3, 0.4) * 0.5;
    const cy = A.kf(t, [[0, -1.2], [0.7, 0, E.outCubic], [2.22, 0.15], [2.45, -0.6, E.inCubic]]) + N(4, 0.35) * 0.12;
    const cx = N(5, 0.3) * 0.12;
    cam.frame({ cx, cy, width: 13.5, pitch, yaw, roll, dolly });
    const camPos = cam.state.pos;

    // ---------------- post: opening blur, landing pulses, push into the cut
    const open = 1 - A.ease(t, 0, 0.5, E.outCubic);
    let zoom = 0.26 * open, ca = 2.2 * open, shake = 0, flash = 0;
    for (const w of this.words) {
      const h = A.hit(t, w.L, 0.1);
      shake += (w === this.words[2] ? 0.26 : 0.18) * h;
      zoom += 0.06 * h + 0.035 * A.window(t, w.L - w.flight, w.L, 0.04, 0.02);
      ca += 1.2 * h;
    }
    flash += 0.16 * A.hit(t, this.words[2].L, 0.12);
    shake += 0.07 * A.hit(t, this.qAt, 0.12);
    const push = A.ease(t, 2.24, 2.45, E.inCubic);
    zoom += 0.12 * push; ca += 1.2 * push;
    fx.zoom = zoom; fx.ca = ca; fx.shake = shake; fx.flash = flash;

    // ---------------- background chart
    const times = [];
    for (let i = 0; i < BG_N; i++) times.push(bgTime(i));
    this.bg.animate(t, times, { dur: 0.34, mode: 'grow' });
    const bgA = A.lerp(0.5, 0.3, A.ease(t, 0, 0.7));
    this.bg.candles.forEach((c) => c.setOpacity(bgA));
    let cur = 7;
    for (let i = 8; i < BG_N; i++) if (t >= bgTime(i)) cur = i;
    const cc = this.bg.candles[cur];
    const since = t - (cur < 8 ? -1 : bgTime(cur));
    this.pool.position.set(BG_X0 + cur, cc.mid, 0.006);
    kit.setOpacity(this.pool, 0.55 + 0.45 * Math.exp(-since * 4));

    // ---------------- words
    const sweepP = A.ease(t, 0.95, 1.6, E.inOutSine);
    const sweepOn = A.window(t, 0.92, 1.65, 0.08, 0.1);
    for (const w of this.words) {
      const t0 = w.L - w.flight;
      const { outer, tx } = w;
      if (t < t0) {
        outer.visible = false; w.ring.visible = false; w.sp.update(t, w.L);
        continue;
      }
      outer.visible = true;
      const p = A.prog(t, t0, w.L);
      const land = [0, w.y, w.z];
      // slam down the view ray from in front of the camera onto the paper
      const s = 0.62 * (1 - E.inCubic(p));
      const settle = t > w.L ? 1 : 0;
      const fz = settle * (0.05 * N(w.seed, 0.8));
      outer.position.set(
        A.lerp(land[0], camPos[0], s),
        A.lerp(land[1], camPos[1], s),
        A.lerp(land[2], camPos[2], s) + fz,
      );
      outer.rotation.set((1 - E.outQuad(p)) * 0.55 + settle * N(w.seed + 1, 0.5) * 0.02, settle * N(w.seed + 2, 0.5) * 0.03, w.rotZ * (1 - E.outCubic(p)));
      tx.setOpacity(A.ease(t, t0, t0 + w.flight * 0.4, E.outQuad));

      // landing ripple per letter + light sweep
      tx.chars.forEach((c, i) => {
        const dt = t - w.L - i * 0.016;
        const b = dt > 0 ? Math.exp(-dt * 9) * Math.sin(dt * 30) : 0;
        const sq = dt > 0 ? Math.exp(-dt * 16) : 0;
        const wx = c.holder.userData.baseX * w.fit;
        const sx = A.lerp(-w.W / 2 - 3.5, w.W / 2 + 3.5, sweepP) + (w.y - 4.9) * 0.6;
        const k = sweepOn * Math.exp(-(((wx - sx) / 1.1) ** 2));
        c.holder.position.z = Math.max(-0.1, b) * 0.45 / w.fit + (k * 0.32) / w.fit;
        c.holder.scale.set(1 + 0.12 * sq, 1 - 0.24 * sq + 0.04 * k, 1 - 0.3 * sq);
        c.holder.rotation.x = -0.12 * k;
        const m = c.mesh.material[0];
        m.color.copy(w.base).lerp(w.lit, k * 0.85);
        m.emissive.copy(m.color);
        m.emissiveIntensity = 0.08 + 0.55 * k + 0.35 * sq;
      });

      // shockwave ring + dust burst
      const rp = A.prog(t, w.L, w.L + 0.5);
      w.ring.visible = t >= w.L && rp < 1;
      const g = A.lerp(0.35, 1.0, E.outExpo(rp));
      w.ring.scale.set((w.W / 2 + 1.2) * g, (w.cap / 2 + 0.9) * g, 1);
      w.ring.material.opacity = 0.42 * (1 - rp) * (1 - rp);
      w.sp.update(t, w.L, [0, w.y - w.cap * 0.45, 0.4]);
    }

    // underline under CONCEPTS
    this.under.setDraw(A.ease(t, 0.8, 1.05, E.outExpo));

    // ---------------- question mark
    const qa = this.qAt;
    const sp = A.spring(t, qa, { freq: 2.3, damp: 0.36 });
    this.qOuter.visible = t >= qa;
    if (t >= qa) {
      const x = t - qa;
      this.qInner.scale.setScalar(this.qFit * Math.max(0.001, sp));
      this.qOuter.position.set(0, Q.y + (1 - A.ease(t, qa, qa + 0.25, E.outBack)) * 1.6, Q.z + 0.08 * N(77, 0.9));
      this.qOuter.rotation.set(0, -(1 - E.outExpo(A.clamp(x / 0.45))) * 2.4, Math.exp(-x * 5) * Math.sin(x * 22) * 0.18);
    }
    kit.setOpacity(this.qPool, A.ease(t, qa, qa + 0.2) * (0.75 + 0.25 * A.hit(t, qa + 0.05, 0.3)));
    this.qPool.scale.set(2.6 * 1.6 * (0.6 + 0.4 * sp), 3.4 * 1.6 * (0.6 + 0.4 * sp), 1);
    this.qSparks.update(t, qa + 0.03, [0, Q.y, 1.2]);

    this.dust.update(t);
  },
};
