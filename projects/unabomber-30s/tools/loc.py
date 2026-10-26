#!/usr/bin/env python3
"""LOC photo search + preview.
Usage: loc.py search "<query>" [count]   -> prints idx | title | item url | rights
       loc.py preview "<query>" out_dir [count]  -> downloads thumbs + numbered sheet, writes out_dir/index.json
       loc.py get <item_url_or_id> dest.jpg [width]  -> IIIF jpeg at width (default 'max' -> full)
       loc.py gettif <item_url_or_id> dest.jpg [maxw]  -> no IIIF: download master TIFF, save as JPEG q92 (optionally downscaled)"""
import json, os, sys, urllib.parse, urllib.request, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

def jget(url):
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=90) as r:
                return json.load(r)
        except Exception as e:
            sys.stderr.write(f"retry {e}\n"); time.sleep(5)

def search(q, c):
    params = {"q": q, "fo": "json", "c": c}
    if os.environ.get("LOC_FA"): params["fa"] = os.environ["LOC_FA"]   # e.g. contributor:highsmith, carol m.
    if os.environ.get("LOC_SP"): params["sp"] = os.environ["LOC_SP"]   # page number
    d = jget("https://www.loc.gov/photos/?" + urllib.parse.urlencode(params))
    out = []
    for x in d.get("results", []):
        imgs = x.get("image_url") or []
        out.append({"title": x.get("title", ""), "id": x.get("id"), "date": x.get("date", ""),
                    "thumb": imgs[-1] if imgs else None,
                    "rights": " ".join(x.get("rights") or []) if isinstance(x.get("rights"), list) else str(x.get("rights") or "")})
    return out

def dl(url, dest):
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=300) as r, open(dest, "wb") as f:
                f.write(r.read())
            return True
        except Exception as e:
            sys.stderr.write(f"retry {e} {url}\n"); time.sleep(5)
    return False

def item(idurl):
    if not idurl.startswith("http"): idurl = f"https://www.loc.gov/item/{idurl}/"
    d = jget(idurl.rstrip("/") + "/?fo=json")
    it = d["item"]
    svc = None; full = None; jpg = None; jw = 0; tif = None
    for r in d.get("resources", []):
        for f in r.get("files", []):
            for v in f:
                u = v.get("url", "")
                if "iiif/service" in u and not svc: svc = u.split("/full/")[0]
                if v.get("mimetype") in ("image/jp2", "image/tiff") and v.get("width"):
                    full = (v.get("width"), v.get("height"))
                if v.get("mimetype") == "image/jpeg" and (v.get("width") or 0) > jw: jw = v["width"]; jpg = u
                if v.get("mimetype") == "image/tiff" and not tif: tif = (u, v.get("size"))
    return {"title": it.get("title"), "creator": it.get("contributor_names") or it.get("creator"),
            "rights": it.get("rights_advisory"), "date": it.get("date"), "svc": svc, "full": full, "url": idurl,
            "jpg": jpg, "tif": tif}

if __name__ == "__main__":
    c = sys.argv[1]
    if c == "search":
        for i, x in enumerate(search(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "40")):
            print(f"{i:02d} | {x['title'][:120]} | {x['id']} | {x['rights'][:40]}")
    elif c == "preview":
        from wm_preview import sheet
        out = sys.argv[3]; os.makedirs(out, exist_ok=True)
        res = search(sys.argv[2], sys.argv[4] if len(sys.argv) > 4 else "40")
        items = []
        for i, x in enumerate(res):
            p = os.path.join(out, f"{i:03d}.jpg")
            if x["thumb"]:
                t = x["thumb"].split("#")[0]
                if t.startswith("//"): t = "https:" + t
                t = re.sub(r"/full/pct:[\d.]+/", "/full/400,/", t)
                if not os.path.exists(p): dl(t, p)
            items.append((f"{i:03d} {x['title']}", p))
        json.dump(res, open(os.path.join(out, "index.json"), "w"), indent=1)
        sheet(items, os.path.join(out, "_sheet.jpg"))
        for i, x in enumerate(res): print(f"{i:02d} | {x['title'][:110]} | {x['id']}")
    elif c == "info":
        print(json.dumps(item(sys.argv[2]), indent=1))
    elif c == "gettif":
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        it = item(sys.argv[2]); print(json.dumps(it))
        tmp = sys.argv[3] + ".tif.part"
        if dl(it["tif"][0], tmp):
            im = Image.open(tmp); im.load(); im = im.convert("RGB")
            mw = int(sys.argv[4]) if len(sys.argv) > 4 else 0
            if mw and im.width > mw: im = im.resize((mw, round(im.height * mw / im.width)), Image.LANCZOS)
            im.save(sys.argv[3], quality=92, subsampling=0); os.remove(tmp); print("ok", im.size)
        else: print("FAIL")
    elif c == "get":
        it = item(sys.argv[2]); w = sys.argv[4] if len(sys.argv) > 4 else "max"
        size = "full" if w in ("max", "full") else f"{w},"
        print(json.dumps(it))
        ok = dl(f"{it['svc']}/full/{size}/0/default.jpg", sys.argv[3])
        print("ok" if ok else "FAIL")
