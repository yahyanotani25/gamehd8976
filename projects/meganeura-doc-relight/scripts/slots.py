"""Replacement slots in the original (25 fps frame indices, inclusive ranges).

Each slot: id, client clip, first/last frame of the replaced layer (including any
dissolve frames where it is partly visible), kind, and how each end joins its
neighbour:
  ("cut",)                      hard cut
  ("fadeblack", a, b)           fades up from black over frames a..b (in only)
  ("kept", a, b)                dissolve with a KEPT original shot over frames a..b
  ("new", a, b)                 dissolve with the neighbouring NEW slot over a..b
kind: footage | title (new plate + original title text) | regrade (original
footage brightened, original title text re-applied on top)

Shots inside the client's ranges that were already bright and clean are kept:
2:58.4-3:00.4 (hand on shale), 12:44.8-12:49.2 (griffinfly over water, top
view) and 14:49.4-14:52.3 (red earth bank and pines).
"""

SLOTS = [
    # ---- 0:00-0:48  (clip_23, clip_22, clip_21) -----------------------------------
    dict(id="S01", clip="clip_23", f0=0,     f1=84,    kind="footage", inn=("fadeblack", 0, 34), out=("cut",)),
    dict(id="S02", clip="clip_23", f0=85,    f1=154,   kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S03", clip="clip_23", f0=155,   f1=283,   kind="footage", inn=("cut",), out=("new", 269, 283)),
    dict(id="S04", clip="clip_23", f0=269,   f1=460,   kind="title",   inn=("new", 269, 283), out=("kept", 431, 460), ovl="T1_ch1"),
    dict(id="S05", clip="clip_22", f0=580,   f1=654,   kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S06", clip="clip_22", f0=655,   f1=732,   kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S07", clip="clip_22", f0=733,   f1=832,   kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S08", clip="clip_22", f0=833,   f1=924,   kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S09", clip="clip_21", f0=925,   f1=974,   kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S10", clip="clip_21", f0=975,   f1=1047,  kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S11", clip="clip_21", f0=1048,  f1=1129,  kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S12", clip="clip_21", f0=1130,  f1=1211,  kind="footage", inn=("cut",), out=("kept", 1203, 1211), ovl="O1_not_modern"),
    # ---- 1:10-1:33  (clip_04, clip_20) --------------------------------------------
    dict(id="S13", clip="clip_04", f0=1760,  f1=1885,  kind="footage", inn=("kept", 1760, 1770), out=("kept", 1859, 1885)),
    dict(id="S14", clip="clip_20", f0=2016,  f1=2184,  kind="footage", inn=("kept", 2016, 2025), out=("cut",)),
    dict(id="S15", clip="clip_20", f0=2185,  f1=2232,  kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S16", clip="clip_20", f0=2233,  f1=2330,  kind="footage", inn=("cut",), out=("kept", 2323, 2330)),
    # ---- 2:11-2:44  (clip_19, photo clip_18, clip_17) -----------------------------
    dict(id="S17", clip="clip_19", f0=3283,  f1=3414,  kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S18", clip="clip_19", f0=3415,  f1=3474,  kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S19", clip="clip_19", f0=3475,  f1=3545,  kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S20", clip="clip_19", f0=3546,  f1=3622,  kind="footage", inn=("cut",), out=("new", 3609, 3622)),
    dict(id="S21", clip="clip_18", f0=3609,  f1=3701,  kind="footage", inn=("new", 3609, 3622), out=("new", 3686, 3701)),
    dict(id="S22", clip="clip_18", f0=3686,  f1=3787,  kind="footage", inn=("new", 3686, 3701), out=("new", 3774, 3787)),
    dict(id="S23", clip="clip_18", f0=3774,  f1=3922,  kind="title",   inn=("new", 3774, 3787), out=("cut",), ovl="T2_ch2"),
    dict(id="S24", clip="clip_17", f0=3923,  f1=3994,  kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S25", clip="clip_17", f0=3995,  f1=4107,  kind="footage", inn=("cut",), out=("kept", 4098, 4107)),
    # ---- 2:54-2:58  (clip_16) -------------------------------------------------------
    dict(id="S26", clip="clip_16", f0=4360,  f1=4459,  kind="footage", inn=("cut",), out=("cut",)),
    # ---- 4:48-5:11  (clip_15, clip_14) ----------------------------------------------
    dict(id="S28", clip="clip_15", f0=7198,  f1=7380,  kind="footage", inn=("cut",), out=("kept", 7348, 7380)),
    dict(id="S29", clip="clip_14", f0=7435,  f1=7572,  kind="regrade", inn=("cut",), out=("cut",), ovl="T3_ch3"),
    dict(id="S30", clip="clip_14", f0=7573,  f1=7639,  kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S31", clip="clip_14", f0=7640,  f1=7687,  kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S32", clip="clip_14", f0=7688,  f1=7783,  kind="footage", inn=("cut",), out=("kept", 7775, 7783)),
    # ---- 6:08-6:23  (clip_13) -------------------------------------------------------
    dict(id="S33", clip="clip_13", f0=9195,  f1=9294,  kind="footage", inn=("kept", 9195, 9206), out=("cut",)),
    dict(id="S34", clip="clip_13", f0=9295,  f1=9367,  kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S35", clip="clip_13", f0=9368,  f1=9459,  kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S36", clip="clip_13", f0=9460,  f1=9579,  kind="footage", inn=("cut",), out=("cut",)),
    # ---- 9:18-9:56  (clip_12, clip_11, clip_10) -------------------------------------
    dict(id="S37", clip="clip_12", f0=13948, f1=14057, kind="footage", inn=("kept", 13948, 13958), out=("cut",)),
    dict(id="S38", clip="clip_11", f0=14235, f1=14347, kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S39", clip="clip_10", f0=14598, f1=14690, kind="footage", inn=("kept", 14598, 14601), out=("new", 14660, 14690), ovl="O2_how_could"),
    dict(id="S40", clip="clip_10", f0=14660, f1=14802, kind="title",   inn=("new", 14660, 14690), out=("new", 14786, 14802), ovl="T5_ch5"),
    dict(id="S41", clip="clip_10", f0=14786, f1=14914, kind="footage", inn=("new", 14786, 14802), out=("cut",)),
    # ---- 11:05-11:24 (clip_09) --------------------------------------------------------
    dict(id="S42", clip="clip_09", f0=16645, f1=16757, kind="footage", inn=("cut",), out=("cut",), ovl="O3_hud"),
    dict(id="S43", clip="clip_09", f0=16758, f1=16849, kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S44", clip="clip_09", f0=16850, f1=16919, kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S45", clip="clip_09", f0=16920, f1=17107, kind="footage", inn=("cut",), out=("cut",)),
    # ---- 11:52-12:08 (clip_08) --------------------------------------------------------
    dict(id="S46", clip="clip_08", f0=17818, f1=17927, kind="footage", inn=("kept", 17818, 17828), out=("cut",)),
    dict(id="S47", clip="clip_08", f0=17928, f1=18088, kind="footage", inn=("cut",), out=("new", 18056, 18088)),
    dict(id="S48", clip="clip_08", f0=18056, f1=18217, kind="title",   inn=("new", 18056, 18088), out=("cut",), ovl="T6_ch6"),
    # ---- 12:38-13:04 (clip_07, clip_06) -----------------------------------------------
    dict(id="S49", clip="clip_07", f0=18958, f1=19119, kind="footage", inn=("cut",), out=("cut",), ovl="O4_uncertain"),
    dict(id="S51", clip="clip_07", f0=19230, f1=19382, kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S52", clip="clip_06", f0=19383, f1=19474, kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S53", clip="clip_06", f0=19475, f1=19606, kind="footage", inn=("cut",), out=("kept", 19595, 19606), ovl="O6_plausible"),
    # ---- 13:13-13:55 (clip_05, clip_03) -----------------------------------------------
    dict(id="S54", clip="clip_05", f0=19830, f1=19965, kind="footage", inn=("kept", 19830, 19841), out=("cut",)),
    dict(id="S55", clip="clip_05", f0=19966, f1=20208, kind="footage", inn=("cut",), out=("new", 20176, 20208)),
    dict(id="S56", clip="clip_05", f0=20176, f1=20324, kind="title",   inn=("new", 20176, 20208), out=("new", 20290, 20324), ovl="T7_ch7"),
    dict(id="S57", clip="clip_03", f0=20290, f1=20429, kind="footage", inn=("new", 20290, 20324), out=("cut",)),
    dict(id="S58", clip="clip_03", f0=20430, f1=20497, kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S59", clip="clip_03", f0=20498, f1=20587, kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S60", clip="clip_03", f0=20588, f1=20737, kind="footage", inn=("cut",), out=("cut",)),
    dict(id="S61", clip="clip_03", f0=20738, f1=20900, kind="footage", inn=("cut",), out=("kept", 20881, 20900)),
    # ---- 14:23-14:29 (clip_02) --------------------------------------------------------
    dict(id="S62", clip="clip_02", f0=21573, f1=21731, kind="footage", inn=("kept", 21573, 21583), out=("kept", 21721, 21731), ovl="O7_nosingle"),
    # ---- 14:43-14:57 (clip_01) --------------------------------------------------------
    dict(id="S63", clip="clip_01", f0=22068, f1=22157, kind="footage", inn=("kept", 22068, 22078), out=("cut",)),
    dict(id="S64", clip="clip_01", f0=22158, f1=22266, kind="footage", inn=("cut",), out=("kept", 22234, 22266)),
    dict(id="S66", clip="clip_01", f0=22308, f1=22443, kind="footage", inn=("kept", 22308, 22318), out=("kept", 22416, 22443)),
]

FPS = 25


def by_id():
    return {s["id"]: s for s in SLOTS}
