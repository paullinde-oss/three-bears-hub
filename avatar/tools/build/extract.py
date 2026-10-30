# Extract a hair or beard layer from a source player as shade levels (0..4), -1 transparent
import numpy as np, colorsys
S = np.load('stack100.npy').astype(int)
NAMES = open('stack_names.txt').read().split('\n')
def lum(p): return 0.299*p[...,0] + 0.587*p[...,1] + 0.114*p[...,2]
def skin_ref(a):
    boxes = [a[19:22, 40:47], a[28:32, 42:48]]
    cands = [b.reshape(-1,3) for b in boxes]
    best = max(cands, key=lambda c: np.median(lum(c)))
    return np.median(best, 0)
def classify(i, region='hair', shift=(0,0)):
    a = np.roll(S[i], shift, axis=(0,1))
    sk = skin_ref(a); skl = lum(sk)
    L = lum(a); d = np.sqrt(((a - sk)**2).sum(-1))
    sat = a.max(-1) - a.min(-1)
    bg = (L > 225) & (sat < 30)
    skinlike = (d < 55) | ((L > skl*0.82) & (a[...,0] > a[...,2] + 25) & (d < 90))
    jersey = (sat < 30) & (L < 60)          # near-black neutral
    m = ~bg & ~skinlike
    sel = np.zeros_like(m)
    if region == 'hair':
        sel[6:24, 24:56] = True              # top of head
        sel[24:36, 24:37] = True             # sides / back down to the collar
        sel[33:40, 24:31] = True             # long hair hanging at the back
        sel[22:30, 36:52] = False            # keep eyes/brows out
    else:                                    # facial hair
        sel[28:42, 34:52] = True
        sel[24:30, 34:38] = True             # sideburn join
        sel[34:42, 24:34] = False
    sel[35:, 31:] &= (region != 'hair')
    m &= sel
    if region == 'hair': m &= ~(jersey & (np.arange(100)[:,None] >= 33))
    else:
        m &= ~(jersey & (np.arange(100)[:,None] >= 38))
        m[:, :] &= ~((a[...,0] > 150) & (a[...,1] < 90))   # orange collar
    # drop the light-grey anti-alias halo that borders the background
    halo = (sat < 32) & (L > 120)
    nb = np.zeros_like(bg)
    nb[1:] |= bg[:-1]; nb[:-1] |= bg[1:]; nb[:, 1:] |= bg[:, :-1]; nb[:, :-1] |= bg[:, 1:]
    m &= ~(halo & nb)
    # isolated specks
    cnt = np.zeros(m.shape, int)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx: cnt += np.roll(np.roll(m, dy, 0), dx, 1)
    m &= cnt >= 2
    lv = np.full((100,100), -1, int)
    if m.sum():
        v = L[m]; q = np.quantile(v, [0.15, 0.4, 0.7, 0.92])
        lv[m] = np.digitize(v, q)
    return lv
