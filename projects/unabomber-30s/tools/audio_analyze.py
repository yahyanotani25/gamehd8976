"""Numerical listening tools for music and SFX (numpy/scipy only).

Used to fill assets/music/README.md and assets/sfx/README.md, and handy for the
lead when checking a mix. Everything is computed from the waveform:

  * loudness  - integrated LUFS (BS.1770 via pyloudnorm if installed), sample
                peak, true-peak estimate (4x oversampled), crest factor
  * envelope  - short-term (1 s window, 0.25 s hop) K-weighted-ish RMS in dB
  * sections  - quiet stretches, builds (sustained rises) and hits (sudden
                jumps / transients) located in seconds
  * tempo     - spectral-flux onset envelope autocorrelation, with a
                confidence value (low confidence = free time / no pulse)
  * key       - chroma profile matched against Krumhansl-Kessler profiles
  * spectrum  - centroid, share of energy in sub/low/mid/high bands
  * arc fit   - for music: the 30 s window whose loudness shape best matches
                the cold-open arc (see ARC below) = suggested in-point

Usage (run with -I when reading downloaded files):
    python3 -I tools/audio_analyze.py FILE [FILE ...]           # music report
    python3 -I tools/audio_analyze.py --sfx FILE [FILE ...]     # SFX: length + hit point
    python3 -I tools/audio_analyze.py --json out.json FILE ...  # machine-readable

Non-WAV inputs are decoded with ffmpeg to 48 kHz float first.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import scipy.signal as ss
import soundfile as sf

SR = 48000

# The film's 30 s arc: (start, end, relative loudness target in dB). Used for
# the "best 30 s window" search. Times from docs/BRIEF.md.
ARC = [
    (0.0, 0.2, -14.0),   # pre-roll
    (0.2, 1.4, 0.0),     # title hit on "Unabomber" (0.20 s)
    (1.4, 5.3, -8.0),    # ominous title open
    (5.3, 5.9, -10.0),
    (5.9, 10.0, -13.0),  # calm-but-uneasy wilderness
    (10.0, 10.5, -10.0),
    (10.5, 19.6, -6.0),  # city-noise contrast, faster cuts
    (19.6, 20.2, -10.0),
    (20.2, 24.5, -16.0),  # quiet drop
    (24.5, 28.6, None),  # unease rising: ramp -14 -> -3
    (28.6, 30.0, 0.0),   # riser -> suck-out -> hit + stinger
]

# Arc sections an editor cuts music to (name, start, end, what the music should do)
SECTIONS = [
    ('title_open', 0.0, 5.3, 'hit'),
    ('wilderness', 5.9, 10.0, 'calm'),
    ('city', 10.5, 19.6, 'busy'),
    ('quiet_drop', 20.2, 24.5, 'quiet'),
    ('cabin_unease', 24.9, 28.6, 'rise'),
    ('stinger', 28.6, 30.0, 'hit'),
]


# ------------------------------------------------------------------ loading
def load(path, sr=SR):
    """Return (x[n, ch] float64, sr). Decodes anything ffmpeg reads."""
    try:
        x, fsr = sf.read(path, always_2d=True)
        if fsr != sr:
            x = ss.resample_poly(x, sr, fsr, axis=0)
        return x.astype(np.float64), sr
    except Exception:
        pass
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, 'x.wav')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-ar', str(sr), '-c:a', 'pcm_f32le', out],
                       check=True)
        x, _ = sf.read(out, always_2d=True)
    return x.astype(np.float64), sr


def mono(x):
    return x.mean(axis=1) if x.ndim == 2 else x


# ------------------------------------------------------------------ loudness
def k_weight(x, sr=SR):
    """BS.1770 K-weighting (pre-filter shelf + RLB high-pass), per channel."""
    # coefficients for 48 kHz from the spec; re-derived for other rates is not needed here
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]
    a2 = [1.0, -1.99004745483398, 0.99007225036621]
    y = ss.lfilter(b1, a1, x, axis=0)
    return ss.lfilter(b2, a2, y, axis=0)


def integrated_lufs(x, sr=SR):
    try:
        import pyloudnorm as pyln
        if len(x) < sr * 0.5:
            x = np.concatenate([x, np.zeros((int(sr * 0.5) - len(x) + 1, x.shape[1]))])
        return float(pyln.Meter(sr).integrated_loudness(x))
    except Exception:
        y = k_weight(x, sr)
        return float(-0.691 + 10 * np.log10(np.mean(np.sum(y ** 2, axis=1)) + 1e-12))


def true_peak_db(x, sr=SR):
    """4x-oversampled peak, computed in 10 s chunks to keep memory low."""
    best = 0.0
    step = 10 * sr
    pad = 64
    for i in range(0, len(x), step):
        seg = x[max(0, i - pad):i + step + pad]
        best = max(best, float(np.max(np.abs(ss.resample_poly(seg, 4, 1, axis=0)))))
    return float(20 * np.log10(best + 1e-12))


def envelope_db(x, sr=SR, win=1.0, hop=0.25):
    """Short-term loudness-ish curve: K-weighted mean-square over `win` s."""
    y = k_weight(x, sr)
    p = np.sum(y ** 2, axis=1) if y.ndim == 2 else y ** 2
    w = int(win * sr)
    h = int(hop * sr)
    c = np.concatenate([[0], np.cumsum(p)])
    starts = np.arange(0, max(1, len(p) - w + 1), h)
    ms = (c[np.minimum(starts + w, len(p))] - c[starts]) / w
    t = (starts + w / 2) / sr
    return t, -0.691 + 10 * np.log10(ms + 1e-12)


def fast_env_db(x, sr=SR, win=0.010):
    """Fast peak-ish envelope (10 ms RMS) for transient / hit detection."""
    m = mono(x) if x.ndim == 2 else x
    w = max(1, int(win * sr))
    p = ss.fftconvolve(m ** 2, np.ones(w) / w, mode='same')
    return 10 * np.log10(np.maximum(p, 1e-14))


# ------------------------------------------------------------------ spectrum
def stft_mag(m, sr=SR, n_fft=4096, hop=1024):
    f, t, Z = ss.stft(m.astype(np.float32), fs=sr, nperseg=n_fft, noverlap=n_fft - hop, boundary=None,
                      padded=False)
    return f, t, np.abs(Z).astype(np.float32)


def spectrum_stats(x, sr=SR):
    m = mono(x)
    f, P = ss.welch(m, fs=sr, nperseg=4096)
    tot = P.sum() + 1e-20
    bands = {'sub<60': (0, 60), 'low60-250': (60, 250), 'mid250-2k': (250, 2000), 'hi2k-8k': (2000, 8000),
             'air>8k': (8000, sr / 2)}
    share = {k: float(P[(f >= lo) & (f < hi)].sum() / tot) for k, (lo, hi) in bands.items()}
    centroid = float((f * P).sum() / tot)
    # 95 % roll-off
    cs = np.cumsum(P) / tot
    rolloff = float(f[np.searchsorted(cs, 0.95)])
    return dict(centroid_hz=round(centroid), rolloff95_hz=round(rolloff),
                band_share={k: round(v, 3) for k, v in share.items()})


def onset_envelope(m, sr=SR, hop=512):
    """Log-spectral flux (half-wave rectified), one value per hop (on a 16 kHz copy)."""
    m = ss.resample_poly(m, 1, 3)
    sr = sr // 3
    hop = hop // 3 if hop >= 384 else hop
    n_fft = 1024
    f, t, S = stft_mag(m, sr, n_fft, hop)
    keep = f < 8000
    L = np.log1p(100 * S[keep])
    d = np.diff(L, axis=1)
    o = np.maximum(d, 0).sum(axis=0)
    o = np.concatenate([[0], o])
    o = o - ss.medfilt(o, 31)  # remove slow drift
    o = np.maximum(o, 0)
    return o, sr / hop


def tempo(m, sr=SR):
    """Return (bpm, confidence 0..1). Confidence < ~0.25 means no steady pulse."""
    o, fr = onset_envelope(m, sr)
    if len(o) < fr * 8:
        return None, 0.0
    o = o - o.mean()
    nf = 1 << int(np.ceil(np.log2(2 * len(o))))
    F = np.fft.rfft(o, nf)
    ac = np.fft.irfft(F * np.conj(F), nf)[:len(o)]
    ac /= ac[0] + 1e-12
    lags = np.arange(len(ac)) / fr
    bpm = 60 / np.maximum(lags, 1e-9)
    ok = (bpm >= 50) & (bpm <= 190)
    # mild prior towards 70-130 BPM
    prior = np.exp(-0.5 * (np.log2(np.maximum(bpm, 1) / 100) / 0.9) ** 2)
    score = np.where(ok, ac * prior, -1)
    i = int(np.argmax(score))
    # refine with parabolic interpolation
    if 0 < i < len(ac) - 1:
        a, b, c = ac[i - 1], ac[i], ac[i + 1]
        den = a - 2 * b + c
        di = 0.5 * (a - c) / den if den != 0 else 0
    else:
        di = 0
    lag = (i + di) / fr
    return round(60 / lag, 1), round(float(max(ac[i], 0)), 3)


KK_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KK_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NOTES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']


def chroma(m, sr=SR):
    m = ss.resample_poly(m, 1, 4)  # 12 kHz is plenty below 2.5 kHz
    sr = sr // 4
    f, _, S = stft_mag(m, sr, 4096, 1024)
    keep = (f > 50) & (f < 2500)
    f = f[keep]
    S = S[keep]
    pc = np.round(12 * np.log2(f / 440.0) + 9).astype(int) % 12  # 0 = C
    E = np.log1p(S / (S.max() + 1e-12) * 1000).sum(axis=1)
    c = np.zeros(12)
    np.add.at(c, pc, E)
    return c / (c.max() + 1e-12)


def key(m, sr=SR):
    c = chroma(m, sr)
    best = (-2, None)
    for i in range(12):
        for prof, mode in ((KK_MAJ, 'major'), (KK_MIN, 'minor')):
            r = np.corrcoef(c, np.roll(prof, i))[0, 1]
            if r > best[0]:
                best = (r, f'{NOTES[i]} {mode}')
    return best[1], round(float(best[0]), 2)


# ------------------------------------------------------------------ structure
def smooth(y, n):
    if n <= 1:
        return y
    k = np.hanning(n)
    k /= k.sum()
    return np.convolve(np.pad(y, (n // 2, n - 1 - n // 2), mode='edge'), k, mode='valid')


def _runs(t, mask, min_len=1.0):
    """[[start, end], ...] for runs of True in mask lasting >= min_len s."""
    out = []
    i = 0
    n = len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            if t[j] - t[i] >= min_len:
                out.append([round(float(t[i]), 1), round(float(t[j]), 1)])
            i = j + 1
        else:
            i += 1
    return out


def sections(t, e, hop=0.25):
    """Quiet stretches, builds and hits from the 1 s loudness curve."""
    es = smooth(e, 9)  # ~2 s smoothing
    active = e > (e.max() - 45)
    med = np.median(e[active]) if active.any() else np.median(e)
    out = {'median_short_term_db': round(float(med), 1), 'max_short_term_db': round(float(e.max()), 1)}
    # quiet: >= 2 s at least 6 dB under the median (but not digital silence)
    q = es < med - 6
    out['quiet'] = _runs(t, q, min_len=2.0)
    # silence: below -60
    out['silence'] = _runs(t, e < -60, min_len=0.75)
    # builds: rise of >= 6 dB over 2.5-14 s, ending at a local max
    builds = []
    n = len(es)
    i = 0
    d1 = np.gradient(es) / hop
    while i < n:
        if d1[i] > 0.6:  # dB per second
            j = i
            while j + 1 < n and d1[j + 1] > -0.3 and (es[j + 1] >= es[j] - 0.5):
                j += 1
            rise = es[j] - es[i]
            dur = t[j] - t[i]
            if rise >= 6 and 2.5 <= dur <= 20:
                builds.append([round(float(t[i]), 1), round(float(t[j]), 1), round(float(rise), 1)])
            i = j + 1
        else:
            i += 1
    out['builds'] = builds
    return out


def hits(x, sr=SR, max_hits=8, min_gap=2.0):
    """Sudden loudness jumps: 10 ms envelope vs the preceding 1 s average.

    Returns [(time_s, jump_db, level_db)] sorted by time, strongest max_hits."""
    fe = fast_env_db(x, sr)
    dec = 48  # 1 ms resolution
    fe = fe[::dec]
    fr = sr / dec
    prev = ss.lfilter([1 / fr], [1, -(1 - 1 / fr)], 10 ** (fe / 10))  # ~1 s leaky average
    prev = 10 * np.log10(np.maximum(np.concatenate([[prev[0]], prev[:-1]]), 1e-14))
    jump = fe - prev
    level = fe
    gmax = level.max()
    cand = np.where((jump > 9) & (level > gmax - 20))[0]
    picked = []
    for c in cand[np.argsort(-(jump[cand] + 0.5 * (level[cand] - gmax)))]:
        tc = c / fr
        if all(abs(tc - p[0]) >= min_gap for p in picked):
            # move to the local envelope peak within 120 ms
            w = int(0.12 * fr)
            k = c + int(np.argmax(level[c:c + w]))
            picked.append((round(k / fr, 2), round(float(jump[c]), 1), round(float(level[k] - gmax), 1)))
        if len(picked) >= max_hits:
            break
    return sorted(picked)


def arc_target(hop=0.25):
    t = np.arange(0, 30.0, hop) + hop / 2
    y = np.zeros_like(t)
    for a, b, v in ARC:
        m = (t >= a) & (t < b)
        if v is None:
            y[m] = -14 + 11 * (t[m] - a) / (b - a)
        else:
            y[m] = v
    return t, y


def arc_fit(t, e, hop=0.25):
    """Best 30 s window (start time, correlation) for the film's loudness arc."""
    _, y = arc_target(hop)
    L = len(y)
    if len(e) < L:
        return None
    yz = (y - y.mean()) / y.std()
    best = (-2, 0)
    for s in range(0, len(e) - L + 1, 2):
        w = e[s:s + L]
        if w.std() < 0.5:
            continue
        r = float(np.dot((w - w.mean()) / w.std(), yz) / L)
        if r > best[0]:
            best = (r, s)
    return dict(start_s=round(float(t[best[1]] - 0.5), 2), corr=round(best[0], 2))


