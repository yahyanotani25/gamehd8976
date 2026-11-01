"""Refine approximate shot boundaries to exact frames.
For each approx time t: look at frames in [t-1.2s, t+1.2s]; anchors A=frame at t-1.2s, B=frame at t+1.2s
(adjusted inward if they straddle other cuts is not handled; we print data to check).
beta(i) = <O_i - A, B - A> / ||B - A||^2  (dissolve weight estimate)."""
import sys, json, numpy as np
W = sys.argv[1]
FPS = 25
th = np.load(W + "/work/orig_thumbs.npy").astype(np.float32)
df = np.load(W + "/work/orig_diffs.npy")
st = np.load(W + "/work/orig_stats.npy")
times = [float(x) for x in sys.argv[2:]]
for t in times:
    c = int(round(t * FPS))
    a, b = c - 25, c + 25
    A, B = th[a], th[b]
    D = (B - A).ravel(); dd = float(D @ D) + 1e-6
    print(f"\n=== approx {t:.2f}s (frame {c}) |B-A|rms={np.sqrt(dd / D.size):.1f}")
    rows = []
    for i in range(a, b + 1):
        beta = float((th[i] - A).ravel() @ D / dd)
        rows.append((i, beta, float(df[i]), float(st[i, 0])))
    # print compactly: only frames where something changes
    prev = None
    for i, beta, d, y in rows:
        flag = ""
        if d > 12: flag += " CUT?"
        if prev is not None and abs(beta - prev) > 0.04: flag += " ramp"
        if flag or i in (a, c, b):
            print(f"  f{i:6d} t={i / FPS:8.2f}  beta={beta:6.3f}  diff={d:6.1f}  Y={y:6.1f}{flag}")
        prev = beta
