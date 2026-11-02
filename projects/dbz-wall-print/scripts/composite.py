"""Put the Dragon Ball mural on the wall of reference 1, printed by its printer.

For every frame of a segment:
  * the flat mural (art.png) is projected onto the wall with the tracked
    homography (canvas -> frame) and the mural's placement on the wall,
  * a print mask says which part of the wall is already printed; it follows
    the real print head (its UV light) found in the footage,
  * the room's light on the wall (shading) is measured from the bare wall in
    the same frame and multiplied onto the mural, so shadows and light fall
    on the new print like on the real wall,
  * the printer, its cables, screen and UV light stay in front.

usage: python composite.py <segment> [frame ...]     (see segments.py)
"""
import sys
import numpy as np
import cv2
from common import *
from track import load_tr, wall_mask
from segments import SEGMENTS, ART_V0, ART_V1, S_CORR, art_to_canvas

cv2.setNumThreads(2)

ART = None
ART_LEVELS = []


def srgb_to_lin(x):
    return np.power(np.clip(x, 0, 1), 2.2)


def lin_to_srgb(x):
    return np.power(np.clip(x, 0, 1), 1 / 2.2)


def load_art():
    global ART, ART_LEVELS
    if ART is None:
        a = cv2.imread(os.path.join(WORK, "art.png")).astype(np.float32) / 255
        ART = srgb_to_lin(a)
        ART_LEVELS = [ART]
        for _ in range(4):
            ART_LEVELS.append(cv2.pyrDown(ART_LEVELS[-1]))
    return ART


def warp_art(Ha2f):
    """Warp the mural into the frame, picking a pyramid level to avoid aliasing."""
    load_art()
    # art px per frame px at the frame centre (from the inverse Jacobian)
    Hi = np.linalg.inv(Ha2f)
    c = np.array([FW / 2, FH / 2, 1.0])
    p = Hi @ c
    J = (Hi[:2, :2] * p[2] - np.outer(p[:2], Hi[2, :2])) / p[2] ** 2
    scale = np.sqrt(abs(np.linalg.det(J)))
    lvl = int(np.clip(np.floor(np.log2(max(scale, 1e-6) / 1.15) + 1e-9), 0, len(ART_LEVELS) - 1)) if scale > 1.15 else 0
    S = np.diag([2.0 ** lvl, 2.0 ** lvl, 1.0])
    img = ART_LEVELS[lvl]
    w = cv2.warpPerspective(img, Ha2f @ S, (FW, FH), flags=cv2.INTER_CUBIC,
                            borderMode=cv2.BORDER_CONSTANT, borderValue=(1, 1, 1))
    cover = cv2.warpPerspective(np.ones(img.shape[:2], np.float32), Ha2f @ S, (FW, FH),
                                flags=cv2.INTER_LINEAR, borderValue=0)
    return np.clip(w, 0, 1), cover


def uv_mask(bgr):
    f = bgr.astype(np.int16)
    b, g, r = f[..., 0], f[..., 1], f[..., 2]
    strength = np.clip(((b - g) - 40) / 60.0, 0, 1) * (r > g).astype(np.float32) * (b > 110)
    return strength.astype(np.float32)


