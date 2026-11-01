"""Upscaling for the AI stills before the Ken Burns move.

The stills are 1344x768; they are upscaled once to 2400 px wide (Lanczos plus a
light unsharp mask) so the slow push-in never enlarges past the source detail.
"""
import cv2


def upscale(img, W=1920, sharpen=0.4):
    h, w = img.shape[:2]
    s = W / w
    up = cv2.resize(img, (W, int(round(h * s))), interpolation=cv2.INTER_LANCZOS4)
    if sharpen > 0:
        bl = cv2.GaussianBlur(up, (0, 0), 1.3)
        up = cv2.addWeighted(up, 1 + sharpen, bl, -sharpen, 0)
    return up
