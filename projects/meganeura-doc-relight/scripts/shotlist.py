"""Write the change log: every replaced shot with timecodes, narration and the new source.

usage: shotlist.py W out_dir      -> out_dir/shotlist.csv and out_dir/shotlist.md
"""
import sys, os, json, csv, glob
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from slots import SLOTS
from plan import PLAN, AI

W, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
tr = json.load(open(W + "/work/transcript.json"))
words = [w for s in tr["segments"] for w in s["words"]]
prompts = {}
for p in glob.glob(W + "/work/ai_jobs*.json"):
    for j in json.load(open(p)):
        prompts[j["name"]] = (j["model"], j["prompt"])
try:
    import pandas as pd
    df = pd.read_parquet(W + "/dl/pexels_meta/pexels_400k.parquet")
    df["id"] = df.video.str.extract(r"/video/(\d+)").astype(int)
    titles = dict(zip(df.id, df.title.str.replace(" · Free Stock Video", "", regex=False).str.replace("Free stock video of ", "", regex=False)))
except Exception:
    titles = {}

TITLE_TEXT = {"S04": "Chapter 1 title card", "S23": "Chapter 2 title card", "S29": "Chapter 3 title card",
              "S40": "Chapter 5 title card", "S48": "Chapter 6 title card", "S56": "Chapter 7 title card"}


def tc(f):
    s = f / 25.0
    return f"{int(s // 60)}:{s % 60:05.2f}"


CAPTION = {
    "emerge_flux": "Giant griffinfly in golden sunlight among tree ferns",
    "emerge_icbinp": "Giant griffinfly emerging from the fern canopy against the sun",
    "flyover_flux": "Giant griffinfly flying overhead, blue sky and ferns",
    "flyover_icbinp": "Giant griffinfly in flight, seen from below through tree ferns",
    "fossil_flux": "Fossil griffinfly wings in stone, close-up",
    "fossil_icbinp": "Fossil griffinfly impression in grey stone",
    "recon_flux": "Sunlit Carboniferous swamp pool with ferns and a griffinfly",
    "recon_icbinp": "Bright swamp forest reflected in still water",
    "scaletrees_flux": "Forest of scale-barked trees (Lepidodendron-like) in sunlight",
    "swoop_flux": "Giant griffinfly closing in on a small insect against the sun",
}
MODEL = {"ICBINP XL": "ICBINP XL", "Flux.1-Schnell fp8 (Compact)": "FLUX.1-schnell"}


def source_desc(seg):
    src = seg["src"]
    if src.startswith("ai:"):
        key = src[3:]
        name = os.path.basename(AI[key]).rsplit(".", 1)[0]
        model, prompt = prompts.get(name, ("?", "?"))
        return f"AI still ({MODEL.get(model, model)})", CAPTION.get(key, prompt), ""
    pid = int(src[2:].split("_")[0])
    t = titles.get(pid, "")
    return f"Pexels video {pid}", t.strip(), f"https://www.pexels.com/video/{pid}/"


rows = []
for s in SLOTS:
    t0, t1 = s["f0"] / 25, (s["f1"] + 1) / 25
    narr = " ".join(w["w"].strip() for w in words if w["e"] > t0 + 0.05 and w["s"] < t1 - 0.05)
    segs = PLAN.get(s["id"], [])
    if s["kind"] == "regrade":
        what, detail, url = "Original Earth shot, background lifted", "the dimming under the title was undone; title text untouched", ""
        srcs = [(what, detail, url)]
    else:
        srcs = [source_desc(g) for g in segs]
    extra = []
    if s.get("ovl"):
        extra.append("original title/label text kept on top" if not s["ovl"].startswith("T") else "original title animation kept on top")
    rows.append(dict(slot=s["id"], client_clip=s["clip"], start=tc(s["f0"]), end=tc(s["f1"] + 1),
                     seconds=round(t1 - t0, 2), narration=narr, kind=TITLE_TEXT.get(s["id"], "shot"),
                     new_visual=" + ".join(a for a, b, c in srcs), description=" / ".join(b for a, b, c in srcs),
                     link=" ".join(c for a, b, c in srcs if c), notes="; ".join(extra)))

with open(OUT + "/shotlist.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

with open(OUT + "/shotlist.md", "w") as f:
    f.write("| Slot | Client clip | Original time | Narration | New visual | Source |\n|---|---|---|---|---|---|\n")
    for r in rows:
        narr = r["narration"].replace("|", "/") or "(music)"
        desc = r["description"].replace("|", "/")
        src = f"[{r['new_visual']}]({r['link']})" if r["link"] and " + " not in r["new_visual"] else r["new_visual"]
        if r["link"] and " + " in r["new_visual"]:
            src = r["new_visual"] + " — " + ", ".join(r["link"].split())
        kind = f" **{r['kind']}**" if r["kind"] != "shot" else ""
        note = f" ({r['notes']})" if r["notes"] else ""
        f.write(f"| {r['slot']}{kind} | {r['client_clip']} | {r['start']}–{r['end']} | {narr} | {desc}{note} | {src} |\n")
print(len(rows), "rows ->", OUT)
