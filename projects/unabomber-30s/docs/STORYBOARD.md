# Storyboard — "THE UNABOMBER" 30 s sample

1920×1080, 30 fps (rendered at 60 fps, folded to 30 with a 180° shutter), 30.00 s.
The owner's VO runs 0.00–28.62 s unedited (`data/vo_raw.wav`); word times
come from `data/words.json` (read them with `ctx.wt(word, nth)`). Look, type,
grade and sound rules are in `docs/STYLE.md`; where this file and STYLE.md's
section 5 beat map disagree, **this file wins** (STYLE.md assumed the title
at the end; the owner chose the VO in order, so the title is at the start).

Picture cuts land **2 frames before** the stressed syllable they illustrate;
SFX hits land on the cut frame. All times below are seconds of film time.

## Word timings (start–end)

```
The 0.02 | Unabomber 0.20-0.68 | Inside 1.04-1.48 | the 1.50 | eighteen 1.70-2.02 | year 2.04-2.18
manhunt 2.24-2.72 | for 2.94 | Ted 3.16-3.32 | Kaczynski 3.36-3.84
The 4.34 | man 4.50-4.68 | in 4.74 | the 4.82 | cabin 4.92-5.26
Imagine 5.86-6.28 | living 6.32-6.58 | in a | remote 6.80-7.11 | cabin 7.14-7.46
surrounded 7.72-8.19 | by 8.23 | forest 8.43-8.85 | and 8.93 | mountains 9.03-9.53
far 10.51 | removed 10.73-11.11 | from 11.13 | the | noise 11.41-11.69 | of | modern 11.83-12.11 | civilization 12.15-12.83
There 13.43 | are | no 13.73 | crowded 13.95-14.25 | streets 14.29-14.57 | outside 14.61 | your 14.89 | door 15.03-15.25
no 16.05 | office 16.27-16.57 | to 16.59 | report 16.69-17.05 | to 17.11-17.21
no 18.11 | busy 18.35-18.57 | city 18.69-18.89 | to 18.97 | navigate 19.09-19.57
just 20.21 | the | quiet 20.57-20.86 | of | the | wilderness 21.09-21.61
and 21.91 | a | life 22.14-22.46 | deliberately 22.60-23.10 | separated 23.22-23.66 | from 23.70 | the | modern 23.96-24.24 | world 24.28-24.52
To 24.88 | anyone 25.02-25.32 | passing 25.34-25.66 | through 25.68 | the | area 26.00-26.22
the 26.52 | cabin 26.66-26.96 | might 27.00 | appear 27.22-27.58 | unremarkable 27.88-28.54
(VO ends 28.62)
```

## Scenes (one builder each)

| id | span | content | acts / look |
|---|---|---|---|
| `s1` | 0.00 – 5.60 | Title sequence on the title read + chapter card, fly-through into mist | `secret` → mist |
| `s2` | 5.60 – 13.87 | Living photo of the cabin → pull-back through branches → 3D terrain, location super, isolation rings | `wild` |
| `s3` | 13.87 – 20.17 | Negation triplet: modern burst → match cut to silent wilderness, ×3 | `modern` / `wild` |
| `s4` | 20.17 – 24.85 | The breath (slow misty forest), then The Divide (city | cabin split) | `wild` |
| `s5` | 24.85 – 28.55 | Glimpse through the trees → frontal "unremarkable" cabin, dimension lines, facts | `cabin` |
| `s6` | 28.55 – 30.00 | Stinger: frame closes, push to the window, 3 subliminal flashes, portal, hit, end card | `secret` |

Scene boundaries are where the builder's span ends; adjacent builders agree on the
handoff described in each section.

---

## s1 — Title (0.00 – 5.60)

**Idea.** The film opens inside the case: darkness, a slit of warm lamp light with
dust motes, the 1987 composite sketch looming as a ghost. The VO says "The
Unabomber" and the title strikes in like typebars and lands with the hit.

