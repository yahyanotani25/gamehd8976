"""Check the no-chapters cut.

usage: verify_recut.py W recut.mp4 master_v2.mp4

- frame count / durations
- picture sync: around every join, frames of the new cut match the v2 master at
  the original position (new index + frames removed so far)
- sound sync: the new soundtrack lines up with the original at the same mapping
  (cross-correlation lag, ms)
- a sheet of frames across every join (before, mid-dissolve, after)
"""
import sys, os, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

W, NEW, V2 = sys.argv[1], sys.argv[2], sys.argv[3]
ORIG = W + "/dl/original/original.mp4"
cards = sorted(json.load(open(W + "/work/recut_plan.json")), key=lambda c: c["v0"])


def probe(p):
    j = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,nb_frames,duration:format=duration,size",
                                            "-of", "json", p]))
    return j


j = probe(NEW)
for s in j["streams"]:
    print(s["codec_type"], "frames", s.get("nb_frames"), "duration", s.get("duration"))
print("file", round(int(j["format"]["size"]) / 1e9, 3), "GB, duration", j["format"]["duration"])


def frame(path, idx, w=480, h=270):
    # input seeking is frame-accurate when decoding; constant 25 fps from t=0
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{idx / 25 + 0.001:.4f}", "-i", path, "-vf", f"scale={w}:{h}:in_color_matrix=bt709",
                          "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw[:w * h * 3], np.uint8).reshape(h, w, 3)


def psnr(a, b):
    m = float(((a.astype(np.float32) - b.astype(np.float32)) ** 2).mean())
    return 99.0 if m < 1e-6 else 10 * np.log10(255 ** 2 / m)


# picture sync around each join
removed = 0
rows = []
for c in cards:
    before_new = c["v0"] - c["n"] - 5 - removed           # 5 frames before the dissolve
    after_orig = c["v1"] + c["n"] + 5                      # 5 frames after the dissolve
    after_new = after_orig - removed - c["D_frames"]
    mid_new = c["v0"] - removed - c["n"] // 2              # mid-dissolve
    pb = psnr(frame(NEW, before_new), frame(V2, before_new + removed))
    pa = psnr(frame(NEW, after_new), frame(V2, after_orig))
    pa_wrong = psnr(frame(NEW, after_new), frame(V2, after_orig + 1))
    print(f"Ch{c['ch']}: before join PSNR {pb:5.1f} dB | after join PSNR {pa:5.1f} dB (vs neighbour frame {pa_wrong:5.1f})")
    rows.append((c, before_new, mid_new, after_new))
    removed += c["D_frames"]

# sound sync: correlate 2 s of the new soundtrack with the original at the mapped time
def pcm(path, t, dur=2.0, sr=16000):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", path, "-t", f"{dur}", "-map", "0:a:0", "-ac", "1",
                          "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32)
removed_s = 0.0
for c in cards:
    removed_s += (c["a1s"] - c["a0s"]) / 48000
    t_new = c["a0"] - (removed_s - (c["a1s"] - c["a0s"]) / 48000) + 3.0   # 3 s after the join
    a = pcm(NEW, t_new); b = pcm(ORIG, t_new + removed_s - 0.1, 2.2)
    best, lag = -1, 0
    for k in range(0, len(b) - len(a)):
        v = float(np.dot(a, b[k:k + len(a)]) / (np.linalg.norm(a) * np.linalg.norm(b[k:k + len(a)]) + 1e-9))
        if v > best:
            best, lag = v, k
    print(f"Ch{c['ch']}: audio 3 s after the join matches the original with correlation {best:.3f} at offset {(lag / 16000 - 0.1) * 1000:+.1f} ms")

# sheet across joins
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
tw, th = 320, 180
sheet = Image.new("RGB", (3 * (tw + 4), len(rows) * (th + 4)), "white")
d = ImageDraw.Draw(sheet)
for r, (c, b, m, a) in enumerate(rows):
    for k, idx in enumerate((b, m, a)):
        im = Image.fromarray(frame(NEW, idx, tw, th))
        x, y = k * (tw + 4), r * (th + 4)
        sheet.paste(im, (x, y))
        lab = f"Ch{c['ch']} {'before' if k == 0 else 'dissolve' if k == 1 else 'after'} {int(idx / 25 // 60)}:{idx / 25 % 60:05.2f}"
        d.rectangle([x, y, x + 8 * len(lab), y + 16], fill="black"); d.text((x + 2, y + 1), lab, fill="yellow", font=font)
sheet.save(W + "/work/frames/recut_joins.jpg", quality=84)
print("sheet", sheet.size)
