"""horde2.py jobs.json outdir  -- submit all jobs to Stable Horde (anon), poll, save webp. Jobs: [{name, model, w, h, steps, seed, prompt, neg, post}]"""
import sys, json, time, urllib.request, os
UA = "ClaudeCode-video-edit/1.0 (+https://claude.ai/code)"
H = {"apikey": "0000000000", "Content-Type": "application/json", "Client-Agent": "claude-code-video-edit:1.0:anon", "User-Agent": UA}
jobs = json.load(open(sys.argv[1])); outdir = sys.argv[2]; os.makedirs(outdir, exist_ok=True)
def call(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers=H, method="POST" if body is not None else "GET")
    return json.loads(urllib.request.urlopen(req, timeout=90).read())
pending = {}
for j in jobs:
    p = j["prompt"] + (" ### " + j["neg"] if j.get("neg") else "")
    params = {"width": j["w"], "height": j["h"], "steps": j["steps"], "n": 1, "sampler_name": "k_euler", "cfg_scale": j.get("cfg", 1.0), "seed": str(j["seed"])}
    if j.get("post"): params["post_processing"] = j["post"]
    body = {"prompt": p, "params": params, "models": [j["model"]], "r2": True, "nsfw": False, "censor_nsfw": True}
    for attempt in range(5):
        try:
            r = call("https://stablehorde.net/api/v2/generate/async", body)
            pending[r["id"]] = j["name"]; print("submitted", j["name"], r["id"], r.get("kudos"), flush=True); break
        except urllib.error.HTTPError as e:
            msg = e.read()[:300]; print("submit error", j["name"], e.code, msg, flush=True)
            if e.code == 429: time.sleep(30); continue
            break
    time.sleep(2)
t0 = time.time()
while pending and time.time() - t0 < 3600:
    time.sleep(15)
    for jid, name in list(pending.items()):
        try:
            s = call(f"https://stablehorde.net/api/v2/generate/check/{jid}")
        except Exception as e:
            print("check err", name, e, flush=True); continue
        if s.get("faulted") or not s.get("is_possible", True):
            print("FAILED", name, s, flush=True); pending.pop(jid); continue
        if s.get("done"):
            st = call(f"https://stablehorde.net/api/v2/generate/status/{jid}")
            for g in st["generations"]:
                data = urllib.request.urlopen(urllib.request.Request(g["img"], headers={"User-Agent": UA}), timeout=120).read()
                fn = os.path.join(outdir, f"{name}.webp"); open(fn, "wb").write(data)
                print("saved", fn, g.get("worker_name"), round(time.time() - t0), "s", flush=True)
            pending.pop(jid)
print("remaining", list(pending.values()))
