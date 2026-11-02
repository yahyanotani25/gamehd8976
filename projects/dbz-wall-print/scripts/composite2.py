"""Reference 1, frame for frame, with the Dragon Ball mural instead of the
balloons.

The whole mural sits where the balloon print was, as large as it can be while
the widest shot still shows all of it (u 10..1600 on the canvas).  Its
height follows from the image's own proportions, so nothing is stretched.
It is printed exactly as the balloons were in each frame (progress.py).  The
old print is wiped off the wall, the room light and shadows are re-applied,
and the printer, cables, screen, UV light and passers-by stay in front.

usage: python composite2.py <first> <last>      (frames of reference 1)
"""
import sys
import numpy as np
import cv2
from common import *
from track import load_tr, wall_mask
from composite import (srgb_to_lin, lin_to_srgb, foreground, shading,
                       master_art_mask, uv_mask)

cv2.setNumThreads(2)

# mural placement on the canvas
U0, U1 = 10.0, 1600.0
S_CORR = 1.072
ART_W, ART_H = 3565, 1652
KU = (U1 - U0) / ART_W                  # canvas px per art px, horizontal
KV = KU * S_CORR                        # vertical (canvas u is 7.2% compressed)
V_MID = 990.0                           # centre of the old balloon print
V0 = V_MID - ART_H * KV / 2
V1 = V0 + ART_H * KV

WALKBY = set(range(21, 27)) | set(range(30, 36)) | set(range(604, 627))


def art_to_canvas():
    return np.array([[KU, 0, U0 + CU], [0, KV, V0 + CV], [0, 0, 1.0]])


class Mural:
    def __init__(self):
        a = cv2.imread(os.path.join(WORK, "art.png")).astype(np.float32) / 255
        self.levels = [srgb_to_lin(a)]
        for _ in range(5):
            self.levels.append(cv2.pyrDown(self.levels[-1]))

    def warp(self, Ha2f):
        Hi = np.linalg.inv(Ha2f)
        best = None
        # pick the pyramid level from the minification at the mural's centre
        c = Ha2f @ np.array([ART_W / 2, ART_H / 2, 1.0])
        c = c[:2] / c[2]
        p = Hi @ np.array([c[0], c[1], 1.0])
        J = (Hi[:2, :2] * p[2] - np.outer(p[:2], Hi[2, :2])) / p[2] ** 2
        scale = np.sqrt(abs(np.linalg.det(J)))          # art px per frame px
        lvl = 0
        while lvl + 1 < len(self.levels) and scale / (2 ** lvl) > 1.6:
            lvl += 1
        S = np.diag([2.0 ** lvl, 2.0 ** lvl, 1.0])
        img = self.levels[lvl]
        w = cv2.warpPerspective(img, Ha2f @ S, (FW, FH), flags=cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_CONSTANT, borderValue=(1, 1, 1))
        cov = cv2.warpPerspective(np.ones(img.shape[:2], np.float32), Ha2f @ S, (FW, FH),
                                  flags=cv2.INTER_LINEAR, borderValue=0)
        return np.clip(w, 0, 1), cov


def people_mask(i, tr, fr):
    """Passers-by: what is in this frame but in none of the nearest frames
    without people (before and after), warped into this view.  Taking the
    smallest difference keeps the time-lapse print progress and the moving
    printer out of the mask."""
    before = [j for j in range(i - 1, i - 12, -1) if j in tr and j not in WALKBY][:2]
    after = [j for j in range(i + 1, i + 12) if j in tr and j not in WALKBY][:2]
    if not before and not after:
        return np.zeros((FH, FW), np.uint8)
    d = None
    for j in before + after:
        G = tr[i] @ np.linalg.inv(tr[j])
        w = cv2.warpPerspective(read_frame(j), G, (FW, FH)).astype(np.int16)
        dj = np.abs(fr.astype(np.int16) - w).max(2)
        d = dj if d is None else np.minimum(d, dj)
    m = (d > 35).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    keep = np.zeros(n, np.uint8)
    keep[1:] = (st[1:, cv2.CC_STAT_HEIGHT] > 250) & (st[1:, cv2.CC_STAT_AREA] > 6000)
    m = keep[lab]
    # fill small holes inside the person (a bald head against white wall)
    inv = (1 - m).astype(np.uint8)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    small = np.zeros(n2, np.uint8)
    small[1:] = st2[1:, cv2.CC_STAT_AREA] < 4000
    m = np.maximum(m, small[lab2])
    return cv2.dilate(m, np.ones((5, 5), np.uint8))


