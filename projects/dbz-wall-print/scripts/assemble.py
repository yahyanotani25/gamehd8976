"""Cut the rendered shots in reference 2's order and timing, add the sound,
and write the final MP4 (1080x1920, 30 fps, H.264 + AAC).

usage: python assemble.py <out.mp4> [--audio ref2|ref1|none]
"""
import os
import sys
import shutil
import subprocess
from common import WORK, REF1, REF2
from segments import SEGMENTS

ORDER = ["s1_wide", "s2_goku", "s3_wide", "s4_vegeta", "s5_buu", "s6_detail", "s7_final"]
# reference 2's cut points (frames at 30 fps): 0, 67, 120, 179, 241, 297, 334, end 383
REF2_CUTS = [67, 53, 59, 62, 56, 37, 49]


def main():
    out = os.path.abspath(sys.argv[1])
    audio = "ref2"
    if "--audio" in sys.argv:
        audio = sys.argv[sys.argv.index("--audio") + 1]
    seq = os.path.join(WORK, "seq")
    shutil.rmtree(seq, ignore_errors=True)
    os.makedirs(seq)
    n = 0
    for name, length in zip(ORDER, REF2_CUTS):
        a, b = SEGMENTS[name]["frames"]
        assert b - a + 1 == length, (name, b - a + 1, length)
        for i in range(a, b + 1):
            os.symlink(os.path.join(WORK, "render", name, f"{i:04d}.png"),
                       os.path.join(seq, f"{n:05d}.png"))
            n += 1
    dur = n / 30.0
    cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", "30", "-i", os.path.join(seq, "%05d.png")]
    if audio in ("ref2", "ref1"):
        cmd += ["-i", REF2 if audio == "ref2" else REF1, "-map", "0:v", "-map", "1:a",
                "-af", f"apad,atrim=0:{dur:.3f},afade=t=out:st={dur - 0.35:.3f}:d=0.35",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    cmd += ["-vf", "scale=1080:1920:flags=lanczos,unsharp=5:5:0.35:5:5:0,format=yuv420p",
            "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high",
            "-movflags", "+faststart", "-t", f"{dur:.3f}", out]
    subprocess.run(cmd, check=True)
    print(out, n, "frames", f"{dur:.2f}s")


if __name__ == "__main__":
    main()
