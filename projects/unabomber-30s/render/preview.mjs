// Render still frames for review.
//   node render/preview.mjs --t 1.2,3.4 [--range a:b:step] [--scenes s2,lookdev]
//                           [--out previews/name] [--sheet 3] [--guides] [--jpeg]
// Writes <out>/t_<time>.png per frame and, with --sheet N, <out>/sheet.jpg: a
// labelled contact sheet N frames wide (640x360 thumbnails) to open with Read.
// --guides draws title-safe (90 %) and the 2.39:1 letterbox lines on the sheet.
import fs from 'fs';
import path from 'path';
import { execFileSync } from 'child_process';
import { openEngine } from './browser.mjs';
import { ROOT } from './server.mjs';

const args = Object.fromEntries(process.argv.slice(2).reduce((acc, a, i, arr) => {
  if (a.startsWith('--')) acc.push([a.slice(2), arr[i + 1] && !arr[i + 1].startsWith('--') ? arr[i + 1] : true]);
  return acc;
}, []));
let times = [];
if (args.t) times.push(...String(args.t).split(',').map(Number));
if (args.range) { const [a, b, s] = String(args.range).split(':').map(Number); for (let x = a; x <= b + 1e-6; x += s) times.push(+x.toFixed(4)); }
if (!times.length) { console.error('give --t or --range'); process.exit(1); }
const out = path.resolve(ROOT, args.out || 'previews/tmp');
fs.mkdirSync(out, { recursive: true });
const eng = await openEngine({ scenes: args.scenes, query: args.overlay ? { overlay: args.overlay } : {} });
const files = [];
const t0 = Date.now();
const ext = args.jpeg ? 'jpg' : 'png';
for (const t of times) {
  const f0 = Date.now();
  const buf = await eng.frame(t, { format: args.jpeg ? 'jpeg' : 'png' });
  const f = path.join(out, `t_${t.toFixed(2).padStart(6, '0')}.${ext}`);
  fs.writeFileSync(f, buf);
  files.push([t, f]);
  if (args.verbose) console.log(`t=${t.toFixed(3)}  ${((Date.now() - f0) / 1000).toFixed(2)}s`, JSON.stringify((await eng.stats()).last));
}
const st = await eng.stats();
await eng.close();
console.log(`rendered ${times.length} frames in ${((Date.now() - t0) / 1000).toFixed(1)}s -> ${out}  (avg world ${st.worldMs.toFixed(0)} ms, dom ${st.domMs.toFixed(0)} ms, post ${st.postMs.toFixed(0)} ms)`);
if (args.sheet) {
  const cols = Number(args.sheet) || 3, TW = 640, TH = 360;
  const rows = Math.ceil(files.length / cols);
  const inputs = files.flatMap(([, f]) => ['-i', f]);
  const g = args.guides ? `drawbox=x=96:y=54:w=1728:h=972:color=yellow@0.6:t=3,drawbox=x=0:y=138:w=1920:h=804:color=red@0.6:t=3,` : '';
  const lab = files.map(([t], i) => `[${i}:v]${g}scale=${TW}:${TH},drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='${t.toFixed(2)}s':x=8:y=8:fontsize=22:fontcolor=yellow:box=1:boxcolor=black@0.7[v${i}]`).join(';');
  const pads = [];
  for (let i = files.length; i < rows * cols; i++) pads.push(`color=c=black:s=${TW}x${TH}:d=1[p${i}]`);
  const all = files.map((_, i) => `[v${i}]`).join('') + pads.map((_, j) => `[p${files.length + j}]`).join('');
  const n = rows * cols;
  const filter = [lab, ...pads].join(';') + (n > 1 ? `;${all}xstack=inputs=${n}:layout=${Array.from({ length: n }, (_, i) => `${(i % cols) * TW}_${Math.floor(i / cols) * TH}`).join('|')}[out]` : `;${all}null[out]`);
  execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', ...inputs, '-filter_complex', filter, '-map', '[out]', '-frames:v', '1', '-q:v', '3', path.join(out, 'sheet.jpg')]);
  console.log('sheet -> ' + path.join(out, 'sheet.jpg'));
}
