"""Check a finished master against the original.

usage: verify.py W master.mp4

- same frame count, frame rate, resolution and duration
- audio packets bit-identical to the original
- frames outside the replaced slots match the original (PSNR per frame)
- brightness of every replaced slot before vs after
"""
import sys, os, json, subprocess, hashlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from slots import SLOTS

W, M = sys.argv[1], sys.argv[2]
O = W + "/dl/original/original.mp4"


def info(p):
    j = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
        "stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,sample_rate,channels:format=duration,size,bit_rate",
        "-of", "json", p]))
    return j


def audio_md5(p):
    h = hashlib.md5()
    pr = subprocess.Popen(["ffmpeg", "-v", "error", "-i", p, "-map", "0:a:0", "-c", "copy", "-f", "data", "-"], stdout=subprocess.PIPE)
    for chunk in iter(lambda: pr.stdout.read(1 << 20), b""):
        h.update(chunk)
    pr.wait()
    return h.hexdigest()


io, im = info(O), info(M)
for tag, j in (("original", io), ("master", im)):
    v = [s for s in j["streams"] if s["codec_type"] == "video"][0]
    a = [s for s in j["streams"] if s["codec_type"] == "audio"][0]
    print(f"{tag:8s} {v['codec_name']} {v['width']}x{v['height']} {v['r_frame_rate']} frames={v.get('nb_frames')} | "
          f"{a['codec_name']} {a['sample_rate']}Hz {a['channels']}ch | dur={float(j['format']['duration']):.3f}s "
          f"size={int(j['format']['size']) / 1e9:.2f}GB br={int(j['format']['bit_rate']) / 1e6:.1f}Mbps")
ma, mo = audio_md5(M), audio_md5(O)
print("audio packets identical:", ma == mo, ma[:12], mo[:12])

# per-frame PSNR (luma) between master and original on a 480x270 downscale, all frames
w, h = 480, 270
def frames(p):
    pr = subprocess.Popen(["ffmpeg", "-v", "error", "-i", p, "-vf", f"scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                          stdout=subprocess.PIPE, bufsize=w * h * 64)
    while True:
        b = pr.stdout.read(w * h)
        if len(b) < w * h:
            break
        yield np.frombuffer(b, np.uint8).astype(np.float32)
    pr.wait()
inslot = np.zeros(23048, bool)
for s in SLOTS:
    inslot[s["f0"]:s["f1"] + 1] = True
ps, Ym, Yo = [], [], []
for i, (a, b) in enumerate(zip(frames(O), frames(M))):
    mse = float(((a - b) ** 2).mean())
    ps.append(99.0 if mse < 1e-6 else 10 * np.log10(255 ** 2 / mse))
    Yo.append(float(a.mean())); Ym.append(float(b.mean()))
ps, Ym, Yo = np.array(ps), np.array(Ym), np.array(Yo)
n = len(ps)
print("frames compared:", n)
out = ps[~inslot[:n]]
print(f"outside slots: {len(out)} frames, PSNR min {out.min():.1f} dB, p1 {np.percentile(out, 1):.1f}, median {np.median(out):.1f}")
bad = np.nonzero((~inslot[:n]) & (ps < 35))[0]
print("outside-slot frames below 35 dB:", len(bad), bad[:20].tolist())
print("slot brightness (mean luma, before -> after):")
for s in SLOTS:
    a, b = s["f0"], s["f1"] + 1
    print(f"  {s['id']} {a / 25:7.2f}s  {np.mean(Yo[a:b]):5.1f} -> {np.mean(Ym[a:b]):5.1f}")
allin = inslot[:n]
print(f"replaced frames: mean luma {Yo[allin].mean():.1f} -> {Ym[allin].mean():.1f}; whole film {Yo.mean():.1f} -> {Ym.mean():.1f}")
