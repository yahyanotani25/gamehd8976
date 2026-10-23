#!/usr/bin/env bash
# Finish the film: 60 fps master -> 30 fps with a 180-degree shutter
# (each output frame blends two 60 fps frames: natural motion blur), light
# sharpening, H.264 + AAC with the mastered soundtrack. No added grain: on
# white paper it costs ~10x the bitrate and platforms smear it into blocks.
#   render/finish.sh out/master60.mkv out/mix.wav out/final.mp4
# (a 30 fps master is also accepted: faster to render, no shutter blur)
set -euo pipefail
master=${1:-out/master60.mkv}
mix=${2:-out/mix.wav}
final=${3:-out/final.mp4}
fps=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$master")
# a 60 fps master gets the 180-degree-shutter blend; a 30 fps one is used as is
blur=""
[ "$fps" = "60/1" ] && blur="tmix=frames=2:weights='1 1',fps=30,"
ffmpeg -hide_banner -loglevel error -stats -y -i "$master" -i "$mix" \
  -filter_complex "[0:v]format=gbrp,${blur}format=yuv444p,unsharp=5:5:0.35:5:5:0,format=yuv420p,setsar=1[v]" \
  -map "[v]" -map 1:a -c:v libx264 -profile:v high -preset slow -crf 16 -tune animation \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart "$final"
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate -of compact "$final"
