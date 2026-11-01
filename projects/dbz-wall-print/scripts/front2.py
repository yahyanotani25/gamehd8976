import sys, numpy as np, cv2
S = sys.argv[1]; frames = list(range(int(sys.argv[2]), int(sys.argv[3]) + 1)); dbg = len(sys.argv) > 4
H = np.load(f"{S}/track/H_all.npy"); Wc2W = np.load(f"{S}/track/Wc2W.npy")
plate = cv2.imread(f"{S}/track/plate2.png"); pv = cv2.imread(f"{S}/track/plate2_valid.png", 0)
X0, Y0, X1, Y1 = 0, 380, 1000, 980
T = np.array([[1, 0, X0], [0, 1, Y0], [0, 0, 1.0]])
P = cv2.warpPerspective(plate, np.linalg.inv(T) @ Wc2W, (X1 - X0, Y1 - Y0), flags=cv2.INTER_AREA)
Pv = cv2.warpPerspective(pv, np.linalg.inv(T) @ Wc2W, (X1 - X0, Y1 - Y0), flags=cv2.INTER_NEAREST) > 0
Plab = cv2.cvtColor(P, cv2.COLOR_BGR2LAB).astype(np.float32)
Pab = cv2.GaussianBlur(Plab[..., 1:], (0, 0), 1.5)
res = []
for i in frames:
    im = cv2.imread(f"{S}/ref_full/{i+1:04d}.png")
    w = cv2.warpPerspective(im, np.linalg.inv(H[i] @ T), (X1 - X0, Y1 - Y0), flags=cv2.INTER_AREA)
    v = cv2.warpPerspective(np.full(im.shape[:2], 255, np.uint8), np.linalg.inv(H[i] @ T), (X1 - X0, Y1 - Y0), flags=cv2.INTER_NEAREST) > 0
    v = cv2.erode(v.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    lab = cv2.cvtColor(w, cv2.COLOR_BGR2LAB).astype(np.float32)
    ab = cv2.GaussianBlur(lab[..., 1:], (0, 0), 1.5)
    L = lab[..., 0]
    fg = L < 90
    # wall colour: bright, near-neutral pixels in frame -> robust median of the brightest 20%
    cand = v & ~fg & (L > np.percentile(L[v], 70))
    wall_ab = np.median(ab[cand], axis=0)
    d_pw = np.linalg.norm(Pab - wall_ab, axis=2)
    d_fp = np.linalg.norm(ab - Pab, axis=2)
    d_fw = np.linalg.norm(ab - wall_ab, axis=2)
    valid = Pv & v & ~fg & (d_pw > 12)
    printed = valid & (d_fp < 0.5 * d_fw)
    blank = valid & (d_fw < 0.4 * d_fp)
    cp = printed.sum(0).astype(float); cb = blank.sum(0).astype(float); tot = cp + cb
    frac = np.where(tot > 12, cp / np.maximum(tot, 1), np.nan)
    fs = np.copy(frac)
    xs = np.arange(X0, X1)
    front = np.nan; run = 0
    for j in range(len(xs)):
        if np.isnan(fs[j]): continue
        if fs[j] > 0.5: front = xs[j]; run = 0
        elif fs[j] < 0.3:
            run += 1
            if run > 25 and not np.isnan(front): break
    vis = xs[v.any(0)]
    res.append((i, front, vis.min(), vis.max()))
    print(i, front, vis.min(), vis.max(), "wall_ab", wall_ab.round(1), flush=True)
    if dbg:
        vis_img = w.copy()
        vis_img[printed] = (0.5 * vis_img[printed] + [0, 128, 0]).astype(np.uint8)
        vis_img[blank] = (0.5 * vis_img[blank] + [0, 0, 128]).astype(np.uint8)
        if not np.isnan(front): cv2.line(vis_img, (int(front - X0), 0), (int(front - X0), Y1 - Y0), (255, 0, 255), 3)
        cv2.imwrite(f"{S}/dbg_front_{i}.jpg", cv2.resize(vis_img, ((X1 - X0) // 2, (Y1 - Y0) // 2)))
np.save(f"{S}/track/front_{frames[0]}_{frames[-1]}.npy", np.array(res, float))
