"""Checkerboard of frame vs. master re-projected into the frame."""
import sys
import numpy as np
import cv2
from common import *
from track import load_tr
from check import sheet

tr = load_tr(sys.argv[1])
out = sys.argv[2]
master = cv2.imread(os.path.join(WORK, "master1_color.png"))
ims = []
frames = [int(x) for x in sys.argv[3:]]
for i in frames:
    fr = read_frame(i)
    w = cv2.warpPerspective(master, tr[i], (FW, FH))
    yy, xx = np.mgrid[0:FH, 0:FW]
    chk = ((yy // 80 + xx // 80) % 2 == 0)[..., None]
    ims.append(np.where(chk & (w.sum(2, keepdims=True) > 0), w, fr))
cv2.imwrite(out, sheet(ims, frames, cols=len(ims), w=360))
