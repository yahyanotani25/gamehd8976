import sys, json, numpy as np
from scipy.io import wavfile
from faster_whisper import WhisperModel
W = sys.argv[1]
P = json.load(open(W + "/work/recut_plan.json"))
sr, B = wavfile.read(W + "/work/recut/audio_recut.wav")
mono = B.mean(1).astype(np.float32)
# resample 48k -> 16k (simple decimation after a low-pass is fine for ASR)
from scipy.signal import resample_poly
m16 = resample_poly(mono, 1, 3).astype(np.float32)
model = WhisperModel("medium.en", device="cpu", compute_type="int8", cpu_threads=4)
shift = 0.0
for p in P:
    j = p["a0"] - shift          # join position in the new timeline
    s0, s1 = max(0, j - 7), j + 7
    seg = m16[int(s0 * 16000):int(s1 * 16000)]
    segs, _ = model.transcribe(seg, language="en", beam_size=5, word_timestamps=False, vad_filter=False)
    txt = " ".join(x.text.strip() for x in segs)
    print(f"Ch{p['ch']} join at new {int(j // 60)}:{j % 60:05.2f}  heard {s0:.1f}-{s1:.1f}s: {txt}", flush=True)
    shift += p["a1"] - p["a0"]
