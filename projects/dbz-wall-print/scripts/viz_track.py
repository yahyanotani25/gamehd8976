import sys, numpy as np, cv2
S = sys.argv[1]; frames = [int(x) for x in sys.argv[2].split(",")]; out = sys.argv[3]
H = np.load(f"{S}/track/H_all.npy")
Wc2W = np.load(f"{S}/track/Wc2W.npy"); plate = cv2.imread(f"{S}/track/plate2.png")
tiles = []
for i in frames:
    im = cv2.imread(f"{S}/ref_full/{i+1:04d}.png")
    Hc = H[i] @ Wc2W
    pv = cv2.warpPerspective(plate, Hc, (720, 1280))
    blend = im.copy()
    # left half: frame; right half: 50/50 blend with plate (ghosting shows misalignment)
    m = pv.sum(2) > 0
    blend[m] = (0.5 * im[m] + 0.5 * pv[m]).astype(np.uint8)
    def P(x, y):
        q = H[i] @ np.array([x, y, 1.0]); return (int(q[0] / q[2]), int(q[1] / q[2]))
    for x in range(-200, 1401, 100):
        cv2.line(blend, P(x, 200), P(x, 1124), (0, 255, 0), 1)
    for y in (200, 1124):
        cv2.line(blend, P(-200, y), P(1400, y), (0, 0, 255), 2)
    cv2.putText(blend, str(i), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
    tiles.append(cv2.resize(blend, (288, 512)))
rows = [np.hstack(tiles[k:k + 8]) for k in range(0, len(tiles), 8)]
w = max(r.shape[1] for r in rows)
rows = [np.pad(r, ((0, 0), (0, w - r.shape[1]), (0, 0))) for r in rows]
cv2.imwrite(out, np.vstack(rows))
