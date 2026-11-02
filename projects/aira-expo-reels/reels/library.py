"""Shot library for the text-free event reels (client-approved concept of R3/R4):
outside -> into the venue -> the AIRA shop and logo -> people inside -> products ->
AIRA wall -> logo card.

Each moment: (clip, stored-time in seconds, category, options). Options:
  cx, cy, z   framing in source px (default: auto - face-centred for people, centre otherwise)
  sp          playback speed (stored s per output s); 6p/3p clips are hyperlapses
  look        a complete outfit is clearly visible (SOP: at least 2 per reel)
Excluded on purpose: third-party brand items (MK handbag C0021, Dior sample cards
C0025-C0027, handbag shelf C0011/C0078/C0059 end, perfume box in hand C0058), phones/screens/keyboards
(C0081-C0082, C0099, C0101-C0104, C0117, C0137-C0141), spinning/blurred moments (C0044), the real-estate expo banners.
"""

EXT = [  # outside the venue: AIRA campaign standees, the fashion-expo banner, the walkway
    ('C0030', 0.3, dict(sp=0.3)), ('C0030', 1.1, dict(sp=0.3)), ('C0030', 2.2, dict(sp=0.3)),
    ('C0001', 0.4, dict(sp=0.6)), ('C0001', 2.6, dict(sp=0.6)), ('C0001', 4.0, dict(sp=0.5)),
    ('C0002', 0.3, dict(sp=0.5)), ('C0002', 1.8, dict(sp=0.5)),
    ('C0003', 1.6, dict(sp=0.5, cx=880)), ('C0003', 2.4, dict(sp=0.5, cx=900)),
    ('C0004', 0.6, dict(sp=0.5, cx=1668, cy=700, z=1.45)), ('C0004', 3.0, dict(sp=0.5, cx=1680, cy=700, z=1.45)),
    ('C0006', 0.8, dict(sp=0.5)), ('C0006', 4.5, dict(sp=0.5)),
    ('C0007', 0.3, dict(sp=0.5)), ('C0007', 1.6, dict(sp=0.5)),
    ('C0008', 0.8, dict(sp=0.5)), ('C0008', 4.0, dict(sp=0.5)),
]

HALL = [  # coming inside: the expo hall (hyperlapses) on the way to the stall
    ('C0028', 0.4, dict(sp=0.5)), ('C0028', 2.5, dict(sp=0.5)), ('C0028', 5.0, dict(sp=0.5)),
    ('C0056', 0.2, dict(sp=0.5)), ('C0056', 2.5, dict(sp=0.5)),
    ('C0030', 6.0, dict(sp=0.3)), ('C0029', 0.3, dict(sp=0.4)),
    ('C0049', 3.0, dict(sp=0.5)),
]

LOGO = [  # the AIRA wall letters
    ('C0022', 0.5, {}), ('C0022', 3.5, {}), ('C0023', 1.0, {}), ('C0023', 4.0, {}), ('C0024', 1.0, {}),
    ('C0024', 3.5, {}), ('C0034', 0.0, dict(sp=0.25, pan=(450, 1400))), ('C0035', 0.2, dict(sp=0.3)),
    ('C0036', 0.2, dict(sp=0.3)), ('C0057', 0.2, dict(sp=0.3)), ('C0024', 2.2, {}), ('C0023', 2.5, {}),
    ('C0029', 1.8, dict(sp=0.4)), ('C0013', 1.0, {}), ('C0039', 0.5, {}),
]

