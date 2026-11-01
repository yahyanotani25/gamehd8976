"""Temporal-median clean plate of the wall in W space for one shot, low-frequency-normalised to the mosaic albedo."""
import sys, numpy as np, cv2
S = sys.argv[1]; name = sys.argv[2]
a, b, step = [int(v) for v in sys.argv[3].split(":")]
X0, X1, Y0, Y1 = [float(v) for v in sys.argv[4].split(",")]
R = float(sys.argv[5])
FGT = float(sys.argv[6]) if len(sys.argv) > 6 else 0.07
H = np.load(f"{S}/track/H_all.npy")
CW, CH = int((X1 - X0) * R), int((Y1 - Y0) * R)
T = np.array([[1 / R, 0, X0], [0, 1 / R, Y0], [0, 0, 1.0]])        # plate px -> W
frames = list(range(a, b + 1, step))
stack = np.full((len(frames), CH, CW, 3), np.nan, np.float16)
for k, i in enumerate(frames):
    im = cv2.imread(f"{S}/ref_full/{i+1:04d}.png").astype(np.float32) / 255
    M = np.linalg.inv(H[i] @ T)
    w = cv2.warpPerspective(im, M, (CW, CH), flags=cv2.INTER_CUBIC)
    v = cv2.warpPerspective(np.ones(im.shape[:2], np.float32), M, (CW, CH), flags=cv2.INTER_NEAREST) > 0.5
    v = cv2.erode(v.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    Y = w.mean(2)
    hsv = cv2.cvtColor((np.clip(w, 0, 1) * 255).astype(np.uint8), cv2.COLOR_BGR2HSV)
    fg = (Y < FGT) | ((hsv[..., 0] > 118) & (hsv[..., 0] < 165) & (hsv[..., 1] > 150) & (hsv[..., 2] > 170))
    fg = cv2.dilate(fg.astype(np.uint8), np.ones((int(4 * R) | 1, int(4 * R) | 1), np.uint8)) > 0
    ok = v & ~fg
    w[~ok] = np.nan
    stack[k] = w.astype(np.float16)
# per-frame gain normalisation against a first-pass median
med0 = np.nanmedian(stack[:, ::4, ::4].astype(np.float32), axis=0)
for k in range(len(frames)):
    s = stack[k, ::4, ::4].astype(np.float32)
    ok = ~np.isnan(s) & ~np.isnan(med0)
    if ok.sum() > 1000:
        g = np.median(med0[ok] / np.maximum(s[ok], 1e-3))
        stack[k] = (stack[k].astype(np.float32) * g).astype(np.float16)
CP = np.zeros((CH, CW, 3), np.float32); cnt = np.zeros((CH, CW), np.int32)
for y0 in range(0, CH, 128):
    blk = stack[:, y0:y0 + 128].astype(np.float32)
    CP[y0:y0 + 128] = np.nanmedian(blk, axis=0)
    cnt[y0:y0 + 128] = (~np.isnan(blk[..., 0])).sum(0)
have = (cnt >= 3) & ~np.isnan(CP[..., 0])
CP = np.nan_to_num(CP, nan=1.0)
# low-frequency normalisation to mosaic albedo
ALB = np.load(f"{S}/comp/albedo_W.npy").astype(np.float32); TA = np.load(f"{S}/comp/albedo_T.npy")
Mal = np.linalg.inv(TA) @ T          # plate px -> albedo canvas px
alb = cv2.warpPerspective(ALB, Mal, (CW, CH), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderValue=(1, 1, 1))
sig = 30 * R
wgt = have.astype(np.float32)
lo_cp = cv2.GaussianBlur(CP * wgt[..., None], (0, 0), sig) / np.maximum(cv2.GaussianBlur(wgt, (0, 0), sig), 1e-4)[..., None]
lo_al = cv2.GaussianBlur(alb * wgt[..., None], (0, 0), sig) / np.maximum(cv2.GaussianBlur(wgt, (0, 0), sig), 1e-4)[..., None]
A = np.where(have[..., None], CP * lo_al / np.maximum(lo_cp, 1e-3), alb)
np.save(f"{S}/comp/plate_{name}.npy", A.astype(np.float16)); np.save(f"{S}/comp/plate_{name}_T.npy", T)
np.save(f"{S}/comp/plate_{name}_have.npy", have)
cv2.imwrite(f"{S}/comp/plate_{name}.jpg", cv2.resize(np.clip(A * 200, 0, 255).astype(np.uint8), (CW // 2, CH // 2)))
print(name, "size", CW, CH, "have frac", have.mean())
