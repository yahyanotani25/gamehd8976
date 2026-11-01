#!/usr/bin/env bash
# Rebuild "DBZ wall print" from the reference video and the client's mural photo.
#   build.sh            full pipeline (tracking takes ~15 min, render ~20 min on 4 cores)
#   build.sh render     reuse the committed tracking/timeline data, only build plates + render
# Inputs:  reference/reference.mp4  (the balloon-mural reference, 720x1280)
#          art/source_photo.jpg      (the client's Dragon Ball Z mural photo)
# Output:  final/DBZ_Wall_Print.mp4
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SC="$HERE/scripts"; W="$HERE/work"; PY="${PYTHON:-python3}"
mkdir -p "$W"/{ref_full,track,comp,art,models}
cp "$HERE/art/source_photo.jpg" "$W/art/src.jpg"
[ -f "$W/ref_full/0896.png" ] || ffmpeg -v error -i "$HERE/reference/reference.mp4" -vsync 0 -q:v 1 "$W/ref_full/%04d.png"

# --- the mural as a flat print file (perspective-corrected, 4x anime upscale, lighting flattened)
if [ ! -f "$W/art/mural_albedo.png" ]; then
  [ -f "$W/models/RealESRGAN_x4plus_anime_6B.pth" ] || curl -sSL -o "$W/models/RealESRGAN_x4plus_anime_6B.pth" \
    https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth
  convert "$W/art/src.jpg" -crop 738x460+0+545 +repage "$W/art/src_crop.png"
  "$PY" "$SC/upscale.py" "$W/models/RealESRGAN_x4plus_anime_6B.pth" "$W/art/src_crop.png" "$W/art/src_crop_x4.png"
  "$PY" "$SC/art_rectify4.py" "$W"
  "$PY" "$SC/mural_albedo.py" "$W"
fi

if [ "${1:-}" != "render" ]; then
  # --- wall space: rectify frame 1, link the shots, build a wall plate
  "$PY" "$SC/rectify0.py" "$W" 1024
  "$PY" "$SC/test_pairs.py" "$W"
  "$PY" "$SC/anchors.py" "$W"
  "$PY" "$SC/plate.py" "$W"; "$PY" "$SC/plate2.py" "$W"
  # --- per-frame homographies (wall -> frame), one run per shot
  ( cd "$W/track"
    "$PY" "$SC/tracker.py" "$W" 559 640 559 & "$PY" "$SC/tracker.py" "$W" 559 452 559 &
    "$PY" "$SC/tracker.py" "$W" 799 895 799 & "$PY" "$SC/tracker.py" "$W" 799 641 799 & wait
    "$PY" "$SC/tracker.py" "$W" 0 130 0 v2 & "$PY" "$SC/tracker.py" "$W" 451 131 451 v2 & wait ) > "$W/track/tracker.log"
  "$PY" "$SC/merge_track.py" "$W"
  # --- where the reference printer has printed up to, per frame
  "$PY" "$SC/front2.py" "$W" 0 130   > "$W/track/front_open.txt"
  "$PY" "$SC/front2.py" "$W" 131 290 > "$W/track/front_close1.txt"
  "$PY" "$SC/front2.py" "$W" 291 451 > "$W/track/front_close2.txt"
  "$PY" "$SC/front2.py" "$W" 452 640 > "$W/track/front_wide.txt"
  "$PY" "$SC/front2.py" "$W" 641 760 > "$W/track/front_fin1.txt"
  "$PY" "$SC/timeline.py" "$W"
  # --- the rotating-panel transition into the final shot: which take each strip between the bars shows
  "$PY" "$SC/wipe_strips.py" "$W" 628 676 > "$W/comp/wipe_strips.log"
else
  cp "$HERE/data/H_all.npy" "$HERE/data/Wc2W.npy" "$W/track/"
  cp "$HERE"/data/front_*.txt "$W/track/"
  cp "$HERE/data/src.npy" "$HERE/data/Fref.npy" "$HERE/data/Fdbz.npy" "$HERE/data/wipe_strips.json" "$W/comp/"
  [ -f "$W/track/plate2.png" ] || { for k in 0 559 799 895; do cp "$HERE/data/anchor_$k.npy" "$W/track/"; done; "$PY" "$SC/plate2.py" "$W"; }
fi

# --- balloon-print albedo + per-shot clean plates (for the lighting transfer and the matte)
"$PY" "$SC/albedo2.py" "$W"
"$PY" "$SC/cleanplate.py" "$W" open  97:130:1  -300,575,195,1128 1.25 0.07
"$PY" "$SC/cleanplate.py" "$W" close 131:451:4 230,610,200,1123  3.0  0.07
"$PY" "$SC/cleanplate.py" "$W" wide  600:646:1 100,872,195,1128  1.0  0.07
"$PY" "$SC/cleanplate.py" "$W" final 680:895:3 230,1030,150,1123 2.0  0.06

# --- composite every frame, then encode with the reference soundtrack
"$PY" "$SC/render_all.py" "$W" "$W/frames" 4
mkdir -p "$HERE/final"
ffmpeg -v error -y -framerate 30 -i "$W/frames/%04d.png" -i "$HERE/reference/reference.mp4" \
  -map 0:v -map 1:a -c:v libx264 -preset slow -crf 16 -profile:v high -pix_fmt yuv420p \
  -c:a copy -shortest -movflags +faststart "$HERE/final/DBZ_Wall_Print.mp4"
echo "wrote $HERE/final/DBZ_Wall_Print.mp4"
