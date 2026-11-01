"""Find where each phone recording of the laptop screen sits in the original video.

Approach: log-spectrogram band energies (speech+music) at 100 frames/s, per-band
normalised; slide 2.5 s windows of each clip over the full original with FFT
cross-correlation and keep the best lag per window. Consecutive windows that
agree on the same offset form a playback run; scrubs/pauses show up as offset
jumps.
"""
import sys, json, glob, os
import numpy as np
from scipy.io import wavfile
from scipy.signal import stft, fftconvolve

SR = 16000
HOP = 160  # 10 ms
def feats(x):
    x = x.astype(np.float32) / 32768.0
    f, t, Z = stft(x, fs=SR, nperseg=1024, noverlap=1024 - HOP, boundary=None, padded=False)
    S = np.abs(Z) ** 2
    # 32 log-spaced bands between 150 Hz and 5 kHz (phone mic + laptop speakers)
    edges = np.geomspace(150, 5000, 33)
    B = np.stack([S[(f >= edges[i]) & (f < edges[i + 1])].sum(0) for i in range(32)])
    B = np.log(B + 1e-9)
    # temporal derivative-ish whitening: remove slow trend per band (room EQ invariance)
    k = 50
    ker = np.ones(k) / k
    trend = np.stack([np.convolve(b, ker, mode="same") for b in B])
    D = B - trend
    D = (D - D.mean(1, keepdims=True)) / (D.std(1, keepdims=True) + 1e-6)
    return D  # bands x frames

def best_lag(Q, R, Rsq):
    # normalised cross-correlation summed over bands
    n = Q.shape[1]
    num = np.zeros(R.shape[1] - n + 1)
    for b in range(Q.shape[0]):
        q = Q[b] - Q[b].mean()
        num += fftconvolve(R[b], q[::-1], mode="valid")
    # local energy of R over window, per band summed
    ones = np.ones(n)
    den = np.sqrt(np.maximum(fftconvolve(Rsq, ones, mode="valid"), 1e-9)) * np.sqrt((Q - Q.mean(1, keepdims=True)).__pow__(2).sum())
    c = num / den
    i = int(np.argmax(c))
    srt = np.sort(c)
    return i, float(c[i]), float(np.median(c)), float(np.std(c))

if __name__ == "__main__":
    W = sys.argv[1]
    sr, orig = wavfile.read(os.path.join(W, "work/audio/original_16k.wav"))
    R = feats(orig)
    # per-frame local mean removal approximated: use centred R; sum of squares across bands
    Rc = R - R.mean(1, keepdims=True)
    Rsq = (Rc ** 2).sum(0)
    out = {}
    for path in sorted(glob.glob(os.path.join(W, "work/audio/clip_*.wav"))):
        name = os.path.basename(path)[:-4]
        sr, x = wavfile.read(path)
        Q = feats(x)
        n = Q.shape[1]
        win, step = 250, 50  # 2.5 s windows every 0.5 s
        rows = []
        for s in range(0, max(1, n - win + 1), step):
            q = Q[:, s:s + win]
            i, c, med, sd = best_lag(q, Rc, Rsq)
            z = (c - med) / (sd + 1e-9)
            clip_t = s / 100.0
            orig_t = i / 100.0
            rows.append(dict(clip_t=clip_t, orig_t=orig_t, offset=round(orig_t - clip_t, 2), score=round(c, 3), z=round(z, 1)))
        out[name] = rows
        print(name, "n_windows", len(rows))
        for r in rows:
            print(f"   clip {r['clip_t']:6.2f}s -> orig {r['orig_t']:7.2f}s  off {r['offset']:7.2f}  score {r['score']:.3f}  z {r['z']:5.1f}")
        sys.stdout.flush()
    json.dump(out, open(os.path.join(W, "work/audio_match.json"), "w"), indent=1)
