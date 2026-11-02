"""Tracking QA: warp each frame back to the canvas and correlate with master.

usage: python qa.py <tracksfile> [step]
"""
import sys
import numpy as np
import cv2
from common import *
from track import load_tr

S = 0.25


def ncc_frame(i, H, master, mvalid):
    fr = read_frame(i)
    ok = (1 - dark_mask(fr, grow=21)).astype(np.uint8)
    Hs = np.diag([S, S, 1]) @ np.linalg.inv(H)
    sz = (int(CANVAS_W * S), int(CANVAS_H * S))
    w = cv2.warpPerspective(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY), Hs, sz).astype(np.float32)
    m = cv2.warpPerspective(ok, Hs, sz, flags=cv2.INTER_NEAREST) > 0
    m &= mvalid > 0
    # compare local structure (high-pass) so lighting changes do not count
    hp = lambda x: x - cv2.GaussianBlur(x, (0, 0), 6)
    a, b = hp(w)[m], hp(master)[m]
    if a.size < 2000:
        return float("nan"), int(a.size)
    a = a - a.mean(); b = b - b.mean()
    return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum() + 1e-9)), int(a.size)


if __name__ == "__main__":
    tr = load_tr(sys.argv[1])
    step = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    master = cv2.imread(os.path.join(WORK, "master1.png"), 0)
    mv = cv2.imread(os.path.join(WORK, "master1_valid.png"), 0)
    master = cv2.resize(master, None, fx=S, fy=S, interpolation=cv2.INTER_AREA).astype(np.float32)
    mv = cv2.resize(mv, None, fx=S, fy=S, interpolation=cv2.INTER_NEAREST)
    for i in sorted(tr)[::step]:
        n, sz = ncc_frame(i, tr[i], master, mv)
        print(i, f"{n:.3f}", sz)
