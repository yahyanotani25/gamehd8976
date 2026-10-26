"""Cinematic "night / dawn" grade of the imagery mosaics: cold, desaturated,
slightly darker, matte blacks. Same grade for every box so a camera move from
the wide box into the regional / close-up boxes stays consistent.

  python3 -I tools/map_grade.py [box ...]   -> assets/map/<box>/imagery_grade_night.jpg
  python3 -I tools/map_grade.py --test in.jpg out.jpg
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from map_common import OUT, write_json  # noqa: E402

Image.MAX_IMAGE_PIXELS = None

PARAMS = dict(saturation=0.48, exposure=0.90, gamma=1.08, contrast=1.08, black_lift=0.03,
              shadow_tint=(0.82, 0.95, 1.14), highlight_tint=(0.95, 0.99, 1.04))


def grade(a, p=PARAMS):
    """a: float32 (H, W, 3) sRGB 0..1 -> graded float32."""
    y = (a @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    a = y + p["saturation"] * (a - y)                         # desaturate
    a = np.clip(a * p["exposure"], 0, 1) ** p["gamma"]           # darker
    a = np.clip((a - 0.5) * p["contrast"] + 0.5, 0, 1)        # gentle contrast
    y = (a @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    w = np.clip(y * 1.6, 0, 1)                                  # 0 = shadows, 1 = highlights
    tint = (1 - w) * np.array(p["shadow_tint"], np.float32) + w * np.array(p["highlight_tint"], np.float32)
    a = a * tint                                                # cold split-tone
    a = p["black_lift"] + (1 - p["black_lift"]) * a             # matte blacks
    return np.clip(a, 0, 1)


def grade_file(src, dst, rows=512):
    im = Image.open(src).convert("RGB")
    W, H = im.size
    out = np.empty((H, W, 3), np.uint8)
    arr = np.asarray(im)
    for y0 in range(0, H, rows):
        chunk = arr[y0:y0 + rows].astype(np.float32) / 255
        out[y0:y0 + rows] = (grade(chunk) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(out).save(dst, quality=92, optimize=True)
    return W, H


def main():
    if sys.argv[1:2] == ["--test"]:
        grade_file(sys.argv[2], sys.argv[3])
        return
    for box in sys.argv[1:] or ["wide", "regional", "closeup"]:
        d = os.path.join(OUT, box)
        W, H = grade_file(os.path.join(d, "imagery.jpg"), os.path.join(d, "imagery_grade_night.jpg"))
        mp = os.path.join(d, "bounds.json")
        meta = json.load(open(mp))
        src = meta["layers"]["imagery"]
        meta["layers"]["imagery_grade_night"] = dict(
            files=["imagery_grade_night.jpg"], width=W, height=H,
            note="imagery.jpg colour-graded (tools/map_grade.py): cold, desaturated, darker, matte blacks. "
                 "Same pixels/bounds as imagery.jpg.", grade_params=PARAMS,
            tile_zoom=src["tile_zoom"], source=src["source"])
        write_json(mp, meta)
        print(box, W, H)


if __name__ == "__main__":
    main()
