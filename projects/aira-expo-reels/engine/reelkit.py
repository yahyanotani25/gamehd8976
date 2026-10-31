"""reelkit: the compositor behind the AIRA expo reels.

Source footage: Sony A7S III, XAVC S HD 1920x1080 at 100p (a few S&Q hyperlapse
clips captured at 6p/3p and stored at 100p). Output: 1080x1920, 30 fps.

A reel is a list of Shots joined by transitions, plus text overlays and the
AIRA logo end card. Every output frame is a pure function of its index, built
in this order:

  source frames (ffmpeg decode + reference-matched 3D LUT)
  -> shutter blend (when a shot plays faster than 1 stored frame per output frame)
  -> reframe to 9:16 (centre / zoom / rotation keyframes, Lanczos)
  -> light sharpening, per-shot effects (B&W halftone flash)
  -> transition compositing (burn, card, whip, zoom, flash, eclipse ...)
  -> vignette + fine grain (matched to the reference)
  -> text overlays -> ffmpeg (H.264, BT.709)
"""
import os, math, json, subprocess, collections
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SW, SH, SFPS = 1920, 1080, 100.0

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, 'assets')
LUT = os.path.join(ASSETS, 'grade', 'ref_grade.cube')
FONT = os.path.join(ASSETS, 'fonts', 'Jost-VF.ttf')
LOGO_POLYS = os.path.join(ASSETS, 'logo', 'aira_logo_polys.json')

# logo card colours sampled from the reference end card (RGB): centre and corners
CARD_CENTRE = (76, 19, 41)
CARD_EDGE = (61, 14, 32)

cv2.setNumThreads(4)


def raw_dirs():
    env = [d for d in os.environ.get('AIRA_RAW', '').split(':') if d]
    return env + [os.path.join(ROOT, 'raw')]


def clip_path(clip):
    for d in raw_dirs():
        for name in (clip + '.MP4', 'keep_' + clip + '.MP4'):
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
    raise FileNotFoundError(f'{clip}.MP4 not found in {raw_dirs()} (set AIRA_RAW)')


# ----------------------------------------------------------------- easing
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def e_lin(p): return clamp01(p)
def e_inout(p): return 0.5 - 0.5 * math.cos(math.pi * clamp01(p))
def e_in(p): return clamp01(p) ** 3
def e_out(p): return 1 - (1 - clamp01(p)) ** 3


def e_expo(p):
    p = clamp01(p)
    if p in (0.0, 1.0):
        return p
    return 0.5 * 2 ** (20 * p - 10) if p < 0.5 else 1 - 0.5 * 2 ** (-20 * p + 10)


EASE = dict(linear=e_lin, inout=e_inout, i=e_in, o=e_out, expo=e_expo)


def kf(keys, p, ease='inout'):
    """Piecewise keyframes [(p, value-or-tuple)]. Linear ease extrapolates past the
    ends (so camera moves keep going through transitions); others hold."""
    def mix(a, b, u):
        if isinstance(a, tuple):
            return tuple(x + (y - x) * u for x, y in zip(a, b))
        return a + (b - a) * u
    if len(keys) == 1:
        return keys[0][1]
    if p < keys[0][0] or p > keys[-1][0]:
        if ease != 'linear':
            return keys[0][1] if p < keys[0][0] else keys[-1][1]
        (p0, v0), (p1, v1) = (keys[0], keys[1]) if p < keys[0][0] else (keys[-2], keys[-1])
        return mix(v0, v1, (p - p0) / (p1 - p0))
    for (p0, v0), (p1, v1) in zip(keys, keys[1:]):
        if p <= p1:
            u = EASE[ease]((p - p0) / (p1 - p0)) if p1 > p0 else 1.0
            return mix(v0, v1, u)
    return keys[-1][1]


# ----------------------------------------------------------------- decode
class Reader:
    """Sequential decoder for one clip from stored frame f_start, LUT applied by ffmpeg."""

    def __init__(self, path, f_start, lut=LUT):
        self.f_start = max(0, int(f_start))
        cmd = ['ffmpeg', '-v', 'error', '-threads', '3', '-ss', f'{self.f_start / SFPS:.5f}', '-i', path,
               '-map', '0:v:0']
        if lut:
            cmd += ['-vf', f"lut3d=file='{lut}':interp=tetrahedral"]
        cmd += ['-f', 'rawvideo', '-pix_fmt', 'bgr24', '-']
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=1 << 24)
        self.next = self.f_start
        self.cache = collections.OrderedDict()
        self.size = SW * SH * 3
        self.eof = False

    def get(self, f):
        f = max(int(f), self.f_start)
        while self.next <= f and not self.eof:
            buf = self.proc.stdout.read(self.size)
            if len(buf) < self.size:
                self.eof = True
                break
            self.cache[self.next] = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
            self.next += 1
            while len(self.cache) > 10:
                self.cache.popitem(last=False)
        if f in self.cache:
            return self.cache[f]
        keys = list(self.cache)
        return self.cache[min(keys, key=lambda k: abs(k - f))]

    def close(self):
        try:
            self.proc.kill()
            self.proc.wait(timeout=5)
        except Exception:
            pass


