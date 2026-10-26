#!/usr/bin/env python3
"""Monocular depth for 2.5D parallax: image -> 16-bit PNG depth map (near = white).

Uses Depth Anything V2 (Hugging Face transformers, CPU). Output is relative
inverse depth ("disparity"), normalised to 0..65535, same size as the input,
optionally snapped to image edges with a guided / joint-bilateral filter.

Usage (venv: /home/user/.venvs/doc25d):
  PY=/home/user/.venvs/doc25d/bin/python
  $PY -I tools/depth.py photo.jpg                       # -> photo_depth.png next to it
  $PY -I tools/depth.py assets/stills/ -o assets/depth --preview
  $PY -I tools/depth.py a.jpg b.jpg --res 1036 --tta --refine guided --preview

Models (--model):
  small  depth-anything/Depth-Anything-V2-Small-hf  Apache-2.0   (DEFAULT, OK for monetised video)
  base   depth-anything/Depth-Anything-V2-Base-hf   CC-BY-NC-4.0 (NON-COMMERCIAL: needs --allow-nc,
                                                     do not use for the monetised film)
  any other Hugging Face depth-estimation repo id is accepted as-is (check its licence).

Outputs per input <stem>:
  <stem>_depth.png          16-bit grayscale, near = white (65535), far/sky = black
  <stem>_depth_preview.jpg  (--preview) original | depth side by side
  <stem>_depth.npy          (--save-npy) float32 raw model disparity at full size, unnormalised
"""
import argparse
import json
import os
import sys
import time

import numpy as np

MODELS = {
    "small": ("depth-anything/Depth-Anything-V2-Small-hf", "Apache-2.0", True),
    "base": ("depth-anything/Depth-Anything-V2-Base-hf", "CC-BY-NC-4.0", False),
    "large": ("depth-anything/Depth-Anything-V2-Large-hf", "CC-BY-NC-4.0", False),
}
IMG_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"}
# files produced by these tools; skipped when a directory is given as input
OUR_SUFFIXES = ("_depth", "_depth_preview", "_cutout", "_mask", "_cutout_preview", "_plate",
                "_plate_preview", "_holemask", "_layers_preview")
MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)


