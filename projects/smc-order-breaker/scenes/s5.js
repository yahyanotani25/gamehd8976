// Scene s5 — Outro (24.90–31.00). See docs/STORYBOARD.md.
//
// "In concepts par mastery hasil karein aur zyada behtar trading decisions lein!"
// Beats: 3D chips ORDER BLOCK + BREAKER BLOCK fly in and stack; a huge gold
// 3D MASTERY slams in at 26.05 (light sweep, gold spark burst, shockwave,
// crown); the chips exit, a row of green candles grows up across the lower
// main band with a big green arrow; BETTER / TRADING / DECISIONS stack in with
// a green 3D check badge; final pulse + sparks at 29.30; slow push-in and
// float; fade to white 30.55–31.00.
//
// All titles/words are real 3D objects pinned to the screen (ctx.pin) and
// zoomed with the camera's push (pushS) so the layout bands stay exact while
// everything moves together.

const N_CANDLES = 8;
const CANDLE_T = [27.37, 27.62, 27.86, 28.11, 28.35, 28.60, 28.84, 29.06];
const CANDLES = Array.from({ length: N_CANDLES }, (_, i) => {
  const o = -5.3 + i * 0.4;
  const c = o + 0.95 + 0.14 * Math.sin(i * 1.7);
  return { o, c, h: c + 0.18 + 0.08 * (i % 2), l: o - 0.2 - 0.07 * ((i + 1) % 2), x: -4.55 + i * 1.3 };
});
const ARROW_FROM = [-5.6, -3.75, 1.15], ARROW_TO = [4.6, -0.95, 1.15];

// screen layout (px, before the push zoom)
const L = {
  chipA: { x: 540, y: 838, h: 96 },
  chipB: { x: 540, y: 948, h: 96 },
  mastery: { x: 540, y: 482, h: 205 },
  crown: { x: 540, y: 300, h: 92 },
  better: { x: 322, y: 765, h: 76 },
  trading: { x: 322, y: 862, h: 100 },
  decisions: { x: 322, y: 975, h: 100 },
  check: { x: 188, y: 868, h: 176 },
};
const T = {
  chipA: [25.12, 25.44], chipB: [25.32, 25.56],
  slam: 26.05, crown: 26.32, karein: 26.81, chipsOut: 27.22,
  better: 28.01, trading: 28.37, decisions: 28.67, check: 28.90, final: 29.30,
  arrow: [27.45, 29.12],
};

