"""Deliver a batch of text-free event reels: MP4, text-free cover (a frame of a complete
look from the reel itself), caption, delivery tracker and music licence log.

usage: python3 tools/deliver_event.py --event 1
"""
import argparse, collections, csv, json, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'reels'))
sys.argv, ARGS = sys.argv[:1], sys.argv[1:]
import event_reels as E  # noqa: E402
from common import audio, FPS  # noqa: E402

BATCH = {1: dict(folder='Expo_2026-10-15', prefix='AIRA_EXPO', event='AIRA stall, fashion & lifestyle expo, 15 Oct 2026',
                flow='outside -> hall -> AIRA logo -> shop -> people -> products -> AIRA wall -> logo card',
                downloaded='2026-10-31'),
         2: dict(folder='Store_2026-09-25', prefix='AIRA_STORE', event='AIRA store evening, 25 Sep 2026',
                 flow='outside -> entrance -> AIRA logo -> store -> people -> products -> AIRA wall -> logo card',
                 downloaded='2026-11-02')}

# 15 captions: short, no on-screen text in the reels, no product / price / fabric claims
CAPTIONS = {1: [
    "Step inside AIRA ✨\nThe stall, the people and the pieces everyone stopped for.\n\nWhich look would you pick? 👇",
    "From the entrance to the rails 🤍\nA day with AIRA at the expo.\n\nSave this for your next outfit idea.",
    "The details everyone came closer for ✨\nEmbroidery, prints and finishing touches, up close.\n\nTell us your favourite 👇",
    "Thank you to everyone who stopped by the AIRA stall 🤍\nSo many beautiful looks in one place.\n\nWhich one's your style? 👇",
    "A little walk through AIRA ✨\nOutside the venue, into the stall, straight to the rails.\n\nShare this with someone who'd love it.",
    "AIRA, up close 🤍\nThe space, the people and the details.\n\nComment your favourite look 👇",
    "Where every rail tells a story ✨\nMoments from the AIRA stall.\n\nSave this for later.",
    "Elegant, effortless, AIRA 🤍\nLooks and details from the expo.\n\nWhich piece caught your eye? 👇",
    "Come in, take a look ✨\nThe AIRA stall, from the first step to the last detail.\n\nTag a friend who'd love this.",
    "Moments from AIRA 🤍\nOur guests, our pieces, our space.\n\nWhich look is your favourite? 👇",
    "The AIRA experience ✨\nFrom the entrance to the finishing touches.\n\nSave this for your next outfit idea.",
    "Styled, chosen, loved 🤍\nA look inside the AIRA stall.\n\nTell us what you'd wear 👇",
    "Every detail, considered ✨\nPrints, embroidery and the people who wore them.\n\nShare this with your shopping partner.",
    "The AIRA wall, the rails, the people 🤍\nA few favourite moments from the expo.\n\nWhich one's you? 👇",
    "See you at AIRA ✨\nThank you for making the expo so special.\n\nComment your favourite look 👇",
], 2: [
    "Step inside the AIRA store ✨\nThe welcome, the people and the pieces everyone came for.\n\nWhich look would you pick? 👇",
    "From the flower-lined entrance to the rails 🤍\nAn evening at AIRA.\n\nSave this for your next outfit idea.",
    "The details everyone stopped for ✨\nPrints, embroidery and finishing touches, up close.\n\nTell us your favourite 👇",
    "Thank you to everyone who came to the AIRA store 🤍\nSo many beautiful looks in one evening.\n\nWhich one's your style? 👇",
    "A little walk through AIRA ✨\nIn from the street, up the stairs, straight to the rails.\n\nShare this with someone who'd love it.",
    "AIRA, up close 🤍\nThe store, the people and the details.\n\nComment your favourite look 👇",
    "Where every rail tells a story ✨\nMoments from the AIRA store.\n\nSave this for later.",
    "Elegant, effortless, AIRA 🤍\nLooks and details from the evening.\n\nWhich piece caught your eye? 👇",
    "Come in, take a look ✨\nThe AIRA store, from the first step to the last detail.\n\nTag a friend who'd love this.",
    "Moments from AIRA 🤍\nOur guests, our pieces, our space.\n\nWhich look is your favourite? 👇",
    "The AIRA experience ✨\nFrom the welcome wall to the finishing touches.\n\nSave this for your next outfit idea.",
    "Styled, chosen, loved 🤍\nA look inside the AIRA store.\n\nTell us what you'd wear 👇",
    "Every detail, considered ✨\nPrints, embroidery and the people who wore them.\n\nShare this with your shopping partner.",
    "The AIRA wall, the rails, the people 🤍\nA few favourite moments from the evening.\n\nWhich one's you? 👇",
    "See you at AIRA ✨\nThank you for making the evening so special.\n\nComment your favourite look 👇",
]}
TAGS = '\n\n#AIRA #AIRAWomenswear #Womenswear #FashionReels #StyleInspiration'


