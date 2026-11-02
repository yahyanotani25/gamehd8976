# Dragon Ball mural: wall printer edit

Reference 1 (the client's own wall-printer video) frame for frame, 29.9 s,
1080×1920, 30 fps, with its own sound. The balloon artwork it prints is
replaced by the client's Dragon Ball image. Every shot, every camera move,
the people walking past, the stripe transition and the reveal are the
original footage. Only the picture on the wall is new, and it is printed
exactly where and when the balloons were.

Final files are in `final/`:

| file | what |
|---|---|
| `DBZ_Wall_Printer.mp4` | the finished video |
| `mural_flat_print_file.jpg` | the client's image made flat (perspective removed): exactly what goes on the wall |

## How it is made

No AI video or image generation is used. Every face and line on the wall
comes straight from the client's pixels.

1. **Flat print file** (`scripts/art.py`). The client's image is a phone
   screenshot of a photo taken at an angle. The main wall is cropped out and
   upscaled 4× with Lanczos and an unsharp mask. Its perspective is undone
   using the ceiling line, the skirting, the left wall edge and the pillar.
   The real width:height ratio (2.16:1) is measured from the views of the
   same mural in reference 2, so nobody gets stretched. The room's light is
   divided out so the wall white prints as white.
2. **Wall tracking** (`scripts/track.py`). Each frame of reference 1 is
   matched against one flattened wall texture (the "master"), which is
   re-projected into the predicted view. This uses SIFT with MAGSAC, then ECC
   for sub-pixel accuracy. Matching every frame to the same texture means
   there is no drift. Frame to frame, the residual against the real wall is
   0.05–0.85 px (median) across the shots.
3. **Placement** (`scripts/composite2.py`). The whole image sits where the
   balloon print was. It is as large as it can be while the widest shot
   still shows all of it, from Frieza to Goku Black. Its height follows from
   its own 2.16:1 proportions.
4. **Print progress** (`scripts/head.py`, `scripts/progress.py`). The
   printer's violet UV light is found in every frame and mapped onto the
   wall. In the time-lapse wide shots, everything left of the head's column
   is printed, as in the footage. In the low-angle close-up, a faint
   first-pass strip (about 35% ink, measured) runs beside the head, as in
   the footage. From the reveal on, everything is printed.
5. **Composite** (`scripts/composite2.py`). The old balloon print is wiped
   off the wall. The room's light on the wall is measured from the bare wall
   and through the old print, and the image is put on as ink on white under
   that light, with the shadows of the head and tower. The printer, its
   cables, its screen, the UV light and the people walking past stay in
   front; passers-by are found against the nearest frames without them.
6. **Transition** (`scripts/wipe.py`). Frames 633–677 are a stripe wipe made
   of skewed copies of the last wide frame and the first reveal frame. Each
   panel's homography is found and chained with the wall track, then the
   panel is rendered like any other frame.
7. **Assembly** (`scripts/assemble2.py`). All 897 frames go out in order,
   with reference 1's audio.

An earlier cut followed reference 2's shot order (`segments.py`,
`composite.py`, `assemble.py`). Its code is kept, but it is not the
delivered version.

## Limits

- The client's image is small: the photo inside the screenshot is 738×484
  px. At this size on the wall it stays sharp in every shot. A larger
  original of the same photo would make it sharper still; re-run
  `art.py build` and the render.
- Reference 1's wall is tall and narrow, while the mural is about 2.16 times
  as wide as it is tall. Showing all of it in the wide shots means it covers
  the middle of the wall, not floor to ceiling. Making it full height would
  push Frieza and Piccolo out of every shot.

## Rebuild

Needs Python 3 with `opencv-python-headless` and `numpy`, plus ffmpeg.
Inputs come from environment variables: `DBZ_REF1`, `DBZ_REF2`, `DBZ_IMG`
and `DBZ_WORK` (the scratch folder; defaults are in `scripts/common.py`).

```bash
cd scripts
mkdir -p "$DBZ_WORK/frames1" "$DBZ_WORK/frames2"
ffmpeg -i "$DBZ_REF1" -q:v 2 "$DBZ_WORK/frames1/%04d.jpg"
ffmpeg -i "$DBZ_REF2" -q:v 2 "$DBZ_WORK/frames2/%04d.jpg"
python3 track.py master0                     # canvas from frame 560
python3 track.py trackE
python3 track.py seed master0 700 100 10
python3 track.py trackshot master0 F 700 seeds_master0.json
python3 track.py trackshot master0 B 100 seeds_master0.json
python3 track.py trackshot master0 A 10 seeds_master0.json
python3 track.py buildmaster master1 tracks_E0.json:8 tracks_F_master0.json:5
python3 track.py seed master1 133 280 350
python3 track.py trackrange master1 seeds_master1.json 133 133 240 D1   # then D2 (280: 241-340), D3 (350: 341-444)
# merge tracks_D1/2/3.json into tracks_D.json
python3 head.py tracks_A_master0.json tracks_B_master0.json tracks_D.json tracks_E0.json tracks_F_master0.json
python3 art.py aspect && python3 art.py build
python3 track.py seed master1 128 449
python3 track.py trackrange master1 seeds_master1.json 128 125 132 C2
python3 track.py trackrange master1 seeds_master1.json 449 445 453 D4
python3 track.py trackrange master0 tracks_B_master0.json 34 18 34 B0
# merge every tracks_*.json into tracks_all.json, then:
python3 head.py tracks_all.json
python3 progress.py
python3 composite2.py 1 897                                   # split into chunks to run in parallel
python3 wipe.py
python3 assemble2.py ../final/DBZ_Wall_Printer.mp4
```

QA tools: `check.py` draws the tracked wall grid, `checker.py` makes a
checkerboard of frame vs. texture, and `qa.py` scores alignment.

The sound effects in `/sfx` were not used, because the video keeps
reference 1's own sound.
