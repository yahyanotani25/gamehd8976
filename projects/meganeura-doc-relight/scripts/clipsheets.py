"""clipsheets.py outdir per_sheet clip.mp4 ... -> sheets with 7 frames per clip + stats."""
import sys, os, subprocess, json, concurrent.futures as cf
import numpy as np
from PIL import Image, ImageDraw, ImageFont
outdir, per = sys.argv[1], int(sys.argv[2]); clips = sys.argv[3:]
os.makedirs(outdir, exist_ok=True)
NF, tw, th = 7, 256, 144
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
def info(p):
    j = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate:format=duration", "-of", "json", p]))
    s = j["streams"][0]; d = float(j["format"]["duration"]); n, de = s["r_frame_rate"].split("/")
    return s["width"], s["height"], float(n) / float(de), d
def strip(p):
    w, h, fps, d = info(p)
    ims = []
    for k in range(NF):
        t = (k + 0.5) * d / NF
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", p, "-frames:v", "1", "-vf", f"scale={tw}:{th}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        if len(raw) >= tw * th * 3:
            ims.append((t, Image.frombytes("RGB", (tw, th), raw[:tw * th * 3])))
    return p, (w, h, fps, d), ims
with cf.ThreadPoolExecutor(4) as ex:
    res = list(ex.map(strip, clips))
for si in range(0, len(res), per):
    grp = res[si:si + per]
    sheet = Image.new("RGB", (NF * (tw + 2) + 2, len(grp) * (th + 22)), "white")
    d = ImageDraw.Draw(sheet)
    for r, (p, (w, h, fps, dur), ims) in enumerate(grp):
        y = r * (th + 22)
        Ys = [np.asarray(im).mean() for _, im in ims]
        d.text((4, y + 3), f"{os.path.basename(p)}  {w}x{h} {fps:.2f}fps {dur:.1f}s  meanY~{np.mean(Ys):.0f}", fill="black", font=font)
        for k, (t, im) in enumerate(ims):
            x = 2 + k * (tw + 2)
            sheet.paste(im, (x, y + 20))
            d.rectangle([x, y + 20, x + 46, y + 34], fill="black"); d.text((x + 2, y + 21), f"{t:.1f}s", fill="yellow", font=font)
    out = os.path.join(outdir, f"sheet_{si // per + 1:02d}.jpg")
    sheet.save(out, quality=80); print(out, sheet.size)
