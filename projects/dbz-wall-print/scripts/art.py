"""Turn the client's photo into a flat, print-ready mural.

The client's image is a phone screenshot of a photo of the mural taken at an
angle.  Here we:
  1. crop the photo out of the screenshot,
  2. upscale it 4x with Lanczos + unsharp mask (classical; nothing is
     redrawn or generated),
  3. undo the perspective of the main wall (ceiling line, skirting line,
     left wall edge, pillar edge), with the true width/height ratio measured
     from the other views of the same mural in reference 2,
  4. divide out the room lighting so the wall white prints as white.

usage: python art.py aspect      -> measure the mural's real aspect ratio
       python art.py build       -> write art.png
"""
import sys
import numpy as np
import cv2
from common import *

# Main wall of the mural in the cropped photo (738x484 px), read by hand:
#   top of art     y = 23 + 0.174 (x - 150)   (just under the ceiling shadow)
#   skirting top   y = 404 - 0.1146 (x - 16)      (bottom edge of the art)
#   left wall edge x = 16,  pillar edge x = 634
CROP = (0, 558, 738, 1042)
X0, X1 = 16.0, 634.0


def top_y(x):
    return 23 + 0.174 * (x - 150)


def bot_y(x):
    return 404 - 0.1146 * (x - 16)


def src_quad():
    return np.float32([[X0, top_y(X0)], [X1, top_y(X1)], [X1, bot_y(X1)], [X0, bot_y(X0)]])


def load_crop():
    im = cv2.imread(CLIENT_IMG)
    x0, y0, x1, y1 = CROP
    c = im[y0:y1, x0:x1].copy()
    c[:2] = c[2]          # first rows are the screenshot's black bar edge
    return c


def rectify(img, scale, height, aspect, border=(255, 255, 255)):
    """img is the crop at `scale` x its original size."""
    w = int(round(height * aspect))
    q = src_quad() * scale
    dst = np.float32([[0, 0], [w, 0], [w, height], [0, height]])
    H = cv2.getPerspectiveTransform(q, dst)
    out = cv2.warpPerspective(img, H, (w, height), flags=cv2.INTER_LANCZOS4,
                              borderMode=cv2.BORDER_CONSTANT, borderValue=border)
    return out, H


def measure_aspect():
    sift = cv2.SIFT_create(nfeatures=8000, contrastThreshold=0.01)
    bf = cv2.BFMatcher(cv2.NORM_L2)
    guess = 2.5
    crop = load_crop()
    up = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    flat, _ = rectify(up, 3, 900, guess, border=(0, 0, 0))
    g = cv2.cvtColor(flat, cv2.COLOR_BGR2GRAY)
    ka, da = sift.detectAndCompute(g, (g > 5).astype(np.uint8) * 255)
    cx, cy = 960, 540
    res = []
    for i in list(range(1, 67, 6)) + list(range(330, 383, 4)):
        fr = cv2.imread(os.path.join(WORK, "frames2", f"{i:04d}.jpg"), 0)
        kb, db = sift.detectAndCompute(fr, None)
        m = bf.knnMatch(da, db, k=2)
        good = [p[0] for p in m if len(p) == 2 and p[0].distance < 0.75 * p[1].distance]
        if len(good) < 30:
            continue
        pa = np.float32([ka[x.queryIdx].pt for x in good])
        pb = np.float32([kb[x.trainIdx].pt for x in good])
        H, inl = cv2.findHomography(pa, pb, cv2.USAC_MAGSAC, 4.0, maxIters=10000)
        if H is None or inl.sum() < 40:
            continue
        h1, h2 = H[:, 0], H[:, 1]
        num = (h1[0] - cx * h1[2]) * (h2[0] - cx * h2[2]) + (h1[1] - cy * h1[2]) * (h2[1] - cy * h2[2])
        den = h1[2] * h2[2]
        f2 = -num / den if abs(den) > 1e-12 else -1
        f = np.sqrt(f2) if f2 > 0 else float("nan")
        out = {"frame": i, "inliers": int(inl.sum()), "f": float(f)}
        for ff in (f, 1400.0, 1700.0):     # also report with typical phone f
            if not np.isfinite(ff):
                continue
            K = np.array([[ff, 0, cx], [0, ff, cy], [0, 0, 1.0]])
            Ki = np.linalg.inv(K)
            m1, m2 = Ki @ h1, Ki @ h2
            out[f"s@{int(ff)}"] = float(np.linalg.norm(m1) / np.linalg.norm(m2))
            out[f"cos@{int(ff)}"] = float(m1 @ m2 / np.linalg.norm(m1) / np.linalg.norm(m2))
        res.append(out)
        print(out, flush=True)
    return guess, res


