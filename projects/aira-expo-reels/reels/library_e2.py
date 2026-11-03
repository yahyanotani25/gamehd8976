"""Shot library for the store-event reels (AIRA store evening, 25 Sep 2026), same flow as
the expo reels: outside -> entrance -> AIRA logo -> shop -> people -> products -> AIRA
wall -> logo card.

Each moment: (clip, stored-time in seconds, options). Clip names: DJ_ = DJI Pocket
(1728x3072 vertical or 3840x2160, 59.94p), S2_ = Sony A7 III card 2 (3840x2160, 29.97p).
Options:
  cx, cy, z   framing as fractions of the frame (default: face-centred for people and
              outside shots, centre otherwise); a vertical clip fills the 9:16 frame at z=1
  sp          playback speed (stored s per output s); by default the planner never goes
              slower than the clip's frame rate allows (0.5 for 60p, 1.0 for 30p)
  pan         (cx0, cx1) horizontal move across the shot (a word wider than the 9:16 crop)
  hold        no push-in or drift (a word that only just fits the crop)
  look        a complete outfit is clearly visible (SOP: at least 2 per reel)

Moments picked from timestamped contact sheets of every clip. Left out on purpose:
third-party branding (the AVIORA sign at the top of the stairs S2_C2222, the perfume-brand
shelves in DJ_0141 and the bottled-food shelf at the end of DJ_0080, a parked car at the
end of S2_C2201, a designer crossbody bag (DJ_0114) and a monogram-print bag (DJ_0115) carried
by guests, a camera-brand microphone (DJ_0201 after ~19 s), the AVIORA sign over the night store front S2_C2233, a monogram-print bag DJ_0087, a designer handbag DJ_0130), clips under a
second (DJ_0204, DJ_0205, DJ_0207), street shots full of other shops' signs (S2_C2203), an
overexposed logo wall (S2_C2214), the camera swinging off the wall in DJ_0150, passers-by blocking the lens, blurred camera moves.
A clip whose footage is not on disk is skipped by the planner (see available()).
"""
import os

EXT = [  # outside: the AIRA campaign standee, the soft-launch board, the store front at night
    ('DJ_0022', 0.5, {}), ('DJ_0022', 2.8, {}), ('DJ_0022', 11.0, {}),
    ('S2_C2200', 5.0, dict(pan=(0.6, 0.85))), ('S2_C2200', 9.8, dict(pan=(0.38, 0.72))),
    ('S2_C2201', 0.5, dict(pan=(0.6, 0.84))), ('S2_C2201', 4.0, dict(pan=(0.62, 0.86))),
]

HALL = [  # coming in: the welcome board, the flower-lined staircase, into the store
    ('DJ_0026', 0.3, {}), ('DJ_0026', 2.0, {}), ('DJ_0027', 0.5, {}),
    ('DJ_0027', 14.3, {}), ('DJ_0118', 1.0, {}), ('DJ_0118', 4.2, {}), ('DJ_0111', 0.5, {}),
    ('S2_C2218', 0.5, {}), ('S2_C2218', 3.5, {}),
    ('S2_C2204', 0.3, dict(cx=0.8)),
]

LOGO = [  # the AIRA name: the story wall, the logo above the door, the lit logo wall, the red sign
    # word positions measured on tick-marked frames (fractions of the frame width)
    ('DJ_0028', 0.3, dict(pan=(0.36, 0.66))), ('DJ_0029', 3.0, dict(cx=0.53)), ('DJ_0029', 6.5, dict(cx=0.5)),
    ('DJ_0030', 0.5, dict(cx=0.485, hold=1)), ('DJ_0030', 4.0, dict(cx=0.485, hold=1)),
    ('DJ_0040', 0.5, dict(cx=0.51, hold=1)), ('DJ_0040', 3.0, dict(cx=0.525, hold=1)),
    ('DJ_0041', 1.5, {}), ('S2_C2309', 18.0, dict(pan=(0.36, 0.76))),
]

