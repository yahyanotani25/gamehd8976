import cv2, numpy as np, glob, sys
fs = sorted(glob.glob(sys.argv[1] + "/*.png"))
ims = [cv2.imread(f).astype(np.float32) for f in fs]
def d(a, b): return float(np.mean(np.abs(ims[a] - ims[b])))
for i in range(1, len(ims) - 1):
    a, b, c = d(i, i - 1), d(i, i + 1), d(i - 1, i + 1)
    if a > 1.6 * c + 2 and b > 1.6 * c + 2 and min(a, b) > 6:
        print(i, round(a, 1), round(b, 1), round(c, 1))
