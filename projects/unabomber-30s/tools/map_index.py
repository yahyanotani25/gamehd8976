"""Write assets/map/index.json: every box's bounds plus, for each pair of
boxes, where the smaller one sits inside the larger one (UV 0..1, origin top
left), and every reference point's UV in every box.

  python3 -I tools/map_index.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from map_common import OUT, lonlat_to_merc, write_json  # noqa: E402

ORDER = ["us", "wide", "regional", "closeup"]


def uv(b, x, y):
    return ((x - b["west"]) / (b["east"] - b["west"]), (b["north"] - y) / (b["north"] - b["south"]))


def main():
    boxes = {n: json.load(open(os.path.join(OUT, n, "bounds.json"))) for n in ORDER}
    pts = json.load(open(os.path.join(OUT, "vector", "points.json")))["features"]
    idx = dict(
        projection="All rasters are EPSG:3857 Web Mercator (R = 6378137 m), north up. UV origin = top-left.",
        lonlat_to_mercator="x = R * lon_rad ; y = R * ln(tan(pi/4 + lat_rad/2))",
        mercator_to_uv="u = (x - west) / (east - west) ; v = (north - y) / (north - south) ; px = u * width ; py = v * height",
        boxes={},
    )
    for n in ORDER:
        b = boxes[n]["bounds_mercator_m"]
        entry = dict(dir=n + "/", bounds_lonlat=boxes[n]["bounds_lonlat"], bounds_mercator_m=b,
                     images={k: dict(files=v["files"], width=v["width"], height=v["height"])
                             for k, v in boxes[n]["layers"].items()},
                     contains={}, points_uv={})
        for m in ORDER[ORDER.index(n) + 1:]:
            c = boxes[m]["bounds_mercator_m"]
            u0, v0 = uv(b, c["west"], c["north"])
            u1, v1 = uv(b, c["east"], c["south"])
            entry["contains"][m] = dict(u0=round(u0, 7), v0=round(v0, 7), u1=round(u1, 7), v1=round(v1, 7))
        for f in pts:
            lon, lat = f["geometry"]["coordinates"]
            u, v = uv(b, *lonlat_to_merc(lon, lat))
            if 0 <= u <= 1 and 0 <= v <= 1:
                entry["points_uv"][f["properties"]["name"]] = [round(u, 6), round(v, 6)]
        idx["boxes"][n] = entry
    write_json(os.path.join(OUT, "index.json"), idx)
    for n in ORDER:
        print(n, idx["boxes"][n]["contains"], list(idx["boxes"][n]["points_uv"]))


if __name__ == "__main__":
    main()
