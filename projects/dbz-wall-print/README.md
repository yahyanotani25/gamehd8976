# Dragon Ball mural: wall printer edit

A 12.8-second vertical video (1080×1920, 30 fps). The client's wall printer
(the one in **reference 1**) prints the client's Dragon Ball image across the
whole wall. The shots follow **reference 2** in the same order, with the same
cut points.

Final files are in `final/`:

| file | what |
|---|---|
| `DBZ_Wall_Printer.mp4` | the finished edit |
| `mural_flat_print_file.jpg` | the client's image made flat (perspective removed): exactly what goes on the wall |

## How it is made

No AI video or image generation is used. Every frame is the real footage of
the printer from reference 1. The old balloon print on its wall is replaced
with the client's image by planar tracking and compositing, so every face and
line on the wall comes straight from the client's pixels.

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
3. **Print head** (`scripts/head.py`). The printer's violet UV light is found
   in every frame and mapped onto the wall. The printed area follows it: in
   the time-lapse wide shots it follows the tower along the rail, and in the
   close-ups it follows the head up or down its column.
4. **Composite** (`scripts/composite.py`). The image goes onto the wall as
   ink on white. It is multiplied by the room light measured from the bare
   wall in the same frame, including the shadows of the head and tower on the
   strip being printed. The printer, its cables, its screen and the UV light
   stay in front.
5. **Edit** (`scripts/segments.py`, `scripts/assemble.py`). The shots are cut
   to reference 2's timing. The sound is reference 2's audio track.

| # | time | reference 2 shot | taken from reference 1 |
|---|---|---|---|
| 1 | 0.00–2.23 | wide, printer finishing Piccolo | time-lapse wide, frames 34–100 |
| 2 | 2.23–4.00 | close-up, head printing Goku's face | close-up, frames 335–387 (head going down) |
| 3 | 4.00–5.97 | wide, printing goes on | far wide, frames 470–528 |
| 4 | 5.97–8.03 | close-up, next figure (Vegeta) | close-up, frames 180–241 (head going up) |
| 5 | 8.03–9.90 | close-up (Buu) | close-up, frames 388–443 |
| 6 | 9.90–11.13 | detail of finished print | moving camera, frames 830–866 |
| 7 | 11.13–12.75 | finished wall | far wide, frames 540–588 |

The mural runs from just under the cornice to just above the floor. Its
position along the wall is chosen for each shot so that the figure being
printed is under the head. A real print of a wall this long takes hours,
with the printer moving along its rail.

## Limits

- The client's image is small: the photo inside the screenshot is 738×484
  px. Wide shots look sharp, but the close-ups magnify it about 13× and look
  soft. A larger original of the same photo would fix this; re-run
  `art.py build` and the render.
- Reference 1's camera stands close to a tall, narrow wall. At full wall
  height, no single shot can show the whole mural, which is about 2.16 times
  as wide as it is tall. The wide shots show about a third of it at a time.

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
for s in s1_wide s2_goku s3_wide s4_vegeta s5_buu s6_detail s7_final; do python3 composite.py $s; done
python3 assemble.py ../final/DBZ_Wall_Printer.mp4             # --audio ref1|none to change the sound
```

QA tools: `check.py` draws the tracked wall grid, `checker.py` makes a
checkerboard of frame vs. texture, and `qa.py` scores alignment.

The sound effects in `/sfx` were not used. Reference 2's own track already
carries the edit.