class ProxyReader:
    """Preview stand-in for Reader: decodes the 640x360 25 fps review proxy (one frame per
    4 stored frames) and upsizes it, so edits can be checked before fetching originals."""

    def __init__(self, path, f_start, lut=LUT):
        self.f_start = max(0, int(f_start))
        cmd = ['ffmpeg', '-v', 'error', '-ss', f'{self.f_start / SFPS:.5f}', '-i', path, '-map', '0:v:0']
        if lut:
            cmd += ['-vf', f"lut3d=file='{lut}'"]
        cmd += ['-f', 'rawvideo', '-pix_fmt', 'bgr24', '-']
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=1 << 22)
        self.q_next = 0
        self.cache = collections.OrderedDict()
        self.eof = False

    def get(self, f):
        q = max(0, int(round((int(f) - self.f_start) / 4.0)))
        while self.q_next <= q and not self.eof:
            buf = self.proc.stdout.read(640 * 360 * 3)
            if len(buf) < 640 * 360 * 3:
                self.eof = True
                break
            small = np.frombuffer(buf, np.uint8).reshape(360, 640, 3)
            self.cache[self.q_next] = cv2.resize(small, (SW, SH), interpolation=cv2.INTER_LINEAR)
            self.q_next += 1
            while len(self.cache) > 4:
                self.cache.popitem(last=False)
        if q in self.cache:
            return self.cache[q]
        return self.cache[min(self.cache, key=lambda k: abs(k - q))]

    def close(self):
        try:
            self.proc.kill()
            self.proc.wait(timeout=5)
        except Exception:
            pass


def open_reader(clip, f_start):
    prx = os.environ.get('AIRA_PROXY_DIR')
    if prx:
        return ProxyReader(os.path.join(prx, clip + '.mp4'), f_start)
    return Reader(clip_path(clip), f_start)