def ffprobe_dur(p):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                                capture_output=True, text=True).stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--event', type=int, default=1)
    a = ap.parse_args(ARGS)
    ev, b = E.EVENTS[a.event], BATCH[a.event]
    if ev.get('raw'):
        os.environ['AIRA_RAW'] = ev['raw']
    dst = os.path.join(ROOT, 'final', b['folder'])
    os.makedirs(dst, exist_ok=True)
    plans = E.plan_all(ev)
    tracker, lic, cover_clips, cover_who = [], [], set(), collections.Counter()
    for p in plans:
        r = p['reel']
        src = os.path.join(E.OUT, f"AIRA_{ev['name']}_R{r:02d}.mp4")
        base = f"{b['prefix']}_R{r:02d}"
        mp4 = os.path.join(dst, base + '.mp4')
        shutil.copy2(src, mp4)
        reel, t0, cuts = E.build_reel(ev, p)
        # cover: middle of a complete-look shot whose clip no earlier cover used, so the
        # 15 covers show different people (else any look, else the first people shot)
        shots = [s for s in p['shots']]
        looks_i = [i for i, s in enumerate(shots) if s.get('opt', {}).get('look')]
        if any(shots[i]['opt'].get('who') for i in looks_i):
            # guests are tagged (`who`): rotate covers between people, then between clips
            k = min(looks_i, key=lambda i: (cover_who[shots[i]['opt'].get('who')],
                                            shots[i]['clip'] in cover_clips, i))
        else:
            fresh = [i for i in looks_i if shots[i]['clip'] not in cover_clips]
            k = (fresh or looks_i or [next(i for i, s in enumerate(shots) if s['cat'] == 'people')])[0]
        cover_clips.add(shots[k]['clip'])
        cover_who[shots[k]['opt'].get('who')] += 1
        tc = (cuts[k] + cuts[k + 1]) / 2
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{tc:.3f}', '-i', mp4, '-frames:v', '1', '-q:v', '2',
                        os.path.join(dst, base + '_thumbnail.jpg')], check=True)
        open(os.path.join(dst, base + '_caption.txt'), 'w').write(CAPTIONS[a.event][r - 1] + TAGS + '\n')
        t = audio.TRACKS[p['track']]
        dur = ffprobe_dur(mp4)
        looks = sum(1 for s in shots if s.get('opt', {}).get('look'))
        tracker.append({'Event': b['event'], 'Reel': r, 'File': base + '.mp4', 'Thumbnail': base + '_thumbnail.jpg',
                        'Caption': base + '_caption.txt',
                        'Flow': b['flow'],
                        'On-screen text': 'none (client request)',
                        'Shots': ' | '.join(f"{s['cat']}:{s['clip']}@{s['t']}" for s in shots if 'clip' in s),
                        'Complete looks shown': looks, 'Duration (s)': f'{dur:.2f}',
                        'Format': 'MP4 H.264, 1080x1920, 9:16, 30 fps, AAC 48 kHz',
                        'Music': f"{t['title']} - {t['artist']} (Mixkit)", 'Licence': t['licence'],
                        'Status': 'Ready for client review', 'Revisions': '', 'Approved': ''})
        lic.append({'Reel': base, 'Track': t['title'], 'Artist': t['artist'], 'Source': t['source'], 'File URL': t['url'],
                    'Section used': f'{t0:.2f}-{t0 + dur:.2f} s', 'Licence': t['licence'],
                    'Licence URL': t['licence_url'],
                    'Commercial use on Instagram/Facebook': 'Yes (social media video posts and online ads are allowed)',
                    'Attribution required': 'No', 'Restrictions': t['licence_terms'], 'Downloaded': b['downloaded'],
                    'Claims contact': 'team@mixkit.co'})
        print(base, f'{dur:.2f}s', t['title'], 'looks', looks)
    for name, rows in ((f"{b['prefix']}_delivery_tracker.csv", tracker), (f"{b['prefix']}_music_licence_log.csv", lic)):
        with open(os.path.join(dst, name), 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    print('delivered to', dst)


if __name__ == '__main__':
    main()
