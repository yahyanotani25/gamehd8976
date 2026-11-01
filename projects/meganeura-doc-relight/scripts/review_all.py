"""Before/after sheets for every replaced slot: original (left) vs new (right) at the
slot's middle frame, labelled with timecode and the narration under it.

usage: review_all.py W out_prefix [video]   (video: read 'new' frames from a finished
master instead of the per-group intermediates)
"""
import sys, os, json, glob, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from slots import SLOTS

W, PREFIX = sys.argv[1], sys.argv[2]
MASTER = sys.argv[3] if len(sys.argv) > 3 else None
ORIG = W + "/dl/original/original.mp4"
metas = [json.load(open(p)) for p in glob.glob(W + "/work/slots/*.json")]
tr = json.load(open(W + "/work/transcript.json"))
words = [w for s in tr["segments"] for w in s["words"]]
tw, th = 400, 225
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)


def grab(path, idx):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{idx / 25:.4f}", "-i", path, "-frames:v", "1",
                          "-vf", f"scale={tw}:{th}:in_color_matrix=bt709", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    return Image.frombytes("RGB", (tw, th), raw[:tw * th * 3]) if len(raw) >= tw * th * 3 else Image.new("RGB", (tw, th), "gray")


def mid_frame(s):
    a = s["inn"][2] + 1 if s["inn"][0] != "cut" else s["f0"]
    b = s["out"][1] - 1 if s["out"][0] != "cut" else s["f1"]
    if s.get("ovl") and s["kind"] in ("title", "regrade"):
        return int(a + 0.62 * (b - a))  # titles: when the full text is on screen
    return (a + b) // 2


cells = []
for s in SLOTS:
    f = mid_frame(s)
    before = grab(ORIG, f)
    if MASTER:
        after = grab(MASTER, f)
    else:
        m = [m for m in metas if m["f0"] <= f <= m["f1"]]
        after = grab(f"{W}/work/slots/{m[0]['name']}.mkv", f - m[0]["f0"]) if m else Image.new("RGB", (tw, th), "gray")
    t0, t1 = s["f0"] / 25, (s["f1"] + 1) / 25
    narr = " ".join(w["w"].strip() for w in words if w["e"] > t0 + 0.05 and w["s"] < t1 - 0.05) or "(music)"
    yb = np.asarray(before, np.float32).mean(); ya = np.asarray(after, np.float32).mean()
    cells.append((s, f, before, after, narr, yb, ya))

per_sheet = 20
cols = 2
cw, ch = 2 * tw + 6, th + 40
for si in range(0, len(cells), per_sheet):
    chunk = cells[si:si + per_sheet]
    rows = (len(chunk) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (cw + 16), rows * (ch + 8)), "white")
    d = ImageDraw.Draw(sheet)
    for k, (s, f, before, after, narr, yb, ya) in enumerate(chunk):
        x, y = (k % cols) * (cw + 16), (k // cols) * (ch + 8)
        tcs = f"{int(s['f0'] / 25 // 60)}:{s['f0'] / 25 % 60:04.1f}"
        d.text((x + 2, y + 2), f"{s['id']}  {tcs}  ({s['clip']})   brightness {yb:.0f} -> {ya:.0f}", fill="black", font=font)
        txt = narr if len(narr) < 118 else narr[:115] + "..."
        d.text((x + 2, y + 19), txt, fill=(60, 60, 60), font=small)
        sheet.paste(before, (x, y + 38)); sheet.paste(after, (x + tw + 6, y + 38))
        d.rectangle([x, y + 38, x + 52, y + 54], fill="black"); d.text((x + 3, y + 39), "BEFORE", fill="white", font=font)
        d.rectangle([x + tw + 6, y + 38, x + tw + 50, y + 54], fill=(0, 110, 40)); d.text((x + tw + 9, y + 39), "AFTER", fill="white", font=font)
    out = f"{PREFIX}_{si // per_sheet + 1}.jpg"
    sheet.save(out, quality=84)
    print(out, sheet.size)
