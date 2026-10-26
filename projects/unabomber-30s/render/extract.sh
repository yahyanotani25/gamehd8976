#!/usr/bin/env bash
# Extract a clip to a JPEG image sequence for kit.videoPlane / media.video.
#   render/extract.sh <clip.mp4> <name> [start_s] [dur_s] [fps] [max_width]
# Writes out/frames/<name>/00001.jpg ... (q 2, near-lossless) and
# out/frames/<name>/meta.json { name, fps, count, width, height, source, start, duration }.
# fps defaults to the clip's own rate (keep it: speed ramps resample in the
# engine; slow motion below ~50 % needs interpolated frames, see STYLE.md).
set -euo pipefail
clip=${1:?clip}; name=${2:?name}; start=${3:-0}; dur=${4:-}; fps=${5:-}; maxw=${6:-1920}
cd "$(dirname "$0")/.."
dir=out/frames/$name
rm -rf "$dir"; mkdir -p "$dir"
src_fps=$(ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate -of csv=p=0 "$clip")
[ -z "$fps" ] && fps=$(python3 -c "from fractions import Fraction as F; print(float(F('$src_fps')))")
vf="fps=$fps,scale='min($maxw,iw)':-2:flags=lanczos,format=yuvj444p"
args=(-hide_banner -loglevel error -y -ss "$start")
[ -n "$dur" ] && args+=(-t "$dur")
ffmpeg "${args[@]}" -i "$clip" -vf "$vf" -q:v 2 -qmin 1 -start_number 1 "$dir/%05d.jpg"
count=$(ls "$dir" | grep -c '\.jpg$')
read -r w h < <(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=' ' "$dir/00001.jpg")
cat > "$dir/meta.json" <<JSON
{ "name": "$name", "fps": $fps, "count": $count, "width": $w, "height": $h, "source": "$clip", "start": $start, "duration": ${dur:-null}, "url": "/out/frames/$name" }
JSON
echo "extracted $count frames ${w}x${h} @ ${fps} fps -> $dir"
