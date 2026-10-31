"""Contact sheets: one row per 16 s of each clip, 8 tiles per row, labelled clip@time."""
import sys, os, subprocess, json, glob
from PIL import Image, ImageDraw, ImageFont
PRX, OUT = sys.argv[1], sys.argv[2]
names = sys.argv[3:] or sorted(os.path.basename(p)[:-4] for p in glob.glob(PRX + '/C*.mp4'))
os.makedirs(OUT, exist_ok=True)
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)
TW, TH, COLS, SPAN = 240, 135, 8, 16.0
rows = []
for n in names:
    p = os.path.join(PRX, n + '.mp4')
    d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                             capture_output=True, text=True).stdout.strip() or 0)
    nrows = max(1, int((d - 0.01) // SPAN) + 1)
    for r in range(nrows):
        a = r * SPAN; b = min(d, a + SPAN)
        ts = [a + (b - a) * (i + 0.5) / COLS for i in range(COLS)]
        tiles = []
        for t in ts:
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.2f}', '-i', p, '-frames:v', '1', '-vf', f'scale={TW}:{TH}',
                                  '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
            im = Image.frombytes('RGB', (TW, TH), raw) if len(raw) == TW * TH * 3 else Image.new('RGB', (TW, TH))
            dr = ImageDraw.Draw(im)
            lab = f'{n[1:]}@{t:.1f}'
            dr.rectangle([0, 0, 8 + 9 * len(lab), 19], fill=(0, 0, 0))
            dr.text((3, 1), lab, fill=(255, 255, 0), font=font)
            tiles.append(im)
        rows.append(tiles)
PER = 10
for s in range(0, len(rows), PER):
    chunk = rows[s:s + PER]
    sheet = Image.new('RGB', (COLS * (TW + 2), len(chunk) * (TH + 2)), 'white')
    for ri, tiles in enumerate(chunk):
        for ci, im in enumerate(tiles):
            sheet.paste(im, (ci * (TW + 2), ri * (TH + 2)))
    fn = os.path.join(OUT, f'sheet_{names[0]}_{s // PER:02d}.jpg')
    sheet.save(fn, quality=85)
    print(fn)
