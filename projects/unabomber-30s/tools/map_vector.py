"""Vector data: US states (Census cartographic boundary 1:5M, 2023), Montana,
contiguous-US nation outline, and reference points -> assets/map/vector/.

Sources are downloaded to the scratch dir and parsed with a tiny built-in
shapefile/DBF reader (no GDAL needed).

  python3 -I tools/map_vector.py
"""
import json
import os
import struct
import sys
import urllib.request
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from map_common import OUT, SCRATCH, UA  # noqa: E402

SRC = os.path.join(SCRATCH, "vector_src")
URLS = {
    "cb_2023_us_state_5m": "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_state_5m.zip",
    "cb_2023_us_nation_5m": "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_nation_5m.zip",
    "ne_10m_admin_0_countries": "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip",
    "ne_10m_lakes": "https://naciscdn.org/naturalearth/10m/physical/ne_10m_lakes.zip",
}
NON_CONTIGUOUS = {"02", "15", "60", "66", "69", "72", "78"}  # AK, HI, AS, GU, MP, PR, VI

# name, lat, lon, state, role. Coordinates from the English Wikipedia
# article infobox (GNIS-derived), read 2026-10-25.
POINTS = [
    ("Lincoln, MT", 46.95556, -112.67278, "MT", "town nearest Kaczynski's cabin"),
    ("Helena, MT", 46.59639, -112.02639, "MT", "Montana state capital, ~63 km SE of Lincoln"),
    ("Missoula, MT", 46.87436, -114.02614, "MT", "context city"),
    ("Great Falls, MT", 47.49167, -111.28917, "MT", "context city"),
    ("Chicago, IL", 41.88194, -87.62778, "IL", "Kaczynski's birthplace (for later use)"),
    ("Berkeley, CA", 37.87167, -122.27278, "CA", "UC Berkeley, where Kaczynski taught mathematics 1967-69 (for later use)"),
]