SHOP = [  # the store: gold shelves, the rails, guests browsing
    ('DJ_0072', 1.0, {}), ('DJ_0072', 7.5, {}), ('DJ_0112', 0.5, {}), ('DJ_0112', 3.0, {}),
    ('S2_C2241', 1.5, {}), ('S2_C2241', 6.0, {}), ('S2_C2284', 0.5, {}), ('S2_C2284', 4.0, {}),
    ('S2_C2300', 1.0, {}),
]

END = [  # the lit AIRA wall, whole word inside the 9:16 frame for the whole shot (checked frame by frame)
    ('DJ_0165', 26.8, {}), ('DJ_0165', 27.4, {}), ('DJ_0165', 28.0, {}), ('DJ_0041', 1.9, {}),
]

PEOPLE = [  # guests and hosts in the store
    ('DJ_0074', 0.5, dict(look=1)), ('DJ_0074', 5.5, dict(look=1)), ('DJ_0074', 28.5, {}),
    ('DJ_0075', 0.5, dict(look=1)), ('DJ_0075', 19.0, dict(look=1)), ('DJ_0075', 114.0, dict(look=1)),
    ('DJ_0075', 95.0, {}),
    ('DJ_0123', 4.5, {}),
    ('DJ_0124', 0.3, dict(look=1)), ('DJ_0124', 7.0, dict(look=1)), ('DJ_0124', 13.0, {}),
    ('DJ_0132', 0.5, dict(look=1)), ('DJ_0132', 2.5, dict(look=1)), ('DJ_0132', 6.5, dict(look=1)),
    ('DJ_0139', 0.5, {}), ('DJ_0139', 1.8, {}),
    ('DJ_0145', 11.0, {}), ('DJ_0052', 15.4, dict(cx=0.6)),
    ('DJ_0154', 2.5, {}), ('DJ_0154', 17.9, {}),
    ('DJ_0169', 0.5, dict(look=1)), ('DJ_0169', 10.0, dict(look=1)), ('DJ_0169', 25.0, dict(look=1)),
    ('DJ_0194', 9.0, {}),
    ('DJ_0201', 0.3, dict(look=1)), ('DJ_0201', 6.0, dict(look=1)),
    ('S2_C2228', 0.5, {}), ('S2_C2280', 0.0, dict(look=1, sp=0.75)),
    ('S2_C2378', 2.5, dict(look=1)), ('S2_C2378', 6.0, {}),
]

PRODUCT = [  # garments on the rails: prints, embroidery, finishing details
    ('DJ_0043', 0.3, {}), ('DJ_0043', 2.5, {}), ('DJ_0079', 1.0, {}), ('DJ_0079', 8.5, {}),
    ('DJ_0080', 1.0, {}), ('DJ_0080', 4.5, {}), ('DJ_0081', 1.0, {}), ('DJ_0081', 5.5, {}),
    ('DJ_0081', 10.0, {}), ('DJ_0084', 0.5, {}), ('DJ_0084', 3.5, {}), ('DJ_0093', 1.0, {}),
    ('DJ_0093', 34.0, {}), ('DJ_0093', 41.0, {}), ('DJ_0094', 0.5, {}), ('DJ_0094', 4.0, {}),
    ('DJ_0096', 0.5, {}), ('DJ_0096', 6.0, {}), ('DJ_0096', 11.0, {}), ('DJ_0098', 1.5, {}),
    ('DJ_0098', 8.5, {}), ('DJ_0098', 12.5, {}), ('DJ_0139', 9.9, {}), ('DJ_0139', 14.8, {}),
    ('S2_C2228', 15.5, {}), ('S2_C2228', 20.0, {}),
]


def available(dirs):
    """Drop moments whose clip has no footage (original or proxy) in any of `dirs`."""
    def ok(clip):
        return any(os.path.exists(os.path.join(d, clip + ext)) for d in dirs for ext in ('.MP4', '.mp4'))
    g = globals()
    for name in ('EXT', 'HALL', 'LOGO', 'SHOP', 'END', 'PEOPLE', 'PRODUCT'):
        g[name] = [m for m in g[name] if ok(m[0])]
