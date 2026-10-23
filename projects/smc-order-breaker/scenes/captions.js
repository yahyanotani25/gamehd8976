// Scene captions (placeholder until built). See docs/STORYBOARD.md.
export default {
  id: 'captions', start: 0, end: 31.00,
  cues: [],
  init(ctx) {
    this.label = ctx.ov.el(ctx.dom, { cls: 'pill ink', html: 'captions placeholder' });
  },
  update(t, lt, ctx) {
    ctx.cam.frame({ cx: 0, cy: 3, width: 13.5 });
    ctx.ov.place(this.label, { x: 540, y: 'captions' === 'captions' ? 1560 : 960 });
  },
};
