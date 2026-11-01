import sys, numpy as np, cv2
S = sys.argv[1]; sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from match import load
X0, Y0, X1, Y1, R = -100, 0, 1400, 1400, 2.0   # W canvas and px per W
CW, CH = int((X1-X0)*R), int((Y1-Y0)*R)
Wc2W = np.array([[1/R, 0, X0], [0, 1/R, Y0], [0, 0, 1.0]])   # canvas px -> W
np.save(f"{S}/track/Wc2W.npy", Wc2W)
order = [559, 0, 895, 799]     # later ones override (higher res)
acc = np.zeros((CH, CW, 3), np.float32); have = np.zeros((CH, CW), bool)
srcmap = np.full((CH, CW), -1, np.int16)
for k in order:
    H = np.load(f"{S}/track/anchor_{k}.npy") @ Wc2W     # canvas -> frame
    im = load(S, k)
    w = cv2.warpPerspective(im, np.linalg.inv(H), (CW, CH), flags=cv2.INTER_CUBIC)
    v = cv2.warpPerspective(np.full(im.shape[:2], 255, np.uint8), np.linalg.inv(H), (CW, CH), flags=cv2.INTER_NEAREST) > 0
    hsv = cv2.cvtColor(w, cv2.COLOR_BGR2HSV)
    ok = v & (hsv[..., 2] > 110)
    ok = cv2.erode(ok.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
    acc[ok] = w[ok]; have |= ok; srcmap[ok] = k
    cv2.imwrite(f"{S}/track/plate_from_{k}.jpg", w)
cv2.imwrite(f"{S}/track/plate.png", acc.astype(np.uint8))
np.save(f"{S}/track/plate_src.npy", srcmap)
small = cv2.resize(acc.astype(np.uint8), (CW//4, CH//4))
# draw W grid every 100 units
for x in range(X0, X1+1, 100):
    cx = int((x - X0) * R / 4); cv2.line(small, (cx, 0), (cx, CH//4), (0, 0, 255) if x % 500 == 0 else (0, 200, 0), 1)
    cv2.putText(small, str(x), (cx+2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0,0,255), 1)
for y in range(Y0, Y1+1, 100):
    cy = int((y - Y0) * R / 4); cv2.line(small, (0, cy), (CW//4, cy), (0, 0, 255) if y % 500 == 0 else (0, 200, 0), 1)
    cv2.putText(small, str(y), (2, cy-2), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0,0,255), 1)
cv2.imwrite(f"{S}/track/plate_small.png", small)
