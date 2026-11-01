"""Per-frame source index, reference print front and DBZ print front."""
import numpy as np, sys
from scipy.ndimage import median_filter
S = sys.argv[1]
N = 896
E = 966.0
src = np.arange(N)
for a, b in {21: 20, 30: 29, 52: 51, 60: 59, 599: 598, 608: 607, 609: 607}.items():
    src[a] = b
def load(fn):
    d = {}
    for line in open(f"{S}/track/{fn}"):
        p = line.split()
        if len(p) >= 2 and p[1] != "nan": d[int(p[0])] = float(p[1])
    return d
raw = {}
for fn in ["front_open.txt", "front_close1.txt", "front_close2.txt", "front_wide.txt", "front_fin1.txt"]:
    raw.update(load(fn))
F = np.zeros(N)
def seg(a, b):
    v = np.array([raw[src[i]] for i in range(a, b + 1)])
    v = median_filter(v, size=7, mode='nearest')
    return np.maximum.accumulate(v)
F[0:131] = seg(0, 130)
F[131:452] = np.median([raw[i] for i in range(131, 452)])
F[452:647] = seg(452, 646)
F[647:] = E
Fref = F.copy(); Fref[647:] = 1012.0
Fdbz = np.minimum(F + 3.0, E); Fdbz[647:] = E
np.save(f"{S}/comp/src.npy", src); np.save(f"{S}/comp/Fref.npy", Fref); np.save(f"{S}/comp/Fdbz.npy", Fdbz)
print("opening", F[0], F[130], "close", F[131], "wide", F[452], F[646])
print(" ".join(f"{i}:{F[i]:.0f}" for i in range(0, 131, 10)))
print(" ".join(f"{i}:{F[i]:.0f}" for i in range(452, 647, 15)))
