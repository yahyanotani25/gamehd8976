#!/usr/bin/env python3
"""Download Commons thumbnails for a list of file titles and build a numbered preview sheet.
Usage: wm_preview.py titles.txt out_dir [thumb_width]
titles.txt: one 'File:Title.ext' per line (lines starting with # ignored)."""
import hashlib, os, sys, time, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFont
UA = "ClaudeCode-AssetFetcher/1.0 (https://claude.com/claude-code; documentary asset research) python-urllib/3.13"

def wm_url(title, width=None):
    name = title.split(":", 1)[1].replace(" ", "_")
    h = hashlib.md5(name.encode()).hexdigest()
    q = urllib.parse.quote(name)
    if width is None:
        return f"https://upload.wikimedia.org/wikipedia/commons/{h[0]}/{h[:2]}/{q}"
    ext = "" if name.lower().endswith((".jpg", ".jpeg", ".png")) else ".jpg"
    pre = "lossy-page1-" if name.lower().endswith((".tif", ".tiff")) else ""
    return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{h[0]}/{h[:2]}/{q}/{pre}{width}px-{q}{ext}"

def fetch(url, dest, tries=8):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
                while True:
                    b = r.read(1 << 16)
                    if not b: break
                    f.write(b)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 429:
                ra = int(e.headers.get("retry-after", "15") or 15)
                sys.stderr.write(f"429 {url[-60:]} wait {ra+2}\n")
                if i < tries - 1: time.sleep(min(ra, 120) + 2)
                continue
            sys.stderr.write(f"HTTP {e.code} {url}\n"); return False
        except Exception as e:
            sys.stderr.write(f"ERR {e} {url}\n"); time.sleep(3)
    return False

def sheet(items, out, cols=5, tw=330, th=230):
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13) if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf") else ImageFont.load_default()
    rows = (len(items) + cols - 1) // cols
    S = Image.new("RGB", (cols * (tw + 10) + 10, rows * (th + 40) + 10), (30, 30, 30))
    d = ImageDraw.Draw(S)
    for k, (label, path) in enumerate(items):
        x = 10 + (k % cols) * (tw + 10); y = 10 + (k // cols) * (th + 40)
        try:
            im = Image.open(path).convert("RGB"); im.thumbnail((tw, th))
            S.paste(im, (x + (tw - im.width) // 2, y + (th - im.height) // 2))
        except Exception:
            d.text((x + 10, y + 10), "unreadable", fill=(255, 80, 80), font=font)
        d.text((x, y + th + 3), label[:46], fill=(255, 255, 255), font=font)
        d.text((x, y + th + 19), label[46:92], fill=(200, 200, 200), font=font)
    S.save(out, quality=85)

if __name__ == "__main__":
    titles = [l.strip() for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]
    out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    w = int(sys.argv[3]) if len(sys.argv) > 3 else 330
    items = []
    for i, t in enumerate(titles):
        dest = os.path.join(out, f"{i:03d}.jpg")
        if not os.path.exists(dest) or os.path.getsize(dest) < 1000:
            # upload.wikimedia.org is often 429 from this shared IP; the commons app-server thumb.php is not
            name = urllib.parse.quote(t.split(":", 1)[1].replace(" ", "_"))
            fetch(f"https://commons.wikimedia.org/w/thumb.php?f={name}&w={w}", dest, tries=3) or fetch(wm_url(t, w), dest, tries=2)
            time.sleep(1)
        items.append((f"{i:03d} {t[5:]}", dest))
    for s in range(0, len(items), 30):
        sheet(items[s:s+30], os.path.join(out, f"_sheet{s//30}.jpg"))
    print("done", len(items))
