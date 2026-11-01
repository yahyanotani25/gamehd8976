"""Cut the spoken chapter announcements out of the soundtrack.

usage: recut_audio.py W out.wav

Each cut removes exactly as much audio as the matching video cut removes, joined
with an equal-power crossfade (recut_plan.C seconds) centred on the join, inside
the music-only pause, so the score flows on and no other word is touched.
"""
import sys, os, json, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import recut_plan as RP

W, OUT = sys.argv[1], sys.argv[2]
SR = RP.SR
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", W + "/dl/original/original.mp4", "-map", "0:a:0", "-f", "f32le",
                      "-ac", "2", "-ar", str(SR), "-"], capture_output=True).stdout
A = np.frombuffer(raw, np.float32).reshape(-1, 2)
print("original audio", len(A), "samples", len(A) / SR, "s")
P = json.load(open(W + "/work/recut_plan.json"))
half = int(round(RP.C * SR / 2))
t = np.linspace(0, np.pi / 2, 2 * half, dtype=np.float32)[:, None]
fo, fi = np.cos(t), np.sin(t)
parts, pos = [], 0
for p in P:
    a0, a1 = p["a0s"], p["a1s"]
    parts.append(A[pos:a0 - half])
    parts.append(A[a0 - half:a0 + half] * fo + A[a1 - half:a1 + half] * fi)
    pos = a1 + half
parts.append(A[pos:])
B = np.concatenate(parts, 0)
removed = sum(p["a1s"] - p["a0s"] for p in P)
assert len(B) == len(A) - removed, (len(B), len(A), removed)
peak = float(np.abs(B).max())
print("new audio", len(B), "samples", len(B) / SR, "s; removed", removed / SR, "s; peak", round(peak, 3))
# 32-bit float WAV
import wave
with open(OUT, "wb") as f:
    pass
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_f32le", OUT],
               input=B.astype(np.float32).tobytes(), check=True)
print("wrote", OUT)
