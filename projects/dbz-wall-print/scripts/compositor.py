"""Replace the balloon print with the DBZ mural, floor to ceiling, keeping the printer in front."""
import sys, os, numpy as np, cv2
S = sys.argv[1]
FW, FH = 720, 1280
N = 896
XL, XR, YT, YB = -300.0, 966.0, 200.0, 1123.0
H = np.load(f"{S}/track/H_all.npy")
src = np.load(f"{S}/comp/src.npy"); Fref = np.load(f"{S}/comp/Fref.npy"); Fdbz = np.load(f"{S}/comp/Fdbz.npy")
ALB = np.load(f"{S}/comp/albedo_W.npy").astype(np.float32)          # balloon albedo, canvas px -> W via T
TA = np.load(f"{S}/comp/albedo_T.npy")
MUR = cv2.imread(f"{S}/art/mural_albedo.png").astype(np.float32) / 255
PLATES = {}
for _n in ("open", "close", "wide", "final"):
    try:
        PLATES[_n] = (np.load(f"{S}/comp/plate_{_n}.npy").astype(np.float32), np.load(f"{S}/comp/plate_{_n}_T.npy"),
                      np.load(f"{S}/comp/plate_{_n}_have.npy").astype(np.float32))
    except FileNotFoundError:
        pass
def plate_for(t):
    if t <= 130: return "open"
    if 131 <= t <= 451: return "close"
    if 452 <= t <= 646: return "wide"
    return "final"
MH, MW = MUR.shape[:2]
MS = MH / (YB - YT)                    # mural px per W unit
MC = float(os.environ.get("MURAL_CENTER", "0.46")) * MW
UC = 503.0                             # W x mapped to MURAL_CENTER
def W2M():
    # W (u,v) -> mural px
    return np.array([[MS, 0, MC - UC * MS], [0, MS, -YT * MS], [0, 0, 1.0]])
yy, xx = np.mgrid[0:FH, 0:FW].astype(np.float32)
PIX = np.stack([xx.ravel(), yy.ravel(), np.ones(FH * FW, np.float32)], 0)
def frame_to_W(Hw2f):
    q = np.linalg.inv(Hw2f) @ PIX
    return (q[0] / q[2]).reshape(FH, FW).astype(np.float32), (q[1] / q[2]).reshape(FH, FW).astype(np.float32)
