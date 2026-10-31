"""Cover thumbnails (1080x1920 JPG) for the four reels.

Same grade as the reels (reference-matched LUT, vignette), white Jost titles and the
official AIRA logo. Titles and faces stay inside the centre 1080x1440 band, which is
what the Instagram profile grid shows (3:4) of a 9:16 cover.
"""
import os, sys, math
import numpy as np
import cv2
from common import rk, hook, _shadowed_logo, ROOT

OUT = os.path.join(ROOT, 'out')
W, H = rk.W, rk.H


def grab(clip, t):
    r = rk.open_reader(clip, int(t * 100))
    img = r.get(int(t * 100)).copy()
    r.close()
    return img


def panel(img, w, h, cx, cy, z=1.0):
    """Crop a w:h window centred at (cx, cy) source px; z=1 fills the panel height with
    the full source height (or the full width if the panel is wider than 16:9)."""
    s = max(h / rk.SH, w / rk.SW) * z
    hx, hy = w / 2 / s, h / 2 / s
    cx = min(max(cx, hx), rk.SW - hx)
    cy = min(max(cy, hy), rk.SH - hy)
    M = np.array([[s, 0, w / 2 - s * cx], [0, s, h / 2 - s * cy]], np.float32)
    out = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT101)
    return rk.sharpen(out)


def put(img, layer, cx, cy):
    return rk.Overlay(layer, 0, 1, cx=cx, cy=cy, fade_in=0, fade_out=0, drift=0).apply(img, 0.5)


def finish(img):
    return rk.Finisher(grain=1.2)(img, 0, vignette=True, grain=True)


def single(clip, t, cx, cy, z, title_layer, title_cy=430):
    img = panel(grab(clip, t), W, H, cx, cy, z)
    img = finish(img)
    return put(img, title_layer, W / 2, title_cy)


def stacked(top, bottom, title_lines):
    """Two looks stacked (each 1080x960) with a thin ivory rule; the title sits on the
    seam and reads top look -> bottom look, so no extra labels cover faces or outfits."""
    a = panel(grab(top[0], top[1]), W, H // 2, top[2], top[3], top[4])
    b = panel(grab(bottom[0], bottom[1]), W, H // 2, bottom[2], bottom[3], bottom[4])
    img = finish(np.vstack([a, b]))
    img[H // 2 - 3:H // 2 + 3] = (238, 244, 247)
    title = rk.text_layer(title_lines, size=64, weight=500, tracking=0.2, upper=True, shadow=0.75, pad=40,
                          scrim=0.55)
    return put(img, title, W / 2, H / 2)


def logo_mark(img, cy=1600, width=230):
    return put(img, _shadowed_logo(width), W / 2, cy)


def save(img, name):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name)
    cv2.imwrite(p, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print('thumb', p)
    return p


def main():
    from common import FPS  # noqa
    from common import have
    # R1: a complete look in the expo hall, title above her head
    r1 = single('C0049', 5.2, 880, 540, 1.0, hook(['Step inside'], logo_width=330), title_cy=380)
    save(r1, 'R01_thumbnail.jpg')
    # R2: embroidered kurta with its AIRA tag, AIRA wall behind (the tag carries the logo)
    r2 = single('C0070', 6.2, 850, 560, 1.0, hook(['The details', 'make the difference'], size=60))
    save(r2, 'R02_thumbnail.jpg')
    # R3: day look (host, pastel print) over evening look (jewel tone and gold)
    evening = ('C0142', 1.0, 800, 470, 1.0) if have('C0142', 1.0) else ('C0127', 4.4, 1085, 400, 1.5)
    r3 = stacked(('C0061', 9.2, 1150, 520, 1.0), evening, ['From daywear', 'to evening'])
    save(r3, 'R03_thumbnail.jpg')
    # R4: the two AIRA campaign looks, print over embroidery
    r4 = stacked(('C0002', 1.0, 900, 430, 1.0), ('C0007', 1.0, 900, 470, 1.0), ['Print', 'or embroidery?'])
    save(r4, 'R04_thumbnail.jpg')


if __name__ == '__main__':
    main()