def blend(frames):
    if len(frames) == 1:
        return frames[0]
    acc = frames[0].astype(np.uint16)
    for fr in frames[1:]:
        acc += fr
    return (acc // len(frames)).astype(np.uint8)


def reframe_matrix(cx, cy, z, rot):
    """Affine source->output for a 9:16 window centred on (cx, cy) in 1920x1080 source
    pixels. z=1 fills the output height with the full source height. Clamped so the
    window never leaves the source frame (no borders)."""
    a = math.radians(rot)
    ca, sa = abs(math.cos(a)), abs(math.sin(a))
    s = (H / SH) * z
    # half extents of the rotated output window, measured in source pixels
    hx = (W / 2 * ca + H / 2 * sa) / s
    hy = (W / 2 * sa + H / 2 * ca) / s
    if hy > SH / 2 or hx > SW / 2:  # zoom in just enough to stay inside
        k = max(hy / (SH / 2), hx / (SW / 2)) * 1.002
        s *= k
        hx /= k
        hy /= k
    cx = min(max(cx, hx), SW - hx)
    cy = min(max(cy, hy), SH - hy)
    c, si = math.cos(a) * s, math.sin(a) * s
    return np.array([[c, -si, W / 2 - c * cx + si * cy],
                     [si, c, H / 2 - si * cx - c * cy]], np.float32)


def sharpen(img, amount=0.38, sigma=1.1):
    blur = cv2.GaussianBlur(img, (0, 0), sigma)
    return cv2.addWeighted(img, 1 + amount, blur, -amount, 0)


# ----------------------------------------------------------------- effects
_halftone = None


def fx_bw_halftone(img):
    """The reference's 5-frame beat flash: high-contrast B&W with a dot screen and
    deep navy shadows."""
    global _halftone
    if _halftone is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        per = 7.0
        u = (xx * 0.7071 + yy * 0.7071) / per
        v = (-xx * 0.7071 + yy * 0.7071) / per
        _halftone = ((np.cos(2 * np.pi * u) * np.cos(2 * np.pi * v)) * 0.5 + 0.5).astype(np.float32)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    g = np.clip((g - 0.30) * 2.3, 0, 1)
    dots = (g > _halftone).astype(np.float32)
    t = 0.55 * g + 0.45 * dots
    lo = np.array([46, 22, 18], np.float32) / 255.0  # BGR deep navy
    hi = np.array([250, 250, 252], np.float32) / 255.0
    out = lo + (hi - lo) * t[..., None]
    return (out * 255).astype(np.uint8)


class Leak:
    """Procedural warm film-burn / light leak (screen-blended)."""

    def __init__(self, seed=1, band=False):
        rng = np.random.default_rng(seed)
        self.band = band
        self.blobs = []
        for _ in range(5):
            self.blobs.append(dict(
                x=rng.uniform(0.1, 0.9), y=rng.uniform(0.15, 0.85),
                vx=rng.uniform(-0.5, 0.5), vy=rng.uniform(-0.25, 0.25),
                sx=rng.uniform(0.25, 0.6), sy=rng.uniform(0.2, 0.5),
                col=[np.array([120, 200, 255]), np.array([70, 150, 255]), np.array([60, 110, 240]),
                     np.array([150, 225, 255])][rng.integers(0, 4)] / 255.0,
                w=rng.uniform(0.6, 1.2)))
        self.small = (W // 8, H // 8)
        ys, xs = np.mgrid[0:self.small[1], 0:self.small[0]].astype(np.float32)
        self.xx = xs / self.small[0]
        self.yy = ys / self.small[1]

    def frame(self, p):
        acc = np.zeros((self.small[1], self.small[0], 3), np.float32)
        for b in self.blobs:
            cx = b['x'] + b['vx'] * p
            cy = b['y'] + b['vy'] * p
            g = np.exp(-(((self.xx - cx) / b['sx']) ** 2 + ((self.yy - cy) / b['sy']) ** 2))
            acc += (g * b['w'])[..., None] * b['col']
        if self.band:  # film-gate band through the middle (reference opening)
            g = np.exp(-((self.yy - 0.5) / 0.09) ** 2) * (0.6 + 0.4 * np.exp(-((self.xx - 0.5) / 0.35) ** 2))
            acc += g[..., None] * np.array([150, 225, 255], np.float32) / 255.0 * 1.6
        acc = 1 - np.exp(-acc * 1.6)
        return cv2.resize(acc, (W, H), interpolation=cv2.INTER_CUBIC)


def screen(img, leak, k):
    f = img.astype(np.float32)
    return np.clip(f + (255.0 - f) * np.clip(leak * k, 0, 1), 0, 255).astype(np.uint8)


def flare_line(img, y, strength, x0=0.5):
    """Thin anamorphic flare streak across the frame at height y (reference: across the logo)."""
    ys = np.arange(H, dtype=np.float32)[:, None]
    xs = np.arange(W, dtype=np.float32)[None, :]
    d = np.abs(ys - y)
    prof = 1.0 * np.exp(-(d / 2.2) ** 2) + 0.45 * np.exp(-(d / 14) ** 2) + 0.18 * np.exp(-(d / 70) ** 2)
    horiz = 0.25 + 0.75 * np.exp(-((xs - x0 * W) / (0.55 * W)) ** 2)
    a = np.clip(prof * horiz * strength, 0, 1)[..., None]
    col = np.array([215, 235, 255], np.float32)  # warm white (BGR)
    f = img.astype(np.float32)
    return np.clip(f + (col - f * 0.0) * a * (1 - f / 255.0 * 0.4), 0, 255).astype(np.uint8)


_dist = None


def _dist_map():
    global _dist
    if _dist is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        _dist = np.hypot(xx - W / 2, yy - H / 2)
    return _dist


def eclipse_ring(r):
    """Black disk with a white corona ring on black (reference 11.6-11.75s)."""
    d = _dist_map()
    ring = np.exp(-((d - r) / (0.10 * r + 2.0)) ** 2)
    glow = np.exp(-np.clip(d - r, 0, None) / (0.55 * r + 10)) * 0.45
    v = np.clip(ring + glow, 0, 1)
    v[d < r * 0.93] = 0
    return np.repeat((v * 245)[..., None], 3, 2).astype(np.uint8)


_gate_xy = None


def gate_open(b, p):
    """The reference's opening (0.1-0.75 s): a warm film-gate light band on black,
    which opens into a horizontally smeared, overexposed first shot that settles."""
    global _gate_xy
    if _gate_xy is None:
        _gate_xy = (np.abs(np.linspace(-1, 1, W, dtype=np.float32))[None, :],
                    np.abs(np.linspace(-1, 1, H, dtype=np.float32))[:, None])
    ax, ay = _gate_xy
    op = e_inout((p - 0.40) / 0.26)                  # 0: band, 1: full frame
    hh, hw = 0.12 + 1.25 * op, 0.80 + 0.6 * op       # half height / half width
    sy, sx = 0.05 + 0.25 * op, 0.16
    mask = np.clip((hh - ay) / sy, 0, 1) * np.clip((hw - ax) / sx, 0, 1)
    mask = (mask * mask * (3 - 2 * mask)) * e_out(p / 0.2)
    smear = int(320 * (1 - e_out((p - 0.38) / 0.5))) + 1
    img = cv2.blur(b, (smear, 3)) if smear > 2 else b
    gain = 1 + 2.6 * (1 - e_out((p - 0.48) / 0.52))
    warm = 1 - e_inout((p - 0.55) / 0.45)
    tint = np.array([1 - 0.22 * warm, 1 - 0.06 * warm, 1 + 0.10 * warm], np.float32)  # BGR, toward amber
    out = img.astype(np.float32) * (gain * tint)
    knee = 185.0  # filmic shoulder: values above the knee approach white smoothly
    out = np.where(out > knee, knee + (255 - knee) * (1 - np.exp(-(out - knee) / (255 - knee))), out)
    return np.clip(out * mask[..., None], 0, 255).astype(np.uint8)


def glitch_band(img, y0, h, seed):
    """Horizontal streaked band (pixels smeared sideways), bright."""
    rng = np.random.default_rng(seed)
    out = img.copy()
    band = img[y0:y0 + h]
    small = cv2.resize(band, (max(4, W // 40), h), interpolation=cv2.INTER_AREA)
    streak = cv2.resize(small, (W, h), interpolation=cv2.INTER_NEAREST)
    rows = rng.integers(0, h, size=h)
    streak = streak[np.sort(rows)]
    streak = np.clip(streak.astype(np.float32) * 0.5 + 150, 0, 255).astype(np.uint8)
    out[y0:y0 + h] = streak
    return out


def white_bloom_disk(img, seed):
    """Over-exposed white frame with a large soft black disk and a glitch bar (11.57s)."""
    d = _dist_map()
    base = np.clip(img.astype(np.float32) * 0.25 + 205, 0, 255)
    r = 0.42 * W
    k = np.clip((d - r) / (0.07 * W), 0, 1)[..., None]
    k = k * k * (3 - 2 * k)
    out = (base * k).astype(np.uint8)
    return glitch_band(out, int(H * 0.46), int(H * 0.08), seed)


# ----------------------------------------------------------------- sources
class Shot:
    """One piece of footage.

    clip   source clip name, e.g. 'C0019'
    t_in   stored-timeline second (frame/100) shown at the shot's first nominal frame
    dur    nominal duration in output seconds (cut to cut)
    speed  stored seconds advanced per output second (1 = real time, 0.3 = 1:1 frames
           = 3.33x slow motion); constant or [(t_out_sec, speed), ...]
    frame  [(p, (cx, cy, z, rot)), ...] reframing keys over the nominal duration
    fx     [(kind, t0, t1)] effects in shot-local output seconds, e.g. ('bw', 1.2, 1.37)
    """

    footage = True

    def __init__(self, clip, t_in, dur, speed=1.0, frame=None, ease='linear', shutter=0.5, fx=None,
                 note=''):
        self.clip, self.t_in, self.dur = clip, float(t_in), float(dur)
        self.n = int(round(self.dur * FPS))
        self.speed = speed
        self.frame = frame or [(0.0, (960.0, 540.0, 1.0, 0.0))]
        self.ease = ease
        self.shutter = shutter
        self.fx = fx or []
        self.note = note
        self.reader = None

    def speed_at(self, t):
        if isinstance(self.speed, (int, float)):
            return float(self.speed)
        return kf(self.speed, t, 'linear') if len(self.speed) > 1 else self.speed[0][1]

    def prepare(self, pre, post):
        self.pre = pre
        us = np.arange(-pre, self.n + post + 1)
        sp = np.array([self.speed_at(u / FPS) for u in us])
        # integrate speed (stored frames per output frame = speed * SFPS / FPS)
        step = sp * SFPS / FPS
        pos = np.concatenate([[0.0], np.cumsum((step[1:] + step[:-1]) / 2)])
        zero = pos[pre]
        self.pos = self.t_in * SFPS + (pos - zero)
        self.step = step
        first = max(0.0, float(self.pos.min()))
        self.reader = open_reader(self.clip, math.floor(first))

    def render(self, u):
        if getattr(self, '_last', None) is not None and self._last[0] == u:
            return self._last[1]
        i = u + self.pre
        pos = max(0.0, float(self.pos[i]))
        span = self.shutter * float(self.step[i])
        if span < 1.0:
            img = self.reader.get(int(round(pos)))
        else:
            k = min(6, int(math.floor(span)) + 1)
            f0 = int(math.floor(pos))
            img = blend([self.reader.get(f0 + j) for j in range(k)])
        p = u / max(1, self.n - 1)
        cx, cy, z, rot = kf(self.frame, p, self.ease)
        out = cv2.warpAffine(img, reframe_matrix(cx, cy, z, rot), (W, H), flags=cv2.INTER_LANCZOS4,
                             borderMode=cv2.BORDER_REFLECT101)
        out = sharpen(out)
        if not hasattr(self, 'hist'):
            self.hist = collections.OrderedDict()
        self.hist[u] = out
        while len(self.hist) > 8:
            self.hist.popitem(last=False)
        t = u / FPS
        for kind, t0, t1 in self.fx:
            if not (t0 <= t < t1):
                continue
            if kind == 'bw':
                out = fx_bw_halftone(out)
            elif kind == 'echo':
                # reference 8.80 s: a double-exposure stutter, the frame from 3 frames
                # earlier laid over the current one with a sideways offset
                prev = self.hist.get(u - 3)
                if prev is not None:
                    out = cv2.addWeighted(out, 0.55, _shift(prev, 48, -10), 0.45, 0)
        self._last = (u, out)
        return out

    def close(self):
        if self.reader:
            self.reader.close()
            self.reader = None


class Card:
    """The AIRA logo end card: wine radial gradient + white logo (traced from the
    reference card), hard cut in like the reference; the last `fade` seconds fade to
    black and `tail` seconds of black close the reel, as the reference ends."""

    footage = False

    def __init__(self, dur, logo_width=0.52, fade=0.45, tail=0.3):
        self.dur = dur
        self.n = int(round(dur * FPS))
        self.img = logo_card(logo_width)
        self.fade_n = int(round(fade * FPS))
        self.tail_n = int(round(tail * FPS))
        self.note = 'AIRA logo card, fade to black'

    def prepare(self, pre, post):
        pass

    def render(self, u):
        left = self.n - u  # frames remaining including this one
        if left <= self.tail_n:
            return np.zeros_like(self.img)
        if left <= self.tail_n + self.fade_n:
            k = (left - self.tail_n) / (self.fade_n + 1)
            return cv2.convertScaleAbs(self.img, alpha=e_inout(k))
        return self.img

    def close(self):
        pass


class Black:
    footage = False

    def __init__(self, dur):
        self.dur = dur
        self.n = int(round(dur * FPS))
        self.note = 'black'

    def prepare(self, pre, post):
        pass

    def render(self, u):
        return np.zeros((H, W, 3), np.uint8)

    def close(self):
        pass


def logo_layer(width_px):
    """Rasterise the traced AIRA logo polygons (white, anti-aliased) as an RGBA array."""
    data = json.load(open(LOGO_POLYS))
    asp = data['aspect']
    ss = 4
    wl = int(width_px * ss)
    hl = int(round(wl / asp))
    acc = np.zeros((hl, wl), np.uint8)
    for poly in data['polys']:
        m = Image.new('L', (wl, hl), 0)
        ImageDraw.Draw(m).polygon([(x * hl, y * hl) for x, y in poly], fill=255)
        acc ^= np.asarray(m)
    a = np.asarray(Image.fromarray(acc).resize((int(width_px), int(round(width_px / asp))), Image.LANCZOS))
    return a


def logo_card(width_frac=0.52):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)) / math.sqrt(2)
    f = np.clip(r, 0, 1) ** 2.8
    c0 = np.array(CARD_CENTRE[::-1], np.float32)
    c1 = np.array(CARD_EDGE[::-1], np.float32)
    bg = c0 + (c1 - c0) * f[..., None]
    bg += np.random.default_rng(7).normal(0, 0.6, bg.shape).astype(np.float32)  # dither, no banding
    a = logo_layer(W * width_frac).astype(np.float32) / 255.0
    h, w = a.shape
    y0 = (H - h) // 2
    x0 = (W - w) // 2
    reg = bg[y0:y0 + h, x0:x0 + w]
    bg[y0:y0 + h, x0:x0 + w] = reg * (1 - a[..., None]) + 252.0 * a[..., None]
    return np.clip(bg, 0, 255).astype(np.uint8)


# ----------------------------------------------------------------- transitions
class Tr:
    """Transition between two sources, n frames centred on the cut."""

    def __init__(self, kind='cut', n=0, **kw):
        self.kind, self.n, self.kw = kind, (0 if kind == 'cut' else n), kw
        self.leak = Leak(kw.get('seed', 3), band=kw.get('band', False)) if kind == 'burn' else None


def _shift(img, dx, dy):
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT101)


def _scale_about_centre(img, s, cx=W / 2, cy=H / 2, rot=0.0, interp=cv2.INTER_LINEAR):
    M = cv2.getRotationMatrix2D((cx, cy), rot, s)
    return cv2.warpAffine(img, M, (W, H), flags=interp, borderMode=cv2.BORDER_REFLECT101)


def _card_layer(img, border):
    """White-bordered, round-cornered photo card (RGB + alpha) in its own space."""
    b = border
    hh, ww = H + 2 * b, W + 2 * b
    card = np.full((hh, ww, 3), 246, np.uint8)
    card[b:b + H, b:b + W] = img
    rad = int(0.045 * W)
    m = Image.new('L', (ww, hh), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, ww - 1, hh - 1], radius=rad, fill=255)
    return card, np.asarray(m)


_card_mask_cache = {}


def _draw_card(canvas, img, scale, angle, cx, cy, border_vis=1.0):
    b = int(0.03 * W)
    card, alpha = _card_layer(img, b)
    if border_vis < 1.0:
        inner = np.full_like(card, 0)
        card = card  # border colour stays; visibility handled by alpha below
        a2 = alpha.astype(np.float32)
        a2[:b, :] *= border_vis
        a2[-b:, :] *= border_vis
        a2[:, :b] *= border_vis
        a2[:, -b:] *= border_vis
        alpha = a2.astype(np.uint8)
    hh, ww = card.shape[:2]
    M = cv2.getRotationMatrix2D((ww / 2, hh / 2), angle, scale)
    M[0, 2] += cx - ww / 2
    M[1, 2] += cy - hh / 2
    wc = cv2.warpAffine(card, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
    wa = cv2.warpAffine(alpha, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0).astype(np.float32) / 255.0
    # soft drop shadow
    sm = cv2.resize(wa, (W // 6, H // 6), interpolation=cv2.INTER_AREA)
    sm = cv2.GaussianBlur(sm, (0, 0), 4)
    sh = cv2.resize(sm, (W, H), interpolation=cv2.INTER_LINEAR)
    sh = np.roll(np.roll(sh, 14, 0), 8, 1)
    out = canvas.astype(np.float32) * (1 - 0.55 * sh[..., None])
    out = out * (1 - wa[..., None]) + wc.astype(np.float32) * wa[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def apply_transition(tr, a, b, k, ctx):
    """a: outgoing frame, b: incoming frame, k: index in window [0, n)."""
    n = tr.n
    p = (k + 0.5) / n
    kind = tr.kind
    kw = tr.kw
    if kind == 'dissolve':
        return cv2.addWeighted(a, 1 - p, b, p, 0)
    if kind == 'gate':
        return gate_open(b, p)
    if kind == 'flash':
        w = (1 - abs(p - 0.5) / 0.5) ** 1.5 * kw.get('peak', 0.92)
        img = a if p < 0.5 else b
        return cv2.addWeighted(img, 1 - w, np.full_like(img, 255), w, 0)
    if kind == 'burn':
        env = math.sin(math.pi * p) ** 0.8
        leak = tr.leak.frame(p)
        mix = e_inout((p - 0.35) / 0.3)
        base = cv2.addWeighted(a, 1 - mix, b, mix, 0)
        base = cv2.convertScaleAbs(base, alpha=1 + 0.9 * env, beta=0)
        return screen(base, leak, 1.15 * env)
    if kind == 'whip':
        d = kw.get('dir', 'left')
        u = e_expo(p)
        vel = abs(e_expo(min(1, p + 0.5 / n)) - e_expo(max(0, p - 0.5 / n))) * n
        horiz = d in ('left', 'right')
        span = W if horiz else H
        off = int(round(u * span))
        canvas = np.empty_like(a)
        if d == 'left':      # content moves left: B enters from the right
            canvas[:, :W - off] = a[:, off:]
            canvas[:, W - off:] = b[:, :off]
        elif d == 'right':
            canvas[:, off:] = a[:, :W - off]
            canvas[:, :off] = b[:, W - off:]
        elif d == 'up':
            canvas[:H - off] = a[off:]
            canvas[H - off:] = b[:off]
        else:
            canvas[off:] = a[:H - off]
            canvas[:off] = b[H - off:]
        k_blur = int(min(span * 0.45, 4 + vel * span / n * 0.9))
        if k_blur > 2:
            canvas = cv2.blur(canvas, (k_blur, 1) if horiz else (1, k_blur))
        return canvas
    if kind == 'zoom':
        if p < 0.5:
            q = p / 0.5
            img, s0, strength = a, 1 + 0.35 * e_in(q), e_in(q)
        else:
            q = (p - 0.5) / 0.5
            img, s0, strength = b, 1.35 - 0.35 * e_out(q), 1 - e_out(q)
        layers = [_scale_about_centre(img, s0 * (1 + 0.10 * strength * i / 4)) for i in range(5)]
        acc = np.zeros((H, W, 3), np.float32)
        for l in layers:
            acc += l
        out = (acc / len(layers)).astype(np.uint8)
        return cv2.convertScaleAbs(out, alpha=1 + 0.25 * strength)
    if kind == 'blur':
        sig = 0.5 + 38 * math.sin(math.pi * p) ** 1.2
        img = cv2.addWeighted(a, 1 - e_inout((p - 0.3) / 0.4), b, e_inout((p - 0.3) / 0.4), 0)
        sm = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        sm = cv2.GaussianBlur(sm, (0, 0), sig / 4)
        return cv2.resize(sm, (W, H), interpolation=cv2.INTER_LINEAR) if sig > 3 else img
    if kind == 'card':
        # reference 3.5-4.2s: A shrinks into a white-bordered photo card over a blurred
        # backdrop, B flies in as a tilted card from the left, then grows to full frame
        sm = cv2.resize(b, (W // 8, H // 8), interpolation=cv2.INTER_AREA)
        sm = cv2.GaussianBlur(sm, (0, 0), 5)
        bg = cv2.resize(sm, (W, H), interpolation=cv2.INTER_LINEAR)
        bg = cv2.convertScaleAbs(bg, alpha=0.82)
        out = bg
        sA = 1 - 0.26 * e_out(p / 0.3)
        if p < 0.78:
            out = _draw_card(out, a, sA, -2.5 * e_inout(p / 0.5), W / 2 + 40 * e_inout(p / 0.6),
                             H / 2, border_vis=min(1, p / 0.08))
        if p > 0.22:
            q = (p - 0.22) / 0.78
            x = -0.75 * W + (W / 2 + 0.75 * W) * e_out(q / 0.5)
            ang = 13 * (1 - e_out(q / 0.6))
            sB = 0.74 + 0.27 * e_inout((q - 0.5) / 0.5)
            vis = 1 - e_inout((q - 0.75) / 0.25)
            out = _draw_card(out, b, sB, ang, x, H / 2 + 20 * (1 - e_out(q)), border_vis=vis)
            if q > 0.82:  # land exactly on the full-frame incoming shot
                m = e_inout((q - 0.82) / 0.18)
                out = cv2.addWeighted(out, 1 - m, b, m, 0)
        if p < 0.1:       # leave the outgoing shot without a jump
            m = e_inout(p / 0.1)
            out = cv2.addWeighted(a, 1 - m, out, m, 0)
        return out
    if kind == 'eclipse':
        # frame-exact recreation of the reference's logo reveal (11.37-11.9s):
        # flare line, glitch, white bloom with black disk, shrinking ring, black, card
        y = kw.get('flare_y', H * 0.3)
        seq = k
        if seq <= 3:
            s = [0.35, 0.9, 1.0, 0.5][seq]
            return flare_line(a, y, s)
        if seq <= 5:
            return flare_line(a, y, [0.25, 0.1][seq - 4])
        if seq == 6:
            dark = cv2.convertScaleAbs(a, alpha=0.6)
            return glitch_band(dark, int(H * 0.40), int(H * 0.2), 11)
        if seq == 7:
            return white_bloom_disk(a, 12)
        if seq <= 12:
            r = 0.27 * W * (0.58 ** (seq - 8))
            return eclipse_ring(r)
        if seq <= 16:
            return np.zeros_like(a)
        return b
    raise ValueError(kind)


# ----------------------------------------------------------------- finishing
class Finisher:
    """Vignette matched to the reference (corner falloff ~0.82) + fine film grain."""

    def __init__(self, grain=2.4, seed=5):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)) / math.sqrt(2)
        # fitted from reference: 1.0 inside r<0.5, 0.94 at 0.7, 0.82 at 1.0
        v = 1.0 - 0.19 * np.clip((r - 0.45) / 0.55, 0, 1) ** 1.6
        self.vig = (v * 256).astype(np.uint16)[..., None]
        rng = np.random.default_rng(seed)
        self.grain = []
        for _ in range(6):
            g = rng.normal(0, grain, (H // 2, W // 2)).astype(np.float32)
            g = cv2.resize(cv2.GaussianBlur(g, (0, 0), 0.6), (W, H), interpolation=cv2.INTER_LINEAR)
            self.grain.append(np.repeat(g[..., None], 3, 2).astype(np.int16))
        self.rng = rng

    def __call__(self, img, i, vignette=True, grain=True):
        out = img
        if vignette:
            out = ((out.astype(np.uint16) * self.vig) >> 8).astype(np.uint8)
        if grain:
            out = np.clip(out.astype(np.int16) + self.grain[i % len(self.grain)], 0, 255).astype(np.uint8)
        return out


# ----------------------------------------------------------------- text
def text_layer(lines, size=60, weight=400, tracking=0.18, line_gap=1.35, upper=False, color=(255, 255, 255),
               shadow=0.55, scrim=0.0, pad=60, sizes=None, weights=None, trackings=None):
    """Render centred lines to an RGBA numpy array (BGR + A). Per-line sizes/weights optional."""
    ss = 2
    fonts = []
    for i, ln in enumerate(lines):
        sz = (sizes[i] if sizes else size) * ss
        f = ImageFont.truetype(FONT, int(sz))
        f.set_variation_by_axes([weights[i] if weights else weight])
        fonts.append(f)
    tr = [((trackings[i] if trackings else tracking)) for i in range(len(lines))]
    lines = [ln.upper() if upper else ln for ln in lines]

    def line_w(ln, f, t):
        w = 0
        for ch in ln:
            w += f.getlength(ch) + t * f.size
        return w - t * f.size

    widths = [line_w(ln, f, t) for ln, f, t in zip(lines, fonts, tr)]
    heights = [f.size for f in fonts]
    tw = int(max(widths)) + 2 * pad * ss
    th = int(sum(h * line_gap for h in heights)) + 2 * pad * ss
    img = Image.new('L', (tw, th), 0)
    dr = ImageDraw.Draw(img)
    y = pad * ss
    for ln, f, t, wv, hv in zip(lines, fonts, tr, widths, heights):
        x = (tw - wv) / 2
        for ch in ln:
            dr.text((x, y), ch, font=f, fill=255)
            x += f.getlength(ch) + t * f.size
        y += hv * line_gap
    alpha = np.asarray(img).astype(np.float32) / 255.0
    sh = np.asarray(img.filter(ImageFilter.GaussianBlur(9 * ss))).astype(np.float32) / 255.0
    sh = np.clip(sh * 1.6, 0, 1) * shadow
    if scrim > 0:
        sc = Image.new('L', (tw, th), 0)
        ImageDraw.Draw(sc).rounded_rectangle([pad * ss * 0.4, pad * ss * 0.5, tw - pad * ss * 0.4, th - pad * ss * 0.5],
                                             radius=40 * ss, fill=255)
        sc = np.asarray(sc.filter(ImageFilter.GaussianBlur(28 * ss))).astype(np.float32) / 255.0 * scrim
        sh = np.maximum(sh, sc)
    a = alpha + sh * (1 - alpha)
    col = np.array(color[::-1], np.float32)
    rgb = np.where(a[..., None] > 1e-4, (alpha[..., None] * col) / np.maximum(a[..., None], 1e-4), 0)
    out = np.dstack([rgb, a * 255]).astype(np.float32)
    out = cv2.resize(out, (tw // ss, th // ss), interpolation=cv2.INTER_AREA)
    return out  # float32 BGRA, colour not premultiplied


class Overlay:
    """Text/graphic layer on the output timeline (seconds), centred at (cx, cy)."""

    def __init__(self, layer, t0, t1, cx=W / 2, cy=H * 0.3, fade_in=0.35, fade_out=0.3, drift=16):
        self.layer, self.t0, self.t1 = layer, t0, t1
        self.cx, self.cy = cx, cy
        self.fi, self.fo, self.drift = fade_in, fade_out, drift

    def apply(self, img, t):
        if not (self.t0 <= t < self.t1):
            return img
        a_in = e_out((t - self.t0) / self.fi) if self.fi > 0 else 1
        a_out = 1 - e_inout((t - (self.t1 - self.fo)) / self.fo) if self.fo > 0 else 1
        k = min(a_in, a_out)
        dy = (1 - a_in) * self.drift
        lay = self.layer
        h, w = lay.shape[:2]
        x0 = int(round(self.cx - w / 2))
        y0 = int(round(self.cy - h / 2 + dy))
        xa, ya = max(0, x0), max(0, y0)
        xb, yb = min(W, x0 + w), min(H, y0 + h)
        if xb <= xa or yb <= ya:
            return img
        sub = lay[ya - y0:yb - y0, xa - x0:xb - x0]
        al = sub[..., 3:4] / 255.0 * k
        reg = img[ya:yb, xa:xb].astype(np.float32)
        img = img.copy()
        img[ya:yb, xa:xb] = np.clip(reg * (1 - al) + sub[..., :3] * al, 0, 255).astype(np.uint8)
        return img


# ----------------------------------------------------------------- timeline
class Reel:
    def __init__(self, name):
        self.name = name
        self.items = []      # [source, Tr-to-next]
        self.overlays = []
        self.no_finish = set()

    def add(self, src, tr=None):
        self.items.append([src, tr or Tr('cut')])
        return self

    def text(self, *a, **k):
        self.overlays.append(Overlay(*a, **k))
        return self

    def layout(self):
        """Nominal cut points; each transition window is centred on its cut."""
        starts, t = [], 0
        for src, _ in self.items:
            starts.append(t)
            t += src.n
        self.starts, self.total = starts, t
        self.windows = []
        for i, (src, tr) in enumerate(self.items[:-1]):
            cut = starts[i + 1]
            if tr.kind == 'eclipse':
                pre = 7          # flare + glitch + bloom on the outgoing shot, ring/black after
                self.windows.append((cut - pre, cut - pre + 17, i, tr))
            else:
                na = tr.n // 2
                self.windows.append((cut - na, cut - na + tr.n, i, tr))
        return self

    def describe(self):
        self.layout()
        rows = []
        for i, (src, tr) in enumerate(self.items):
            rows.append(dict(i=i, start=round(self.starts[i] / FPS, 3), dur=round(src.n / FPS, 3),
                             src=getattr(src, 'clip', type(src).__name__), t_in=getattr(src, 't_in', None),
                             speed=getattr(src, 'speed', None), note=src.note, tr_out=tr.kind))
        return rows

    def render(self, out_path, audio=None, preview_scale=None, frames=None, crf=17):
        self.layout()
        n_total = self.total
        need = collections.defaultdict(lambda: [0, 0])  # per item: pre, post frames
        for (w0, w1, i, tr) in self.windows:
            cut = self.starts[i + 1]
            need[i][1] = max(need[i][1], w1 - cut)
            need[i + 1][0] = max(need[i + 1][0], cut - w0)
        fin = Finisher()
        ow, oh = (W, H) if not preview_scale else (int(W * preview_scale) // 2 * 2, int(H * preview_scale) // 2 * 2)
        cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{ow}x{oh}',
               '-r', str(FPS), '-i', '-']
        if audio:
            cmd += ['-i', audio]
        vf = 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p'
        cmd += ['-vf', vf, '-c:v', 'libx264', '-preset', 'slow' if not preview_scale else 'veryfast',
                '-crf', str(crf if not preview_scale else 24), '-profile:v', 'high', '-level', '4.2',
                '-g', '30', '-bf', '2', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                '-color_range', 'tv', '-r', str(FPS)]
        if audio:
            cmd += ['-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-shortest']
        cmd += ['-movflags', '+faststart', out_path]
        enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        active = {}
        rng = range(n_total) if frames is None else frames
        try:
            for fno in rng:
                # which items are needed at this frame
                want = []
                for i, (src, _) in enumerate(self.items):
                    s0 = self.starts[i] - need[i][0]
                    s1 = self.starts[i] + src.n + need[i][1]
                    if s0 <= fno < s1:
                        want.append(i)
                for i in list(active):
                    if i not in want:
                        self.items[i][0].close()
                        del active[i]
                for i in want:
                    if i not in active:
                        self.items[i][0].prepare(need[i][0], need[i][1])
                        active[i] = True
                win = None
                for (w0, w1, i, tr) in self.windows:
                    if w0 <= fno < w1:
                        win = (w0, w1, i, tr)
                if win:
                    w0, w1, i, tr = win
                    a_src, b_src = self.items[i][0], self.items[i + 1][0]
                    k = fno - w0
                    if tr.kind == 'eclipse':
                        a = a_src.render(min(fno - self.starts[i], a_src.n - 1 + need[i][1]))
                        b = b_src.render(0)
                    else:
                        a = a_src.render(fno - self.starts[i])
                        b = b_src.render(fno - self.starts[i + 1])
                    img = apply_transition(tr, a, b, k, None)
                    footage = a_src.footage or (b_src.footage and tr.kind != 'eclipse')
                    if tr.kind == 'eclipse' and k > 6:
                        footage = False
                else:
                    i = max(j for j in range(len(self.items)) if self.starts[j] <= fno)
                    src = self.items[i][0]
                    img = src.render(fno - self.starts[i])
                    footage = src.footage
                # pure black stays pure black (opening, eclipse, final fade), as in the reference
                img = fin(img, fno, vignette=footage, grain=bool(img.max() > 12))
                t = fno / FPS
                for ov in self.overlays:
                    img = ov.apply(img, t)
                if preview_scale:
                    img = cv2.resize(img, (ow, oh), interpolation=cv2.INTER_AREA)
                enc.stdin.write(img.tobytes())
        finally:
            for i in list(active):
                self.items[i][0].close()
            enc.stdin.close()
            enc.wait()
        return out_path
