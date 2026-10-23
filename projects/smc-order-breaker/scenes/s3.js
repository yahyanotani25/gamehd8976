// Scene s3 (placeholder until built). See docs/STORYBOARD.md.
export default {
  id: 's3', start: 11.70, end: 18.00,
  cues: [],
  init(ctx) {
    this.label = ctx.ov.el(ctx.dom, { cls: 'pill ink', html: 's3 placeholder' });
  },
  update(t, lt, ctx) {
    ctx.cam.frame({ cx: 0, cy: 3, width: 13.5 });
    ctx.ov.place(this.label, { x: 540, y: 's3' === 'captions' ? 1560 : 960 });
  },
};