# ---------------------------------------------------------------- io helpers
def list_inputs(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            for f in sorted(os.listdir(p)):
                stem, ext = os.path.splitext(f)
                if ext.lower() in IMG_EXT and not stem.endswith(OUR_SUFFIXES) and "_layer" not in stem:
                    out.append(os.path.join(p, f))
        elif os.path.isfile(p):
            out.append(p)
        else:
            sys.exit(f"not found: {p}")
    return out


def load_rgb(path):
    """Load any image as uint8 RGB (EXIF orientation applied)."""
    from PIL import Image, ImageOps
    Image.MAX_IMAGE_PIXELS = 400_000_000
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    if im.mode in ("I;16", "I;16B", "I"):
        a = np.asarray(im).astype(np.float32)
        a = (a / max(1.0, a.max()) * 255).astype(np.uint8)
        return np.dstack([a] * 3)
    return np.asarray(im.convert("RGB"))


def save_png16(path, arr01, meta=None):
    from PIL import Image
    from PIL.PngImagePlugin import PngInfo
    a = np.clip(arr01 * 65535.0 + 0.5, 0, 65535).astype(np.uint16)
    im = Image.fromarray(a)  # mode I;16
    info = PngInfo()
    if meta:
        info.add_text("doc25d", json.dumps(meta))
    im.save(path, pnginfo=info, compress_level=6)


def load_depth_png(path):
    """Read a depth PNG written by this tool (or any 8/16-bit gray) -> float32 0..1, near = 1."""
    import cv2
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if a is None:
        raise SystemExit(f"cannot read depth map {path}")
    if a.ndim == 3:
        a = a[..., 0]
    return a.astype(np.float32) / (65535.0 if a.dtype == np.uint16 else 255.0)


# ------------------------------------------------------------- edge refinement
def guided_filter(guide_rgb_u8, src, radius, eps):
    """Edge-aware smoothing of `src` (float32 HxW) steered by the RGB image."""
    import cv2
    g = guide_rgb_u8.astype(np.float32) / 255.0
    if hasattr(cv2, "ximgproc"):
        return cv2.ximgproc.guidedFilter(g, src.astype(np.float32), int(radius), float(eps))
    # fallback: grey-guide guided filter with box filters (He et al. 2010)
    I = cv2.cvtColor(g, cv2.COLOR_RGB2GRAY)
    k = (2 * radius + 1, 2 * radius + 1)
    box = lambda x: cv2.boxFilter(x, -1, k)
    mI, mp = box(I), box(src)
    a = (box(I * src) - mI * mp) / (box(I * I) - mI * mI + eps)
    b = mp - a * mI
    return box(a) * I + box(b)


def refine_depth(rgb, d, mode, radius, eps, sigma_color):
    import cv2
    if mode == "none":
        return d
    if mode == "wmf":  # joint weighted median: snaps depth edges onto photo edges without blurring
        if not hasattr(cv2, "ximgproc"):
            raise SystemExit("wmf refine needs opencv-contrib (cv2.ximgproc)")
        d16 = np.clip(d * 65535 + 0.5, 0, 65535).astype(np.uint16)
        # WMF wants 8-bit or float src; run on float32 but quantised to keep histogram small
        out = cv2.ximgproc.weightedMedianFilter(rgb, (d16 >> 4).astype(np.float32), radius,
                                                sigma_color, cv2.ximgproc.WMF_EXP)
        return out.astype(np.float32) / 4095.0
    if mode == "guided":
        return guided_filter(rgb, d, radius, eps)
    if mode == "bilateral":  # joint (cross) bilateral, guide = image
        if not hasattr(cv2, "ximgproc"):
            raise SystemExit("bilateral refine needs opencv-contrib (cv2.ximgproc)")
        g = rgb.astype(np.float32)
        return cv2.ximgproc.jointBilateralFilter(g, d.astype(np.float32), 2 * radius + 1,
                                                 sigma_color, radius)
    raise SystemExit(f"unknown refine mode {mode}")


# ------------------------------------------------------------------ the model
class DepthModel:
    def __init__(self, name="small", allow_nc=False, threads=None):
        import torch
        from transformers import AutoModelForDepthEstimation
        repo, lic, commercial = MODELS.get(name, (name, "check the model card", True))
        if not commercial and not allow_nc:
            raise SystemExit(f"{repo} is {lic} (non-commercial). Not for the monetised film; "
                             "pass --allow-nc for tests only.")
        if not commercial:
            sys.stderr.write(f"WARNING: {repo} is {lic}: test/preview use only.\n")
        if threads:
            torch.set_num_threads(threads)
        self.torch = torch
        self.repo, self.licence = repo, lic
        self.model = AutoModelForDepthEstimation.from_pretrained(repo).eval()

    def _infer(self, x):
        with self.torch.inference_mode():
            return self.model(pixel_values=x).predicted_depth  # (1,h,w), larger = nearer

    def predict(self, rgb, res=518, tta=False):
        """rgb uint8 HxWx3 -> float32 HxW raw disparity (larger = nearer), full input size."""
        import torch
        import torch.nn.functional as F
        H, W = rgb.shape[:2]
        # Depth Anything convention: shorter side -> res, keep aspect, multiple of 14
        s = res / min(H, W)
        h = max(14, int(round(H * s / 14)) * 14)
        w = max(14, int(round(W * s / 14)) * 14)
        x = torch.from_numpy(((rgb.astype(np.float32) / 255.0 - MEAN) / STD).transpose(2, 0, 1))[None]
        x = F.interpolate(x, size=(h, w), mode="bicubic", align_corners=False)
        d = self._infer(x)
        if tta:  # horizontal-flip test-time augmentation
            d = 0.5 * (d + torch.flip(self._infer(torch.flip(x, dims=[3])), dims=[2]))
        d = F.interpolate(d[:, None], size=(H, W), mode="bicubic", align_corners=False)[0, 0]
        return d.float().numpy()


def normalise(d, lo_pct=0.5, hi_pct=99.5):
    lo, hi = np.percentile(d, [lo_pct, hi_pct])
    return np.clip((d - lo) / max(1e-6, hi - lo), 0.0, 1.0).astype(np.float32)


def fuse_detail(base, detail, sigma):
    """Keep the global layout of `base` (native-res pass) and the fine edges of `detail`
    (high-res pass): affine-align detail to base, then low(base) + high(detail)."""
    import cv2
    A = np.stack([detail.ravel()[::7], np.ones(detail.size)[::7]], 1)
    s, o = np.linalg.lstsq(A, base.ravel()[::7], rcond=None)[0]
    detail = detail * s + o
    blur = lambda x: cv2.GaussianBlur(x, (0, 0), sigma)
    return (blur(base) + detail - blur(detail)).astype(np.float32)


def estimate(model, rgb, res=518, tta=False, refine="wmf", radius=None, eps=1e-4,
             sigma_color=25.0, lo_pct=0.5, hi_pct=99.5, detail=0):
    """Full pipeline used by depth.py and layers.py. Returns (depth01 near=1, raw)."""
    raw = model.predict(rgb, res=res, tta=tta)
    if detail and detail > res:
        raw = fuse_detail(raw, model.predict(rgb, res=detail, tta=tta), sigma=min(rgb.shape[:2]) / 40)
    d = normalise(raw, lo_pct, hi_pct)
    if radius is None:  # scale filter footprint with image size (~4 px at 1080p, ~9 px at 4K)
        radius = max(2, int(round(min(rgb.shape[:2]) / 270)))
    d = np.clip(refine_depth(rgb, d, refine, radius, eps, sigma_color), 0, 1)
    return d, raw


def preview(rgb, d01, path, height=720):
    import cv2
    H, W = rgb.shape[:2]
    s = height / H
    size = (max(1, int(W * s)), height)
    a = cv2.resize(rgb, size, interpolation=cv2.INTER_AREA)
    b = cv2.resize((d01 * 255).astype(np.uint8), size, interpolation=cv2.INTER_AREA)
    b = np.dstack([b] * 3)
    sheet = np.concatenate([a, np.full((height, 8, 3), 255, np.uint8), b], axis=1)
    cv2.imwrite(path, cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])


