# AIRA expo reels: Week 1 sample batch (4 Reels)

Four vertical Reels (1080×1920, 30 fps, H.264, under 30 s) for AIRA Womenswear's
Instagram and Facebook. They are cut from the client's raw expo footage in the style
of the client's reference video, and follow the "AIRA Master Reels Editing SOP".

| # | reel | concept | length | music |
|---|---|---|---|---|
| 1 | **Step inside AIRA** | expo recap closest to the reference: shop, products, people | 24.9 s | Winter Breeze, Arulo |
| 2 | **The details make the difference** | embroidery, necklines, AIRA tags, packaging | 22.4 s | House 02, Lily J |
| 3 | **From daywear to evening** | daywear looks vs evening looks | 22.7 s | Hazy After Hours, Alejandro Magaña |
| 4 | **Print or embroidery?** | the two AIRA campaign looks and pieces from the rails | 21.8 s | Cat Walk, Arulo |

Deliverables are in `final/Week01/`: MP4, caption and thumbnail for each reel, plus the
delivery tracker, the music licence log and delivery notes. The reference analysis is
in `docs/REFERENCE_ANALYSIS.md`.

## What each reel takes from the reference

- **Opening.** The film-gate light band opens into a smeared, over-exposed first shot.
  The music fades in at 0.3 s.
- **Grade.** The reference's warm grade is measured from matched frames and applied as
  a 3D LUT, with the reference's vignette and fine grain.
- **Transitions.** Light-leak burn, photo card, whip pans, zoom blur, echo stutter and
  the 5-frame B&W halftone beat flash. Cuts land on the beat.
- **Ending.** The AIRA wall, then the flare streak across the letters (with a hit on the
  music), the eclipse ring, the AIRA logo card in silence, and a fade to black.

## Rebuild

Needs Python 3 with `numpy opencv-python-headless pillow librosa`, and ffmpeg 6.

```
# camera originals: raw/ (or AIRA_RAW=/path/one:/path/two), named C0001.MP4 ...
python3 reels/r1_event.py --table          # timeline only
python3 reels/r1_event.py --preview        # quick half-size preview from proxies (proxy/)
python3 reels/r1_event.py                  # final -> out/R01_Step_Inside_AIRA.mp4
python3 reels/thumbs.py                    # covers -> out/R0n_thumbnail.jpg
python3 tools/qc.py out/R0*_*.mp4          # technical QC table
python3 tools/deliver.py                   # copy to final/Week01 + tracker + licence log
```

The Mixkit tracks are downloaded on first use (see `audio/tracks.json`) and are not
stored in the repo.

## How it fits together

| path | what |
|---|---|
| `engine/reelkit.py` | compositor: decoding with the grade LUT, 9:16 reframing, slow motion with frame blending, transitions, effects, logo card, text, finishing, encode |
| `engine/audio.py` | music and SFX mix in the reference's shape, two-pass loudness to -14 LUFS / -1 dBTP |
| `reels/r1…r4_*.py` | one script per reel: the shot plan (beats per shot, source clip, in-point, speed, framing keys, transition), the hook and the styling tip |
| `reels/common.py` | beat grid → cut times, text styles, the reference's logo-reveal audio, build CLI |
| `reels/thumbs.py` | cover thumbnails |
| `assets/` | reference-matched LUT, traced AIRA logo (SVG, PNG, polygons), Jost font (OFL) |
| `audio/tracks.json` | track metadata and licence, plus the fitted beat grids |
| `tools/` | Drive zip range reader, prefix rebuild, proxies, contact sheets, LUT fitting, logo tracing, QC, delivery |

## Footage notes

The Drive folder holds one 25 GB zip of 142 clips (Sony A7S III, 1080p at 100 fps).
All 142 clips were read, and a review proxy and contact sheets were made for each.
Later, Google Drive started refusing downloads of the zip ("quota exceeded: too many
users have viewed or downloaded this file recently"). Eight full-resolution originals
were never fetched: C0123, C0124, C0125, C0126, C0128, C0131, C0139, C0142. They hold
the rust-kurta guest, a close shot of the navy-kurta guest, and the dusty-rose and
bridal-red saree looks.

Each reel script uses `pick(primary, fallback, clip, seconds)`. When an original is
missing, a pre-chosen alternative from footage on disk is used, and every reel still
shows at least two complete looks. Once the originals are in `raw/`, re-running the
scripts swaps the planned shots back in. `tools/rebuild_prefix.py` can also rebuild
just the first seconds of a clip from a partial download.
