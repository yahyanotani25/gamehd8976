"""Shared helpers for the map data tools (tools/map_*.py).

Web Mercator (EPSG:3857) maths, box definitions snapped to the XYZ tile pixel
grid, a cached concurrent tile fetcher and a mosaicker.

Run the tools with `python3 -I tools/map_xxx.py` (isolated mode); each tool
adds this directory to sys.path itself.
"""
import io
import json
import math
import os
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image

R = 6378137.0
HALF = math.pi * R  # 20037508.342789244
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")

PROJECT = "/home/user/gamehd8976/projects/unabomber-30s"
OUT = os.path.join(PROJECT, "assets", "map")
SCRATCH = "/tmp/claude-0/-home-user/c93f696e-b0c6-5e9f-976a-d45dcf4ab420/scratchpad/map"
TILE_CACHE = os.path.join(SCRATCH, "tiles")

SOURCES = {
    # name: (url template, extension)
    "terrarium": ("https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png", "png"),
    "imagery": ("https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}", "img"),
    "shaded": ("https://basemap.nationalmap.gov/arcgis/rest/services/USGSShadedReliefOnly/MapServer/tile/{z}/{y}/{x}", "img"),
    "topo": ("https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}", "img"),
}

# Lincoln, MT (town centre as given in the production brief).
LINCOLN = (46.958, -112.683)

# Box definitions. Ground size is measured at the box centre latitude.
# base_zoom = the zoom whose 256-px tile pixel grid the box edges snap to.
BOXES = {
    "regional": dict(center=LINCOLN, width_km=60.0, height_km=40.0, base_zoom=12),
    "wide": dict(center=LINCOLN, width_km=400.0, height_km=300.0, base_zoom=9),
    # Forest close-up: Lincoln's south edge -> Stemple Pass Rd / Gehring Ranch Rd ->
    # the forested foothills of Baldy Mountain (general area of the cabin; the
    # exact cabin site is NOT marked anywhere in this data).
    "closeup": dict(center=(46.9294, -112.6523), width_km=10.0, height_km=7.0, base_zoom=14),
}


# ---------------------------------------------------------------- projection
def lonlat_to_merc(lon, lat):
    x = math.radians(lon) * R
    y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * R
    return x, y


def merc_to_lonlat(x, y):
    lon = math.degrees(x / R)
    lat = math.degrees(2 * math.atan(math.exp(y / R)) - math.pi / 2)
    return lon, lat


def res_at(z):
    """Mercator metres per pixel at zoom z (256-px tiles)."""
    return 2 * HALF / (256 * 2 ** z)


def merc_to_gpx(x, y, z):
    r = res_at(z)
    return (x + HALF) / r, (HALF - y) / r


def gpx_to_merc(px, py, z):
    r = res_at(z)
    return px * r - HALF, HALF - py * r


def snapped_box(center, width_km, height_km, base_zoom):
    lat, lon = center
    cx, cy = lonlat_to_merc(lon, lat)
    k = 1.0 / math.cos(math.radians(lat))  # ground -> mercator scale
    hw = width_km * 1000 / 2 * k
    hh = height_km * 1000 / 2 * k
    gx0, gy0 = merc_to_gpx(cx - hw, cy + hh, base_zoom)
    gx1, gy1 = merc_to_gpx(cx + hw, cy - hh, base_zoom)
    return dict(zoom=base_zoom, px0=int(math.floor(gx0)), py0=int(math.floor(gy0)),
                px1=int(math.ceil(gx1)), py1=int(math.ceil(gy1)))


def box_px_at(box, z):
    """Box edges (global pixel coords) at zoom z. Exact for z >= box zoom."""
    f = 2 ** (z - box["zoom"])
    return (box["px0"] * f, box["py0"] * f, box["px1"] * f, box["py1"] * f)


def box_bounds(box):
    z = box["zoom"]
    west, north = gpx_to_merc(box["px0"], box["py0"], z)
    east, south = gpx_to_merc(box["px1"], box["py1"], z)
    lw, ln = merc_to_lonlat(west, north)
    le, ls = merc_to_lonlat(east, south)
    return dict(mercator_m=dict(west=west, south=south, east=east, north=north),
                lonlat=dict(west=lw, south=ls, east=le, north=ln))


# ---------------------------------------------------------------- tiles
def _tile_path(src, z, x, y):
    ext = SOURCES[src][1]
    return os.path.join(TILE_CACHE, src, str(z), str(x), f"{y}.{ext}")


