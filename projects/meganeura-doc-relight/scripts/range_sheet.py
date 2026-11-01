"""Contact sheet of the original for [t0,t1] every `step` s + diff/luma plot.
usage: range_sheet.py W t0 t1 step out.jpg"""
import sys, subprocess, io, numpy as np
from PIL import Image, ImageDraw, ImageFont
W, t0, t1, step, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
src = W + "/dl/original/original.mp4"
FPS = 25
st = np.load(W + "/work/orig_stats.npy"); df = np.load(W + "/work/orig_diffs.npy"); th = np.load(W + "/work/orig_thumbs.npy").astype(np.float32)
tw, thh, cols = 320, 180, 6
times = list(np.arange(t0, t1 + 1e-6, step))
# extract frames via a single ffmpeg call using select on frame numbers
frames = [int(round(t * FPS)) for t in times]
sel = "+".join(f"eq(n\\,{f})" for f in frames)
cmd = ["ffmpeg", "-v", "error", "-ss", str(max(0, t0 - 1)), "-i", src, "-vf",
       f"setpts=PTS-STARTPTS", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{tw}x{thh}",
       "-frames:v", str(int((t1 - max(0, t0 - 1)) * FPS) + 3), "-"]
raw = subprocess.run(cmd, stdout=subprocess.PIPE).stdout
fs = tw * thh * 3
allf = [np.frombuffer(raw[i:i + fs], np.uint8).reshape(thh, tw, 3) for i in range(0, len(raw) - fs + 1, fs)]
base = int(round(max(0, t0 - 1) * FPS))
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
rows = (len(times) + cols - 1) // cols
plot_h = 160
sheet = Image.new("RGB", (cols * (tw + 4), rows * (thh + 4) + plot_h + 10), "white")
d = ImageDraw.Draw(sheet)
for k, (t, f) in enumerate(zip(times, frames)):
    idx = f - base
    if 0 <= idx < len(allf):
        im = Image.fromarray(allf[idx])
    else:
        im = Image.new("RGB", (tw, thh), "gray")
    x, y = (k % cols) * (tw + 4), (k // cols) * (thh + 4)
    sheet.paste(im, (x + 2, y + 2))
    lab = f"{int(t // 60)}:{t % 60:05.2f} f{f} Y{st[f, 0]:.0f}"
    d.rectangle([x + 2, y + 2, x + 2 + 8 * len(lab), y + 20], fill="black")
    d.text((x + 4, y + 3), lab, fill="yellow", font=font)
# plot: per-frame diff (red), luma (blue), long-lag diff (green)
a, b = int(t0 * FPS), min(len(df) - 1, int(t1 * FPS))
Wd = sheet.width - 20
y0 = rows * (thh + 4) + 5
d.rectangle([10, y0, 10 + Wd, y0 + plot_h], outline="black")
def X(i): return 10 + (i - a) / max(1, (b - a)) * Wd
k = 6
lag = np.array([np.abs(th[min(i + k, len(th) - 1)] - th[max(i - k, 0)]).mean() for i in range(a, b + 1)])
for arr, col, sc in [(df[a:b + 1], "red", 60.0), (st[a:b + 1, 0], "blue", 160.0), (lag, "green", 60.0)]:
    pts = [(X(a + i), y0 + plot_h - min(1.0, v / sc) * plot_h) for i, v in enumerate(arr)]
    d.line(pts, fill=col, width=1)
for s in range(int(t0), int(t1) + 1):
    xx = X(s * FPS); d.line([(xx, y0 + plot_h - 6), (xx, y0 + plot_h)], fill="black")
    d.text((xx + 1, y0 + plot_h - 18), f"{s // 60}:{s % 60:02d}", fill="black", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10))
sheet.save(out, quality=82)
print(out, sheet.size)
