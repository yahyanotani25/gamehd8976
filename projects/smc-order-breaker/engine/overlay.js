// DOM overlay helpers: crisp 2D typography and labels drawn over the 3D
// frame. Like the 3D side, every element is fully re-specified each frame.

export function css(str) {
  const s = document.createElement('style');
  s.textContent = str;
  document.head.appendChild(s);
  return s;
}

export function el(parent, { tag = 'div', cls = '', html = '', style = {} } = {}) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html) e.innerHTML = html;
  Object.assign(e.style, { position: 'absolute', left: '0px', top: '0px', ...style });
  parent.appendChild(e);
  return e;
}

// Position an element by its anchor (ax, ay = 0.5 centre) at pixel (x, y).
export function place(e, { x = 540, y = 960, ax = 0.5, ay = 0.5, opacity = 1, scale = 1, sx = 1, sy = 1, rot = 0, rx = 0, ry = 0, blur = 0, persp = 0, visible = true } = {}) {
  if (!visible || opacity <= 0.001) { e.style.display = 'none'; return; }
  e.style.display = '';
  const p = persp ? `perspective(${persp}px) ` : '';
  e.style.transform = `translate(${x}px, ${y}px) translate(${-ax * 100}%, ${-ay * 100}%) ${p}rotateX(${rx}deg) rotateY(${ry}deg) rotate(${rot}deg) scale(${scale * sx}, ${scale * sy})`;
  e.style.opacity = String(Math.min(1, opacity));
  e.style.filter = blur > 0.05 ? `blur(${blur.toFixed(2)}px)` : 'none';
}

// Split an element's text into per-letter spans (spaces preserved).
export function letters(e, text) {
  e.innerHTML = '';
  return [...text].map((ch) => {
    const s = document.createElement('span');
    s.textContent = ch === ' ' ? ' ' : ch;
    s.style.display = 'inline-block';
    e.appendChild(s);
    return s;
  });
}
// Style an inline span (letter/word) relative to its natural place.
export function nudge(s, { x = 0, y = 0, opacity = 1, scale = 1, rot = 0, blur = 0 } = {}) {
  s.style.transform = `translate(${x}px, ${y}px) rotate(${rot}deg) scale(${scale})`;
  s.style.opacity = String(Math.max(0, Math.min(1, opacity)));
  s.style.filter = blur > 0.05 ? `blur(${blur.toFixed(2)}px)` : 'none';
}

// Base styles shared by all scenes.
css(`
  .scene-layer { position: absolute; inset: 0; pointer-events: none; }
  .pill { font: 800 40px/1 Montserrat; letter-spacing: 0.04em; color: #fff; padding: 18px 30px 16px;
          border-radius: 999px; white-space: nowrap; display: inline-flex; align-items: center; gap: 14px;
          box-shadow: 0 14px 34px rgba(18, 24, 38, 0.28), inset 0 1px 0 rgba(255,255,255,0.35); }
  .pill svg { width: 1.1em; height: 1.1em; }
  .pill.green { background: linear-gradient(180deg, #22d86c, #0b9b45); }
  .pill.red { background: linear-gradient(180deg, #ff4b4b, #c4121c); }
  .pill.ink { background: linear-gradient(180deg, #2a2f3a, #111318); }
  .pill.navy { background: linear-gradient(180deg, #24427f, #10224a); }
  .pill.gold { background: linear-gradient(180deg, #ffc93d, #e69100); color: #2a1600; }
  .pill.white { background: #fff; color: #15171c; box-shadow: 0 14px 34px rgba(18,24,38,0.22), 0 0 0 3px rgba(21,23,28,0.08); }
  .title2d { font: 150px/1 Bebas; color: #5e0f1a; white-space: nowrap; letter-spacing: 0.01em;
             text-shadow: 0 2px 0 #3d0810, 0 4px 0 #34070d, 0 6px 0 #2c0509, 0 18px 30px rgba(40, 6, 12, 0.28); }
`);

// Stroke-style icons for DOM use (24x24 viewBox, currentColor).
export const ICON = {
  bank: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9.5 12 4l9 5.5"/><path d="M4 10h16"/><path d="M6 10v8M10 10v8M14 10v8M18 10v8"/><path d="M3 20.5h18"/></svg>',
  target: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.2"/><circle cx="12" cy="12" r="0.8" fill="currentColor"/><path d="M12 1.5v3M12 19.5v3M1.5 12h3M19.5 12h3"/></svg>',
  reverse: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M7 20V5M3.5 8.5 7 5l3.5 3.5"/><path d="M17 4v15M13.5 15.5 17 19l3.5-3.5"/></svg>',
  up: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/></svg>',
  down: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l6 6 4-4 8 8"/><path d="M15 17h6v-6"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 12.5l5 5L19.5 7"/></svg>',
  x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>',
  bolt: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M13.5 2 4 14h6.5L9.5 22 20 9.5h-6.6z"/></svg>',
  crown: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M2.5 7.5 7 11l5-7 5 7 4.5-3.5-2 11h-15z"/><rect x="4.5" y="19.5" width="15" height="2.2" rx="1"/></svg>',
  shield: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"><path d="M12 2.5 4 5.5v6c0 5 3.4 8.6 8 10 4.6-1.4 8-5 8-10v-6z"/></svg>',
  flip: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9a8 8 0 0 1 14-3l2 2"/><path d="M20 3v5h-5"/><path d="M20 15a8 8 0 0 1-14 3l-2-2"/><path d="M4 21v-5h5"/></svg>',
};

// Filled icons (100x100 viewBox) for kit.svgIcon 3D extrusion.
export const ICON3D = {
  bank: '<svg viewBox="0 0 100 100"><path d="M50 6 94 30H6Z"/><path d="M8 33h84v8H8Z"/><path d="M15 45h11v35H15Z"/><path d="M35 45h11v35H35Z"/><path d="M54 45h11v35H54Z"/><path d="M74 45h11v35H74Z"/><path d="M6 84h88v10H6Z"/></svg>',
  check: '<svg viewBox="0 0 100 100"><path d="M10 52 24 38 42 56 78 20 92 34 42 84Z"/></svg>',
  x: '<svg viewBox="0 0 100 100"><path d="M20 10 50 40 80 10 90 20 60 50 90 80 80 90 50 60 20 90 10 80 40 50 10 20Z"/></svg>',
  crown: '<svg viewBox="0 0 100 100"><path d="M8 78 14 28 34 50 50 14 66 50 86 28 92 78Z"/><path d="M8 84h84v10H8Z"/></svg>',
  bolt: '<svg viewBox="0 0 100 100"><path d="M58 4 18 56H46L38 96 82 40H54Z"/></svg>',
  swap: '<svg viewBox="0 0 100 100"><path d="M8 40 30 10 52 40H39V90H21V40Z"/><path d="M48 60 70 90 92 60H79V10H61V60Z"/></svg>',
  target: '<svg viewBox="0 0 100 100"><path fill-rule="evenodd" d="M50 4a46 46 0 1 1 0 92 46 46 0 1 1 0-92Zm0 13a33 33 0 1 0 0 66 33 33 0 1 0 0-66Z"/><path fill-rule="evenodd" d="M50 27a23 23 0 1 1 0 46 23 23 0 1 1 0-46Zm0 11a12 12 0 1 0 0 24 12 12 0 1 0 0-24Z"/><path d="M50 44a6 6 0 1 1 0 12 6 6 0 1 1 0-12Z"/></svg>',
};
