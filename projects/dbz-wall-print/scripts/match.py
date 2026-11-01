import cv2, numpy as np
SIFT = cv2.SIFT_create(nfeatures=8000, contrastThreshold=0.01)
def load(S, i):
    return cv2.imread(f"{S}/ref_full/{i+1:04d}.png")
def wallmask(im):
    """rough mask of pixels likely on the wall art/wall: not too dark, not floor-ish later refined"""
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    v = hsv[...,2]
    m = (v > 90).astype(np.uint8) * 255
    m = cv2.erode(m, np.ones((9,9), np.uint8))
    return m
def feats(im, mask=None):
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    kp, des = SIFT.detectAndCompute(g, mask)
    pts = np.array([k.pt for k in kp], np.float32)
    return pts, des
def match(fa, fb, ratio=0.75):
    pa, da = fa; pb, db = fb
    if da is None or db is None or len(da) < 4 or len(db) < 4: return None, None
    bf = cv2.BFMatcher(cv2.NORM_L2)
    m = bf.knnMatch(da, db, k=2)
    good = [x[0] for x in m if len(x) == 2 and x[0].distance < ratio * x[1].distance]
    A = np.float32([pa[g.queryIdx] for g in good]); B = np.float32([pb[g.trainIdx] for g in good])
    return A, B
def homog(A, B, thr=3.0):
    if A is None or len(A) < 8: return None, 0, None
    H, inl = cv2.findHomography(A, B, cv2.USAC_MAGSAC, thr, maxIters=20000, confidence=0.9999)
    if H is None: return None, 0, None
    return H, int(inl.sum()), inl.ravel().astype(bool)
