// Scene captions: global word-synced captions of the Roman Urdu voice-over.
// DOM only (no 3D, no camera: captions run last, so touching ctx.cam here
// would override every scene's camera). Drawn in the caption band, centre
// y 1560, on top of everything.
//
// Look: a frosted white pill that morphs its width from chunk to chunk;
// bold Montserrat 900 caps; each word flips/pops in at its start (blur +
// overshoot); a rounded colour block slides to the word being spoken
// (ink by default, keyword colour on keywords); keywords keep their colour
// once spoken. Chunks swap in 0.06 s and hide in long pauses.

// Curated chunking (<= 3 words, <= 20 chars, breaks at every comma, sentence
// end and pause > 0.25 s). Matched against ctx.words in init; if the words
// ever change, a rule-based chunker takes over.
const CHUNKS = [
  'Smart Money Concepts', 'ko samajhna', 'chahte hain?',
  'Order Block', 'woh zone', 'hota hai', 'jahan institutions', 'market mein entry', 'le sakte hain,',
  'jis ki', 'wajah se', 'price mein reaction', 'aane ka imkaan', 'hota hai.',
  'Jab yeh', 'block fail', 'ho jata hai', 'aur apna', 'role reverse', 'kar leta hai,',
  'toh yeh', 'Breaker Block', 'ban jata hai.',
  'Order Block', 'potential entry', 'ka signal', 'deta hai,',
  'jabke', 'Breaker Block', 'potential reversal', 'ko show', 'karta hai.',
  'In concepts par', 'mastery hasil karein',
  'aur zyada behtar', 'trading decisions', 'lein!',
];

// Keyword phrases (normalised word sequences) and their colour role.
const KEYWORDS = [
  [['smart', 'money', 'concepts'], 'gold'],
  [['order', 'block'], 'green'],
  [['breaker', 'block'], 'red'],
  [['institutions'], 'navy'],
  [['entry'], 'green'],
  [['reaction'], 'green'],
  [['fail'], 'red'],
  [['reverse'], 'red'],
  [['reversal'], 'red'],
  [['mastery'], 'gold'],
  [['trading', 'decisions'], 'green'],
];

// text colour when spoken (on the white pill), block colour when active,
// text colour on the block
const ROLE = {
  ink: { text: '#15171c', block: '#15171c', on: '#ffffff' },
  green: { text: '#079a3e', block: '#0bb04a', on: '#ffffff' },
  red: { text: '#e3121f', block: '#f5222d', on: '#ffffff' },
  navy: { text: '#142a57', block: '#1d3b7c', on: '#ffffff' },
  gold: { text: '#b86e00', block: '#ffb21a', on: '#2a1600' },
};

const FONT_PX = 64;
const GAP_PX = 30;        // space between words
const MAX_W = 830;        // max text width (pill adds padding; stays inside x 70-1010)
const PAD_X = 42;         // pill horizontal padding
const PILL_H = 108;
const CY = 1560;          // caption centre
const BLK_PX = 11;        // highlight block padding around a word
const LEAD = 0.02;        // words start popping this much before their start
const SWAP = 0.06;        // chunk exit time before the next chunk
const HOLD = 0.35;        // hold after the last word before hiding in long pauses
const HIDE_DUR = 0.1;     // exit time when hiding

const norm = (s) => s.toLowerCase().replace(/[^a-z]/g, '');
const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));

function ruleChunks(words) {
  // fallback: greedy, keeps keyword phrases whole
  const chunks = [];
  let cur = [];
  const phraseLen = (i) => {
    for (const [seq] of KEYWORDS) {
      if (seq.length > 1 && seq.every((k, j) => words[i + j] && norm(words[i + j].word) === k)) return seq.length;
    }
    return 1;
  };
  let i = 0;
  while (i < words.length) {
    const n = phraseLen(i);
    const add = words.slice(i, i + n);
    const prev = cur[cur.length - 1];
    const txt = [...cur, ...add].map((w) => w.word.replace(/[,.]/g, '')).join(' ');
    const hard = prev && (/[,.?!]$/.test(prev.word) || add[0].start - prev.end > 0.25);
    if (cur.length && (hard || cur.length + n > 3 || txt.length > 20)) { chunks.push(cur); cur = []; }
    cur.push(...add);
    i += n;
  }
  if (cur.length) chunks.push(cur);
  return chunks;
}