def fetch(name):
    os.makedirs(SRC, exist_ok=True)
    d = os.path.join(SRC, name)
    shp = os.path.join(d, name + ".shp")
    if os.path.exists(shp):
        return shp
    z = d + ".zip"
    req = urllib.request.Request(URLS[name], headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r, open(z, "wb") as f:
        f.write(r.read())
    with zipfile.ZipFile(z) as zf:
        zf.extractall(d)
    return shp


# ------------------------------------------------------------ shapefile I/O
def read_dbf(path):
    with open(path, "rb") as f:
        data = f.read()
    n, hlen, rlen = struct.unpack("<IHH", data[4:12])
    fields = []
    off = 32
    while data[off] != 0x0D:
        name = data[off:off + 11].split(b"\0")[0].decode("ascii")
        fields.append((name, chr(data[off + 11]), data[off + 16]))
        off += 32
    rows = []
    for i in range(n):
        rec = data[hlen + i * rlen: hlen + (i + 1) * rlen]
        pos, row = 1, {}
        for name, typ, ln in fields:
            raw = rec[pos:pos + ln].decode("utf-8", "replace").replace("\0", "").strip()
            pos += ln
            if typ in "NF" and raw:
                try:
                    raw = float(raw) if ("." in raw or "e" in raw.lower()) else int(raw)
                except ValueError:
                    pass
            row[name] = raw
        rows.append(row)
    return rows


def ring_area(r):
    a = 0.0
    for (x0, y0), (x1, y1) in zip(r, r[1:]):
        a += x0 * y1 - x1 * y0
    return a / 2  # > 0 = counter-clockwise


def point_in_ring(x, y, r):
    inside = False
    for (x0, y0), (x1, y1) in zip(r, r[1:]):
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            inside = not inside
    return inside


def read_shp(path):
    """Polygon shapefile -> list of polygons per record; each polygon is
    [outer, hole, ...] with RFC 7946 winding (outer CCW, holes CW)."""
    with open(path, "rb") as f:
        data = f.read()
    off = 100
    out = []
    while off < len(data):
        _, clen = struct.unpack(">ii", data[off:off + 8])
        off += 8
        rec = data[off:off + clen * 2]
        off += clen * 2
        st = struct.unpack("<i", rec[:4])[0]
        if st == 0:
            out.append([])
            continue
        assert st in (5, 15, 25), st
        nparts, npts = struct.unpack("<ii", rec[36:44])
        parts = list(struct.unpack(f"<{nparts}i", rec[44:44 + 4 * nparts]))
        p0 = 44 + 4 * nparts
        pts = struct.unpack(f"<{2 * npts}d", rec[p0:p0 + 16 * npts])
        xy = list(zip(pts[0::2], pts[1::2]))
        rings = [xy[a:b] for a, b in zip(parts, parts[1:] + [npts])]
        outers, holes = [], []
        for r in rings:
            (outers if ring_area(r) < 0 else holes).append(r)  # shapefile: outer = CW
        polys = [[o[::-1]] for o in outers]  # make outers CCW
        for h in holes:
            hx, hy = h[0]
            for poly in polys:
                if point_in_ring(hx, hy, poly[0]):
                    poly.append(h[::-1])  # holes CW
                    break
        out.append(polys)
    return out


def rnd(polys, nd=5):
    return [[[[round(x, nd), round(y, nd)] for x, y in ring] for ring in poly] for poly in polys]


def feature(props, polys):
    return {"type": "Feature", "properties": props,
            "geometry": {"type": "MultiPolygon", "coordinates": rnd(polys)}}


def fc(features, **meta):
    d = {"type": "FeatureCollection"}
    d.update(meta)
    d["features"] = features
    return d


def save(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, separators=(",", ":"))


def main():
    vd = os.path.join(OUT, "vector")
    os.makedirs(vd, exist_ok=True)
    credit_states = ("U.S. Census Bureau, 2023 Cartographic Boundary File cb_2023_us_state_5m (1:5,000,000), "
                     "public domain (US federal government work)")
    shp = fetch("cb_2023_us_state_5m")
    geoms = read_shp(shp)
    rows = read_dbf(shp[:-4] + ".dbf")
    feats = []
    for g, r in zip(geoms, rows):
        if r["STATEFP"] in NON_CONTIGUOUS:
            continue
        props = {k: r[k] for k in ("NAME", "STUSPS", "STATEFP", "GEOID")}
        feats.append(feature(props, g))
    feats.sort(key=lambda f: f["properties"]["NAME"])
    save(os.path.join(vd, "us_states_contiguous.geojson"),
         fc(feats, name="US states, contiguous 48 + DC", source=credit_states, crs_note="WGS84/NAD83 lon,lat (EPSG:4269 ~ 4326)"))
    mt = [f for f in feats if f["properties"]["STUSPS"] == "MT"]
    save(os.path.join(vd, "montana.geojson"), fc(mt, name="Montana", source=credit_states))
    print("states:", len(feats), "MT rings:", sum(len(p) for p in mt[0]["geometry"]["coordinates"]))

    # nation outline, contiguous part only (drop polygons outside the CONUS bbox)
    shp = fetch("cb_2023_us_nation_5m")
    g = read_shp(shp)[0]
    conus = [p for p in g if all(-125.5 < x < -66 and 24 < y < 49.5 for x, y in p[0][:: max(1, len(p[0]) // 20)])]
    save(os.path.join(vd, "us_nation_contiguous.geojson"),
         fc([feature({"NAME": "United States (contiguous)"}, conus)], name="US national outline, contiguous",
            source="U.S. Census Bureau, 2023 Cartographic Boundary File cb_2023_us_nation_5m, public domain"))
    print("nation polys:", len(conus), "of", len(g))

    pts = [{"type": "Feature", "properties": {"name": n, "state": s, "note": note},
            "geometry": {"type": "Point", "coordinates": [lon, lat]}} for n, lat, lon, s, note in POINTS]
    save_pts = fc(pts, name="Reference points",
                  source="English Wikipedia article coordinates (GNIS-derived), read 2026-10-25",
                  note="Lincoln, MT: the production brief uses 46.958, -112.683 (approx. town); Wikipedia gives "
                       "46.95556, -112.67278 (~0.8 km apart). The cabin site itself is intentionally NOT given.")
    with open(os.path.join(vd, "points.json"), "w") as f:
        json.dump(save_pts, f, indent=1)


if __name__ == "__main__":
    main()