SHOP = [  # the stall: racks, staff arranging, the counter, the space
    ('C0010', 1.0, {}), ('C0010', 4.0, {}), ('C0012', 1.5, {}), ('C0012', 6.5, {}), ('C0014', 1.5, {}),
    ('C0016', 1.5, {}), ('C0016', 5.5, {}), ('C0031', 1.0, {}), ('C0031', 3.2, {}), ('C0033', 3.0, dict(sp=0.4)),
    ('C0033', 12.0, dict(sp=0.4)), ('C0033', 22.0, dict(sp=0.4)), ('C0033', 30.0, dict(sp=0.4)),
    ('C0040', 1.0, {}), ('C0041', 1.0, {}), ('C0045', 1.5, dict(echo=1)), ('C0046', 1.0, {}),
    ('C0046', 3.5, {}), ('C0047', 1.5, {}), ('C0047', 5.0, {}), ('C0048', 1.0, {}), ('C0052', 1.0, {}),
    ('C0053', 1.0, {}), ('C0054', 0.5, {}), ('C0055', 1.0, {}), ('C0019', 0.8, dict(sp=0.3)),
    ('C0020', 1.0, dict(sp=0.3)),
]

END = [  # stall wide with the whole AIRA word inside the 9:16 crop: flare / eclipse into the logo card.
    # cx (word centre, source px) read off tick-marked frames: the word is ~370-500 px wide in these
    # shots, so it fits the 607 px crop; the flare row comes from tools/letters.py
    ('C0037', 4.0, dict(cx=883)), ('C0037', 6.0, dict(cx=893)), ('C0038', 0.3, dict(cx=950)),
    ('C0013', 0.4, dict(cx=1152)), ('C0013', 2.2, dict(cx=1056)), ('C0010', 1.4, dict(cx=1162)),
    ('C0033', 3.0, dict(cx=912, sp=0.25)), ('C0033', 14.0, dict(cx=912, sp=0.25)),
    ('C0033', 26.0, dict(cx=912, sp=0.25)),
]

PEOPLE = [  # people inside the shop: host, guests, customers, families
    ('C0049', 5.0, dict(look=1)), ('C0049', 8.6, dict(look=1, z=1.2)), ('C0049', 11.0, dict(look=1)),
    ('C0060', 2.3, {}), ('C0065', 0.5, dict(cx=1000, z=1.05)),
    ('C0061', 3.0, dict(look=1)), ('C0061', 19.4, {}), ('C0061', 58.0, dict(look=1)), ('C0061', 97.0, {}),
    ('C0063', 10.5, dict(look=1)), ('C0063', 31.4, dict(look=1)), ('C0063', 52.4, dict(look=1)),
    ('C0064', 55.0, dict(look=1)), ('C0064', 86.2, {}), ('C0064', 119.0, dict(look=1)), ('C0064', 143.6, {}),
    ('C0068', 1.0, {}), ('C0068', 5.0, {}), ('C0069', 1.0, {}), ('C0069', 4.8, {}),
    ('C0072', 4.2, dict(look=1)), ('C0074', 7.0, dict(look=1)), ('C0075', 3.7, {}), ('C0075', 11.0, dict(look=1)),
    ('C0075', 18.4, {}), ('C0076', 1.3, {}), ('C0076', 6.4, dict(look=1)), ('C0077', 2.6, dict(look=1)),
    ('C0077', 7.7, {}), ('C0079', 1.8, {}), ('C0079', 8.8, {}),
    ('C0080', 6.0, dict(look=1)), ('C0080', 40.0, dict(look=1)), ('C0080', 70.0, {}),
    ('C0083', 1.0, {}), ('C0083', 7.0, {}), ('C0084', 1.0, dict(look=1)), ('C0086', 2.0, dict(look=1)),
    ('C0086', 6.0, dict(look=1)), ('C0087', 3.0, {}), ('C0088', 5.0, {}), ('C0089', 3.0, {}),
    ('C0090', 10.0, {}), ('C0090', 20.0, dict(look=1)), ('C0091', 1.6, dict(look=1)), ('C0091', 4.4, dict(look=1)),
    ('C0092', 3.0, {}), ('C0093', 9.0, dict(look=1)), ('C0095', 1.0, {}), ('C0097', 3.0, dict(look=1)),
    ('C0098', 1.4, dict(look=1)), ('C0098', 6.0, dict(look=1)), ('C0100', 2.0, {}), ('C0100', 7.5, dict(look=1)),
    ('C0105', 3.0, {}), ('C0107', 1.5, dict(look=1)), ('C0114', 1.5, {}), ('C0115', 3.0, {}), ('C0116', 7.0, dict(look=1)),
    ('C0118', 14.0, {}), ('C0118', 23.0, {}),
    ('C0119', 3.0, dict(look=1)), ('C0119', 20.0, dict(look=1)), ('C0120', 1.0, {}), ('C0121', 5.0, dict(look=1)),
    ('C0122', 4.0, dict(look=1)),
    ('C0123', 1.0, dict(look=1)), ('C0123', 7.6, dict(look=1)), ('C0123', 9.4, dict(look=1)),
    ('C0124', 12.6, dict(look=1)), ('C0124', 1.5, dict(look=1)),
    ('C0125', 5.0, dict(look=1)), ('C0125', 13.0, dict(look=1)),
    ('C0126', 1.0, dict(look=1)), ('C0126', 9.0, dict(look=1)),
    ('C0127', 0.3, dict(look=1)), ('C0127', 2.4, dict(look=1)), ('C0127', 4.4, dict(look=1)),
    ('C0128', 3.0, dict(look=1)), ('C0128', 9.0, dict(look=1)),
    ('C0129', 4.0, dict(look=1)), ('C0130', 4.0, dict(look=1)), ('C0130', 9.0, {}),
    ('C0132', 2.0, {}), ('C0133', 3.0, {}), ('C0133', 9.0, {}), ('C0134', 2.0, {}), ('C0127', 1.2, dict(look=1)),
    ('C0142', 1.0, dict(look=1)), ('C0142', 5.0, dict(look=1)), ('C0142', 11.0, dict(look=1)),
]

