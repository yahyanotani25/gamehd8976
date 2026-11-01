"""Balloon-art albedo in wall space W (1 px/W): gain-matched mosaic / harmonic-interpolated white-wall illumination."""
import sys, numpy as np, cv2
from scipy.sparse import lil_matrix, csr_matrix
from scipy.sparse.linalg import spsolve
S = sys.argv[1]
H = np.load(f"{S}/track/H_all.npy")
XA, YA, XB, YB = -300, 150, 1300, 1200
CW, CH = XB - XA, YB - YA
T = np.array([[1, 0, XA], [0, 1, YA], [0, 0, 1.0]])
def warpW(i):
    im = cv2.imread(f"{S}/ref_full/{i+1:04d}.png").astype(np.float32) / 255
    M = np.linalg.inv(H[i] @ T)
    w = cv2.warpPerspective(im, M, (CW, CH), flags=cv2.INTER_AREA)
    v = cv2.warpPerspective(np.ones(im.shape[:2], np.float32), M, (CW, CH), flags=cv2.INTER_NEAREST)
    v = cv2.erode(v, np.ones((7, 7), np.uint8)) > 0.5
    return w, v
def rect(x0, x1, y0, y1):
    m = np.zeros((CH, CW), bool); m[max(0, y0 - YA):max(0, y1 - YA), max(0, x0 - XA):max(0, x1 - XA)] = True; return m
WALL = rect(-300, 1300, 200, 1123)
ref, vref = warpW(559)
okref = vref & WALL & ~rect(843, 1300, 0, 2000)
mos = np.where(okref[..., None], ref, 0).astype(np.float32); have = okref.copy()
for k, reg in [(799, rect(660, 1010, 170, 1123)), (895, rect(240, 720, 260, 1123)), (0, rect(-300, 335, 200, 1123))]:
    w, v = warpW(k)
    reg = v & reg & WALL
    ov = reg & okref & (ref.mean(2) > 0.25)
    g = np.median(ref[ov] / np.maximum(w[ov], 1e-3), axis=0) if ov.sum() > 500 else np.ones(3)
    print("source", k, "gain", g.round(3), "overlap", int(ov.sum()))
    fill = reg & ~have
    mos[fill] = (w * g)[fill]; have |= fill
cv2.imwrite(f"{S}/comp/mosaic.png", np.clip(mos * 255, 0, 255).astype(np.uint8))
# white wall sample mask
hsv = cv2.cvtColor(np.clip(mos * 255, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV)
art_bbox = rect(100, 972, 345, 1018)
wall = have & WALL & ~art_bbox & (hsv[..., 1] < 55) & (hsv[..., 2] > 90)
# coarse grid (cell = 10 W units) medians, then harmonic fill
C = 10; gh, gw = CH // C, CW // C
grid = np.zeros((gh, gw, 3), np.float32); known = np.zeros((gh, gw), bool)
for gy in range(gh):
    for gx in range(gw):
        m = wall[gy*C:(gy+1)*C, gx*C:(gx+1)*C]
        if m.sum() > 0.5 * C * C:
            grid[gy, gx] = np.median(mos[gy*C:(gy+1)*C, gx*C:(gx+1)*C][m], axis=0); known[gy, gx] = True
# only solve inside the wall rows
idx = -np.ones((gh, gw), int); unk = ~known
n = int(unk.sum()); idx[unk] = np.arange(n)
A = lil_matrix((n, n)); B = np.zeros((n, 3))
for gy in range(gh):
    for gx in range(gw):
        if not unk[gy, gx]: continue
        r = idx[gy, gx]; deg = 0
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = gy + dy, gx + dx
            if 0 <= yy < gh and 0 <= xx < gw:
                deg += 1
                if unk[yy, xx]: A[r, idx[yy, xx]] = -1
                else: B[r] += grid[yy, xx]
        A[r, r] = deg
sol = spsolve(csr_matrix(A), B)
grid[unk] = sol
Ill = cv2.resize(grid, (CW, CH), interpolation=cv2.INTER_CUBIC)
Ill = cv2.GaussianBlur(Ill, (0, 0), 12)
alb = np.where(have[..., None], mos / np.maximum(Ill, 1e-3), 1.0).astype(np.float32)
alb = np.clip(alb, 0, 1.25)
np.save(f"{S}/comp/albedo_W.npy", alb.astype(np.float16)); np.save(f"{S}/comp/albedo_have.npy", have)
np.save(f"{S}/comp/albedo_T.npy", T)
cv2.imwrite(f"{S}/comp/albedo_W.png", np.clip(alb * 200, 0, 255).astype(np.uint8))
cv2.imwrite(f"{S}/comp/ill_W.png", np.clip(Ill * 255, 0, 255).astype(np.uint8))
print("wall albedo median", np.median(alb[wall], axis=0), "p5/p95", np.percentile(alb[wall].mean(1), [5, 95]))
