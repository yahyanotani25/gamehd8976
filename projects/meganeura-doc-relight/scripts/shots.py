import sys, json, numpy as np
W = sys.argv[1]
st = np.load(W + "/work/orig_stats.npy"); df = np.load(W + "/work/orig_diffs.npy")
N = len(df); FPS = 25.0
# adaptive hard-cut detection
cuts = [0]
for i in range(1, N):
    lo, hi = max(1, i - 12), min(N, i + 13)
    neigh = np.concatenate([df[lo:i], df[i + 1:hi]])
    base = np.median(neigh) if len(neigh) else 0
    if df[i] > 14 and df[i] > 3.0 * base + 6 and df[i] == df[max(1, i - 2):min(N, i + 3)].max():
        if i - cuts[-1] >= 4:
            cuts.append(i)
cuts.append(N)
shots = []
for a, b in zip(cuts[:-1], cuts[1:]):
    s = st[a:b]
    shots.append(dict(a=a, b=b, t0=a / FPS, t1=b / FPS, dur=(b - a) / FPS, Y=float(s[:, 0].mean()),
                      Ymin=float(s[:, 0].min()), Ymax=float(s[:, 0].max()), p90=float(s[:, 3].mean()),
                      p10=float(s[:, 1].mean()), sat=float(s[:, 4].mean())))
json.dump(shots, open(W + "/work/shots.json", "w"), indent=1)
print("n shots", len(shots), "median dur", np.median([s["dur"] for s in shots]))
print("global mean luma", st[:, 0].mean())
