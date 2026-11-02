"""Planar tracking of the wall in reference 1.

Every frame is matched against a single wall texture ("master", in canvas
coordinates) re-projected into the predicted view, so there is no drift and
strong perspective in the close-ups still matches.  SIFT + MAGSAC gives the
homography, ECC refines it to sub-pixel.

usage: python track.py master0 | seed | all | master1
"""
import sys
import numpy as np
import cv2
from common import *

cv2.setNumThreads(1)
SIFT = cv2.SIFT_create(nfeatures=6000, contrastThreshold=0.015)
BF = cv2.BFMatcher(cv2.NORM_L2)


def feats(img, mask):
    return SIFT.detectAndCompute(img, mask)


def match_H(fa, fb, ratio=0.78, th=3.0):
    """H mapping image a -> image b from precomputed (kp, desc)."""
    ka, da = fa
    kb, db = fb
    if da is None or db is None or len(ka) < 12 or len(kb) < 12:
        return None, 0
    m = BF.knnMatch(da, db, k=2)
    good = [p[0] for p in m if len(p) == 2 and p[0].distance < ratio * p[1].distance]
    if len(good) < 15:
        return None, len(good)
    pa = np.float32([ka[g.queryIdx].pt for g in good])
    pb = np.float32([kb[g.trainIdx].pt for g in good])
    H, inl = cv2.findHomography(pa, pb, cv2.USAC_MAGSAC, th, maxIters=10000,
                                confidence=0.9995)
    if H is None:
        return None, 0
    return H, int(inl.sum())


def wall_mask(H, grow=0, v0=0.0, v1=WALL_H):
    """Frame-space mask of the wall band (canvas v in [v0, v1]).

    Rasterised with warpPerspective from a coarse canvas so views with strong
    perspective (horizon near the frame) stay correct.
    """
    s = 1 / 8
    cm = np.zeros((int(CANVAS_H * s), int(CANVAS_W * s)), np.uint8)
    cm[int((CV + v0) * s):int((CV + v1) * s), :] = 1
    Hs = H @ np.diag([1 / s, 1 / s, 1.0])
    wm = cv2.warpPerspective(cm, Hs, (FW, FH), flags=cv2.INTER_NEAREST)
    if grow:
        wm = cv2.dilate(wm, np.ones((grow, grow), np.uint8))
    return wm


def frame_mask(fr, H_pred=None):
    m = 1 - dark_mask(fr, grow=15)
    if H_pred is not None:
        m &= wall_mask(H_pred, grow=41)
    return m * 255


