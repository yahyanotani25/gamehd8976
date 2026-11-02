"""Shot library for the store-event reels (AIRA store evening, 25 Sep 2026), same flow as
the expo reels: outside -> entrance -> AIRA logo -> shop -> people -> products -> AIRA
wall -> logo card.

Each moment: (clip, stored-time in seconds, options). Clip names: DJ_ = DJI Pocket (mostly
vertical), S1_/S2_ = Sony A7 III cards 1/2 (4K, 25p / 29.97p). Options:
  cx, cy, z   framing as fractions of the frame (default: face-centred for people,
              centre otherwise); a vertical clip already fills the 9:16 frame at z=1
  sp          playback speed (stored s per output s)
  look        a complete outfit is clearly visible (SOP: at least 2 per reel)

Excluded on purpose: third-party branding (a monogram-print bag DJ_0087, a designer
handbag in DJ_0130), phones/screens, out-of-focus and whip-pan moments.

Moments marked in the contact sheets of tools/prep_event.py; a clip whose footage is not
on disk is skipped by the planner (see available()).
"""
import os

EXT = [  # outside: the street, the AIRA standees and flower wall, the building at dusk
    ('DJ_0022', 1.0, {}), ('DJ_0022', 4.0, {}),
    ('DJ_0205', 1.0, {}), ('DJ_0205', 4.0, {}),
    ('DJ_0204', 1.0, {}), ('DJ_0207', 1.0, {}),
    ('S2_C2203', 1.0, dict(sp=0.6)), ('S2_C2200', 1.0, {}), ('S2_C2200', 4.0, {}),
    ('S2_C2201', 1.0, {}), ('S2_C2233', 1.0, dict(sp=0.6)),
]

HALL = [  # coming in: the welcome board, the flower-lined staircase
    ('DJ_0026', 1.0, {}), ('DJ_0027', 1.0, {}), ('DJ_0118', 1.0, {}), ('DJ_0111', 1.0, {}),
    ('S2_C2218', 1.0, {}), ('S2_C2218', 4.0, {}), ('S2_C2222', 1.0, {}), ('S2_C2204', 1.0, {}),
]

LOGO = [  # the AIRA name: welcome wall, the lit logo wall inside, the red AIRA sign
    ('DJ_0028', 1.0, {}), ('DJ_0029', 1.0, {}), ('DJ_0030', 1.0, {}), ('DJ_0040', 1.0, {}),
    ('DJ_0041', 1.0, {}), ('S2_C2214', 1.0, {}), ('S2_C2309', 1.0, {}),
]

SHOP = [  # the store: rails, gold shelves, the space
    ('DJ_0072', 1.0, {}), ('DJ_0112', 1.0, {}), ('DJ_0114', 1.0, {}),
    ('S2_C2241', 1.0, {}), ('S2_C2284', 1.0, {}), ('S2_C2300', 1.0, {}),
]

END = [  # the lit AIRA wall with the counter, whole word inside the 9:16 frame
    ('DJ_0164', 1.0, {}), ('DJ_0165', 1.0, {}), ('DJ_0150', 1.0, {}), ('DJ_0052', 1.0, dict(cx=0.75)),
]

PEOPLE = [  # guests and hosts in the store
    ('DJ_0074', 1.0, dict(look=1)), ('DJ_0075', 1.0, dict(look=1)), ('DJ_0115', 1.0, {}),
    ('DJ_0123', 1.0, dict(look=1)), ('DJ_0124', 1.0, dict(look=1)), ('DJ_0132', 1.0, dict(look=1)),
    ('DJ_0139', 1.0, {}), ('DJ_0141', 1.0, dict(look=1)), ('DJ_0145', 1.0, {}), ('DJ_0154', 1.0, {}),
    ('DJ_0169', 1.0, dict(look=1)), ('DJ_0194', 1.0, {}), ('DJ_0201', 1.0, dict(look=1)),
    ('S2_C2228', 1.0, {}), ('S2_C2280', 1.0, dict(look=1)), ('S2_C2378', 1.0, {}),
]

PRODUCT = [  # garments on the rails: prints, embroidery, finishing details
    ('DJ_0043', 1.0, {}), ('DJ_0079', 1.0, {}), ('DJ_0080', 1.0, {}), ('DJ_0081', 1.0, {}),
    ('DJ_0084', 1.0, {}), ('DJ_0093', 1.0, {}), ('DJ_0094', 1.0, {}), ('DJ_0096', 1.0, {}),
    ('DJ_0098', 1.0, {}),
]


def available(dirs):
    """Drop moments whose clip has no footage (original or proxy) in any of `dirs`."""
    def ok(clip):
        return any(os.path.exists(os.path.join(d, clip + ext)) for d in dirs for ext in ('.MP4', '.mp4'))
    g = globals()
    for name in ('EXT', 'HALL', 'LOGO', 'SHOP', 'END', 'PEOPLE', 'PRODUCT'):
        g[name] = [m for m in g[name] if ok(m[0])]
