// DOM overlay -> WebGL texture. The overlay (crisp CSS typography) is
// serialised into an SVG <foreignObject> image each frame and uploaded, so the
// film pass (grain, weave, CA, blur, glitch, letterbox, fades) treats type
// exactly like the picture. Fonts are embedded as data: URLs (an SVG image
// cannot fetch), only the faces the visible text uses.
import * as THREE from 'three';
import { matchFace, faceDataURL, fontFaceCSS } from './fonts.js';

const W = 1920, H = 1080;
const tex = new THREE.Texture();
tex.colorSpace = THREE.NoColorSpace;
tex.minFilter = THREE.LinearFilter; tex.magFilter = THREE.LinearFilter; tex.generateMipmaps = false;
tex.flipY = true;
export const domTexture = tex;

// Collect overlay CSS (ov.css() marks its <style> elements with data-ov).
function overlayCSS() {
  return [...document.querySelectorAll('style[data-ov]')].map((s) => s.textContent).join('\n');
}
function hasText(el) {
  for (const n of el.childNodes) if (n.nodeType === 3 && n.nodeValue.trim()) return true;
  return false;
}
// Is anything visible in the overlay? (cheap check, skips the raster when empty)
export function overlayVisible(root) {
  for (const layer of root.children) {
    if (layer.style.display === 'none' || layer.style.opacity === '0') continue;
    if (layer.childElementCount > 0) return true;
  }
  return false;
}

let lastKey = '';
export async function capture(root) {
  if (!overlayVisible(root)) return null;
  // fonts used by visible text
  const faces = new Set();
  for (const layer of root.children) {
    if (layer.style.display === 'none') continue;
    for (const el of layer.querySelectorAll('*')) {
      if (!hasText(el)) continue;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') continue;
      const fam = cs.fontFamily.split(',')[0];
      const face = matchFace(fam, cs.fontWeight, cs.fontStyle);
      if (face) faces.add(face);
    }
  }
  const fontCSS = (await Promise.all([...faces].map(async (f) => fontFaceCSS(f, await faceDataURL(f))))).join('\n');
  const xml = new XMLSerializer().serializeToString(root);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}"><foreignObject x="0" y="0" width="${W}" height="${H}">`
    + `<div xmlns="http://www.w3.org/1999/xhtml" style="position:relative;width:${W}px;height:${H}px;overflow:hidden;margin:0"><style>${fontCSS}\n${overlayCSS()}</style>${xml}</div></foreignObject></svg>`;
  if (svg === lastKey && tex.image) return tex; // unchanged frame
  const img = new Image(W, H);
  img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
  await img.decode();
  lastKey = svg;
  tex.image = img;
  tex.needsUpdate = true;
  return tex;
}