| t | VO | picture | sound |
|---|---|---|---|
| 0.00 | "The" | Near-black frame already moving: a slit of `lamp` light from upper left, 20–40 dust motes drifting through it; camera 3° yawed, drifting. Kicker **"THE"** (Plex Mono 600, `red`) types on in 4 f at 0.02. | Room tone; one typewriter key strike at 0.00 |
| 0.03–0.20 | | Letters of **UNABOMBER** (Archivo 125/900, extruded 3D, `bone` face / `char` metal sides) strike in left→right, ~1 letter per frame (pairs allowed), final letters on the hit | Typebar clacks, one per letter |
| **0.20** | "U-nabomber" | **HIT**: exposure +0.5 decaying 10 f, CA 2.5→0.4 over 8 f, shake 6 px over 5 f, scale 1.04→1.00 `outExpo` 16 f. Camera starts settling frontal over 60 f. | **Title hit** (transient + taiko/braam on low D + sub sweep 60→28 Hz), long dark tail; underscore begins out of the hit |
| 0.53–1.87 | | Light sweep (narrow `lamp` spot) crosses the bevels left→right; selective bloom on speculars | Soft metallic shimmer |
| 0.70→ | | Ghost: the composite sketch, inverted light-on-dark, 12 % opacity, blurred 6 px, ~6 units behind, hood + glasses just above the word; scale 1.00→1.03 | — |
| 1.00–2.75 | "Inside the eighteen-year manhunt" | Subtitle line 1 **"INSIDE THE 18-YEAR MANHUNT"** (Plex Mono 500, 22 px, +0.32 em, `fog`) per-character fade, 1 f stagger, 6 px rise. The "18" digits roll 00→18 during "eighteen" (1.70–2.02) and lock. | Very soft tick on the lock |
| 2.90–3.85 | "for Ted Kaczynski" | Line 2 **"FOR TED KACZYNSKI"** appears under a `char`/`redDeep` redaction bar that slides off right→left at 3.10–3.40 (`outExpo`), revealing the name — declassified | Paper slide / soft swipe |
| 3.9–4.30 | | Slow push-in on the whole title card | Tail rings |
| 4.30–5.30 | "The man in the cabin" | Chapter marker **"01 · THE MAN IN THE CABIN"** (Plex Mono 500, 20 px, `bone` 90 %) types on at 45 cps at lower left (x 120, y 930) with block cursor | 1–2 soft key clicks |
| 5.05–5.60 | | **Z-space fly-through**: camera accelerates (`inCubic`) forward through the gap between the letters; title and ghost pass the lens; a mist card fills the frame at 5.50–5.60 (handoff to s2) | Owner's `whoosh.mp3` with its peak (0.89 s in) at **5.55**, low-passed ~5 kHz |

Handoff: s1 ends inside a bright-grey mist card (`fog` → `frost`), full-frame at 5.55–5.60.

---

## s2 — Cabin to terrain (5.60 – 13.87)

**Idea.** "Imagine living in a remote cabin" — we start tight on the real cabin
(1996 FBI photo) as a living photograph and pull back in one continuous move
(the "Powers of Ten" oner): through branches, through mist, up over the real
valley, until the cabin is a red dot surrounded by distance.

