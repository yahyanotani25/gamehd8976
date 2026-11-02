"""Shared paths, shot list and geometry for the Dragon Ball wall-print edit.

Coordinates
-----------
* frame px   : a 720x1280 frame of reference 1 (the client's printer video).
* canvas px  : the "canonical wall" image.  The wall of reference 1 is
               flattened so that the wall top (under the cornice) is v=0
               and the wall/floor line is v=WALL_H.  canvas = (u+CU, v+CV).
* art px     : the flattened Dragon Ball mural (art.png).

A homography H "canvas->frame" maps canvas px to frame px.
"""
import os
import json
import numpy as np
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get(
    "DBZ_WORK",
    "/tmp/claude-0/-home-user/e114e975-b291-553b-a442-daaf5e95046f/scratchpad/work")
REF1 = os.environ.get(
    "DBZ_REF1",
    "/root/.claude/uploads/e114e975-b291-553b-a442-daaf5e95046f/c18ce4b8-refrence_1.mp4")
REF2 = os.environ.get(
    "DBZ_REF2",
    "/root/.claude/uploads/e114e975-b291-553b-a442-daaf5e95046f/6c04a146-Refrence_2_.mp4")
CLIENT_IMG = os.environ.get(
    "DBZ_IMG",
    "/tmp/claude-0/-home-user/e114e975-b291-553b-a442-daaf5e95046f/images/1.jpg")
FRAMES = os.path.join(WORK, "frames1")      # ref1 frames, 0001.jpg ...
os.makedirs(WORK, exist_ok=True)

FW, FH = 720, 1280

# canonical wall canvas
WALL_H = 2000.0
CU, CV = 800, 200                # canvas offset of (u=0, v=0)
CANVAS_W, CANVAS_H = 3400, 2400

# Shots of reference 1 (1-based frame numbers, inclusive).  Frames with
# people walking past (23-24, 32-33) are left out of B.
SHOTS = {
    "A": (1, 17),      # early progress, printer mid-wall
    "B": (34, 124),    # wide, printer on the right
    "D": (133, 444),   # low-angle close-up of the print head
    "E": (454, 632),   # far wide shot, ceiling visible
    "F": (678, 897),   # finished-art reveal, moving camera
}

# Frame 560 (shot E) defines the canvas: wall top (under the cornice) and the
# wall/floor line, read off that frame by hand.
REF_FRAME = 560
REF_QUAD_IMG = np.float32([[0, 177], [600, 268.2], [600, 944.8], [0, 1027]])
REF_QUAD_W = 1573.0              # canvas width of that quad (aspect fixed later)


def ref_quad_canvas():
    return np.float32([[CU, CV], [CU + REF_QUAD_W, CV],
                       [CU + REF_QUAD_W, CV + WALL_H], [CU, CV + WALL_H]])


def frame_path(i):
    return os.path.join(FRAMES, f"{i:04d}.jpg")


def read_frame(i):
    return cv2.imread(frame_path(i), cv2.IMREAD_COLOR)


def save_json(obj, name):
    with open(os.path.join(WORK, name), "w") as f:
        json.dump(obj, f)


def load_json(name):
    with open(os.path.join(WORK, name)) as f:
        return json.load(f)


def load_tracks():
    """dict frame -> 3x3 canvas->frame homography (smoothed if available)."""
    for name in ("tracks_smooth.json", "tracks.json"):
        p = os.path.join(WORK, name)
        if os.path.exists(p):
            d = load_json(name)
            return {int(k): np.array(v, dtype=np.float64) for k, v in d.items()}
    return {}


def wall_poly_canvas(u0=-CU, u1=CANVAS_W - CU):
    return np.float32([[CU + u0, CV], [CU + u1, CV],
                       [CU + u1, CV + WALL_H], [CU + u0, CV + WALL_H]])


def warp_pts(H, pts):
    pts = np.asarray(pts, np.float64).reshape(-1, 1, 2)
    return cv2.perspectiveTransform(pts, H).reshape(-1, 2)


def dark_mask(bgr, thr=55, min_area=3000, grow=9):
    """Printer / rail / cables: large connected regions of very dark pixels.

    Small dark bits of artwork (balloon baskets, stripes) are left out by the
    area test; the result is grown a little to cover the printer's edges.
    """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    m = (hsv[..., 2] < thr).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    keep = np.zeros(n, np.uint8)
    keep[1:] = st[1:, cv2.CC_STAT_AREA] >= min_area
    m = keep[lab]
    if grow:
        m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (grow, grow)))
    return m
