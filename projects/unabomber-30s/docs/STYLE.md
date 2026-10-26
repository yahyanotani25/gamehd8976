# Style bible — "THE UNABOMBER" cold open (30 s)

16:9, 1920×1080, 30 fps. Rendered by code (Three.js and a DOM overlay in headless
Chromium). This document sets the look, motion, type, sound and rules for the
30-second cold open. The storyboard (`docs/STORYBOARD.md`) decides shot by shot;
when the two disagree, update one of them on purpose.

Supporting images live in `docs/reference/`:

| file | what |
|---|---|
| `reference_frames.jpg` | the owner's reference tutorial (thumbnail plus frames at 25/50/75 %) and three sibling Vane Motion tutorials |
| `title_font_specimen.jpg` | candidate title faces, set in "THE UNABOMBER" |
| `title_mock.jpg` | flat layout of the final title card (sizes as in section 12) |
| `palette.png` | the palette in section 6 |
| `grade_lookdev.jpg` | FBI cabin photos before and after the `wild` and `secret` looks (made with `tools/grade_lookdev.py`) |

---

## 0. The look in six lines

1. **A quiet, cold, beautiful wilderness that turns out to hide something.** The
   film moves from vast, open and cold to small, closed and dark.
2. **Real evidence, real terrain, no fakes.** We use 1996 FBI evidence photos of
   the cabin, USGS elevation data and imagery, and licensed footage. We never
   generate images of real people or places.
3. **Every photograph is alive and three-dimensional.** Stills are rebuilt on depth
   meshes and get drifting snow, smoke, light and parallax.
4. **Two typographic voices.** IBM Plex Mono speaks for the investigators
   (coordinates, measurements, labels). Courier Prime appears only in the
   secret's flashes. The title is set in Archivo Expanded Black.
5. **Colour and frame tell the story.** Cold teal becomes warm umber, which becomes
   black with one red. The 16:9 frame closes to 2.39:1 at the turn.
6. **The soundtrack leads the edit.** Wind and room tone, short bursts of modern
   noise that cut to silence, a tick that speeds up, a suck-out, true silence,
   then a three-layer title hit.

---

## 1. Brief and constraints