| t | VO | picture | sound |
|---|---|---|---|
| 5.60–5.85 | | Mist clears (mist card dissolves/passes) revealing the cabin | Whoosh tail; wind bed fades up |
| 5.85–7.60 | "Imagine living in a remote cabin" | **Living photograph** of the FBI cabin exterior in snow: depth mesh, falling snow (foreground bokeh), a smoke wisp from the stovepipe, slow pull-out (3–6 %/s), breathing camera | Wind in pines; low felt-piano note at ~5.9 |
| 7.60–8.15 | "surrounded" | Pull-back accelerates up through 3D branches (foreground trunk/branch cards pass the lens, motion-blurred) and into a mist card | Owner's `whoosh.mp3` peak at **8.05**, low-passed (reads as air) |
| 8.15–9.60 | "by forest and mountains" | Emerge above **real 3D terrain** (closeup box → regional box), patchy snow, `exp2` fog, altitude rising in log space (~600 m → ~5 km above ground by 12.8). A red pin (6 px `red`, 1 px `bone` ring) marks the cabin area. | Thin high air layer; distant raven once (~9.0) |
| 8.60–9.40 | | Location super types on at 45 cps: **"NEAR LINCOLN, MONTANA"** (Plex Mono 500, 26 px, `bone` 92 %, red 8 px bullet) and **"46°57′N 112°41′W"** (20 px, `fog`) at left x 120, baseline y 930 | 2–3 soft key ticks |
| 10.45–11.30 | "far removed" | **Isolation rings**: 3 `mapline` rings (1.5 px, 60 %) expand from the pin, staggered 6 f, `outExpo` 24 f | Soft low "ring" pulse per ring |
| 11.00–12.40 | "from the noise of modern civilization" | Leaders slide out to frame edges: **"HELENA · 40 MI"** (bearing 130°), **"MISSOULA · 62 MI"** (265°), **"GREAT FALLS · 75 MI"** (59°), each ending at a faint warm city glow at the frame edge | Faint, distant city murmur under "noise" (11.4), filtered, gone by 12.8 |
| 12.40–13.87 | "…civilization. There are no" | Camera keeps rising; labels/rings fade by 13.4; the frame is vast and quiet | Wind only; everything thins for the burst |

Handoff: hard cut at 13.87.

---

## s3 — The negation triplet (13.87 – 20.17)

**Idea.** The negation is the cut itself, no "NO" text: each "no …" is a loud,
harsh modern clip (the `modern` look, fluorescent green-cyan, contrast 1.15, CA
0.8), then a hard match cut to a silent wilderness shot with the same
composition or motion vector. Modern clips get shorter: 22 f, 20 f, 16 f.

| t | VO | picture | sound |
|---|---|---|---|
| **13.87** | "crowded streets" | **CUT** crowd moving L→R (modern) | Crowd walla + traffic burst on the cut (momentary −20 LUFS) |
| **14.60** | "outside your door" | **MATCH CUT** snow drifting L→R across pines (wild), slow drift | Burst cut with 5 ms fade → wind; snow creak |
| **16.20** | "office" | **CUT** fluorescent office ceiling grid / keyboards (modern) | Phones, keys, HVAC burst |
| **16.87** | "report to" | **MATCH CUT** bare branches against overcast sky (grid matches) | Silence + branch creak |
| **18.27** | "busy city" | **CUT** night traffic light trails (modern) | Horn + traffic burst |
| **18.80** | "to navigate" | **MATCH CUT** still creek / snowfield at dusk (horizontal line matches) | Silence + trickling water |
| 18.80–20.17 | | Hold, very slow push | Wind returns softly |

Handoff: s4 begins at 20.17 with a soft 6 f dissolve or a straight cut to the breath plate.

---

## s4 — The breath and the divide (20.17 – 24.85)

| t | VO | picture | sound |
|---|---|---|---|
| 20.17–21.85 | "just the quiet of the wilderness" | **The breath**: the longest-feeling image. Misty forest (slow motion 25–40 % if footage, else living photograph) with god rays and drifting mist; push 1.5 %/s. No text. | Wind almost gone; felt-piano note 2 on "quiet" (20.57); one distant bird |
| **21.88** | "and a life" | **The Divide**: a 1 px `bone` hairline at 70 % draws top→bottom at frame centre (6 f). Left half = night city (`modern`), right half = the cabin in the woods (`wild`) | City hum panned hard left enters |
| 22.6–23.1 | "deliberately" | Hold the split; tiny push on both halves | — |
| 23.15–24.45 | "separated from the modern world" | The line sweeps left (`inOutCubic`, 1.3 s), pushing the city out of frame; the line lands as an aspen trunk / tree edge in the forest half | City hum fades with the line; forest takes over |
| 24.45–24.85 | | Forest/cabin frame settles, slight lateral drift into s5 | — |

Handoff: s5 begins with a lateral truck — keep s4's last 0.3 s drifting left→right.

---

## s5 — The cabin (24.85 – 28.55)