def ecc_refine(tmpl, tmask, g, iters=60):
    W = np.eye(3, dtype=np.float32)
    try:
        crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, iters, 1e-5)
        # downscale x0.5 for speed/robustness, then scale the warp back up
        s = 0.5
        t2 = cv2.resize(tmpl, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        g2 = cv2.resize(g, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        m2 = cv2.resize(tmask, None, fx=s, fy=s, interpolation=cv2.INTER_NEAREST)
        _, W2 = cv2.findTransformECC(t2, g2, W.copy(), cv2.MOTION_HOMOGRAPHY, crit,
                                     m2, 5)
        S = np.diag([s, s, 1]).astype(np.float64)
        W = np.linalg.inv(S) @ W2.astype(np.float64) @ S
        # ECC returns warp from template coords to input coords
        if np.abs(W - np.eye(3)).max() > 0.2:
            return np.eye(3)
        return W
    except cv2.error:
        return np.eye(3)


def sane(H):
    """Wall must stay a sensible, non-flipped quad on screen."""
    if H is None or not np.all(np.isfinite(H)):
        return False
    q = warp_pts(H, wall_poly_canvas(0, 1500))
    if not np.all(np.isfinite(q)) or np.abs(q).max() > 20000:
        return False
    a = cv2.contourArea(q.astype(np.float32), oriented=True)
    return a > 2e4


class Tracker:
    def __init__(self, master, mvalid):
        self.master = master
        self.mvalid = mvalid

    def view(self, H):
        t = cv2.warpPerspective(self.master, H, (FW, FH), flags=cv2.INTER_LINEAR)
        v = cv2.warpPerspective(self.mvalid, H, (FW, FH), flags=cv2.INTER_NEAREST)
        v = cv2.erode(v, np.ones((9, 9), np.uint8))
        return t, v

    def step(self, i, H_pred, use_ecc=True):
        fr = read_frame(i)
        g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        fm = frame_mask(fr, H_pred)
        H = H_pred
        n_tot = 0
        for it in range(2):
            t, v = self.view(H)
            D, n = match_H(feats(t, v), feats(g, fm), th=3.0 if it == 0 else 2.0)
            n_tot = n
            if D is None or n < 20:
                break
            H = D @ H
        if use_ecc:
            t, v = self.view(H)
            em = (v > 0) & (fm > 0)
            em = cv2.erode(em.astype(np.uint8), np.ones((7, 7), np.uint8)) * 255
            if em.sum() / 255 > 20000:
                W = ecc_refine(t, em, g)
                H = W @ H
        return H / H[2, 2], n_tot

    def run(self, seq, H0, log=""):
        out, ninl = {}, {}
        H = H0
        Hs = []
        for i in seq:
            pred = H
            if len(Hs) >= 2:      # constant-velocity prediction
                pred = Hs[-1] @ np.linalg.inv(Hs[-2]) @ Hs[-1]
                pred /= pred[2, 2]
            Hn, n = self.step(i, pred)
            if n < 30 or not sane(Hn):    # retry from the last good homography
                Hn, n = self.step(i, H)
            if n < 30 or not sane(Hn):    # re-detect against the whole master
                best = (None, 0)
                for sc in (0.5, 0.7, 1.0):
                    Hd, nd = direct_seed(i, self.master, self.mvalid, sc)
                    if Hd is not None and nd > best[1] and sane(Hd):
                        best = (Hd, nd)
                if best[0] is not None and best[1] >= 40:
                    Hn, n = self.step(i, best[0])
                    print(f"{log} frame {i}: re-detected ({best[1]})", flush=True)
            if n < 30 or not sane(Hn):
                Hn, n = H, 0              # keep last good; flagged by n=0
            out[i], ninl[i] = Hn, n
            H = Hn
            Hs.append(Hn)
            print(f"{log} frame {i}: inliers {n}", flush=True)
        return out, ninl


def direct_seed(i, master, mvalid, scale=0.5):
    """Match a frame against the whole master (no prior)."""
    fr = read_frame(i)
    g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
    fm = frame_mask(fr)
    ms = cv2.resize(master, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    vs = cv2.resize(mvalid, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    D, n = match_H(feats(ms, vs), feats(g, fm), ratio=0.8, th=4.0)
    if D is None:
        return None, n
    S = np.diag([scale, scale, 1.0])
    return D @ S, n


def build_master(tracks, frames, res_weight=True):
    """Weighted mosaic of frames in canvas space; weight ~ resolution^2."""
    acc = np.zeros((CANVAS_H, CANVAS_W, 3), np.float64)
    wsum = np.zeros((CANVAS_H, CANVAS_W), np.float64)
    for i in frames:
        H = tracks[i]
        fr = read_frame(i).astype(np.float32)
        ok = (1 - dark_mask(read_frame(i), grow=21)).astype(np.float32)
        Hi = np.linalg.inv(H)
        w = cv2.warpPerspective(fr, Hi, (CANVAS_W, CANVAS_H), flags=cv2.INTER_LINEAR)
        m = cv2.warpPerspective(ok, Hi, (CANVAS_W, CANVAS_H), flags=cv2.INTER_NEAREST)
        if res_weight:
            # frame px per canvas px at each canvas point = sqrt(|det J|)
            ys, xs = np.mgrid[0:CANVAS_H:16, 0:CANVAS_W:16].astype(np.float64)
            p = np.stack([xs.ravel(), ys.ravel(), np.ones(xs.size)])
            q = H @ p
            # det of Jacobian of projective map = det(H) / w^3
            det = np.abs(np.linalg.det(H)) / np.abs(q[2]) ** 3
            det = det.reshape(xs.shape).astype(np.float32)
            det = cv2.resize(det, (CANVAS_W, CANVAS_H), interpolation=cv2.INTER_LINEAR)
            m = m * det ** 2
        acc += w * m[..., None]
        wsum += m
    master = (acc / np.maximum(wsum, 1e-9)[..., None]).astype(np.uint8)
    valid = (wsum > 1e-6).astype(np.uint8) * 255
    return master, valid


def save_tracks(tr, name):
    save_json({str(k): v.tolist() for k, v in tr.items()}, name)


def load_tr(name):
    return {int(k): np.array(v) for k, v in load_json(name).items()}


if __name__ == "__main__":
    stage = sys.argv[1]
    if stage == "master0":
        H560 = cv2.getPerspectiveTransform(ref_quad_canvas(), REF_QUAD_IMG)
        fr = read_frame(REF_FRAME)
        master, valid = build_master({REF_FRAME: H560}, [REF_FRAME], res_weight=False)
        cv2.imwrite(os.path.join(WORK, "master0.png"), master)
        cv2.imwrite(os.path.join(WORK, "master0_valid.png"), valid)
        save_tracks({REF_FRAME: H560}, "H560.json")
        print("ok")
    elif stage == "trackE":
        # track shot E against master0, from the reference frame outwards
        master = cv2.imread(os.path.join(WORK, "master0.png"), 0)
        valid = cv2.imread(os.path.join(WORK, "master0_valid.png"), 0)
        H560 = load_tr("H560.json")[REF_FRAME]
        T = Tracker(master, valid)
        a, b = SHOTS["E"]
        fwd, _ = T.run(list(range(REF_FRAME, b + 1)), H560, "E+")
        bwd, _ = T.run(list(range(REF_FRAME, a - 1, -1)), H560, "E-")
        fwd.update(bwd)
        save_tracks(fwd, "tracks_E0.json")
    elif stage == "seed":
        # direct seeding test for given frames against a master
        mname = sys.argv[2]
        master = cv2.imread(os.path.join(WORK, mname + ".png"), 0)
        valid = cv2.imread(os.path.join(WORK, mname + "_valid.png"), 0)
        res = {}
        for i in map(int, sys.argv[3:]):
            best = (None, 0)
            for sc in (0.35, 0.5, 0.7, 1.0):
                H, n = direct_seed(i, master, valid, sc)
                print(i, sc, n, flush=True)
                if H is not None and n > best[1]:
                    best = (H, n)
            if best[0] is not None:
                res[i] = best[0]
        save_tracks(res, f"seeds_{mname}.json")
    elif stage == "trackshot":
        # trackshot <master> <shot> <seedframe> <seedsfile>
        mname, shot, seed, seedfile = sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
        master = cv2.imread(os.path.join(WORK, mname + ".png"), 0)
        valid = cv2.imread(os.path.join(WORK, mname + "_valid.png"), 0)
        H0 = load_tr(seedfile)[seed]
        T = Tracker(master, valid)
        a, b = SHOTS[shot]
        fwd, n1 = T.run(list(range(seed, b + 1)), H0, shot + "+")
        bwd, n2 = T.run(list(range(seed, a - 1, -1)), fwd[seed], shot + "-")
        fwd.update(bwd)
        n1.update(n2)
        save_tracks(fwd, f"tracks_{shot}_{mname}.json")
        save_json({str(k): v for k, v in n1.items()}, f"inliers_{shot}_{mname}.json")
    elif stage == "buildmaster":
        # buildmaster <outname> <tracksfile:step> ...
        out = sys.argv[2]
        tr, frames = {}, []
        for spec in sys.argv[3:]:
            fn, step = spec.split(":")
            t = load_tr(fn)
            tr.update(t)
            frames += sorted(t)[::int(step)]
        master, valid = build_master(tr, frames)
        cv2.imwrite(os.path.join(WORK, out + "_color.png"), master)
        cv2.imwrite(os.path.join(WORK, out + ".png"), cv2.cvtColor(master, cv2.COLOR_BGR2GRAY))
        cv2.imwrite(os.path.join(WORK, out + "_valid.png"), valid)
        print("frames used", len(frames))
    elif stage == "trackrange":
        # trackrange <master> <seedsfile> <seed> <a> <b> <outname>
        mname, seedfile, seed, a, b, outname = sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), sys.argv[7]
        master = cv2.imread(os.path.join(WORK, mname + ".png"), 0)
        valid = cv2.imread(os.path.join(WORK, mname + "_valid.png"), 0)
        H0 = load_tr(seedfile)[seed]
        T = Tracker(master, valid)
        out, nn = {}, {}
        if b >= seed:
            o, n = T.run(list(range(seed, b + 1)), H0, outname + "+")
            out.update(o); nn.update(n)
        if a < seed:
            o, n = T.run(list(range(seed, a - 1, -1)), out.get(seed, H0), outname + "-")
            out.update(o); nn.update(n)
        save_tracks(out, f"tracks_{outname}.json")
        save_json({str(k): v for k, v in nn.items()}, f"inliers_{outname}.json")
