#!/usr/bin/env bash
# Finish the film: 60 fps master -> 30 fps with a 180-degree shutter (each
# output frame blends two 60 fps frames: natural motion blur), light
# sharpening, BT.709 H.264 High (tune film: keeps the grain), muxed with the
# soundtrack when one exists.
#   render/finish.sh out/master60.mkv out/mix.wav out/final.mp4
# (a 30 fps master is also accepted: used as is, no shutter blend)
set -euo pipefail
master=${1:-out/master60.mkv}
mix=${2:-out/mix.wav}
final=${3:-out/final.mp4}
crf=${CRF:-15}
fps=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$master")
blur=""
[ "$fps" = "60/1" ] && blur="tmix=frames=2:weights='1 1',fps=30,"
vf="[0:v]format=gbrp,${blur}unsharp=5:5:0.25:5:5:0,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setsar=1[v]"
audio=()
if [ -f "$mix" ]; then
  audio=(-i "$mix")
  amap=(-map 1:a -c:a aac -b:a 320k -ar 48000 -shortest)
else
  echo "finish: no $mix, video only"
  amap=(-an)
fi
ffmpeg -hide_banner -loglevel error -stats -y -i "$master" "${audio[@]}" \
  -filter_complex "$vf" -map "[v]" "${amap[@]}" \
  -c:v libx264 -profile:v high -preset slow -crf "$crf" -tune film -pix_fmt yuv420p \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -movflags +faststart "$final"
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate,pix_fmt -of compact "$final"
