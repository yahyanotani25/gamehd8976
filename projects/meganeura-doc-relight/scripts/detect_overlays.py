"""Find text/graphic overlays inside each replacement slot.

Half-resolution (960x540) analysis: white top-hat of luma (removes broad
background), keep low-saturation pixels well above their surroundings, count how
often each pixel lights up across the slot, and box the persistent blobs.
Prints boxes in full-res coordinates with the frames they are visible in.
usage: detect_overlays.py W [slot ids...]
"""
import sys, json, subprocess
import numpy as np, cv2
sys.path.insert(0, sys.argv[0].rsplit("/", 1)[0])
from slots import SLOTS

W = sys.argv[1]
want = set(sys.argv[2:])
SRC = W + "/dl/original/original.mp4"
w, h = 960, 540
K = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
out = {}
for s in SLOTS:
    if want and s["id"] not in want:
        continue
    f0, f1 = s["f0"], s["f1"]
    n = f1 - f0 + 1
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{f0 / 25:.3f}", "-i", SRC, "-frames:v", str(n),
           "-vf", f"scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    F = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    cnt = np.zeros((h, w), np.int32)
    masks = []
    for fr in F:
        hsv = cv2.cvtColor(fr, cv2.COLOR_RGB2HSV)
        Y = cv2.cvtColor(fr, cv2.COLOR_RGB2GRAY)
        th = cv2.morphologyEx(Y, cv2.MORPH_TOPHAT, K)
        m = (th > 45) & (hsv[..., 1] < 90) & (Y > 110)
        masks.append(m)
        cnt += m
    frac = cnt / max(1, len(F))
    pers = (frac > 0.12).astype(np.uint8)
    pers = cv2.dilate(pers, cv2.getStructuringElement(cv2.MORPH_RECT, (25, 9)))
    nlab, lab, stats, _ = cv2.connectedComponentsWithStats(pers)
    boxes = []
    for i in range(1, nlab):
        x, y, bw, bh, area = stats[i]
        if area < 60:
            continue
        reg = lab == i
        act = [int((m & reg).sum()) for m in masks]
        on = [k for k, a in enumerate(act) if a > 0.25 * max(act)]
        boxes.append(dict(x=int(x * 2), y=int(y * 2), w=int(bw * 2), h=int(bh * 2),
                          first=f0 + on[0], last=f0 + on[-1], peak=int(max(act))))
    out[s["id"]] = boxes
    print(s["id"], f"f{f0}-{f1}", "frames", len(F), "boxes:", len(boxes))
    for b in boxes:
        print(f"    box x={b['x']} y={b['y']} w={b['w']} h={b['h']}  frames {b['first']}-{b['last']}  "
              f"({b['first'] / 25:.2f}-{b['last'] / 25:.2f}s) peak={b['peak']}")
    sys.stdout.flush()
json.dump(out, open(W + "/work/overlays.json", "w"), indent=1)
