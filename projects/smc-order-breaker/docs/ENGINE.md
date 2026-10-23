# Engine guide (for scene builders)

The film is rendered frame by frame in headless Chromium: Three.js (WebGL)
for the 3D world plus a DOM overlay for crisp 2D type. `renderFrame(t)`
draws the frame at time `t` from scratch, and frames are rendered out of
order and in parallel browsers.

## Hard rules

1. **A scene is a pure function of time.** `update(t, lt, ctx)` must set
   every property it animates on every call, computed from `t` only. No
   state carried between frames, no `Math.random()` (use `A.rng(seed)` in
   `init`), no `Date`, no `requestAnimationFrame`, no CSS transitions or
   animations (the overlay is restyled every frame).
2. Build geometry, materials and DOM in `init`; `update` only sets
   transforms, opacities, colours and draw progress. (`stroke`/`arrow`
   `setDraw` rebuild a small tube internally; that's fine.)
3. Scene files import nothing except plain data modules in `scenes/` (such
   as `./story-data.js`). Everything else comes from `ctx`. This lets Node
   import the scene files to read their `cues`.
4. Only edit your own scene file(s). Do not edit `engine/`, `render/`,
   `scenes/index.js` or other scenes. If the engine has a bug, work around
   it in your file and report it.
5. Call `ctx.cam.frame(...)` (or `ctx.cam.set`) every frame. Call
   `ctx.toScreen` only after setting the camera.

## Scene module shape

```js
export default {
  id: 's2', start: 2.45, end: 11.70,     // fixed by scenes/index.js — keep
  cues: [ { t: 3.92, sfx: 'click' }, ... ], // SFX cue sheet for this scene
  async init(ctx) { ... },               // build objects; add to ctx.group / ctx.dom
  update(t, lt, ctx) { ... },            // t = global seconds, lt = t - start
};
```

The engine shows `ctx.group` (a THREE.Group in the scene) and `ctx.dom` (a
div over the canvas) only while `start <= t < end`. Store your objects on
`this` in `init` and read them in `update`.

## ctx

| key | what |
|---|---|
| `THREE` | three.js |
| `A` | animation helpers (`engine/anim.js`) |
| `kit` | 3D building blocks (`engine/kit.js`) |
| `ov` | DOM overlay helpers (`engine/overlay.js`) |
| `PAL` | colour palette |
| `cam` | camera rig |
| `fx` | per-frame post FX state (reset each frame) |
| `wt(word, nth = 1, which = 'start')` | time of the nth occurrence of a script word (`which: 'end'` for its end) |
| `words` | all aligned words `[{ word, start, end }]` |
| `toScreen(v)` | world `[x, y, z]` or Vector3 → `{ x, y }` pixels |
| `unitPx(v)` | pixels per world unit at `v` |
| `screenToWorld(x, y, z)` | world point shown at pixel (x, y) on the plane z |
| `pin(obj, { x, y, z, heightPx, worldHeight, scale })` | keep a 3D object at a screen position and pixel size while the camera moves (call after setting the camera) |
| `group`, `dom` | this scene's 3D group and DOM layer |
| `lights` | `{ hemi, key, rim, shadow }` (leave alone unless needed) |
| `core` | engine core (camera object etc.; read-only use) |

## World

- The paper is the plane z = 0, a white sheet with grid lines on integer
  coordinates (1 unit = 1 cell). Objects stand off it towards +z and cast
  soft shadows (key light from the upper left).
- Text and objects meant to float should sit at z ≈ 0.3–1.5 so the shadow
  separates them from the paper.

## Camera — `ctx.cam`

- `cam.frame({ cx, cy, width = 13.5, pitch = 0, yaw = 0, roll = 0, fov = 28, dolly = 1 })`:
  frames `width` units of paper centred on (cx, cy). `pitch` (degrees,
  negative = looking up the page from below, like a table-top shot) and
  `yaw` give 3D angles; `dolly` multiplies the distance (< 1 pushes in).
- `cam.set({ pos, target, fov, roll })` for full control.
- Keep it alive: slow drifts (`A.noise1`) plus purposeful moves (`A.kf`).
  Pitch between about -25 and +10 and yaw within ±20 look good; extreme
  angles reveal the paper's edge-on perspective.

## Post FX — `ctx.fx` (set per frame, reset to defaults before each frame)

`zoom` (radial blur 0–0.3), `zoomC` ([u, v] centre), `dir` ([du, dv]
directional blur), `ca` (chromatic aberration 0–3), `flash` (0–1 towards
`flashColor`), `fade` (0–1 towards `fadeColor`), `vignette`, `contrast`,
`saturation`, `exposure`, `shake` (camera shake amplitude in world units,
about 0.05–0.3), `overlayBlur` (px), `overlayScale`, `dof`
(`{ focus, aperture, maxblur }` — costs ~1.5 s per frame, use only in short
hero moments, if at all). Scene-boundary transitions are added by the
engine on top.

## kit (3D) — see `engine/kit.js` for full signatures

- `kit.candle({ o, h, l, c, x, width, depth, color })` → `{ group, setAppear(p, 'pop'|'grow'), setGlow(a), setOpacity(a), setColor(c) }`.
  `'pop'` = reference-style scale pop with overshoot; `'grow'` = forms like a
  live candle from the open price.
- `kit.chart({ data, x0 = 0.5, step = 1 })` → `{ group, candles, x(i), animate(t, times, { dur, mode }) }`.
  `times[i]`: start time for candle i; `-1` already shown; `undefined` hidden.
- `kit.zone({ x0, x1, y0, y1, color })` → glass slab with rails and hatch:
  `reveal(p)` (grows left→right), `setColor(c)`, `flip(deg)` (3D flip about
  its horizontal centre line), `pulse(a)`, `setOpacity(a)`, `at(fx, fy, z)` →
  world point.
- `kit.stroke(points, { color, radius })` → `setDraw(to, from = 0)`.
- `kit.arrow(from, to, { color, radius, head, bend })` → `setDraw(p)`.
- `kit.outlineBox({ cx, cy, w, h, r, color })` → highlight box like the
  reference, `setDraw(p)` draws it clockwise from the top.
- `kit.text3d(str, { font: 'bebas'|'anton'|'montserrat'|'montserrat800'|'oswald', size, depth, bevel, color, side, align, tracking })`
  → `{ group, chars: [{ ch, holder, mesh }], width, capH, setOpacity, setColor }`.
  Animate letters via `chars[i].holder` (position/rotation/scale) and opacity
  via `chars[i].mesh.material[0|1].opacity` (front / sides). `size` is in
  world units (cap height ≈ 0.7 × size for bebas).
- `kit.svgIcon(ICON3D.bank, { size, depth, color })` → extruded 3D icon.
  Available: `ov.ICON3D.{bank, check, x, crown, bolt, swap, target}`; you
  can author your own filled SVG paths (100×100 viewBox).
- `kit.card({ w, h, r, depth, color })` → white rounded slab.
- `kit.glow({ color, size, opacity })` sprite; `kit.paperGlow({ color, w, h, opacity })` light pool on the paper.
- `kit.dust({ count, w, h, zMin, zMax, size, cx, cy, seed })` → `update(t)`.
- `kit.sparks({ count, color, speed, life, seed })` → `update(t, t0, origin)`.
- `kit.glossy(color, opts)`, `kit.matte(color, opts)` materials;
  `kit.setOpacity(obj, a)` fades any object tree.

## ov (DOM)

- `ov.el(parent, { cls, html, style })` → absolutely positioned element.
- `ov.place(e, { x, y, ax, ay, opacity, scale, sx, sy, rot, rx, ry, persp, blur })`
  — positions an element by its anchor at pixel (x, y). Call every frame.
- `ov.letters(e, text)` → per-letter spans; `ov.nudge(span, { x, y, opacity, scale, rot, blur })`.
- `ov.css(str)` injects scene CSS (prefix your classes with your scene id).
- Ready-made styles: `.pill` + `green|red|ink|navy|gold|white`, `.title2d`.
- Icons: `ov.ICON.{bank, target, reverse, up, down, check, x, bolt, crown, shield, flip}` (inline SVG strings).
- Fonts available in CSS: `Bebas`, `Anton`, `Montserrat` (700/800/900),
  `Oswald` (700).

## anim (A)

`clamp, lerp, prog(t, a, b), ease(t, a, b, fn), E.* easings (outBack,
outExpo, inOutCubic…), kf(t, [[t0, v0], [t1, v1, easeFn], …]),
spring(t, t0, { freq, damp }), pulse(t, at, dur), hit(t, at, release),
window(t, a, b, fadeIn, fadeOut), noise1(x, seed), rng(seed)`.

## Previewing

```
node render/preview.mjs --scenes s2 --range 2.45:11.6:0.25 --sheet 6 --guides --out previews/s2/v1
node render/preview.mjs --scenes s2 --t 5.2,9.7 --out previews/s2/v1-detail
```

`--scenes` loads only the listed scenes (faster); `--sheet N` writes a
labelled contact sheet `sheet.png` (N frames per row) you can open with the
Read tool; `--guides` draws the layout bands from the storyboard on the
sheet. Full-size PNGs are written too, for close inspection. A frame takes
about 1–3 s; keep sheets to ≤ 36 frames. Engine errors fail the preview with
the message.

`scenes/lookdev.js` is a small working example of most kit pieces.
