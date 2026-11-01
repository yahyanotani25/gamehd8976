"""pxdl.py outdir prefer(1080|4k) id [id...] -- find the CDN file name by probing, then download."""
import sys, os, subprocess, concurrent.futures as cf
UA = "ClaudeCode-video-edit/1.0 (+https://claude.ai/code)"
outdir, prefer, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
os.makedirs(outdir, exist_ok=True)
SIZES_1080 = ["hd_1920_1080", "hd_2048_1080", "hd_1920_1012", "hd_1920_1018", "hd_1920_1024", "hd_1920_1040", "hd_1920_1036", "hd_1920_960", "hd_1920_1008"]
SIZES_4K = ["uhd_3840_2160", "uhd_4096_2160", "uhd_2560_1440", "uhd_2732_1440", "uhd_3840_2026", "uhd_3840_2024"]
SIZES_LO = ["hd_1280_720", "hd_1366_720"]
FPS = ["25", "30", "24", "50", "60", "23", "29", "59", "48", "120"]
def probe(url):
    r = subprocess.run(["curl", "-sS", "-m", "20", "-A", UA, "-r", "0-0", "-o", "/dev/null", "-w", "%{http_code}", url], capture_output=True, text=True)
    return r.stdout.strip() in ("200", "206")
def find(i):
    order = (SIZES_4K + SIZES_1080) if prefer == "4k" else (SIZES_1080 + SIZES_4K)
    for s in order + SIZES_LO:
        for f in FPS:
            u = f"https://videos.pexels.com/video-files/{i}/{i}-{s}_{f}fps.mp4"
            if probe(u):
                return u, s, f
    return None, None, None
def get(i):
    dst = os.path.join(outdir, f"px{i}.mp4")
    if os.path.exists(dst) and os.path.getsize(dst) > 100000:
        return i, "exists", dst
    u, s, f = find(i)
    if not u:
        return i, "NOTFOUND", None
    r = subprocess.run(["curl", "-sS", "-L", "-m", "900", "--retry", "3", "-A", UA, "-o", dst, u], capture_output=True, text=True)
    return i, f"{s}_{f}fps rc={r.returncode} {os.path.getsize(dst) if os.path.exists(dst) else 0}", dst
with cf.ThreadPoolExecutor(6) as ex:
    for i, status, dst in ex.map(get, ids):
        print(i, status, flush=True)
