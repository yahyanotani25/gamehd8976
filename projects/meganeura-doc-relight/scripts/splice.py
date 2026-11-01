"""Splice the rendered replacement groups into the original and encode the master.

usage: splice.py W out.mp4 [crf] [preset]

Original frames pass through untouched (yuv420p, no colour conversion); frames
inside a rendered group come from its intermediate. Video is re-encoded once
(x264 High, BT.709 tags), the original AAC audio is copied bit for bit.
"""
import sys, os, json, glob, subprocess, time
import numpy as np

W, OUTP = sys.argv[1], sys.argv[2]
CRF = sys.argv[3] if len(sys.argv) > 3 else "17"
PRESET = sys.argv[4] if len(sys.argv) > 4 else "medium"
ORIG = W + "/dl/original/original.mp4"
FW, FH, FPS = 1920, 1080, 25
FS = FW * FH * 3 // 2
N = 23048

groups = sorted([json.load(open(p)) for p in glob.glob(W + "/work/slots/*.json")], key=lambda m: m["f0"])
# sanity: no overlaps, every intermediate has the right length
prev_end = -1
for g in groups:
    assert g["f0"] > prev_end, ("overlap", g["name"])
    prev_end = g["f1"]
    nb = int(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                                      "stream=nb_read_frames", "-of", "csv=p=0", f"{W}/work/slots/{g['name']}.mkv"]).decode().strip())
    assert nb == g["frames"], (g["name"], nb, g["frames"])
print(len(groups), "groups,", sum(g["frames"] for g in groups), "replacement frames", flush=True)

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", ORIG, "-map", "0:v:0", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"],
                       stdout=subprocess.PIPE, bufsize=FS * 4)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y",
                        "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{FW}x{FH}", "-r", str(FPS), "-i", "-",
                        "-i", ORIG, "-map", "0:v:0", "-map", "1:a:0",
                        "-c:v", "libx264", "-preset", PRESET, "-crf", CRF, "-profile:v", "high", "-level:v", "4.2",
                        "-pix_fmt", "yuv420p", "-g", "50", "-bf", "3",
                        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
                        "-c:a", "copy", "-movflags", "+faststart", OUTP], stdin=subprocess.PIPE)
t0 = time.time()
gi, cur = 0, None
for i in range(N):
    buf = dec.stdout.read(FS)
    assert len(buf) == FS, ("short read at", i)
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
            p.stdout.close(); p.wait()
            cur = None
            gi += 1
    enc.stdin.write(buf)
    if i % 1000 == 0:
        el = time.time() - t0
        print(f"frame {i}/{N}  {el:.0f}s  {i / max(el, 1e-6):.1f} fps", flush=True)
enc.stdin.close()
enc.wait(); dec.wait()
assert gi == len(groups), ("not all groups used", gi, len(groups))
print("done", OUTP, round(time.time() - t0), "s", flush=True)
