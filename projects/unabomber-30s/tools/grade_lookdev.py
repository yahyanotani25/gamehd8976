"""Look-dev prototype of the docs/STYLE.md grade (section 5): applies a look to stills
and writes before|after strips. The real grade lives in the engine (LUT + shader);
keep the numbers here and in STYLE.md in sync.
usage: python3 -I tools/grade_lookdev.py out.jpg {wild|modern|cabin|secret} in1.jpg [in2.jpg ...]"""
import sys, numpy as np
from PIL import Image

LOOKS = {
  # wb: grey-world strength | lift/gain per RGB | gamma: out = in**gamma (>1 darkens) |
  # sat: global, gsat: greens (hue 50-170), ghue: nudge greens toward cyan | black/white: output
  # points after the S-curve | red_keep: 1 keeps reds (hue 335-25) at full saturation |
  # contrast: optional, around mid grey (modern only)
  'wild':   dict(wb=0.6, lift=(-0.004, 0.006, 0.020), gamma=(1.03, 1.0, 0.97), gain=(0.97, 0.99, 1.03), sat=0.80, gsat=0.62, ghue=-10, black=0.025, white=0.93, red_keep=0.0),
  'modern': dict(wb=0.5, lift=(0.000, 0.010, 0.000), gamma=(1.00, 0.98, 1.02), gain=(1.02, 1.03, 0.97), sat=0.95, gsat=0.95, ghue=0,   black=0.020, white=0.95, red_keep=0.0, contrast=1.15),
  'cabin':  dict(wb=0.5, lift=(0.010, 0.006, 0.000), gamma=(0.98, 1.0, 1.04), gain=(1.03, 1.00, 0.95), sat=0.85, gsat=0.70, ghue=-6,  black=0.020, white=0.92, red_keep=0.0),
  'secret': dict(wb=0.6, lift=(0.000, 0.004, 0.010), gamma=(1.02, 1.03, 1.03), gain=(1.00, 0.98, 0.96), sat=0.45, gsat=0.40, ghue=0,   black=0.015, white=0.90, red_keep=1.0),
}

def rgb2hsv(c):
    r,g,b = c[...,0],c[...,1],c[...,2]
    mx = c.max(-1); mn = c.min(-1); d = mx-mn+1e-8
    h = np.where(mx==r, ((g-b)/d)%6, np.where(mx==g, (b-r)/d+2, (r-g)/d+4))*60
    s = np.where(mx>0, (mx-mn)/(mx+1e-8), 0); return h, s, mx

def grade(img, L, seed=1):
    x = img.astype(np.float32)/255.0
    # 1. partial grey-world white balance (archival photos have casts)
    m = x.reshape(-1,3).mean(0); x = x * (1 + L['wb']*(m.mean()/m - 1))
    x = np.clip(x, 0, 1)
    # 2. lift / gamma / gain
    lift, gam, gain = map(np.array, (L['lift'], L['gamma'], L['gain']))
    x = gain*(x + lift*(1-x)); x = np.clip(x,0,1)**gam
    # 3. saturation, greens desaturated and pushed toward teal; reds optionally kept
    h,s,v = rgb2hsv(x)
    luma = (x@np.array([0.2126,0.7152,0.0722]))[...,None]
    gw = np.clip(1-np.abs(h-110)/60,0,1)[...,None]           # greens/yellow-greens
    rw = np.clip(1-np.minimum(np.abs(h-0),np.abs(h-360))/25,0,1)[...,None]
    sat = L['sat']*(1-gw) + L['gsat']*gw
    sat = sat*(1-rw*L['red_keep']) + 1.0*rw*L['red_keep']
    x = luma + (x-luma)*sat
    x = (x-0.5)*L.get('contrast',1.0)+0.5
    # green hue nudge toward cyan: rotate a little blue into greens
    x[...,2:3] += gw*(-L['ghue']/100.0)*np.clip(x[...,1:2]-x[...,2:3],0,1)
    # 4. filmic S-curve + shoulder, then black/white points
    x = np.clip(x,0,1); x = x*x*(3-2*x)*0.35 + x*0.65
    x = L['black'] + (L['white']-L['black'])*x
    # 5. vignette
    H,W = x.shape[:2]; yy,xx = np.mgrid[0:H,0:W]; q = np.hypot((xx/W-0.5)*0.9*1.0,(yy/H-0.5)*1.0)*1.25
    x *= (1-0.22*np.clip((q-0.25)/0.6,0,1)**2)[...,None]
    # 6. grain: luma-weighted, 80% mono
    rng = np.random.default_rng(seed); g = rng.normal(0,1,(H,W,1)); gc = rng.normal(0,1,(H,W,3))
    w = 0.024*(4*luma*(1-luma)+0.35)
    x = x + w*(0.8*g+0.2*gc)
    return (np.clip(x,0,1)*255+0.5).astype(np.uint8)

out, look, *ins = sys.argv[1:]
tiles = []
for p in ins:
    im = Image.open(p).convert('RGB'); im.thumbnail((640,480))
    a = np.asarray(im); tiles.append(np.concatenate([a, grade(a, LOOKS[look])], 1))
Wm = max(t.shape[1] for t in tiles)
tiles = [np.pad(t, ((0,0),(0,Wm-t.shape[1]),(0,0))) for t in tiles]
Image.fromarray(np.concatenate(tiles,0)).save(out, quality=88)
