# Storyboard — "Order Block vs Breaker Block" (SMC short)

Vertical 1080×1920, 31.0 s. Voice-over (Roman Urdu) runs 0.00–29.47 s.

## The brief

The owner's reference is a 16 s TikTok-style explainer (`reference/` sheets):
white graph-paper background, a condensed bold maroon title at the top
("1. HAMMER") that fades in word by word, red/green candles popping in one at
a time, a black rounded highlight box drawn around the key candle, red/green
arrows drawn on, and a quick zoom-blur cut between sections.

Our film keeps that exact visual language and goes further:

- **Real 3D.** Glossy candles standing off the paper with soft shadows,
  extruded and bevelled titles, translucent glass zones, 3D arrows and
  icons, a camera that drifts, pushes and tilts over the paper.
- **More motion design.** Kinetic typography, label pills, light pools,
  particles, shockwaves, flips, a title morph, synced captions.
- **Sound design.** Every visual event that matters has a sound.
- **Premium finish.** Motion blur, zoom/whip-blur transitions with
  chromatic aberration, colour grade, vignette and grain.

Everything is synced to the word timings in `data/words.json`.

## Word timings (start, seconds)

```
Smart 0.14 | Money 0.48 | Concepts 0.68 | ko 1.12 | samajhna 1.30 | chahte 1.70 | hain? 2.02
Order 2.78 | Block 3.06 | woh 3.70 | zone 3.92 | hota 4.18 | hai 4.50 | jahan 4.80 | institutions 5.12
market 6.02 | mein 6.40 | entry 6.64 | le 6.94 | sakte 7.10 | hain, 7.40
jis 8.00 | ki 8.16 | wajah 8.28 | se 8.60 | price 9.06 | mein 9.44 | reaction 9.64 | aane 10.14
ka 10.38 | imkaan 10.60 | hota 11.04 | hai. 11.30
Jab 12.06 | yeh 12.24 | block 12.36 | fail 12.74 | ho 13.00 | jata 13.12 | hai 13.46 | aur 13.84
apna 14.14 | role 14.44 | reverse 14.72 | kar 15.10 | leta 15.26 | hai, 15.52
toh 16.04 | yeh 16.18 | Breaker 16.46 | Block 16.84 | ban 17.10 | jata 17.26 | hai. 17.56
Order 18.28 | Block 18.58 | potential 19.06 | entry 19.74 | ka 20.08 | signal 20.22 | deta 20.56 | hai, 20.84
jabke 21.38 | Breaker 21.75 | Block 22.12 | potential 22.68 | reversal 23.29 | ko 23.84 | show 24.00
karta 24.16 | hai. 24.50
In 25.20 | concepts 25.36 | par 25.84 | mastery 26.05 | hasil 26.49 | karein 26.81
aur 27.37 | zyada 27.67 | behtar 28.01 | trading 28.37 | decisions 28.67 | lein! 29.13 (ends 29.27)
```

In code, prefer `ctx.wt('institutions')` / `ctx.wt('Block', 2)` (nth
occurrence, 1-based) over typing the numbers.

## Scenes and cuts

| id | span (s) | content |
|---|---|---|
| `s1` | 0.00 – 2.45 | Hook: "SMART MONEY CONCEPTS" |
| `s2` | 2.45 – 11.70 | 1. Order Block: forms, institutions enter, price reacts |
| `s3` | 11.70 – 18.00 | The block fails, flips role, becomes 2. Breaker Block |
| `s4` | 18.00 – 24.90 | Comparison: Order Block = potential entry, Breaker Block = potential reversal |
| `s5` | 24.90 – 31.00 | Outro: master these concepts → better trading decisions |
| `captions` | 0.00 – 31.00 | Global word-synced captions |

Cuts happen at the peak of a blur transition (engine `TRANSITIONS`):
2.45 zoom, 11.70 whip (left→right), 18.00 zoom, 24.90 zoom. Each scene should
be moving into the cut (camera push / drift) in its last 0.2 s and moving
out of it in its first 0.3 s, so the blur reads as one continuous motion.

## Layout (pixels on the 1080×1920 frame)

Run previews with `--guides` to see these bands.

- **0–200**: top platform UI. Background only.
- **230–700 TITLE band** (blue): titles. Title centre ≈ y 450–480.
- **700–1420 MAIN band** (green): chart, zones, cards, icons, pills.
- **1440–1680 CAPTION band** (orange): reserved for captions. Scene
  objects may pass behind briefly, but no scene text or pills here.
- **1680–1920**: bottom platform UI. Background only.
- **x 960–1080, y 900–1700**: platform buttons. No text there.
- Keep all text within x 70–1010.

