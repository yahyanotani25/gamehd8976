import numpy as np
def shear_mat(k=np.tan(np.radians(1.2)), yref=660.0):
    return np.array([[1, -k, k*yref], [0, 1, 0], [0, 0, 1.0]])
def apply(H, pts):
    p = np.c_[pts, np.ones(len(pts))] @ H.T
    return p[:, :2] / p[:, 2:3]
def local_scale(Hw2f, xy_frame):
    """frame px per wall unit near a frame point"""
    Hf2w = np.linalg.inv(Hw2f)
    w0 = apply(Hf2w, np.array([xy_frame]))[0]
    a = apply(Hw2f, np.array([w0, w0 + [1, 0], w0 + [0, 1]]))
    return np.linalg.norm(a[1]-a[0]), np.linalg.norm(a[2]-a[0])
