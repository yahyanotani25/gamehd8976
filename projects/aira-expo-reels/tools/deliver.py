"""Assemble the week's delivery: final MP4s, thumbnails and captions under matching
names, plus the delivery tracker and the music licence log (CSV).

usage: python3 tools/deliver.py   (after the reels and thumbnails are rendered)
"""
import csv, importlib, json, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'reels'))
sys.argv = sys.argv[:1]
OUT = os.path.join(ROOT, 'out')
WEEK = os.path.join(ROOT, 'final', 'Week01')
TRACKS = json.load(open(os.path.join(ROOT, 'audio', 'tracks.json')))

REELS = [
    dict(n=1, mod='r1_event', slug='Step-Inside', track='winter_breeze',
         concept='Expo recap in the reference style: shop, products, people',
         hook='STEP INSIDE + AIRA logo',
         tip='Embellished neckline? Skip the necklace and let statement earrings lead.'),
    dict(n=2, mod='r2_details', slug='The-Details', track='house_02',
         concept='Close-up details: embroidery, necklines, AIRA tags, packaging',
         hook='THE DETAILS MAKE THE DIFFERENCE',
         tip="Match your dupatta to the kurta's base colour and let the embroidery shine."),
    dict(n=3, mod='r3_day_evening', slug='Day-to-Evening', track='hazy_after_hours',
         concept='Occasion-based: daywear looks vs evening looks',
         hook='FROM DAYWEAR TO EVENING',
         tip='Day to evening? Swap soft pastels for rich jewel tones and add a touch of gold.'),
    dict(n=4, mod='r4_print_embroidery', slug='Print-or-Embroidery', track='cat_walk',
         concept='Two AIRA campaign looks: print vs embroidery, with pieces from the rails',
         hook='PRINT OR EMBROIDERY? (CTA: Which one\'s you?)',
         tip='Pick one statement, print or embroidery, and keep the rest of the look simple.'),
]


def dur(p):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                                capture_output=True, text=True).stdout)


def main():
    os.makedirs(WEEK, exist_ok=True)
    tracker, licences = [], []
    for r in REELS:
        m = importlib.import_module(r['mod'])
        base = f"AIRA_W01_R{r['n']:02d}_{r['slug']}"
        src = os.path.join(OUT, m.reel.name + '.mp4')
        shutil.copy2(src, os.path.join(WEEK, base + '.mp4'))
        shutil.copy2(os.path.join(OUT, f"R{r['n']:02d}_thumbnail.jpg"), os.path.join(WEEK, base + '_thumbnail.jpg'))
        assert os.path.exists(os.path.join(WEEK, base + '_caption.txt')), base
        looks = [s.note for s, _ in m.reel.items if 'look' in getattr(s, 'note', '')]
        t = TRACKS[r['track']]
        total = dur(src)
        music_used = f"{m.music_start:.2f}-{m.music_start + total:.2f} s"
        tracker.append({
            'Week': 1, 'Reel': r['n'], 'File': base + '.mp4', 'Caption': base + '_caption.txt',
            'Thumbnail': base + '_thumbnail.jpg', 'Concept': r['concept'], 'Hook (on screen)': r['hook'],
            'Complete looks shown': ' | '.join(looks), 'Styling tip (on screen)': r['tip'],
            'Duration (s)': f'{total:.2f}', 'Format': 'MP4 H.264, 1080x1920, 9:16, 30 fps, AAC 48 kHz',
            'Music': f"{t['title']} - {t['artist']} (Mixkit)", 'Licence': t['licence'],
            'Ending': 'AIRA wall, flare + eclipse into the AIRA logo card, fade to black (as the reference)',
            'Status': 'Sample batch: ready for client review', 'Revisions': '', 'Approved': ''})
        licences.append({
            'Reel': base, 'Track': t['title'], 'Artist': t['artist'], 'Genre': t['genre'],
            'Source': t['source'], 'File URL': t['url'], 'Section used': music_used,
            'Licence': t['licence'], 'Licence URL': t['licence_url'],
            'Commercial use on Instagram/Facebook': 'Yes (social media video posts and online ads are allowed)',
            'Attribution required': 'No', 'Restrictions': t['licence_terms'],
            'Downloaded': '2026-10-31', 'Claims contact': 'team@mixkit.co'})
    for name, rows in (('AIRA_W01_delivery_tracker.csv', tracker), ('AIRA_W01_music_licence_log.csv', licences)):
        with open(os.path.join(WEEK, name), 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print('wrote', name)
    for r in tracker:
        print(r['Reel'], r['File'], r['Duration (s)'], '|', r['Complete looks shown'])


if __name__ == '__main__':
    main()
