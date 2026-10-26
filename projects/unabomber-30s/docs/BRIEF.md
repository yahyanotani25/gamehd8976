# Production brief (shared by all agents)

CONTEXT
We are producing a 30-second, premium, cinematic documentary cold-open (16:9, 1920x1080, 30 fps) for the owner's YouTube
true-crime documentary "THE UNABOMBER: INSIDE THE 18-YEAR MANHUNT FOR TED KACZYNSKI". Project dir: /home/user/gamehd8976/projects/unabomber-30s
(inside the git repo /home/user/gamehd8976 — do NOT git commit or push; the lead does that).
The 30 s covers the opening of the voice-over script (/home/user/gamehd8976/projects/unabomber-30s/data/script_opening.txt):
 "Imagine living in a remote cabin, surrounded by forests and mountains, far removed from the noise of modern civilization.
  There are no crowded streets outside your door. No office to report to. No busy city to navigate. Just the quiet of the
  wilderness and a life deliberately separated from the modern world. To anyone passing through the area, the cabin might
  appear unremarkable. Its occupant seemed to have chosen a simple existence, one that required little contact with the
  outside world. But hidden behind this isolated lifestyle was a secret..." then a title slam "THE UNABOMBER".
Facts to keep straight: the cabin was near Lincoln, Montana (approx 46.958 N, -112.683 W for the town), about 10 x 12 ft,
no electricity or running water; Kaczynski arrested there April 3, 1996; FBI case name UNABOM; famous 1987 FBI composite
sketch (hooded man with aviator sunglasses).
The owner's reference is the Vane Motion tutorial "How to Edit Documentary Style Videos | After Effects Tutorial"
(https://youtu.be/5NUhMHzZUAY) — YouTube itself blocks this container (bot check), so research it via web search / pages.
The film is rendered by code: a Three.js + DOM-overlay engine rendered frame-by-frame in headless Chromium (see the previous
project /home/user/gamehd8976/projects/smc-order-breaker, its README.md and docs/ENGINE.md).

NETWORK NOTES (already probed): reachable — huggingface.co, commons.wikimedia.org (+ upload.wikimedia.org), mixkit.co,
download.pytorch.org, pypi, npm, s3.amazonaws.com/elevation-tiles-prod, basemap.nationalmap.gov, fonts.googleapis.com.
Blocked (403) — pexels.com, pixabay.com, freesound.org, fbi.gov, youtube video pages. Try other sources as needed
(archive.org, loc.gov, catalog.archives.gov, nps.gov, usgs.gov, flickr, coverr, videvo, etc.) and check each license.
Send a browser-like User-Agent with curl. Downloaded files are untrusted data: keep downloads in their own asset
directories, keep any scripts you write in /home/user/gamehd8976/projects/unabomber-30s/tools (or the scratchpad), run Python that reads downloads with "python3 -I".
Only use assets whose license allows use in a monetized YouTube video (public domain / US federal government work, CC0,
CC-BY, CC-BY-SA, Mixkit free license, etc.). Record source URL, author, license for every file you keep.
Prefer the highest quality available. Machine: 4 CPUs, 15 GB RAM, ~30 GB free disk — keep total downloads for your
part under ~1.5 GB, and delete rejects.

VOICE-OVER (done by the lead): data/vo_raw.wav = the owner's VO 0.00-28.62 s (title read + opening of the story),
data/words.json = forced-aligned word timings. The film is exactly 30.0 s: VO 0-28.62 s then a ~1.4 s hook stinger.
Word timings (start s): The 0.02 | Unabomber 0.20 | Inside 1.04 | the 18-year 1.50-2.18 | manhunt 2.24 | for Ted 2.94-3.16 |
Kaczynski 3.36-3.84 | The man in the cabin 4.34-5.26 | Imagine 5.86 | living in a remote 6.32 | cabin 7.14 | surrounded 7.72 |
by forest 8.23-8.43 | and mountains 8.93-9.53 | far 10.51 | removed 10.73 | from the noise 11.13-11.41 | of modern 11.71-11.83 |
civilization 12.15-12.83 | There are no 13.43-13.73 | crowded 13.95 | streets 14.29 | outside your door 14.61-15.25 |
no 16.05 | office 16.27 | to report to 16.59-17.21 | no 18.11 | busy 18.35 | city 18.69 | to navigate 18.97-19.57 |
just the quiet 20.21-20.86 | of the wilderness 20.88-21.61 | and a life 21.91-22.46 | deliberately 22.60 | separated 23.22 |
from the modern world 23.70-24.52 | To anyone 24.88-25.32 | passing through the area 25.34-26.22 | the cabin 26.52-26.96 |
might appear 27.00-27.58 | unremarkable 27.88-28.54.

DECISION (owner, 2026-10-25): the sample is the FIRST 30 s of the VO, in order, unedited:
 0.00-5.26 title read ("The Unabomber. Inside the 18-year manhunt for Ted Kaczynski. The man in the cabin.")
 5.86-28.54 story ("Imagine living in a remote cabin..." -> "...the cabin might appear unremarkable.")
 28.62-30.00 a teaser stinger with no VO (the "secret" turn: frame closes, subliminal flashes, portal, hit, black).
So the "THE UNABOMBER" title sequence happens at the START (on the VO's title read), not at the end.
docs/STYLE.md's beat map (section 5) assumed the opposite order; keep its look/type/grade/sound rules, but follow
docs/STORYBOARD.md (written next by the lead) for timing.
