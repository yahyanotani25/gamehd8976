// Scene s5 (placeholder until built). See docs/STORYBOARD.md.
export default {
  id: 's5', start: 24.90, end: 31.00,
  cues: [],
  init(ctx) {
    this.label = ctx.ov.el(ctx.dom, { cls: 'pill ink', html: 's5 placeholder' });
  },
  update(t, lt, ctx) {
    ctx.cam.frame({ cx: 0, cy: 3, width: 13.5 });
    ctx.ov.place(this.label, { x: 540, y: 's5' === 'captions' ? 1560 : 960 });
  },
};
