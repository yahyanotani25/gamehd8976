#!/usr/bin/env bash
# Build the film (picture is audio-free; the soundtrack out/mix.wav is muxed
# in when present):
#   render/make.sh [workers]
#   1. 60 fps lossless master in N parallel browsers  -> out/master60.mkv
#   2. finish to 30 fps, 180-degree shutter, H.264     -> out/final.mp4
set -euo pipefail
cd "$(dirname "$0")/.."
workers=${1:-3}
node render/render.mjs --fps 60 --workers "$workers" --out out/master60.mkv
render/finish.sh out/master60.mkv out/mix.wav out/final.mp4
