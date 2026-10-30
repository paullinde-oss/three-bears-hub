# Goalie body: Koobie2's goalie gear scaled/positioned so its collar sits under the shared head
import numpy as np, colorsys
from PIL import Image
from collections import deque
src = Image.open('../avatars_zip/3 Bears - Avatars/Koobie2.png').convert('RGB').resize((500, 500), Image.LANCZOS)
s, offx, offy = 0.9, -6.2, 11.6
big = src.resize((int(500*s), int(500*s)), Image.LANCZOS)
can = Image.new('RGB', (500, 500), (255, 255, 255))
can.paste(big, (int(round(offx*5)), int(round(offy*5))))
a = np.asarray(can.resize((100, 100), Image.BOX)).astype(int)
H, W = 100, 100
lum = a @ [0.299, 0.587, 0.114]; sat = a.max(2) - a.min(2)
bgish = (lum > 205) & (sat < 30)
bg = np.zeros((H, W), bool); q = deque([(y, x) for x in range(W) for y in (0, H-1)] + [(y, x) for y in range(H) for x in (0, W-1)])
while q:
    y, x = q.popleft()
    if not (0 <= y < H and 0 <= x < W) or bg[y, x] or not bgish[y, x]: continue
    bg[y, x] = True; q.extend([(y+1, x), (y-1, x), (y, x+1), (y, x-1)])
# enclosed white gaps between the pads -> transparent too (but keep white pad panels: they are enclosed by dark outlines)
fg = a[~bg].astype(float); rng = np.random.default_rng(3); k = 22
C = fg[rng.choice(len(fg), k, replace=False)]
for _ in range(40):
    lab = ((fg[:, None] - C[None])**2).sum(-1).argmin(1)
    for i in range(k):
        if (lab == i).any(): C[i] = fg[lab == i].mean(0)
C = C.round().astype(int)
idx = ((a[:, :, None, :] - C[None, None])**2).sum(-1).argmin(-1)
out = np.zeros((H, W, 4), np.uint8); out[..., :3] = C[idx]; out[..., 3] = np.where(bg, 0, 255)
# remove Koobie's head and neck
out[:34, 26:58, 3] = 0
for y in range(34, 46):
    for x in range(28, 52):
        r, g, b = map(int, out[y, x, :3]); h, l, sat_ = colorsys.rgb_to_hls(r/255, g/255, b/255)
        if r > g > b and (r - b) > 30 and h < 0.12 and not (r > 150 and g < 90): out[y, x, 3] = 0
out[out[..., 3] == 0] = 0
Image.fromarray(out).save('parts/goalie_body.png')
