"""Small DSP toolkit for synthesising the film's sound effects and music.

Everything is numpy at 48 kHz; stereo signals are (n, 2) float arrays.
"""
import numpy as np
import scipy.signal as ss
import soundfile as sf

SR = 48000


def secs(dur):
    return np.arange(int(round(dur * SR))) / SR


def rng(seed):
    return np.random.default_rng(seed)


def db(x):
    return 10 ** (x / 20)


def exp_env(n, attack=0.002, decay=0.2):
    """Linear attack, exponential decay (decay = time constant, s)."""
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-6), 0, 1)
    return a * np.exp(-np.maximum(t - attack, 0) / decay)


def adsr(n, a=0.01, d=0.1, s=0.7, r=0.2, hold=None):
    """ADSR with the note held for `hold` seconds (default: until release fits)."""
    t = np.arange(n) / SR
    total = n / SR
    hold = total - r if hold is None else hold
    e = np.where(t < a, t / max(a, 1e-6), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-6)))
    rel = np.clip((t - hold) / max(r, 1e-6), 0, 1)
    return e * np.where(t > hold, (1 - rel) ** 2, 1)


def phase(freq):
    """Integrate an instantaneous-frequency array (Hz) into phase (radians)."""
    return 2 * np.pi * np.cumsum(freq) / SR


def glide(f0, f1, n, curve=4.0):
    """Exponential-ish pitch glide from f0 to f1 over n samples."""
    x = np.linspace(0, 1, n)
    k = (1 - np.exp(-curve * x)) / (1 - np.exp(-curve))
    return f0 * (f1 / f0) ** k


def saw(freq, n, max_h=None, decay_per_h=0.0, t0=0.0):
    """Band-limited saw from additive harmonics. freq: Hz scalar or array."""
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    ph = phase(f) + t0
    out = np.zeros(n)
    top = float(np.max(f))
    H = int(min(max_h or 60, (SR / 2 - 500) / max(top, 1)))
    t = np.arange(n) / SR
    for h in range(1, H + 1):
        amp = 1.0 / h
        if decay_per_h:
            amp = amp * np.exp(-t * decay_per_h * (h - 1))
        out += amp * np.sin(h * ph)
    return out * (2 / np.pi)


def lp(x, f, order=2):
    return ss.sosfilt(ss.butter(order, min(f, SR / 2 - 100), 'low', fs=SR, output='sos'), x, axis=0)


def hp(x, f, order=2):
    return ss.sosfilt(ss.butter(order, f, 'high', fs=SR, output='sos'), x, axis=0)


def bp(x, lo, hi, order=2):
    return ss.sosfilt(ss.butter(order, [lo, min(hi, SR / 2 - 100)], 'band', fs=SR, output='sos'), x, axis=0)


def sweep_filter(x, fc, kind='low', q=0.9, block=256):
    """Time-varying biquad: fc is an array (Hz) as long as x (mono)."""
    out = np.zeros_like(x)
    zi = np.zeros(2)
    for i in range(0, len(x), block):
        f = float(np.clip(fc[min(i + block // 2, len(fc) - 1)], 30, SR / 2 - 200))
        w = 2 * np.pi * f / SR
        alpha = np.sin(w) / (2 * q)
        c = np.cos(w)
        if kind == 'low':
            b = np.array([(1 - c) / 2, 1 - c, (1 - c) / 2])
        elif kind == 'high':
            b = np.array([(1 + c) / 2, -(1 + c), (1 + c) / 2])
        else:  # band (constant peak gain)
            b = np.array([alpha, 0, -alpha])
        a = np.array([1 + alpha, -2 * c, 1 - alpha])
        out[i:i + block], zi = ss.lfilter(b / a[0], a / a[0], x[i:i + block], zi=zi)
    return out


def noise(n, seed=0):
    return rng(seed).standard_normal(n)


def sat(x, drive=1.0):
    return np.tanh(x * drive) / np.tanh(drive)


def to_stereo(x, width=0.0, seed=0, delay_ms=0.0):
    """Mono -> stereo. width > 0 adds a decorrelated side component."""
    if x.ndim == 2:
        return x
    l = x.copy()
    r = x.copy()
    if delay_ms:
        d = int(SR * delay_ms / 1000)
        r = np.concatenate([np.zeros(d), x[:-d] if d else x])
    if width:
        side = ss.lfilter([1, 0, 0, 0, -0.6], [1], x) * width
        l, r = l + side, r - side
    return np.stack([l, r], axis=1)


def pan(x, p):
    """Constant-power pan of a mono signal, p in [-1, 1]."""
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


_ir_cache = {}


def reverb_ir(dur=2.0, decay=0.6, predelay=0.012, damp=6000, seed=5):
    key = (dur, decay, predelay, damp, seed)
    if key in _ir_cache:
        return _ir_cache[key]
    n = int(dur * SR)
    r = rng(seed)
    t = np.arange(n) / SR
    chans = []
    for c in range(2):
        x = r.standard_normal(n) * np.exp(-t / decay)
        # darker as it decays
        x = lp(x, damp) * 0.6 + lp(x, damp / 3) * 0.4
        x[: int(predelay * SR)] = 0
        chans.append(x)
    ir = np.stack(chans, axis=1)
    ir /= np.sqrt(np.sum(ir ** 2) / 2)
    _ir_cache[key] = ir
    return ir


def reverb(x, wet=0.25, **kw):
    """Convolution reverb; returns dry + wet with the tail appended."""
    x = fade(to_stereo(x), 0, 0.02)  # never cut the dry signal off abruptly
    ir = reverb_ir(**kw)
    w = np.stack([ss.fftconvolve(x[:, c], ir[:, c]) for c in range(2)], axis=1)
    out = np.zeros_like(w)
    out[: len(x)] += x
    return out + w * wet


def fade(x, fin=0.0, fout=0.0):
    x = x.copy()
    n = len(x)
    if fin:
        k = min(n, int(fin * SR))
        x[:k] *= np.linspace(0, 1, k)[:, None] if x.ndim == 2 else np.linspace(0, 1, k)
    if fout:
        k = min(n, int(fout * SR))
        x[n - k:] *= np.linspace(1, 0, k)[:, None] if x.ndim == 2 else np.linspace(1, 0, k)
    return x


def trim_silence(x, thresh_db=-70):
    a = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
    idx = np.where(a > db(thresh_db))[0]
    return x[: idx[-1] + 1] if len(idx) else x


def peak_norm(x, peak_db=-1.0):
    m = np.max(np.abs(x))
    return x * (db(peak_db) / m) if m > 0 else x


def read(path):
    x, sr = sf.read(path, always_2d=True)
    if sr != SR:
        x = ss.resample_poly(x, SR, sr, axis=0)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    return x


def write(path, x):
    sf.write(path, np.asarray(x, dtype=np.float32), SR, subtype='FLOAT')


def place(bus, x, at):
    """Add x into bus starting at time `at` (s), clipping at the bus edges."""
    i = int(round(at * SR))
    if i < 0:
        x = x[-i:]
        i = 0
    n = min(len(x), len(bus) - i)
    if n > 0:
        bus[i:i + n] += x[:n]


def repitch(x, semitones):
    """Resample to shift pitch (and length), like a sampler."""
    if not semitones:
        return x
    k = 2 ** (semitones / 12)
    n = int(len(x) / k)
    src = np.arange(n) * k
    return np.stack([np.interp(src, np.arange(len(x)), x[:, c]) for c in range(x.shape[1])], axis=1)
