# Body layer: median body, collar region from Example, head/skin removed, white gaps transparent
import numpy as np, colorsys
from PIL import Image
q = np.asarray(Image.open('body_q.png').convert('RGBA')).copy()
ex = np.asarray(Image.open('example100.png').convert('RGB')).astype(int)
C = np.load('body_pal.npy')
def snap(px): return C[((C - px)**2).sum(1).argmin()]
def is_skin_or_hair(px):
    r, g, b = px; h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    return r > g > b and (r - b) > 30 and h < 0.12 and not (r > 150 and g < 90)
# collar/shoulder band from Example (snapped to body palette)
for y in range(33, 47):
    for x in range(24, 56):
        if q[y, x, 3] == 0: continue
        q[y, x, :3] = snap(ex[y, x])
# remove head: everything above the shoulders in the head column, and skin/hair-ish pixels in the collar band
for y in range(0, 35):
    q[y, 26:57, 3] = 0
for y in range(35, 45):
    for x in range(30, 52):
        if is_skin_or_hair(q[y, x, :3]): q[y, x, 3] = 0
# white / near-white enclosed gaps (between legs) -> transparent, but keep skate blades (rows 88-91)
lum = q[..., :3] @ [0.299, 0.587, 0.114]
sat = q[..., :3].max(2) - q[..., :3].min(2)
gap = (lum > 235) & (sat < 20)
gap[86:92] = False
q[gap, 3] = 0
Image.fromarray(q).save('parts/body.png')
# collar band: anything that isn't jersey-dark or orange becomes jersey black (trim is drawn by the collar layer)
K = np.array([22, 18, 26])
for y in range(34, 47):
    for x in range(26, 53):
        if q[y, x, 3] == 0 and not (30 <= x <= 50 and y >= 35): continue
        r, g, b = map(int, q[y, x, :3])
        lum_ = 0.299*r + 0.587*g + 0.114*b
        orange = r > 120 and g < 90 and b < 60
        if not orange and lum_ > 70: q[y, x, :3] = K; q[y, x, 3] = 255
        if q[y, x, 3] == 0: q[y, x, :3] = K; q[y, x, 3] = 255
# light grey halo pixels on the silhouette edge (torso/arms) -> transparent
a = q[..., 3] > 0
for y in range(30, 86):
    for x in range(1, 99):
        if not a[y, x]: continue
        r, g, b = map(int, q[y, x, :3]); lum_ = 0.299*r + 0.587*g + 0.114*b
        if lum_ > 120 and max(r,g,b) - min(r,g,b) < 30 and not (a[y, x-1] and a[y, x+1] and a[y-1, x] and a[y+1, x]):
            q[y, x, 3] = 0
Image.fromarray(q).save('parts/body.png')
# clear the averaged jersey-number smudge on the sleeve (the app draws the real number there)
J1, J2 = np.array([22, 18, 26]), np.array([37, 37, 43])
for y in range(39, 46):
    for x in range(19, 26):
        if q[y, x, 3]: q[y, x, :3] = J2 if (x + y) % 3 == 0 else J1
Image.fromarray(q).save('parts/body.png')
q[q[..., 3] == 0] = 0
Image.fromarray(q).save('parts/body.png')
