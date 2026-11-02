"""Text-free event reels in the client-approved R3/R4 style, generated from a shot library.

Flow of every reel (client brief): outside -> into the venue -> AIRA logo + shop ->
people inside the shop -> products (mixed with people) -> AIRA wall -> flare /
eclipse -> AIRA logo card -> fade to black. No on-screen text at all.

  python3 reels/event_reels.py --event 1 --plan            # print all 15 shot plans
  python3 reels/event_reels.py --event 1 --reel 3 --preview
  python3 reels/event_reels.py --event 1 --reel 3          # final -> out/AIRA_E1_R03.mp4
"""
import argparse, collections, json, os, random, subprocess, sys
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import rk, audio, FPS, OUT, ROOT, logo_reveal_audio  # noqa: E402
import library as L  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import letters as LT  # noqa: E402

EVENTS = {
    1: dict(name='E1', lib=L, proxy=os.path.join(ROOT, 'proxy'), proxy_scale=3.0,
            tracks=['hazy_after_hours', 'cat_walk', 'feast_from_the_east', 'house_vibez', 'new_york',
                    'talent_in_the_air', 'house_one', 'pop_08', 'deep_house', 'loner', 'electro_dreams',
                    'see_line_funk', 'what_about_action', 'urban_grooves', 'rising_forest']),
}
N_REELS = 15
CACHE = os.path.join(ROOT, 'reels', 'autoframe_cache.json')

# ---------------------------------------------------------------- auto framing
_face = [cv2.CascadeClassifier(cv2.data.haarcascades + n) for n in
         ('haarcascade_frontalface_default.xml', 'haarcascade_profileface.xml')]


def proxy_frame(ev, clip, t):
    p = os.path.join(ev['proxy'], clip + '.mp4')
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.2f}', '-i', p, '-frames:v', '1', '-f', 'rawvideo',
                          '-pix_fmt', 'bgr24', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(360, 640, 3) if len(raw) == 640 * 360 * 3 else None


def autoframe(ev, clip, t):
    """Horizontal centre (source px) of the main subject: the largest face, else frame centre."""
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    key = f"{ev['name']}:{clip}@{t}"
    if key in cache:
        return cache[key]
    xs = []
    for dt in (0.1, 0.5):
        img = proxy_frame(ev, clip, t + dt)
        if img is None:
            continue
        g = cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        faces = []
        for c in _face:
            faces += [tuple(f) for f in c.detectMultiScale(g, 1.1, 6, minSize=(26, 26))]
        if faces:
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            xs.append((x + w / 2) * ev['proxy_scale'])
    cx = float(np.median(xs)) if xs else 960.0
    cache[key] = cx
    json.dump(cache, open(CACHE, 'w'), indent=0)
    return cx


def wall_letters(ev, clip, t):
    """(cx, flare_y) for an end shot: centre of the AIRA wall letters (source px) and
    their row in the output frame at z=1; None if the word isn't found or won't fit."""
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    key = f"{ev['name']}:letters:{clip}@{t}"
    if key not in cache:
        img = proxy_frame(ev, clip, t + 0.4)
        r = LT.letters(img) if img is not None else None
        ok = r is not None and r['mass'] > 300
        cache[key] = [(r['x0'] + r['x1']) / 2, (r['y'] - 540) * rk.H / rk.SH + rk.H / 2] if ok else None
        json.dump(cache, open(CACHE, 'w'), indent=0)
    return cache[key]


def flare_row(ev, clip, t, cx, z):
    """Output-frame row of the AIRA wall letters (bright, unsaturated) for the end flare."""
    img = proxy_frame(ev, clip, t)
    if img is None:
        return 620
    big = cv2.resize(img, (1920, 1080))
    out = cv2.warpAffine(big, rk.reframe_matrix(cx, 540, z, 0), (rk.W, rk.H))
    hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV)
    white = ((hsv[..., 2] > 200) & (hsv[..., 1] < 60)).astype(np.float32)
    rows = white[:int(rk.H * 0.6)].sum(1)
    rows[:int(rk.H * 0.08)] = 0
    band = np.convolve(rows, np.ones(60), 'same')
    return int(np.argmax(band)) if band.max() > 2000 else 620


