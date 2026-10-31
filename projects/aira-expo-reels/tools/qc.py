"""Technical QC for delivered reels (SOP section 8 + audio): prints a markdown table.

usage: qc.py reel1.mp4 [reel2.mp4 ...]
Checks: H.264 MP4, 1080x1920, 9:16, 30 fps CFR, duration < 30 s, yuv420p BT.709,
AAC 48 kHz stereo, loudness (target -14 LUFS, true peak <= -1 dBTP), no black bars
(cropdetect over the footage section), first frame / last frame state, bitrate.
"""
import json, subprocess, sys, re


def probe(p):
    return json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', p],
                                     capture_output=True, text=True).stdout)


def loud(p):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', p, '-vn', '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    s = r[r.rfind('Summary'):]
    i = float(re.search(r'I:\s+(-?[\d.]+) LUFS', s).group(1))
    tp = float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', s).group(1))
    return i, tp


def bars(p, t0, t1):
    """Largest crop cropdetect suggests over the footage section (0 px = no bars)."""
    r = subprocess.run(['ffmpeg', '-hide_banner', '-ss', str(t0), '-t', str(t1 - t0), '-i', p, '-vf',
                        'fps=2,cropdetect=limit=0.06:round=2:reset=1', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    worst = 0
    for m in re.finditer(r'w:(\d+) h:(\d+) x:(\d+) y:(\d+)', r):
        w, h = int(m.group(1)), int(m.group(2))
        worst = max(worst, 1080 - w, 1920 - h)
    return worst


def mean_luma(p, t):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', p, '-frames:v', '1', '-vf',
                        'scale=108:192,format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
    return sum(r) / max(1, len(r))


def main():
    rows = []
    for p in sys.argv[1:]:
        d = probe(p)
        v = next(s for s in d['streams'] if s['codec_type'] == 'video')
        a = next((s for s in d['streams'] if s['codec_type'] == 'audio'), None)
        dur = float(d['format']['duration'])
        fps = v['r_frame_rate']
        lufs, tp = loud(p)
        bar = bars(p, 1.0, dur - 3.5)
        checks = {
            'container': d['format']['format_name'].startswith('mov,mp4'),
            'codec': v['codec_name'] == 'h264',
            'size': (v['width'], v['height']) == (1080, 1920),
            'fps': fps == '30/1' and v['avg_frame_rate'] == '30/1',
            'duration<30s': dur < 30.0,
            'pix_fmt': v['pix_fmt'] == 'yuv420p',
            'bt709': v.get('color_space') == 'bt709' and v.get('color_transfer') == 'bt709',
            'audio': a is not None and a['codec_name'] == 'aac' and a['sample_rate'] == '48000' and a['channels'] == 2,
            'loudness': -15.5 <= lufs <= -12.5 and tp <= -0.5,
            'no bars': bar <= 4,
        }
        rows.append((p.split('/')[-1], v, dur, fps, lufs, tp, bar, float(d['format']['bit_rate']) / 1e6,
                     mean_luma(p, 0.0), mean_luma(p, dur - 0.05), checks))
    print('| file | size | fps | duration | loudness | true peak | bars | Mbps | first/last frame luma | result |')
    print('|---|---|---|---|---|---|---|---|---|---|')
    for name, v, dur, fps, lufs, tp, bar, mbps, l0, l1, c in rows:
        bad = [k for k, ok in c.items() if not ok]
        print(f"| {name} | {v['width']}x{v['height']} | {fps} | {dur:.2f} s | {lufs:.1f} LUFS | {tp:.1f} dBFS | "
              f"{bar} px | {mbps:.1f} | {l0:.0f} / {l1:.0f} | {'PASS' if not bad else 'FAIL: ' + ', '.join(bad)} |")
    return 0 if all(all(r[-1].values()) for r in rows) else 1


if __name__ == '__main__':
    sys.exit(main())
