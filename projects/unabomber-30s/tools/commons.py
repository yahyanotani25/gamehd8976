#!/usr/bin/env python3
"""Small Wikimedia Commons API helper with rate-limit backoff.
Usage:
  commons.py search "<query>" [limit]          -> list File: titles (+size, license)
  commons.py info "File:Title.jpg" ...          -> JSON imageinfo with extmetadata
  commons.py cat "Category:Name" [limit]        -> list files in a category (+size, license)
  commons.py rsearch "<query>" [limit]         -> REST search (not rate-limited like api.php); titles only
  commons.py hinfo "File:Title.jpg" ...         -> licence/size/url parsed from the file page HTML (fallback)
  commons.py get list.tsv out_dir               -> download originals; list.tsv lines: dest_name<TAB>File:Title
                                                  (writes out_dir/_meta.json with licence metadata; if upload.wikimedia.org
                                                  answers 429, falls back to a full-width render via commons /w/thumb.php)
"""
import json, os, sys, time, urllib.parse, urllib.request, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

UA = "ClaudeCode-AssetFetcher/1.0 (https://claude.com/claude-code; documentary asset research) python-urllib/3.13"
API = "https://commons.wikimedia.org/w/api.php"

def get(params, tries=8):
    params = dict(params, format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                ra = int(e.headers.get("retry-after", "20") or 20)
                sys.stderr.write(f"429, waiting {ra+2}s\n")
                time.sleep(ra + 2)
                continue
            raise
    raise SystemExit("too many retries")

def strip(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()

def info(titles):
    out = []
    for i in range(0, len(titles), 40):
        d = get({"action": "query", "titles": "|".join(titles[i:i+40]), "prop": "imageinfo",
                 "iiprop": "url|size|extmetadata|mime", "iiurlwidth": "400"})
        for p in d["query"]["pages"]:
            ii = (p.get("imageinfo") or [{}])[0]
            em = ii.get("extmetadata", {})
            out.append({
                "title": p["title"], "w": ii.get("width"), "h": ii.get("height"),
                "size": ii.get("size"), "mime": ii.get("mime"), "url": ii.get("url"),
                "thumb": ii.get("thumburl"),
                "page": ii.get("descriptionurl"),
                "license": strip(em.get("LicenseShortName", {}).get("value")),
                "artist": strip(em.get("Artist", {}).get("value"))[:200],
                "credit": strip(em.get("Credit", {}).get("value"))[:200],
                "desc": strip(em.get("ImageDescription", {}).get("value"))[:300],
                "date": strip(em.get("DateTimeOriginal", {}).get("value"))[:60],
                "restrictions": strip(em.get("Restrictions", {}).get("value")),
            })
    return out

def show(rows):
    for r in rows:
        print(f"{r['w']}x{r['h']}\t{(r['size'] or 0)//1024}KB\t{r['license']}\t{r['title']}")

def rsearch(q, lim=50):
    url = "https://commons.wikimedia.org/w/rest.php/v1/search/page?" + urllib.parse.urlencode({"q": q, "limit": lim})
    for i in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                d = json.load(r)
            return [p["title"] for p in d.get("pages", []) if p["title"].startswith("File:")]
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(15); continue
            raise
    return []

def hinfo(title):
    import html as H
    url = "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))
    for i in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                h = r.read().decode("utf-8", "replace"); break
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(15); continue
            return {"title": title, "error": e.code}
    h = h.replace("&#95;", "_")
    m = re.search(r'class="fullMedia".*?href="([^"]+)".*?\(([\d,]+) \D+ ([\d,]+) pixels', h, re.S)
    lic = re.findall(r'class="licensetpl_short"[^>]*>(.*?)</span>', h, re.S)
    aut = re.search(r'id="fileinfotpl_aut"[^>]*>.*?</td>\s*<td[^>]*>(.*?)</td>', h, re.S)
    return {"title": title, "url": H.unescape(m.group(1)).split("?")[0] if m else None,
            "w": int(m.group(2).replace(",", "")) if m else None, "h": int(m.group(3).replace(",", "")) if m else None,
            "license": [strip(H.unescape(x)) for x in lic], "artist": strip(H.unescape(aut.group(1)))[:200] if aut else None,
            "page": url}

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "search":
        lim = sys.argv[3] if len(sys.argv) > 3 else "50"
        d = get({"action": "query", "list": "search", "srsearch": sys.argv[2], "srnamespace": "6", "srlimit": lim})
        titles = [x["title"] for x in d["query"]["search"]]
        show(info(titles)) if titles else print("(none)")
    elif cmd == "cat":
        lim = sys.argv[3] if len(sys.argv) > 3 else "100"
        d = get({"action": "query", "list": "categorymembers", "cmtitle": sys.argv[2], "cmlimit": lim, "cmtype": "file|subcat"})
        titles = [x["title"] for x in d["query"]["categorymembers"]]
        subs = [t for t in titles if t.startswith("Category:")]
        for s in subs: print("SUBCAT\t" + s)
        files = [t for t in titles if t.startswith("File:")]
        show(info(files)) if files else None
    elif cmd == "rsearch":
        for t in rsearch(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 50): print(t)
    elif cmd == "hinfo":
        for t in sys.argv[2:]: print(json.dumps(hinfo(t))); time.sleep(1)
    elif cmd == "get":
        from wm_preview import wm_url, fetch
        out = sys.argv[3]; os.makedirs(out, exist_ok=True)
        rows = [l.rstrip("\n").split("\t")[:2] for l in open(sys.argv[2]) if l.strip() and not l.startswith("#")]
        mp = os.path.join(out, "_meta.json")
        meta = json.load(open(mp)) if os.path.exists(mp) else {}
        need = [t for d, t in rows if t not in meta]
        for r in (info(need) if need else []): meta[r["title"]] = r
        json.dump(meta, open(mp, "w"), indent=1)
        for dest, t in rows:
            p = os.path.join(out, dest)
            if os.path.exists(p) and os.path.getsize(p) > 5000: continue
            m = meta.get(t, {})
            ok = fetch(wm_url(t), p, tries=1); how = "original"
            if not ok and m.get("w"):
                name = urllib.parse.quote(t.split(":", 1)[1].replace(" ", "_"))
                ok = fetch(f"https://commons.wikimedia.org/w/thumb.php?f={name}&w={m['w']}", p, tries=4); how = "thumb.php full-width"
            m["fetched_as"] = how; m["dest"] = dest; meta[t] = m
            print(("ok " if ok else "FAIL ") + dest + " " + how, flush=True); time.sleep(1)
        json.dump(meta, open(mp, "w"), indent=1)
    elif cmd == "info":
        print(json.dumps(info(sys.argv[2:]), indent=1))