- **Running time:** 30.0 s. The voice-over (the owner's file from Google Drive)
  runs from "Imagine living in a remote cabin…" to "…was a secret". The
  "THE UNABOMBER" title slam follows.
- **Timing risk:** the VO is 90 words. At a usual documentary pace (150–160 wpm)
  that is 34–36 s, so this 30 s cut only works if the read is brisk.
  - The title needs at least 2.1 s after its hit, and the silence before it
    needs 10–14 frames, so the VO must end by about 27.6 s.
  - If the aligned VO runs long, first cut pauses longer than 0.35 s down to
    0.2 s. Then allow at most 6 % pitch-preserving time compression. Beyond that,
    the lead or owner decides what to trim; we do not quietly drop words.
- **Tone:** prestige documentary that is serious and restrained, never lurid.
  The full script is careful to separate ideology from violence, and the edit
  must be just as careful (section 16).
- **Platform:** YouTube, monetised. Every asset must be cleared (public domain or
  US federal work, CC0, CC-BY, CC-BY-SA, or the Mixkit licence). Nothing graphic.

---

## 2. The reference, decoded

Owner's reference: Vane Motion, "How to Edit Documentary Style Videos | After
Effects Tutorial" (`5NUhMHzZUAY`, channel `@vanemotion`).

**What we could and could not see.** YouTube's bot check blocks the watch page
and its description or chapters from this container, and transcript mirrors
returned 403. This analysis therefore rests on:
- the tutorial's public thumbnail and frame stills at 25, 50 and 75 %;
- three sibling tutorials built on the same workflow (`NUQyUctGQIQ` "My
  Documentary Animation Workflow", which storyboards the same project,
  `dtc0cN2KXjM` and `mgEC7Bepq18`);
- the creator's Gumroad course page.

### What the reference does

The tutorial project is called "Back to the moon". Its storyboard in
`NUQyUctGQIQ` has eight panels: newspaper, crew, man on the moon, real or fake?,
back to the Moon, no landing, Artemis 2, dark side.

- **Scenes are stacks of stills arranged in 3D space.** AI-generated or archival
  photos are cut out in Photoshop and layered on Z in AE's Classic 3D renderer.
  - In the frames at 50 and 75 %, the "Hands newspaper" plate sits at z −1000
    and the "Tripulation Apollo" (Apollo 11 crew) photo at z −180, in front of
    a moon plate.
  - The camera hangs off a chain of three parented nulls (null to null to null
    to camera). One handles the dolly, one the orbit and one the drift.
- **Z-space fly-through transitions.** The camera pushes through one scene's
  plane into the next, for example the newspaper into the crew portrait. One
  sibling project names a comp "Smoooth 3D transition".
- **Frame-in-frame props.** Hands hold a newspaper ("MAN WALKS ON THE MOON")
  lit by window-blind light, and an old-TV PNG frames footage.
- **3D type with simple reveals.** A light small line ("On July 20") sits over a
  big bold number ("1969"), revealed per character with a Range Selector
  offset (the timeline shows the Range Selector 1 Offset keyed).
- **Texture and overlay kit**, from the project panel:
  - `Texture.jpg/png`, `text halftone.jpg`, `Ink footage.mp4` / `Ink Reveal.mov`
    (ink mattes), `glitch 03.mov`, `Smoke.mov`, `Clouds.mp4`, `Starry sky.jpg`;
  - `Research board.jpeg`, `Sketches.jpeg`;
  - torn-paper edges (Spanish-flag shot), fabric texture.
- **Grade:** dark, desaturated and gritty, with one saturated accent (red tape
  over a mouth, a glowing yellow peace sign). Glows come from Deep Glow and
  particles from Trapcode Particular, per the course page.
- **3D models:** `.glb` objects (a peace sign) in AE's Advanced 3D renderer.
- **Workflow,** per the course page: script, then AI audio, moodboard, storyboard,
  AI images, Photoshop prep, a four-scene After Effects animation with camera
  moves, then details and effects, then render.

### Where it is weak, and what we do instead (the "10×")

| Reference | Ours |
|---|---|
| AI-generated people and scenes, which look uncanny and are not factual | Real 1996 FBI evidence photos of the actual cabin, USGS terrain of the actual valley, licensed footage. No synthetic faces. |
| Flat cut-out cards in Classic 3D; edges and "cardboard" depth show | Depth-mesh projection (true per-pixel parallax), real 3D geometry (terrain, trees, extruded title), lighting and shadows, depth of field |
| Mostly slow push-ins | A designed move vocabulary: pull-back oner, lateral truck, crane-up, portal push. Altitude is interpolated in log space and every shot breathes like a handheld camera. |
| Paper and halftone overlays | A full film pipeline: per-act LUT looks, halation, selective bloom, animated luma-weighted grain, gate weave, 180° shutter motion blur |
| A default sans and a per-character fade | A typographic system with meaning (investigator mono vs typewriter vs title), at most 6 text events, kinetic only when it carries information |
| Z-space fly-throughs as decoration | The fly-through is the story beat ("into the secret"), alongside match cuts and silence cuts |
| A music bed plus stock SFX | A sound-led edit: stereo storytelling, modern noise cut to silence, an accelerating tick, riser to suck-out to silence to a three-layer hit, a reverb throw on "secret" |
| One tonal register | A three-act arc in colour (cold to warm to black and red) and in frame (16:9 to 2.39:1) |

---

## 3. What the best do (transferable techniques)

| Source | Technique | How we use it |
|---|---|---|
| *Se7en* titles (Kyle Cooper; Art of the Title) | The titles look as if the killer made them himself: hand-etched type, jitter, staccato cuts, analog accidents kept in | The secret's flashes are his artefacts: clippings found in his own cabin, typewritten text. We keep them raw and imperfect, but only for 2-frame glimpses. |
| *True Detective* titles (Patrick Clair; AoTT) | "Living photographs": footage at 10–20 % speed, photos projected onto low-poly geometry with slow virtual camera moves, a light-to-dark arc | Depth-projected archival stills with slow moves; the "quiet of the wilderness" plate in slow motion; the whole cold open goes from light to dark |
| *Mindhunter* titles (Blur and Neil Kellerhouse; Big Shiny Robot) | Sterile, orderly close-ups interrupted by subliminal flash cuts: order against chaos | Calm, orderly nature interrupted by 2-frame evidence flashes at the turn |
| *Zodiac* (Fincher; AoTT) | Period-accurate newsroom detail; coded typography | Real 1990s clippings, typewriter only for the case name |
| *Manhunt* (HBO 2013, The Mill+; AoTT) | Typographic, built around the analysts' point of view | The investigator's mono voice: coordinates, measurements, case labels |
| *Making a Murderer* (Elastic) | A slow, textural, landscape-led opening | Act I is about landscape |
| Johnny Harris | GEOlayers maps; physical paper props shot on a desk rather than faked flat; photo slides with blur and a projector sound | Real 3D terrain map instead of a flat one; evidence prints as lit physical objects on a table; a soft paper-slide sound on photo moves |
| LEMMiNO (lemmi.no FAQ) | After Effects plus Cinema 4D, Blender or Unreal; original music composed in FL Studio; very sparse type, long holds, silence as a tool | The score is written to the picture and stops dead; long held shots are allowed |
| MagnatesMedia (as freelancers describe the style) | 3D parallax photos, speed ramps, newspaper and map visuals, retention-first pacing | Speed ramps at the turn; nothing static for longer than 12 frames |
| Trailer sound design (Violet Recording; Ableton) | Bed, then risers, then hits; silence before the biggest hit; three-layer hits (transient, body, sub); the riser peaks on the exact frame; the bed is side-chained under hits | The whole sound architecture of section 14 |
| YouTube retention guidance | The first 30 s decide retention: open on motion, deliver the promise early, no channel intro | First frame is a moving picture, not black; the title promise lands by 28 s |

House knowledge from watching the genre, not sourced above: dark-documentary
channels such as Barely Sociable and Nexpo work with slow creeping push-ins,
monospaced on-screen text, near-black palettes and ambient drones with very few
hits. We borrow the restraint, not the lo-fi look.

---

## 4. Concept: "The Quiet"

The narration asks us to imagine a peaceful, simple life, and then reveals that it
hides a secret. The picture has to hold that double meaning: beautiful, but
watched. The audience should feel the quiet before they understand it.

**Three movements:**

| | I. THE WILDERNESS | II. THE CABIN | III. THE SECRET |
|---|---|---|---|
| VO | "Imagine…" to "…modern world." | "To anyone passing…" to "…outside world." | "But hidden…" to "…a secret", then the title |
| ≈ time | 0.0 – 17.0 s | 17.0 – 25.4 s | 25.4 – 30.0 s |
| Scale | Vast: terrain, forests, sky | Human: one 10 × 12 ft cabin, its objects | Intimate and abstract: a window, darkness, type |
| Look | `wild`: cold teal-steel, open | `cabin`: warm umber, lamp light | `secret`: near-black, desaturated, red kept |
| Frame | 16:9 open | 16:9 | Closes to 2.39:1 |
| Camera | Big, slow, floating | Lateral, curious, then settled | A single forward push through the window |
| Sound | Wind, silence, short bursts of modern noise | Car pass-by, wood creak, paper, a shutter click, drone enters | Ticks speeding up, riser, suck-out, **silence**, hit |
| Type | Location super, map labels | Measurements, facts | Case name (typewriter), title |

**Motif system:**
- **Cold against warm.** The modern world is harsh fluorescent and sodium light;
  the wilderness is cold and soft; the cabin is warm; the secret is black and red.
- **Open against closed.** Wide lenses and an open frame give way to long lenses,
  a closing letterbox and the window.
- **The investigator's eye.** Coordinates, distance rings and measurement ticks
  quietly frame an innocent life as a case file before the narration does.
- **The typewriter.** It is heard before it is seen: a single off-screen key
  strike in the silence before the title.

---

## 5. Proposed shape of the 30 s (input for the storyboard)

Times are targets for a VO that ends "secret" at about 27.6 s. Re-key everything
to `data/words.json`. Picture cuts land **2 frames before** the stressed
syllable they illustrate; SFX hits land on the cut frame.

| # | VO | ≈ t (s) | Picture | Move / transition | Sound |
|---|---|---|---|---|---|
| 1 | "Imagine living in a remote cabin, | 0.00–1.9 | Tight on the cabin as a living photograph: depth mesh, falling snow, a smoke wisp from the stovepipe | Already moving on frame 1 (a slow pull-out). No fade from black longer than 6 f. | Wind bed; a low piano note at 0.3 s |
| 1′ | surrounded by forests and mountains, | 1.9–3.4 | The pull-back continues up through branches (3D foreground trunks pass the lens) | **T3 mist pass-through** (14 f) hides the swap to the 3D terrain (S1) | Owner's `whoosh.mp3`, peak on the mist frame, −10 dB, filtered soft |
| 1″ | far removed from the noise of modern civilization." | 3.4–5.6 | 3D terrain of the Blackfoot valley rising to about 5 km. A red pin marks the cabin; the location super types on; isolation rings expand and city labels drift outward (S2). | Crane-up, altitude in log space | Distant raven once; very high, thin air layer |
| 2 | "There are no crowded streets | 5.6–6.5 | **Modern** clip: a dense crowd moving L→R, harsh `modern` look | **T1 hard cut** with a sound burst | Crowd walla and traffic burst, −20 LUFS momentary |
| 2′ | outside your door. | 6.5–7.4 | **Match cut**: snow drifting L→R across pines, same motion vector (S3) | T2 match cut. Modern sound cut with a 5 ms fade. | Instant drop to wind |
| 3 | No office to report to. | 7.4–8.1 / 8.1–9.0 | Fluorescent office ceiling grid and keyboards, then bare aspen branches against an overcast sky (the grid matches) | T1, then T2 | Phones and keys burst, then silence plus a creak of branches |
| 4 | No busy city to navigate. | 9.0–9.6 / 9.6–10.6 | Night traffic light trails, then a still creek or snowfield at dusk (the horizontal line matches) | T1, then T2. Modern clips get shorter: 24 f, then 20 f, then 16 f. | Horn and traffic, then silence plus trickling water |
| 5 | Just the quiet of the wilderness | 10.6–13.4 | **The breath**: the longest held image. A misty forest or mountain plate at 20–40 % speed. No text. | A very slow push (1.5 %/s) | Wind almost gone; piano note 2; one bird |
| 6 | and a life deliberately separated from the modern world. | 13.4–17.0 | **The Divide** (S5): a hairline splits the frame, city at night on the left, the cabin in the woods on the right. The line sweeps left and pushes the city out, then lands as an aspen trunk. | Hairline move 1.6 s, `inOutCubic` | City hum panned hard left fades as the line moves; forest on the right takes over |
| 7 | "To anyone passing through the area, | 17.0–18.8 | **Glimpse through the trees** (S6): passing-car point of view, a lateral truck past 3D trunks, the cabin seen 2–3 times through the gaps | Truck at "30 mph", depth of field on the foreground | Car pass-by L→R, gravel |
| 8 | the cabin might appear unremarkable. | 18.8–20.6 | The truck slows and settles on the most ordinary, frontal, flat framing of the cabin (FBI exterior, living photo) | Ease-out over 1.2 s, then a 2 %/s push | Car fades away; one wood creak |
| 9 | Its occupant seemed to have chosen a simple existence, | 20.6–23.0 | **Inventory** (S7): FBI interior photos as physical prints on a dark table under lamp light. Dimension ticks draw on: "10 × 12 FT". Label: "NO ELECTRICITY · NO RUNNING WATER". | Overhead glide at 85 mm, rack focus between prints | Paper slide; scribe tick on the lines; owner's `click-double.mp3` when a print is "snapped" |
| 10 | one that required little contact with the outside world. | 23.0–25.4 | Rise from the prints to the cabin's dark window (exterior photo with the loft windows); the push toward the window begins | Crane, then push | Owner's `low-drone.mp3` fades in; a soft tick pulse starts at 72 BPM |
| 11 | "But hidden behind this isolated lifestyle | 25.4–26.8 | **The frame closes** to 2.39:1 (S8). **Subliminal flashes** (S9), 2 f each: the "Bomber elusive" clipping, the 1987 composite sketch, typed "UNABOM" with a sliding redaction bar, the fenced cabin in 1996. | The push continues and speeds up (speed ramp) | Ticks speed up from 72 to 144 BPM; riser builds; a sharp transient on each flash |
| 12 | was a secret…" | 26.8–27.6 | **Portal** (S10): the camera passes through the window into black | T4 Z-space push, 20 f | Riser hard-stops (suck-out) on the last phoneme; reverb throw on "secret" |
| 13 | (silence) | 27.6–28.0 | Near-black; a few dust motes catch a slit of light; then the title's letters strike in, one per frame | **T5 silence**, 10–14 f | Room tone at −60 dBFS, the "secret" tail, one off-screen typewriter key strike, then 9 rapid typebar clacks |
| 14 | TITLE | 28.0–30.0 | **THE UNABOMBER** slam (section 12) | Hit, then light sweep and settle | Three-layer hit plus braam on low D; long dark tail; cut to black at 29.9 s |

That is 16–18 shots (flashes excluded), averaging about 1.8 s. The longest is
the opening oner at about 5.6 s; the shortest are the 2-frame flashes.

---

## 6. Palette

See `docs/reference/palette.png`. Use these exact values for graphics; footage
and photos are graded towards them (section 8).

| token | hex | role |
|---|---|---|
| `ink` | `#0A0B0D` | Black point of the image. Image blacks never go below this (letterbox bars are `#000000`). |
| `char` | `#15181C` | Deep shadow; side faces of the 3D title |
| `slate` | `#2B3238` | Hairlines on dark backgrounds, plates, map land at night |
| `fog` | `#8FA3AE` | Secondary text, subtitle, fog colour for terrain haze |
| `frost` | `#D6DEE2` | Cold highlight, snow at its brightest |
| `bone` | `#F2EFE8` | Primary type. **Never `#FFFFFF`.** |
| `spruce` | `#1D2A26` | Conifer shadow (the target for green shadows) |
| `pine` | `#3E524B` | Conifer midtone |
| `birch` | `#CFC8B8` | Aspen bark, snow midtone |
| `umber` | `#5A3E2B` | Cabin plywood |
| `kraft` | `#9C7A4E` | Evidence envelope, print backs |
| `manila` | `#CDB27A` | Case folder, label stock |
| `lamp` | `#E3A04A` | Warm key light (lamp interior, the title's light sweep) |
| `red` | `#C8102E` | Evidence red: the single accent |
| `redDeep` | `#7A0C14` | Red in shadow; the underside of the redaction bar |
| `mapline` | `#7FA8B5` | Map rings, contours, leader lines |

**Ratios:**
- **`red`** covers at most 3 % of the frame at any moment. It is used only for:
  the cabin pin and location bullet, the measurement leader dots, the title's
  "THE", and flash-frame accents.
- **Act I** is about 85 % cold neutrals and greens. Warm colour only comes from
  the cabin itself.
- **Act II** shifts towards `umber`, `kraft` and `lamp`.
- **Act III** is more than 90 % `ink` and `char`, with `bone` type and a touch
  of `red`.

---

## 7. Typography

All three families are free under the OFL and come from Google Fonts. Requesting
the css2 API without a browser user agent returns static TTF instances, which
the 3D extrusion needs:
- Archivo: `https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@125,900`
- IBM Plex Mono: `…family=IBM+Plex+Mono:wght@400;500;600`
- Courier Prime: `…family=Courier+Prime:wght@400;700`

| Role | Face | Use |
|---|---|---|
| **Title** | **Archivo, wdth 125, wght 900** (Expanded Black) | "UNABOMBER" only. A wide, heavy grotesque that is rare on YouTube and reads as prestige. Fallback: Archivo Black. |
| **Investigator voice** | **IBM Plex Mono 500** (600 for emphasis) | Location supers, coordinates, distances, measurements, the "THE" kicker, the subtitle |
| **His voice: the typewriter** | **Courier Prime 700** with an ink treatment | Only the "UNABOM" flash card and the off-screen key strike. Never more than 6 characters on screen. |

**Banned faces:** Bebas Neue, Anton, Impact, Montserrat, Special Elite (it reads
as cheap creepypasta), Trajan or Cinzel (they read as epic fantasy).

### Sizes at 1080p (px)

| Element | Face | Size | Tracking | Colour | Position |
|---|---|---|---|---|---|
| Location line 1 "NEAR LINCOLN, MONTANA" | Plex Mono 500 | 26 | +0.14 em | `bone` at 92 % | Left x = 120, baseline y = 930 (y = 880 once letterboxed) |
| Location line 2 "46°57′N 112°41′W" | Plex Mono 500 | 20 | +0.14 em | `fog` | 34 px below line 1 |
| Bullet before line 1 | — | 8 × 8 square | — | `red` | x = 96, centred on line 1's x-height |
| Map labels "HELENA · 40 MI" | Plex Mono 500 | 18 | +0.12 em | `fog` | At the end of a 1.5 px `mapline` leader at 70 % |
| Measurements "10 FT", "12 FT" | Plex Mono 500 | 20 | +0.10 em | `bone` | Centred on 2 px `bone` dimension lines at 85 % with 12 px end ticks (architectural ticks, no arrowheads) |
| Facts "NO ELECTRICITY · NO RUNNING WATER" | Plex Mono 500 | 20 | +0.18 em | `bone` at 90 % | One line, lower third, left-aligned to the print edge |
| Typewriter flash "UNABOM" | Courier Prime 700 | 64 | 0 | Ink `#16171A` on `manila` paper | Centred on the card |
| Title "UNABOMBER" | Archivo 125/900 | 152 (cap height ≈ 108) | +0.05 em | `bone` face | Centred, width ≈ 1,400 px (73 % of the frame) |
| Kicker "THE" | Plex Mono 600 | 30 | +0.50 em | `red` | Left edge aligned to the U's stem; baseline 22 px above the cap top |
| Subtitle "INSIDE THE 18-YEAR MANHUNT FOR TED KACZYNSKI" | Plex Mono 500 | 22 | +0.32 em | `fog` | Centred, 40 px below the title baseline |

### Rules

- All caps for supers and labels. Never set more than 7 words in one text event.
- **On-screen text adds facts; it never repeats the VO word for word.** For
  example, the VO says "remote cabin" and the screen says "NEAR LINCOLN, MONTANA".
- **No drop shadows, outer glows or boxes behind text.** Separation comes from
  the grade (darken the plate locally by 15–20 % under the text with a soft
  gradient) and from depth of field.
- **Title-safe area is 90 %:** 96 px left and right, 54 px top and bottom. Keep
  text 120 px from the left and right edges.
- **Mono type-on** runs at 45 characters per second with a block cursor `█`
  (`bone` at 80 %, blinking 8 f on and 7 f off) that disappears 10 f after the
  last character. Type-on SFX are optional and only for short lines.
- **Courier ink treatment:** each glyph gets random density 85–100 %, a baseline
  jitter of ±0.6 px, rotation ±0.4° and a rough edge from a noise threshold. On
  strike the glyph overshoots to 110 % density for 1 frame, then settles.

---

## 8. Grade

Prototype numbers are in `tools/grade_lookdev.py`; see
`docs/reference/grade_lookdev.jpg`. In the engine, build each look as a 33³
`.cube` LUT and blend between LUTs per shot (`fx.look`, cross-fading 8–12 f
between acts).

**Pipeline (linear HDR render, then display):**
1. Selective bloom
2. Halation
3. Filmic tone map (AgX, or ACES with exposure 1.0)
4. LUT look
5. Chromatic aberration
6. Vignette
7. Gate weave (UV offset)
8. Grain, in display space after the LUT
9. Letterbox

**Archival photos first get normalised:** a partial grey-world white balance
(strength 0.5–0.6). This removes the 1996 prints' magenta and yellow casts; the
FBI night shot of the cabin becomes usable. Then a gentle local-contrast lift
(unsharp at radius 30 px, amount 0.15) and the shared look.

| Look | Used for | Lift RGB | Gamma RGB (out = in^γ) | Gain RGB | Sat | Greens (hue 50–170°) | Black / white out | Notes |
|---|---|---|---|---|---|---|---|---|
| `wild` | Act I nature, terrain, cabin exteriors in Act I | −0.004, +0.006, +0.020 | 1.03, 1.00, 0.97 | 0.97, 0.99, 1.03 | 0.80 | sat ×0.62, nudged −10° toward cyan | 0.025 / 0.93 | Teal shadows, neutral highlights; snow never clips |
| `modern` | The negation-triplet clips | 0, +0.01, 0 | 1.0, 0.98, 1.02 | 1.02, 1.03, 0.97 | 0.95 | none | 0.02 / 0.95 | Fluorescent green-cyan mids, contrast 1.15, CA 0.8, extra sharp; deliberately harsh |
| `cabin` | Act II | +0.010, +0.006, 0 | 0.98, 1.00, 1.04 | 1.03, 1.00, 0.95 | 0.85 | sat ×0.70, nudged −6° | 0.020 / 0.92 | Warm umber mids, cool shadows kept |
| `secret` | Act III and flashes | 0, +0.004, +0.010 | 1.02, 1.03, 1.03 | 1.00, 0.98, 0.96 | 0.45 | sat ×0.40 | 0.015 / 0.90 | Reds (hue 335–25°) keep full saturation |

All looks share a soft S-curve: out = 0.35·smoothstep(x) + 0.65·x, then the
black and white points.

**Exposure targets:**
- Act I average picture level 35–45 %; snow at most 92 %.
- Act II 30–40 %.
- Act III 8–15 %, with the title face at 88–92 %.
- Skin is not a concern: no faces are shown, apart from the sketch.

**Sources must match.** Footage from different cameras gets the same grain, the
same weave and the same black point, so nothing looks pasted in.

---

## 9. Texture stack

From the top layer down; values are at 1080p.

| Layer | Spec | Where |
|---|---|---|
| **Grain** | Gaussian, animated (new seed every frame), luma-weighted with σ = 0.024·(4L(1−L)+0.35), so stronger in midtones. 80 % monochrome, 20 % chroma. Grain size 1.3–1.6 px (generate at 1/1.4 resolution and upsample bicubic). | Every frame, including the title and black frames (black frames get grain at 50 %) |
| **Halation** | Luminance above 0.82, blurred 18 px (24 px for lamp and window), tinted `#FF5A2A`, added at 10 % (15 % in Act II) | Snow edges, sky behind branches, lamp, the title's light sweep |
| **Selective bloom** | Only on a "glow" layer: lamp, window slit, title sweep. UnrealBloom strength 0.35, radius 0.55, threshold 0.80. | Never global |
| **Vignette** | Elliptical: 0.18 in Act I, 0.24 in Act II, 0.32 in Act III | Always |
| **Chromatic aberration** | Radial 0.4 px at the corners at rest; 2.5 px for 2–4 f on impacts and whips, then decaying | Always (rest value); spikes only on hits |
| **Gate weave** | Smoothed noise: x ±0.5 px, y ±0.7 px, rotation ±0.03°, period 1.5–3 s. Doubled on archival "projected" moments. | Always. **Freeze it** on the title's final 12 f. |
| **Dust and specks** | 1–2 specks per second, 2–6 px, alive 1–2 f, `ink` or `bone` at 60 %. One fine vertical scratch for 6 f during the flashes. | Acts II and III only |
| **Paper** | Prints and documents: fibre texture multiplied at 18 %, 0.5° curl, real contact shadow plus a soft shadow (40 px blur, 35 %), the photo's own white border | Inventory, flashes |
| **Atmosphere** | Snow particles (2–5 px, bokeh-blurred in the foreground), mist cards, dust motes in light shafts | Act I snow, Act III motes |
| **Light leak** | At most **once**: a warm `lamp`-tinted leak from the left edge over 14 f, additive at 30 % | At the cut into Act II (18.8 s) if it helps; otherwise none |
| **Letterbox** | `#000000` bars, 138 px each, which gives 2.39:1 | From 25.4 s to the end |

**Banding:** with dark gradients and 8-bit delivery, the grain is the dither.
Never disable grain on gradients.

---

## 10. Motion language

**Easing.** Engine names come first; CSS cubic-béziers are given for the DOM.

| Name | Curve | Use |
|---|---|---|
| Glide | `inOutSine` / `cubic-bezier(0.37, 0, 0.63, 1)` | Long camera moves (2–6 s) |
| Settle | `outExpo` / `cubic-bezier(0.16, 1, 0.3, 1)` | Text and annotation reveals, 14–20 f; moves ending into a hold |
| Commit | `inCubic` / `cubic-bezier(0.32, 0, 0.67, 0)` | Accelerating into a hit or a portal |
| Sweep | `inOutCubic` | The Divide hairline, the letterbox close (12 f) |

**Banned easing:** `outBack`, elastic, bounce or any overshoot on type or camera.
This is a serious documentary, not an explainer.

**Camera:**
- **Focal lengths (35 mm full-frame equivalent, 16:9) and vertical FOV:**
  - terrain 28–35 mm (39.8°–32.3°);
  - exteriors 35–50 mm (32.3°–22.9°);
  - inventory 85 mm (13.6°);
  - portal 50 mm, narrowing to 35 mm during the push (a slight dolly-zoom
    unease);
  - title 50 mm.
- **Every shot has one primary move** (push, pull, truck, crane or orbit) **plus
  breathing**: rotation noise ±0.12° in pitch and yaw, ±0.06° in roll, made of two
  noise octaves at 0.25 and 0.5 Hz. No positional jitter on stills.
- **Speeds:**
  - Stills on depth meshes: dolly 3–6 % of the subject distance per second;
    orbit at most 0.8°/s, at most 4° per shot.
  - Plain push-ins: 1.5–3 % scale per second.
  - Terrain: interpolate altitude **in log space** so the perceived zoom speed
    stays constant (about 5 km to 600 m above ground over 4 s, or the reverse).
- **Parallax ceiling:** on depth-projected photos, the foreground and background
  may not differ in displacement by more than 3 % of frame width across a shot.
  Beyond that, stretching shows.
- **Never static:** no frame without camera or subject motion for longer than
  12 f, except the title's final hold (at most 20 f).
- **Depth of field:** use it on the hero moments only: the glimpse through the
  trees, the inventory rack focus, and the title (sketch defocused). Bokeh costs
  about 1.5 s per frame; budget it.

**Speed ramps (footage):**
- 100 % to 25 % over 8 f on the breath plate. The longer clip can instead run
  at a constant 30–40 %.
- 100 % to 160 % over 6 f into the portal (camera speed).
- Slow motion needs real interpolated frames: RIFE (PyTorch) or ffmpeg
  `minterpolate=mi_mode=mci`. **Never duplicate frames.** Without
  interpolation, stay at or above 50 % for 25p sources and 40 % for 60p sources.

**Motion blur:**
- Render at 60 fps and blend pairs, which gives a 180° shutter at 30 fps (as in
  the previous engine).
- Whips, the portal and the slam get 4–8 accumulated sub-frames, or a
  directional blur scaled to velocity.

**Hits:** the frame of impact gets:
- exposure +0.5, decaying over 10 f;
- CA 2.5, decaying to 0.4 over 8 f;
- camera shake of 6 px decaying to 0 over 5 f at 18 Hz;
- a 2 % scale punch-in that decays with `outExpo` over 12 f.

Never more than one hit per 2 s outside the title.

---

## 11. Signature moves

Execute all twelve; they are what makes this "10×".

1. **S1 Powers-of-Ten pull-back (0–5.6 s).** One continuous camera move.
   - It starts tight on the cabin as a living photograph (S4), pulls back
     through 3D branches, crosses a mist card (T3), and emerges above real
     terrain that keeps rising.
   - Terrain: AWS Terrarium elevation tiles (zoom 12–13) for about 30 × 20 km
     around Lincoln, draped with USGS National Map imagery. Vertical
     exaggeration 1.15×. `exp2` fog in `fog` colour, about 25 km visibility.
   - Add a patchy-snow mask above 1,800 m on slopes under 35°. This matches the
     April 1996 photos, which show late-winter snow patches.
   - The cabin pin is a 6 px `red` dot with a 1 px `bone` ring.
2. **S2 Isolation radius (4.0–5.6 s).**
   - Thin `mapline` rings expand from the pin (1.5 px, 60 % opacity, 3 rings
     staggered 6 f, `outExpo` over 24 f).
   - Three leaders slide out to the frame edges with straight-line distances
     **from Lincoln**: "HELENA · 40 MI" (bearing 130°), "MISSOULA · 62 MI"
     (265°), "GREAT FALLS · 75 MI" (59°).
   - Each city sits at the frame edge as a faint warm glow, the "noise of modern
     civilization" kept far away.
3. **S3 Match-cut negation triplet (5.6–10.6 s).**
   - Each "No…" is a pair: a loud, harsh `modern` clip, then a hard cut to a
     silent wilderness shot with **the same composition or motion vector**
     (crowd L→R to snow L→R; ceiling grid to branch grid; light-trail line to
     horizon line).
   - The negation is the cut itself, with no "NO" text. Modern clips get
     shorter each time: 24 f, then 20 f, then 16 f.
4. **S4 Living photographs (throughout).**
   - Every archival still gets a depth map (Depth Anything V2 Small, from
     Hugging Face) and becomes a subdivided mesh of 256 × N segments, displaced
     by depth.
   - Discard triangles that cross depth edges, and fill behind them with an
     inpainted background plate (OpenCV Telea).
   - Then add life: drifting snow, a smoke wisp from the stovepipe, a slow
     light change (exposure ±3 % over 3 s), and grass sway in masked regions
     (vertex noise at most 2 px).
5. **S5 The Divide (13.4–17.0 s).**
   - A 1 px `bone` hairline at 70 % splits the frame: the night city (`modern`
     look) on the left, the cabin in the woods (`wild`) on the right.
   - The line sweeps left over 1.6 s, the city half is pushed out, and the line
     ends as an aspen trunk (match).
   - Sound tells the same story: the city hum is panned hard left and fades with
     the line.
6. **S6 Glimpse through the trees (17.0–18.8 s).**
   - A lateral truck at constant speed past instanced 3D trunks and branches in
     the foreground (blurred by depth of field and motion blur).
   - The cabin plate sits in the midground and appears in 2–3 gaps. The truck
     eases out over 1.2 s into the flat, frontal "unremarkable" frame.
7. **S7 Evidence inventory (20.6–23.0 s).**
   - FBI interior photos as physical prints on a dark wood table, lit by one
     warm `lamp` key from the upper left plus a cool fill at 20 %. Each print has
     a real shadow.
   - An overhead 85 mm glide with one rack focus.
   - Architectural dimension lines draw onto the cabin print: "10 FT" and
     "12 FT", 2 px, drawn in 14 f each with `outExpo`.
   - Then the facts label (Plex Mono) types on.
8. **S8 The frame closes (25.4 s).** Letterbox bars slide in from 1.78:1 to
   2.39:1 over 12 f (`inOutCubic`), with a soft low "shutter" thump at −30 LUFS.
   The world literally closes in.
9. **S9 Subliminal intrusions (25.6–26.7 s).**
   - Four 2-frame flashes cut into the push, spaced 12 f, then 9 f, then 7 f.
     That is at most 3 per second (photosensitivity, section 16).
   - The flashes, in order:
     1. the "Bomber elusive" newspaper clipping found in the cabin;
     2. the 1987 FBI composite sketch, cropped to the hood and glasses;
     3. a `manila` card typed "UNABOM" with a redaction bar sliding off;
     4. the cabin behind the 1996 FBI fence.
   - All flashes use the `secret` look. Each gets a single sharp transient.
10. **S10 Portal push (26.8–27.6 s).**
    - A Z-space push through the cabin's dark window (on the depth mesh, the
      window is a hole in the geometry) into black.
    - The narrowing focal length and exposure dipping to 0 make the darkness
      feel like it swallows us.
    - This is the reference's signature fly-through, but here it carries the
      story beat.
11. **S11 Silence drop (27.6–28.0 s).**
    - 10–14 f of near-black with a few lit dust motes.
    - Audio is room tone at −60 dBFS, the reverb tail of "secret", and one
      off-screen typewriter key strike at −24 LUFS midway through the silence.
    - Then the title's letters strike in and the slam lands (section 12).
12. **S12 Light-sweep title with the ghost (28.0–30.0 s).** The extruded title
    is lit by a moving `lamp` light; behind it the 1987 composite sketch looms
    at 12 % opacity. Full spec in section 12.

---

## 12. Title design: "THE UNABOMBER"

**Layout** (see `docs/reference/title_mock.jpg`), inside the 2.39:1 frame:
- "UNABOMBER" in Archivo 125/900, font size 152 px (cap height ≈ 108 px),
  tracking +0.05 em, width ≈ 1,400 px, centred, optical centre 12 px above the
  frame centre.
- Above it, "THE" in Plex Mono 600 at 30 px, tracking +0.5 em, `red`, aligned to
  the U's stem.
- Below it, "INSIDE THE 18-YEAR MANHUNT FOR TED KACZYNSKI" in Plex Mono 500 at
  22 px, tracking +0.32 em, `fog`.

**3D build:**
- Extrude "UNABOMBER" by 0.12 × the cap height, with a bevel of 0.015 × the cap
  height and 3 segments.
- The face is `bone` with a subtle ink-and-paper texture (roughness 0.6; a
  noise normal map at strength 0.05). The sides and bevel are `char` metal
  (metalness 0.6, roughness 0.35), which catches the sweep.
- Lights:
  - **key:** a `lamp` area light, 3,200 K feel, from the upper left at 35°;
  - **rim:** cool `#8FB3C9` from the back right at 25 %;
  - **sweep:** a narrow spot that travels left to right over 40 f, starting
    10 f after the hit. Its speculars on the bevel are what bloom.
- Behind the title, about 6 units back: the 1987 composite sketch, inverted to
  light-on-dark, at 12 % opacity, blurred 6 px. It drifts in scale from 1.00 to
  1.03 and is cropped so the hood and glasses sit just above the word.
  (Option B: a double exposure with the forest filling the hooded silhouette.
  Use it only if it reads clearly at 12 %.)
- Dust motes drift through the sweep beam, 20–40 particles of 1–3 px.

**Timeline** (H = the frame of the hit, ≈ 28.0 s):

| Frame | Event |
|---|---|
| H−20 to H−9 | Silence drop (S11), 12 f: black with motes; one off-screen key strike at H−14 |
| H−8 to H | The nine letters strike in, **one per frame** (left to right), each a typebar clack. The burst lasts 0.3 s, and the final "R" lands on H with the hit. |
| H | **HIT** (section 14): exposure +0.6 for 2 f, decaying over 10 f; CA 2.5 to 0.4 over 8 f; shake 6 px decaying over 5 f; scale 1.04 to 1.00 `outExpo` over 16 f. The camera starts 3° yawed and settles frontal over 60 f. |
| H+6 | "THE" appears with a 4 f type-on |
| H+10 to H+50 | Light sweep crosses left to right; bloom on the bevels |
| H+18 to H+38 | Subtitle: per-character fade with a 1 f stagger (the reference's Range Selector reveal, done cleanly), a 6 px rise and `outExpo` |
| H+20 onward | Ghost sketch fades from 0 to 12 % over 30 f |
| ≈ 29.9 s | **Hard cut to black.** The hit's reverb tail rings past the cut. |

**Never:** a glitch-in, a wipe, a zoom-blur transition, a lens flare, a red
glow, or a bounce on the title.

---

## 13. On-screen text and captions

- **No burned-in subtitles.** Deliver an `.srt` of the VO for YouTube closed
  captions. Premium documentary cold opens keep the frame clean; YouTube's CC
  serves accessibility.
- **At most 6 text events** before the title:
  1. the location super;
  2. the map distance labels (one event);
  3. the measurements;
  4. the facts line;
  5. the "UNABOM" flash (2 f);
  6. no sixth unless the storyboard needs it.
- **Exact strings** (verified facts only):
  - "NEAR LINCOLN, MONTANA"
  - "46°57′N 112°41′W" (the town; the cabin's exact position is not published
    here)
  - "HELENA · 40 MI", "MISSOULA · 62 MI", "GREAT FALLS · 75 MI" (straight-line
    distances from Lincoln's town centre)
  - "10 FT", "12 FT"
  - "NO ELECTRICITY · NO RUNNING WATER"
  - "UNABOM"
- **Lincoln is in Lewis and Clark County,** not Lincoln County. If a county ever
  appears on a map, label it correctly.

---

## 14. Sound palette and mix philosophy

**Philosophy:** the sound decides where the eye goes. Silence is the loudest
element. Every visual event that matters gets a sound, but there are never more
than 3 simultaneous design layers before the title. The music serves the VO and
**stops dead** at the turn.

### Palette

| Element | Spec | Where |
|---|---|---|
| **Wind bed** | Pink noise band-passed 200–2,000 Hz with gusts (0.1–0.25 Hz amplitude modulation), plus a pine-whistle layer at 3–6 kHz, −12 dB relative; stereo decorrelated | Act I and II under everything |
| **Nature spots** | One distant raven (low-passed at 4 kHz, with reverb); a creek trickle; a snow creak; a branch creak | Act I and the triplet's wilderness halves |
| **Modern bursts** | Crowd walla with traffic; phones and keyboards with an office HVAC hum; horn and traffic. 0.5–0.8 s each, momentary −20 to −18 LUFS, **cut with a 5 ms fade on the picture cut** to near silence | S3 |
| **City hum** | Low traffic roar, panned hard left, fading with the hairline | S5 |
| **Car pass-by** | Gravel tyre rumble with a Doppler pass L→R, about 1.6 s | S6 |
| **Cabin** | Wood creak, stove tick. **No electrical hum anywhere inside the cabin** (it had no electricity), and no 60 Hz buzz. | Act II |
| **Paper and evidence** | Print slide, a paper rustle, a scribe tick for the dimension lines, the owner's `click-double.mp3` as the evidence-camera shutter (first hit at 0.16 s, aligned to the snap frame) | S7 |
| **Drone** | The owner's `low-drone.mp3` (audible 5.3–32.9 s, about 180–210 Hz): trim the leading silence, raise the gain about 14 dB, low-shelf +3 dB at 120 Hz, fade in over 1.5 s from 23.0 s | Turn |
| **Tick pulse** | A muted clock or carriage tick at 72 BPM, accelerating to 144 BPM from 25.4 to 27.6 s | Turn |
| **Riser** | 2.2 s: a filtered noise sweep (high-pass 200 Hz to 6 kHz), a pitch riser (100 to 400 Hz), and the reversed reverb of the title hit. It **hard-stops** on the last phoneme of "secret" (the suck-out). | Turn |
| **Flash transients** | A short metallic tick or a camera-flash "pop", 30–60 ms, for each S9 flash | S9 |
| **Whoosh** | The owner's `whoosh.mp3` (peak at 0.89 s, placed on the mist frame in S1 and the portal frame in S10). Low-pass at 5 kHz in S1 so it reads as air, not as a swipe. | S1, S10 |
| **Typewriter** | A single key strike in the silence; then 9 rapid typebar clacks on the title letters (1 per frame) | S11, title |
| **Title hit** | Three layers, time-aligned: **transient** = a metallic slam or typebar pitched −5 semitones, plus a crack; **body** = taiko or low tom plus a distorted braam on low D (D1–D2, brass or synth stacked in octaves, pitch falling about 1 semitone over 1.5 s); **sub** = a sine sweep 60 to 28 Hz over 1.5 s with a 5 ms fade-in. A dark reverb tail of 3.5 s (high-frequency damping at 3 kHz). | Title |

The owner's `/sfx` files are justified here: the whoosh, the shutter-like click
and the low tension drone each fit a specific beat. That follows `CLAUDE.md`: we
use them where this video needs them, not by default.

### Music

- **Character:** sparse, dark and intimate, not "epic trailer". D minor.
  Instruments: a felt piano (single notes, long decay), a low cello or bass
  drone on D, faint high harmonics, and a sub pulse under Act III.
- **Shape:**
  - free time (no beat) from 0 to 17 s, with piano notes at 0.3 s and on "Just
    the quiet";
  - a soft pulse from 17 to 25.4 s;
  - from 25.4 s the music thins to the drone, ticks and riser;
  - **hard stop at 27.6 s**;
  - the hit lands the root note (low D) and lets it ring.
- **Source:** if a licensed track is used (for example from Mixkit), edit it to
  the picture: cut it to the silence drop and do not fade it out. Otherwise
  synthesise the cue, as `audio/music.py` did in the previous project.

### Mix

| Bus | Target |
|---|---|
| Master | **−14 LUFS integrated** (±0.5), **true peak ≤ −1.0 dBTP**, loudness range 8–12 LU (keep it dynamic; YouTube normalises) |
| VO | Short-term −16 to −15 LUFS. Chain: high-pass 80 Hz; −2 dB at 250–350 Hz; +2 dB at 3–5 kHz; +1.5 dB shelf at 10 kHz; compression 3:1 (at most 6 dB of gain reduction); de-ess 6–8 kHz; dry. The one exception is a **reverb throw on "secret"** (dark plate, 1.8 s, 30 ms pre-delay, 15 % wet) that rings into the silence. |
| Music | −26 to −24 LUFS under the VO; side-chain ducked 6–8 dB by the VO (attack 30 ms, release 400 ms) |
| Ambience | −32 to −28 LUFS; fades out under the riser, so that only room tone is left in the silence drop |
| Modern bursts | Momentary −20 to −18 LUFS, always at least 4 dB under the VO |
| Hits | Title hit momentary −9 to −8 LUFS. Other hits side-chain the music and ambience bus by 3–4 dB for 150 ms. |
| Silence drop | Room tone at −60 dBFS, not digital zero (true zero sounds like a dropout) |
| Low end | Everything except the sub elements is high-passed at 30–40 Hz; below 120 Hz is mono; one sub event at a time |
| Edits | Every audio cut gets a 5–10 ms fade (no clicks); ambience pre-laps picture cuts by 8–12 f (J-cuts) except the S3 bursts, which hit on the cut |

---

## 15. Things that make an edit look cheap (banned)

- Ken Burns zooms on flat photos with linear easing; stills without depth;
  visible cut-out edges or halos; parallax stretch.
- Bebas, Anton, Impact, Montserrat or Special Elite titles; drop shadows,
  outer glows, boxed lower thirds; pure `#FFFFFF` text; type that bounces or
  overshoots.
- Preset transition packs: zoom-blur on every cut, RGB-split glitches, film
  burns, light leaks everywhere, lens flares, spins, cube wipes, cross-dissolves
  longer than 20 f (except the mist pass).
- An evidence board with red string as a flat 2D template. If a case-file object
  appears, it is lit in 3D with real shadows.
- Stock clichés: a hooded "hacker", generic police-tape stock, CGI explosions,
  fake newspaper headlines (we have real clippings).
- Mismatched sources: different grain, black levels or white balance between
  shots; one photo with a magenta cast; letterboxing that comes and goes
  without meaning.
- Over-grading: a full-strength orange and teal look, crushed shadows with no
  detail, oversharpened stock with halos, over-saturated greens.
- Camera shake on everything; constant hits ("braam every 2 seconds"); music
  that fights the VO; SFX for every tiny motion; music that stops without a
  tail when the stop is not a deliberate drop.
- On-screen text repeating the VO; long typewriter type-ons with a clack per
  letter; misspellings or unverified facts.
- Frozen frames or duplicated-frame slow motion (stutter); upscaled low-res
  footage; visible watermarks.
- Banding in dark gradients (grain switched off, or 8-bit gradients without
  dither).

---

## 16. Accuracy, ethics, safety

- **No synthetic images or video of real people** (Kaczynski, agents,
  witnesses) or of the real cabin or valley. Use archival material or real data.
  Textures (fog, paper fibre, dust) can be generated.
- **Use only facts that can be checked:**
  - the cabin near Lincoln, Montana (Lewis and Clark County), about 10 × 12 ft,
    with no electricity or running water;
  - his arrest there on April 3, 1996;
  - the FBI case name UNABOM ("University and Airline Bombing");
  - the 1987 composite sketch (hooded, aviator sunglasses), made after the
    February 20, 1987 Salt Lake City bombing;
  - bombings from 1978 to 1995: 16 bombs, 3 killed, 23 injured.

  The 30 s needs only a few of these, but any on-screen fact must come from
  this list or carry a source.
- **No violence on screen:** no explosions, injuries, victims or bomb
  components. Do not stage the manifesto as hero text; documents appear only as
  2-frame glimpses or out-of-focus texture.
- **Photosensitivity** (WCAG 2.3.1): at most 3 flashes in any 1-second window,
  no saturated-red full-frame flashes, and an exposure punch of +0.6 at most.
- **Licences:** record the source URL, author and licence of every kept asset
  (in the assets manifest). Composite-sketch and FBI photos must be confirmed as
  US federal works or otherwise free.

---

## 17. QC checklist: the "10×" bar

- [ ] Frame 1 is a moving picture; the title promise lands by 28.0 s; the
      total running time is 30.0 s.
- [ ] Every still is depth-projected or layered into at least 3 planes, with a
      motivated move and no stretch at 100 % zoom.
- [ ] No frame is static for more than 12 f (the title hold is at most 20 f).
- [ ] Grain is present on 100 % of frames; dark gradients show no banding at
      8-bit; black point ≥ `#0A0B0D`; nothing above 0.93 except the title's
      speculars.
- [ ] Looks are consistent per act; cross-act changes are deliberate
      (8–12 f blends).
- [ ] Text: verified strings only, inside title-safe, kerning checked, at most
      6 events.
- [ ] Every cut lands within ±1 f of its anchor (2 f before the stressed
      syllable, or on a music or SFX accent); modern bursts hit on the cut.
- [ ] Sound: −14 LUFS ±0.5, true peak ≤ −1 dBTP, no clicks; the VO is always
      intelligible; the silence drop is real; the riser stops on "secret".
- [ ] Flashes: at most 3 per second.
- [ ] Licences recorded; no synthetic imagery of real people.
- [ ] Watch it once with sound off and once with eyes closed. It must work both
      ways.

---

## 18. Engine notes (what this look needs beyond the SMC engine)

The previous engine (`projects/smc-order-breaker`) gives us: a frame-pure
renderer, a 60 → 30 fps 180° shutter blend, a final shader with zoom and
directional blur, CA, vignette, contrast, saturation and fades, Bokeh depth of
field, and a DOM overlay. Add:

1. A 16:9 canvas at 1920×1080 (the previous one was vertical).
2. `fx.look`, a blend of two LUTs:
   - three's `LUTPass` with `.cube` files generated from section 8, or a 3D
     texture lookup in the final shader;
   - add AgX tone mapping before it.
3. Grain (luma-weighted, animated per frame), halation (threshold, blur, tint,
   add), selective bloom (`UnrealBloomPass` on a glow layer), gate weave (a UV
   offset in the final pass), and the letterbox as a shader uniform
   `fx.bars` (0 to 1).
4. A `kit.photoMesh(texture, depth, { segs, depthScale, edgeCut })` depth-mesh
   photo projection, plus a background inpaint layer.
5. `kit.terrain(tiles, imagery, { exaggeration, snowMask, fog })` and a
   log-space altitude helper for camera keyframes.
6. Instanced trees and trunks for S6 (or depth-cut photo cards); particle
   systems for snow and dust; mist cards.
7. A 3D title from the Archivo 125/900 TTF (`TTFLoader` or opentype.js to
   `TextGeometry` with a bevel); an area light or narrow spot for the sweep.
8. Sub-frame accumulation (4–8 samples) for the whip, portal and slam frames.
9. Finishing:
   - H.264 High, `-tune film` (not `animation`: grain), CRF 14–16, BT.709 tags.
   - Optionally also upload a Lanczos-upscaled 2560×1440 master. YouTube then
     serves VP9 or AV1 at a much higher bitrate, which preserves grain and dark
     gradients.

---

## 19. Sources

**Reference tutorial and creator:**
- YouTube oEmbed for `5NUhMHzZUAY` (title and author):
  https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=5NUhMHzZUAY&format=json
- Frame stills from the public thumbnail CDN, `https://i.ytimg.com/vi/<id>/maxres{default,1,2,3}.jpg`,
  for `5NUhMHzZUAY`, `NUQyUctGQIQ` ("My Documentary Animation Workflow"),
  `dtc0cN2KXjM` ("How to EDIT Documentary Style Videos | After Effects
  Tutorial") and `mgEC7Bepq18` ("How to EDIT DOCUMENTARY Style videos | Full
  tutorial from scratch"), all by Vane Motion and confirmed via oEmbed. They
  are collected in `docs/reference/reference_frames.jpg`.
- Vane Motion's editing and animation course: https://vanemotion.gumroad.com/l/eomtxw
  (the workflow; plugins Trapcode Particular and Deep Glow).
- Vane Motion's store: https://vanemotion.gumroad.com/

**Title-sequence references:**
- Art of the Title: *Se7en* https://www.artofthetitle.com/title/se7en/ ·
  *True Detective* https://www.artofthetitle.com/title/true-detective/ ·
  *Zodiac* https://www.artofthetitle.com/title/zodiac/ ·
  *Mindhunter* (credits) https://www.artofthetitle.com/title/mindhunter/ ·
  *Manhunt* (HBO 2013) https://www.artofthetitle.com/title/manhunt-the-search-for-bin-laden/
- *Mindhunter*'s intro: https://bigshinyrobot.com/movies/mindhunter-an-intro-is-worth-a-thousand-words/ ·
  https://thefincheranalyst.com/2018/05/06/recreating-the-mindhunter-reel-to-reel-titles-minus-the-corpses/
- *Making a Murderer* main titles (Elastic; credits): https://vimeo.com/145672872
- *Unabomber: In His Own Words*: https://en.wikipedia.org/wiki/Unabomber:_In_His_Own_Words
  (theme "MAN" by The Worst).
- *Manhunt: Unabomber*: https://en.wikipedia.org/wiki/Manhunt:_Unabomber

**YouTube creators:**
- LEMMiNO's tools: https://lemmi.no/faq
- Johnny Harris maps (GEOlayers): https://aescripts.com/learn/how-johnny-harris-makes-maps/
  (search summary; the page returned 403 to direct fetch) ·
  physical props: https://rndr.beehiiv.com/p/5-visuals-next-video-ead0
- The MagnatesMedia style as freelancers describe it (secondary):
  https://www.upwork.com/freelance-jobs/apply/YouTube-Documentary-Animator-Motion-Graphics-Editor-Needed-Vox-MagnatesMedia-Style_~022061919757222663022/

**Sound and film look:**
- Trailer sound design: https://violetrecording.com/sound-design-for-trailers/ ·
  https://www.ableton.com/en/blog/learn-how-to-make-high-impact-sounds-for-movies-and-trailers/
- Gate weave: https://dehancer.com/learn/article/gate-weave

**Facts, standards and assets:**
- Facts: https://en.wikipedia.org/wiki/Ted_Kaczynski
- FBI cabin evidence photos (candidates; licences to be confirmed by the asset
  pass): Wikimedia Commons, e.g. `File:Exterior of Ted Kaczynski's cabin.jpg`,
  `File:Kaczynski cabin.jpg`, `File:Cabin outside 1 0.jpg`,
  `File:Interior of Ted Kaczynski's cabin.jpg`,
  `File:Newspaper clippings found in Ted Kaczynski's cabin.jpg`,
  `File:Exterior of Ted Kaczynski's cabin, showing windows in loft.jpg`,
  `File:Ted Kaczynski's cabin surrounded by fence.jpg`.
- Photosensitivity: https://www.w3.org/WAI/WCAG21/Understanding/three-flashes-or-below-threshold.html
- Fonts: https://fonts.google.com/specimen/Archivo ·
  https://fonts.google.com/specimen/IBM+Plex+Mono ·
  https://fonts.google.com/specimen/Courier+Prime
- Distances: haversine from Lincoln (46.958 N, −112.683 W) to Helena (46.589,
  −112.039) = 39.7 mi, Missoula (46.872, −113.994) = 62.2 mi and Great Falls
  (47.505, −111.301) = 75.1 mi.
