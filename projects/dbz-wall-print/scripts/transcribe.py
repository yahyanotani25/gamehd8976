import sys, numpy as np
from faster_whisper import WhisperModel
audio = np.fromfile(sys.argv[1], dtype=np.float32)
model = WhisperModel("large-v3", device="cpu", compute_type="int8", download_root=sys.argv[2])
for lang, task in [("ur", "transcribe"), ("hi", "transcribe"), ("ur", "translate")]:
    segs, info = model.transcribe(audio, language=lang, task=task, beam_size=5, vad_filter=False)
    print(f"=== {lang} {task}", flush=True)
    for s in segs:
        print(f"[{s.start:5.1f}-{s.end:5.1f}] {s.text}", flush=True)
