#!/usr/bin/env python3
"""Openverse image search. Usage: openverse.py "<query>" [min_width] [page_size]
Filters: commercial-usable licences, photographs, wide aspect."""
import json, sys, urllib.parse, urllib.request, time
UA = "UnabomberDocAssetResearch/1.0 (personal documentary video project)"
q = sys.argv[1]; minw = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
ps = sys.argv[3] if len(sys.argv) > 3 else "20"
params = {"q": q, "license": "cc0,pdm,by,by-sa", "page_size": ps,
}
url = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(params)
for i in range(5):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
            d = json.load(r); break
    except urllib.error.HTTPError as e:
        if e.code == 429: time.sleep(30); continue
        raise
for x in d.get("results", []):
    w = x.get("width") or 0
    if w and w < minw: continue
    print(f"{w}x{x.get('height')}\t{x['license']}{x.get('license_version') or ''}\t{x.get('source')}\t{(x.get('title') or '')[:60]}\t{x.get('foreign_landing_url')}\t{x.get('creator')}")
