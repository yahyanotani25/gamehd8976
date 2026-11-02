import sys, subprocess, numpy as np, cv2
PRX = __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))), 'proxy')
def frame(c, t):
    raw = subprocess.run(['ffmpeg','-v','error','-ss',f'{t:.2f}','-i',f'{PRX}/{c}.mp4','-frames:v','1','-f','rawvideo','-pix_fmt','bgr24','-'],capture_output=True).stdout
    return np.frombuffer(raw,np.uint8).reshape(360,640,3) if len(raw)==640*360*3 else None
def letters(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[...,0], hsv[...,1], hsv[...,2]
    red = (((h < 14) | (h > 168)) & (s > 110) & (v > 60)).astype(np.uint8)
    white = ((s < 70) & (v > 175)).astype(np.uint8)
    near = cv2.dilate(red, np.ones((11, 11), np.uint8))
    lt = white & near
    # letters are surrounded by wall on most sides: require red both above and below within 25 px
    up = cv2.dilate(red, np.ones((25,1),np.uint8), anchor=(0,24)); dn = cv2.dilate(red, np.ones((25,1),np.uint8), anchor=(0,0))
    lt = lt & up & dn
    rows = cv2.blur(lt.astype(np.float32), (1, 1)).sum(1)
    band = np.convolve(rows, np.ones(15), 'same')
    if band.max() < 60: return None
    y = int(np.argmax(band)); y0, y1 = max(0, y-20), min(360, y+20)
    cols = lt[y0:y1].sum(0).astype(np.float32)
    cs = np.convolve(cols, np.ones(9), 'same')
    xs = np.where(cs > 2)[0]
    if len(xs) < 10: return None
    # longest run allowing gaps < 30 px (letter spacing)
    runs, a, prev = [], xs[0], xs[0]
    for x in xs[1:]:
        if x - prev > 30: runs.append((a, prev)); a = x
        prev = x
    runs.append((a, prev))
    a, b = max(runs, key=lambda r: cols[r[0]:r[1]+1].sum())
    # letter height: contiguous rows around the band that hold letter pixels
    prof = lt[:, a:b + 1].sum(1)
    top = bot = y
    while top > 0 and prof[top - 1] > 1: top -= 1
    while bot < 359 and prof[bot + 1] > 1: bot += 1
    hgt = (bot - top + 1) * 3
    # the thin strokes of the crossbar-less A are often missed, so judge the word by
    # its height: the AIRA wordmark is 4.72x as wide as it is tall
    return dict(x0=int(a)*3, x1=int(b)*3, y=int(y)*3, mass=float(cols[a:b+1].sum()), h=int(hgt),
                word_w=int(4.72 * hgt))
if __name__ == '__main__':
    for spec in sys.argv[1:]:
        c, t = spec.split('@'); r = letters(frame(c, float(t)))
        if r: w = r['x1']-r['x0']; print(f"{spec:12s} x {r['x0']:4d}-{r['x1']:4d} w {w:4d} h {r['h']:3d} word {r['word_w']:4d} cx {(r['x0']+r['x1'])//2:4d} y {r['y']:4d} mass {r['mass']:.0f}")
        else: print(spec, 'none')
