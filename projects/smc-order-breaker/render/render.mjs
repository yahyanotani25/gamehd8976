// Render the timeline to a lossless video.
//   node render/render.mjs --from 0 --to 31 --fps 60 --workers 3 --out out/master.mkv
// Each worker renders a contiguous slice in its own browser; slices are
// concatenated losslessly at the end.
import fs from 'fs';
import path from 'path';
import { spawn, execFileSync } from 'child_process';
import { openEngine } from './browser.mjs';
import { ROOT } from './server.mjs';

const args = Object.fromEntries(process.argv.slice(2).reduce((acc, a, i, arr) => {
  if (a.startsWith('--')) acc.push([a.slice(2), arr[i + 1] && !arr[i + 1].startsWith('--') ? arr[i + 1] : true]);
  return acc;
}, []));
const fps = Number(args.fps || 60);
const out = path.resolve(ROOT, args.out || 'out/master.mkv');
fs.mkdirSync(path.dirname(out), { recursive: true });

async function renderSlice(f0, f1, file, label) {
  const eng = await openEngine({ scenes: args.scenes });
  const ff = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
    '-c:v', 'libx264rgb', '-preset', 'ultrafast', '-crf', '0', file], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', (c) => (c === 0 ? res() : rej(new Error('ffmpeg exit ' + c)))));
  const t0 = Date.now();
  for (let f = f0; f < f1; f++) {
    const buf = await eng.frame(f / fps);
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if ((f - f0) % 30 === 0) console.log(`[${label}] frame ${f}/${f1 - 1}  ${(((Date.now() - t0) / 1000) / Math.max(1, f - f0)).toFixed(2)}s/frame`);
  }
  ff.stdin.end();
  await done;
  await eng.close();
}

if (args.worker) {
  const [f0, f1] = String(args.worker).split(':').map(Number);
  await renderSlice(f0, f1, out, `w${f0}`);
  process.exit(0);
}

const probe = await openEngine({ scenes: args.scenes });
const duration = Number(args.to ?? probe.duration);
await probe.close();
const from = Number(args.from || 0);
const F0 = Math.round(from * fps), F1 = Math.round(duration * fps);
const workers = Number(args.workers || 3);
const per = Math.ceil((F1 - F0) / workers);
const parts = [];
const runs = [];
for (let w = 0; w < workers; w++) {
  const a = F0 + w * per, b = Math.min(F1, a + per);
  if (a >= b) break;
  const file = out.replace(/\.mkv$/, `.part${w}.mkv`);
  parts.push(file);
  const extra = args.scenes ? ['--scenes', args.scenes] : [];
  runs.push(new Promise((res, rej) => {
    const p = spawn(process.execPath, [path.join(ROOT, 'render/render.mjs'), '--worker', `${a}:${b}`, '--fps', String(fps), '--out', file, ...extra], { stdio: 'inherit' });
    p.on('close', (c) => (c === 0 ? res() : rej(new Error(`worker ${w} failed`))));
  }));
}
const t0 = Date.now();
await Promise.all(runs);
const list = out.replace(/\.mkv$/, '.txt');
fs.writeFileSync(list, parts.map((p) => `file '${p}'`).join('\n'));
execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', out]);
for (const p of parts) fs.unlinkSync(p);
fs.unlinkSync(list);
console.log(`rendered ${F1 - F0} frames in ${((Date.now() - t0) / 60000).toFixed(1)} min -> ${out}`);
