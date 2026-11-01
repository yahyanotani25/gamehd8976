"""Precompute masks + stroke-colour maps for every overlay that must survive.

For each overlay: read its frames from the original, compute the white top-hat
(frame minus a morphological opening that erases thin bright strokes), and keep
pixels that are persistently lifted (median over the plateau for overlays on
moving footage; max over the whole span for title cards on near-black).
Stroke colour = median colour of the strongest stroke pixels, spread to the
whole mask by nearest-core lookup.
usage: overlay_masks.py W   -> W/work/ovl/<id>.npz + preview sheet
"""
import sys, json, subprocess
import numpy as np, cv2

W = sys.argv[1]
SRC = W + "/dl/original/original.mp4"

# id, slot, bbox (x0,y0,x1,y1), frames [a,b] where it can appear, plateau [p0,p1], mode, kernel, thr
OVERLAYS = [
    dict(id="O1_not_modern",   slot="S12", box=(70, 905, 475, 1000),  span=(1140, 1211), plat=(1160, 1190), mode="median", k=21, thr=18),
    dict(id="O2_how_could",    slot="S39", box=(170, 830, 1750, 930), span=(14598, 14690), plat=(14600, 14640), mode="median", k=31, thr=45),
    dict(id="O3_hud",          slot="S42", box=(590, 265, 1535, 735), span=(16645, 16757), plat=(16650, 16740), mode="median", k=21, thr=20),
    dict(id="O4_uncertain",    slot="S49", box=(80, 740, 430, 865),   span=(18958, 19119), plat=(19000, 19100), mode="median", k=31, thr=20),
    dict(id="O6_plausible",    slot="S53", box=(395, 904, 1530, 974), span=(19475, 19606), plat=(19510, 19580), mode="median", k=21, thr=55),
    dict(id="O7_nosingle",     slot="S62", box=(585, 778, 1315, 872), span=(21573, 21731), plat=(21680, 21714), mode="median", k=41, thr=70),
    dict(id="T1_ch1",          slot="S04", box=(240, 300, 1680, 780), span=(269, 460),     plat=(320, 425),     mode="median", k=31, thr=14),
    dict(id="T2_ch2",          slot="S23", box=(240, 300, 1680, 780), span=(3774, 3922),   plat=(3828, 3905),   mode="median", k=31, thr=14),
    dict(id="T3_ch3",          slot="S29", box=(240, 300, 1680, 780), span=(7435, 7572),   plat=(7480, 7545),   mode="median", k=31, thr=14),
    dict(id="T5_ch5",          slot="S40", box=(240, 300, 1680, 780), span=(14660, 14802), plat=(14712, 14770), mode="median", k=31, thr=14),
    dict(id="T6_ch6",          slot="S48", box=(240, 300, 1680, 780), span=(18056, 18217), plat=(18100, 18200), mode="median", k=31, thr=14),
    dict(id="T7_ch7",          slot="S56", box=(240, 300, 1680, 780), span=(20176, 20324), plat=(20214, 20280), mode="median", k=31, thr=14),
]


def read(f0, n):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{f0 / 25:.4f}", "-i", SRC, "-frames:v", str(n),
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 1080, 1920, 3)


def lum(a):
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


