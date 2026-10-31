# Client reference: what the edit does, and how the reels copy it

Reference: `WhatsApp Video 2026-10-28 at 2.05.41 AM (1).mp4`. It's a 1280×720, 30 fps, 105.9 s
recap of the AIRA stall at the October 2026 expo (Aloki Convention Center, Dhaka), cut
from the same Sony A7S III footage as these reels. Five of its shots were matched
frame-for-frame to the raw clips: C0004, C0019, C0021, C0040 and C0045.

## Structure

| time | what happens |
|---|---|
| 0.00–0.35 | black, silence |
| 0.10–0.75 | **film-gate opening**: a warm light band on black opens into a horizontally smeared, over-exposed first shot that settles by 0.7 s; music fades in from 0.35 s |
| 0.7–11.4 | intro montage on the beat: exterior hyperlapse → AIRA campaign standee → expo banners → hall → AIRA wall letters → stall → decor details |
| 11.37–11.90 | **logo reveal**: anamorphic flare streak across the AIRA wall letters (4–6 frames, with a hit on the music at 11.30 s), a glitch band, a white bloom with a black disk, a white ring shrinking to a point on black (5 frames), black (4 frames) |
| 11.90–14.5 | **AIRA logo card**: white logo on a wine radial gradient (centre ≈ RGB 76,19,41, corners ≈ 61,14,32), static, **silent** (music fades out 11.75–11.95) |
| 14.5–101 | people, products, shopping, packing, guests, VIPs |
| 101.2–104.8 | final shot: the AIRA wall, slow push |
| 104.8–105.2 | fade to black; music fades 105.4–105.9 |

## Transition vocabulary (all rebuilt in `engine/reelkit.py`)

| transition | reference time | engine |
|---|---|---|
| film-gate opening | 0.1–0.75 | `Tr('gate', 20)` |
| warm light-leak burn, 2–6 frames over-exposed | 1.83, 2.07 | `Tr('burn', n)` |
| photo card: shot shrinks into a white-bordered card, next shot flies in tilted | 3.5–4.2 | `Tr('card', n)` |
| whip pan with motion blur | 6.07, 7.97, 9.22 | `Tr('whip', n, dir=…)` |
| zoom blur | 7.43 | `Tr('zoom', n)` |
| double-exposure "echo" stutter | 8.80 | shot fx `('echo', t0, t1)` |
| B&W halftone beat flash, deep-navy shadows, 5 frames | 10.23–10.37 | shot fx `('bw', t0, t1)` |
| flare → glitch → bloom → eclipse ring → black → logo card | 11.37–11.90 | `Tr('eclipse', 17)` + `Card` |
| fade to black | 104.8 | `Card(fade=…, tail=…)` |

## Look

- **Grade.** A 33³ LUT (`assets/grade/ref_grade.cube`) fitted from about 700,000 pixel pairs:
  raw frames warped onto the matching reference frames, then a 3rd-order colour
  polynomial fitted on the centre region. Error is 2.5–4.4 levels at the centre. The
  result is warm and slightly lifted, with soft highlights and accurate skin tones.
- **Vignette.** Measured from the same pairs: 1.0 within half the radius, 0.94 at 0.7,
  0.82 in the corners.
- **Music.** 117–120 BPM, cuts land on beats, and the logo card is silent.
- **Logo.** Traced from the reference card into vector polygons (`assets/logo/`). Its
  proportions are kept exactly: open Λ shapes without a crossbar, and an open-bowl R.

## Adapting a 16:9 recap to 9:16 reels under 30 s

- Each reel keeps the reference's opening, its transitions, its grade and its
  wall → flare → eclipse → silent logo card → fade-to-black ending. The 2.5 s logo card moves
  from 12 s to the end of the reel, where the client asked for the logo.
- The SOP requires an on-screen hook, a styling tip and at least two complete looks.
  These sit in the safe zones: titles at y ≈ 330–580 px, and nothing in the bottom
  ~400 px or the right-hand button column.
- The 9:16 frames are cropped from the 1920×1080 originals with Lanczos scaling and
  light sharpening. Slow motion uses the 100 fps capture: speed 0.3–0.6, with frame
  blending when a shot plays faster than one stored frame per output frame.
