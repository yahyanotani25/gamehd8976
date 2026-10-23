// Render still frames for review.
//   node render/preview.mjs --t 1.2,3.4 [--range a:b:step] [--scenes s2,captions]
//                           [--out previews/name] [--sheet 4] [--half]
// Writes <out>/t_<time>.png per frame and, with --sheet N, <out>/sheet.png:
// a labelled contact sheet N frames wide (half-size frames), easy to view.
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
const eng = await openEngine({ scenes: args.scenes });
const files = [];
const t0 = Date.now();
for (const t of times) {
  const buf = await eng.frame(t);
  const f = path.join(out, `t_${t.toFixed(2).padStart(6, '0')}.png`);
  fs.writeFileSync(f, buf);
  files.push([t, f]);
}
await eng.close();
console.log(`rendered ${times.length} frames in ${((Date.now() - t0) / 1000).toFixed(1)}s -> ${out}`);
if (args.sheet) {
  const cols = Number(args.sheet) || 4;
  const rows = Math.ceil(files.length / cols);
  const inputs = files.flatMap(([, f]) => ['-i', f]);
  const g = args.guides ? 'drawbox=y=230:h=470:w=iw:color=blue@0.5:t=3,drawbox=y=700:h=720:w=iw:color=green@0.5:t=3,drawbox=y=1440:h=240:w=iw:color=orange@0.6:t=3,drawbox=x=960:y=900:w=120:h=800:color=red@0.35:t=fill,drawbox=y=1680:h=240:w=iw:color=red@0.25:t=fill,drawbox=y=0:h=200:w=iw:color=red@0.25:t=fill,' : '';
  const lab = files.map(([t], i) => `[${i}:v]${g}scale=432:768,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='${t.toFixed(2)}s':x=10:y=10:fontsize=30:fontcolor=yellow:box=1:boxcolor=black@0.7[v${i}]`).join(';');
  const pads = [];
  for (let i = files.length; i < rows * cols; i++) pads.push(`color=c=black:s=432x768:d=1[p${i}]`);
  const all = files.map((_, i) => `[v${i}]`).join('') + pads.map((_, j) => `[p${files.length + j}]`).join('');
  const filter = [lab, ...pads].join(';') + `;${all}xstack=inputs=${rows * cols}:layout=${Array.from({ length: rows * cols }, (_, i) => `${(i % cols) * 432}_${Math.floor(i / cols) * 768}`).join('|')}[out]`;
  execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', ...inputs, '-filter_complex', filter, '-map', '[out]', '-frames:v', '1', path.join(out, 'sheet.png')]);
  console.log('sheet -> ' + path.join(out, 'sheet.png'));
}
