// Scene s1 (placeholder until built). See docs/STORYBOARD.md.
export default {
  id: 's1', start: 0, end: 2.45,
  cues: [],
  init(ctx) {
    this.label = ctx.ov.el(ctx.dom, { cls: 'pill ink', html: 's1 placeholder' });
  },
  update(t, lt, ctx) {
    ctx.cam.frame({ cx: 0, cy: 3, width: 13.5 });
    ctx.ov.place(this.label, { x: 540, y: 's1' === 'captions' ? 1560 : 960 });
  },
};
