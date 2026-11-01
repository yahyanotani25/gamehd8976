import numpy as np, sys
def homline(l):
    x1,y1,x2,y2 = l
    return np.cross([x1,y1,1.0],[x2,y2,1.0])
def vp_ls(lines):
    # least squares VP: minimize sum (l . v)^2 with normalized lines, weighted by length
    A = []
    for l in lines:
        h = homline(l); h = h / np.linalg.norm(h[:2])
        w = np.hypot(l[2]-l[0], l[3]-l[1])
        A.append(h * np.sqrt(w))
    A = np.array(A)
    _,_,Vt = np.linalg.svd(A)
    v = Vt[-1]
    return v
def ransac_vp(lines, iters=3000, thr_deg=0.6, seed=0):
    rng = np.random.default_rng(seed)
    best = None; bestn = -1
    for _ in range(iters):
        i, j = rng.choice(len(lines), 2, replace=False)
        v = np.cross(homline(lines[i]), homline(lines[j]))
        if abs(v[2]) < 1e-12: v = v
        inl = []
        for k, l in enumerate(lines):
            mid = np.array([(l[0]+l[2])/2, (l[1]+l[3])/2, 1.0])
            d = np.array([l[2]-l[0], l[3]-l[1]])
            # direction from mid to vp
            if abs(v[2]) > 1e-9:
                tv = v[:2]/v[2] - mid[:2]
            else:
                tv = v[:2]
            ang = np.degrees(np.arccos(min(1, abs(np.dot(tv, d)) / (np.linalg.norm(tv)*np.linalg.norm(d)+1e-12))))
            if ang < thr_deg: inl.append(k)
        w = sum(np.hypot(lines[k][2]-lines[k][0], lines[k][3]-lines[k][1]) for k in inl)
        if w > bestn: bestn = w; best = inl
    v = vp_ls([lines[k] for k in best])
    return v, best
