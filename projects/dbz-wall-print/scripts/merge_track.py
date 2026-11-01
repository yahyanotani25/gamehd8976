import json, numpy as np, sys, glob
S = sys.argv[1]
H = np.full((896, 3, 3), np.nan); N = np.zeros(896)
for f in sorted(glob.glob(f"{S}/track/trk_*.json")):
    d = json.load(open(f))
    for k, (h, n) in d.items():
        k = int(k)
        if n > N[k]: H[k] = np.array(h); N[k] = n
missing = [i for i in range(896) if np.isnan(H[i, 0, 0])]
print("missing", missing[:20], len(missing))
np.save(f"{S}/track/H_all.npy", H); np.save(f"{S}/track/N_all.npy", N)
# junction consistency: project W point grid at frames 640/641
def proj(Hm, p):
    q = np.c_[p, np.ones(len(p))] @ Hm.T; return q[:, :2] / q[:, 2:]
P = np.array([[300, 400], [700, 400], [300, 900], [700, 900]], float)
for a in [451, 452, 640, 641]:
    if not np.isnan(H[a, 0, 0]): print(a, proj(H[a], P).round(1).tolist())
