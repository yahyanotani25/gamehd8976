"""What goes into each replacement slot.

Each slot maps to a list of segments that fill it back to back (with an
optional crossfade between them). Segment fields:
  src     path key: "px<id>" (Pexels stock, 1080p or larger) or "ai:<name>" (AI still)
  t       in-point in seconds (video)
  frac    share of the slot for multi-segment slots (default: all)
  kb      Ken Burns for stills: (zoom0, zoom1, cx0, cy0, cx1, cy1), centres as
          fractions of the image; zoom 1.0 = image width fills the frame
  push    gentle push-in for video: (zoom0, zoom1)
  hflip   mirror the shot (only where direction matters for continuity)
  crop    (zoom, cx, cy) reframe a video segment, e.g. to keep man-made objects out
  target  mean-luma target for the exposure grade (default 100)
  title   plate treatment for title cards: dim factor (0..1) and blur sigma
Which visual goes where follows the narration under each slot (kept out of this public repo).
"""

AI = {  # photographic stills (ICBINP XL / FLUX.1-schnell); the earlier Z-Image set had a mesh artifact
    "emerge_flux": "ai4/emerge_flux.webp",
    "emerge_icbinp": "ai4/emerge_icbinp.webp",
    "flyover_flux": "ai4/flyover_flux.webp",
    "flyover_icbinp": "ai4/flyover_icbinp.webp",
    "swoop_icbinp": "ai4/swoop_icbinp.webp",
    "recon_icbinp": "ai4/recon_icbinp.webp",
    "recon_flux": "ai4/recon_flux.webp",
    "swoop_flux": "ai4/swoop_flux.webp",
    "scaletrees_flux": "ai4/scaletrees_flux.webp",
    "fossil_flux": "ai4/fossil_flux.webp",
    "scaletrees_icbinp": "ai4/scaletrees_icbinp.webp",
    "fossil_icbinp": "ai4/fossil_icbinp.webp",
}

TITLE = dict(dim=0.55, blur=2.5)

PLAN = {
    # 0:00 opening (music)
    "S01": [dict(src="px2317719", t=12.0)],
    "S02": [dict(src="px7407334", t=3.0)],
    "S03": [dict(src="ai:emerge_flux", kb=(1.0, 1.08, .50, .48, .53, .45))],
    "S04": [dict(src="px6554123", t=3.0, title=TITLE)],
    "S05": [dict(src="px2894890", t=0.0)],
    "S06": [dict(src="px6528794_4k", t=10.0, crop=(1.25, .40, .40))],
    "S07": [dict(src="px5764717", t=1.0, crop=(1.18, .40, .56))],
    "S08": [dict(src="px1793014", t=3.0)],
    "S09": [dict(src="px5899473", t=0.3)],
    "S10": [dict(src="px5692323", t=8.0)],
    "S11": [dict(src="px5692316", t=2.0)],
    "S12": [dict(src="ai:scaletrees_flux", kb=(1.0, 1.08, .50, .50, .50, .46))],
    # 1:10
    "S13": [dict(src="px2599193", t=5.0)],
    "S14": [dict(src="px8394584", t=10.0)],
    "S15": [dict(src="px1727785", t=3.0)],
    "S16": [dict(src="px10789868", t=2.0, target=92)],
    # 2:11
    "S17": [dict(src="px7417468", t=3.0)],
    "S18": [dict(src="px8402915", t=5.0)],
    "S19": [dict(src="ai:flyover_flux", kb=(1.0, 1.10, .50, .50, .52, .44))],
    "S20": [dict(src="px4788058", t=3.0)],
    "S21": [dict(src="ai:fossil_flux", kb=(1.18, 1.30, .36, .50, .34, .52))],
    "S22": [dict(src="px2711112", t=5.0)],
    "S23": [dict(src="px11197125", t=3.0, title=TITLE)],
    "S24": [dict(src="px10623820", t=5.0)],
    "S25": [dict(src="px9010956_1440", t=2.0)],
    "S26": [dict(src="px8494160", t=4.0)],
    # 4:48
    "S28": [dict(src="px13831215", t=10.0)],
    "S29": [],
    "S30": [dict(src="px4825783", t=4.0, crop=(1.6, .33, .52))],
    "S31": [dict(src="px12903806", t=2.0)],
    "S32": [dict(src="px9055220", t=9.0)],
    # 6:08
    "S33": [dict(src="px2455151", t=3.0)],
    "S34": [dict(src="ai:recon_flux", kb=(1.0, 1.08, .50, .55, .50, .50))],
    "S35": [dict(src="px3295230", t=2.0)],
    "S36": [dict(src="px4334548", t=5.0)],
    # 9:18
    "S37": [dict(src="px855182", t=5.0)],
    "S38": [dict(src="px4788057", t=5.0)],
    "S39": [dict(src="px4709491", t=2.0)],
    "S40": [dict(src="px5738616", t=0.5, title=TITLE)],
    "S41": [dict(src="px6444542", t=2.0, target=105)],
    # 11:05
    "S42": [dict(src="ai:flyover_icbinp", kb=(1.0, 1.10, .50, .50, .48, .46))],
    "S43": [dict(src="ai:emerge_icbinp", kb=(1.0, 1.10, .50, .55, .50, .45))],
    "S44": [dict(src="px4788061_1440", t=4.0)],
    "S45": [dict(src="px855466", t=2.0, frac=0.48),
            dict(src="px14386849", t=0.0)],
    # 11:52
    "S46": [dict(src="px8397411_4k", t=1.0)],
    "S47": [dict(src="px2317719", t=24.0)],
    "S48": [dict(src="px2599193", t=25.0, title=TITLE)],
    # 12:38
    "S49": [dict(src="px4788054", t=3.0)],
    "S51": [dict(src="ai:swoop_flux", kb=(1.0, 1.12, .55, .45, .62, .42))],
    "S52": [dict(src="px3161307", t=2.0)],
    "S53": [dict(src="ai:recon_icbinp", kb=(1.0, 1.08, .50, .50, .47, .50))],
    # 13:13
    "S54": [dict(src="px4500637", t=5.0)],
    "S55": [dict(src="px5692314", t=3.0)],
    "S56": [dict(src="px4259460", t=3.0, title=TITLE)],
    "S57": [dict(src="px2736469", t=5.0)],
    "S58": [dict(src="px6446215", t=2.0)],
    "S59": [dict(src="px5646804", t=5.0)],
    "S60": [dict(src="px3239812", t=5.0)],
    "S61": [dict(src="px5135829", t=2.0)],
    # 14:23
    "S62": [dict(src="px6444538", t=3.0, target=100)],
    # 14:43
    "S63": [dict(src="px4457808", t=2.0)],
    "S64": [dict(src="px13796793", t=3.0)],
    "S66": [dict(src="ai:fossil_icbinp", kb=(1.0, 1.10, .50, .50, .50, .50))],
}
