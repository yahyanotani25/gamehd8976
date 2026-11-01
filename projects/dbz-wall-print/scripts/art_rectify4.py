import numpy as np, cv2, sys
S = sys.argv[1]
f = 600.0
vp = np.array([1365.0, 803.0, 1.0]); c = np.array([369.0, 799.0])
top = lambda x: 560 + 0.18 * (x - 15)
bot = lambda x: 964 - 0.1194 * (x - 18)
Q = np.array([[16, top(16)], [636, top(636)], [636, bot(636)], [16, bot(16)]])
K = np.array([[f, 0, c[0]], [0, f, c[1]], [0, 0, 1.0]]); Ki = np.linalg.inv(K)
dh = Ki @ vp; dh /= np.linalg.norm(dh)
dv = np.array([0, 1.0, 0]); dv -= dv.dot(dh) * dh; dv /= np.linalg.norm(dv)
Hi2w = np.linalg.inv(K @ np.column_stack([dh, dv, [0, 0, 1.0]]))
q = np.c_[Q, np.ones(4)] @ Hi2w.T; q = q[:, :2] / q[:, 2:]
aspect = np.linalg.norm(q[1] - q[0]) / np.linalg.norm(q[3] - q[0])
sc = 4.0; off = np.array([0, 545.0])
Hout = 2400; Wout = int(round(Hout * aspect))
dst = np.float32([[0, 0], [Wout, 0], [Wout, Hout], [0, Hout]])
M = cv2.getPerspectiveTransform(np.float32((Q - off) * sc), dst)
im = cv2.imread(f"{S}/art/src_crop_x4.png")
r = cv2.warpPerspective(im, M, (Wout, Hout), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
cv2.imwrite(f"{S}/art/mural_rect_x4.png", r)
cv2.imwrite(f"{S}/art/mural_rect_x4_small.jpg", cv2.resize(r, (Wout // 3, Hout // 3), interpolation=cv2.INTER_AREA))
print("aspect", aspect, "size", Wout, Hout)