def fetch_tile(src, z, x, y, retries=5):
    path = _tile_path(src, z, x, y)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    url = SOURCES[src][0].format(z=z, x=x, y=y)
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            Image.open(io.BytesIO(data)).verify()
            tmp = path + ".part"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, path)
            return path
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 404:
                return None
            time.sleep(1.5 * (i + 1))
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"failed {url}: {last}")


def fetch_range(src, z, px0, py0, px1, py1, workers=8):
    tx0, ty0 = px0 // 256, py0 // 256
    tx1, ty1 = (px1 - 1) // 256, (py1 - 1) // 256
    jobs = [(tx, ty) for ty in range(ty0, ty1 + 1) for tx in range(tx0, tx1 + 1)]
    missing = []
    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(fetch_tile, src, z, tx, ty): (tx, ty) for tx, ty in jobs}
        for f in futs:
            if f.result() is None:
                missing.append(futs[f])
    print(f"  {src} z{z}: {len(jobs)} tiles ({tx1 - tx0 + 1}x{ty1 - ty0 + 1}), "
          f"{len(missing)} missing, {time.time() - t0:.1f}s", flush=True)
    return missing


def mosaic(src, z, px0, py0, px1, py1, mode="RGB"):
    """Mosaic tiles covering global pixel rect [px0,px1)x[py0,py1) at zoom z
    and crop to it exactly. Returns a uint8 numpy array (H, W, C)."""
    fetch_range(src, z, px0, py0, px1, py1)
    tx0, ty0 = px0 // 256, py0 // 256
    tx1, ty1 = (px1 - 1) // 256, (py1 - 1) // 256
    ch = len(mode)
    big = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256, ch), np.uint8)
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            p = _tile_path(src, z, tx, ty)
            if not os.path.exists(p):
                continue
            im = Image.open(p).convert(mode)
            a = np.asarray(im).reshape(256, 256, ch)
            big[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = a
    ox, oy = px0 - tx0 * 256, py0 - ty0 * 256
    return big[oy:oy + (py1 - py0), ox:ox + (px1 - px0)]


def terrarium_decode(rgb):
    rgb = rgb.astype(np.float64)
    return rgb[..., 0] * 256.0 + rgb[..., 1] + rgb[..., 2] / 256.0 - 32768.0


def despike(elev, threshold_m, passes=6):
    """Remove the isolated spike/pit pixels terrarium tiles have (resampling
    ringing near lake shores / data seams). A pixel is an outlier when it is
    above the max (or below the min) of its 8 neighbours by > threshold_m; it
    is replaced by the median of its 8 neighbours. Iterated so that 2-3 px
    clusters are removed too. Returns (fixed array, number of fixes)."""
    e = elev.astype(np.float64).copy()
    total = 0
    h, w = e.shape
    for _ in range(passes):
        p = np.pad(e, 1, mode="edge")
        nb = np.stack([p[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
                       for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0)])
        mx, mn = nb.max(0), nb.min(0)
        bad = (e - mx > threshold_m) | (mn - e > threshold_m)
        n = int(bad.sum())
        if n == 0:
            break
        med = np.median(nb[:, bad], axis=0)
        e[bad] = med
        total += n
    return e, total


# ---------------------------------------------------------------- outputs
def save_png16(path, arr_u16):
    """Save a 2-D uint16 array as a 16-bit grayscale PNG."""
    h, w = arr_u16.shape
    im = Image.frombytes("I;16", (w, h), arr_u16.astype("<u2").tobytes())
    im.save(path, optimize=False)


def encode_height(elev):
    lo, hi = float(elev.min()), float(elev.max())
    v = np.round((elev - lo) / (hi - lo) * 65535.0).clip(0, 65535).astype(np.uint16)
    return v, lo, hi


def hillshade(elev, ground_px_m, azimuth=315.0, altitude=40.0, z_factor=1.0):
    """Classic hillshade (0..1). elev rows run north->south."""
    gy, gx = np.gradient(elev.astype(np.float64) * z_factor, ground_px_m)
    dzdx, dzdy = gx, -gy  # x east, y north (rows run southwards)
    az, alt = math.radians(azimuth), math.radians(altitude)
    lx, ly, lz = math.sin(az) * math.cos(alt), math.cos(az) * math.cos(alt), math.sin(alt)
    hs = (-dzdx * lx - dzdy * ly + lz) / np.sqrt(dzdx * dzdx + dzdy * dzdy + 1.0)
    return np.clip(hs, 0, 1)


def write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def rel(path):
    return os.path.relpath(path, OUT)
