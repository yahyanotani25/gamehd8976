"""Alignment check previews: imagery multiplied by the DEM hillshade, plus a
checkerboard (imagery / hillshade) crop at full imagery resolution, with
reference points plotted from lat/lon via the bounds.json formulas.

  python3 -I tools/map_preview.py            -> assets/map/previews/*.jpg
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from map_common import OUT, hillshade, lonlat_to_merc  # noqa: E402

Image.MAX_IMAGE_PIXELS = None


def load_points():
    p = os.path.join(OUT, "vector", "points.json")
    if not os.path.exists(p):
        return []
    return [(f["properties"]["name"], *f["geometry"]["coordinates"])
            for f in json.load(open(p))["features"]]


def to_px(meta, lon, lat, w, h):
    b = meta["bounds_mercator_m"]
    x, y = lonlat_to_merc(lon, lat)
    return ((x - b["west"]) / (b["east"] - b["west"]) * w,
            (b["north"] - y) / (b["north"] - b["south"]) * h)


def dem(d, meta):
    hm = meta["layers"]["heightmap"]
    a = np.fromfile(os.path.join(d, "heightmap_u16le.bin"), "<u2").reshape(hm["height"], hm["width"])
    return hm["min_m"] + a.astype(np.float64) / 65535.0 * (hm["max_m"] - hm["min_m"])


def main():
    pv = os.path.join(OUT, "previews")
    os.makedirs(pv, exist_ok=True)
    pts = load_points()
    for box in ("wide", "regional", "closeup"):
        d = os.path.join(OUT, box)
        meta = json.load(open(os.path.join(d, "bounds.json")))
        e = dem(d, meta)
        img = Image.open(os.path.join(d, "imagery.jpg")).convert("RGB")
        W, H = img.size
        # 1) whole box, imagery x hillshade (hillshade upsampled from the DEM)
        tw = 1600
        th = round(H * tw / W)
        small = np.asarray(img.resize((tw, th), Image.LANCZOS)).astype(np.float32) / 255
        hs = Image.fromarray((hillshade(e, meta["layers"]["heightmap"]["pixel_size_ground_m_at_center"],
                                        azimuth=315, altitude=35, z_factor=1.5) * 255).astype(np.uint8))
        hs_s = np.asarray(hs.resize((tw, th), Image.BICUBIC)).astype(np.float32)[..., None] / 255
        out = np.clip(small * (0.25 + 1.1 * hs_s), 0, 1)
        im = Image.fromarray((out * 255).astype(np.uint8))
        dr = ImageDraw.Draw(im)
        mtp = os.path.join(OUT, "vector", "montana.geojson")
        if os.path.exists(mtp):  # Montana border from the vector data, projected with the same formula
            for poly in json.load(open(mtp))["features"][0]["geometry"]["coordinates"]:
                ring = [to_px(meta, lon, lat, tw, th) for lon, lat in poly[0]]
                dr.line(ring, fill=(255, 210, 0), width=2)
        for name, lon, lat in pts:
            x, y = to_px(meta, lon, lat, tw, th)
            if 0 <= x < tw and 0 <= y < th:
                dr.ellipse((x - 5, y - 5, x + 5, y + 5), outline=(255, 40, 40), width=2)
                dr.text((x + 8, y - 6), name, fill=(255, 255, 255))
        im.save(os.path.join(pv, f"{box}_imagery_x_hillshade.jpg"), quality=88)
        # 2) checkerboard crop at full imagery res around the box centre-ish
        cw = ch = 1400
        cx0, cy0 = W // 2 - cw // 2 + W // 8, H // 2 - ch // 2 - H // 10
        crop = np.asarray(img.crop((cx0, cy0, cx0 + cw, cy0 + ch))).astype(np.float32) / 255
        hw, hh = e.shape[1], e.shape[0]
        sx, sy = hw / W, hh / H
        hs_full = hs.transform((cw, ch), Image.EXTENT,
                               (cx0 * sx, cy0 * sy, (cx0 + cw) * sx, (cy0 + ch) * sy), Image.BICUBIC)
        hsa = np.asarray(hs_full).astype(np.float32)[..., None] / 255
        yy, xx = np.mgrid[0:ch, 0:cw]
        cell = 175
        chk = (((yy // cell) + (xx // cell)) % 2 == 0)[..., None]
        mix = np.where(chk, crop, np.repeat(hsa, 3, axis=2) * np.array([0.85, 0.9, 1.0]))
        Image.fromarray((np.clip(mix, 0, 1) * 255).astype(np.uint8)).save(
            os.path.join(pv, f"{box}_checker_fullres.jpg"), quality=88)
        print(box, "ok", (W, H), e.shape)


if __name__ == "__main__":
    main()
