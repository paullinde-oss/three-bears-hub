import numpy as np
from PIL import Image
from collections import deque
med = np.asarray(Image.open('median100.png').convert('RGB')).astype(int)
H, W = med.shape[:2]
lum = med @ [0.299, 0.587, 0.114]
sat = med.max(2) - med.min(2)
# background: flood fill from border through light, low-saturation pixels
bgish = (lum > 200) & (sat < 40)
bg = np.zeros((H, W), bool); q = deque()
for x in range(W):
    for y in (0, H-1): q.append((y, x))
for y in range(H):
    for x in (0, W-1): q.append((y, x))
while q:
    y, x = q.popleft()
    if not (0 <= y < H and 0 <= x < W) or bg[y, x] or not bgish[y, x]: continue
    bg[y, x] = True
    q.extend([(y+1, x), (y-1, x), (y, x+1), (y, x-1)])
# k-means palette on foreground
fg = med[~bg].astype(float)
rng = np.random.default_rng(1); k = 22
C = fg[rng.choice(len(fg), k, replace=False)]
for _ in range(40):
    lab = ((fg[:, None] - C[None])**2).sum(-1).argmin(1)
    for i in range(k):
        if (lab == i).any(): C[i] = fg[lab == i].mean(0)
C = C.round().astype(int)
out = np.zeros((H, W, 4), np.uint8)
idx = ((med[:, :, None, :] - C[None, None])**2).sum(-1).argmin(-1)
out[..., :3] = C[idx]; out[..., 3] = np.where(bg, 0, 255)
np.save('body_idx.npy', idx); np.save('body_pal.npy', C); np.save('body_bg.npy', bg)
Image.fromarray(out).save('body_q.png')
print('palette:', [tuple(c) for c in C])