function curatedChunks(words) {
  const out = [];
  let i = 0;
  for (const c of CHUNKS) {
    const g = [];
    for (const piece of c.split(' ')) {
      if (!words[i] || words[i].word !== piece) return null;
      g.push(words[i++]);
    }
    const txt = g.map((w) => w.word.replace(/[,.]/g, '')).join(' ');
    if (g.length > 3 || txt.length > 20) return null;
    for (let j = 0; j < g.length - 1; j++) {
      if (/[,.?!]$/.test(g[j].word) || g[j + 1].start - g[j].end > 0.25) return null;
    }
    out.push(g);
  }
  return i === words.length ? out : null;
}

export default {
  id: 'captions', start: 0, end: 31.00,
  // Captions are typography, not story events: every sound in the film is
  // already cued by the scene that owns the visual event, so the caption
  // layer adds none (doubling would muddy the mix).
  cues: [],
  init(ctx) {
    const { ov, dom } = ctx;
    ov.css(`
      .captions-pill { height: ${PILL_H}px; border-radius: 30px;
        background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(246,247,250,0.9));
        box-shadow: 0 16px 36px rgba(18,24,38,0.20), 0 3px 8px rgba(18,24,38,0.10), inset 0 1px 0 rgba(255,255,255,1);
        border: 1.5px solid rgba(21,23,28,0.07); box-sizing: border-box; }
      .captions-chunk { white-space: nowrap; transform-origin: 0 50%; font: 900 ${FONT_PX}px/1 Montserrat; letter-spacing: 0.005em;
        perspective: 700px; padding: 0; }
      .captions-w { display: inline-block; position: relative; transform-origin: 50% 70%;
        margin-right: ${GAP_PX}px; padding: 6px 0 2px; }
      .captions-w:last-child { margin-right: 0; }
      .captions-blk { position: absolute; left: 0; top: 0; border-radius: 16px; transform-origin: 50% 50%;
        background-image: linear-gradient(180deg, rgba(255,255,255,0.22), rgba(255,255,255,0) 55%, rgba(0,0,0,0.12)); }
    `);

    // keyword role per word index
    const words = ctx.words;
    const role = words.map(() => 'ink');
    for (let i = 0; i < words.length; i++) {
      for (const [seq, r] of KEYWORDS) {
        if (seq.every((k, j) => words[i + j] && norm(words[i + j].word) === k)) {
          for (let j = 0; j < seq.length; j++) role[i + j] = r;
        }
      }
    }
    const index = new Map(words.map((w, i) => [w, i]));
    const groups = curatedChunks(words) || ruleChunks(words);

    this.pill = ov.el(dom, { cls: 'captions-pill' });
    this.chunks = groups.map((g) => {
      const e = ov.el(dom, { cls: 'captions-chunk' });
      const blk = ov.el(e, { cls: 'captions-blk' });
      const spans = g.map((w) => {
        const s = document.createElement('span');
        s.className = 'captions-w';
        s.textContent = w.word.replace(/[,.]/g, '').toUpperCase();
        e.appendChild(s);
        return s;
      });
      return { e, blk, spans, g, roles: g.map((w) => role[index.get(w)]) };
    });
    // measure (fonts are loaded before init)
    for (const c of this.chunks) {
      c.e.style.display = '';
      c.w = c.e.offsetWidth;
      c.h = c.e.offsetHeight;
      c.fit = Math.min(1, MAX_W / c.w);
      c.boxes = c.spans.map((s) => ({ x: s.offsetLeft, w: s.offsetWidth, y: s.offsetTop, h: s.offsetHeight }));
      c.e.style.display = 'none';
    }
    // timing
    this.chunks.forEach((c, k) => {
      const next = this.chunks[k + 1];
      const first = c.g[0], last = c.g[c.g.length - 1];
      c.tIn = first.start - LEAD;
      const pause = next ? next.g[0].start - last.end : Infinity;
      c.hides = pause > 0.5;
      if (c.hides) { c.exS = last.end + HOLD; c.exE = c.exS + HIDE_DUR; }
      else { c.exE = next.g[0].start - LEAD; c.exS = c.exE - SWAP; }
      c.pillW = c.w * c.fit + 2 * PAD_X;
    });
  },
  update(t, lt, ctx) {
    const { A } = ctx;
    const { E } = A;
    const chunks = this.chunks;
    // index of the word being spoken (last started) in chunk c
    const active = (c) => {
      let a = 0;
      for (let j = 0; j < c.g.length; j++) if (t >= c.g[j].start - LEAD) a = j;
      return a;
    };
    // revealed line width: grows (and the line re-centres) as words pop in
    const rw = (c, j) => c.boxes[j].x + c.boxes[j].w;
    const lineW = (c) => {
      const a = active(c);
      if (a === 0) return rw(c, 0);
      const st = c.g[a].start - LEAD;
      return A.lerp(rw(c, a - 1), rw(c, a), E.outExpo(A.prog(t, st, st + 0.16)));
    };

    // ---- pill: follows the current chunk, morphing width between chunks
    let pc = -1;
    for (let k = 0; k < chunks.length; k++) {
      const c = chunks[k], prev = chunks[k - 1];
      const contig = prev && !prev.hides;
      const t0 = contig ? c.tIn - SWAP : c.tIn - 0.04;
      if (t >= t0) pc = k; else break;
    }
    if (pc >= 0 && t < chunks[pc].exE + 0.001) {
      const c = chunks[pc], prev = chunks[pc - 1];
      const contig = prev && !prev.hides;
      const cw = lineW(c) * c.fit + 2 * PAD_X;
      let w = cw, scale = 1, opacity = 1, y = CY, blur = 0;
      if (contig) {
        const m = E.outExpo(A.prog(t, c.tIn - 0.03, c.tIn + 0.14));
        w = A.lerp(prev.pillW, cw, m);
        scale = 1 + 0.025 * A.pulse(t, c.tIn + 0.02, 0.16); // tiny breath on each swap
      } else {
        const p = A.prog(t, c.tIn - 0.04, c.tIn + 0.2);
        scale = 0.82 + 0.18 * E.outBack(p);
        opacity = A.prog(t, c.tIn - 0.04, c.tIn + 0.05);
        w = A.lerp(cw * 0.7, cw, E.outExpo(p));
        y = CY + 14 * (1 - E.outExpo(p));
      }
      if (c.hides) {
        const q = A.prog(t, c.exS, c.exE);
        opacity *= 1 - q;
        scale *= 1 - 0.08 * E.inCubic(q);
        blur = 6 * q;
        y += 10 * q;
      }
      this.pill.style.width = `${w.toFixed(1)}px`;
      // keyword glow: the pill picks up the keyword colour as it is spoken
      const a = active(c);
      const R = c.roles[a];
      const k = R === 'ink' ? 0 : A.hit(t, c.g[a].start, 0.5) * 0.8 + 0.2;
      const [kr, kg, kb] = hex(ROLE[R].block);
      this.pill.style.boxShadow = `0 16px 36px rgba(18,24,38,0.20), 0 3px 8px rgba(18,24,38,0.10), inset 0 1px 0 #fff` +
        (k > 0.01 ? `, 0 0 0 ${(2 + 3 * k).toFixed(2)}px rgba(${kr},${kg},${kb},${(0.32 * k).toFixed(3)}), 0 12px 40px rgba(${kr},${kg},${kb},${(0.3 * k).toFixed(3)})` : '');
      ctx.ov.place(this.pill, { x: 540, y, scale, opacity, blur });
    } else ctx.ov.place(this.pill, { visible: false });

    // ---- chunks
    for (const c of chunks) {
      if (t < c.tIn || t >= c.exE) { c.e.style.display = 'none'; continue; }
      const q = A.prog(t, c.exS, c.exE);
      const qe = E.inCubic(q);
      const sc = c.fit * (1 - 0.1 * qe);
      ctx.ov.place(c.e, {
        x: 540 - (lineW(c) * sc) / 2, ax: 0, y: CY + 4 - (c.hides ? -8 : 18) * qe,
        scale: sc, opacity: 1 - q, blur: 7 * q,
      });

      const a = active(c);

      c.spans.forEach((s, j) => {
        const st = c.g[j].start - LEAD;
        if (t < st) { s.style.opacity = '0'; s.style.transform = 'scale(0.5)'; s.style.filter = 'none'; return; }
        const p = A.prog(t, st, st + 0.2);
        const op = A.prog(t, st, st + 0.035);
        const sc0 = 0.5 + 0.5 * E.outBack(p);
        const rx = 62 * (1 - E.outCubic(A.prog(t, st, st + 0.16)));
        const y = 26 * (1 - E.outExpo(p));
        const bl = 9 * (1 - E.outCubic(A.prog(t, st, st + 0.11)));
        // active word stands slightly proud, settles back when the next starts
        const actK = j === a ? 1 : 1 - E.outCubic(A.prog(t, c.g[j + 1] ? c.g[j + 1].start - LEAD : 1e9, (c.g[j + 1] ? c.g[j + 1].start - LEAD : 1e9) + 0.12));
        const sc = sc0 * (1 + 0.05 * actK);
        s.style.opacity = op.toFixed(3);
        s.style.transform = `translateY(${y.toFixed(2)}px) rotateX(${rx.toFixed(2)}deg) scale(${sc.toFixed(4)})`;
        s.style.filter = bl > 0.05 ? `blur(${bl.toFixed(2)}px)` : 'none';
        const R = ROLE[c.roles[j]];
        // text turns to its "on block" colour as the block arrives (the
        // first word of a chunk pops in together with its block)
        let k = 0;
        if (j === a) k = j === 0 ? 1 : E.outExpo(A.prog(t, st, st + 0.13));
        if (k >= 0.999) s.style.color = R.on;
        else if (k <= 0.001) s.style.color = R.text;
        else {
          const c0 = hex(R.text), c1 = hex(R.on);
          s.style.color = `rgb(${c0.map((v, i) => Math.round(A.lerp(v, c1[i], k))).join(', ')})`;
        }
      });

      // highlight block slides from the previous word to the active one
      const box = (j) => {
        const b = c.boxes[j];
        return [b.x - BLK_PX, b.w + 2 * BLK_PX];
      };
      const st = c.g[a].start - LEAD;
      const m = E.outExpo(A.prog(t, st, st + 0.13));
      const [x1, w1] = box(a);
      let x = x1, w = w1, bs = 1, bo = 1;
      const c1 = hex(ROLE[c.roles[a]].block);
      let col = c1;
      if (a > 0) {
        const [x0, w0] = box(a - 1);
        x = A.lerp(x0, x1, m); w = A.lerp(w0, w1, m);
        const c0 = hex(ROLE[c.roles[a - 1]].block);
        col = c0.map((v, i) => A.lerp(v, c1[i], E.outCubic(A.prog(t, st, st + 0.08))));
        // squash-stretch while travelling
        bs = 1 + 0.06 * A.pulse(t, st + 0.05, 0.14);
      } else {
        const p = A.prog(t, st, st + 0.2);
        bs = 0.45 + 0.55 * E.outBack(p);
        bo = A.prog(t, st, st + 0.06);
      }
      const b = c.boxes[a];
      const top = b.y - 2, h = b.h + 4;
      const [r, g, bl] = col.map((v) => Math.round(v));
      Object.assign(c.blk.style, {
        width: `${w.toFixed(1)}px`, height: `${h}px`,
        transform: `translate(${x.toFixed(1)}px, ${top}px) scale(${(bs * 1.02).toFixed(4)}, ${(1.02 / Math.sqrt(bs)).toFixed(4)}) rotate(-1deg)`,
        opacity: bo.toFixed(3),
        backgroundColor: `rgb(${r}, ${g}, ${bl})`,
        boxShadow: `0 10px 22px rgba(${r}, ${g}, ${bl}, 0.34), 0 2px 4px rgba(18, 24, 38, 0.18)`,
      });
    }
  },
};
