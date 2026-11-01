"""Hidden bar wipe between the wide take (A) and the final take (B): per frame, the black bars and,
for each strip between bars, how well each take's wall pose explains it (gradient error, lower = better)."""
import sys, numpy as np, cv2, json
S = sys.argv[1]; a, b = int(sys.argv[2]), int(sys.argv[3])
H = np.load(f"{S}/track/H_all.npy"); Wc = np.load(f"{S}/track/Wc2W.npy")
plate = cv2.imread(f"{S}/track/plate2.png"); pvld = cv2.imread(f"{S}/track/plate2_valid.png", 0)
FW, FH = 720, 1280
def H_take(t, take): return H[640] if take == "A" else H[max(t, 648)]
def grad(g):
    g = cv2.GaussianBlur(g, (0, 0), 1.2)
    return np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
res = {}
for t in range(a, b + 1):
    g8 = cv2.imread(f"{S}/ref_full/{t+1:04d}.png", 0)
    colfrac = (g8[150:1150] < 30).mean(0)
    bars = []; x = 0
    while x < FW:
        if colfrac[x] > 0.85:
            x0 = x
            while x < FW and colfrac[x] > 0.85: x += 1
            if x - x0 >= 8: bars.append((x0, x - 1))
        x += 1
    gi = grad(g8.astype(np.float32)); dark = g8 < 60
    errs = []
    for take in ("A", "B"):
        Hx = H_take(t, take) @ Wc
        pv = cv2.warpPerspective(plate, Hx, (FW, FH)); m = cv2.warpPerspective(pvld, Hx, (FW, FH)) > 0
        gp = grad(cv2.cvtColor(pv, cv2.COLOR_BGR2GRAY).astype(np.float32))
        mm = m & ~dark; mm[:200] = False; mm[1100:] = False
        errs.append((np.abs(gi - gp) * mm, mm))
    edges = [-1] + [c for bar in bars for c in bar] + [FW]
    strips = []
    for k in range(len(bars) + 1):
        s0, s1 = edges[2 * k] + 1, edges[2 * k + 1] - 1
        x0, x1 = s0 + 3, s1 - 3
        if x1 - x0 < 6: strips.append([int(s0), int(s1), 0, None, None]); continue
        (dA, mA), (dB, mB) = errs
        n = int(min(mA[:, x0:x1].sum(), mB[:, x0:x1].sum()))
        eA = float(dA[:, x0:x1].sum() / max(mA[:, x0:x1].sum(), 1)); eB = float(dB[:, x0:x1].sum() / max(mB[:, x0:x1].sum(), 1))
        strips.append([int(s0), int(s1), n, round(eA, 1), round(eB, 1)])
    res[t] = dict(bars=[[int(p), int(q)] for p, q in bars], strips=strips)
    print(t, " | ".join(f"{s0}-{s1}:{'-' if eA is None else ('B' if eB < eA - 2 else ('A' if eA < eB - 2 else '?'))}({n//1000}k {eA}/{eB})" for s0, s1, n, eA, eB in strips), flush=True)
json.dump(res, open(f"{S}/comp/wipe_strips.json", "w"))
