import sys, json, time
import numpy as np
from scipy.io import wavfile
from faster_whisper import WhisperModel
src, out, model_name = sys.argv[1], sys.argv[2], sys.argv[3]
t0 = time.time()
sr, x = wavfile.read(src)
assert sr == 16000
audio = x.astype(np.float32) / 32768.0
model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=3)
segments, info = model.transcribe(audio, language="en", word_timestamps=True, beam_size=5, vad_filter=False,
                                  condition_on_previous_text=True)
res = []
for s in segments:
    res.append(dict(start=s.start, end=s.end, text=s.text.strip(),
                    words=[dict(w=w.word, s=w.start, e=w.end, p=w.probability) for w in (s.words or [])]))
    print(f"[{s.start:7.2f} - {s.end:7.2f}] {s.text.strip()}", flush=True)
json.dump(dict(model=model_name, duration=info.duration, segments=res), open(out, "w"), indent=1)
print("done in", time.time() - t0, flush=True)
