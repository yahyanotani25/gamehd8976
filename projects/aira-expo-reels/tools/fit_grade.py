"""Fit raw->reference colour transform from matched frame pairs; write a 33^3 .cube LUT + vignette estimate."""
import sys, cv2, numpy as np, subprocess, json
sys.path.insert(0, sys.argv[1])
from match_frames import grab, score
REF = sys.argv[2]; PRX = sys.argv[3]; OUT = sys.argv[4]
pairs = [(2.8, 'C0004', 2.10), (16.5, 'C0019', 1.10), (21.0, 'C0021', 1.90), (7.0, 'C0045', 2.30), (24.5, 'C0040', 1.90)]
X, Y, R = [], [], []
dbg = []
for rt, clip, pt in pairs:
    a = grab(REF, rt)
    best = (0, None, None)
    for dt in np.arange(-0.16, 0.17, 0.04):
        b = grab(f'{PRX}/{clip}.mp4', max(0, pt + dt))
        if b is None: continue
        s, H = score(a, b)
        if s > best[0]: best = (s, H, b)
    s, H, b = best
    w = cv2.warpPerspective(b, H, (640, 360), flags=cv2.INTER_LINEAR)
    valid = cv2.warpPerspective(np.ones((360, 640), np.uint8), H, (640, 360), flags=cv2.INTER_NEAREST) > 0
    valid = cv2.erode(valid.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    g = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32)
    grad = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    m = valid & (grad < 40)
    # also exclude letterbox rows in ref (black bars at top/bottom rows)
    m[:4] = False; m[-4:] = False
    yy, xx = np.mgrid[0:360, 0:640]
    r = np.hypot((xx - 320) / 320, (yy - 180) / 180) / np.sqrt(2)
    X.append(w[m][:, ::-1] / 255.0); Y.append(a[m][:, ::-1] / 255.0); R.append(r[m])
    dbg.append(np.hstack([w, a]))
    print(clip, 'inliers', s, 'pixels', int(m.sum()))
cv2.imwrite(OUT + '/pairs.jpg', np.vstack(dbg))
X = np.vstack(X); Y = np.vstack(Y); R = np.concatenate(R)
def feats(x):
    r, g, b = x[:, 0], x[:, 1], x[:, 2]
    cols = [np.ones_like(r), r, g, b, r*r, g*g, b*b, r*g, g*b, r*b, r*r*r, g*g*g, b*b*b, r*r*g, r*r*b, g*g*r, g*g*b, b*b*r, b*b*g, r*g*b]
    return np.stack(cols, 1)
c = R < 0.45  # centre pixels for colour fit
F = feats(X[c]); lam = 1e-3
W = np.linalg.solve(F.T @ F + lam * np.eye(F.shape[1]), F.T @ Y[c])
pred = np.clip(feats(X) @ W, 0, 1)
err = np.abs(pred - Y)
print('MAE centre', err[c].mean(0) * 255, 'all', err.mean(0) * 255)
# vignette: ratio of luminance ref/pred by radius bins
lum = lambda z: z @ np.array([0.2126, 0.7152, 0.0722])
bins = np.linspace(0, 1, 11); vig = []
for i in range(10):
    s = (R >= bins[i]) & (R < bins[i+1]) & (lum(pred) > 0.08)
    vig.append(float(np.median(lum(Y[s]) / np.maximum(lum(pred[s]), 1e-3))) if s.sum() > 200 else None)
print('vignette ratio by radius', [None if v is None else round(v, 3) for v in vig])
# identity check on curve: grey ramp
ramp = np.linspace(0, 1, 11)[:, None].repeat(3, 1)
print('grey ramp ->', np.round(np.clip(feats(ramp) @ W, 0, 1) * 255).astype(int).tolist())
# write LUT
N = 33; gr = np.linspace(0, 1, N)
bb, gg, rr = np.meshgrid(gr, gr, gr, indexing='ij')
pts = np.stack([rr.ravel(), gg.ravel(), bb.ravel()], 1)
out = np.clip(feats(pts) @ W, 0, 1)
with open(OUT + '/ref_grade.cube', 'w') as f:
    f.write('TITLE "AIRA reference match"\nLUT_3D_SIZE 33\n')
    for v in out: f.write(f'{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n')
np.save(OUT + '/grade_W.npy', W)
json.dump(dict(vignette=vig), open(OUT + '/vignette.json', 'w'))
print('saturation check: mean chroma raw vs ref vs pred',
      [float(np.mean(np.std(z, 1))) for z in (X, Y, pred)])
