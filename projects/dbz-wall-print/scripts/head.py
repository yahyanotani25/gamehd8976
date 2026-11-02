"""Find the print head in every frame (its violet UV-curing light) and map it
onto the wall canvas.  Output: heads.json {frame: [u, v, px, py, area]}.

usage: python head.py <tracksfile> ...
"""
import sys
import numpy as np
import cv2
from common import *
from track import load_tr


def uv_blob(bgr):
    f = bgr.astype(np.int16)
    b, g, r = f[..., 0], f[..., 1], f[..., 2]
    # violet UV light: blue with red above green (the touchscreen is cyan-blue)
    m = ((b > 140) & (b - g > 70) & (b - r > 30) & (r > g + 5)).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
    if n <= 1:
        return None
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    if st[k, cv2.CC_STAT_AREA] < 6:
        return None
    return float(cen[k][0]), float(cen[k][1]), int(st[k, cv2.CC_STAT_AREA])


if __name__ == "__main__":
    out = {}
    for fn in sys.argv[1:]:
        tr = load_tr(fn)
        for i in sorted(tr):
            r = uv_blob(read_frame(i))
            if r is None:
                continue
            x, y, a = r
            u, v = warp_pts(np.linalg.inv(tr[i]), [[x, y]])[0]
            out[str(i)] = [float(u - CU), float(v - CV), x, y, a]
    save_json(out, "heads.json")
    print(len(out))
