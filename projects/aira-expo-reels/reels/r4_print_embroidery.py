"""Reel 4 - "Print or embroidery?": the two AIRA campaign looks (printed; black
embroidered) and the pieces at the stall that carry each, cut to "Cat Walk"
(130 BPM). The track's drop lands on the switch from print to embroidery.

Looks: campaign standee in the printed outfit; campaign standee in the black
embroidered outfit; host holding pieces against herself; guest in navy kurta with
embroidered yoke.
Ends with a question CTA, then the reference's flare/eclipse into the logo card,
music dropping out like the reference (owner's whoosh as the flare hit).
"""
from common import rk, durations, hook, tip, label, build, logo_reveal_audio, pick

TRACK, B0 = 'cat_walk', 43          # 20.09 s, a downbeat; the drop (29.32 s, beat 63) lands on the 9.23 s cut
S, T = rk.Shot, rk.Tr

plan = [
    (1, rk.Black, T('gate', 20)),
    (4, lambda d: S('C0002', 0.5, d, speed=0.5, frame=[(0, (960, 540, 1.0, 0)), (1, (1000, 540, 1.05, 0))],
                    note='campaign look 1: printed outfit (standee)'), T('cut')),
    (3, lambda d: S('C0064', 54.5, d, speed=0.5, frame=[(0, (900, 540, 1.0, 0)), (1, (930, 540, 1.03, 0))],
                    note='host holds a black-and-gold print'), T('cut')),
    (3, lambda d: S('C0119', 10.0, d, speed=0.5, frame=[(0, (780, 540, 1.0, 0))], note='guest holds a multicolour print'),
     T('whip', 8, dir='left')),
    (3, lambda d: S('C0064', 118.6, d, speed=0.5, frame=[(0, (900, 540, 1.0, 0))], note='red floral print'), T('cut')),
    (2, lambda d: S('C0135', 1.2, d, speed=0.5, frame=[(0, (600, 540, 1.0, 0))], note='printed shirt shown to guests'),
     T('cut')),
    (4, lambda d: S('C0043', 2.8, d, speed=0.4, frame=[(0, (800, 540, 1.0, 0)), (1, (900, 540, 1.04, 0))],
                    note='floral prints on the rail'), T('flash', 6)),
    (3, lambda d: S('C0007', 0.4, d, speed=0.5, frame=[(0, (960, 540, 1.0, 0)), (1, (1000, 540, 1.05, 0))],
                    note='campaign look 2: black embroidered outfit (standee)'), T('cut')),
    (2, lambda d: S('C0017', 0.2, d, speed=0.5, frame=[(0, (1000, 540, 1.0, 0))], note='embroidered yoke close-up'),
     T('zoom', 8)),
    (3, lambda d: S('C0127', 1.2, d, speed=0.5, frame=[(0, (1075, 540, 1.0, 0)), (1, (1075, 520, 1.05, 0))],
                    note='look 3: guest wearing a navy kurta with gold-and-pink embroidered yoke'), T('cut')),
    (2, lambda d: S('C0071', 1.4, d, speed=0.3, frame=[(0, (980, 540, 1.0, 0))], fx=[('bw', 0.46, 0.62)],
                    note='beige sequin-embroidered kurta + AIRA tag, B&W beat flash'), T('cut')),
    (2, pick(lambda d: S('C0139', 2.4, d, speed=0.3, frame=[(0, (920, 540, 1.0, 0))],
                         note='gold floral embroidery + AIRA tag'),
             lambda d: S('C0070', 7.2, d, speed=0.3, frame=[(0, (900, 600, 1.15, 0))],
                         note='sequin and thread embroidery close-up, AIRA tag'),
             'C0139', 2.9), T('cut')),
    (3, lambda d: S('C0074', 2.2, d, speed=0.5, frame=[(0, (1000, 540, 1.0, 0))],
                    note='host shows a beige embroidered kameez'), T('cut')),
    (2, lambda d: S('C0070', 6.4, d, speed=0.4, frame=[(0, (860, 560, 1.0, 0))], note='blue embroidered kurta on hanger'),
     T('whip', 8, dir='right')),
    (4, lambda d: S('C0038', 0.3, d, speed=0.5, frame=[(0, (960, 540, 1.0, 0)), (1, (960, 540, 1.04, 0))],
                    note='stall wide, full AIRA wall'), T('eclipse', 17, flare_y=530)),
]

durs, music_start, cuts = durations(TRACK, B0, [p[0] for p in plan])
reel = rk.Reel('R04_Print_or_Embroidery')
for (beats, make, tr), d in zip(plan, durs):
    reel.add(make(d), tr)
reel.add(rk.Card(2.9))

reel.text(hook(['Print', 'or embroidery?'], size=66), 0.7, 2.4, cy=430)
reel.text(label('Print'), cuts[2] + 0.1, cuts[7] - 0.15, cy=330)
reel.text(label('Embroidery'), cuts[7] + 0.1, cuts[11] - 0.1, cy=330)
reel.text(tip(['Pick one statement, print', 'or embroidery, and keep the', 'rest of the look simple.'], size=50),
          cuts[11] + 0.1, cuts[14] - 0.1, cy=440)
reel.text(label("Which one's you?", size=44), cuts[14] + 0.1, cuts[15] - 0.35, cy=1260)

if __name__ == '__main__':
    build(reel, TRACK, music_start, **logo_reveal_audio(cuts))
