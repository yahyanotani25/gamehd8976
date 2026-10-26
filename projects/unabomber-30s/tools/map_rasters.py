"""Download + mosaic terrain (AWS Terrain Tiles, terrarium) and USGS National Map
imagery / shaded relief / topo for the map boxes, all cropped to identical
Web Mercator bounds. Writes into assets/map/<box>/.

  python3 -I tools/map_rasters.py [box ...]      (default: all boxes)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from map_common import (OUT, BOXES, box_bounds, box_px_at, despike,  # noqa: E402
                        encode_height, hillshade, mosaic, res_at, save_png16,
                        snapped_box, terrarium_decode, write_json)

Image.MAX_IMAGE_PIXELS = None
MAX_SIDE = 8192

# Per box: DEM zoom (= box base zoom) and the raster layers to build.
# layer: (source, zoom, output name)
PLAN = {
    "regional": dict(layers=[("imagery", 14, "imagery"), ("shaded", 13, "usgs_shaded_relief"),
                             ("topo", 13, "usgs_topo")]),
    # USGSShadedReliefOnly has no cached tiles at z9-z11 here, so the wide box uses z12 (resampled).
    "wide": dict(layers=[("imagery", 11, "imagery"), ("shaded", 12, "usgs_shaded_relief"),
                         ("topo", 10, "usgs_topo")]),
    "closeup": dict(layers=[("imagery", 16, "imagery"), ("topo", 15, "usgs_topo")]),
}


def fit(img, max_side=MAX_SIDE):
    w, h = img.size
    s = min(1.0, max_side / max(w, h))
    if s >= 1.0:
        return img, 1.0
    nw, nh = round(w * s), round(h * s)
    return img.resize((nw, nh), Image.LANCZOS), s


def build(name):
    cfg = BOXES[name]
    box = snapped_box(**cfg)
    bb = box_bounds(box)
    lat_mid = math.degrees(math.atan(math.sinh(
        (bb["mercator_m"]["north"] + bb["mercator_m"]["south"]) / 2 / 6378137.0)))
    cos_c = math.cos(math.radians(lat_mid))
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    W_m = bb["mercator_m"]["east"] - bb["mercator_m"]["west"]
    H_m = bb["mercator_m"]["north"] - bb["mercator_m"]["south"]
    meta = dict(
        box=name,
        projection="EPSG:3857 (Web Mercator, spherical, R = 6378137 m). Rows run north->south, columns west->east.",
        pixel_convention="area: every image spans exactly the bounds below edge-to-edge; pixel (i, j) covers "
                         "[west + i*W/width, west + (i+1)*W/width] etc. Pixel centres are at +0.5.",
        requested=dict(center_lat=cfg["center"][0], center_lon=cfg["center"][1],
                       width_km=cfg["width_km"], height_km=cfg["height_km"]),
        snapped_to=f"zoom {box['zoom']} tile-pixel grid (global px {box['px0']}..{box['px1']} x "
                   f"{box['py0']}..{box['py1']})",
        bounds_lonlat=bb["lonlat"],
        bounds_mercator_m=bb["mercator_m"],
        size_mercator_m=dict(width=W_m, height=H_m),
        center_lat_of_bounds=lat_mid,
        size_ground_km_at_center=dict(width=W_m * cos_c / 1000, height=H_m * cos_c / 1000,
                                      note="ground metres = mercator metres * cos(lat); "
                                           "scale varies ~±%.1f%% north/south edge" % (
                                               100 * abs(math.cos(math.radians(bb['lonlat']['north'])) / cos_c - 1))),
        layers={},
    )

    # ---- terrain
    z = box["zoom"]
    px = box_px_at(box, z)
    rgb = mosaic("terrarium", z, *px)
    gpx = res_at(z) * cos_c
    elev, nfix = despike(terrarium_decode(rgb), threshold_m=max(40.0, 0.9 * gpx))
    u16, lo, hi = encode_height(elev)
    h, w = u16.shape
    save_png16(os.path.join(d, "heightmap.png"), u16)
    u16.astype("<u2").tofile(os.path.join(d, "heightmap_u16le.bin"))
    hs = hillshade(elev, gpx, azimuth=315, altitude=40)
    Image.fromarray((hs * 255).round().astype(np.uint8)).save(os.path.join(d, "hillshade.png"), optimize=True)
    meta["layers"]["heightmap"] = dict(
        files=["heightmap.png", "heightmap_u16le.bin"], width=w, height=h,
        source="AWS Terrain Tiles (terrarium)", tile_zoom=z,
        pixel_size_mercator_m=res_at(z), pixel_size_ground_m_at_center=gpx,
        encoding="16-bit unsigned, linear: elevation_m = min_m + value / 65535 * (max_m - min_m). "
                 "heightmap.png = 16-bit grayscale PNG; heightmap_u16le.bin = the same values as raw "
                 "little-endian uint16, row-major, width*height, no header.",
        min_m=round(lo, 3), max_m=round(hi, 3), mean_m=round(float(elev.mean()), 2),
        quantum_m=round((hi - lo) / 65535, 5),
        despiked_pixels=nfix,
        despike_note="isolated terrarium spike/pit pixels (> max(40 m, 0.9 px) above/below all 8 neighbours) "
                     "replaced by the neighbour median")
    meta["layers"]["hillshade"] = dict(
        files=["hillshade.png"], width=w, height=h,
        note="8-bit hillshade computed from the heightmap (sun azimuth 315 deg, altitude 40 deg, no exaggeration).")
    print(f"[{name}] heightmap {w}x{h} z{z}  elev {lo:.1f}..{hi:.1f} m  ground px {gpx:.1f} m  "
          f"despiked {nfix}", flush=True)

    # ---- rasters
    for src, lz, out in PLAN[name]["layers"]:
        p = box_px_at(box, lz)
        arr = mosaic(src, lz, *p)
        img = Image.fromarray(arr)
        native = img.size
        img, s = fit(img)
        fn = f"{out}.jpg"
        img.save(os.path.join(d, fn), quality=92 if src == "imagery" else 90,
                 subsampling=0 if src != "imagery" else 2, optimize=True)
        meta["layers"][out] = dict(
            files=[fn], width=img.size[0], height=img.size[1], tile_zoom=lz,
            native_mosaic_size=list(native), resampled=s < 1.0,
            pixel_size_ground_m_at_center=res_at(lz) * cos_c / s,
            source={"imagery": "USGS The National Map - USGSImageryOnly (orthoimagery, USDA NAIP at large scales)",
                    "shaded": "USGS The National Map - USGSShadedReliefOnly (3DEP)",
                    "topo": "USGS The National Map - USGSTopo"}[src])
        print(f"[{name}] {out}: z{lz} native {native} -> {img.size}", flush=True)
    write_json(os.path.join(d, "bounds.json"), meta)


if __name__ == "__main__":
    names = sys.argv[1:] or list(PLAN)
    for n in names:
        build(n)