PRODUCT = [  # products: garments, embroidery, tags, fabric, packaging
    ('C0015', 1.8, dict(sp=0.4)), ('C0015', 5.0, dict(sp=0.4)), ('C0017', 0.2, dict(sp=0.4)),
    ('C0018', 0.8, dict(sp=0.4)), ('C0018', 2.2, dict(sp=0.4)), ('C0042', 1.0, {}), ('C0042', 3.0, {}),
    ('C0043', 1.2, {}), ('C0043', 3.4, {}), ('C0050', 1.6, {}), ('C0050', 4.6, {}), ('C0051', 1.3, {}),
    ('C0051', 3.8, {}), ('C0064', 13.2, dict(sp=0.3)), ('C0064', 15.5, dict(sp=0.3)),
    ('C0067', 1.3, dict(sp=0.4)), ('C0067', 3.6, dict(sp=0.4)), ('C0070', 0.6, dict(sp=0.3)),
    ('C0070', 5.6, dict(sp=0.4)), ('C0070', 9.0, dict(sp=0.4)), ('C0071', 0.4, dict(sp=0.3)),
    ('C0071', 1.4, dict(sp=0.3)), ('C0071', 4.0, dict(sp=0.3)), ('C0073', 2.4, {}), ('C0096', 0.5, dict(sp=0.3, z=1.1)),
    ('C0096', 1.6, dict(sp=0.3, z=1.15)), ('C0096', 2.6, dict(sp=0.3, z=1.1)), ('C0108', 0.3, dict(sp=0.4)),
    ('C0108', 1.4, dict(sp=0.4)), ('C0109', 2.0, dict(sp=0.4)), ('C0113', 2.2, dict(sp=0.5)),
    ('C0111', 5.8, dict(sp=0.3)), ('C0112', 0.3, dict(sp=0.4)), ('C0113', 0.8, dict(sp=0.5)),
    ('C0139', 0.6, dict(sp=0.3)), ('C0139', 2.4, dict(sp=0.3)), ('C0131', 1.4, dict(sp=0.4)),
    ('C0129', 1.5, dict(sp=0.4)), ('C0134', 1.0, dict(sp=0.4)), ('C0015', 3.4, dict(sp=0.4)),
]