def upscale(bgr, factor=4):
    """Classical upscaling: no neural network, nothing redrawn.

    Light JPEG clean-up, Lanczos in 2x steps, then an unsharp mask scaled to
    the new size so the ink lines stay crisp.
    """
    img = cv2.fastNlMeansDenoisingColored(bgr, None, 2, 2, 5, 15)
    f = 1
    while f < factor:
        img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
        f *= 2
        blur = cv2.GaussianBlur(img, (0, 0), 1.2 * f / 2)
        img = cv2.addWeighted(img, 1.45, blur, -0.45, 0)
    return img


def white_map(img, sigma=70):
    """Per-channel level of the bare (white) wall, smooth over the image.

    Normalised convolution over near-white pixels.  A second, flat estimate
    (narrow vertically, wide horizontally) follows the soft shadow under the
    ceiling; it is used wherever it has enough white pixels to trust.
    """
    f = img.astype(np.float32)
    mn, mx = f.min(2), f.max(2)
    m = ((mn > 150) & (mx - mn < 28)).astype(np.float32)
    m = cv2.erode(m, np.ones((5, 5), np.uint8))
    out = np.zeros_like(f)

    def nconv(sx, sy):
        den = cv2.GaussianBlur(m, (0, 0), sigmaX=sx, sigmaY=sy) + 1e-6
        num = [cv2.GaussianBlur(f[..., c] * m, (0, 0), sigmaX=sx, sigmaY=sy) for c in range(3)]
        return np.stack(num, 2) / den[..., None], den

    iso, _ = nconv(sigma, sigma)
    ani, den_a = nconv(4 * sigma, sigma / 4)
    conf = np.clip(den_a / 0.35, 0, 1)[..., None]
    out = conf * ani + (1 - conf) * iso
    return out, m


if __name__ == "__main__":
    stage = sys.argv[1]
    if stage == "aspect":
        guess, res = measure_aspect()
        save_json({"guess": guess, "views": res}, "aspect.json")
    elif stage == "build":
        asp = load_json("aspect.json")
        views = asp["views"]
        # frontal views of reference 2 give |h1|/|h2| directly; perspective
        # views give it with the focal length solved from orthogonality.
        ss = [v.get(f"s@{int(v['f'])}") if np.isfinite(v["f"]) else v["s@1400"] for v in views]
        aspect = asp["guess"] * float(np.median(ss))
        crop = load_crop()
        up = upscale(crop, 4)
        ART_H = 1652
        flat, Hr = rectify(up, 4, ART_H, aspect, border=(0, 0, 0))
        valid, _ = rectify(np.full_like(up, 255), 4, ART_H, aspect, border=(0, 0, 0))
        valid = valid[..., 0] > 128
        wm, _ = white_map(np.where(valid[..., None], flat, 255).astype(np.uint8))
        alb = flat.astype(np.float32) / np.maximum(wm, 1) * 255
        alb = np.clip(alb * 1.0, 0, 255)
        alb[~valid] = 255
        # the top rows are bare wall right under the ceiling: clean any
        # leftover shadow there (greyish, unsaturated pixels only)
        top = alb[:70]
        mn, mx = top.min(2), top.max(2)
        bare = (mn > 120) & (mx - mn < 30)
        ramp = np.clip((70 - np.arange(70)) / 35.0, 0, 1)[:, None]
        top[bare] = (top + (255 - top) * ramp[..., None])[bare]
        alb = alb.astype(np.uint8)
        cv2.imwrite(os.path.join(WORK, "art.png"), alb)
        cv2.imwrite(os.path.join(WORK, "art_raw.png"), flat)
        save_json({"aspect": aspect, "w": int(alb.shape[1]), "h": int(alb.shape[0])}, "art.json")
        print("aspect", aspect, alb.shape)
