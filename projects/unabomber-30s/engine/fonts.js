// Font registry. One list feeds three consumers:
//   * the page's @font-face rules (DOM overlay type),
//   * the DOM-to-texture rasteriser, which embeds the faces a frame uses as
//     data: URLs (an SVG image cannot fetch fonts),
//   * kit.text3d, which extrudes glyph outlines (needs TTF/OTF/WOFF, not WOFF2).
// All families are SIL OFL (fontsource / Google Fonts).

const FS = '/node_modules/@fontsource';
const range = (a, b, step = 100) => { const r = []; for (let w = a; w <= b; w += step) r.push(w); return r; };

// [css family, package dir, file stem, weights, italics?]
const STATIC = [
  ['Bebas Neue', 'bebas-neue', 'bebas-neue', [400], false],
  ['Oswald', 'oswald', 'oswald', range(200, 700), false],
  ['Anton', 'anton', 'anton', [400], false],
  ['Inter', 'inter', 'inter', range(100, 900), true],
  ['IBM Plex Mono', 'ibm-plex-mono', 'ibm-plex-mono', range(100, 700), true],
  ['Special Elite', 'special-elite', 'special-elite', [400], false],
  ['Playfair Display', 'playfair-display', 'playfair-display', range(400, 900), true],
  ['Cormorant Garamond', 'cormorant-garamond', 'cormorant-garamond', range(300, 700), true],
  ['Montserrat', 'montserrat', 'montserrat', range(100, 900), true],
  ['Archivo Black', 'archivo-black', 'archivo-black', [400], false],
  ['Courier Prime', 'courier-prime', 'courier-prime', [400, 700], true],
];

// Every face: { family, weight, style, stretch, url, format }
export const FACES = [];
for (const [family, pkg, stem, weights, italics] of STATIC) {
  for (const w of weights) {
    for (const style of italics ? ['normal', 'italic'] : ['normal']) {
      FACES.push({ family, weight: String(w), style, stretch: 'normal', url: `${FS}/${pkg}/files/${stem}-latin-${w}-${style}.woff2`, format: 'woff2' });
    }
  }
}
// Archivo as a variable font: weight 100-900, width 62-125 % (font-stretch: 125% = Expanded).
FACES.push({ family: 'Archivo', weight: '100 900', style: 'normal', stretch: '62% 125%', url: '/node_modules/@fontsource-variable/archivo/files/archivo-latin-wdth-normal.woff2', format: 'woff2-variations' });
FACES.push({ family: 'Archivo', weight: '100 900', style: 'italic', stretch: '62% 125%', url: '/node_modules/@fontsource-variable/archivo/files/archivo-latin-wdth-italic.woff2', format: 'woff2-variations' });
// Static Archivo Expanded instances (identical outlines to the 3D title).
FACES.push({ family: 'Archivo Expanded', weight: '900', style: 'normal', stretch: 'normal', url: '/engine/fonts/archivo-expanded-900.ttf', format: 'truetype' });
FACES.push({ family: 'Archivo Expanded', weight: '700', style: 'normal', stretch: 'normal', url: '/engine/fonts/archivo-expanded-700.ttf', format: 'truetype' });

export function fontFaceCSS(face, src = face.url) {
  return `@font-face{font-family:'${face.family}';font-style:${face.style};font-weight:${face.weight};font-stretch:${face.stretch};font-display:block;src:url(${src}) format('${face.format}');}`;
}

export function installFontFaces() {
  const s = document.createElement('style');
  s.textContent = FACES.map((f) => fontFaceCSS(f)).join('\n');
  document.head.appendChild(s);
}

// Pick the registered face closest to a computed (family, weight, style).
export function matchFace(family, weight, style) {
  const fam = family.replace(/["']/g, '').trim().toLowerCase();
  const cands = FACES.filter((f) => f.family.toLowerCase() === fam);
  if (!cands.length) return null;
  const w = Number(weight) || 400;
  let best = null, bd = Infinity;
  for (const f of cands) {
    const [a, b = a] = f.weight.split(' ').map(Number);
    const d = (w < a ? a - w : w > b ? w - b : 0) + (f.style === style ? 0 : 1000);
    if (d < bd) { bd = d; best = f; }
  }
  return best;
}

const dataCache = new Map();
// The face's file as a data: URL (cached), for embedding in SVG images.
export async function faceDataURL(face) {
  if (dataCache.has(face.url)) return dataCache.get(face.url);
  const p = (async () => {
    const buf = new Uint8Array(await (await fetch(face.url)).arrayBuffer());
    let bin = '';
    for (let i = 0; i < buf.length; i += 0x8000) bin += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
    const mime = face.format.startsWith('woff2') ? 'font/woff2' : face.format === 'truetype' ? 'font/ttf' : 'font/woff';
    return `data:${mime};base64,${btoa(bin)}`;
  })();
  dataCache.set(face.url, p);
  return p;
}

// Fonts for 3D extrusion (kit.text3d). TTF/OTF/WOFF only.
export const FONT3D = {
  archivoX900: '/engine/fonts/archivo-expanded-900.ttf', // Archivo Expanded Black — the title face
  archivoX700: '/engine/fonts/archivo-expanded-700.ttf',
  archivo900: '/engine/fonts/archivo-900.ttf',
  plex500: '/engine/fonts/ibm-plex-mono-500.ttf',
  plex600: '/engine/fonts/ibm-plex-mono-600.ttf',
  courier700: '/engine/fonts/courier-prime-700.ttf',
  archivoBlack: `${FS}/archivo-black/files/archivo-black-latin-400-normal.woff`,
  bebas: `${FS}/bebas-neue/files/bebas-neue-latin-400-normal.woff`,
  anton: `${FS}/anton/files/anton-latin-400-normal.woff`,
  oswald700: `${FS}/oswald/files/oswald-latin-700-normal.woff`,
  inter800: `${FS}/inter/files/inter-latin-800-normal.woff`,
  montserrat800: `${FS}/montserrat/files/montserrat-latin-800-normal.woff`,
  montserrat900: `${FS}/montserrat/files/montserrat-latin-900-normal.woff`,
  playfair700: `${FS}/playfair-display/files/playfair-display-latin-700-normal.woff`,
  playfair900: `${FS}/playfair-display/files/playfair-display-latin-900-normal.woff`,
  cormorant700: `${FS}/cormorant-garamond/files/cormorant-garamond-latin-700-normal.woff`,
  specialElite: `${FS}/special-elite/files/special-elite-latin-400-normal.woff`,
};

// CSS shorthands for the overlay (document fonts). Usage: font: `500 26px ${CSSF.plex}`.
export const CSSF = {
  plex: "'IBM Plex Mono', monospace",
  courier: "'Courier Prime', monospace",
  archivo: "'Archivo', sans-serif",
  archivoX: "'Archivo Expanded', 'Archivo', sans-serif",
  inter: "'Inter', sans-serif",
  oswald: "'Oswald', sans-serif",
  bebas: "'Bebas Neue', sans-serif",
  anton: "'Anton', sans-serif",
  montserrat: "'Montserrat', sans-serif",
  playfair: "'Playfair Display', serif",
  cormorant: "'Cormorant Garamond', serif",
  specialElite: "'Special Elite', monospace",
};
