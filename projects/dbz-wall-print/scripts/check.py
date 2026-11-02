"""Visual checks: draw the tracked canvas grid on frames, make a sheet.

usage: python check.py <tracksfile> <out.jpg> frame frame ...
"""
import sys
import numpy as np
import cv2
from common import *
from track import load_tr


def draw_grid(fr, H, step=250, color=(0, 255, 255)):
    out = fr.copy()
    for u in range(-CU, CANVAS_W - CU + 1, step):
        p = warp_pts(H, [[CU + u, CV + v] for v in np.linspace(0, WALL_H, 40)])
        cv2.polylines(out, [p.astype(np.int32)], False, color, 1, cv2.LINE_AA)
    for v in np.arange(0, WALL_H + 1, step):
        p = warp_pts(H, [[CU + u, CV + v] for u in np.linspace(-CU, CANVAS_W - CU, 60)])
        cv2.polylines(out, [p.astype(np.int32)], False,
                      (0, 0, 255) if v in (0, WALL_H) else color, 2 if v in (0, WALL_H) else 1,
                      cv2.LINE_AA)
    return out


def sheet(images, labels, cols=6, w=240):
    h = int(w * FH / FW)
    rows = (len(images) + cols - 1) // cols
    S = np.zeros((rows * (h + 20), cols * w, 3), np.uint8)
    for k, (im, lb) in enumerate(zip(images, labels)):
        r, c = divmod(k, cols)
        S[r * (h + 20):r * (h + 20) + h, c * w:(c + 1) * w] = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)
        cv2.putText(S, str(lb), (c * w + 4, r * (h + 20) + h + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
    return S


if __name__ == "__main__":
    tr = load_tr(sys.argv[1])
    out = sys.argv[2]
    frames = [int(x) for x in sys.argv[3:]]
    ims = [draw_grid(read_frame(i), tr[i]) for i in frames]
    cols = min(6, len(ims))
    cv2.imwrite(out, sheet(ims, frames, cols=cols, w=360 if cols <= 4 else 240))
