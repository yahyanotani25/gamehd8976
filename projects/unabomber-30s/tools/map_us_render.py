"""Stylised dark map of the contiguous US (Web Mercator, 4096 x 2304, 16:9)
with subtle terrain relief, plus a Montana-highlight version and a Montana
alpha mask, all pixel-aligned. Also writes the matching US heightmap.

  python3 -I tools/map_us_render.py        -> assets/map/us/
Needs tools/map_vector.py to have run (vector sources in the scratch dir).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

from map_common import (OUT, despike, encode_height, gpx_to_merc, hillshade, lonlat_to_merc,  # noqa: E402
                        merc_to_gpx, merc_to_lonlat, mosaic, res_at, save_png16,
                        terrarium_decode, write_json)
from map_vector import fetch, read_dbf, read_shp  # noqa: E402

Image.MAX_IMAGE_PIXELS = None

Z = 7                      # tile-pixel grid the US box snaps to
BOX_W, BOX_H = 5824, 3276  # z7 pixels, exactly 16:9 (364 * 16 x 364 * 9)
OUT_W, OUT_H = 4096, 2304
SS = 3                     # supersampling for vector rasterisation

COL = dict(
    ocean=(9, 12, 17), land_ctx=(19, 23, 29), us=(30, 36, 44), state_line=(66, 76, 89),
    coast=(92, 104, 118), mt_fill=(116, 24, 28), mt_line=(240, 84, 64), mt_glow=(210, 44, 36))


def us_box():
    cx, _ = lonlat_to_merc(-96.0, 0)
    _, ys = lonlat_to_merc(0, 24.40)
    _, yn = lonlat_to_merc(0, 49.40)
    gx, _ = merc_to_gpx(cx, 0, Z)
    _, gy = merc_to_gpx(0, (ys + yn) / 2, Z)
    px0 = int(round(gx - BOX_W / 2))
    py0 = int(round(gy - BOX_H / 2))
    return px0, py0, px0 + BOX_W, py0 + BOX_H


def make_projector(box, scale):
    px0, py0, _, _ = box
    r = res_at(Z)
    k = scale  # output px per z7 px

    def proj(ring):
        out = []
        for lon, lat in ring:
            x, y = lonlat_to_merc(lon, max(min(lat, 85), -85))
            out.append((((x + math.pi * 6378137.0) / r - px0) * k, ((math.pi * 6378137.0 - y) / r - py0) * k))
        return out
    return proj


def raster(polys_list, proj, size, kind="fill", width=1):
    im = Image.new("L", size, 0)
    dr = ImageDraw.Draw(im)
    for polys in polys_list:
        for poly in polys:
            rings = [proj(r) for r in poly]
            if kind == "fill":
                dr.polygon(rings[0], fill=255)
                for h in rings[1:]:
                    dr.polygon(h, fill=0)
            else:
                for r in rings:
                    dr.line(r, fill=255, width=width, joint="curve")
    return im


def down(im):
    return np.asarray(im.resize((OUT_W, OUT_H), Image.BOX)).astype(np.float32) / 255.0


def bbox_ok(poly, lon0=-140, lon1=-50, lat0=10, lat1=60):
    xs = [p[0] for p in poly[0]]
    ys = [p[1] for p in poly[0]]
    return max(xs) > lon0 and min(xs) < lon1 and max(ys) > lat0 and min(ys) < lat1


def main():
    d = os.path.join(OUT, "us")
    os.makedirs(d, exist_ok=True)
    box = us_box()
    px0, py0, px1, py1 = box
    west, north = gpx_to_merc(px0, py0, Z)
    east, south = gpx_to_merc(px1, py1, Z)
    lw, ln = merc_to_lonlat(west, north)
    le, ls = merc_to_lonlat(east, south)
    print("US box z7 px", box, "lon", lw, le, "lat", ls, ln)

    # ---------------- DEM (terrarium z7) resampled to the render grid
    e = terrarium_decode(mosaic("terrarium", Z, *box))
    lat_mid = merc_to_lonlat(0, (gpx_to_merc(0, py0, Z)[1] + gpx_to_merc(0, py1, Z)[1]) / 2)[1]
    e, nfix = despike(e, threshold_m=max(40.0, 0.9 * res_at(Z) * math.cos(math.radians(lat_mid))))
    e_img = Image.fromarray(e.astype(np.float32), mode="F").resize((OUT_W, OUT_H), Image.BOX)
    e4 = np.asarray(e_img).astype(np.float64)
    u16, lo, hi = encode_height(e4)
    save_png16(os.path.join(d, "us_heightmap.png"), u16)
    u16.astype("<u2").tofile(os.path.join(d, "us_heightmap_u16le.bin"))
    lat_c = merc_to_lonlat(0, (north + south) / 2)[1]
    gpx = (east - west) / OUT_W * math.cos(math.radians(lat_c))

    # ---------------- vectors
    sproj = make_projector(box, OUT_W * SS / BOX_W)
    big = (OUT_W * SS, OUT_H * SS)
    shp = fetch("ne_10m_land")
    land = [[p for p in g if bbox_ok(p)] for g in read_shp(shp)]
    lakes_shp = fetch("ne_10m_lakes")
    lake_rows = read_dbf(lakes_shp[:-4] + ".dbf")
    lake_geo = read_shp(lakes_shp)
    lakes_ctx = [[p for p in g if bbox_ok(p)] for g, r in zip(lake_geo, lake_rows) if r["scalerank"] <= 3]
    lakes_top = [[p for p in g if bbox_ok(p)] for g, r in zip(lake_geo, lake_rows) if r["scalerank"] <= 2]
    st_shp = fetch("cb_2023_us_state_5m")
    st_rows = read_dbf(st_shp[:-4] + ".dbf")
    st_geo = read_shp(st_shp)
    skip = {"02", "15", "60", "66", "69", "72", "78"}
    states = [g for g, r in zip(st_geo, st_rows) if r["STATEFP"] not in skip]
    mt = [g for g, r in zip(st_geo, st_rows) if r["STUSPS"] == "MT"]
    nat = read_shp(fetch("cb_2023_us_nation_5m"))[0]
    nat = [[p for p in nat if bbox_ok(p, -126, -66, 24, 50)]]

    M = {}
    M["land"] = down(raster(land, sproj, big))
    M["lakes_ctx"] = down(raster(lakes_ctx, sproj, big))
    M["us"] = down(raster(states, sproj, big))
    M["lakes_top"] = down(raster(lakes_top, sproj, big))
    M["state_line"] = down(raster(states, sproj, big, "line", width=4))
    M["coast"] = down(raster(nat, sproj, big, "line", width=5))
    mt_fill_big = raster(mt, sproj, big)
    M["mt"] = down(mt_fill_big)
    M["mt_line"] = down(raster(mt, sproj, big, "line", width=7))
    print("masks ok")

    # ---------------- relief
    hs = hillshade(np.maximum(e4, 0), gpx, azimuth=315, altitude=45, z_factor=9.0)
    hs2 = hillshade(np.maximum(e4, 0), gpx, azimuth=20, altitude=55, z_factor=9.0)
    flat = math.sin(math.radians(45)) * 0.6 + math.sin(math.radians(55)) * 0.4
    rel = (hs * 0.6 + hs2 * 0.4) - flat
    rel_us = np.clip(1.0 + 1.15 * rel, 0.55, 1.6)[..., None]
    rel_ctx = np.clip(1.0 + 0.8 * rel, 0.65, 1.4)[..., None]

    def c(name):
        return np.array(COL[name], np.float32) / 255.0

    def lerp(a, b, m):
        return a + (b - a) * m[..., None]

    img = np.empty((OUT_H, OUT_W, 3), np.float32)
    img[:] = c("ocean")
    img = lerp(img, c("land_ctx") * rel_ctx, M["land"])
    img = lerp(img, c("ocean"), M["lakes_ctx"])
    img = lerp(img, c("us") * rel_us, M["us"])
    img = lerp(img, c("ocean"), M["lakes_top"])
    img = lerp(img, c("state_line"), M["state_line"] * M["us"].clip(0.35, 1))
    img = lerp(img, c("coast"), M["coast"])
    base = np.clip(img, 0, 1)

    def save(a, name):
        Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(d, name), optimize=True)

    save(base, "us_dark.png")

    # Montana highlight
    m = M["mt"]
    glow_im = Image.fromarray((m * 255).astype(np.uint8))
    glow = (np.asarray(glow_im.filter(ImageFilter.GaussianBlur(26))).astype(np.float32) / 255 * 0.55 +
            np.asarray(glow_im.filter(ImageFilter.GaussianBlur(8))).astype(np.float32) / 255 * 0.45)
    hi_img = base + c("mt_glow") * (glow * (1 - m) * 0.7)[..., None]
    hi_img = lerp(hi_img, c("mt_fill") * np.clip(rel_us * 1.05, 0.6, 1.7), m * 0.92)
    hi_img = lerp(hi_img, c("mt_line"), M["mt_line"])
    save(hi_img, "us_dark_montana.png")
    Image.fromarray((m * 255 + 0.5).astype(np.uint8)).save(os.path.join(d, "montana_mask.png"), optimize=True)
    # boundary-only mask (handy for a glowing outline / draw-on)
    Image.fromarray((M["mt_line"] * 255 + 0.5).astype(np.uint8)).save(os.path.join(d, "montana_outline_mask.png"),
                                                                      optimize=True)

    meta = dict(
        box="us",
        projection="EPSG:3857 (Web Mercator, spherical, R = 6378137 m). Rows run north->south.",
        pixel_convention="area: every image spans exactly the bounds edge-to-edge.",
        snapped_to=f"zoom 7 tile-pixel grid (global px {px0}..{px1} x {py0}..{py1}), {BOX_W}x{BOX_H} z7 px "
                   f"resampled to {OUT_W}x{OUT_H} (exact 16:9)",
        bounds_lonlat=dict(west=lw, south=ls, east=le, north=ln),
        bounds_mercator_m=dict(west=west, south=south, east=east, north=north),
        size_mercator_m=dict(width=east - west, height=north - south),
        layers=dict(
            us_dark=dict(files=["us_dark.png"], width=OUT_W, height=OUT_H,
                         note="dark stylised contiguous US: Census 1:5M states, Natural Earth 10m land/lakes "
                              "for context, subtle relief from the terrain tiles"),
            us_dark_montana=dict(files=["us_dark_montana.png"], width=OUT_W, height=OUT_H,
                                 note="same with Montana highlighted (crimson fill, bright edge, soft outer glow)"),
            montana_mask=dict(files=["montana_mask.png"], width=OUT_W, height=OUT_H,
                              note="8-bit alpha mask of Montana (antialiased, 3x supersampled); white = Montana"),
            montana_outline_mask=dict(files=["montana_outline_mask.png"], width=OUT_W, height=OUT_H,
                                      note="8-bit mask of the Montana border line (~2.3 px wide)"),
            us_heightmap=dict(files=["us_heightmap.png", "us_heightmap_u16le.bin"], width=OUT_W, height=OUT_H,
                              source="AWS Terrain Tiles (terrarium) z7, box-filtered to the render grid",
                              encoding="elevation_m = min_m + value / 65535 * (max_m - min_m); includes ocean "
                                       "bathymetry (negative) - clamp at 0 for a land-only relief",
                              min_m=round(lo, 2), max_m=round(hi, 2), despiked_pixels=nfix,
                              pixel_size_ground_m_at_center=gpx)),
        colours=COL,
    )
    write_json(os.path.join(d, "bounds.json"), meta)
    print("done", lo, hi, nfix)


if __name__ == "__main__":
    main()
