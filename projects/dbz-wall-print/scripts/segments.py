"""Where the mural sits on the wall, and the shots of the edit.

The edit follows reference 2 shot for shot (same cut points, 30 fps):

  #  ref2 time      ref2 shot                          from reference 1
  1  0.00-2.23  wide, left part printed, printer mid   B 34-100  (time-lapse wide)
  2  2.23-4.00  close-up, head printing Goku's face    D 335-387 (head moving down)
  3  4.00-5.97  wide, printing continues               E 470-528 (far wide)
  4  5.97-8.03  close-up, head printing next figure    D 180-241 (head moving up)
  5  8.03-9.90  close-up, head printing                D 388-443 (head moving down)
  6  9.90-11.13 detail of the finished print           F 830-866 (moving camera)
  7 11.13-12.75 wide reveal of the finished wall       E 540-588

The mural covers the wall from just under the cornice to just above the
floor (canvas v = ART_V0 .. ART_V1).  Its horizontal position is chosen per
shot so the figure being printed is under the print head (a real print of a
wall this long takes hours and the printer moves along its rail).
"""
import numpy as np
from common import *

ART_W, ART_H = 3565, 1652
ART_V0, ART_V1 = 60.0, 1880.0          # canvas v of the mural's top / bottom
K = (ART_V1 - ART_V0) / ART_H           # canvas px per art px (vertical)
S_CORR = 1.072                          # canvas u is 7.2% compressed (measured)
KU = K / S_CORR                         # canvas px per art px (horizontal)

# landmarks in art px (x, y) -- figures' faces and edges
ART = {
    "piccolo_goku": 1248, "goku_face": (1464, 764), "goku_vegeta": 1935,
    "vegeta_face": (2215, 840), "buu_face": (2750, 738), "black_face": (3220, 687),
}


def art_to_canvas(u_off):
    return np.array([[KU, 0, u_off + CU], [0, K, ART_V0 + CV], [0, 0, 1.0]])


def u_off_for(art_x, u):
    """Mural offset that puts art column art_x at wall position u."""
    return u - art_x * KU


def _heads():
    try:
        h = load_json("heads.json")
    except FileNotFoundError:
        return {}
    return {int(k): v for k, v in h.items()}


def head_series(a, b, smooth=5):
    """Interpolated, smoothed head (u, v) for frames a..b."""
    h = _heads()
    fr = np.arange(a, b + 1)
    ks = [k for k in sorted(h) if a - 10 <= k <= b + 10]
    if not ks:
        return fr, np.zeros(len(fr)), np.zeros(len(fr))
    uu = np.interp(fr, ks, [h[k][0] for k in ks])
    vv = np.interp(fr, ks, [h[k][1] for k in ks])
    if smooth > 1:
        ker = np.ones(smooth) / smooth
        pad = smooth // 2
        uu = np.convolve(np.pad(uu, pad, mode="edge"), ker, "valid")
        vv = np.convolve(np.pad(vv, pad, mode="edge"), ker, "valid")
    return fr, uu, vv


def pass_state(a, b, frontier, strip_w, direction, lead=25.0):
    """Close-up on the head during one vertical pass.

    Everything left of `frontier` is printed; inside the strip the rows the
    head has already passed are printed (above it going down, below it going
    up).  `lead` puts the printed edge just under the head's light.
    """
    fr, uu, vv = head_series(a, b, smooth=5)

    def st(i):
        j = int(np.clip(i - a, 0, len(fr) - 1))
        return {"frontier": frontier, "strip_w": strip_w, "dir": direction,
                "head_v": vv[j] + direction * lead}
    return st


def timelapse_state(a, b, back=60.0, win=15):
    """Wide time-lapse: the printed edge follows the tower along the rail."""
    fr, uu, vv = head_series(a, b, smooth=1)
    # robust running position of the head column, never moving backwards
    half = win // 2
    med = np.array([np.median(uu[max(0, k - half):k + half + 1]) for k in range(len(uu))])
    front = np.maximum.accumulate(med) - back

    def st(i):
        j = int(np.clip(i - a, 0, len(fr) - 1))
        return {"frontier": float(front[j]), "strip_w": 0, "dir": 1, "head_v": 0}
    return st, front


def done_state():
    def st(i):
        return {"frontier": 1e6, "strip_w": 0, "dir": 1, "head_v": 0}
    return st


def _build():
    segs = {}
    # D close-up: the head's light runs up/down the column u ~ 590
    D_COL = 590.0
    FRONT, STRIP = D_COL - 30, 200.0
    strip_mid = FRONT + 45

    # 1: wide time-lapse, printer finishing Piccolo and starting on Goku
    st1, front1 = timelapse_state(34, 100)
    segs["s1_wide"] = dict(frames=(34, 100), tracks="tracks_B_master0.json", state=st1,
                           u_off=u_off_for(ART["piccolo_goku"] + 40, float(front1[-1])))
    # 2: close-up, head going down across Goku's face
    segs["s2_goku"] = dict(frames=(335, 387), tracks="tracks_D.json",
                           state=pass_state(335, 387, FRONT, STRIP, +1),
                           u_off=u_off_for(ART["goku_face"][0], strip_mid))
    # 3: far wide, printing Vegeta
    st3, front3 = timelapse_state(470, 528)
    segs["s3_wide"] = dict(frames=(470, 528), tracks="tracks_E0.json", state=st3,
                           u_off=u_off_for(ART["vegeta_face"][0] - 60, float(front3[-1])))
    # 4: close-up, head going up across Vegeta's face
    segs["s4_vegeta"] = dict(frames=(180, 241), tracks="tracks_D.json",
                             state=pass_state(180, 241, FRONT, STRIP, -1),
                             u_off=u_off_for(ART["vegeta_face"][0], strip_mid))
    # 5: close-up, head going down Buu's body (face already printed above)
    segs["s5_buu"] = dict(frames=(388, 443), tracks="tracks_D.json",
                          state=pass_state(388, 443, FRONT, STRIP, +1),
                          u_off=u_off_for(ART["buu_face"][0], strip_mid))
    # 6: detail of the finished print, Goku and Vegeta
    segs["s6_detail"] = dict(frames=(830, 866), tracks="tracks_F_master0.json", state=done_state(),
                             u_off=None, center_art_x=1700)
    # 7: far wide, finished wall; the mural ends at the parked printer
    segs["s7_final"] = dict(frames=(540, 588), tracks="tracks_E0.json", state=done_state(),
                            u_off=u_off_for(ART_W, 1470.0))
    return segs


SEGMENTS = _build()


def resolve_center_offsets():
    """Segments placed by 'what is in the middle of the frame'."""
    from track import load_tr
    for s in SEGMENTS.values():
        if s.get("u_off") is None:
            tr = load_tr(s["tracks"])
            mid = (s["frames"][0] + s["frames"][1]) // 2
            u, v = warp_pts(np.linalg.inv(tr[mid]), [[FW / 2, FH / 2]])[0]
            s["u_off"] = u_off_for(s["center_art_x"], u - CU)


resolve_center_offsets()
