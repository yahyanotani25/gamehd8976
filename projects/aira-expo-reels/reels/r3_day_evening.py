"""Reel 3 - "From daywear to evening": the expo by daylight (soft ivories, pastels,
the AIRA campaign standees outside) into the evening hall (jewel tones and gold),
cut to "Hazy After Hours" (121 BPM). The track's lift lands on the day->evening cut.

Day looks: AIRA campaign standees (print; black embroidered), host in ivory
embroidered kurta, white kaftan with blue embroidered neckline. Evening looks: guest
in white-and-gold saree, guest in bridal red saree with gold blouse, guest host in
rust kurta with gold embroidery, guest in dusty-rose saree. Ends like the reference:
flare hit, eclipse, silent logo card, fade to black.
"""
from common import rk, durations, hook, tip, label, build, logo_reveal_audio, pick

TRACK, B0 = 'hazy_after_hours', 12  # 6.0 s; the lift (15.91 s, beat 32) lands on the 9.92 s day->evening cut
S, T = rk.Shot, rk.Tr

plan = [
    (1, rk.Black, T('gate', 20)),
    (2, lambda d: S('C0030', 0.9, d, speed=0.3, frame=[(0, (820, 540, 1.0, 0)), (1, (860, 540, 1.04, 0))],
                    note='expo exterior by day, hyperlapse'), T('cut')),
    (3, lambda d: S('C0003', 2.0, d, speed=0.5, frame=[(0, (880, 540, 1.0, 0)), (1, (900, 540, 1.05, 0))],
                    note='AIRA campaign standee, printed look (day light)'), T('cut')),
    (3, lambda d: S('C0007', 0.6, d, speed=0.5, frame=[(0, (960, 540, 1.0, 0)), (1, (1000, 540, 1.04, 0))],
                    note='AIRA campaign standee, black embroidered look'), T('card', 22)),
    (2, lambda d: S('C0012', 2.4, d, speed=0.5, frame=[(0, (900, 540, 1.0, 0))], note='stall being dressed, daytime'),
     T('cut')),
    (3, lambda d: S('C0061', 9.0, d, speed=0.5, frame=[(0, (1150, 560, 1.04, 0)), (1, (1150, 560, 1.08, 0))],
                    note='day look: host, pastel floral-print kurta, embroidered yoke, printed dupatta'), T('cut')),
    (3, lambda d: S('C0091', 1.6, d, speed=0.5, frame=[(0, (650, 540, 1.0, 0)), (1, (690, 540, 1.03, 0))],
                    note='soft day tones: host with guest in peach'), T('cut')),
    (3, lambda d: S('C0098', 1.4, d, speed=0.5, frame=[(0, (860, 540, 1.0, 0))],
                    note='day look: white kaftan, blue embroidered neckline'), T('burn', 14, seed=33)),
    (2, lambda d: S('C0056', 0.2, d, speed=0.5, frame=[(0, (1000, 540, 1.0, 0))], note='the hall at night, hyperlapse'),
     T('cut')),
    (3, lambda d: S('C0049', 5.0, d, speed=0.5, frame=[(0, (880, 540, 1.0, 0)), (1, (880, 540, 1.04, 0))],
                    note='evening look: white saree with gold border'), T('flash', 6)),
    (3, pick(lambda d: S('C0142', 0.9, d, speed=0.5, frame=[(0, (790, 540, 1.0, 0)), (1, (810, 540, 1.04, 0))],
                         note='evening look: bridal red saree, gold blouse'),
             lambda d: S('C0127', 4.4, d, speed=0.5, frame=[(0, (1075, 540, 1.0, 0)), (1, (1075, 520, 1.05, 0))],
                         note='evening look: navy kurta with gold-and-pink embroidery'),
             'C0142', 2.0), T('cut')),
    (3, pick(lambda d: S('C0123', 9.0, d, speed=0.5, frame=[(0, (880, 540, 1.0, 0))],
                         note='evening look: rust kurta with gold-embroidered neckline'),
             lambda d: S('C0119', 4.0, d, speed=0.5, frame=[(0, (950, 540, 1.0, 0))],
                         note='evening look: dark kurta with gold embroidery'),
             'C0123', 9.9), T('cut')),
    (3, pick(lambda d: S('C0128', 4.5, d, speed=0.5, frame=[(0, (1180, 540, 1.0, 0))],
                         note='evening look: dusty-rose saree'),
             lambda d: S('C0049', 8.6, d, speed=0.5, frame=[(0, (760, 560, 1.22, 0))],
                         note='detail: white-and-gold saree, earrings and gold border'),
             'C0128', 5.6), T('zoom', 8)),
    (2, lambda d: S('C0064', 15.5, d, speed=0.3, frame=[(0, (1000, 540, 1.0, 0))], fx=[('bw', 0.5, 0.67)],
                    note='shimmer fabric, B&W beat flash'), T('whip', 8, dir='left')),
    (4, lambda d: S('C0037', 4.0, d, speed=0.5, frame=[(0, (885, 540, 1.0, 0)), (1, (885, 540, 1.03, 0))],
                    note='stall wide, full AIRA wall'), T('eclipse', 17, flare_y=700)),
]

durs, music_start, cuts = durations(TRACK, B0, [p[0] for p in plan])
reel = rk.Reel('R03_Day_to_Evening')
for (beats, make, tr), d in zip(plan, durs):
    reel.add(make(d), tr)
reel.add(rk.Card(2.9))

reel.text(hook(['From daywear', 'to evening'], size=64), 0.7, cuts[3] - 0.12, cy=430)
reel.text(label('Day'), cuts[3] + 0.12, cuts[8] - 0.2, cy=330)
reel.text(label('Evening'), cuts[8] + 0.15, cuts[10] - 0.1, cy=330)
reel.text(tip(['Day to evening? Swap soft', 'pastels for rich jewel tones', 'and add a touch of gold.'], size=50),
          cuts[10] + 0.1, cuts[12] + 0.6, cy=440)

if __name__ == '__main__':
    build(reel, TRACK, music_start, **logo_reveal_audio(cuts))
