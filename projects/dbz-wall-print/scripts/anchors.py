import sys, numpy as np
S = sys.argv[1]; sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from wallspace import *
R1 = np.load(f"{S}/Hi2w_0001.npy")          # frame0 image -> rect1
Hf0_to_W = shear_mat() @ R1
HW = {0: np.linalg.inv(Hf0_to_W)}
HW[559] = np.load(f"{S}/H_0_559.npy") @ HW[0]
HW[799] = np.load(f"{S}/H_559_799.npy") @ HW[559]
HW[451] = np.load(f"{S}/H_559_451.npy") @ HW[559]
HW[895] = np.load(f"{S}/H_799_895.npy") @ HW[799]
for k, H in HW.items():
    np.save(f"{S}/track/anchor_{k}.npy", H)
    sx, sy = local_scale(H, (360, 640))
    c = apply(np.linalg.inv(H), np.array([[0,0],[720,0],[720,1280],[0,1280],[360,640]]))
    print(k, "px/W at center: %.2f %.2f" % (sx, sy), " frame corners in W:", c.round(0).tolist())
