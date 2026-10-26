#!/usr/bin/env python3
"""Flickr photo page scraper (no API key).
Usage: flickr.py info <photo_id> [...]            -> JSON lines: id,title,owner,license,best size url
       flickr.py get <photo_id> <dest_path>         -> download largest available size
       flickr.py thumb <photo_id> <dest_path>       -> download ~500px preview"""
import json, re, sys, time, urllib.request, html
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
ORDER = ["o", "6k", "5k", "4k", "3k", "k", "h", "l", "c", "z"]

def page(pid):
    req = urllib.request.Request(f"https://www.flickr.com/photo.gne?id={pid}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace"), r.geturl()

def info(pid):
    h, final = page(pid)
    sizes = {}
    for m in re.finditer(r'"([0-9a-z]{1,3})":\{"displayUrl":"([^"]+)","width":(\d+),"height":(\d+)', h):
        k, u, w, ht = m.groups()
        sizes.setdefault(k, ("https:" + u.replace("\\/", "/"), int(w), int(ht)))
    lic = re.search(r'"license":\s*"(https?://[^"]+)"', h)
    lic = lic.group(1) if lic else None
    if not lic:
        m = re.search(r'<a[^>]+rel="license"[^>]*href="([^"]+)"', h) or re.search(r'href="(https://creativecommons.org/[^"]+)"', h)
        lic = m.group(1) if m else None
    t = re.search(r'<meta property="og:title" content="([^"]*)"', h)
    owner = re.search(r'"ownerNsid":"([^"]+)"', h)
    rn = re.search(r'"realname":"([^"]*)"', h); un = re.search(r'"username":"([^"]*)"', h)
    pd = "publicdomain" in (lic or "") or "No known copyright" in h[:0]
    best = None
    for k in ORDER:
        if k in sizes: best = (k,) + sizes[k]; break
    return {"id": pid, "page": final, "title": html.unescape(t.group(1)) if t else "",
            "owner": (rn.group(1) if rn and rn.group(1) else (un.group(1) if un else "")),
            "license": lic, "best": best, "preview": sizes.get("z") or sizes.get("c") or sizes.get("l")}

def dl(url, dest):
    for i in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r, open(dest, "wb") as f:
                f.write(r.read())
            return True
        except Exception as e:
            sys.stderr.write(f"retry {e}\n"); time.sleep(5)
    return False

if __name__ == "__main__":
    c = sys.argv[1]
    if c == "info":
        for p in sys.argv[2:]:
            try: print(json.dumps(info(p)))
            except Exception as e: print(json.dumps({"id": p, "error": str(e)}))
    elif c == "get":
        i = info(sys.argv[2]); print(json.dumps(i)); dl(i["best"][1], sys.argv[3])
    elif c == "thumb":
        i = info(sys.argv[2]); dl(i["preview"][0], sys.argv[3])
