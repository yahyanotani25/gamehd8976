"""Reel 2 - "The details make the difference": embroidery, necklines, tags, fabric
movement and packaging, cut to "House 02" (123 BPM, steady deep house).

Looks: guest in navy kurta with gold-and-pink embroidered yoke + matching navy
dupatta, guest in rust kurta with gold-embroidered neckline + matching rust dupatta
(both demonstrate the tip; if the rust clip is unavailable, the guest in a peach kurta
with matching peach dupatta), host in pastel floral-print kurta with embroidered yoke.
Ends like the reference: flare hit, eclipse, silent logo card, fade to black.
"""
from common import rk, durations, hook, tip, build, logo_reveal_audio, pick

TRACK, B0 = 'house_02', 19          # 9.58 s: a section start on a downbeat
S, T = rk.Shot, rk.Tr

plan = [
    (1, rk.Black, T('gate', 20)),
    (4, lambda d: S('C0096', 0.2, d, speed=0.3, frame=[(0, (950, 560, 1.15, 0)), (1, (1010, 560, 1.24, 0))],
                    note='stone-embellished neckline, slow push'), T('cut')),
    (3, lambda d: S('C0017', 0.0, d, speed=0.4, frame=[(0, (1000, 540, 1.0, 0)), (1, (1000, 540, 1.05, 0))],
                    note='AIRA campaign standee: embroidered yoke'), T('card', 22)),
    (2, lambda d: S('C0070', 0.6, d, speed=0.3, frame=[(0, (1150, 540, 1.0, 0)), (1, (1250, 540, 1.04, 0))],
                    note='embroidered sleeve close-up'), T('cut')),
    (3, lambda d: S('C0070', 5.6, d, speed=0.4, frame=[(0, (850, 560, 1.0, 0)), (1, (850, 560, 1.06, 0))],
                    note='blue sequin-embroidered kurta with AIRA tag, AIRA wall behind'), T('whip', 8, dir='left')),
    (2, lambda d: S('C0071', 0.4, d, speed=0.3, frame=[(0, (980, 540, 1.0, 0))],
                    note='beige sequin-embroidered kurta, AIRA tag'), T('cut')),
    (2, pick(lambda d: S('C0139', 0.6, d, speed=0.3, frame=[(0, (960, 540, 1.0, 0)), (1, (960, 540, 1.05, 0))],
                         note='gold floral embroidery + AIRA tag'),
             lambda d: S('C0072', 4.2, d, speed=0.4, frame=[(0, (620, 540, 1.0, 0))],
                         note='host shows a beige embroidered kameez, AIRA tag'),
             'C0139', 1.1), T('flash', 6)),
    (3, lambda d: S('C0127', 0.3, d, speed=0.5, frame=[(0, (1075, 540, 1.0, 0)), (1, (1075, 520, 1.05, 0))],
                    note='look 1: navy kurta, embroidered yoke, matching navy dupatta'), T('cut')),
    (3, pick(lambda d: S('C0123', 8.4, d, speed=0.5, frame=[(0, (900, 540, 1.0, 0)), (1, (910, 540, 1.04, 0))],
                         note='look 2: rust kurta, gold-embroidered neckline, matching rust dupatta'),
             lambda d: S('C0091', 4.4, d, speed=0.5, frame=[(0, (1580, 540, 1.0, 0))],
                         note='look 2: peach kurta with matching peach dupatta'),
             'C0123', 9.5), T('cut')),
    (3, lambda d: S('C0127', 2.4, d, speed=0.5, frame=[(0, (830, 540, 1.0, 0)), (1, (830, 540, 1.04, 0))],
                    note='host and navy-kurta guest at the AIRA wall (two complete looks)'), T('zoom', 8)),
    (2, lambda d: S('C0064', 14.0, d, speed=0.3, frame=[(0, (1000, 540, 1.0, 0))], note='shimmer fabric movement'),
     T('cut')),
    (2, lambda d: S('C0073', 3.0, d, speed=0.5, frame=[(0, (1100, 540, 1.0, 0))], fx=[('bw', 0.49, 0.66)],
                    note='host holds the shimmer kaftan, B&W beat flash'), T('whip', 8, dir='right')),
    (2, lambda d: S('C0119', 12.0, d, speed=0.4, frame=[(0, (560, 520, 1.25, 0))],
                    note='beaded, embroidered neckline on a printed piece'), T('cut')),
    (2, lambda d: S('C0108', 0.3, d, speed=0.4, frame=[(0, (950, 540, 1.0, 0))], note='AIRA bag with gold seal'),
     T('cut')),
    (2, lambda d: S('C0111', 6.0, d, speed=0.3, frame=[(0, (1050, 540, 1.0, 0))], note='seal and ribbon close-up'),
     T('cut')),
    (4, lambda d: S('C0038', 0.3, d, speed=0.5, frame=[(0, (960, 540, 1.0, 0)), (1, (960, 540, 1.04, 0))],
                    note='stall wide, full AIRA wall'), T('eclipse', 17, flare_y=530)),
]

durs, music_start, cuts = durations(TRACK, B0, [p[0] for p in plan])
reel = rk.Reel('R02_The_Details')
for (beats, make, tr), d in zip(plan, durs):
    reel.add(make(d), tr)
reel.add(rk.Card(2.9))

reel.text(hook(['The details', 'make the difference'], size=62), 0.7, 3.0, cy=430)
reel.text(tip(['Match your dupatta to the', "kurta's base colour and let", 'the embroidery shine.'], size=50),
          cuts[7] + 0.15, cuts[9] - 0.05, cy=430)

if __name__ == '__main__':
    build(reel, TRACK, music_start, **logo_reveal_audio(cuts))
