"""Prepare downloaded store-event originals for editing:
  * a 640 px review proxy (source frame rate) + <proxy>.src.json with the original's geometry
  * a contact sheet per clip (one frame per second, time-stamped) for picking moments
  * a white-balance estimate per clip -> WB json {clip: [r, g, b]} (gamma-space gains for
    ffmpeg colorchannelmixer, applied before the look LUT; see wb_filter)

The store was lit by very warm LEDs on gold shelves, so the footage reads orange and the
garments lose their colour. The estimate pulls each clip part of the way (STRENGTH) toward
a warm-neutral balance, keeping the evening warmth, and keeps the overall brightness.

  python3 tools/prep_event.py RAW_DIR PROXY_DIR SHEET_DIR WB_JSON
  python3 tools/prep_event.py --images WB_JSON img1.jpg ...   (estimate from stills, key = file stem)
"""
import glob, json, os, subprocess, sys
import numpy as np
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'engine'))

TARGET_RG, TARGET_BG = 1.12, 0.82   # warm-neutral (linear R/G, B/G)
STRENGTH = 0.6
GR, GB = (0.55, 1.3), (0.8, 2.6)     # linear gain limits


def wb_gains(frames_bgr):
    """gamma-space (r, g, b) gains from a list of 8-bit BGR frames. Strength backs off
    (from STRENGTH) while the bright areas - white walls, ceiling, lit signage - would come
    out cooler than neutral, so an overexposed wall never turns blue."""
    acc, hi = np.zeros(3), np.zeros(3)
    for img in frames_bgr:
        lin = (img.astype(np.float32) / 255.0) ** 2.2
        y = lin.mean(2)
        m = (y > 0.02) & (y < 0.8) & (lin.max(2) < 0.95)
        if m.sum() < 500:
            continue
        acc += [lin[..., c][m].mean() for c in range(3)]
        mb = y > 0.35
        if mb.sum() > 200:
            hi += [lin[..., c][mb].mean() for c in range(3)]
    b, g, r = acc
    if g <= 0:
        return [1.0, 1.0, 1.0]
    for k in np.linspace(STRENGTH, 0.0, 13):
        gr = float(np.clip((TARGET_RG / (r / g)) ** k, *GR))
        gb = float(np.clip((TARGET_BG / (b / g)) ** k, *GB))
        if hi[1] <= 0:
            break
        hb, hg, hr = hi
        # brights after the gains, in display terms (clipped at 1)
        if min(1.0, hb * gb) / min(1.0, hg) <= 0.97 and min(1.0, hr * gr) / min(1.0, hg) >= 0.98:
            break
    y0 = 0.2126 * r + 0.7152 * g + 0.0722 * b
    y1 = 0.2126 * r * gr + 0.7152 * g + 0.0722 * b * gb
    n = y0 / y1
    return [round((gr * n) ** (1 / 2.2), 3), round(n ** (1 / 2.2), 3), round((gb * n) ** (1 / 2.2), 3)]


def wb_filter(gains):
    r, g, b = gains
    return f'colorchannelmixer=rr={r}:gg={g}:bb={b}'


def probe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                        'stream=width,height,avg_frame_rate:format=duration', '-of', 'json', path],
                       capture_output=True, text=True)
    j = json.loads(r.stdout)
    st = j['streams'][0]
    num, den = st['avg_frame_rate'].split('/')
    return st['width'], st['height'], float(num) / float(den or 1), float(j['format']['duration'])


def frames(path, every=1.0):
    w, h, fps, dur = probe(path)
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'fps=1/{every}', '-f', 'rawvideo',
                          '-pix_fmt', 'bgr24', '-'], capture_output=True).stdout
    n = len(raw) // (w * h * 3)
    return [np.frombuffer(raw[i * w * h * 3:(i + 1) * w * h * 3], np.uint8).reshape(h, w, 3) for i in range(n)]


def sheet(imgs, labels, cols=8, tile=240):
    tiles = []
    for im, lab in zip(imgs, labels):
        h, w = im.shape[:2]
        s = tile / max(h, w)
        im = cv2.resize(im, (int(w * s), int(h * s)))
        t = np.zeros((tile + 20, tile, 3), np.uint8)
        y, x = (tile - im.shape[0]) // 2, (tile - im.shape[1]) // 2
        t[y:y + im.shape[0], x:x + im.shape[1]] = im
        cv2.putText(t, lab, (4, tile + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        tiles.append(t)
    while len(tiles) % cols:
        tiles.append(np.zeros_like(tiles[0]))
    return np.vstack([np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)])


def main():
    if sys.argv[1] == '--images':
        out, wb = sys.argv[2], {}
        for p in sys.argv[3:]:
            wb[os.path.splitext(os.path.basename(p))[0]] = wb_gains([cv2.imread(p)])
        json.dump(wb, open(out, 'w'), indent=0, sort_keys=True)
        return
    raw, prx, sheets, wbj = sys.argv[1:5]
    os.environ['AIRA_RAW'] = raw
    import reelkit as rk
    os.makedirs(prx, exist_ok=True)
    os.makedirs(sheets, exist_ok=True)
    wb = json.load(open(wbj)) if os.path.exists(wbj) else {}
    for src in sorted(glob.glob(os.path.join(raw, '*.MP4'))):
        clip = os.path.splitext(os.path.basename(src))[0]
        p = os.path.join(prx, clip + '.mp4')
        if not os.path.exists(p):
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf',
                            "scale='if(gt(iw,ih),640,-2)':'if(gt(iw,ih),-2,640)'", '-an', '-c:v', 'libx264',
                            '-preset', 'veryfast', '-crf', '23', '-g', '10', p], check=True)
        info = rk.source_info(clip)
        json.dump(dict(w=info['w'], h=info['h'], fps=info['fps'], rot=info['rot']), open(p + '.src.json', 'w'))
        sp = os.path.join(sheets, clip + '.jpg')
        if clip not in wb or not os.path.exists(sp):
            fr = frames(p)
            wb[clip] = wb_gains(fr[::max(1, len(fr) // 8)])
            cv2.imwrite(sp, sheet(fr, [f'{clip} {i}s' for i in range(len(fr))]), [cv2.IMWRITE_JPEG_QUALITY, 80])
        print(clip, f"{info['w']}x{info['h']} {info['fps']:.2f}fps", wb[clip], flush=True)
    if wb:  # nothing on disk yet: leave no empty file behind
        json.dump(wb, open(wbj, 'w'), indent=0, sort_keys=True)


if __name__ == '__main__':
    main()
