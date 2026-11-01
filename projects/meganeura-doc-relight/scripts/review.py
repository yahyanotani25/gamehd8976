"""review.py W out.jpg frame [frame...]  -> rows of (original | new) at 480x270 for the given frames."""
import sys, os, glob, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
W, out = sys.argv[1], sys.argv[2]
frames = [int(x) for x in sys.argv[3:]]
ORIG = W + "/dl/original/original.mp4"
metas = [json.load(open(p)) for p in glob.glob(W + "/work/slots/*.json")]
tw, th = 480, 270
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
def grab(path, idx, fps=25):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{idx / fps:.4f}", "-i", path, "-frames:v", "1",
                          "-vf", f"scale={tw}:{th}:in_color_matrix=bt709", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombytes("RGB", (tw, th), raw[:tw * th * 3]) if len(raw) >= tw * th * 3 else Image.new("RGB", (tw, th), "gray")
cols = 2
sheet = Image.new("RGB", (cols * (tw + 4) * 2, ((len(frames) + cols - 1) // cols) * (th + 4)), "white")
d = ImageDraw.Draw(sheet)
for k, f in enumerate(frames):
    a = grab(ORIG, f)
    m = [m for m in metas if m["f0"] <= f <= m["f1"]]
    b = grab(W + f"/work/slots/{m[0]['name']}.mkv", f - m[0]["f0"]) if m else a
    x = (k % cols) * (tw + 4) * 2; y = (k // cols) * (th + 4)
    sheet.paste(a, (x, y)); sheet.paste(b, (x + tw + 2, y))
    ya = np.asarray(a, np.float32).mean(); yb = np.asarray(b, np.float32).mean()
    lab = f"f{f} {int(f/25//60)}:{f/25%60:05.2f}  {ya:.0f} -> {yb:.0f}"
    d.rectangle([x, y, x + 9 * len(lab), y + 18], fill="black"); d.text((x + 3, y + 1), lab, fill="yellow", font=font)
sheet.save(out, quality=82)
print(out, sheet.size)