if __name__ == "__main__":
    import os
    os.makedirs(W + "/work/ovl", exist_ok=True)
    meta = {}
    sheets = []
    for o in OVERLAYS:
        x0, y0, x1, y1 = o["box"]
        a, b = o["span"]
        F = read(a, b - a + 1)[:, y0:y1, x0:x1].astype(np.float32)
        ker = cv2.getStructuringElement(cv2.MORPH_RECT, (o["k"], o["k"]))
        lifts = []
        for fr in F:
            Y = lum(fr)
            op = cv2.morphologyEx(Y, cv2.MORPH_OPEN, ker)
            lifts.append(np.clip(Y - cv2.blur(op, (5, 5)), 0, 255))
        L = np.stack(lifts)
        p0, p1 = o["plat"][0] - a, o["plat"][1] - a
        persist = np.median(L[p0:p1 + 1], 0) if o["mode"] == "median" else L[p0:p1 + 1].max(0)
        sd = L[p0:p1 + 1].std(0)
        core = (persist > o["thr"]) & (sd < 0.35 * persist + 6)
        # drop isolated specks (noise / background detail)
        n, lab, st, _ = cv2.connectedComponentsWithStats(core.astype(np.uint8), 8)
        keep = np.zeros_like(core)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] >= 3:
                keep |= lab == i
        core = keep
        # keep only stroke clusters: drop small specks far from the main text
        # (title cards skip this: their small letters sit far from the big digits;
        #  the centring filter below cleans them instead)
        n, lab, st, cen = cv2.connectedComponentsWithStats(core.astype(np.uint8), 8) if not o["id"].startswith("T") else (1, None, None, None)
        tot = core.sum() + 1
        big = np.zeros_like(core)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] >= max(25, 0.004 * tot):
                big |= lab == i
        rad = 91 if o["id"].startswith("T") else 31
        near = cv2.dilate(big.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (rad, rad))) > 0
        keep = np.zeros_like(core)
        for i in range(1, n):
            comp = lab == i
            if st[i, cv2.CC_STAT_AREA] >= (3 if o["id"].startswith("T") else 6) and (comp & near).sum() == comp.sum():
                keep |= comp
        if not o["id"].startswith("T"):
            core = keep
        if o["id"].startswith("T"):
            # title template is centred on x=960: keep only centred text lines
            line = cv2.dilate(core.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_RECT, (61, 5)))
            n2, lab2, st2, _ = cv2.connectedComponentsWithStats(line, 8)
            keep = np.zeros_like(core)
            for i in range(1, n2):
                cx = x0 + st2[i, cv2.CC_STAT_LEFT] + st2[i, cv2.CC_STAT_WIDTH] / 2
                if abs(cx - 960) < 45:
                    keep |= (lab2 == i) & core
            core = keep
        soft = cv2.dilate(core.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        soft = cv2.GaussianBlur(soft.astype(np.float32), (0, 0), 1.0)
        soft = np.clip(soft * 1.5, 0, 1)
        # stroke colour per glyph: each connected stroke component takes the median
        # colour of its own strongest pixels (gold letters stay gold, white stays white);
        # every other mask pixel takes the colour of the nearest stroke pixel
        med = np.median(F[p0:p1 + 1], 0)
        colr = np.full(core.shape + (3,), 230, np.float32)
        if core.any():
            ncc, lcc = cv2.connectedComponents(core.astype(np.uint8), connectivity=8)
            fill = np.zeros(core.shape + (3,), np.float32)
            for i in range(1, ncc):
                comp = lcc == i
                pv = persist[comp]
                top = comp & (persist >= np.percentile(pv, 70))
                fill[comp] = np.median(med[top], 0)
            # text is never dark: glyph pieces whose colour came out dark (stroke over a
            # dark patch of the plate) borrow the colour of the nearest bright glyph
            fl = lum(fill)
            bright = core & (fl >= 120)
            if bright.any() and (core & (fl < 120)).any():
                idx = np.zeros(core.shape, np.uint8); idx[~bright] = 255
                _, lb = cv2.distanceTransformWithLabels(idx, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
                by, bx = np.nonzero(bright)
                od = np.zeros(lb.max() + 1, np.int64); od[lb[by, bx]] = np.arange(len(by))
                nb = od[lb]
                dark = core & (fl < 120)
                fill[dark] = fill[by[nb[dark]], bx[nb[dark]]]
            idx = np.zeros(core.shape, np.uint8); idx[~core] = 255
            dist, labels = cv2.distanceTransformWithLabels(idx, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
            ys, xs = np.nonzero(core)
            order = np.zeros(labels.max() + 1, np.int64)
            order[labels[ys, xs]] = np.arange(len(ys))
            nearest = order[labels]
            colr = fill[ys[nearest], xs[nearest]]
        np.savez_compressed(W + f"/work/ovl/{o['id']}.npz", soft=soft.astype(np.float16), color=colr.astype(np.uint8),
                            box=np.array(o["box"]), k=o["k"])
        meta[o["id"]] = dict(o, pixels=int(core.sum()), color_med=[float(c) for c in np.median(colr[core], 0)] if core.any() else None)
        print(o["id"], "core px", int(core.sum()), "median stroke colour", meta[o["id"]]["color_med"])
        vis = np.zeros((y1 - y0, (x1 - x0) * 2 + 10, 3), np.uint8)
        vis[:, :x1 - x0] = np.clip(med * 1.0, 0, 255).astype(np.uint8)
        vis[:, x1 - x0 + 10:] = (soft[..., None] * colr).astype(np.uint8)
        sheets.append((o["id"], vis))
    json.dump(meta, open(W + "/work/ovl/meta.json", "w"), indent=1)
    # preview sheet (scaled to 1400 wide)
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    rows = []
    for name, v in sheets:
        im = Image.fromarray(v)
        s = min(1.0, 1400 / im.width)
        im = im.resize((int(im.width * s), int(im.height * s)))
        r = Image.new("RGB", (1400, im.height + 22), "white"); r.paste(im, (0, 22))
        ImageDraw.Draw(r).text((4, 2), name, fill="black", font=font)
        rows.append(r)
    out = Image.new("RGB", (1400, sum(r.height for r in rows)), "white")
    y = 0
    for r in rows:
        out.paste(r, (0, y)); y += r.height
    out.save(W + "/work/ovl/masks.jpg", quality=85)
    print(out.size)