def out_base(path, outdir):
    stem = os.path.splitext(os.path.basename(path))[0]
    d = outdir or os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, stem)


def add_depth_args(ap):
    ap.add_argument("--model", default="small", help="small (default, Apache-2.0) | base (CC-BY-NC) | HF repo id")
    ap.add_argument("--allow-nc", action="store_true", help="permit non-commercial models (tests only)")
    ap.add_argument("--res", type=int, default=518,
                    help="inference size of the shorter side (multiple of 14). 518 = model native; "
                         "756/1036 = more detail on big stills, slower")
    ap.add_argument("--detail", type=int, default=0, metavar="RES",
                    help="extra high-res pass (e.g. 1036) whose fine edges are fused onto the "
                         "--res pass; keeps global layout, adds thin branches/gaps (~3x time)")
    ap.add_argument("--tta", action="store_true", help="average with a horizontally flipped pass (2x time)")
    ap.add_argument("--refine", default="wmf", choices=["none", "wmf", "guided", "bilateral"],
                    help="edge-aware filter guided by the photo: wmf = joint weighted median "
                         "(default, crisp edges snapped to the photo), guided = soft guided filter, "
                         "bilateral = joint bilateral, none")
    ap.add_argument("--radius", type=int, default=None, help="refine radius px (default ~min(H,W)/270)")
    ap.add_argument("--eps", type=float, default=1e-4, help="guided-filter eps (smaller = sharper edges)")
    ap.add_argument("--sigma-color", type=float, default=25.0,
                    help="wmf/bilateral colour sigma in 0-255 units (default 25)")
    ap.add_argument("--clip", type=float, nargs=2, default=[0.5, 99.5], metavar=("LO", "HI"),
                    help="percentiles mapped to black/white (default 0.5 99.5)")
    ap.add_argument("--threads", type=int, default=None, help="torch CPU threads (default: all)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="image files and/or directories")
    ap.add_argument("-o", "--outdir", default=None, help="output directory (default: next to each input)")
    add_depth_args(ap)
    ap.add_argument("--preview", action="store_true", help="write <stem>_depth_preview.jpg (side by side)")
    ap.add_argument("--save-npy", action="store_true", help="also save raw float32 disparity as .npy")
    ap.add_argument("--suffix", default="_depth", help="output suffix (default _depth)")
    a = ap.parse_args()

    files = list_inputs(a.inputs)
    t0 = time.time()
    model = DepthModel(a.model, a.allow_nc, a.threads)
    print(f"model {model.repo} ({model.licence}) loaded in {time.time() - t0:.1f}s", flush=True)
    for f in files:
        t = time.time()
        rgb = load_rgb(f)
        d, raw = estimate(model, rgb, a.res, a.tta, a.refine, a.radius, a.eps, a.sigma_color, *a.clip,
                          detail=a.detail)
        base = out_base(f, a.outdir)
        meta = dict(src=os.path.basename(f), model=model.repo, licence=model.licence, res=a.res,
                    detail=a.detail, tta=a.tta, refine=a.refine, near="white")
        save_png16(base + a.suffix + ".png", d, meta)
        if a.save_npy:
            np.save(base + a.suffix + ".npy", raw.astype(np.float32))
        if a.preview:
            preview(rgb, d, base + a.suffix + "_preview.jpg")
        print(f"{f}: {rgb.shape[1]}x{rgb.shape[0]} -> {base + a.suffix}.png  {time.time() - t:.1f}s",
              flush=True)


if __name__ == "__main__":
    main()
