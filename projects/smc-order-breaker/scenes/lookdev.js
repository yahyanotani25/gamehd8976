// Look-development scene: exercises every kit piece for tuning the look.
export default {
  id: 'lookdev', start: 0, end: 100,
  init(ctx) {
    const { kit, PAL, group, ov, dom } = ctx;
    const data = [
      { o: 6.2, h: 6.6, l: 4.9, c: 5.1 }, { o: 5.1, h: 5.4, l: 3.6, c: 3.8 }, { o: 3.8, h: 4.1, l: 2.2, c: 2.4 },
      { o: 2.4, h: 2.6, l: 0.7, c: 1.0 }, { o: 1.0, h: 3.0, l: 0.4, c: 2.8 }, { o: 2.8, h: 4.9, l: 2.6, c: 4.6 },
      { o: 4.6, h: 7.0, l: 4.4, c: 6.8 },
    ];
    this.ch = kit.chart({ data, x0: -3, step: 1 });
    group.add(this.ch.group);
    this.zone = kit.zone({ x0: -0.4, x1: 5.5, y0: 0.4, y1: 2.6, color: PAL.zoneGreen });
    group.add(this.zone.group);
    this.box = kit.outlineBox({ cx: 0, cy: 1.65, w: 1.15, h: 2.6 });
    group.add(this.box.group);
    this.arrow = kit.arrow([-5.6, 6.5], [-2.2, 1.4], { color: PAL.red });
    this.arrow2 = kit.arrow([1.8, 1.0], [5.6, 5.8], { color: PAL.green });
    group.add(this.arrow.group, this.arrow2.group);
    this.title = kit.text3d('1. ORDER BLOCK', { font: 'bebas', size: 1.55, depth: 0.32, color: PAL.maroon });
    group.add(this.title.group);
    this.dust = kit.dust({ count: 60, w: 18, h: 30, zMin: 2, zMax: 14, size: 0.14 });
    group.add(this.dust.group);
    const bank = kit.svgIcon(ov.ICON3D.bank, { size: 1.6, color: PAL.navy, depth: 0.3 });
    bank.group.position.set(4.3, -2.2, 0.3);
    group.add(bank.group);
    this.pill = ov.el(dom, { cls: 'pill green', html: ov.ICON.target + 'ORDER BLOCK' });
  },
  update(t, lt, ctx) {
    const { cam, toScreen } = ctx;
    cam.frame({ cx: 0, cy: 3.2, width: 15, pitch: -12 + t * 2, yaw: 8 });
    this.ch.animate(t, [-1, -1, -1, -1, -1, -1, -1]);
    this.ch.candles[3].setGlow(1);
    this.zone.reveal(1);
    this.box.setDraw(1);
    this.arrow.setDraw(1);
    this.arrow2.setDraw(1);
    this.dust.update(t);
    ctx.pin(this.title.group, { x: 540, y: 470, z: 0.6, heightPx: 118, worldHeight: this.title.capH });

    const p = toScreen([2.5, 0.4, 0.4]);
    ctx.ov.place(this.pill, { x: p.x, y: p.y + 70 });
  },
};