export default {
  id: 's5', start: 24.90, end: 31.00,
  cues: [
    // chips fly in and stack
    { t: 25.24, sfx: 'swipe', gain: -5 },
    { t: 25.36, sfx: 'swipe' },
    { t: 25.44, sfx: 'pop', gain: -3, pitch: -2 },
    { t: 25.55, sfx: 'pop' },
    // MASTERY slam
    { t: 25.96, sfx: 'whoosh', gain: -6 },
    { t: 26.05, sfx: 'impact', gain: 2 },
    { t: 26.05, sfx: 'shimmer' },
    { t: 26.32, sfx: 'pop', gain: -3, pitch: 5 },          // crown pops
    { t: 26.81, sfx: 'blip', gain: -8, pitch: 3 },         // chips flash gold on "karein"
    { t: 27.24, sfx: 'swipe', gain: -5 },                  // chips exit
    // candles grow up (pitch stepping up)
    ...CANDLE_T.map((t, i) => ({ t, sfx: 'pop', gain: -4, pitch: i })),
    { t: 27.50, sfx: 'swipe', gain: -6, pitch: 2 },        // arrow starts drawing
    // words stack in
    { t: 28.01, sfx: 'impact' },
    { t: 28.37, sfx: 'impact', pitch: 1 },
    { t: 28.67, sfx: 'impact', pitch: 2 },
    { t: 28.90, sfx: 'ding', gain: -2 },                   // green check badge
    // final pulse
    { t: 29.25, sfx: 'riser', gain: -9 },
    { t: 29.30, sfx: 'final' },
    { t: 29.34, sfx: 'shimmer', gain: -5 },
  ],

  init(ctx) {
    const { THREE, kit, PAL, group, ov } = ctx;
    this.cSheen = new THREE.Color('#fff4c9');
    this.cGold = new THREE.Color(PAL.gold);
    this.cWhite = new THREE.Color('#ffffff');
    this.cTmp = new THREE.Color();

    // pinned holder: outer is pinned, inner is animated in local units
    const mkPinned = (obj) => {
      const outer = new THREE.Group(), inner = new THREE.Group();
      outer.add(inner); inner.add(obj); group.add(outer);
      return { outer, inner };
    };

    // ---------------------------------------------------------- chips
    const mkChip = (label, color, deep) => {
      const txt = kit.text3d(label, { font: 'montserrat800', size: 0.5, depth: 0.07, bevel: 0.012, color: '#ffffff', side: deep, tracking: 0.06, emissive: 0.25 });
      const w = txt.width + 1.0, h = 1.0;
      const card = kit.card({ w, h, r: 0.5, depth: 0.28, color });
      card.mesh.material.emissive = new THREE.Color(color);
      card.mesh.material.emissiveIntensity = 0.22;
      card.mesh.material.roughness = 0.28;
      card.mesh.material.clearcoat = 1;
      txt.group.position.set(0, 0, 0.36);
      const body = new THREE.Group();
      body.add(card.group, txt.group);
      const pinned = mkPinned(body);
      return { ...pinned, card, txt, w, h, base: new THREE.Color(color) };
    };
    this.chipA = mkChip('ORDER BLOCK', PAL.green, PAL.greenDeep);
    this.chipB = mkChip('BREAKER BLOCK', PAL.red, PAL.redDeep);

    // ---------------------------------------------------------- MASTERY
    this.mastery = kit.text3d('MASTERY', { font: 'bebas', size: 1, depth: 0.42, bevel: 0.035, color: PAL.gold, side: PAL.goldDeep, emissive: 0.2, rough: 0.22, tracking: 0.04 });
    this.mPin = mkPinned(this.mastery.group);
    this.mGlow = kit.glow({ color: PAL.gold, size: 1, opacity: 0.5 });
    this.mGlow.position.set(0, 0, -0.35);
    this.mPin.inner.add(this.mGlow);
    this.crown = kit.svgIcon(ov.ICON3D.crown, { size: 1, depth: 0.22, color: PAL.gold });
    this.crown.mesh.material.emissiveIntensity = 0.22;
    this.cPin = mkPinned(this.crown.group);

    // ---------------------------------------------------------- words
    const mkWord = (s, color, side) => {
      const tx = kit.text3d(s, { font: 'bebas', size: 1, depth: 0.32, bevel: 0.03, color, side, align: 'left', tracking: 0.03, emissive: 0.12 });
      return { tx, ...mkPinned(tx.group) };
    };
    this.wBetter = mkWord('BETTER', PAL.maroon, PAL.maroonSide);
    this.wTrading = mkWord('TRADING', PAL.green, PAL.greenDeep);
    this.wDecisions = mkWord('DECISIONS', PAL.green, PAL.greenDeep);
    // keep every word inside x 322..850
    for (const [w, k] of [[this.wBetter, 'better'], [this.wTrading, 'trading'], [this.wDecisions, 'decisions']]) {
      const wpx = (w.tx.width / w.tx.capH) * L[k].h;
      w.h = wpx > 528 ? (L[k].h * 528) / wpx : L[k].h;
    }

    // ---------------------------------------------------------- check badge
    const badge = new THREE.Group();
    const disc = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 0.34, 64), kit.glossy(PAL.green, { emissive: 0.2, rough: 0.25 }));
    disc.rotation.x = Math.PI / 2; disc.position.z = 0.17; disc.castShadow = true;
    const rim = new THREE.Mesh(new THREE.TorusGeometry(1, 0.07, 14, 72), kit.glossy('#ffffff', { emissive: 0.1 }));
    rim.position.z = 0.34; rim.castShadow = true;
    const chk = kit.svgIcon(ov.ICON3D.check, { size: 1.15, depth: 0.16, color: '#ffffff' });
    chk.group.position.set(0, -0.02, 0.36);
    badge.add(disc, rim, chk.group);
    this.badgeGlow = kit.glow({ color: PAL.green, size: 3.6, opacity: 0.45 });
    this.badgeGlow.position.z = -0.2;
    badge.add(this.badgeGlow);
    this.bPin = mkPinned(badge);

    // ---------------------------------------------------------- candles + arrow
    this.candles = CANDLES.map((d) => {
      const c = kit.candle({ ...d, width: 0.74, depth: 0.66, color: PAL.green });
      group.add(c.group);
      return c;
    });
    this.arrow = kit.arrow(ARROW_FROM, ARROW_TO, { color: PAL.green, radius: 0.13, head: 0.8 });
    group.add(this.arrow.group);
    this.arrowGlow = kit.glow({ color: PAL.green, size: 2.2, opacity: 0.5 });
    group.add(this.arrowGlow);
    this.greenPool = kit.paperGlow({ color: PAL.zoneGreen, w: 11, h: 4.5, opacity: 0.22 });
    this.greenPool.position.set(0, -3.4, 0.006);
    group.add(this.greenPool);

    // ---------------------------------------------------------- light pools, rings, sparks
    this.goldPool = kit.paperGlow({ color: PAL.gold, w: 9, h: 3.4, opacity: 0.3 });
    group.add(this.goldPool);
    const ringGeo = new THREE.RingGeometry(0.93, 1, 96);
    const mkRing = (color) => {
      const m = new THREE.Mesh(ringGeo, new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide }));
      group.add(m);
      return m;
    };
    this.slamRings = [mkRing(PAL.gold), mkRing(PAL.goldDeep)];
    this.finalRings = [mkRing(PAL.green), mkRing(PAL.gold)];
    this.wordRings = [mkRing(PAL.green), mkRing(PAL.green), mkRing(PAL.green)];
    this.slamSparks = kit.sparks({ count: 110, color: PAL.gold, size: 0.26, speed: 13, life: 1.15, seed: 51 });
    this.slamSparks2 = kit.sparks({ count: 40, color: '#ffe08a', size: 0.17, speed: 7, life: 0.9, seed: 52 });
    this.finalSparksG = kit.sparks({ count: 70, color: PAL.green, size: 0.22, speed: 11, life: 1.1, seed: 53 });
    this.finalSparksY = kit.sparks({ count: 80, color: PAL.gold, size: 0.22, speed: 12, life: 1.2, seed: 54 });
    this.tipSparks = kit.sparks({ count: 36, color: PAL.green, size: 0.18, speed: 6, life: 0.8, seed: 55, spread: Math.PI * 1.2, dir: Math.PI / 4 });
    for (const s of [this.slamSparks, this.slamSparks2, this.finalSparksG, this.finalSparksY, this.tipSparks]) group.add(s.group);

    // ---------------------------------------------------------- glints
    const star = starTexture(THREE);
    this.glints = [[-0.38, 0.32, 26.62], [0.12, -0.3, 26.78], [0.42, 0.34, 26.95], [-0.15, 0.36, 29.55], [0.35, -0.25, 29.75]].map(([fx, fy, t0]) => {
      const m = new THREE.SpriteMaterial({ map: star, color: '#ffffff', transparent: true, opacity: 0, depthWrite: false });
      const s = new THREE.Sprite(m);
      this.mPin.inner.add(s);
      s.position.set(fx * this.mastery.width, fy * this.mastery.capH * 1.4, 0.55);
      return { s, t0 };
    });

    // ---------------------------------------------------------- depth dust + gold glitter
    this.dust = kit.dust({ count: 44, w: 22, h: 32, zMin: 1.5, zMax: 9, size: 0.09, cx: 0, cy: 0, seed: 61, opacity: 0.36 });
    this.glitter = kit.dust({ count: 38, w: 16, h: 24, zMin: 1, zMax: 7, size: 0.15, color: PAL.gold, cx: 0, cy: 1, seed: 62, opacity: 0.7 });
    group.add(this.dust.group, this.glitter.group);
  },

  // ------------------------------------------------------------------ camera
  camera(t, ctx) {
    const { A, cam } = ctx;
    const E = A.E;
    let dolly = A.kf(t, [[24.9, 1.5], [25.3, 1.0, E.outExpo], [27.3, 0.975, E.inOutSine], [29.3, 0.955, E.inOutSine], [31.0, 0.915, E.inOutSine]]);
    dolly -= 0.03 * A.hit(t, T.slam, 0.3) + 0.012 * (A.hit(t, T.better, 0.2) + A.hit(t, T.trading, 0.2) + A.hit(t, T.decisions, 0.2)) + 0.035 * A.hit(t, T.final, 0.35);
    const pitch = A.kf(t, [[24.9, -14], [25.4, -9, E.outCubic], [27.4, -8], [31, -6]]) + A.noise1(t * 0.35, 21) * 0.8;
    const yaw = A.kf(t, [[24.9, -6], [25.4, -3, E.outCubic], [27.4, 2.5], [29.3, -1.5], [31, 1.5]]) + A.noise1(t * 0.3, 22) * 0.9;
    const roll = A.noise1(t * 0.25, 23) * 0.35 + 1.2 * (1 - E.outExpo(A.prog(t, 24.9, 25.4)));
    cam.frame({
      cx: A.noise1(t * 0.4, 24) * 0.06, cy: A.noise1(t * 0.37, 25) * 0.05,
      width: 13.5, pitch, yaw, roll, dolly, fov: 28,
    });
    this.pushS = 1 / dolly;
  },

  // pin with the camera push applied (zoom about the frame centre) + float
  pinAt(ctx, obj, x, y, hPx, worldH, { z = 0.6, seed = 0, float = 1 } = {}) {
    const { A } = ctx;
    const t = this.t;
    const S = this.pushS;
    const fy = float * (A.noise1(t * 0.45 + seed * 3.1, 30 + seed) * 4 + Math.sin(t * 1.6 + seed) * 2);
    const fx2 = float * A.noise1(t * 0.38 + seed * 1.7, 40 + seed) * 2.5;
    return ctx.pin(obj, { x: 540 + (x - 540) * S + fx2, y: 960 + (y - 960) * S + fy, z, heightPx: hPx * S, worldHeight: worldH });
  },

  update(t, lt, ctx) {
    const { A, fx, THREE } = ctx;
    const E = A.E;
    this.t = t;

    // ---------------------------------------------------------- grade + camera
    fx.contrast = 1.06; fx.saturation = 1.1; fx.vignette = 0.2;
    fx.shake = 0.13 * A.hit(t, T.slam, 0.2) + 0.04 * (A.hit(t, T.better, 0.12) + A.hit(t, T.trading, 0.12) + A.hit(t, T.decisions, 0.12)) + 0.08 * A.hit(t, T.final, 0.22);
    fx.ca = 0.9 * A.hit(t, T.slam, 0.16) + 0.6 * A.hit(t, T.final, 0.18);
    fx.flash = 0.22 * A.hit(t, T.slam, 0.12) + 0.14 * A.hit(t, T.final, 0.14);
    fx.flashColor = '#fff6dc';
    // radial zoom streak as MASTERY rushes in
    fx.zoom = 0.07 * A.window(t, 25.9, 26.08, 0.08, 0.04);
    fx.zoomC = [0.5, 0.75];
    fx.fade = E.inOutSine(A.prog(t, 30.55, 31.0));
    this.camera(t, ctx);
    const finalK = A.hit(t, T.final, 0.28);

    // ---------------------------------------------------------- chips
    const chip = (c, lay, [t0, t1], fromX, rotZ, seed, outDir) => {
      const p = A.prog(t, t0, t1);
      const vis = t >= t0 && t < T.chipsOut + 0.3;
      c.outer.visible = vis;
      if (!vis) return;
      const e = E.outCubic(p);
      const land = A.prog(t, t1, t1 + 0.4);
      const settle = Math.exp(-land * 5) * Math.sin(land * 18) * (land > 0 ? 1 : 0);
      let x = A.lerp(fromX, lay.x, e);
      let y = lay.y;
      // the first chip gets nudged when the second one lands
      if (c === this.chipA) y -= 8 * A.hit(t, T.chipB[1], 0.12) * (t > T.chipB[1] - 0.03 ? 1 : 0);
      // exit
      const q = E.inCubic(A.prog(t, T.chipsOut, T.chipsOut + 0.26));
      x += outDir * 900 * q;
      const pos = this.pinAt(ctx, c.outer, x, y, lay.h * (1 - 0.25 * q), c.h, { z: 0.55, seed });
      c.inner.rotation.set(
        THREE.MathUtils.degToRad(-14 * (1 - e) + 4 * settle),
        THREE.MathUtils.degToRad(-Math.sign(fromX - 540) * (70 * (1 - e) + 6 * settle) + outDir * 40 * q),
        THREE.MathUtils.degToRad(rotZ + -Math.sign(fromX - 540) * 10 * (1 - e)));
      c.inner.position.z = 1.6 * (1 - e) + 0.15 * A.hit(t, T.slam, 0.2);
      c.inner.scale.setScalar(1 + 0.05 * Math.max(0, settle) + 0.06 * A.hit(t, T.slam + 0.02, 0.15));
      const a = E.outCubic(A.prog(t, t0, t0 + 0.1)) * (1 - A.prog(t, T.chipsOut + 0.12, T.chipsOut + 0.26));
      kitOpacity(c.outer, a);
      // gold flash on "karein" + mastery slam
      const g = 0.8 * A.hit(t, T.karein, 0.3) * (t > T.karein - 0.03 ? 1 : 0) + 0.35 * A.hit(t, T.slam, 0.25);
      this.cTmp.copy(c.base).lerp(this.cGold, Math.min(1, g));
      c.card.mesh.material.emissive.copy(this.cTmp);
      c.card.mesh.material.emissiveIntensity = 0.22 + 0.5 * g;
      return pos;
    };
    chip(this.chipA, L.chipA, T.chipA, -420, -1.8, 1, -1);
    chip(this.chipB, L.chipB, T.chipB, 1500, 1.4, 2, 1);

    // ---------------------------------------------------------- MASTERY slam
    const m = this.mastery;
    const mIn = A.prog(t, 25.88, T.slam);
    const mVis = t >= 25.88;
    this.mPin.outer.visible = mVis;
    if (mVis) {
      const post = Math.max(0, t - T.slam);
      const squash = t >= T.slam ? Math.exp(-post / 0.11) * Math.cos(post * 34) * 0.14 : 0;
      const kick = 0.05 * finalK;
      const mp = this.pinAt(ctx, this.mPin.outer, L.mastery.x, L.mastery.y, L.mastery.h, m.capH, { z: 0.7, seed: 3 });
      const ein = E.inCubic(mIn);
      this.mPin.inner.position.set(0, 0, A.lerp(7, 0, ein));
      this.mPin.inner.rotation.set(THREE.MathUtils.degToRad(A.lerp(-22, 0, ein)), 0, THREE.MathUtils.degToRad(A.lerp(4, 0, ein)));
      const s0 = A.lerp(1.5, 1, ein);
      this.mPin.inner.scale.set(s0 * (1 + squash + kick), s0 * (1 - squash * 0.8 + kick), 1 + kick);
      kitOpacity(this.mastery.group, E.outCubic(A.prog(t, 25.88, 25.96)));
      // light sweep across the letters, again on the final pulse
      const sweepA = A.lerp(-0.75, 0.75, E.inOutSine(A.prog(t, 26.12, 26.72)));
      const sweepB = A.lerp(-0.75, 0.75, E.inOutSine(A.prog(t, 29.32, 29.95)));
      m.chars.forEach((c, i) => {
        const fxp = c.x / m.width;
        let e = 0;
        if (t > 26.12 && t < 26.72) e = Math.max(e, Math.exp(-(((fxp - sweepA) / 0.13) ** 2)));
        if (t > 29.32 && t < 29.95) e = Math.max(e, 0.8 * Math.exp(-(((fxp - sweepB) / 0.13) ** 2)));
        e = Math.max(e, 0.7 * A.hit(t, T.slam, 0.25) * (t >= T.slam - 0.03 ? 1 : 0));
        c.mesh.material[0].emissive.copy(this.cGold).lerp(this.cSheen, Math.min(1, e));
        c.mesh.material[0].emissiveIntensity = 0.2 + 0.55 * e;
        // letter ripple after the slam
        const rip = A.pulse(t, T.slam + 0.06 + i * 0.035, 0.22) + 0.7 * A.pulse(t, T.final + 0.03 + i * 0.03, 0.22);
        c.holder.position.set(c.holder.userData.baseX, 0.06 * rip, 0.35 * rip);
      });
      this.mGlow.scale.set(m.width * 1.25, m.capH * 2.6, 1);
      this.mGlow.material.opacity = 0.18 + 0.4 * A.hit(t, T.slam, 0.45) + 0.2 * finalK;
      // gold pool + rings + sparks on the paper below the word
      this.goldPool.position.set(mp.x, mp.y, 0.006);
      const gp = E.outCubic(A.prog(t, T.slam - 0.05, T.slam + 0.3));
      this.goldPool.scale.set(9 * 1.6 * gp, 3.4 * 1.6 * gp, 1);
      this.goldPool.material.opacity = 0.18 + 0.32 * A.hit(t, T.slam, 0.5) + 0.12 * finalK;
      this.goldPool.visible = gp > 0.01;
      this.slamRings.forEach((r, k) => {
        const tk = T.slam + k * 0.08;
        const rp = A.prog(t, tk, tk + 0.7);
        r.visible = rp > 0 && rp < 1;
        r.position.set(mp.x, mp.y, 0.03);
        const s = A.lerp(0.6, 7.5, E.outCubic(rp));
        r.scale.set(s, s * 0.55, 1);
        r.material.opacity = 0.75 * (1 - rp) ** 1.5;
      });
      this.slamSparks.update(t, T.slam, [mp.x, mp.y, mp.z + 0.4]);
      this.slamSparks2.update(t, T.slam + 0.04, [mp.x, mp.y + 0.3, mp.z + 0.6]);
      this.finalSparksY.update(t, T.final, [mp.x, mp.y, mp.z + 0.5]);
      this.glints.forEach(({ s, t0 }) => {
        const g = A.pulse(t, t0 + 0.14, 0.28);
        s.visible = g > 0.001;
        s.material.opacity = g;
        const sz = 0.9 * g;
        s.scale.set(sz, sz, 1);
        s.material.rotation = (t - t0) * 2;
      });
    } else {
      this.goldPool.visible = false;
      this.slamRings.forEach((r) => { r.visible = false; });
      this.slamSparks.update(t, T.slam, [0, 0, 0]);
      this.slamSparks2.update(t, T.slam, [0, 0, 0]);
      this.finalSparksY.update(t, T.final, [0, 0, 0]);
      this.glints.forEach(({ s }) => { s.visible = false; });
    }

    // ---------------------------------------------------------- crown
    const cp = A.prog(t, T.crown - 0.12, T.crown + 0.3);
    this.cPin.outer.visible = cp > 0;
    if (cp > 0) {
      this.pinAt(ctx, this.cPin.outer, L.crown.x, L.crown.y, L.crown.h, 1, { z: 0.8, seed: 5 });
      const sp = A.spring(t, T.crown - 0.12, { freq: 2.6, damp: 0.4 });
      this.cPin.inner.scale.setScalar(Math.max(0.001, sp) * (1 + 0.08 * finalK));
      this.cPin.inner.position.set(0, 0.5 * (1 - E.outCubic(cp)), 0);
      this.cPin.inner.rotation.set(0, THREE.MathUtils.degToRad(A.lerp(-180, 0, E.outBack(cp)) + 8 * Math.sin(t * 1.3)), THREE.MathUtils.degToRad(3 * Math.sin(t * 1.9)));
      this.crown.mesh.material.emissiveIntensity = 0.22 + 0.4 * A.hit(t, T.crown + 0.05, 0.3) + 0.3 * finalK;
    }

    // ---------------------------------------------------------- words stack in
    const word = (w, lay, tin, seed) => {
      const p = A.prog(t, tin - 0.16, tin);
      w.outer.visible = t >= tin - 0.16;
      if (!w.outer.visible) return null;
      const e = E.inCubic(p);
      const post = Math.max(0, t - tin);
      const sq = t >= tin ? Math.exp(-post / 0.09) * Math.cos(post * 36) * 0.12 : 0;
      // earlier words bump up when later words land
      let bump = 0;
      for (const tl of [T.better, T.trading, T.decisions]) if (tl > tin && t >= tl) bump += 7 * A.hit(t, tl, 0.12);
      const pos = this.pinAt(ctx, w.outer, lay.x, lay.y - bump, w.h, w.tx.capH, { z: 0.65, seed });
      w.inner.position.set(-0.6 * (1 - e), 0.9 * (1 - e), 5 * (1 - e));
      w.inner.rotation.set(THREE.MathUtils.degToRad(-25 * (1 - e)), 0, 0);
      const s = A.lerp(1.45, 1, e) * (1 + 0.04 * finalK);
      w.inner.scale.set(s * (1 + sq), s * (1 - sq), s);
      kitOpacity(w.tx.group, E.outCubic(A.prog(t, tin - 0.16, tin - 0.06)));
      // a bright flash wave through the letters on landing
      w.tx.chars.forEach((c, i) => {
        const g = t >= tin ? 0.7 * A.pulse(t, tin + 0.04 + i * 0.025, 0.2) : 0;
        c.mesh.material[0].emissiveIntensity = 0.12 + 0.6 * g + 0.25 * finalK;
        c.holder.position.set(c.holder.userData.baseX, 0, 0.25 * g);
      });
      return pos;
    };
    const wps = [word(this.wBetter, L.better, T.better, 7), word(this.wTrading, L.trading, T.trading, 8), word(this.wDecisions, L.decisions, T.decisions, 9)];
    // small green ring on each landing (behind the word, on the paper)
    [[T.better, wps[0], this.wBetter], [T.trading, wps[1], this.wTrading], [T.decisions, wps[2], this.wDecisions]].forEach(([tl, wp, w], k) => {
      const r = this.wordRings[k];
      const rp = A.prog(t, tl, tl + 0.5);
      r.visible = !!wp && rp > 0 && rp < 1;
      if (!r.visible) return;
      const sc = w.outer.scale.x;
      r.position.set(wp.x + (w.tx.width * sc) / 2, wp.y, 0.03);
      const s = A.lerp(0.5, (w.tx.width * sc) * 0.62, E.outCubic(rp));
      r.scale.set(s, s * 0.32, 1);
      r.material.opacity = 0.55 * (1 - rp) ** 1.5;
    });

    // ---------------------------------------------------------- check badge
    const bp = A.prog(t, T.check - 0.12, T.check + 0.3);
    this.bPin.outer.visible = bp > 0;
    let badgePos = null;
    if (bp > 0) {
      badgePos = this.pinAt(ctx, this.bPin.outer, L.check.x, L.check.y, L.check.h, 2, { z: 0.7, seed: 10 });
      const sp = A.spring(t, T.check - 0.12, { freq: 2.8, damp: 0.38 });
      this.bPin.inner.scale.setScalar(Math.max(0.001, sp) * (1 + 0.1 * finalK));
      this.bPin.inner.rotation.set(THREE.MathUtils.degToRad(6 * Math.sin(t * 1.4)), THREE.MathUtils.degToRad(A.lerp(-200, 0, E.outCubic(bp)) + 10 * Math.sin(t * 1.1)), 0);
      this.bPin.inner.position.z = 0.3 * finalK;
      this.badgeGlow.material.opacity = 0.25 + 0.4 * A.hit(t, T.check + 0.05, 0.4) + 0.35 * finalK;
    }
    this.finalRings.forEach((r, k) => {
      const tk = T.final + k * 0.09;
      const rp = A.prog(t, tk, tk + 0.8);
      r.visible = !!badgePos && rp > 0 && rp < 1;
      if (!r.visible) return;
      r.position.set(badgePos.x, badgePos.y, 0.03);
      const s = A.lerp(0.8, 9, E.outCubic(rp));
      r.scale.set(s, s * 0.7, 1);
      r.material.opacity = 0.65 * (1 - rp) ** 1.5;
    });
    this.finalSparksG.update(t, T.final, badgePos ? [badgePos.x, badgePos.y, badgePos.z + 0.5] : [0, 0, 0]);

    // ---------------------------------------------------------- candles
    const wave = A.lerp(-1.5, N_CANDLES + 1.5, A.prog(t, T.final, T.final + 0.6));
    this.candles.forEach((c, i) => {
      const t0 = CANDLE_T[i];
      const p = A.prog(t, t0, t0 + 0.3);
      c.setAppear(p, 'grow');
      c.group.position.z = 0.5 * (1 - E.outCubic(p));
      let g = t >= t0 ? 0.6 * A.hit(t, t0 + 0.05, 0.3) : 0;
      if (p > 0 && p < 1) g = Math.max(g, 0.6);
      if (t > T.final && t < T.final + 0.6) g = Math.max(g, 0.8 * Math.exp(-(((i - wave) / 1.2) ** 2)));
      c.setGlow(g);
      const k = 1 + 0.05 * finalK;
      if (p >= 1) c.group.scale.set(k, k, k);
    });
    this.greenPool.material.opacity = 0.22 * E.outCubic(A.prog(t, 27.37, 28.3)) * (1 + 0.8 * finalK);
    this.greenPool.visible = t > 27.37;

    // ---------------------------------------------------------- arrow
    const ap = E.inOutSine(A.prog(t, T.arrow[0], T.arrow[1]));
    this.arrow.setDraw(ap);
    const tip = this.arrow.head.position;
    this.arrowGlow.visible = ap > 0.01;
    this.arrowGlow.position.set(tip.x, tip.y, tip.z + 0.1);
    const ag = (ap > 0 && ap < 1 ? 0.45 : 0.2) + 0.5 * finalK;
    this.arrowGlow.material.opacity = ag;
    this.arrowGlow.scale.setScalar(2.2 * (1 + 0.4 * finalK));
    this.arrow.mat.emissiveIntensity = 0.2 + 0.4 * finalK;
    this.tipSparks.update(t, T.final, [ARROW_TO[0], ARROW_TO[1], ARROW_TO[2] + 0.3]);

    // ---------------------------------------------------------- dust
    this.dust.update(t);
    this.glitter.update(t);
    this.glitter.setOpacity(0.25 + 0.75 * E.outCubic(A.prog(t, T.slam, T.slam + 0.8)));
  },
};

// fade an object tree (same as kit.setOpacity, kept local: scenes import only data)
function kitOpacity(obj, a) {
  obj.traverse((o) => {
    if (!o.material) return;
    for (const mm of Array.isArray(o.material) ? o.material : [o.material]) {
      mm.opacity = a * (mm.userData.baseOpacity ?? 1);
      mm.depthWrite = a > 0.98 && mm.userData.depthWrite !== false;
    }
  });
  obj.visible = a > 0.001;
}

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
