#!/usr/bin/env bash
# Build the whole film: cues -> soundtrack -> 60 fps render -> finished MP4.
#   render/make.sh [workers]      (PY: python with numpy/scipy/soundfile/pyloudnorm)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python3}
node audio/collect_cues.mjs
(cd audio && $PY sfx.py >/dev/null && $PY music.py)
$PY audio/mix.py --out out/mix.wav
node render/render.mjs --fps 60 --workers "${1:-3}" --out out/master60.mkv
render/finish.sh out/master60.mkv out/mix.wav out/final.mp4