def foreground(fr, uv_hint=None):
    """Soft mask of printer, cables, screen, UV light (1 = keep original).

    Dark regions count as printer when they touch the frame edge (the tower,
    the rail), are big, or sit next to the UV light (the head).  Small dark
    islands -- baskets and stripes of the old balloon print -- do not.
    """
    hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV)
    dark = (hsv[..., 2] < 62).astype(np.uint8)
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    uv = uv_mask(fr)
    uvb = cv2.dilate((uv > 0.2).astype(np.uint8), np.ones((61, 61), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(dark, connectivity=8)
    x, y, w, h, area = st[:, 0], st[:, 1], st[:, 2], st[:, 3], st[:, 4]
    border = (x <= 1) | (y <= 1) | (x + w >= FW - 1) | (y + h >= FH - 1)
    near_uv = np.zeros(n, bool)
    if uvb.any():
        ids = np.unique(lab[uvb > 0])
        near_uv[ids] = True
    keep = ((area >= 1200) & border) | (area >= 9000) | ((area >= 300) & near_uv)
    keep[0] = False
    m = keep[lab].astype(np.uint8)
    # the print head: close its outline so its light-grey front plate and
    # the gaps between its parts count as head too
    hk = ((area >= 300) & near_uv)
    hk[0] = False
    if hk.any():
        head = hk[lab].astype(np.uint8)
        head = cv2.morphologyEx(head, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
        hinv = (1 - head).astype(np.uint8)
        nh, labh, sth, _ = cv2.connectedComponentsWithStats(hinv, connectivity=4)
        holes = np.zeros(nh, np.uint8)
        holes[1:] = sth[1:, cv2.CC_STAT_AREA] < 20000
        m = np.maximum(m, np.maximum(head, holes[labh]))
    # the touchscreen: bright cyan-blue UI
    f = fr.astype(np.int16)
    scr = ((f[..., 0] > 200) & (f[..., 0] - f[..., 2] > 95) & (f[..., 1] > f[..., 2] + 30)).astype(np.uint8)
    scr = cv2.morphologyEx(scr, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    ns, labs_, sts, _ = cv2.connectedComponentsWithStats(scr, connectivity=8)
    near_pr = np.zeros(ns, bool)
    ids = np.unique(labs_[cv2.dilate(m, np.ones((21, 21), np.uint8)) > 0])
    near_pr[ids] = True
    big = np.zeros(ns, np.uint8)
    big[1:] = (sts[1:, cv2.CC_STAT_AREA] >= 150) & near_pr[1:]
    m = np.maximum(m, cv2.dilate(big[labs_], np.ones((9, 9), np.uint8)))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    # fill small enclosed holes (screen inside its bezel, gaps in the head)
    inv = (1 - m).astype(np.uint8)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    small = np.zeros(n2, np.uint8)
    small[1:] = st2[1:, cv2.CC_STAT_AREA] < 2500
    m = np.maximum(m, small[lab2])
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    mf = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.0)
    uvs = cv2.GaussianBlur(cv2.dilate(uv, np.ones((5, 5), np.uint8)), (0, 0), 2.0)
    return np.clip(np.maximum(mf, uvs), 0, 1), m


def shading(fr_lin, fr_bgr, fg_hard, wallm, exclude=None):
    """Colour of bare white wall under this frame's light, per pixel."""
    s = 0.5
    small = cv2.resize(fr_lin, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(cv2.resize(fr_bgr, None, fx=s, fy=s, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2HSV)
    g = cv2.cvtColor(cv2.resize(fr_bgr, None, fx=s, fy=s, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    grad = np.sqrt(gx * gx + gy * gy)
    fgs = cv2.resize(cv2.dilate(fg_hard, np.ones((9, 9), np.uint8)), (small.shape[1], small.shape[0]),
                     interpolation=cv2.INTER_NEAREST)
    ws = cv2.resize(wallm, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_NEAREST)
    hue, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    # bare wall: neutral, or the warm tint the room lights give it; not the
    # blue sky / red / pink of the old print, no edges, not the printer
    wallish = (sat < 22) | ((hue >= 6) & (hue <= 28) & (sat < 70))
    m = (wallish & (val > 70) & (grad < 40) & (fgs == 0) & (ws > 0))
    if exclude is not None:
        ex = cv2.resize(exclude, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_NEAREST)
        m &= ex == 0
    m = m.astype(np.float32)
    m = cv2.erode(m, np.ones((3, 3), np.uint8))
    S = None
    for sig in (90, 30, 10, 3.5):
        den = cv2.GaussianBlur(m, (0, 0), sig) + 1e-6
        est = np.stack([cv2.GaussianBlur(small[..., c] * m, (0, 0), sig) for c in range(3)], 2) / den[..., None]
        if S is None:
            S = est
            # where there is no bare wall at all within reach, use the frame's median wall colour
            if m.sum() > 50:
                med = np.median(small[m > 0], axis=0)
            else:
                med = np.array([0.45, 0.45, 0.45], np.float32)
            far = np.clip(den / 0.02, 0, 1)[..., None]
            S = far * S + (1 - far) * med
        else:
            conf = np.clip(den / 0.25, 0, 1)[..., None]
            S = conf * est + (1 - conf) * S
    S = cv2.resize(S, (FW, FH), interpolation=cv2.INTER_LINEAR)
    return S, m


def master_art_mask(master, valid):
    """Canvas mask of the old balloon print (anything that is not bare wall)."""
    hsv = cv2.cvtColor(master, cv2.COLOR_BGR2HSV)
    g = cv2.cvtColor(master, cv2.COLOR_BGR2GRAY).astype(np.float32)
    white = cv2.dilate(cv2.GaussianBlur(g, (0, 0), 25), np.ones((61, 61), np.uint8))
    mu = cv2.blur(g, (15, 15))
    sd = np.sqrt(np.maximum(cv2.blur(g * g, (15, 15)) - mu * mu, 0))
    art = (hsv[..., 1] > 28) | (g < 0.86 * white) | (sd > 4.5)
    art = art & (valid > 0)
    art = cv2.morphologyEx(art.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    art = cv2.dilate(art, np.ones((21, 21), np.uint8))
    # the old print only ever covered the wall band
    art[:CV, :] = 0
    return art


class Renderer:
    def __init__(self, seg):
        self.seg = seg
        self.tr = load_tr(seg["tracks"])
        self.master = cv2.imread(os.path.join(WORK, "master1_color.png"))
        mv = cv2.imread(os.path.join(WORK, "master1_valid.png"), 0)
        self.master_art = master_art_mask(self.master, mv)
        # how far the OLD balloon print reached in this segment's footage:
        # up to the head column plus its strip (all of it if the head is idle)
        from segments import head_series, _heads
        a, b = seg["frames"]
        hs = [k for k in _heads() if a <= k <= b]
        if len(hs) >= 5:
            _, uu, _ = head_series(a, b, smooth=1)
            self.orig_front = float(np.median(uu)) + 150
        else:
            self.orig_front = 1e6
        load_art()

    def print_alpha(self, i, H):
        """Printed fraction of the wall, rasterised in the frame."""
        seg = self.seg
        sc = 0.25
        cw, ch = int(CANVAS_W * sc), int(CANVAS_H * sc)
        u = (np.arange(cw) / sc) - CU
        v = (np.arange(ch) / sc) - CV
        U, V = np.meshgrid(u, v)
        st = seg["state"](i)          # dict with frontier, strip, head_v, direction
        soft = 8.0
        a = np.clip((st["frontier"] - U) / soft + 0.5, 0, 1)
        if st.get("strip_w", 0) > 0:
            in_strip = np.clip((st["frontier"] + st["strip_w"] - U) / soft + 0.5, 0, 1) * (1 - a)
            if st["dir"] > 0:        # head moving down: printed above it
                rows = np.clip((st["head_v"] - V) / soft + 0.5, 0, 1)
            else:                    # head moving up: printed below it
                rows = np.clip((V - st["head_v"]) / soft + 0.5, 0, 1)
            a = a + in_strip * rows
        a = a.astype(np.float32)
        Hs = H @ np.diag([1 / sc, 1 / sc, 1.0])
        return cv2.warpPerspective(a, Hs, (FW, FH), flags=cv2.INTER_LINEAR, borderValue=0)

    def render(self, i, debug=False):
        seg = self.seg
        H = self.tr[i]
        fr = read_frame(i)
        fr_lin = srgb_to_lin(fr.astype(np.float32) / 255)
        wallm = wall_mask(H)
        wall_soft = cv2.GaussianBlur(wallm.astype(np.float32), (0, 0), 1.0)
        fg, fg_hard = foreground(fr)
        ex = self.master_art.copy()
        c0 = int(np.clip(self.orig_front + CU, 0, CANVAS_W))
        ex[:, c0:] = 0
        exw = cv2.warpPerspective(ex, H, (FW, FH), flags=cv2.INTER_NEAREST)
        S, smask = shading(fr_lin, fr, fg_hard, wallm, exclude=exw)

        A2C = art_to_canvas(seg["u_off"])
        art, cover = warp_art(H @ A2C)
        alpha = self.print_alpha(i, H) * cover
        if seg.get("blur", 0.6) > 0:
            art = cv2.GaussianBlur(art, (0, 0), seg.get("blur", 0.6))
        alb = 1 - alpha[..., None] * (1 - art)          # ink on white wall
        shade = np.ones((FH, FW), np.float32)
        st = seg["state"](i)
        if st.get("strip_w", 0) > 0:
            # strong shadows (head, cables, tower) falling on the strip, taken
            # from the footage as a luminance ratio to the local bright level
            L = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
            Ll = srgb_to_lin(L)
            env = cv2.GaussianBlur(cv2.dilate(Ll, np.ones((61, 61), np.uint8)), (0, 0), 20)
            r = np.clip(Ll / np.maximum(env, 1e-3), 0.4, 1)
            r = np.where(r < 0.8, r / 0.8, 1.0).astype(np.float32)   # only real shadows
            r = cv2.GaussianBlur(r, (0, 0), 2.0)
            band = np.zeros((CANVAS_H // 4, CANVAS_W // 4), np.float32)
            u0 = int((st["frontier"] - 20 + CU) / 4)
            u1 = int((st["frontier"] + st["strip_w"] + 60 + CU) / 4)
            band[:, max(u0, 0):max(u1, 0)] = 1
            band = cv2.warpPerspective(band, H @ np.diag([4.0, 4.0, 1.0]), (FW, FH))
            band = cv2.GaussianBlur(band, (0, 0), 3)
            shade = 1 - band * (1 - r)
        new = S * shade[..., None] * alb
        # bare wall in the original that stays unprinted: keep the real pixels
        dev = np.abs(fr_lin / np.maximum(S, 1e-3) - 1).mean(2)
        bare = np.clip(1 - (dev - 0.05) / 0.10, 0, 1)
        bare = cv2.GaussianBlur(bare, (0, 0), 1.5)
        keep_orig = bare * (1 - alpha)
        new = keep_orig[..., None] * fr_lin + (1 - keep_orig[..., None]) * new
        # grain so the print sits in the footage
        rng = np.random.default_rng(i)
        noise = rng.normal(0, seg.get("grain", 0.006), (FH, FW, 1)).astype(np.float32)
        new = np.clip(new + noise * np.sqrt(np.clip(new, 0, 1)), 0, 1)
        k = (wall_soft * (1 - fg))[..., None]
        out = k * new + (1 - k) * fr_lin
        out = (lin_to_srgb(out) * 255 + 0.5).astype(np.uint8)
        if debug:
            return out, dict(S=S, smask=smask, fg=fg, alpha=alpha, bare=bare)
        return out


if __name__ == "__main__":
    name = sys.argv[1]
    seg = SEGMENTS[name]
    R = Renderer(seg)
    frames = [int(x) for x in sys.argv[2:]] or list(range(seg["frames"][0], seg["frames"][1] + 1))
    outdir = os.path.join(WORK, "render", name)
    os.makedirs(outdir, exist_ok=True)
    for i in frames:
        cv2.imwrite(os.path.join(outdir, f"{i:04d}.png"), R.render(i))
        print(name, i, flush=True)