# ---------------------------------------------------------------- planning
SEGMENTS = [('black', 1), ('ext', 3), ('hall', 3), ('logo', 2), ('shop', 2), ('people', 3), ('people', 2),
            ('product', 2), ('people', 3), ('product', 2), ('product', 2), ('people', 2), ('product', 2)]
EXTRA = [('people', 2), ('product', 2), ('people', 3), ('product', 2)]
POOLS = dict(ext='EXT', hall='HALL', logo='LOGO', shop='SHOP', people='PEOPLE', product='PRODUCT', end='END')
SPEED = dict(ext=0.5, hall=0.5, logo=0.5, shop=0.5, people=0.5, product=0.35, end=0.5)


def plan_all(ev):
    lib = ev['lib']
    used = collections.Counter()
    plans = []
    for r in range(N_REELS):
        rng = random.Random(1000 + r)
        track = audio.TRACKS[ev['tracks'][r]]
        per = 60.0 / track['tempo']
        segs = list(SEGMENTS)
        k = 0
        while (sum(b for _, b in segs) + 3) * per < 18.0:
            segs.append(EXTRA[k % len(EXTRA)])
            k += 1
        segs.append(('end', 3))
        clips_in_reel, shots, looks = set(), [], 0
        for cat, beats in segs:
            if cat == 'black':
                shots.append(dict(cat=cat, beats=beats))
                continue
            pool = getattr(lib, POOLS[cat])
            cands = [m for m in pool if m[0] not in clips_in_reel]
            need_look = cat == 'people' and looks < 2
            if need_look and any(m[2].get('look') for m in cands):
                cands = [m for m in cands if m[2].get('look')]
            low = min(used[(m[0], m[1])] for m in cands)
            cands = [m for m in cands if used[(m[0], m[1])] == low]
            m = rng.choice(cands)
            used[(m[0], m[1])] += 1
            clips_in_reel.add(m[0])
            looks += 1 if m[2].get('look') else 0
            shots.append(dict(cat=cat, beats=beats, clip=m[0], t=m[1], opt=m[2]))
        plans.append(dict(reel=r + 1, track=ev['tracks'][r], shots=shots, rng_seed=2000 + r))
    return plans


