// Scene s2 (placeholder until built). See docs/STORYBOARD.md.
export default {
  id: 's2', start: 2.45, end: 11.70,
  cues: [],
  init(ctx) {
    this.label = ctx.ov.el(ctx.dom, { cls: 'pill ink', html: 's2 placeholder' });
  },
  update(t, lt, ctx) {
    ctx.cam.frame({ cx: 0, cy: 3, width: 13.5 });
    ctx.ov.place(this.label, { x: 540, y: 's2' === 'captions' ? 1560 : 960 });
  },
};
