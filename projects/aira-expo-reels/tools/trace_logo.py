import sys, numpy as np, potrace, json
from PIL import Image, ImageDraw, ImageFilter
D = sys.argv[1]
im = np.asarray(Image.open(D + '/card_median.png').convert('RGB')).astype(np.float32)
L = im @ np.array([0.299, 0.587, 0.114])
x0, x1, y0, y1 = 340, 940, 280, 440
crop = L[y0:y1, x0:x1]
bg = np.median(L[y0:y1, x0:x0 + 20]); wh = np.percentile(crop, 99.7)
a = np.clip((crop - bg) / (wh - bg), 0, 1)
print('bg', bg, 'white', wh)
S = 8
big = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((a.shape[1] * S, a.shape[0] * S), Image.BICUBIC)).astype(np.float32) / 255
big = np.asarray(Image.fromarray((big * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(S * 0.35))).astype(np.float32) / 255
bm = potrace.Bitmap(big <= 0.5)
path = bm.trace(turdsize=50, alphamax=0.9, opticurve=True, opttolerance=0.2)
def flatten(curve, steps=24):
    P = lambda q: (float(q.x), float(q.y)) if hasattr(q, 'x') else (float(q[0]), float(q[1]))
    pts = [P(curve.start_point)]
    for seg in curve.segments:
        if seg.is_corner:
            pts += [P(seg.c), P(seg.end_point)]
        else:
            p0 = np.array(pts[-1]); c1 = np.array(P(seg.c1)); c2 = np.array(P(seg.c2)); p3 = np.array(P(seg.end_point))
            for t in np.linspace(0, 1, steps)[1:]:
                pts.append(tuple((1-t)**3*p0 + 3*(1-t)**2*t*c1 + 3*(1-t)*t**2*c2 + t**3*p3))
    return [(float(p[0]), float(p[1])) for p in pts]
polys = [flatten(c) for c in path.curves]
allp = np.concatenate([np.array(p) for p in polys])
mn = allp.min(0); mx = allp.max(0)
print('n curves', len(polys), 'bbox (8x px)', mn, mx, 'size', mx - mn)
# normalise to logo units: height = 1.0
h = mx[1] - mn[1]
norm = [[((x - mn[0]) / h, (y - mn[1]) / h) for x, y in p] for p in polys]
json.dump(dict(aspect=float((mx[0] - mn[0]) / h), polys=norm, orig_box_px=[float(v / S) for v in (*mn, *mx)], crop_origin=[x0, y0]), open(D + '/aira_logo_polys.json', 'w'))
# SVG (even-odd fill handles holes like the R bowl)
W = (mx[0] - mn[0]) / h * 1000
with open(D + '/AIRA_logo_traced.svg', 'w') as f:
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.1f} 1000"><path fill="#FFFFFF" fill-rule="evenodd" d="')
    for p in norm:
        f.write('M' + ' L'.join(f'{x*1000:.2f},{y*1000:.2f}' for x, y in p) + ' Z ')
    f.write('"/></svg>\n')
# rasterise high-res white-on-transparent PNG with even-odd via XOR compositing
def render(width, pad=0):
    sc = 4; Wt = int(width * sc); Ht = int(Wt / (W / 1000))
    acc = np.zeros((Ht, Wt), np.uint8)
    for p in norm:
        m = Image.new('L', (Wt, Ht), 0)
        ImageDraw.Draw(m).polygon([(x * Ht, y * Ht) for x, y in p], fill=255)
        acc ^= np.asarray(m)
    al = Image.fromarray(acc).resize((int(width), int(width / (W / 1000))), Image.LANCZOS)
    out = Image.new('RGBA', al.size, (255, 255, 255, 0)); out.putalpha(al)
    return out
render(3000).save(D + '/AIRA_logo_white_3000.png')
print('saved')
