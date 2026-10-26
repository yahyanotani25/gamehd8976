#!/usr/bin/env python3
"""Subject cutout for 2.5D: image -> full-frame RGBA PNG of the main subject (+ its mask).

Segmentation via rembg (ONNX Runtime, CPU). Commercial-OK models only by default:
  isnet-general-use      DIS / IS-Net, Apache-2.0   (DEFAULT: good on buildings, objects, people)
  birefnet-general-lite  BiRefNet Swin-T, MIT       (often cleaner edges, ~2x slower)
  birefnet-general       BiRefNet Swin-L, MIT       (best, ~1 GB download, slow on CPU)
  u2net                  U^2-Net, Apache-2.0        (fast, coarse 320 px mask)
  u2net_human_seg        U^2-Net people, Apache-2.0
Do NOT use bria-rmbg (non-commercial licence) for the film.

The low-res model mask is upsampled to the photo and refined at full resolution:
  --refine guided    (default) guided-filter matte snapped to the photo's edges
  --refine vitmatte  rembg's ViTMatte refiner (MIT weights, works at 1024 px), then guided upsampling
  --refine none      model mask as-is
--decontam removes background colour fringing from soft edges (pymatting ML foreground
estimation) so the cutout can slide over a different/moving plate without a halo.

Usage (venv: /home/user/.venvs/doc25d):
  PY=/home/user/.venvs/doc25d/bin/python
  $PY -I tools/cutout.py cabin.jpg --preview                  # -> cabin_cutout.png, cabin_mask.png
  $PY -I tools/cutout.py stills/ -o cutouts --largest --decontam --preview
  $PY -I tools/cutout.py cabin.jpg --model birefnet-general-lite --trim

Outputs per input <stem> (full frame, same size as the input, straight/unpremultiplied alpha):
  <stem>_cutout.png          RGBA
  <stem>_mask.png            8-bit alpha (feed to inpaint_bg.py)
  <stem>_cutout_trim.png     (--trim) RGBA cropped to the subject + <stem>_cutout_trim.json offset
  <stem>_cutout_preview.jpg  (--preview) photo | alpha | cutout over checkerboard
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from depth import guided_filter, list_inputs, load_rgb, out_base  # noqa: E402

NONCOMMERCIAL = {"bria-rmbg"}


def segment(session, rgb):
    from PIL import Image
    from rembg import remove
    m = remove(Image.fromarray(rgb), session=session, only_mask=True, post_process_mask=False)
    m = np.asarray(m, dtype=np.float32) / 255.0
    if m.shape != rgb.shape[:2]:
        import cv2
        m = cv2.resize(m, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_LINEAR)
    return m


def keep_largest(alpha, min_frac=0.15):
    """Drop blobs smaller than min_frac of the largest one (stray bits of background)."""
    import cv2
    n, lab, stats, _ = cv2.connectedComponentsWithStats((alpha > 0.5).astype(np.uint8), 8)
    if n <= 2:
        return alpha
    areas = stats[1:, cv2.CC_STAT_AREA]
    keep = np.zeros(n, bool)
    keep[1:] = areas >= areas.max() * min_frac
    support = keep[lab].astype(np.uint8)
    # keep the soft fringe that touches kept blobs
    k = max(3, int(min(alpha.shape) / 300) | 1)
    support = cv2.dilate(support, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    return alpha * support


def fill_holes(alpha, max_frac=0.002):
    """Fill small enclosed holes (e.g. specular gaps) up to max_frac of the frame."""
    import cv2
    inv = (alpha < 0.5).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(inv, 4)
    H, W = alpha.shape
    out = alpha.copy()
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        if a < max_frac * H * W and x > 0 and y > 0 and x + w < W and y + h < H:
            out[lab == i] = 1.0
    return out


def refine_guided(rgb, alpha, radius, eps, contrast):
    a = guided_filter(rgb, alpha.astype(np.float32), radius, eps)
    if contrast > 1:  # steepen the soft transition around 0.5, keeps fine partial coverage
        a = (a - 0.5) * contrast + 0.5
    return np.clip(a, 0, 1).astype(np.float32)


def refine_vitmatte(rgb, alpha):
    from PIL import Image
    from rembg.matting import vitmatte_alpha
    m = Image.fromarray((alpha * 255).astype(np.uint8))
    out = vitmatte_alpha(Image.fromarray(rgb), m)  # small-distinctions-646, 1024x1024
    out = np.asarray(out.convert("L"), dtype=np.float32) / 255.0
    if out.shape != alpha.shape:
        import cv2
        out = cv2.resize(out, (alpha.shape[1], alpha.shape[0]), interpolation=cv2.INTER_LINEAR)
    return out


def decontaminate(rgb, alpha, max_side=2048):
    """Foreground colour estimation (pymatting ML). Run at <= max_side for speed, then only
    the edge band of the full-res image takes the estimated colours."""
    import cv2
    from pymatting import estimate_foreground_ml
    H, W = alpha.shape
    s = min(1.0, max_side / max(H, W))
    img = rgb.astype(np.float64) / 255.0
    if s < 1:
        size = (int(W * s), int(H * s))
        fg = estimate_foreground_ml(cv2.resize(img, size, interpolation=cv2.INTER_AREA),
                                    cv2.resize(alpha.astype(np.float64), size, interpolation=cv2.INTER_AREA))
        fg = cv2.resize(fg, (W, H), interpolation=cv2.INTER_LINEAR)
    else:
        fg = estimate_foreground_ml(img, alpha.astype(np.float64))
    # use estimated colour only where the matte is soft (+ a little around it)
    soft = ((alpha > 0.02) & (alpha < 0.98)).astype(np.uint8)
    k = max(3, int(max(H, W) / 500) | 1)
    soft = cv2.GaussianBlur(cv2.dilate(soft, np.ones((k, k), np.uint8)).astype(np.float32), (k, k), 0)
    out = img * (1 - soft[..., None]) + np.clip(fg, 0, 1) * soft[..., None]
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


def checker_composite(rgb, alpha, sq=24):
    H, W = alpha.shape
    yy, xx = np.mgrid[:H, :W]
    chk = np.where(((yy // sq) + (xx // sq)) % 2 == 0, 200, 120).astype(np.float32)[..., None]
    return (rgb * alpha[..., None] + chk * (1 - alpha[..., None])).astype(np.uint8)


def preview(rgb, fg, alpha, path, height=600):
    import cv2
    H, W = alpha.shape
    s = height / H
    size = (int(W * s), height)
    r = lambda x: cv2.resize(x, size, interpolation=cv2.INTER_AREA)
    a8 = r((alpha * 255).astype(np.uint8))
    comp = r(checker_composite(fg.astype(np.float32), alpha, sq=max(8, int(24 / s / 2))))
    gap = np.full((height, 8, 3), 255, np.uint8)
    sheet = np.concatenate([r(rgb), gap, np.dstack([a8] * 3), gap, comp], 1)
    cv2.imwrite(path, cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])


def save_rgba(path, rgb, alpha):
    from PIL import Image
    a8 = (np.clip(alpha, 0, 1) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(np.dstack([rgb, a8]), "RGBA").save(path, compress_level=6)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="image files and/or directories")
    ap.add_argument("-o", "--outdir", default=None, help="output directory (default: next to each input)")
    ap.add_argument("--model", default="isnet-general-use",
                    help="rembg model (default isnet-general-use; birefnet-general-lite, birefnet-general, u2net ...)")
    ap.add_argument("--refine", default="guided", choices=["none", "guided", "vitmatte"],
                    help="edge refinement at full resolution (default guided)")
    ap.add_argument("--radius", type=int, default=None, help="guided radius px (default ~min(H,W)/360)")
    ap.add_argument("--eps", type=float, default=2e-4, help="guided eps (smaller = follows photo edges harder)")
    ap.add_argument("--contrast", type=float, default=1.6,
                    help="steepen the refined matte around 0.5 (1 = off, default 1.6)")
    ap.add_argument("--largest", action="store_true", help="keep only the main blob(s), drop strays")
    ap.add_argument("--fill-holes", action="store_true", help="fill small enclosed holes in the matte")
    ap.add_argument("--erode", type=float, default=0.0, help="shrink the matte by N px (negative grows)")
    ap.add_argument("--feather", type=float, default=0.0, help="extra Gaussian feather sigma px")
    ap.add_argument("--decontam", action="store_true", help="remove background colour fringe from soft edges")
    ap.add_argument("--trim", action="store_true", help="also write a cropped RGBA + offset json")
    ap.add_argument("--preview", action="store_true", help="write <stem>_cutout_preview.jpg")
    ap.add_argument("--threads", type=int, default=None, help="ONNX Runtime intra-op threads")
    a = ap.parse_args()

    import cv2
    from rembg import new_session
    if a.model in NONCOMMERCIAL:
        sys.stderr.write(f"WARNING: {a.model} has a non-commercial licence: not for the monetised film.\n")
    kw = {}
    if a.threads:
        import onnxruntime as ort
        so = ort.SessionOptions()
        so.intra_op_num_threads = a.threads
        kw["sess_opts"] = so
    t0 = time.time()
    session = new_session(a.model, **kw)
    print(f"rembg session {a.model} ready in {time.time() - t0:.1f}s", flush=True)

    for f in list_inputs(a.inputs):
        t = time.time()
        rgb = load_rgb(f)
        H, W = rgb.shape[:2]
        alpha = segment(session, rgb)
        t_seg = time.time() - t
        if a.largest:
            alpha = keep_largest(alpha)
        if a.fill_holes:
            alpha = fill_holes(alpha)
        radius = a.radius or max(2, int(round(min(H, W) / 360)))
        if a.refine == "vitmatte":
            alpha = refine_vitmatte(rgb, alpha)
            alpha = refine_guided(rgb, alpha, max(2, radius // 2), a.eps, 1.0)
        elif a.refine == "guided":
            alpha = refine_guided(rgb, alpha, radius, a.eps, a.contrast)
        if a.erode:
            k = int(abs(a.erode)) * 2 + 1
            se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
            alpha = cv2.erode(alpha, se) if a.erode > 0 else cv2.dilate(alpha, se)
        if a.feather > 0:
            alpha = cv2.GaussianBlur(alpha, (0, 0), a.feather)
        alpha = np.clip(alpha, 0, 1).astype(np.float32)
        fg = decontaminate(rgb, alpha) if a.decontam else rgb

        base = out_base(f, a.outdir)
        save_rgba(base + "_cutout.png", fg, alpha)
        cv2.imwrite(base + "_mask.png", (alpha * 255 + 0.5).astype(np.uint8))
        ys, xs = np.nonzero(alpha > 0.01)
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if len(xs) else [0, 0, W, H]
        if a.trim:
            pad = max(4, int(min(H, W) * 0.01))
            x0, y0 = max(0, bbox[0] - pad), max(0, bbox[1] - pad)
            x1, y1 = min(W, bbox[2] + pad), min(H, bbox[3] + pad)
            save_rgba(base + "_cutout_trim.png", fg[y0:y1, x0:x1], alpha[y0:y1, x0:x1])
            with open(base + "_cutout_trim.json", "w") as fh:
                json.dump(dict(src=os.path.basename(f), frame=[W, H], x=x0, y=y0, w=x1 - x0, h=y1 - y0,
                               model=a.model), fh, indent=1)
        if a.preview:
            preview(rgb, fg, alpha, base + "_cutout_preview.jpg")
        cover = float((alpha > 0.5).mean())
        print(f"{f}: {W}x{H} seg {t_seg:.1f}s total {time.time() - t:.1f}s  bbox {bbox} "
              f"coverage {cover:.1%} -> {base}_cutout.png", flush=True)


if __name__ == "__main__":
    main()
