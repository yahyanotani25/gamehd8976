"""Render the film without its chapter title cards.

usage: recut.py W audio.wav out.mp4 [crf] [preset]

Reads the same sources as splice.py (untouched original frames plus the rendered
replacement groups), drops each chapter card's frames (recut_plan.CARDS), and
dissolves the n frames before every cut into the n frames after it. The video is
encoded once; the soundtrack is the recut one from recut_audio.py.
"""
import sys, os, json, glob, subprocess, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import recut_plan as RP

W, AUDIO, OUTP = sys.argv[1], sys.argv[2], sys.argv[3]
CRF = sys.argv[4] if len(sys.argv) > 4 else "17"
PRESET = sys.argv[5] if len(sys.argv) > 5 else "medium"
ORIG = W + "/dl/original/original.mp4"
FW, FH, FPS = 1920, 1080, 25
YS, CS = FW * FH, (FW // 2) * (FH // 2)
FS = YS + 2 * CS
N = 23048

groups = sorted([json.load(open(p)) for p in glob.glob(W + "/work/slots/*.json")], key=lambda m: m["f0"])
cards = sorted(json.load(open(W + "/work/recut_plan.json")), key=lambda c: c["v0"])
n_out = N - sum(c["D_frames"] for c in cards)
print(len(groups), "replacement groups;", len(cards), "chapter cards removed; output frames", n_out, flush=True)


def source_frames():
    """Every frame of the corrected film in original order (yuv420p bytes)."""
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", ORIG, "-map", "0:v:0", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"],
                           stdout=subprocess.PIPE, bufsize=FS * 4)
    gi, cur = 0, None
    for i in range(N):
        buf = dec.stdout.read(FS)
        assert len(buf) == FS, ("short read", i)
        if cur is None and gi < len(groups) and i == groups[gi]["f0"]:
            g = groups[gi]
            cur = (g, subprocess.Popen(["ffmpeg", "-v", "error", "-i", f"{W}/work/slots/{g['name']}.mkv", "-f", "rawvideo",
                                        "-pix_fmt", "yuv420p", "-"], stdout=subprocess.PIPE, bufsize=FS * 4))
        if cur is not None:
            g, p = cur
            rb = p.stdout.read(FS)
            assert len(rb) == FS, ("short slot read", g["name"], i)
            buf = rb
            if i == g["f1"]:
                p.stdout.close(); p.wait(); cur = None; gi += 1
        yield i, buf
    dec.wait()
    assert gi == len(groups)


def blend(a, b, w):
    x = np.frombuffer(a, np.uint8).astype(np.float32)
    y = np.frombuffer(b, np.uint8).astype(np.float32)
    return np.clip(x * (1 - w) + y * w + 0.5, 0, 255).astype(np.uint8).tobytes()


enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y",
                        "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{FW}x{FH}", "-r", str(FPS), "-i", "-",
                        "-i", AUDIO, "-map", "0:v:0", "-map", "1:a:0",
                        "-c:v", "libx264", "-preset", PRESET, "-crf", CRF, "-profile:v", "high", "-level:v", "4.2",
                        "-pix_fmt", "yuv420p", "-g", "50", "-bf", "3",
                        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
                        "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", OUTP], stdin=subprocess.PIPE)
t0 = time.time()
ci, pre, written = 0, [], 0
for i, buf in source_frames():
    c = cards[ci] if ci < len(cards) else None
    if c and c["v0"] - c["n"] <= i < c["v0"]:
        pre.append(buf)                      # tail of the shot before the card
        continue
    if c and c["v0"] <= i <= c["v1"]:
        continue                             # the chapter card itself
    if c and c["v1"] < i <= c["v1"] + c["n"]:
        k = i - c["v1"] - 1                  # dissolve into the shot after the card
        buf = blend(pre[k], buf, (k + 1) / (c["n"] + 1))
        if k == c["n"] - 1:
            pre, ci = [], ci + 1
    enc.stdin.write(buf)
    written += 1
    if i % 2000 == 0:
        el = time.time() - t0
        print(f"source frame {i}/{N}, written {written}, {el:.0f}s, {written / max(el, 1e-6):.1f} fps", flush=True)
enc.stdin.close(); enc.wait()
assert ci == len(cards), ("cards not all applied", ci)
assert written == n_out, (written, n_out)
print("done", OUTP, written, "frames", round(time.time() - t0), "s", flush=True)
