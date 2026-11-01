import sys, numpy as np, cv2
S = sys.argv[1]; sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from match import load
Wc2W = np.load(f"{S}/track/Wc2W.npy"); R = 1 / Wc2W[0, 0]; X0, Y0 = Wc2W[0, 2], Wc2W[1, 2]
CW, CH = int(1500 * R), int(1400 * R)
def wmask(x0, x1, y0, y1):
    m = np.zeros((CH, CW), bool)
    m[int((y0-Y0)*R):int((y1-Y0)*R), int((x0-X0)*R):int((x1-X0)*R)] = True
    return m
acc = np.zeros((CH, CW, 3), np.uint8); have = np.zeros((CH, CW), bool)
# (frame, W-region that is clean wall/art in that frame)
srcs = [(0, (-100, 330, 195, 1125)), (559, (-100, 955, 195, 1125)), (895, (240, 720, 260, 1100)), (799, (660, 955, 170, 1125))]
for k, reg in srcs:
    H = np.load(f"{S}/track/anchor_{k}.npy") @ Wc2W
    im = load(S, k)
    w = cv2.warpPerspective(im, np.linalg.inv(H), (CW, CH), flags=cv2.INTER_CUBIC)
    v = cv2.warpPerspective(np.full(im.shape[:2], 255, np.uint8), np.linalg.inv(H), (CW, CH), flags=cv2.INTER_NEAREST) > 0
    v = cv2.erode(v.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    ok = v & wmask(*reg)
    acc[ok] = w[ok]; have |= ok
cv2.imwrite(f"{S}/track/plate2.png", acc)
cv2.imwrite(f"{S}/track/plate2_valid.png", have.astype(np.uint8) * 255)
cv2.imwrite(f"{S}/track/plate2_small.jpg", cv2.resize(acc, (CW // 4, CH // 4)))
