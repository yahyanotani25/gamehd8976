// Boots the engine, loads every scene, then exposes renderFrame(t) for the
// render driver. ?scenes=a,b loads only those scene ids (faster previews).
import * as core from './core.js';
import * as kit from './kit.js';
import * as A from './anim.js';
import * as ov from './overlay.js';

try {
  const words = await (await fetch('/data/words.json')).json();
  core.setWords(words);
  await Promise.all(['150px Bebas', '150px Anton', '800 40px Montserrat', '900 40px Montserrat', '700 40px Montserrat', '700 40px Oswald'].map((f) => document.fonts.load(f)));
  await kit.loadFonts();

  const only = new URLSearchParams(location.search).get('scenes')?.split(',');
  const { SCENES, EXAMPLES, TRANSITIONS, DURATION } = await import('/scenes/index.js');
  const pool = only ? [...SCENES, ...EXAMPLES] : SCENES;
  for (const s of pool) if (!only || only.includes(s.id)) core.addScene(s);
  for (const tr of TRANSITIONS) core.addTransition(tr);

  const ctx = {
    THREE: core.THREE, core, kit, A, ov, PAL: kit.PAL, W: core.W, H: core.H,
    cam: core.cam, fx: core.fx, lights: core.lights, wt: core.wt, words, toScreen: core.toScreen, unitPx: core.unitPx, screenToWorld: core.screenToWorld, pin: core.pin,
  };
  await core.initScenes(ctx);
  window.DURATION = DURATION;
  window.renderFrame = (t) => core.renderFrame(t);
  window.ready = true;
} catch (e) {
  window.bootError = String(e && e.stack || e);
  console.error(window.bootError);
}
