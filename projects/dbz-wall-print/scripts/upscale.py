import sys, torch, numpy as np, cv2
from spandrel import ModelLoader
torch.set_num_threads(4)
model = ModelLoader().load_from_file(sys.argv[1]).eval()
im = cv2.imread(sys.argv[2])[:, :, ::-1].astype(np.float32) / 255.0
t = torch.from_numpy(np.ascontiguousarray(im.transpose(2, 0, 1)))[None]
# tile to save memory
_, _, H, W = t.shape; T = 192; P = 16; sc = model.scale
out = torch.zeros(1, 3, H * sc, W * sc)
with torch.inference_mode():
    for y in range(0, H, T):
        for x in range(0, W, T):
            y0, x0 = max(0, y - P), max(0, x - P); y1, x1 = min(H, y + T + P), min(W, x + T + P)
            o = model(t[:, :, y0:y1, x0:x1])
            oy, ox = (y - y0) * sc, (x - x0) * sc
            hh, ww = min(T, H - y) * sc, min(T, W - x) * sc
            out[:, :, y * sc:y * sc + hh, x * sc:x * sc + ww] = o[:, :, oy:oy + hh, ox:ox + ww]
r = (out[0].clamp(0, 1).numpy().transpose(1, 2, 0)[:, :, ::-1] * 255).round().astype(np.uint8)
cv2.imwrite(sys.argv[3], r)
print("done", r.shape)
