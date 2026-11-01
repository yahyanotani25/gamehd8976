"""pxsheet.py W out.jpg N 'regex[!exclude]' ...  -> thumbnail sheet of top-N (by views) per query."""
import sys, io, re, concurrent.futures as cf, urllib.request, pandas as pd
from PIL import Image, ImageDraw, ImageFont
W, out, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
qs = sys.argv[4:]
UA = "ClaudeCode-video-edit/1.0 (+https://claude.ai/code)"
df = pd.read_parquet(W + "/dl/pexels_meta/pexels_400k.parquet")
df["id"] = df.video.str.extract(r"/video/(\d+)").astype(int)
df["t"] = df.title.str.replace(" · Free Stock Video", "", regex=False).str.replace("Free stock video of ", "", regex=False)
rows, seen = [], set()
for q in qs:
    inc, _, exc = q.partition("!")
    m = df.t.str.contains(inc, case=False, regex=True) & (df.duration >= 5)
    if exc:
        m &= ~df.t.str.contains(exc, case=False, regex=True)
    for _, x in df[m].sort_values("view_count", ascending=False).head(N).iterrows():
        if x.id not in seen:
            seen.add(x.id); rows.append(x)
def fetch(x):
    try:
        req = urllib.request.Request(x.thumbnail + "?auto=compress&cs=tinysrgb&w=400", headers={"User-Agent": UA})
        return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB")
    except Exception as e:
        return None
with cf.ThreadPoolExecutor(12) as ex:
    ims = list(ex.map(fetch, rows))
tw, th, cols = 384, 216, 5
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
fsm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
n = len(rows); R = (n + cols - 1) // cols
sheet = Image.new("RGB", (cols * (tw + 6), R * (th + 34)), "white")
d = ImageDraw.Draw(sheet)
for k, (x, im) in enumerate(zip(rows, ims)):
    X, Y = (k % cols) * (tw + 6), (k // cols) * (th + 34)
    if im is not None:
        im = im.resize((tw, int(im.height * tw / im.width)))
        im = im.crop((0, max(0, (im.height - th) // 2), tw, max(0, (im.height - th) // 2) + th))
        sheet.paste(im, (X + 3, Y + 3))
    d.rectangle([X + 3, Y + 3, X + 3 + 150, Y + 20], fill="black")
    d.text((X + 6, Y + 4), f"{x.id} {x.duration}s", fill="yellow", font=font)
    d.text((X + 3, Y + th + 5), x.t[:62], fill="black", font=fsm)
    d.text((X + 3, Y + th + 18), f"{int(x.view_count):,} views", fill="gray", font=fsm)
sheet.save(out, quality=82)
print(out, sheet.size, n)
