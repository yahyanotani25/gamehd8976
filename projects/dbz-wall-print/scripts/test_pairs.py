import sys, numpy as np, cv2
S = sys.argv[1]; sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from match import *
pairs = [(0, 559), (559, 799), (0, 99), (559, 451), (799, 895), (799, 680)]
F = {}
for a, b in pairs:
    for i in (a, b):
        if i not in F:
            im = load(S, i); F[i] = feats(im, wallmask(im))
    A, B = match(F[a], F[b])
    H, n, inl = homog(A, B)
    print(a, b, "matches", 0 if A is None else len(A), "inliers", n)
    if H is not None:
        np.save(f"{S}/H_{a}_{b}.npy", H)