def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def gblur(a, s):
    if s >= 12:   # large blurs at reduced resolution (same result, much faster)
        f = int(s // 6)
        h, w = a.shape[:2]
        sm = cv2.resize(a, (w // f, h // f), interpolation=cv2.INTER_AREA)
        sm = cv2.GaussianBlur(sm, (0, 0), s / f)
        return cv2.resize(sm, (w, h), interpolation=cv2.INTER_LINEAR)
    return cv2.GaussianBlur(a, (0, 0), s)
def lum(a):
    return a[..., 0] * 0.114 + a[..., 1] * 0.587 + a[..., 2] * 0.299
def interp_H(Ha, Hb, t):
    """interpolate homographies by moving 4 W points"""
    P = np.array([[0, 200, 1], [900, 200, 1], [900, 1100, 1], [0, 1100, 1]], float).T
    pa = Ha @ P; pa = pa[:2] / pa[2]; pb = Hb @ P; pb = pb[:2] / pb[2]
    p = (1 - t) * pa + t * pb
    M = cv2.getPerspectiveTransform(P[:2].T.astype(np.float32), p.T.astype(np.float32))
    return M
def seg_ok(a, b):
    """True if frames a,b belong to the same continuous camera move (no jump cut)"""
    if a < 0 or b >= N: return False
    P = np.array([[300, 600, 1], [700, 900, 1]], float).T
    pa = H[a] @ P; pa = pa[:2] / pa[2]; pb = H[b] @ P; pb = pb[:2] / pb[2]
    d = np.abs(pa - pb).max()
    return d < 120 and src[a] == a and src[b] == b
def mural_samples(t):
    """list of W->frame homographies covering the shutter interval (motion blur)"""
    Hc = H[src[t]]
    if src[t] != t: return [Hc]
    Hs = []
    prv = H[t - 1] if seg_ok(t - 1, t) else None
    nxt = H[t + 1] if seg_ok(t, t + 1) else None
    P = np.array([[200, 400, 1], [700, 400, 1], [200, 1000, 1], [700, 1000, 1]], float).T
    def disp(Ha):
        if Ha is None: return 0.0
        a = Hc @ P; a = a[:2] / a[2]; b = Ha @ P; b = b[:2] / b[2]
        return float(np.abs(a - b).max())
    blur = 0.5 * max(disp(prv), disp(nxt))         # 180-degree shutter
    n = int(min(9, max(1, np.ceil(blur / 1.2))))
    if n == 1: return [Hc]
    for k in range(n):
        s = -0.25 + 0.5 * (k + 0.5) / n
        if s < 0:
            Hs.append(interp_H(Hc, prv, -s) if prv is not None else Hc)
        else:
            Hs.append(interp_H(Hc, nxt, s) if nxt is not None else Hc)
    return Hs
# ---- the transition into the final shot is a rotating-panel wipe: black bars sweep across the frame and each
#      strip between bars shows either the wide take (A, tripod) or the final take (B). Per frame and strip the
#      take was measured by scripts/wipe_strips.py; ambiguous strips keep the previous frame's take.
WIPE = (632, 674)
def H_take(t, take):
    if take == "A":                     # wide take: tripod, use its last clean pose
        return H[640]
    return H[max(t, 648)]               # final take (static before 648, tracked from 648)
WIPE_COLS = {}; WIPE_POOR = {}
try:
    import json as _json
    _ws = _json.load(open(f"{S}/comp/wipe_strips.json"))
    _prev = None
    for _t in range(WIPE[0], WIPE[1] + 1):
        _d = _ws[str(_t)]
        _base = _prev.copy() if _prev is not None else np.zeros(FW, np.uint8)
        _cols = _base.copy()
        for s0, s1, n, eA, eB in _d["strips"]:
            if s1 < s0: continue
            if eA is not None and n >= 3000 and abs(eA - eB) >= 2.5:
                tk = 1 if eB < eA else 0
            else:
                tk = _base[min(max((s0 + s1) // 2, 0), FW - 1)]
            _cols[s0:s1 + 1] = tk
        for b0, b1 in _d["bars"]:
            _cols[b0:b1 + 1] = _cols[b0 - 1] if b0 > 0 else _cols[min(b1 + 1, FW - 1)]
        _poor = np.zeros(FW, bool)
        for s0, s1, n, eA, eB in _d["strips"]:
            if s1 < s0 or s0 <= 0 or s1 >= FW - 1 or s1 - s0 >= 200: continue
            e = (eA if _cols[(s0 + s1) // 2] == 0 else eB) if eA is not None else None
            if e is None or n < 3000 or e > 15: _poor[s0:s1 + 1] = True
        WIPE_COLS[_t] = _cols; WIPE_POOR[_t] = _poor; _prev = _cols
except FileNotFoundError:
    pass
def render(t, debug=False, take=None, own=None, poor=None):
    i = int(src[t])
    obs = cv2.imread(f"{S}/ref_full/{i+1:04d}.png").astype(np.float32) / 255
    if take is None:
        Hw2f = H[i]; hs = mural_samples(t); pn = plate_for(t); fr = Fref[t]; fd = Fdbz[t]
    else:
        Hw2f = H_take(t, take); hs = [Hw2f]
        pn = "wide" if take == "A" else "final"
        fr = Fref[646] if take == "A" else Fref[700]
        fd = Fdbz[646] if take == "A" else Fdbz[700]
    u, v = frame_to_W(Hw2f)
    # ---- expected reference albedo (balloon print where printed, white wall elsewhere),
    #      motion-blurred over the same shutter samples as the footage
    A_bal = 0; pr = 0; A_exp = 0; wallrows = 0; rev_s = 0
    for Hk in hs:
        uk, vk = frame_to_W(Hk) if len(hs) > 1 else (u, v)
        ax = (uk - np.float32(TA[0, 2])).astype(np.float32); ay = (vk - np.float32(TA[1, 2])).astype(np.float32)
        Ab = cv2.remap(ALB, ax, ay, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(1, 1, 1))
        if pn in PLATES:
            Ap, Tp, hv = PLATES[pn]
            px = ((uk - np.float32(Tp[0, 2])) / np.float32(Tp[0, 0])).astype(np.float32)
            py = ((vk - np.float32(Tp[1, 2])) / np.float32(Tp[1, 1])).astype(np.float32)
            Apl = cv2.remap(Ap, px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(1, 1, 1))
            h = cv2.remap(hv, px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)[..., None]
            Ab = h * Apl + (1 - h) * Ab
        prk = smoothstep(fr + 1.5, fr - 1.5, uk)[..., None]          # 1 where printed in reference
        wrk = smoothstep(YT - 3, YT + 1, vk) * smoothstep(YB + 3, YB - 1, vk)
        A_bal = A_bal + Ab / len(hs); pr = pr + prk / len(hs)
        A_exp = A_exp + (prk * Ab + (1 - prk)) / len(hs)
        wallrows = wallrows + wrk / len(hs)
        rev_s = rev_s + smoothstep(fd + 1.5, fd - 1.5, uk) * smoothstep(XL - 1, XL + 1, uk) * wrk / len(hs)
    # ---- foreground matte (printer, cables, rails)
    Yo = lum(obs)
    m0 = (Yo > 0.25).astype(np.float32)
    if own is not None: m0 = m0 * own
    I0 = gblur(obs * m0[..., None], 9) / np.maximum(gblur(A_exp * m0[..., None], 9), 1e-3)
    Ye = lum(A_exp * I0)
    r = Yo / np.maximum(Ye, 1e-3)
    seeds = (r < 0.33)
    cand = (r < 0.58).astype(np.uint8)
    nlab, lab = cv2.connectedComponents(cand, connectivity=8)
    keep = np.zeros(nlab, bool); keep[np.unique(lab[seeds])] = True; keep[0] = False
    fgm = keep[lab]
    fgm = cv2.morphologyEx(fgm.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) > 0
    # drop small/thin isolated specks (dark print details such as balloon baskets and ropes)
    core = cv2.morphologyEx(fgm.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(core, connectivity=8)
    big = np.zeros(n2, bool); big[1:] = st2[1:, cv2.CC_STAT_AREA] >= 250
    bigm = big[lab2]
    reach = cv2.dilate(bigm.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    n3, lab3 = cv2.connectedComponents(fgm.astype(np.uint8), connectivity=8)
    keep3 = np.zeros(n3, bool); keep3[np.unique(lab3[reach & fgm])] = True; keep3[0] = False
    fgm = keep3[lab3]
    soft = smoothstep(0.62, 0.38, r)
    near = cv2.dilate(fgm.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    afg = np.where(fgm, np.maximum(soft, 0.85), np.where(near, soft, 0.0))
    # violet UV lamp itself stays in front
    hsv = cv2.cvtColor((np.clip(obs, 0, 1) * 255).astype(np.uint8), cv2.COLOR_BGR2HSV)
    lamp = (hsv[..., 0] > 115) & (hsv[..., 0] < 160) & (hsv[..., 1] > 110) & (hsv[..., 2] > 150)
    near_l = cv2.dilate(lamp.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    lamp = lamp | (near_l & (hsv[..., 2] > 200))
    lamp = cv2.dilate(lamp.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    afg = np.maximum(afg, lamp.astype(np.float32))
    PC = None
    if poor is not None and poor.any():
        # closing panels of the wipe show the old take blurred/turned: only truly dark pixels (the bars) stay in front
        PC = np.repeat(poor[None, :], FH, 0)
        afg = np.where(PC, np.maximum(smoothstep(0.16, 0.08, Yo), lamp.astype(np.float32)), afg)
    afg = gblur(afg.astype(np.float32), 0.6)
    # ---- illumination on the wall (shadows, glow, light falloff)
    m = (1 - afg)
    m = m * (m > 0.5)
    if own is not None: m = m * own
    # local scale (frame px per W unit) to size the shading blur
    c0 = np.linalg.inv(Hw2f) @ np.array([360.0, 640.0, 1.0]); c0 = c0[:2] / c0[2]
    pp = Hw2f @ np.array([[c0[0], c0[0] + 1], [c0[1], c0[1]], [1, 1]]); pp = pp[:2] / pp[2]
    sc = float(np.hypot(*(pp[:, 1] - pp[:, 0])))
    s1 = float(np.clip(2.6 * sc, 4.5, 10.0))
    Ye_ = lum(A_exp)
    I_l = gblur(Yo * m, s1) / np.maximum(gblur(Ye_ * m, s1), 1e-3)
    C = gblur(obs * m[..., None], 40) / np.maximum(gblur(A_exp * m[..., None], 40), 1e-3)
    C = C / np.maximum(lum(C), 1e-3)[..., None]
    I = np.clip(I_l[..., None] * C, 0, 1.6)
    # UV lamp glow on the freshly printed area
    lampf = lamp.astype(np.float32)
    if lampf.sum() > 3:
        lc = obs[lamp].mean(0); lc = lc / max(float(lc.max()), 1e-3)
        glow = gblur(lampf, 9) * 0.55 + gblur(lampf, 22) * 0.35
        glow = np.clip(glow * 6.0, 0, 1)[..., None] * lc[None, None, :] * 0.30
    else:
        glow = 0.0
    # ---- partially printed swath just right of the reference front (reference only): find it, paint it back to wall
    band = (u > fr + 1) & (u < fr + 70) & (wallrows > 0.5) & (afg < 0.3)
    Pb = np.zeros((FH, FW), np.float32)
    if band.sum() > 200:
        def lab_ab(img):
            return cv2.cvtColor(np.clip(img, 0, 1).astype(np.float32), cv2.COLOR_BGR2LAB)[..., 1:]
        ab_o = lab_ab(gblur(obs, 1.0)); ab_p = lab_ab(gblur(A_bal * I, 1.0)); ab_w = lab_ab(I)
        d_op = np.linalg.norm(ab_o - ab_p, axis=2); d_ow = np.linalg.norm(ab_o - ab_w, axis=2)
        d_pw = np.linalg.norm(ab_p - ab_w, axis=2)
        pb = band & (d_pw > 6) & (d_op < 0.6 * d_ow)
        pb = cv2.morphologyEx(pb.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        pb = cv2.morphologyEx(pb, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        pb = cv2.dilate(pb, np.ones((5, 5), np.uint8)) & (band | (cv2.dilate(band.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)).astype(np.uint8)
        Pb = gblur(pb.astype(np.float32), 1.2)
        if Pb.max() > 0.01:
            A_exp = A_exp * (1 - Pb[..., None]) + A_bal * Pb[..., None]
            I_l = gblur(Yo * m, s1) / np.maximum(gblur(lum(A_exp) * m, s1), 1e-3)
            I = np.clip(I_l[..., None] * C, 0, 1.6)
    if PC is not None:
        # ... and get broad, content-independent lighting: heavily smoothed luminance ratio, global colour cast
        pm = PC.astype(np.float32) * m
        I_lp = gblur(Yo * pm, 25) / np.maximum(gblur(lum(A_exp) * pm, 25), 1e-3)
        good = m * (~PC)
        if good.sum() > 5000:
            cg = np.array([float((obs[..., c] * good).sum() / max((A_exp[..., c] * good).sum(), 1e-3)) for c in range(3)], np.float32)
        else:
            cg = np.ones(3, np.float32)
        cg = cg / max(float(cg[0] * 0.114 + cg[1] * 0.587 + cg[2] * 0.299), 1e-3)
        I = np.where(PC[..., None], np.clip(I_lp[..., None] * cg[None, None, :], 0, 1.6), I)
    # ---- DBZ mural albedo in frame (motion-blurred)
    Ms = W2M()
    acc = np.zeros_like(obs)
    for Hk in hs:
        Mk = Ms @ np.linalg.inv(Hk)          # frame -> mural
        q = Mk @ PIX
        mx = (q[0] / q[2]).reshape(FH, FW).astype(np.float32); my = (q[1] / q[2]).reshape(FH, FW).astype(np.float32)
        acc += cv2.remap(MUR, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    A_dbz = acc / len(hs)
    A_dbz = gblur(A_dbz, 0.45)
    # ---- reveal (printed part of the DBZ mural)
    rev = rev_s
    comp = A_dbz * I + glow * (0.4 + 0.6 * A_dbz)
    # grain matched to the wall
    hp = lum(obs) - gblur(lum(obs), 1.0)
    wallmask = (rev < 0.01) & (wallrows > 0.99) & (afg < 0.01) & (pr[..., 0] < 0.01)
    sig = float(1.4826 * np.median(np.abs(hp[wallmask]))) if wallmask.sum() > 2000 else 0.004
    sig = float(np.clip(sig, 0.002, 0.007))
    rng = np.random.default_rng(t)
    g = rng.normal(0, 1, (FH, FW)).astype(np.float32)
    g = gblur(g, 0.6); g *= sig / max(float(g.std()), 1e-6)
    comp = comp + g[..., None] * (0.6 + 0.4 * comp)
    a = (rev * (1 - afg))[..., None]
    # reference print beyond our print front -> repaint as bare wall
    aw = (np.maximum(pr[..., 0] * wallrows, Pb) * (1 - rev) * (1 - afg))[..., None]
    wallc = I + g[..., None] * 0.9
    out = obs * (1 - a - aw) + comp * a + wallc * aw
    out8 = (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
    if debug:
        return out8, dict(afg=afg, rev=rev, I=I, A_exp=A_exp, r=r, sig=sig, nsamp=len(hs))
    return out8
def render_frame(t, debug=False):
    if t in WIPE_COLS:
        cols = WIPE_COLS[t]
        res = {}
        for tk, name in ((0, "A"), (1, "B")):
            ownc = (cols == tk)
            if not ownc.any(): continue
            own = np.repeat(ownc[None, :], FH, 0).astype(np.float32)
            res[tk] = render(t, debug, name, own, WIPE_POOR[t] & ownc)
        imgs = {k: (v[0] if debug else v) for k, v in res.items()}
        out = next(iter(imgs.values())) if len(imgs) == 1 else np.where((cols == 1)[None, :, None], imgs[1], imgs[0])
        return (out, list(res.values())[-1][1]) if debug else out
    return render(t, debug)
if __name__ == "__main__":
    outdir = sys.argv[2]; os.makedirs(outdir, exist_ok=True)
    frames = [int(x) for x in sys.argv[3].split(",") if x.strip()] if "," in sys.argv[3] or "-" not in sys.argv[3] else list(range(int(sys.argv[3].split("-")[0]), int(sys.argv[3].split("-")[1]) + 1))
    dbg = len(sys.argv) > 4 and sys.argv[4] == "dbg"
    for t in frames:
        if dbg:
            o, d = render_frame(t, True)
            cv2.imwrite(f"{outdir}/{t:04d}.png", o)
            cv2.imwrite(f"{outdir}/{t:04d}_afg.png", (d["afg"] * 255).astype(np.uint8))
            cv2.imwrite(f"{outdir}/{t:04d}_I.png", (np.clip(d["I"], 0, 1) * 255).astype(np.uint8))
            print(t, "grain sigma", round(d["sig"], 4), "samples", d["nsamp"], flush=True)
        else:
            cv2.imwrite(f"{outdir}/{t:04d}.png", render_frame(t))
            print(t, flush=True)
