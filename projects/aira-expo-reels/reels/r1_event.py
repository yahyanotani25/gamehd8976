"""Reel 1 - "Step inside AIRA": the expo recap, closest to the client's reference edit.

Shop -> products -> people, cut on the beat of "Winter Breeze" (120 BPM), with the
reference's transitions (film-gate opening, light-leak burn, photo card, whip, blur,
echo stutter, flash, B&W halftone beat flash, flare + eclipse into the logo card),
its colour grade and its ending (silent logo card, fade to black).

Looks: AIRA campaign standee (printed outfit); host in a pastel floral-print kurta
with embroidered yoke; guest in rust kurta with gold-embroidered neckline (or, if that
clip is unavailable, the guest in the navy kurta with embroidered yoke); guest in
white-and-gold saree; guest in bridal red saree with gold blouse.
"""
from common import rk, durations, hook, tip, build, logo_reveal_audio, pick

TRACK, B0 = 'winter_breeze', 47          # music from the 23.75 s downbeat: the track's drop (31.75 s) lands on the 8.0 s cut
S, T = rk.Shot, rk.Tr

plan = [  # (beats, source, transition to next)
    (1, rk.Black, T('gate', 20)),
    (2, lambda d: S('C0030', 0.35, d, speed=0.3, frame=[(0, (760, 540, 1.0, 0)), (1, (830, 540, 1.04, 0))],
                    note='expo exterior, hyperlapse'), T('cut')),
    (4, lambda d: S('C0001', 1.15, d, speed=0.6, frame=[(0, (1010, 540, 1.0, 0)), (1, (1030, 540, 1.06, 0))],
                    note='AIRA campaign standee: printed look (look 1)'), T('burn', 12, seed=9)),
    (2, lambda d: S('C0004', 1.0, d, speed=0.5, frame=[(0, (1668, 700, 1.45, 0)), (1, (1690, 700, 1.58, 0))],
                    note='Dhaka Fashion & Lifestyle Expo 2026 banner at the venue'), T('card', 24)),
    (3, lambda d: S('C0028', 0.45, d, speed=0.5, frame=[(0, (960, 540, 1.0, 0))], note='expo hall, hyperlapse'),
     T('whip', 8, dir='left')),
    (2, lambda d: S('C0034', 0.0, d, speed=0.25, frame=[(0, (450, 520, 1.05, 0)), (1, (1400, 520, 1.05, 0))],
                    note='AIRA wall letters, pan'), T('blur', 10)),
    (2, lambda d: S('C0045', 1.55, d, speed=0.6, frame=[(0, (600, 540, 1.0, 0)), (1, (830, 540, 1.0, 0))],
                    fx=[('echo', 0.42, 0.55)], note='stall reveal arc, echo stutter'), T('flash', 6)),
    (3, lambda d: S('C0061', 3.0, d, speed=0.5, frame=[(0, (1140, 560, 1.04, 0)), (1, (1140, 560, 1.09, 0))],
                    note='host: pastel floral-print kurta, embroidered yoke, printed dupatta (look 2)'), T('cut')),
    (2, lambda d: S('C0053', 3.0, d, speed=0.6, frame=[(0, (1300, 540, 1.0, 0)), (1, (1240, 540, 1.0, 0))],
                    fx=[('bw', 0.5, 0.67)], note='stall interior, B&W beat flash'), T('zoom', 8)),
    (2, lambda d: S('C0019', 0.8, d, speed=0.3, frame=[(0, (900, 560, 1.0, 0)), (1, (900, 560, 1.06, 0))],
                    note='stall decor detail (gold-antler deer), as in the reference'), T('cut')),
    (2, lambda d: S('C0096', 0.5, d, speed=0.3, frame=[(0, (900, 560, 1.1, 0)), (1, (1050, 560, 1.1, 0))],
                    note='stone-embellished neckline detail'), T('cut')),
    (3, pick(lambda d: S('C0123', 7.6, d, speed=0.5, frame=[(0, (860, 540, 1.0, 0))],
                         note='guest: rust kurta, gold-embroidered neckline, statement earrings (look 3)'),
             lambda d: S('C0127', 3.6, d, speed=0.5, frame=[(0, (1075, 540, 1.0, 0)), (1, (1075, 520, 1.05, 0))],
                         note='guest: navy kurta, embroidered yoke, statement earrings (look 3)'),
             'C0123', 8.7), T('whip', 8, dir='right')),
    (3, lambda d: S('C0049', 2.4, d, speed=0.5, frame=[(0, (760, 540, 1.0, 0)), (1, (790, 540, 1.03, 0))],
                    note='guest: white saree with gold border (look 4)'), T('flash', 6)),
    (2, lambda d: S('C0080', 6.0, d, speed=0.6, frame=[(0, (1040, 540, 1.0, 0))], note='VIP guest with host'), T('cut')),
    (1, lambda d: S('C0065', 0.5, d, speed=0.5, frame=[(0, (1000, 560, 1.05, 0))], note='little visitor'), T('cut')),
    (2, lambda d: S('C0113', 0.8, d, speed=0.5, frame=[(0, (1050, 540, 1.0, 0))], note='AIRA bag handed over'),
     T('whip', 8, dir='left')),
    (3, pick(lambda d: S('C0142', 0.6, d, speed=0.5, frame=[(0, (780, 540, 1.0, 0)), (1, (800, 540, 1.04, 0))],
                         note='guest: bridal red saree with gold blouse (look 5)'),
             lambda d: S('C0098', 6.0, d, speed=0.5, frame=[(0, (1150, 540, 1.0, 0))],
                         note='guest with the white kaftan, blue embroidered neckline (look 5)'),
             'C0142', 1.7), T('cut')),
    (2, lambda d: S('C0086', 2.0, d, speed=0.6, frame=[(0, (830, 540, 1.0, 0))], note='family at the AIRA wall'),
     T('cut')),
    (3, lambda d: S('C0037', 4.0, d, speed=0.5, frame=[(0, (885, 540, 1.0, 0)), (1, (885, 540, 1.03, 0))],
                    note='stall wide, full AIRA wall'), T('eclipse', 17, flare_y=700)),
]

durs, music_start, cuts = durations(TRACK, B0, [p[0] for p in plan])
reel = rk.Reel('R01_Step_Inside_AIRA')
for (beats, make, tr), d in zip(plan, durs):
    reel.add(make(d), tr)
reel.add(rk.Card(2.9))

reel.text(hook(['Step inside'], logo_width=330), 0.7, cuts[3] - 0.12, cy=430)
reel.text(tip(['Embellished neckline?', 'Skip the necklace and let', 'statement earrings lead.'], size=50),
          cuts[10] + 0.1, cuts[12] + 0.6, cy=430)

if __name__ == '__main__':
    build(reel, TRACK, music_start, **logo_reveal_audio(cuts))
