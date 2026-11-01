# Meganeura documentary — dark shots replaced

The client sent back the finished 15:22 documentary about the giant griffinfly
(*Meganeura*) with 23 phone recordings and one photo of the parts they wanted
fixed: shots that were too dark, or murky and badly lit. This project swaps
those shots for bright, well-lit visuals that match the narration, and leaves
everything else alone: narration, music, motion graphics, title animations and
on-screen labels are untouched.

- Original: the finished render (1920×1080, 25 fps, 921.96 s, H.264 + AAC)
- Client notes: 22 phone recordings `clip_01`–`clip_23` and one photo (`clip_18.jpg`)

The client's material — their film, the recordings, the narration transcript,
the shot list that quotes it, and before/after frames — is **not** in this
public repo; it was delivered privately. `.gitignore` keeps those paths out.
The finished video is described under *Output* below.

## What changed

`scripts/shotlist.py` writes the full shot list (timecode, narration, new
visual, source link) from the transcript; it was delivered privately. In short:

- **66 shots** sat inside the client's recorded ranges. **62** were replaced,
  **1** (the Chapter 3 title) was re-lit, and **3** that were already bright
  and clean were kept: the hand on the shale (2:58.4), the griffinfly over
  the water, seen from above (12:44.8), and the red earth bank with pines (14:49.4).
  In all, 6,883 frames (4 min 35 s of the 15:22 film) are new; every other
  frame is the original.
- New visuals are 51 HD/4K stock clips from Pexels (rainforest and Amazon
  aerials, swamps, mangroves, ferns, modern dragonflies, wildfire, dry land,
  rock strata) and, where no real footage can show the subject, 10 AI stills
  (giant griffinflies, the Carboniferous swamp, the fossil wing). The stills
  are slowly pushed in (Ken Burns), as documentaries usually treat stills.
  Shots are reframed where needed to keep man-made things (a fence, a sawn
  log, a mast, farm plots) out of a prehistoric story.
- **Chapter titles 1, 2, 5, 6, 7** keep their original animation; only the
  near-black plate behind them is replaced with a dimmed, softly defocused
  shot that fits the chapter, so the text stays easy to read.
- **Chapter 3** sits on the same Earth shot as before; the editor had dimmed
  it to about 35% under the title. That dimming is mostly undone (mean
  brightness about 25 → 45) and the text keeps its contrast through a soft
  local shadow.
- **Labels on replaced shots** (six of them, including the flight-data HUD
  and a full-screen statement) are lifted from the original frame by frame
  (so their fades and typing animations are exact) and composited over the
  new picture. Because the new pictures are much brighter, each label gets a
  soft dark shadow that follows the text as it appears, so it stays readable.
- **Cuts and dissolves** are frame-exact: every dissolve uses the blend curve
  measured from the original, and the opening keeps its fade from black.
- **Audio is copied bit for bit** from the original.

## How it was built

All scripts take the working directory `W` as their first argument; they read
`W/dl/` (downloads) and write `W/work/`.

1. `match_audio.py` finds where each phone recording sits in the original by
   cross-correlating spectrogram bands (all 22 recordings matched with z > 8).
   `clip_18.jpg` is a photo of the paused player at 2:35 / 15:22 (the Chapter 2
   title), covering the gap between `clip_19` and `clip_17`.
2. `analyze_frames.py`, `shots.py`, `boundaries.py` measure brightness per
   frame and find every cut and dissolve (to the frame).
3. `transcribe.py` (faster-whisper medium.en) gives the narration with word
   timings, so each replacement matches what is being said (the transcript
   stays private).
4. `detect_overlays.py` and `overlay_masks.py` find on-screen text and build
   per-overlay stroke masks and colour maps.
5. `pxsearch.py` / `pxsheet.py` / `pxdl.py` search and fetch Pexels footage
   (metadata from the public `jovianzm/Pexels-400k` dataset); `horde2.py`
   generates the AI stills on Stable Horde (prompts in `data/ai_jobs4.json`).
6. `slots.py` (what to replace) + `plan.py` (what goes there) → `render.py`
   renders each slot: conform to 25 fps, exposure grade to a mean luma of about
   100 with a gentle S-curve and vignette, Ken Burns for stills, text
   composited back from the original, dissolves rebuilt.
7. `splice.py` drops the rendered slots into the untouched original frames and
   encodes once (x264 CRF 17, BT.709), copying the audio.
8. `review_all.py` makes the before/after sheets (delivered privately), and
   `verify.py` checks the master against the original (frame count, audio
   identity, untouched frames, brightness per slot).

## Output

`Documentary_bright_visuals_v2.mp4`: 1920×1080, 25 fps, 23,048 frames,
H.264 High (CRF 17, 11.6 Mbit/s, 1.34 GB), original AAC audio. `verify.py`
(see `data/verify.log`) confirms the audio packets are bit-identical to the
original and every frame outside the replaced shots matches it (PSNR ≥ 46.8 dB).

It is too large for git, and the chat's 400 MB transfer limit meant it was
delivered as:

- `Documentary_bright_visuals_v2_part1_of_4.mp4` … `part4_of_4.mp4`: the
  full-quality master cut at keyframes (stream copy, nothing re-encoded;
  rejoined, all 23,048 decoded frames and the audio match the master exactly).
  Put them back to back on a timeline, or join them with
  `ffmpeg -f concat -safe 0 -i list.txt -c copy Documentary_bright_visuals_v2.mp4`,
  where `list.txt` lists the four files, one `file '<name>'` per line
  (or use LosslessCut → Merge/concatenate files). A smaller re-encoded single
  file was dropped in favour of the full-quality master.

To rebuild from scratch, download the original and the stock clips named in
`scripts/plan.py` (`px<id>` = https://www.pexels.com/video/<id>/) into `W/dl/`,
then run the steps above.

## Sources and licences

- Stock footage: 51 Pexels clips (free to use, no attribution required); the
  IDs are in `scripts/plan.py` (`px<id>` → https://www.pexels.com/video/<id>/).
- AI stills: Stable Horde, models ICBINP XL and FLUX.1-schnell
  (`assets/ai/`, prompts in `data/ai_jobs4.json`).