One grid cell = one world unit. `cam.frame({ width: 13.5 })` gives the
reference's cell size (~80 px). Wider framings are fine when a scene needs
more candles, but stay ≥ 55 px per cell (width ≤ 19.5) so candles read.

## Style rules

- Background: the engine's white graph paper. No dark scenes.
- Colours (`ctx.PAL`): candles `red`/`green`; titles `maroon` (reference
  title colour); highlight box `ink`; zones `zoneGreen` (order block,
  support) / `zoneRed` (breaker block, resistance); institutions `navy`;
  mastery / premium accents `gold`.
- Titles: 3D extruded `bebas` (the reference's condensed caps) in maroon,
  e.g. `1. ORDER BLOCK`, reference-style entrance: number first, then each
  word fades in from blur with a slight scale-down, plus a light sweep.
- **Section titles are pinned to the screen** so they sit in the same place
  whatever the camera does, and match exactly across the s2→s3 cut:
  `kit.text3d(text, { font: 'bebas', size: 1, depth: 0.3, color: PAL.maroon })`
  then every frame `ctx.pin(title.group, { x: 540, y: 470, z: 0.6, heightPx: 118, worldHeight: title.capH })`.
  Letter animation happens on `chars[i].holder` inside the pinned group.
  Use the same convention for any other titles (other y / heightPx are fine).
- Pills (DOM `.pill`): Montserrat 800 caps with an icon, colour-coded.
  Max 2 words. They pop in with overshoot and leave with a quick
  scale/blur out.
- Motion: snappy ease-outs (`outBack`, `outExpo`), nothing linear except
  continuous drifts. The camera always has a slow drift — never a dead frame.
- Every scene: a few floating dust specks for depth (`kit.dust`), subtle.
- Nothing may clip off-frame unintentionally; nothing may overlap text.

## Shared chart data (s2 and s3)

Both scenes build the same chart from `scenes/story-data.js` so the cut at
11.70 is continuous. Candle i is at x = i + 0.5 (cell centres).

The order block is candle 4 — the **last down candle before the strong up
move** (candles 5–7 displace up and break above candle 0's high, a break of
structure). Zone: y 2.9–4.4 (candle 4's low to high), starting at candle 4's
left edge (x 4.05).

| i | role | o | h | l | c |
|---|---|---|---|---|---|
| 0 | downtrend | 8.6 | 9.0 | 7.4 | 7.6 |
| 1 | downtrend | 7.6 | 7.9 | 6.2 | 6.4 |
| 2 | downtrend | 6.4 | 6.8 | 5.0 | 5.3 |
| 3 | downtrend | 5.3 | 5.6 | 3.9 | 4.1 |
| 4 | **ORDER BLOCK** (last red before impulse) | 4.1 | 4.4 | 2.9 | 3.2 |
| 5 | impulse | 3.2 | 5.9 | 3.0 | 5.7 |
| 6 | impulse | 5.7 | 8.3 | 5.5 | 8.1 |
| 7 | impulse, breaks structure | 8.1 | 10.6 | 7.9 | 10.3 |
| 8 | pullback | 10.3 | 10.6 | 8.9 | 9.1 |
| 9 | pullback | 9.1 | 9.3 | 7.0 | 7.2 |
| 10 | pullback | 7.2 | 7.4 | 5.2 | 5.4 |
| 11 | pullback taps the zone | 5.4 | 5.6 | 3.7 | 4.2 |
| 12 | reaction | 4.2 | 6.6 | 4.0 | 6.4 |
| 13 | reaction | 6.4 | 8.9 | 6.2 | 8.7 |
| 14 | reaction, new high | 8.7 | 11.6 | 8.5 | 11.3 |
| 15 | return down (s3) | 11.3 | 11.5 | 9.6 | 9.8 |
| 16 | return down | 9.8 | 10.0 | 7.6 | 7.8 |
| 17 | return down, reaches zone | 7.8 | 8.0 | 5.0 | 5.2 |
| 18 | **FAIL**: smashes through the zone | 5.2 | 5.4 | 1.2 | 1.5 |
| 19 | continuation | 1.5 | 1.7 | 0.2 | 0.4 |
| 20 | retrace up | 0.4 | 1.8 | 0.2 | 1.6 |
| 21 | retrace up | 1.6 | 2.7 | 1.5 | 2.4 |
| 22 | **REJECTION**: wick into zone from below | 2.4 | 3.8 | 2.0 | 2.1 |
| 23 | drop | 2.1 | 2.3 | 0.4 | 0.6 |
| 24 | drop | 0.6 | 0.8 | -1.1 | -0.9 |
| 25 | drop | -0.9 | -0.7 | -2.4 | -2.2 |

## Beat sheet

Times are seconds. **SFX** names refer to the audio palette (see bottom).
Each scene module lists its SFX in its `cues` export; the times below are the
minimum required cues — add more for any other event you animate.

### s1 — Hook (0.00–2.45)

- 0.00–0.30: open mid-motion: the camera rushes back from very close over the
  paper (zoom-blur easing out), revealing a background of glossy candles rising
  diagonally (a bullish chart, softly out of focus or dimmed) and dust.
  SFX `whoosh` at 0.10.
- 0.14 "SMART", 0.48 "MONEY", 0.68 "CONCEPTS": three 3D words slam in one
  after another (from in front of the camera down onto the paper, motion
  blur, a small camera shake on each landing). SMART and MONEY maroon,
  CONCEPTS green (or gold) and slightly larger, stacked in the title/main
  bands. SFX `impact` at 0.14, 0.48; `impact` + `shimmer` at 0.68.
- 0.8–2.2 "ko samajhna chahte hain?": slow orbit/push; a light sweep runs
  across the words; candles behind keep rising.
- 2.02 "hain?": a 3D question mark pops in with a springy bounce next to or
  under the title. SFX `pop` at 2.02.
- 2.25–2.45: camera pushes hard into the paper towards the cut.
  SFX `riser` ending at 2.45, `whoosh` peaking at 2.45.

### s2 — Order Block (2.45–11.70)

- 2.45–2.75: arrive on clean paper; title band empty, gentle drift.
- 2.70 / 2.78 / 3.06: title `1. ORDER BLOCK` types in reference-style
  ("1." then "ORDER" then "BLOCK"). SFX `tick` at 2.70, 2.78, 3.06.
- 3.00–3.60: candles 0–4 pop in (0.15 s apart), reference-style pop with
  overshoot. SFX `pop` per candle (pitch stepping down).
- 3.92 "zone": the black highlight box draws itself around candle 4
  (0.35 s), candle 4 glows. SFX `click` at 3.92.
- 4.18–4.75: impulse candles 5–7 grow fast upward (`grow` mode), small camera
  push. SFX `grow` at 4.18, 4.36, 4.54.
- 4.80–5.35 "jahan": the order-block zone grows out of candle 4 to the right
  (glass slab, green). The box fades. SFX `swipe` at 4.80.
- 5.12 "institutions": a 3D navy bank icon drops onto/above the zone with a
  bounce and a soft light pool; pill `INSTITUTIONS` (navy, bank icon).
  SFX `impact` (soft) at 5.18, `shimmer` at 5.25.
- 6.02–6.80 "market mein": order-flow particles / small 3D tokens stream from
  the bank into the zone. SFX `tick` ×4 between 6.02–6.6.
- 6.64 "entry": pill `ENTRY` (green, target icon) pops on the zone; zone
  pulses. SFX `ding` at 6.64.
- 7.4–8.0: institutions pill/icon leave; camera eases right/up so candles
  8–14 will fit.
- 8.00 / 8.20 / 8.45: pullback candles 8–10 pop. SFX `pop` each.
- 9.06 "price": candle 11 grows down into the zone (wick tags it); zone lights
  up as it's touched. SFX `click` at 9.10.
- 9.64 "reaction": zone pulse + shockwave ring; candles 12–14 grow up (9.64,
  9.84, 10.04); a green 3D arrow draws up from the zone (9.7–10.3); pill
  `REACTION` (green, up icon). Small camera kick. SFX `impact` at 9.64,
  `grow` at 9.84 and 10.04, `swipe` at 9.75.
- 10.4–11.5: hold the finished picture, slow push-in, specular glints.
- 11.50–11.70: camera starts whipping right into the cut.

### s3 — Breaker Block (11.70–18.00)

- 11.70: whip in from the left onto the same chart, already showing candles
  0–14, the green zone now extended far right (to x ≈ 27), and the title
  `1. ORDER BLOCK`. Camera frames candles ~11–25.
- 12.00 / 12.18 / 12.36 "block": candles 15–17 come back down to the zone.
  SFX `pop` each.
- 12.74 "fail": candle 18 smashes down through the zone (`grow`, very fast,
  0.18 s). Big hit: camera shake, red flash, the zone cracks / glitches and
  drains to grey, pill `FAILED` (red, x icon) slams in like a stamp; the
  title shakes and tints red briefly. SFX `boom` + `crack` at 12.74,
  `stamp` at 12.82.
- 13.05: candle 19 continues down. SFX `pop`.
- 13.84 "aur": pill `SUPPORT` (green, shield icon) appears at the zone.
- 14.00: candle 20 (green) begins the retrace up. SFX `pop`.
- 14.44–15.00 "role reverse": the zone **flips 180° in 3D** around its
  horizontal axis and comes out red; at 14.72 the `SUPPORT` pill flips over
  into `RESISTANCE` (red). SFX `flip` at 14.50, `click` at 14.72.
- 15.20: candle 21 (green) climbs to just under the zone. SFX `pop`.
- 16.04–16.30: candle 22 grows up into the zone from below and is rejected
  (long upper wick); zone pulses red. SFX `click` at 16.20.
- 16.46 "Breaker": the title **morphs** `1. ORDER BLOCK` → `2. BREAKER BLOCK`
  (old letters flip/scatter out, new ones flip in). SFX `impact` +
  `shimmer` at 16.46.
- 16.60 / 16.85 / 17.10: candles 23–25 drop; a red 3D arrow draws downward
  from the zone (16.6–17.3); camera follows down. SFX `grow` each (pitched
  down), `swipe` at 16.65.
- 17.10 "ban jata hai": pill `BREAKER BLOCK` (red) on the zone.
- 17.80–18.00: push in towards the cut.

### s4 — Comparison (18.00–24.90)

Two white 3D cards stacked vertically on the paper (they float above it and
cast shadows), each with a coloured header and a mini 3D chart.

- 18.00–18.28: arrive pulling back over the paper.
- 18.28 "Order Block": top card swings in (3D rotation settle). Header
  `ORDER BLOCK` (green). Its mini chart: drop into a green zone and a bounce.
  SFX `swipe` at 18.28.
- 19.06 "potential" / 19.74 "entry": big word `ENTRY` with a 3D target icon
  on the card; target locks on (rings snap in). SFX `ding` at 19.74.
- 20.22 "signal": signal pulse rings expand from the target. SFX `blip` at
  20.22.
- 21.38 "jabke": bottom card swings in; a `VS` badge pops between the cards.
  SFX `swipe` at 21.38, `pop` at 21.50.
- 21.75 "Breaker Block": header `BREAKER BLOCK` (red). Mini chart: break
  below a zone, retest from below, rejection. SFX `click` at 21.75.
- 22.68 "potential" / 23.29 "reversal": big word `REVERSAL` with a 3D
  reversal (swap-arrows) icon that flips; red arrow draws down. SFX `impact`
  + `flip` at 23.29.
- 24.00–24.70 "show karta hai": camera tilts/pulls to hold both cards, a
  soft light sweep across both.
- 24.70–24.90: push into the cut.

### s5 — Outro (24.90–31.00)

- 25.20–25.90 "In concepts": two chips `ORDER BLOCK` + `BREAKER BLOCK`
  (or mini zone tiles) fly in and stack. SFX `swipe` at 25.36, `pop` at 25.55.
- 26.05 "mastery": huge gold 3D `MASTERY` (or `MASTER THESE CONCEPTS`) slams
  in with a light sweep and a gold spark burst; optional 3D crown icon.
  SFX `impact` + `shimmer` at 26.05.
- 27.37–29.10 "aur zyada behtar trading decisions": a row of green candles
  grows up across the lower main band (ascending), a big green arrow draws
  up and to the right; the words `BETTER` (28.01), `TRADING` (28.37),
  `DECISIONS` (28.67) stack in, with a green check icon. SFX `pop` per
  candle (pitch stepping up), `impact` at 28.01, 28.37, 28.67.
- 29.13–29.40 "lein!": final pulse; everything kicks once; sparks.
  SFX `final` at 29.30.
- 29.40–31.00: slow push-in and gentle float; fade to white 30.55–31.00.

### captions (0.00–31.00)

Word-synced captions in the CAPTION band (centre y ≈ 1560): bold
Montserrat, short chunks (≤ 3 words / ≤ 20 characters, break at commas,
sentence ends and pauses > 0.25 s). Each word pops in exactly at its start
time; the current word is highlighted. Keyword colours: Smart Money Concepts
(gold), Order Block (green), Breaker Block (red), institutions (navy), entry
(green), reaction (green), fail (red), reverse (red), reversal (red),
mastery (gold), trading decisions (green). Chunks leave quickly (≤ 0.12 s)
when the next one starts or after a pause. No caption shows during long
pauses (> 0.5 s) after the chunk's last word has been up 0.35 s. Captions
blur with the transitions (the engine already blurs the whole overlay).

## Audio palette (cue names)

From the owner's library (`/home/user/gamehd8976/sfx`): `whoosh` (peak
0.89 s into the file), `click` (first hit 0.16 s), `drone` (low tension
hum; use in s3 between the fail and the breaker reveal). Synthesised:
`pop`, `grow`, `tick`, `impact`, `boom`, `crack`, `stamp`, `ding`, `blip`,
`swipe`, `flip`, `shimmer`, `riser`, `final`.

A cue is `{ t, sfx, gain?, pitch? }`: `t` is when the visual event happens
(the sound's transient/peak lands on it), `gain` in dB (default 0),
`pitch` in semitones (default 0).
