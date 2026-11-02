# DBZ wall print — wall-printer promo, art floor to ceiling

A 30-second vertical video (720×1280, 30 fps) of the vertical wall printer
printing a Dragon Ball Z mural. It is the client's reference video (the
same machine printing a hot-air-balloon mural) with the balloon print
replaced, frame by frame, by the Dragon Ball Z art from the client's photo.

## Why this version exists

An earlier edit by another editor placed the whole mural as a small strip in
the middle of the wall, leaving bare white wall above and below it. The
client's voice note (`data/client_voice_note.md`) asks for the art to cover
the wall **from the floor up to the ceiling**, with the machine printing it.

This version:

- covers the wall from the bottom of the ceiling trim down to the floor, with
  no white band above or below, in every shot;
- follows the machine: in each frame the art is printed exactly up to where
  the reference printer had printed, so the print head is always at the edge
  of the fresh print (opening timelapse, close-up, wide timelapse), and the
  mural is complete in the final shot;
- keeps the machine, its cables, the rails and the UV lamp in front of the
  art, and carries the room's light, the machine's shadows and the lamp glow
  onto the new print;
- uses the reference soundtrack unchanged, so the cuts stay on the music.

At floor-to-ceiling size the mural (about 2.45:1) is wider than the stretch
of wall the camera sees, so the visible part is Piccolo, Super Saiyan Goku
(centre) and Super Saiyan Vegeta. `MURAL_CENTER` (default `0.46`, a fraction
of the mural's width) slides the mural left or right. The print does not
stretch or squash the art.

The client approved the edit and asked to remove 4–9 s, where the start of
the close-up looked like paper lifting off the wall. The delivered video
skips 4.37–9.9 s of the edit (frames 131–296). That is exactly 16 beats of
the 172 BPM soundtrack, so the music carries on in rhythm. There is a 10 ms
fade at the audio join. To rebuild it from the frames:

```
ffmpeg -framerate 30 -i work/frames/%04d.png -framerate 30 -start_number 297 -i work/frames/%04d.png \
  -i reference/reference.mp4 -filter_complex "[0:v]trim=end_frame=131,setpts=PTS-STARTPTS[v0];\
[1:v]setpts=PTS-STARTPTS[v1];[v0][v1]concat=n=2:v=1:a=0[v];\
[2:a]atrim=end=4.366667,asetpts=PTS-STARTPTS,afade=t=out:st=4.356667:d=0.01[a0];\
[2:a]atrim=start=9.9,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.01[a1];[a0][a1]concat=n=2:v=0:a=1[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -crf 16 -pix_fmt yuv420p -c:a aac -b:a 192k final/DBZ_Wall_Print_final.mp4
```

Seven single frames in the two timelapses showed people walking through
(frames 21, 30, 52, 60, 599, 608, 609). Each is replaced by the frame before
it.

## Files

| path | what |
|---|---|
| `final/DBZ_Wall_Print_final.mp4` | **the delivered video** (24.3 s): the approved edit with 4.37–9.9 s cut out |
| `final/DBZ_Wall_Print.mp4` | the approved edit before the cut (29.9 s) |
| `art/source_photo.jpg` | the client's photo of the mural (input) |
| `art/dbz_mural_print_file.jpg` | the mural as a flat print file: perspective removed, 4× anime upscale (Real-ESRGAN x4plus_anime_6B), photo lighting flattened (5874×2400) |
| `data/H_all.npy` | per-frame homography, wall space → frame (896 × 3 × 3) |
| `data/front_*.txt` | measured print edge of the reference, per frame, in wall units |
| `data/src.npy`, `data/Fref.npy`, `data/Fdbz.npy` | frame substitutions, reference print edge, DBZ print edge |
| `data/wipe_strips.json` | the transition into the final shot: bars and per-strip take evidence, per frame |
| `data/client_voice_note.md` | transcript and translation of the client's feedback |
| `scripts/` | the pipeline (below) |
| `build.sh` | runs everything |

## Rebuild

Needs Python 3 with `numpy scipy opencv-contrib-python-headless`, plus
`torch` (CPU is fine) and `spandrel` for the upscale, and ffmpeg and
ImageMagick. Put the reference video at `reference/reference.mp4` (not
committed), then:

```
./build.sh          # everything (~1 h on 4 cores)
./build.sh render   # reuse the committed tracking data; plates + render only
```

Intermediate files go to `work/` (ignored).

## How it works

1. **Wall space.** Frame 1 is rectified from its vanishing points (ceiling
   trim, rails, tower). A 1.2° shear makes the tower vertical, so the print
   swaths line up with the machine. In this space, 1 unit is about 1 px of
   frame 1. The wall runs from y = 200 (bottom of the ceiling trim) to
   y = 1123 (floor).
2. **Tracking** (`tracker.py`). Each frame is matched with SIFT against a view
   of the balloon print synthesised from the previous frame's pose, then
   solved with RANSAC. This gives one homography per frame, and all five
   sections (opening timelapse, close-up, wide timelapse, move past the
   tower, final) share the same wall coordinates.
3. **Print edge** (`front2.py`, `timeline.py`). Per frame, wall columns are
   classified as printed or bare by comparing colour against the finished
   balloon print. The result is median-filtered and kept monotonic within each
   timelapse.
4. **Lighting and matte** (`albedo2.py`, `cleanplate.py`, `compositor.py`).
   For each section, a temporal-median clean plate of the balloon print gives
   the expected wall appearance. The ratio between the frame and that plate
   gives the light on the wall (luminance in fine detail, colour coarse).
   Pixels much darker than expected, and connected to dark seeds, are the
   machine and stay in front.
5. **Composite.** The mural is warped into each frame with the same
   homography, motion-blurred over a 180° shutter when the camera moves, lit
   with the measured light, and grain-matched. Anything the reference printed
   beyond the DBZ print edge is repainted as bare wall.
6. **The transition into the final shot** (frames 632–674, `wipe_strips.py`).
   The reference cuts from the wide timelapse to the final shot with a
   rotating-panel wipe: black bars sweep across the frame, and each strip
   between two bars shows either the wide take or the final take. For each
   frame and strip, `wipe_strips.py` measures which take's wall pose explains
   the strip. A strip that is ambiguous (mostly the tower) keeps the take it
   had in the previous frame. Each take is rendered with its own pose and
   lighting, and the two are joined behind the bars. Panels that are closing
   show the old take turned and blurred, so they get broad, smooth lighting
   instead of per-pixel lighting.
