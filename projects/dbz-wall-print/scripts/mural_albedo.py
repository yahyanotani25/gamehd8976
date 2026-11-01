"""Flatten the photo lighting of the rectified mural -> print-file albedo (paper white = 1)."""
import sys, numpy as np, cv2
S = sys.argv[1]
m = cv2.imread(f"{S}/art/mural_rect_x4.png").astype(np.float32) / 255
H, W = m.shape[:2]
# work at 1/8 res for the illumination envelope
sm = cv2.resize(m, (W // 8, H // 8), interpolation=cv2.INTER_AREA)
hsv = cv2.cvtColor((sm * 255).astype(np.uint8), cv2.COLOR_BGR2HSV)
Y = sm.mean(2)
white = (hsv[..., 1] < 40) & (Y > 0.55)
# local high percentile of near-white pixels -> envelope
env = np.zeros_like(sm)
k = 31
pad = k // 2
Yw = np.where(white[..., None], sm, np.nan)
from scipy.ndimage import generic_filter
for c in range(3):
    ch = Yw[..., c]
    def p85(v):
        v = v[~np.isnan(v)]
        return np.percentile(v, 85) if len(v) > 20 else np.nan
    env[..., c] = generic_filter(ch, p85, size=k, mode='nearest')
# fill nans by nearest valid + smooth
valid = ~np.isnan(env[..., 0])
from scipy.ndimage import distance_transform_edt
idx = distance_transform_edt(~valid, return_distances=False, return_indices=True)
env = env[idx[0], idx[1]]
env = cv2.GaussianBlur(env, (0, 0), 6)
env = cv2.resize(env, (W, H), interpolation=cv2.INTER_CUBIC)
alb = np.clip(m / np.maximum(env, 0.3), 0, 1.0)
# print look: ink black is not perfectly black; keep colours vivid
alb = 0.035 + 0.965 * alb
cv2.imwrite(f"{S}/art/mural_albedo.png", (alb * 255).round().astype(np.uint8))
cv2.imwrite(f"{S}/art/mural_albedo_small.jpg", cv2.resize((alb * 255).astype(np.uint8), (W // 4, H // 4), interpolation=cv2.INTER_AREA))
print("env range", env.min(), env.max())
