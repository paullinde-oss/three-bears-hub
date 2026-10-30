# Accessories, captain badge and jersey digits
import sys; sys.path.insert(0, 'tools')
import numpy as np
from feat import draw, FIX
FIX.update({'G': (232, 190, 70), 'g': (170, 128, 40), 'S': (214, 218, 226), 's': (140, 146, 158),
            'F': (84, 80, 92), 'L': (150, 190, 215), 'K': (14, 12, 18), 'Q': (250, 250, 250)})
S100 = np.load('stack100.npy').astype(int)
def cap():
    a = S100[15]; L = 0.299*a[...,0] + 0.587*a[...,1] + 0.114*a[...,2]
    m = np.zeros((100, 100), bool)
    reg = (a[..., 2] > a[..., 0] + 12) & (L < 170)
    m[4:24, 24:62] = reg[4:24, 24:62]
    # include the cap's dark outline next to blue pixels
    dark = L < 50
    grow = m.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1): grow |= np.roll(np.roll(m, dy, 0), dx, 1)
    m |= grow & dark & (np.arange(100)[:, None] < 24)
    lv = np.full((100, 100), -1, int)
    v = L[m]; q = np.quantile(v, [0.12, 0.35, 0.65, 0.9]); lv[m] = np.digitize(v, q)
    return lv
def toque():
    lv = np.full((100, 100), -1, int)
    spans = {6:(39,42),7:(38,43),8:(36,45),9:(34,47),10:(33,48),11:(32,49),12:(31,50),13:(30,51),14:(30,51),15:(29,51),16:(29,52),17:(29,52),18:(29,52),19:(29,52),20:(29,52)}
    for y,(a,b) in spans.items(): lv[y, a:b+1] = 2
    for y in range(9, 18):
        for x in range(30, 52):
            if lv[y, x] >= 0 and (x % 3 == 0): lv[y, x] = 1          # knit ribs
            if lv[y, x] >= 0 and 42 <= x <= 47 and y < 15 and x % 3: lv[y, x] = 3
    for y in (18, 19, 20):                                            # folded band
        for x in range(29, 53):
            if lv[y, x] >= 0: lv[y, x] = 3 if x % 2 else 2
    for (x, y) in [(39,3),(40,3),(41,3),(38,4),(39,4),(40,4),(41,4),(42,4),(39,5),(40,5),(41,5)]: lv[y, x] = 4  # pom-pom
    m = lv >= 0
    for y in range(1, 99):
        for x in range(1, 99):
            if m[y, x] and not (m[y-1,x] and m[y+1,x] and m[y,x-1] and m[y,x+1]): lv[y, x] = 0
    return lv
GLASSES = {
  'glasses':    (["FFFFFF.FFFFF", "F....FFF...F", "F....F.F...F", ".FFFF...FFF."], (36, 23)),
  'sunglasses': (["FFFFFF.FFFFF", "FKKKKFFFKKKF", "FKKLKF.FKKLF", ".FFFF...FFF."], (36, 23)),
}
EARRINGS = {'earring_gold': (["G", "g"], (29, 32)), 'earring_silver': (["S", "s"], (29, 32))}
# Captain 'C': black letter with a white outline (reads correctly, not mirrored)
def _captain():
    letter = [".KKKK", "KK...", "KK...", "KK...", "KK...", ".KKKK"]
    H, W = len(letter) + 2, len(letter[0]) + 2
    g = [['.'] * W for _ in range(H)]
    for j, r in enumerate(letter):
        for i, c in enumerate(r):
            if c == 'K': g[j+1][i+1] = 'K'
    for j in range(H):
        for i in range(W):
            if g[j][i] == '.' and any(0 <= j+dy < H and 0 <= i+dx < W and g[j+dy][i+dx] == 'K'
                                      for dy in (-1,0,1) for dx in (-1,0,1)):
                g[j][i] = 'Q'
    return [''.join(r) for r in g]
CAPTAIN = (_captain(), (25, 41))
DIGITS = {'0':["111","101","101","101","111"],'1':["010","110","010","010","111"],'2':["111","001","111","100","111"],
          '3':["111","001","111","001","111"],'4':["101","101","111","001","001"],'5':["111","100","111","001","111"],
          '6':["111","100","111","101","111"],'7':["111","001","001","010","010"],'8':["111","101","111","101","111"],'9':["111","101","111","001","111"]}
def number(n, out):
    s = str(n)[:2]; O = (214, 76, 30)
    x0 = 19 if len(s) == 2 else 21
    for k, ch in enumerate(s):
        for j, row in enumerate(DIGITS[ch]):
            for i, c in enumerate(row):
                if c == '1': out[41 + j, x0 + k*4 + i] = (*O, 255)
    return out
