"""Reference 1 frame for frame (897 frames, 29.9 s) with the new mural, with
reference 1's own sound.  Output 1080x1920, 30 fps, H.264 + AAC.

usage: python assemble2.py <out.mp4>
"""
import os
import sys
import shutil
import subprocess
from common import WORK, REF1


def main():
    out = os.path.abspath(sys.argv[1])
    seq = os.path.join(WORK, "seq2")
    shutil.rmtree(seq, ignore_errors=True)
    os.makedirs(seq)
    missing = []
    for i in range(1, 898):
        src = os.path.join(WORK, "render2", f"{i:04d}.png")
        if not os.path.exists(src):
            missing.append(i)
            src = os.path.join(WORK, "frames1", f"{i:04d}.jpg")
        os.symlink(src, os.path.join(seq, f"{i:05d}" + os.path.splitext(src)[1]))
    if missing:
        sys.exit(f"missing rendered frames: {missing[:20]} ... ({len(missing)})")
    cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", "30", "-start_number", "1",
           "-i", os.path.join(seq, "%05d.png"), "-i", REF1,
           "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k",
           "-vf", "scale=1080:1920:flags=lanczos,format=yuv420p",
           "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high",
           "-movflags", "+faststart", "-shortest", out]
    subprocess.run(cmd, check=True)
    print(out)


if __name__ == "__main__":
    main()