def shading2(fr_lin, fr_bgr, fg_hard, wallm, exclude, extra_val, extra_w):
    """Like composite.shading, plus light measured through the old print.

    extra_val/extra_w: frame / (old print's albedo) and its confidence, so
    the light is known under the balloons too, not only on bare wall.
    """
    s = 0.5
    sz = (FW // 2, FH // 2)
    small = cv2.resize(fr_lin, sz, interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(cv2.resize(fr_bgr, sz, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2HSV)
    g = cv2.cvtColor(cv2.resize(fr_bgr, sz, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32)
    grad = np.sqrt(cv2.Sobel(g, cv2.CV_32F, 1, 0) ** 2 + cv2.Sobel(g, cv2.CV_32F, 0, 1) ** 2)
    fgs = cv2.resize(cv2.dilate(fg_hard, np.ones((9, 9), np.uint8)), sz, interpolation=cv2.INTER_NEAREST)
    ws = cv2.resize(wallm, sz, interpolation=cv2.INTER_NEAREST)
    ex = cv2.resize(exclude, sz, interpolation=cv2.INTER_NEAREST)
    hue, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    wallish = (sat < 22) | ((hue >= 6) & (hue <= 28) & (sat < 70))
    m = (wallish & (val > 70) & (grad < 40) & (fgs == 0) & (ws > 0) & (ex == 0)).astype(np.float32)
    m = cv2.erode(m, np.ones((3, 3), np.uint8))
    ev = cv2.resize(extra_val, sz, interpolation=cv2.INTER_AREA)
    ew = cv2.resize(extra_w, sz, interpolation=cv2.INTER_AREA) * (fgs == 0) * (ws > 0)
    # tint check of bare samples against the combined coarse estimate
    num = np.stack([cv2.GaussianBlur(small[..., c] * m + ev[..., c] * ew, (0, 0), 40) for c in range(3)], 2)
    den = cv2.GaussianBlur(m + ew, (0, 0), 40)[..., None] + 1e-6
    coarse = num / den
    chr_s = small / np.maximum(small.sum(2, keepdims=True), 1e-4)
    chr_c = coarse / np.maximum(coarse.sum(2, keepdims=True), 1e-4)
    m = m * (np.abs(chr_s - chr_c).max(2) < 0.03)
    S = None
    for sig in (90, 30, 10, 4):
        we = ew if sig >= 30 else ew * 0.0      # through-print light: broad level only
        den = cv2.GaussianBlur(m + we, (0, 0), sig) + 1e-6
        est = np.stack([cv2.GaussianBlur(small[..., c] * m + ev[..., c] * we, (0, 0), sig)
                        for c in range(3)], 2) / den[..., None]
        if S is None:
            tot = m + ew
            med = (np.median(small[m > 0], axis=0) if m.sum() > 50 else
                   np.array([0.45, 0.45, 0.45], np.float32))
            far = np.clip(den / 0.02, 0, 1)[..., None]
            S = far * est + (1 - far) * med
        else:
            conf = np.clip(den / 0.25, 0, 1)[..., None]
            S = conf * est + (1 - conf) * S
    return cv2.resize(S, (FW, FH), interpolation=cv2.INTER_LINEAR), m


class Renderer:
    def __init__(self):
        self.tr = load_tr("tracks_all.json")
        self.prog = {int(k): v for k, v in load_json("progress.json").items()}
        master = cv2.imread(os.path.join(WORK, "master1_color.png"))
        mv = cv2.imread(os.path.join(WORK, "master1_valid.png"), 0)
        self.master_art = master_art_mask(master, mv)
        # albedo of the old print: master divided by its own bare-wall light
        h = 0.5
        ml = srgb_to_lin(cv2.resize(master, None, fx=h, fy=h, interpolation=cv2.INTER_AREA).astype(np.float32) / 255)
        bare = ((cv2.resize(self.master_art, (ml.shape[1], ml.shape[0]), interpolation=cv2.INTER_NEAREST) == 0)
                & (cv2.resize(mv, (ml.shape[1], ml.shape[0]), interpolation=cv2.INTER_NEAREST) > 0)).astype(np.float32)
        den = cv2.GaussianBlur(bare, (0, 0), 80) + 1e-6
        Sm = np.stack([cv2.GaussianBlur(ml[..., c] * bare, (0, 0), 80) for c in range(3)], 2) / den[..., None]
        far = np.clip(den / 0.02, 0, 1)[..., None]
        Sm = far * Sm + (1 - far) * np.median(ml[bare > 0], axis=0)
        self.alb = np.clip(ml / np.maximum(Sm, 1e-3), 0, 1.1).astype(np.float32)
        L = self.alb.mean(2)
        gl = np.sqrt(cv2.Sobel(L, cv2.CV_32F, 1, 0) ** 2 + cv2.Sobel(L, cv2.CV_32F, 0, 1) ** 2)
        okc = ((L > 0.3) & (gl < 0.25)).astype(np.float32)
        okc *= (cv2.resize(mv, (ml.shape[1], ml.shape[0]), interpolation=cv2.INTER_NEAREST) > 0)
        self.alb_ok = cv2.erode(okc, np.ones((5, 5), np.uint8))
        self.mural = Mural()
        self.A2C = art_to_canvas()

    def alpha_canvas(self, st):
        sc = 0.25
        cw, ch = int(CANVAS_W * sc), int(CANVAS_H * sc)
        u = (np.arange(cw) / sc) - CU
        F, gw, ga = st
        soft = 8.0
        a = np.clip((F - u) / soft + 0.5, 0, 1)
        if gw > 0:
            g = np.clip((F + gw - u) / soft + 0.5, 0, 1) * (1 - a)
            a = a + ga * g
        return np.repeat(a[None, :].astype(np.float32), ch, 0)

    def render(self, i, debug=False, H=None, fr=None, st=None):
        H = self.tr[i] if H is None else H
        fr = read_frame(i) if fr is None else fr
        st = self.prog[i] if st is None else st
        F, gw, ga = st
        fr_lin = srgb_to_lin(fr.astype(np.float32) / 255)
        wallm = wall_mask(H)
        wall_soft = cv2.GaussianBlur(wallm.astype(np.float32), (0, 0), 1.0)
        fg, fg_hard = foreground(fr)
        if i in WALKBY:
            pm = people_mask(i, self.tr, fr)
            fg_hard = np.maximum(fg_hard, pm)
            fg = np.maximum(fg, cv2.GaussianBlur(pm.astype(np.float32), (0, 0), 2.0))

        # light on the wall: sample bare wall only (not the old print)
        ex = self.master_art.copy()
        c0 = int(np.clip(F + gw + 60 + CU, 0, CANVAS_W))
        ex[:, c0:] = 0
        exw = cv2.warpPerspective(ex, H, (FW, FH), flags=cv2.INTER_NEAREST)
        # light seen through the old print: frame / (old print as printed now)
        H2 = H @ np.diag([2.0, 2.0, 1.0])
        Ab = cv2.warpPerspective(self.alb, H2, (FW, FH), flags=cv2.INTER_LINEAR, borderValue=(1, 1, 1))
        okb = cv2.warpPerspective(self.alb_ok, H2, (FW, FH), flags=cv2.INTER_NEAREST)
        a_old = cv2.warpPerspective(self.alpha_canvas(st), H @ np.diag([4.0, 4.0, 1.0]), (FW, FH),
                                    flags=cv2.INTER_LINEAR)
        A_old = 1 - a_old[..., None] * (1 - Ab)
        ratio = fr_lin / np.maximum(A_old, 0.2)
        ew = (okb * exw * (a_old > 0.97)).astype(np.float32)
        ew *= (uv_mask(fr) < 0.05)
        S, smask = shading2(fr_lin, fr, fg_hard, wallm, exw, ratio.astype(np.float32), ew)

        art, cover = self.mural.warp(H @ self.A2C)
        art = cv2.GaussianBlur(art, (0, 0), 0.5)
        Hs = H @ np.diag([4.0, 4.0, 1.0])
        alpha = cv2.warpPerspective(self.alpha_canvas(st), Hs, (FW, FH), flags=cv2.INTER_LINEAR) * cover
        alb = 1 - alpha[..., None] * (1 - art)

        shade = np.ones((FH, FW), np.float32)
        if gw > 0:
            # strong shadows (head, cables, tower) on the strip being printed
            L = srgb_to_lin(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255)
            env = cv2.GaussianBlur(cv2.dilate(L, np.ones((61, 61), np.uint8)), (0, 0), 20)
            r = np.clip(L / np.maximum(env, 1e-3), 0.4, 1)
            r = np.where(r < 0.8, r / 0.8, 1.0).astype(np.float32)
            r = cv2.GaussianBlur(r, (0, 0), 2.0)
            band = np.zeros((CANVAS_H // 4, CANVAS_W // 4), np.float32)
            u0 = int((F - 20 + CU) / 4)
            u1 = int((F + gw + 60 + CU) / 4)
            band[:, max(u0, 0):max(u1, 0)] = 1
            band = cv2.GaussianBlur(cv2.warpPerspective(band, Hs, (FW, FH)), (0, 0), 3)
            shade = 1 - band * (1 - r)
        new = S * shade[..., None] * alb

        # bare wall that stays bare in the original: keep the real pixels
        dev = np.abs(fr_lin / np.maximum(S, 1e-3) - 1).mean(2)
        bare = np.clip(1 - (dev - 0.05) / 0.10, 0, 1)
        bare = cv2.GaussianBlur(bare, (0, 0), 1.5)
        # ...but never where the old balloon print is: that gets wiped
        old_print = cv2.GaussianBlur(exw.astype(np.float32), (0, 0), 3.0)
        keep_orig = bare * (1 - alpha) * (1 - old_print)
        new = keep_orig[..., None] * fr_lin + (1 - keep_orig[..., None]) * new
        rng = np.random.default_rng(i)
        noise = rng.normal(0, 0.006, (FH, FW, 1)).astype(np.float32)
        new = np.clip(new + noise * np.sqrt(np.clip(new, 0, 1)), 0, 1)
        k = (wall_soft * (1 - fg))[..., None]
        out = k * new + (1 - k) * fr_lin
        out = (lin_to_srgb(out) * 255 + 0.5).astype(np.uint8)
        if debug:
            return out, dict(S=S, fg=fg, alpha=alpha, bare=bare, smask=smask)
        return out


if __name__ == "__main__":
    a, b = int(sys.argv[1]), int(sys.argv[2])
    R = Renderer()
    outdir = os.path.join(WORK, "render2")
    os.makedirs(outdir, exist_ok=True)
    for i in range(a, b + 1):
        if i not in R.tr or i not in R.prog:
            continue
        cv2.imwrite(os.path.join(outdir, f"{i:04d}.png"), R.render(i))
        print(i, flush=True)
