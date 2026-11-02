"""Add Mixkit tracks to audio/tracks.json with a fitted constant-tempo beat grid,
downbeat phase, section starts (energy jumps) and a 'drop' beat to cut the shop
reveal on.  usage: beatgrid.py CATALOG.json MP3DIR key=id [key=id ...]"""
import json, os, sys, warnings
import numpy as np, librosa
warnings.filterwarnings('ignore')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKS = os.path.join(ROOT, 'audio', 'tracks.json')
TERMS = ('Free for commercial and non-commercial projects; allowed in social media video posts and online '
         'marketing ads; no attribution required. Not allowed: standalone redistribution, remixing into '
         'music-only tracks, registering with rights-management (Content ID) services.')


def fit(path):
    y, sr = librosa.load(path, sr=22050, mono=True)
    oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=256)
    _, beats = librosa.beat.beat_track(onset_envelope=oenv, sr=sr, hop_length=256, tightness=200)
    b = librosa.frames_to_time(beats, sr=sr, hop_length=256)
    best = None
    for per0 in np.linspace(np.median(np.diff(b)) * 0.99, np.median(np.diff(b)) * 1.01, 41):
        t0, per = b[0], per0
        for _ in range(6):
            idx = np.round((b - t0) / per)
            r = b - (t0 + idx * per)
            keep = np.abs(r) < 0.05
            if keep.sum() < 10:
                break
            A = np.vstack([np.ones(keep.sum()), idx[keep]]).T
            (t0, per), *_ = np.linalg.lstsq(A, b[keep], rcond=None)
        r = b - (t0 + np.round((b - t0) / per) * per)
        score = (np.abs(r) < 0.03).sum()
        if best is None or score > best[0]:
            best = (score, t0, per)
    _, t0, per = best
    while t0 - per > 0:
        t0 -= per
    grid = t0 + per * np.arange(int((len(y) / sr - t0) / per) + 1)
    rms = librosa.feature.rms(y=y, hop_length=256)[0]
    tt = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=256)
    db = np.array([20 * np.log10(rms[np.searchsorted(tt, grid[i]):np.searchsorted(tt, grid[i + 1])].mean() + 1e-6)
                   for i in range(len(grid) - 1)])
    jumps = []
    for i in range(4, len(db) - 8):
        jumps.append((db[i:i + 4].mean() - db[i - 4:i].mean(), i))
    sel = []
    for j, i in sorted(jumps, reverse=True):
        if j < 2.5:
            break
        if all(abs(i - k) > 6 for k in sel):
            sel.append(i)
    phases = [i % 4 for i in sel] or [0]
    phase = max(set(phases), key=phases.count)
    sections = sorted(i for i in sel if i % 4 == phase)
    # drop: first section start leaving >= 8 beats before it and >= 48 beats after it
    cands = [i for i in sections if i >= 8 and len(grid) - i >= 48]
    if not cands:  # no clear jump: use the loudest 16-beat stretch's first downbeat
        loud = [(db[i:i + 16].mean(), i) for i in range(8, len(db) - 48) if i % 4 == phase]
        cands = [max(loud)[1]]
    return dict(tempo=round(60 / per, 3), beats=[round(float(x), 4) for x in grid], downbeat_phase=int(phase),
                sections=[int(i) for i in sections], drop=int(cands[0]), beat_db=[round(float(x), 1) for x in db])


def main():
    cat = {e['url'].split('/')[-1][:-4]: e for e in json.load(open(sys.argv[1]))}
    tracks = json.load(open(TRACKS))
    for spec in sys.argv[3:]:
        key, mid = spec.split('=')
        e = cat[mid]
        info = fit(os.path.join(sys.argv[2], mid + '.mp3'))
        tracks[key] = dict(title=e['name'], artist=e['artist'], genre=e['genre'], duration=e['dur'], url=e['url'],
                           source='https://mixkit.co/free-stock-music/', licence='Mixkit Stock Music Free License',
                           licence_url='https://mixkit.co/license/#musicFree', licence_terms=TERMS, **info)
        print(f"{key:22s} {e['name'][:24]:24s} {info['tempo']:7.2f} BPM  drop beat {info['drop']:3d} "
              f"({info['beats'][info['drop']]:.1f}s)  sections {info['sections'][:6]}")
    json.dump(tracks, open(TRACKS, 'w'), indent=1)


if __name__ == '__main__':
    main()
