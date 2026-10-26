// Boots the engine, loads the scenes, then exposes renderFrame(t) for the
// render driver. ?scenes=a,b loads only those scene ids (or scene groups,
// e.g. ?scenes=lookdev) for faster previews. ?overlay=top keeps the DOM
// overlay live above the canvas instead of rasterising it into the film pass.
import { installFontFaces, FACES } from './fonts.js';
installFontFaces();

try {
  const core = await import('./core.js');
  const kit = await import('./kit.js');
  const A = await import('./anim.js');
  const ov = await import('./overlay.js');
  const post = await import('./post.js');
  const media = await import('./media.js');
  const tex = await import('./textures.js');
  const q = new URLSearchParams(location.search);

  const words = await (await fetch('/data/words.json')).json().catch(() => []);
  core.setWords(words);
  // make sure the commonly used faces are decoded before the first frame
  await Promise.all(["500 26px 'IBM Plex Mono'", "600 26px 'IBM Plex Mono'", "700 64px 'Courier Prime'", "900 64px 'Archivo Expanded'", "400 64px 'Inter'"].map((f) => document.fonts.load(f)));
  await kit.loadFonts(['archivoX900', 'plex500', 'courier700']);
  if (q.get('overlay') === 'top') core.setOverlayMode('top');

  const only = q.get('scenes')?.split(',');
  const { SCENES, EXAMPLES, TRANSITIONS, DURATION, LOOKS } = await import('/scenes/index.js');
  const pool = only ? [...SCENES, ...EXAMPLES] : SCENES;
  const pick = (s) => !only || only.includes(s.id) || (s.group && only.includes(s.group));
  for (const s of pool) if (pick(s)) core.addScene(s);
  for (const tr of TRANSITIONS) core.addTransition(tr);
  if (LOOKS) await LOOKS(post);

  const ctx = {
    THREE: core.THREE, core, kit, A, ov, post, media, tex, PAL: kit.PAL, W: core.W, H: core.H,
    cam: core.cam, fx: core.fx, lights: core.lights, scene: core.scene, camera: core.camera,
    wt: core.wt, words, toScreen: core.toScreen, unitPx: core.unitPx, screenToWorld: core.screenToWorld, screenRay: core.screenRay, pin: core.pin,
  };
  await core.initScenes(ctx);
  window.DURATION = DURATION;
  window.renderFrame = (t) => core.renderFrame(t);
  window.engineStats = () => core.stats();
  window.ready = true;
} catch (e) {
  window.bootError = String(e && e.stack || e);
  console.error(window.bootError);
}