def build_reel(ev, plan):
    rng = random.Random(plan['rng_seed'])
    T, S = rk.Tr, rk.Shot
    track = plan['track']
    beats = audio.beat_times(track)
    drop = audio.TRACKS[track]['drop']
    b0 = max(0, drop - 7)  # the drop lands on the cut to the AIRA logo (after black 1 + ext 3 + hall 3)
    counts = [s['beats'] for s in plan['shots']]
    idx = np.cumsum([0] + counts)
    t0 = beats[b0]
    cuts = [round((beats[b0 + i] - t0) * FPS) / FPS for i in idx]
    durs = [b - a for a, b in zip(cuts, cuts[1:])]
    n = len(plan['shots'])
    # transitions
    trs = []
    bw_at = rng.choice([i for i, s in enumerate(plan['shots']) if s['cat'] == 'product'])
    whip_at = set(rng.sample([i for i, s in enumerate(plan['shots']) if s['cat'] in ('people', 'product')
                              and i < n - 2], 2))
    for i, s in enumerate(plan['shots']):
        nxt = plan['shots'][i + 1]['cat'] if i + 1 < n else None
        if s['cat'] == 'black':
            trs.append(T('gate', 20))
        elif s['cat'] == 'ext':
            trs.append(T(rng.choice(['burn', 'card', 'blur']), 22 if rng.random() < 0.5 else 14,
                         seed=rng.randint(1, 99)))
        elif s['cat'] == 'hall':
            trs.append(T(rng.choice(['flash', 'whip', 'zoom']), 8, dir=rng.choice(['left', 'right'])))
        elif s['cat'] == 'logo':
            trs.append(T(rng.choice(['cut', 'blur']), 10))
        elif s['cat'] == 'end':
            trs.append(None)
        elif i in whip_at:
            trs.append(T('whip', 8, dir=rng.choice(['left', 'right', 'up'])))
        elif nxt == 'end':
            trs.append(T(rng.choice(['cut', 'flash']), 6))
        else:
            trs.append(T('cut'))
    reel = rk.Reel(f"AIRA_{ev['name']}_R{plan['reel']:02d}")
    end_info = None
    for i, (s, d) in enumerate(zip(plan['shots'], durs)):
        if s['cat'] == 'black':
            reel.add(rk.Black(d), trs[i])
            continue
        o = s['opt']
        cx = o.get('cx') or (autoframe(ev, s['clip'], s['t']) if s['cat'] in ('people', 'ext') else 960.0)
        cy, z = o.get('cy', 540), o.get('z', 1.0)
        wl = wall_letters(ev, s['clip'], s['t']) if s['cat'] == 'end' else None
        sp = o.get('sp', SPEED[s['cat']])
        if 'pan' in o:
            frame = [(0, (o['pan'][0], cy, 1.05, 0)), (1, (o['pan'][1], cy, 1.05, 0))]
        else:
            mv = 'push' if s['cat'] == 'end' else rng.choice(['push', 'drift', 'drift'])
            dx = rng.choice([-1, 1]) * rng.randint(20, 50)
            frame = ([(0, (cx, cy, z, 0)), (1, (cx, cy, z * 1.05, 0))] if mv == 'push' else
                     [(0, (cx - dx / 2, cy, z, 0)), (1, (cx + dx / 2, cy, z * 1.02, 0))])
        fx = []
        if i == bw_at:
            fx.append(('bw', d * 0.45, d * 0.45 + 5 / FPS))
        if o.get('echo'):
            fx.append(('echo', d * 0.4, d * 0.4 + 4 / FPS))
        note = f"{s['cat']}: {s['clip']}@{s['t']}" + (' (look)' if o.get('look') else '')
        tr = trs[i]
        if s['cat'] == 'end':
            end_info = (s['clip'], s['t'], cx, z)
            tr = T('eclipse', 17, flare_y=wl[1] if wl else flare_row(ev, s['clip'], s['t'] + d * sp * 0.9, cx, z))
        reel.add(S(s['clip'], s['t'], d, speed=sp, frame=frame, fx=fx, note=note), tr)
    reel.add(rk.Card(2.9))
    return reel, t0, cuts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--event', type=int, default=1)
    ap.add_argument('--reel', type=int)
    ap.add_argument('--plan', action='store_true')
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--needs', action='store_true', help='print original clips + stored seconds needed')
    a = ap.parse_args()
    ev = EVENTS[a.event]
    plans = plan_all(ev)
    if a.plan or a.needs:
        need = collections.defaultdict(float)
        for p in plans:
            if a.plan:
                print(f"R{p['reel']:02d} {p['track']}: " + ' | '.join(
                    s['cat'][:4] + (':' + s['clip'][1:] + '@' + str(s['t']) if 'clip' in s else '') for s in p['shots']))
            for s in p['shots']:
                if 'clip' in s:
                    sp = s['opt'].get('sp', SPEED[s['cat']])
                    need[s['clip']] = max(need[s['clip']], s['t'] + 3.0 * sp + 0.8)
        if a.needs:
            print(' '.join(f'{c}:{v:.1f}' for c, v in sorted(need.items())))
        return
    todo = [a.reel] if a.reel else range(1, N_REELS + 1)
    os.makedirs(OUT, exist_ok=True)
    for r in todo:
        plan = plans[r - 1]
        reel, t0, cuts = build_reel(ev, plan)
        reel.layout()
        total = reel.total / FPS
        wav = os.path.join(OUT, f'{reel.name}_mix.wav')
        aud = logo_reveal_audio(cuts)
        audio.mix(wav, plan['track'], t0, total, **aud)
        if a.preview:
            os.environ.setdefault('AIRA_PROXY_DIR', ev['proxy'])
            out = os.path.join(OUT, f'{reel.name}_preview.mp4')
            reel.render(out, audio=wav, preview_scale=0.5)
        else:
            out = os.path.join(OUT, f'{reel.name}.mp4')
            reel.render(out, audio=wav)
        print('wrote', out, f'{total:.2f}s', plan['track'])


if __name__ == '__main__':
    main()
