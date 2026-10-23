// Gather every scene's SFX cues into audio/cues.json for the mixer.
//   node audio/collect_cues.mjs
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const { SCENES } = await import(path.join(here, '..', 'scenes', 'index.js'));
const palette = JSON.parse(fs.readFileSync(path.join(here, 'sfx', 'palette.json'), 'utf8'));
const cues = [];
for (const s of SCENES) {
  for (const c of s.cues || []) {
    if (!palette[c.sfx]) throw new Error(`${s.id}: unknown sfx "${c.sfx}" at ${c.t}`);
    if (!(c.t >= 0 && c.t <= 31.5)) throw new Error(`${s.id}: cue time out of range: ${JSON.stringify(c)}`);
    cues.push({ ...c, scene: s.id });
  }
}
cues.sort((a, b) => a.t - b.t);
// Two scenes often both mark the cut between them (e.g. a whoosh at 18.00):
// keep one of any same sound from different scenes within 80 ms.
const merged = [];
for (const c of cues) {
  const dup = merged.find((m) => m.sfx === c.sfx && m.scene !== c.scene && Math.abs(m.t - c.t) < 0.08);
  if (dup) { dup.gain = Math.max(dup.gain ?? 0, c.gain ?? 0); continue; }
  merged.push(c);
}
cues.length = 0;
cues.push(...merged);
fs.writeFileSync(path.join(here, 'cues.json'), JSON.stringify(cues, null, 1));
const by = {};
for (const c of cues) by[c.scene] = (by[c.scene] || 0) + 1;
console.log(`${cues.length} cues`, by);