| t | VO | picture | sound |
|---|---|---|---|
| 24.85–26.45 | "To anyone passing through the area" | **Glimpse through the trees**: lateral truck at constant speed past 3D trunks (instanced cards, DOF + motion blur); the cabin plate sits midground and appears in 2–3 gaps | Car pass-by L→R on gravel (~1.6 s) |
| 26.45–27.70 | "the cabin might appear" | Truck eases out (1.2 s) into the flat, frontal, ordinary framing of the FBI cabin exterior (living photograph, `cabin` look) | Car fades away; one wood creak; owner's `click-double.mp3` first hit at **26.62** as an evidence-camera shutter on the settle frame |
| 27.00–27.60 | | Architectural dimension lines draw on the cabin: **"10 FT"**, **"12 FT"** (2 px `bone` 85 %, 12 px end ticks, `outExpo` 14 f each) | Scribe tick per line |
| 27.85–28.55 | "unremarkable" | Facts line types on: **"NO ELECTRICITY · NO RUNNING WATER"** (Plex Mono 500, 20 px, +0.18 em) lower third, left-aligned to the print edge; 2 %/s push toward the dark window begins | Owner's `low-drone.mp3` (trimmed, +14 dB) fades in from 26.8; tick pulse starts at 27.9 (72 BPM) |

Handoff: s6 continues the push on the same cabin image.

---

## s6 — Stinger (28.55 – 30.00)

| t | picture | sound |
|---|---|---|
| 28.55–28.95 | Letterbox closes 1.78 → 2.39:1 (`inOutCubic`, 12 f); the push toward the dark window speeds up (speed ramp); look blends to `secret` (near-black, desaturated, red kept); text from s5 fades | Low "shutter" thump on the bars; ticks accelerate 72 → 144 BPM; riser builds (2 s, from ~27.6) |
| 28.85 | Flash 1 (2 f): the 1987 composite sketch, cropped to hood + glasses (`secret`) | Sharp transient |
| 29.15 | Flash 2 (2 f): `manila` card typed **"UNABOM"** (Courier Prime 700, ink treatment) with a redaction bar sliding | Sharp transient + typebar |
| 29.42 | Flash 3 (2 f): newspaper clippings found in the cabin / the fenced cabin, 1996 | Sharp transient |
| 29.45–29.60 | **Portal**: camera passes through the window into black (Z-space push, focal narrowing, exposure → 0) | Riser **hard-stops** at 29.58 (suck-out); room tone |
| **29.62** | **HIT** on near-black: a final card fades in from the hit — **"UNABOM"** (Courier Prime 700, ink, `bone`) small over **"1978 — 1995"** (Plex Mono, `fog`); grain continues | Big final hit (transient + body + sub), tail rings past the end |
| 30.00 | End (hard cut to black on the last frame if needed) | Tail cut at 30.00 with a 20 ms fade |

Flashes: at most 3 in any 1 s window; no saturated-red full-frame flashes.

---

## Global

- **Grain, gate weave, vignette, halation** on every frame (engine post); letterbox
  `fx.bars` only from 28.55.
- **Captions**: none burned in; `data/captions.srt` ships for YouTube CC.
- **Text events** (verified strings only): THE / UNABOMBER / INSIDE THE 18-YEAR
  MANHUNT / FOR TED KACZYNSKI / 01 · THE MAN IN THE CABIN / NEAR LINCOLN, MONTANA +
  46°57′N 112°41′W / HELENA · 40 MI, MISSOULA · 62 MI, GREAT FALLS · 75 MI /
  10 FT, 12 FT / NO ELECTRICITY · NO RUNNING WATER / UNABOM / 1978 — 1995.
- **Owner's SFX used**: `whoosh.mp3` at 5.55 and 8.05 (mist pass-throughs),
  `click-double.mp3` at 26.62 (evidence shutter), `low-drone.mp3` under 26.8–29.6
  (the stinger build). Nowhere else.
- **Assets per shot**: see the "Asset picks" section (filled after the asset pass).

## Asset picks

_(to be filled from assets/photos, assets/footage, assets/music, assets/sfx inventories)_
