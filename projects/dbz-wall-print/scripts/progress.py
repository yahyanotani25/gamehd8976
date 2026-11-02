"""How far the printer has printed in every frame of reference 1.

The new mural is printed exactly where and when the old balloon print was:
  * wide time-lapse shots: everything left of the print head's column is
    printed; the column follows the head (its UV light) along the rail,
  * the low-angle close-up: printed up to the head's column, then a faint
    first-pass strip (about 35% ink) to the right of it, as in the footage,
  * from the reveal on: everything printed.
The state is column-wise (the printer prints full-height columns).

usage: python progress.py   -> progress.json {frame: [frontier_u, ghost_w, ghost_a]}
"""
import numpy as np
from common import *

TIMELAPSE = [(1, 17), (18, 124), (125, 132), (454, 632)]
CLOSEUP = [(133, 444), (445, 453)]
DONE = [(633, 897)]
CLOSEUP_STATE = (595.0, 165.0, 0.35)     # measured in the footage (canvas u)


def frontier_track(a, b, heads, win=15):
    fr = np.arange(a, b + 1)
    ks = [k for k in sorted(heads) if a <= k <= b]
    if len(ks) < 2:
        return None
    uu = np.interp(fr, ks, [heads[k][0] for k in ks])
    half = win // 2
    med = np.array([np.median(uu[max(0, j - half):j + half + 1]) for j in range(len(uu))])
    return np.maximum.accumulate(med)


def build():
    heads = {int(k): v for k, v in load_json("heads.json").items()}
    out = {}
    for a, b in TIMELAPSE:
        f = frontier_track(a, b, heads)
        for j, i in enumerate(range(a, b + 1)):
            out[i] = [float(f[j]), 0.0, 0.0]
    for a, b in CLOSEUP:
        for i in range(a, b + 1):
            out[i] = list(CLOSEUP_STATE)
    for a, b in DONE:
        for i in range(a, b + 1):
            out[i] = [1e6, 0.0, 0.0]
    save_json({str(k): v for k, v in out.items()}, "progress.json")
    return out


if __name__ == "__main__":
    p = build()
    for i in (1, 17, 18, 60, 124, 125, 132, 200, 454, 500, 560, 632, 700):
        print(i, [round(x, 1) for x in p[i]])
