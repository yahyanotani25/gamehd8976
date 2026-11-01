"""Decode the original at low res; per-frame luma stats + cut scores + tiny thumbs."""
import sys, subprocess, numpy as np, json
src, out = sys.argv[1], sys.argv[2]
w, h = 192, 108
cmd = ["ffmpeg", "-v", "error", "-i", src, "-vf", f"scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**8)
fsz = w * h * 3
stats, thumbs, diffs = [], [], []
prev_hsv = None
prev_small = None
import cv2
i = 0
while True:
    buf = p.stdout.read(fsz)
    if len(buf) < fsz:
        break
    f = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
    y = (0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2])
    hsv = cv2.cvtColor(f, cv2.COLOR_RGB2HSV).astype(np.float32)
    sat = hsv[..., 1].mean()
    stats.append([y.mean(), np.percentile(y, 10), np.percentile(y, 50), np.percentile(y, 90), sat, y.std()])
    if prev_hsv is not None:
        # PySceneDetect-like content score: mean abs diff of H,S,V
        d = np.abs(hsv - prev_hsv).mean(axis=(0, 1))
        diffs.append(float(d.mean()))
    else:
        diffs.append(0.0)
    prev_hsv = hsv
    thumbs.append(cv2.resize(f, (64, 36), interpolation=cv2.INTER_AREA))
    i += 1
p.wait()
np.save(out + "_stats.npy", np.array(stats, np.float32))
np.save(out + "_diffs.npy", np.array(diffs, np.float32))
np.save(out + "_thumbs.npy", np.array(thumbs, np.uint8))
print("frames", i)