def edit_map(x, t, e, sr=SR, hop=0.25):
    """For each arc section, the source region of the track that best suits it.

    calm  : lowest onset activity at moderate level (not silence)
    busy  : highest onset activity (rhythmic / dense)
    quiet : quietest non-silent stretch
    rise  : strongest sustained loudness rise over the section length
    hit   : strongest transient preceded by >= 1 s of lower level (in-point = hit time)
    Returns {section: [src_start_s, src_end_s, note]}.
    """
    m = mono(x)
    o, fr = onset_envelope(m, sr)
    to = np.arange(len(o)) / fr
    oi = np.interp(t, to, smooth(o, int(fr)))  # 1 s smoothed onset strength on the e grid
    on = oi / (np.median(oi) + 1e-9)
    med = np.median(e[e > e.max() - 45])
    out = {}
    for name, a, b, kind in SECTIONS:
        L = max(1, int(round((b - a) / hop)))
        best = None
        for s in range(0, len(e) - L, 2):
            we = e[s:s + L]
            wo = on[s:s + L]
            if we.min() < -70:
                continue
            if kind == 'calm':
                score = -wo.mean() - 0.15 * abs(we.mean() - (med - 4)) - 0.2 * we.std()
            elif kind == 'busy':
                score = wo.mean() + 0.05 * (we.mean() - med)
            elif kind == 'quiet':
                score = -(we.mean() - med) - 0.3 * we.std() if we.mean() > med - 25 else -99
            elif kind == 'rise':
                q = max(1, L // 4)
                score = we[-q:].mean() - we[:q].mean()
            else:
                continue
            if best is None or score > best[0]:
                best = (score, s)
        if kind == 'hit':
            hs = hits(x, sr, max_hits=30, min_gap=1.0)
            cand = [h for h in hs if h[0] > 1.5]
            if cand:
                h = max(cand, key=lambda h: h[1] + 0.5 * h[2])
                out[name] = [h[0], round(h[0] + (b - a), 2), f'hit at {h[0]} s (+{h[1]} dB jump)']
            continue
        if best:
            s0 = float(t[best[1]] - 0.5)
            out[name] = [round(max(s0, 0), 2), round(max(s0, 0) + (b - a), 2), f'score {best[0]:.2f}']
    return out


# ------------------------------------------------------------------ reports
def analyse_music(path):
    x, sr = load(path)
    m = mono(x)
    t, e = envelope_db(x, sr)
    rep = dict(file=os.path.basename(path), duration_s=round(len(x) / sr, 2), channels=x.shape[1],
               lufs_i=round(integrated_lufs(x, sr), 1), peak_dbfs=round(float(20 * np.log10(np.abs(x).max() + 1e-12)), 2),
               true_peak_dbtp=round(true_peak_db(x), 2))
    rep['bpm'], rep['bpm_conf'] = tempo(m, sr)
    rep['key'], rep['key_corr'] = key(m, sr)
    rep['spectrum'] = spectrum_stats(x, sr)
    rep.update(sections(t, e))
    rep['hits'] = hits(x, sr)
    rep['arc_fit'] = arc_fit(t, e)
    rep['edit_map'] = edit_map(x, t, e, sr)
    # coarse 5 s loudness map, handy for the README
    step = 5.0
    rep['loudness_map_5s'] = [round(float(np.mean(e[(t >= a) & (t < a + step)])), 1)
                              for a in np.arange(0, t[-1], step) if ((t >= a) & (t < a + step)).any()]
    return rep


def analyse_sfx(path):
    x, sr = load(path)
    m = mono(x)
    fe = fast_env_db(x, sr, win=0.005)
    pk = int(np.argmax(fe))
    a = np.abs(m)
    first = np.where(a > a.max() * 10 ** (-20 / 20))[0]
    rep = dict(file=os.path.basename(path), duration_s=round(len(x) / sr, 3), channels=x.shape[1],
               peak_t_s=round(pk / sr, 3), onset_t_s=round(first[0] / sr, 3) if len(first) else 0.0,
               peak_dbfs=round(float(20 * np.log10(a.max() + 1e-12)), 2),
               lufs_i=round(integrated_lufs(x, sr), 1))
    rep['spectrum'] = spectrum_stats(x, sr)
    # tail: time after the peak until the 10 ms envelope falls 40 dB under its maximum
    below = np.where(fe[pk:] < fe[pk] - 40)[0]
    rep['tail_s'] = round(below[0] / sr, 2) if len(below) else round((len(fe) - pk) / sr, 2)
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--sfx', action='store_true')
    ap.add_argument('--json')
    a = ap.parse_args()
    reps = []
    for f in a.files:
        r = analyse_sfx(f) if a.sfx else analyse_music(f)
        reps.append(r)
        if a.sfx:
            print(f"{r['file']:34s} {r['duration_s']:7.2f}s  peak@{r['peak_t_s']:6.3f}s  onset@{r['onset_t_s']:6.3f}s  "
                  f"{r['lufs_i']:6.1f} LUFS  pk {r['peak_dbfs']:6.2f}  cent {r['spectrum']['centroid_hz']} Hz")
        else:
            print(json.dumps(r))
        sys.stdout.flush()
    if a.json:
        with open(a.json, 'w') as fh:
            json.dump(reps, fh, indent=1)


if __name__ == '__main__':
    main()
