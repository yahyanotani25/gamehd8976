// Scene s4 (placeholder until built). See docs/STORYBOARD.md.
export default {
  id: 's4', start: 18.00, end: 24.90,
  cues: [],
  init(ctx) {
    this.label = ctx.ov.el(ctx.dom, { cls: 'pill ink', html: 's4 placeholder' });
  },
  update(t, lt, ctx) {
    ctx.cam.frame({ cx: 0, cy: 3, width: 13.5 });
    ctx.ov.place(this.label, { x: 540, y: 's4' === 'captions' ? 1560 : 960 });
  },
};
