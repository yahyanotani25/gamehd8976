"""Shared helpers for the AIRA reels: beat-synced cut lists, text styles, build entry point."""
import os, sys, json, argparse
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'engine'))
import reelkit as rk  # noqa: E402
import audio  # noqa: E402

FPS = rk.FPS
OUT = os.path.join(ROOT, 'out')


def have(clip, t_end=0.0):
    """Is full-resolution footage for `clip` on disk up to stored time t_end? A prefix
    rebuild (tools/rebuild_prefix.py) only covers the first seconds of a clip."""
    for d in rk.raw_dirs():
        for name in (clip + '.MP4', 'keep_' + clip + '.MP4'):
            if os.path.exists(os.path.join(d, name)):
                meta = os.path.join(d, clip + '.prefix.json')
                if os.path.exists(meta):
                    return json.load(open(meta))['seconds'] >= t_end
                return True
    return False


def pick(primary, fallback, clip, t_end):
    """Shot factory: `primary` when its footage is on disk, else `fallback`
    (Google Drive's download quota kept some originals out of reach)."""
    return primary if have(clip, t_end) else fallback


def cut_frames(track, b0, counts):
    """Frame index of every cut when shot k lasts counts[k] beats, music starting at beat b0."""
    beats = audio.beat_times(track)
    t0 = beats[b0]
    idx = np.cumsum([0] + list(counts))
    return [int(round((beats[b0 + i] - t0) * FPS)) for i in idx], t0


def durations(track, b0, counts):
    cuts, t0 = cut_frames(track, b0, counts)
    return [(b - a) / FPS for a, b in zip(cuts, cuts[1:])], t0, [c / FPS for c in cuts]


# ------------------------------------------------------------------ text styles
def _shadowed_logo(width):
    a = rk.logo_layer(width).astype(np.float32) / 255.0
    pad = 40
    a = np.pad(a, pad)
    sh = cv2.GaussianBlur(a, (0, 0), 9) * 0.55
    al = a + sh * (1 - a)
    rgb = np.where(al[..., None] > 1e-4, a[..., None] * 255.0 / np.maximum(al[..., None], 1e-4), 0)
    return np.dstack([rgb, rgb, rgb, al * 255]).astype(np.float32)


def stack(layers, gap=0):
    w = max(l.shape[1] for l in layers)
    h = sum(l.shape[0] for l in layers) + gap * (len(layers) - 1)
    out = np.zeros((h, w, 4), np.float32)
    y = 0
    for l in layers:
        x = (w - l.shape[1]) // 2
        out[y:y + l.shape[0], x:x + l.shape[1]] = l
        y += l.shape[0] + gap
    return out


def hook(lines, sub=None, size=70, logo_width=None):
    """Hook headline: caps, generous tracking; optional official logo under the words."""
    parts = [rk.text_layer(lines, size=size, weight=500, tracking=0.20, upper=True, shadow=0.6, pad=36)]
    if logo_width:
        parts.append(_shadowed_logo(logo_width))
    if sub:
        parts.append(rk.text_layer([sub], size=29, weight=420, tracking=0.26, upper=True, shadow=0.6, pad=30))
    return stack(parts, gap=-34)


def label(text, size=34):
    return rk.text_layer([text], size=size, weight=500, tracking=0.32, upper=True, shadow=0.65, pad=30)


def tip(lines, size=44):
    head = rk.text_layer(['Styling tip'], size=27, weight=520, tracking=0.34, upper=True, shadow=0.65, pad=28)
    body = rk.text_layer(lines, size=size, weight=400, tracking=0.02, shadow=0.7, pad=30, line_gap=1.3, scrim=0.22)
    return stack([head, body], gap=-40)


def logo_reveal_audio(cuts, hit_db=-3.0):
    """Reference logo reveal: hit (the owner's whoosh, peak 0.89 s in) on the first
    flare frame; music fades out over 0.2 s, gone as the card appears (cut + 10 frames)."""
    flare = cuts[-1] - 7 / FPS
    card = cuts[-1] + 10 / FPS
    return dict(music_out=(card, 0.2), sfx=[('whoosh.mp3', flare, 0.89, hit_db)])


def build(reel, track, music_start, music_out=None, sfx=(), name=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--preview', action='store_true', help='render from the 640x360 proxies at 1/2 size')
    ap.add_argument('--frames', default=None, help='a:b frame range (preview)')
    ap.add_argument('--table', action='store_true')
    ap.add_argument('--stills', default=None, help='comma-separated times: full-size PNG stills (from proxies)')
    ap.add_argument('--hires', action='store_true', help='stills from the original footage')
    ap.add_argument('--remux-audio', action='store_true', help='re-mix the audio into an already rendered reel')
    args = ap.parse_args()
    if args.remux_audio:
        import subprocess
        reel.layout()
        total = reel.total / FPS
        name = name or reel.name
        wav = os.path.join(OUT, f'{name}_mix.wav')
        audio.mix(wav, track, music_start, total, music_out=music_out, sfx=sfx)
        mp4 = os.path.join(OUT, f'{name}.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp4, '-i', wav, '-map', '0:v:0', '-map', '1:a:0',
                        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-shortest', '-movflags',
                        '+faststart', mp4 + '.tmp.mp4'], check=True)
        os.replace(mp4 + '.tmp.mp4', mp4)
        print('remuxed audio into', mp4)
        return mp4
    if args.stills:
        if not args.hires:
            os.environ.setdefault('AIRA_PROXY_DIR', os.path.join(ROOT, 'proxy'))
        import subprocess
        for t in [float(x) for x in args.stills.split(',')]:
            f = int(round(t * FPS))
            tmp = os.path.join(OUT, f'{reel.name}_still.mp4')
            os.makedirs(OUT, exist_ok=True)
            reel.render(tmp, frames=range(f, f + 1), crf=12)
            png = os.path.join(OUT, f'{reel.name}_t{t:05.2f}.png')
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-frames:v', '1', png], check=True)
            print('still', png)
        return
    os.makedirs(OUT, exist_ok=True)
    name = name or reel.name
    reel.layout()
    total = reel.total / FPS
    if args.table:
        for r in reel.describe():
            print(r)
        print('total', total)
        return
    wav = os.path.join(OUT, f'{name}_mix.wav')
    audio.mix(wav, track, music_start, total, music_out=music_out, sfx=sfx)
    if args.preview:
        os.environ.setdefault('AIRA_PROXY_DIR', os.path.join(ROOT, 'proxy'))
        fr = None
        if args.frames:
            a, b = map(int, args.frames.split(':'))
            fr = range(a, b)
        out = os.path.join(OUT, f'{name}_preview.mp4')
        reel.render(out, audio=wav if fr is None else None, preview_scale=0.5, frames=fr)
    else:
        out = os.path.join(OUT, f'{name}.mp4')
        reel.render(out, audio=wav)
    print('wrote', out, f'{total:.2f}s')
    return out
