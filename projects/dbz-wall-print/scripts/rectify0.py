import cv2, numpy as np, sys, json
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from vplib import ransac_vp, vp_ls
S = sys.argv[1]
im = cv2.imread(S + "/ref_full/0001.png"); H0, W0 = im.shape[:2]
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
L = lsd.detect(g)[0].reshape(-1, 4)
ln = np.hypot(L[:,2]-L[:,0], L[:,3]-L[:,1]); L = L[ln > 50]
ang = np.degrees(np.arctan2(L[:,3]-L[:,1], L[:,2]-L[:,0])) % 180
hor = L[((ang < 25) | (ang > 155))]
ver = L[(ang > 80) & (ang < 100)]
vh, ih = ransac_vp(list(hor), thr_deg=0.5)
vv, iv = ransac_vp(list(ver), thr_deg=0.3)
vh = vh / vh[2]; vv = vv / vv[2]
print("VPh", vh[:2], len(ih), "/", len(hor)); print("VPv", vv[:2], len(iv), "/", len(ver))
f = float(sys.argv[2]) if len(sys.argv) > 2 else 1024.0
K = np.array([[f,0,W0/2],[0,f,H0/2],[0,0,1.0]]); Ki = np.linalg.inv(K)
dh = Ki @ vh; dh /= np.linalg.norm(dh)
if dh[0] < 0: dh = -dh
dv = Ki @ vv; dv /= np.linalg.norm(dv)
if dv[1] < 0: dv = -dv
dv = dv - np.dot(dv, dh) * dh; dv /= np.linalg.norm(dv)
n = np.cross(dh, dv)
print("dh", dh, "dv", dv, "n", n, "oblique deg", np.degrees(np.arccos(abs(n[2]))))
O = np.array([0, 0, 1.0])
Hw2i = K @ np.column_stack([dh, dv, O])   # wall (u,v,1) -> image
# wall units: u,v in 'depth-1' units; scale so 1 wall px ~ 1 image px at image center: multiply by f
Sc = np.diag([1/f, 1/f, 1.0])
Hw2i = Hw2i @ Sc
Hi2w = np.linalg.inv(Hw2i)
# where does the image map in wall space?
corners = np.array([[0,0,1],[W0,0,1],[W0,H0,1],[0,H0,1]], float).T
wc = Hi2w @ corners; wc = wc[:2] / wc[2]
print("image corners in wall:", wc.T.round(1))
mn = wc.min(1) - 50; mx = wc.max(1) + 50
T = np.array([[1,0,-mn[0]],[0,1,-mn[1]],[0,0,1.0]])
size = (int(mx[0]-mn[0]), int(mx[1]-mn[1]))
rect = cv2.warpPerspective(im, T @ Hi2w, size, flags=cv2.INTER_LINEAR)
cv2.imwrite(S + "/rect_0001.png", rect)
np.save(S + "/Hi2w_0001.npy", T @ Hi2w)
print("rect size", size)
