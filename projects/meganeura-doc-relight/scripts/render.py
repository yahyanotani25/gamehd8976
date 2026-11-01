"""Render replacement slots to intermediates.

usage: render.py W [slot ids...]      (default: all groups)

Slots chained by "new" dissolves render together as one group, one intermediate
per group: W/work/slots/<first>-<last>.mkv covering [first.f0, last.f1].
Everything is RGB in BT.709; intermediates are x264 CRF 10 yuv420p (BT.709).
"""
import sys, os, json, math, subprocess, time
import numpy as np, cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from slots import SLOTS
from plan import PLAN, AI
import stills as DM

W = sys.argv[1]
ORIG = W + "/dl/original/original.mp4"
OUT = W + "/work/slots"
os.makedirs(OUT, exist_ok=True)
FW, FH, FPS = 1920, 1080, 25
THUMBS = np.load(W + "/work/orig_thumbs.npy").astype(np.float32)
STATS = np.load(W + "/work/orig_stats.npy")
OVL_META = json.load(open(W + "/work/ovl/meta.json"))

# ---------------------------------------------------------------- utilities

def probe(path):
    j = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                            "stream=width,height,r_frame_rate:format=duration", "-of", "json", path]))
    s = j["streams"][0]
    n, d = s["r_frame_rate"].split("/")
    return s["width"], s["height"], float(n) / float(d), float(j["format"]["duration"])


def src_path(key):
    if key.startswith("px"):
        return f"{W}/dl/pexels/{key}.mp4"
    raise KeyError(key)


def read_orig(f0, n):
    """n original frames from frame f0, RGB uint8 (BT.709)."""
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{f0 / FPS:.4f}", "-i", ORIG, "-frames:v", str(n),
           "-vf", "scale=in_color_matrix=bt709:in_range=tv,format=rgb24", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    F = np.frombuffer(raw, np.uint8).reshape(-1, FH, FW, 3)
    assert len(F) == n, (f0, n, len(F))
    return F


def read_video(key, t, n, crop=None):
    """n frames at 25 fps from a stock clip: every source frame is used once
    (conform), 50/60 fps sources drop every other frame first. Scaled to cover
    1920x1080 and centre-cropped."""
    path = src_path(key)
    w, h, fps, dur = probe(path)
    step = 2 if fps > 45 else 1
    eff = fps / step
    need = n / eff + 0.2
    if t + need > dur:
        t = max(0.0, dur - need)
    vf = []
    if step == 2:
        vf.append("select='not(mod(n\\,2))'")
    if crop:
        z, cx, cy = crop
        zw, zh = int(round(1920 * z / 2) * 2), int(round(1080 * z / 2) * 2)
        vf.append(f"scale={zw}:{zh}:force_original_aspect_ratio=increase:flags=lanczos:in_color_matrix=bt709:in_range=tv")
        vf.append(f"crop=1920:1080:'min(max(iw*{cx}-960,0),iw-1920)':'min(max(ih*{cy}-540,0),ih-1080)'")
    else:
        vf.append("scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos:in_color_matrix=bt709:in_range=tv")
        vf.append("crop=1920:1080")
    vf.append("format=rgb24")
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-vsync", "passthrough", "-vf", ",".join(vf),
           "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    F = np.frombuffer(raw, np.uint8).reshape(-1, FH, FW, 3)
    if len(F) < n:  # pad by holding the last frame (should not happen)
        F = np.concatenate([F, np.repeat(F[-1:], n - len(F), 0)], 0)
    return F, dict(src=key, t=t, fps=fps, w=w, h=h)


_still_cache = {}


def load_still(name):
    if name in _still_cache:
        return _still_cache[name]
    im = np.asarray(Image.open(f"{W}/dl/{AI[name]}").convert("RGB"))
    up = DM.upscale(im, 2400, sharpen=0.55)
    _still_cache[name] = up
    return up


