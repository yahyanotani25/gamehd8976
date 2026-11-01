import sys, numpy as np, cv2, json
S = sys.argv[1]; sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from match import load, homog
Wc2W = np.load(f"{S}/track/Wc2W.npy")
plate = cv2.imread(f"{S}/track/plate2.png"); pvalid = cv2.imread(f"{S}/track/plate2_valid.png", 0)
SIFT = cv2.SIFT_create(nfeatures=6000, contrastThreshold=0.008)
bf = cv2.BFMatcher(cv2.NORM_L2)
FW, FH = 720, 1280
def frame_feats(im):
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 2] > 70)).astype(np.uint8) * 255
    m = cv2.erode(m, np.ones((7, 7), np.uint8))
    kp, des = SIFT.detectAndCompute(g, m)
    return np.float32([k.pt for k in kp]), des
def synth(Hw2f):
    Hc2f = Hw2f @ Wc2W
    v = cv2.warpPerspective(plate, Hc2f, (FW, FH), flags=cv2.INTER_AREA if False else cv2.INTER_LINEAR)
    m = cv2.warpPerspective(pvalid, Hc2f, (FW, FH), flags=cv2.INTER_NEAREST)
    m = cv2.erode(m, np.ones((9, 9), np.uint8))
    return v, m
def refine(im, ff, Hguess, iters=2):
    H = Hguess.copy(); n = 0
    for it in range(iters):
        v, m = synth(H)
        g = cv2.cvtColor(v, cv2.COLOR_BGR2GRAY)
        kp, des = SIFT.detectAndCompute(g, m)
        if des is None or len(kp) < 10 or ff[1] is None: return None, 0
        mm = bf.knnMatch(des, ff[1], k=2)
        good = [x[0] for x in mm if len(x) == 2 and x[0].distance < 0.8 * x[1].distance]
        if len(good) < 10: return None, 0
        A = np.float32([kp[g.queryIdx].pt for g in good]); B = np.float32([ff[0][g.trainIdx] for g in good])
        # also require spatial consistency: synthesized view should already be close
        d = np.linalg.norm(A - B, axis=1); sel = d < (80 if it == 0 else 25)
        A, B = A[sel], B[sel]
        if len(A) < 10: return None, 0
        dH, inl = cv2.findHomography(A, B, cv2.USAC_MAGSAC, 2.0, maxIters=10000, confidence=0.9999)
        if dH is None: return None, 0
        n = int(inl.sum())
        H = dH @ H
    return H / H[2, 2], n
def run(start, end, Hstart, out):
    step = 1 if end >= start else -1
    H = Hstart.copy(); prev = None
    for i in range(start, end + step, step):
        im = load(S, i); ff = frame_feats(im)
        guess = H
        if prev is not None:   # constant-velocity extrapolation in homography space
            guess = H @ np.linalg.inv(prev) @ H
            guess /= guess[2, 2]
        Hn, n = refine(im, ff, guess)
        if Hn is None or n < 25:
            Hn2, n2 = refine(im, ff, H)   # retry from previous without extrapolation
            if Hn2 is not None and n2 > n: Hn, n = Hn2, n2
        if Hn is None:
            print(i, "FAIL", flush=True); out[i] = (H.tolist(), 0); continue
        prev, H = H, Hn
        out[i] = (H.tolist(), n)
        print(i, n, flush=True)
    return out
def _main():
    a, b, anchor = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    out = {}
    Ha = np.load(f"{S}/track/anchor_{anchor}.npy")
    if len(sys.argv) > 5 and sys.argv[5] == "v2": run2(a, b, Ha, out)
    else: run(a, b, Ha, out)
    json.dump(out, open(f"{S}/track/trk_{a}_{b}.json", "w"))

_PF = None
def plate_feats():
    global _PF
    if _PF is None:
        g = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
        sift = cv2.SIFT_create(nfeatures=40000, contrastThreshold=0.008)
        kp, des = sift.detectAndCompute(g, cv2.erode(pvalid, np.ones((9, 9), np.uint8)))
        _PF = (np.float32([k.pt for k in kp]), des)
    return _PF
def global_match(ff):
    pp, pd = plate_feats()
    mm = bf.knnMatch(ff[1], pd, k=2)
    good = [x[0] for x in mm if len(x) == 2 and x[0].distance < 0.8 * x[1].distance]
    if len(good) < 12: return None, 0
    A = np.float32([pp[g.trainIdx] for g in good]); B = np.float32([ff[0][g.queryIdx] for g in good])
    Hc, inl = cv2.findHomography(A, B, cv2.USAC_MAGSAC, 4.0, maxIters=20000, confidence=0.9999)
    if Hc is None: return None, 0
    return Hc @ np.linalg.inv(Wc2W), int(inl.sum())
def run2(start, end, Hstart, out, minin=60):
    step = 1 if end >= start else -1
    H = Hstart.copy(); prev = None
    for i in range(start, end + step, step):
        im = load(S, i); ff = frame_feats(im)
        cands = []
        g1 = H if prev is None else (H @ np.linalg.inv(prev) @ H)
        for guess in ([g1, H] if prev is not None else [H]):
            Hn, n = refine(im, ff, guess / guess[2, 2])
            if Hn is not None: cands.append((n, Hn, "trk"))
        if not cands or max(c[0] for c in cands) < minin:
            Hg, ng = global_match(ff)
            if Hg is not None:
                Hn, n = refine(im, ff, Hg / Hg[2, 2])
                if Hn is not None: cands.append((n, Hn, "glob"))
        if not cands:
            print(i, "FAIL", flush=True); out[i] = (H.tolist(), 0); prev = None; continue
        n, Hn, how = max(cands, key=lambda c: c[0])
        # detect jump cut: if global was chosen, reset velocity
        prev = None if how == "glob" else H
        H = Hn
        out[i] = (H.tolist(), n)
        print(i, n, how, flush=True)
    return out
if __name__ == "__main__":
    _main()
