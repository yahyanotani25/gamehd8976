"""Force-align the script's words to the voice-over -> data/words.json.

Uses torchaudio's MMS forced aligner, which takes romanised text, so the
Roman Urdu script aligns directly.

    pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cpu
    python audio/align.py data/vo.mp3 data/script.txt data/words.json
"""
import json
import re
import subprocess
import sys

import numpy as np
import torch
import torchaudio

audio_path, script_path, out_path = sys.argv[1:4]
words = open(script_path, encoding='utf-8').read().split()
norm = [re.sub(r"[^a-z]", "", w.lower()) for w in words]
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', audio_path, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                     capture_output=True, check=True).stdout
wav = torch.from_numpy(np.frombuffer(raw, dtype=np.float32).copy()).unsqueeze(0)
bundle = torchaudio.pipelines.MMS_FA
model = bundle.get_model(with_star=False)
with torch.inference_mode():
    emission, _ = model(wav)
spans = bundle.get_aligner()(emission[0], bundle.get_tokenizer()(norm))
ratio = wav.size(1) / emission.size(1) / 16000
res = []
for w, sp in zip(words, spans):
    score = float(sum(x.score * len(x) for x in sp) / sum(len(x) for x in sp))
    res.append({'word': w, 'start': round(sp[0].start * ratio, 3), 'end': round(sp[-1].end * ratio, 3), 'score': round(score, 3)})
json.dump(res, open(out_path, 'w'), indent=1)
print(f'{len(res)} words -> {out_path}')