def still_frames(name, n, kb):
    img = load_still(name)
    ih, iw = img.shape[:2]
    z0, z1, cx0, cy0, cx1, cy1 = kb
    out = np.empty((n, FH, FW, 3), np.uint8)
    base = FW / iw  # zoom 1.0: image width fills the frame
    for i in range(n):
        u = i / max(1, n - 1)
        z = z0 + (z1 - z0) * u
        s = base * z
        vw, vh = FW / s, FH / s
        cx = (cx0 + (cx1 - cx0) * u) * iw
        cy = (cy0 + (cy1 - cy0) * u) * ih
        cx = min(max(cx, vw / 2), iw - vw / 2)
        cy = min(max(cy, vh / 2), ih - vh / 2)
        M = np.array([[s, 0, FW / 2 - s * cx], [0, s, FH / 2 - s * cy]], np.float32)
        out[i] = cv2.warpAffine(img, M, (FW, FH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    return out


# ---------------------------------------------------------------- grading

def luma(a):
    a = a.astype(np.float32)
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


VIG = None


def vignette():
    global VIG
    if VIG is None:
        yy, xx = np.mgrid[0:FH, 0:FW].astype(np.float32)
        r = np.sqrt(((xx - FW / 2) / (FW / 2)) ** 2 + ((yy - FH / 2) / (FH / 2)) ** 2) / math.sqrt(2)
        VIG = (1.0 - 0.16 * r ** 2.4).astype(np.float32)[..., None]
    return VIG


def grade(frames, target=100.0, sat=1.06, contrast=0.07, warm=0.015):
    """Shot-level exposure to a mean-luma target (gamma, so highlights never clip),
    gentle S-curve, a touch of saturation and warmth, soft vignette."""
    sample = frames[:: max(1, len(frames) // 12)]
    m = float(np.mean([luma(f[::4, ::4]).mean() for f in sample]))
    m = min(max(m, 8.0), 240.0)
    gamma = math.log(target / 255.0) / math.log(m / 255.0)
    gamma = min(max(gamma, 0.5), 1.35)
    x = np.arange(256, dtype=np.float32) / 255.0
    y = x ** gamma
    y = y - contrast / (2 * math.pi) * np.sin(2 * math.pi * y)
    lut = np.clip(y * 255.0 + 0.5, 0, 255).astype(np.uint8)
    V = vignette()
    out = np.empty_like(frames)
    for i, f in enumerate(frames):
        g = cv2.LUT(f, lut).astype(np.float32)
        Y = (g[..., 0] * 0.2126 + g[..., 1] * 0.7152 + g[..., 2] * 0.0722)[..., None]
        g = Y + sat * (g - Y)
        g[..., 0] *= 1 + warm
        g[..., 2] *= 1 - warm
        g *= V
        out[i] = np.clip(g, 0, 255).astype(np.uint8)
    return out, dict(mean_in=m, gamma=gamma)


# ---------------------------------------------------------------- text overlays

_ovl = {}


def ovl_data(oid):
    if oid not in _ovl:
        z = np.load(f"{W}/work/ovl/{oid}.npz")
        soft = z["soft"].astype(np.float32)
        box = tuple(int(v) for v in z["box"])
        if oid == "O1_not_modern":  # keep only the bracketed label
            x0, y0, x1, y1 = box
            keep = np.zeros_like(soft)
            keep[max(0, 905 - y0):975 - y0, max(0, 95 - x0):462 - x0] = 1
            soft *= keep
        color = z["color"].astype(np.float32)
        Yc = luma(color)
        shadow = cv2.GaussianBlur(cv2.dilate((soft > 0.2).astype(np.float32), np.ones((9, 9), np.uint8)), (0, 0), 11)
        shadow = np.clip(shadow * 1.6, 0, 1)
        _ovl[oid] = dict(soft=soft, box=box, color=color, Yc=Yc, k=int(z["k"]), shadow=shadow,
                         span=tuple(OVL_META[oid]["span"]))
    return _ovl[oid]


def text_alpha(orig_crop, d):
    Y = luma(orig_crop)
    ker = cv2.getStructuringElement(cv2.MORPH_RECT, (d["k"], d["k"]))
    B = cv2.blur(cv2.morphologyEx(Y, cv2.MORPH_OPEN, ker), (5, 5))
    lift = np.clip(Y - B, 0, None)
    denom = np.maximum(d["Yc"] - B, 25.0)
    return np.clip(lift / denom, 0, 1) * d["soft"]


# legibility shadow per overlay: (strength, dilate px, blur sigma). Thin labels that
# now sit on bright pictures get a darker, wider shadow than the bold titles.
SHADOW = {"O1_not_modern": (0.78, 13, 14), "O2_how_could": (0.6, 9, 12), "O3_hud": (0.74, 13, 14),
          "O4_uncertain": (0.62, 11, 13), "O6_plausible": (0.8, 13, 14), "O7_nosingle": (0.5, 9, 11)}


def composite_text(base, orig, oid, shadow_strength=0.5):
    """Put the original's text (frame-accurate alpha) on top of a new base frame."""
    d = ovl_data(oid)
    x0, y0, x1, y1 = d["box"]
    a = text_alpha(orig[y0:y1, x0:x1], d)
    out = base.copy()
    reg = out[y0:y1, x0:x1].astype(np.float32)
    if shadow_strength > 0 and a.max() > 0.02:
        # soft shadow that follows the text as it is on screen in this very frame
        # (typing and fades included), so nothing shows before a letter appears
        shadow_strength, dil, sig = SHADOW.get(oid, (shadow_strength, 9, 11))
        sh = cv2.GaussianBlur(cv2.dilate(a, np.ones((dil, dil), np.uint8)), (0, 0), sig)
        sh = np.clip(sh * 1.6, 0, 1)
        reg *= (1 - shadow_strength * sh)[..., None]
    reg = reg * (1 - a[..., None]) + d["color"] * a[..., None]
    out[y0:y1, x0:x1] = np.clip(reg, 0, 255).astype(np.uint8)
    return out


# ---------------------------------------------------------------- transitions

def beta_curve(a, b):
    """Measured dissolve weight of the incoming shot for frames a..b (inclusive)."""
    A = THUMBS[a - 3:a].mean(0)
    B = THUMBS[b + 1:b + 4].mean(0)
    D = (B - A).ravel()
    dd = float(D @ D) + 1e-6
    be = np.array([float((THUMBS[i] - A).ravel() @ D) / dd for i in range(a, b + 1)])
    be = np.clip(be, 0, 1)
    be = np.maximum.accumulate(be)
    # pin the ends and keep it smooth
    if len(be) > 2:
        be = np.convolve(np.concatenate([[be[0]], be, [be[-1]]]), [0.25, 0.5, 0.25], "valid")
    lo, hi = be[0], be[-1]
    if hi - lo > 0.2:
        be = (be - lo) / (hi - lo) * (1 - 2 / (len(be) + 1)) + 1 / (len(be) + 1)
    return np.clip(be, 0, 1)


# ---------------------------------------------------------------- slot bases

def slot_base(slot, orig):
    """New picture for every frame of the slot (no transitions)."""
    n = slot["f1"] - slot["f0"] + 1
    sid = slot["id"]
    info = []
    if slot["kind"] == "regrade":
        return regrade(slot, orig), [dict(regrade=True)]
    segs = PLAN[sid]
    # split frames across segments
    fr = [s.get("frac") for s in segs]
    counts, left = [], n
    for i, s in enumerate(segs):
        if i == len(segs) - 1:
            counts.append(left)
        else:
            c = int(round(n * (s.get("frac") or 1.0 / len(segs))))
            counts.append(c); left -= c
    xf = 12  # crossfade frames between segments inside one slot
    parts = []
    for i, (s, c) in enumerate(zip(segs, counts)):
        extra = xf if i < len(segs) - 1 else 0
        if s["src"].startswith("ai:"):
            F = still_frames(s["src"][3:], c + extra, s["kb"])
            meta = dict(src=s["src"])
        else:
            F, meta = read_video(s["src"], s.get("t", 0.0), c + extra, s.get("crop"))
        if s.get("hflip"):
            F = F[:, :, ::-1]
        F, g = grade(F, target=s.get("target", 100.0))
        meta.update(g)
        if s.get("title"):
            dim, blur = s["title"]["dim"], s["title"]["blur"]
            for k in range(len(F)):  # in place, one frame at a time (a float stack of a whole shot is ~5 GB)
                F[k] = np.clip(cv2.GaussianBlur(F[k].astype(np.float32) * dim, (0, 0), blur), 0, 255).astype(np.uint8)
            meta["title_dim"] = dim
        parts.append(F); info.append(meta)
    base = parts[0][:counts[0]]
    for i in range(1, len(parts)):
        prev_tail = parts[i - 1][counts[i - 1]:counts[i - 1] + xf].astype(np.float32)
        head = parts[i][:xf].astype(np.float32)
        w = (np.arange(xf, dtype=np.float32) + 1) / (xf + 1)
        mix = (prev_tail * (1 - w[:, None, None, None]) + head * w[:, None, None, None]).astype(np.uint8)
        # segment i-1 runs on for xf extra frames while segment i fades in over them
        base = np.concatenate([base, mix, parts[i][xf:counts[i]]], 0)
    assert len(base) == n, (sid, len(base), n)
    return base, info  # text is composited later, after the dissolves (see render_group)


def remove_text(frame, oid):
    """The frame with the overlay's strokes painted out (morphological opening), so
    dissolve maths can work on the plate alone."""
    d = ovl_data(oid)
    x0, y0, x1, y1 = d["box"]
    out = frame.copy()
    reg = out[y0:y1, x0:x1].astype(np.float32)
    ker = cv2.getStructuringElement(cv2.MORPH_RECT, (d["k"], d["k"]))
    op = np.stack([cv2.blur(cv2.morphologyEx(reg[..., c], cv2.MORPH_OPEN, ker), (5, 5)) for c in range(3)], -1)
    m = np.clip(cv2.GaussianBlur(cv2.dilate(d["soft"], np.ones((5, 5), np.uint8)), (0, 0), 2) * 1.5, 0, 1)[..., None]
    out[y0:y1, x0:x1] = np.clip(reg * (1 - m) + op * m, 0, 255).astype(np.uint8)
    return out


def overlays_at(g, f):
    """Overlay ids visible at original frame f among the group's (non-regrade) slots."""
    ids = []
    for s in g:
        if s.get("ovl") and s["kind"] != "regrade" and s["f0"] <= f <= s["f1"]:
            a, b = ovl_data(s["ovl"])["span"]
            if a <= f <= b and s["ovl"] not in ids:
                ids.append(s["ovl"])
    return ids


def regrade(slot, orig):
    """Chapter 3 card: the original Earth shot was dimmed to ~35% under the title.
    Lift the background (not the text) back up to a mean luma of ~50, keep the
    text's own contrast with a soft local shadow, re-apply the text crisply."""
    oid = slot["ovl"]
    d = ovl_data(oid)
    x0, y0, x1, y1 = d["box"]
    out = np.empty_like(orig)
    ker = cv2.getStructuringElement(cv2.MORPH_RECT, (31, 31))
    for i, f in enumerate(orig):
        Y = luma(f[::4, ::4]).mean()
        gain = min(max(max(Y, 50.0) / max(Y, 1.0), 1.0), 2.2)
        ff = f.astype(np.float32)
        B = np.stack([cv2.blur(cv2.morphologyEx(ff[..., c], cv2.MORPH_OPEN, ker), (9, 9)) for c in range(3)], -1)
        lift = (gain - 1.0) * B
        sh = np.zeros((FH, FW), np.float32)
        sh[y0:y1, x0:x1] = d["shadow"]
        lift *= (1 - 0.55 * sh)[..., None]
        g = np.clip(ff + lift, 0, 255).astype(np.uint8)
        out[i] = composite_text(g, f, oid, 0.0)
    return out


# ---------------------------------------------------------------- groups

def groups():
    gs, cur = [], []
    for s in SLOTS:
        if cur and s["inn"][0] == "new":
            cur.append(s)
        else:
            if cur:
                gs.append(cur)
            cur = [s]
    gs.append(cur)
    return gs


def render_group(g):
    t0 = time.time()
    F0, F1 = g[0]["f0"], g[-1]["f1"]
    n = F1 - F0 + 1
    orig = read_orig(F0, n)
    canvas = np.zeros((n, FH, FW, 3), np.uint8)
    have = np.zeros(n, bool)
    log = []
    for si, s in enumerate(g):
        a, b = s["f0"] - F0, s["f1"] - F0
        base, info = slot_base(s, orig[a:b + 1])
        log.append(dict(id=s["id"], info=info))
        if s["inn"][0] == "new":
            ta, tb = s["inn"][1] - F0, s["inn"][2] - F0
            be = beta_curve(s["inn"][1], s["inn"][2])
            for k, i in enumerate(range(ta, tb + 1)):
                w = be[k]
                canvas[i] = (canvas[i].astype(np.float32) * (1 - w) + base[i - a].astype(np.float32) * w).astype(np.uint8)
            canvas[tb + 1:b + 1] = base[tb + 1 - a:]
            have[ta:b + 1] = True
        else:
            canvas[a:b + 1] = base
            have[a:b + 1] = True
    assert have.all()
    first, last = g[0], g[-1]
    out = canvas
    # keep text-free copies of the frames that dissolve with a kept original shot
    notext = {}
    if first["inn"][0] == "kept":
        for f in range(first["inn"][1], first["inn"][2] + 1):
            notext[f] = out[f - F0].copy()
    if last["out"][0] == "kept":
        for f in range(last["out"][1], last["out"][2] + 1):
            notext[f] = out[f - F0].copy()
    # the original's text on top (frame-accurate alpha taken from the original)
    for f in range(F0, F1 + 1):
        for oid in overlays_at(g, f):
            strength = 0.5
            out[f - F0] = composite_text(out[f - F0], orig[f - F0], oid, strength)
    # group ends against the original
    if first["inn"][0] == "fadeblack":
        fa, fb = first["inn"][1], first["inn"][2]
        ref = float(np.mean([STATS[f, 0] for f in range(fb + 1, fb + 6)]))
        for f in range(fa, fb + 1):
            gk = min(1.0, float(STATS[f, 0]) / ref)
            out[f - F0] = (out[f - F0].astype(np.float32) * gk).astype(np.uint8)
    # dissolves with kept original shots: orig = (1-w)*kept + w*(old plate + text), so
    # orig + w*(new plate - old plate) swaps the plate and lets the text and the kept
    # shot through exactly as they were
    def plate(fref):
        fr = orig[fref - F0]
        for oid in overlays_at(g, fref):
            fr = remove_text(fr, oid)
        return fr.astype(np.float32)
    def swap_plate(o, delta, f):
        # opaque text keeps its own colour: no plate change underneath it
        for oid in overlays_at(g, f):
            d = ovl_data(oid)
            x0, y0, x1, y1 = d["box"]
            a = text_alpha(o[y0:y1, x0:x1], d)
            delta[y0:y1, x0:x1] *= (1 - a)[..., None]
        return np.clip(o.astype(np.float32) + delta, 0, 255).astype(np.uint8)
    if first["inn"][0] == "kept":
        ta, tb = first["inn"][1], first["inn"][2]
        be = beta_curve(ta, tb)  # weight of the slot side
        Dh = plate(tb + 1)
        for k, f in enumerate(range(ta, tb + 1)):
            i = f - F0
            out[i] = swap_plate(orig[i], be[k] * (notext[f].astype(np.float32) - Dh), f)
    if last["out"][0] == "kept":
        ta, tb = last["out"][1], last["out"][2]
        be = beta_curve(ta, tb)  # weight of the kept side
        Dh = plate(ta - 1)
        for k, f in enumerate(range(ta, tb + 1)):
            i = f - F0
            out[i] = swap_plate(orig[i], (1 - be[k]) * (notext[f].astype(np.float32) - Dh), f)
    name = f"{g[0]['id']}-{g[-1]['id']}" if len(g) > 1 else g[0]["id"]
    path = f"{OUT}/{name}.mkv"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{FW}x{FH}", "-r", str(FPS),
                            "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
                            "-c:v", "libx264", "-preset", "fast", "-crf", "10", "-colorspace", "bt709",
                            "-color_primaries", "bt709", "-color_trc", "bt709", path], stdin=subprocess.PIPE)
    enc.stdin.write(out.tobytes()); enc.stdin.close(); enc.wait()
    meta = dict(name=name, f0=F0, f1=F1, frames=n, slots=log, secs=round(time.time() - t0, 1))
    json.dump(meta, open(f"{OUT}/{name}.json", "w"), indent=1, default=str)
    print(name, f"f{F0}-{F1}", n, "frames", meta["secs"], "s", flush=True)
    return meta


if __name__ == "__main__":
    want = set(sys.argv[2:])
    todo = [g for g in groups() if not want or any(s["id"] in want for s in g)]
    for g in todo:
        render_group(g)
