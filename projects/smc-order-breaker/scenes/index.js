// The timeline: every scene and transition in the film, in draw order
// (captions last so they sit on top). Spans and cuts follow docs/STORYBOARD.md.
import s1 from './s1.js';
import s2 from './s2.js';
import s3 from './s3.js';
import s4 from './s4.js';
import s5 from './s5.js';
import captions from './captions.js';
import lookdev from './lookdev.js';

export const DURATION = 31.0;
export const SCENES = [s1, s2, s3, s4, s5, captions];
// Not in the film; preview with --scenes lookdev.
export const EXAMPLES = [lookdev];
export const TRANSITIONS = [
  { at: 2.45, kind: 'zoom', dur: 0.4 },
  { at: 11.70, kind: 'whip', dir: [0.2, 0], dur: 0.36 },
  { at: 18.00, kind: 'zoom', dur: 0.4 },
  { at: 24.90, kind: 'zoom', dur: 0.4 },
];
