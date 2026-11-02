"""The 1.5 s stripe transition of reference 1 (frames 633-677).

Each frame of the transition is a row of vertical panels; every panel is a
skewed copy of either the last frame of the wide shot or the first frame of
the reveal.  For each panel we find that copy's homography (SIFT against both
source frames); chained with the source frame's wall track it gives the wall
of that panel, which is then rendered like any other frame.  The transition
plays exactly as in the original.

usage: python wipe.py
"""
import numpy as np
import cv2
from common import *

A, B = 633, 677
SRC = {"E": 632, "F": 678}
SIFT = cv2.SIFT_create(nfeatures=8000, contrastThreshold=0.01)
BF = cv2.BFMatcher(cv2.NORM_L2)


def panels(fr):
    g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    colmean = g.mean(0)
    dark = colmean < 35
    # seams: columns whose neighbour differs far more than usual
    d = np.abs(np.diff(g, axis=1)).mean(0)
    med = np.median(d) + 1e-3
    seam = np.zeros(FW, bool)
    seam[1:] = d > 6 * med
    bnd = dark | seam
    out, s = [], None
    for x in range(FW + 1):
        b = x == FW or bnd[x]
        if not b and s is None:
            s = x
        if b and s is not None:
            if x - s >= 12:
                out.append((s, x))
            s = None
    return out


def feats(img, mask=None):
    return SIFT.detectAndCompute(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), mask)


def main():
    from composite2 import Renderer
    R = Renderer()
    src_feats = {k: feats(read_frame(i)) for k, i in SRC.items()}
    states = {"E": R.prog[SRC["E"] - 1], "F": [1e6, 0.0, 0.0]}
    outdir = os.path.join(WORK, "render2")
    prev = []
    for i in range(A, B + 1):
        fr = read_frame(i)
        found = []
        for (x0, x1) in panels(fr):
            m = np.zeros((FH, FW), np.uint8)
            m[:, x0:x1] = 255
            kb, db = feats(fr, m)
            best = (None, 0, None)
            if db is not None and len(kb) >= 8:
                for k, (ka, da) in src_feats.items():
                    mm = BF.knnMatch(db, da, k=2)
                    good = [p[0] for p in mm if len(p) == 2 and p[0].distance < 0.75 * p[1].distance]
                    if len(good) < 10:
                        continue
                    pb = np.float32([kb[g.queryIdx].pt for g in good])
                    pa = np.float32([ka[g.trainIdx].pt for g in good])
                    H, inl = cv2.findHomography(pa, pb, cv2.USAC_MAGSAC, 3.0, maxIters=10000)
                    if H is not None and inl.sum() > best[1]:
                        best = (H, int(inl.sum()), k)
            found.append([x0, x1] + list(best))
        good = [f for f in found if f[2] is not None and f[3] >= 12]
        for f in found:
            if f[2] is None or f[3] < 12:
                pool = good or prev
                if not pool:
                    continue
                c = (f[0] + f[1]) / 2
                g = min(pool, key=lambda q: abs((q[0] + q[1]) / 2 - c))
                f[2], f[3], f[4] = g[2], -1, g[4]
        out = fr.copy()
        for x0, x1, H, n, k in found:
            if H is None:
                continue
            Hc = H @ R.tr[SRC[k]]
            img = R.render(i, H=Hc, fr=fr, st=states[k])
            out[:, x0:x1] = img[:, x0:x1]
        prev = [f for f in found if f[2] is not None and f[3] != -1] or prev
        cv2.imwrite(os.path.join(outdir, f"{i:04d}.png"), out)
        print(i, [(f[0], f[1], f[4], f[3]) for f in found], flush=True)


if __name__ == "__main__":
    main()
