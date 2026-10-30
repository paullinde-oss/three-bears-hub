#!/usr/bin/env python3
"""Lift hairstyles and facial hair out of existing player illustrations onto the base.

The original Three Bears player images were all drawn on the same body template as base.png, so a
player's hair or beard can be cut out and placed on the base. This writes "edited copies" of the base
(hair_<name>.png, beard_<name>.png) that canva_import.py then turns into parts, exactly like Canva edits.

  python3 harvest_originals.py <base.png> <folder of player images> <out folder> <spec>

spec is a comma list of  kind:name=file  e.g.  "hair:mullet=Paul.png,beard:full=Dave.jpg"
"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

SIZE = 500


def load(path):
    return np.asarray(Image.open(path).convert('RGB').resize((SIZE, SIZE), Image.LANCZOS)).astype(float)


def lum(a):
    return a @ np.array([0.299, 0.587, 0.114])


def skin_ref(a):
    boxes = [a[98:110, 200:240].reshape(-1, 3), a[145:165, 212:245].reshape(-1, 3)]
    def score(px):
        m = (px[:, 0] > px[:, 1]) & (px[:, 1] > px[:, 2]) & (lum(px) > 120)
        return m.mean(), px[m] if m.any() else px
    best = max((score(b) for b in boxes), key=lambda s: s[0])[1]
    return np.median(best, 0)


def mask_for(src, kind, base_ref=None):
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    sk = skin_ref(src)
    L = lum(src); sat = src.max(-1) - src.min(-1)
    d = np.sqrt(((src - sk) ** 2).sum(-1))
    bg = (L > 228) & (sat < 30)
    skinlike = (d < 52) | ((L > lum(sk) * 0.8) & (src[..., 0] > src[..., 2] + 25) & (d < 85))
    m = ~bg & ~skinlike
    if kind == 'hat':                                                      # the cap itself: its colour + outline
        region = (yy < 140) & (xx > 80) & (xx < 340)
        capc = (src[..., 2] > src[..., 0] + 12) & (L < 190)
        near = ndi.binary_dilation(capc, iterations=3)
        m = region & (capc | (near & (L < 60)))
        return ndi.binary_fill_holes(ndi.binary_closing(m, structure=np.ones((3, 3)))) & region
    if kind == 'glasses':                                                  # frames + lenses across the eyes
        region = (yy >= 104) & (yy < 150) & (xx > 160) & (xx < 280)
        frame = (L < 70) & (sat < 45)                     # dark frame only; the base's own eyes show through
        m = region & frame
        if base_ref is not None: m &= ~(lum(base_ref) < 70)
    elif kind == 'captain':                                                # the C patch on the chest
        region = (yy >= 195) & (yy < 250) & (xx > 125) & (xx < 185)
        m = region & ((L > 200) & (sat < 40))
        m = ndi.binary_dilation(m, iterations=2) & region                 # include the black inside the outline
        return ndi.binary_fill_holes(m)
    if kind == 'hair':
        region = (yy < 122) & (xx > 95) & (xx < 315)                       # top of the head
        region |= (yy >= 100) & (yy < 185) & (xx > 95) & (xx < 172)        # sides / back of the head
        region |= (yy >= 150) & (yy < 215) & (xx > 95) & (xx < 150)        # long hair at the back
        region &= ~((yy >= 108) & (yy < 152) & (xx >= 176) & (xx < 270))  # brows and eyes
        region &= ~((yy > 165) & (L < 55) & (sat < 30))                    # jersey
    elif kind != 'glasses':
        region = (yy >= 128) & (yy < 222) & (xx > 150) & (xx < 272)
        region &= ~((yy > 196) & (src[..., 0] > 150) & (src[..., 1] < 100))   # orange collar
        region &= ~((yy > 205) & (L < 50) & (sat < 25))                      # jersey below the chin
        m |= region & (L > 205) & (sat < 45)                                  # keep teeth with the beard's mouth
    m &= region
    m = ndi.binary_opening(m, structure=np.ones((2, 2)))
    lab, n = ndi.label(m)
    if n:
        sizes = ndi.sum(m, lab, range(1, n + 1))
        m = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= 40])
    m = ndi.binary_closing(m, structure=np.ones((4, 4)))
    return ndi.binary_fill_holes(m) & region


def clean_base(base):
    """Repaint grey, low-colour patches on the bald scalp as skin of the same brightness."""
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    L = lum(base); sat = base.max(-1) - base.min(-1)
    sk = skin_ref(base)
    patch = (sat < 40) & (L > 90) & (L < 220) & (yy < 160) & (xx > 95) & (xx < 300)
    patch = ndi.binary_opening(patch, structure=np.ones((2, 2)))
    patch = ndi.binary_dilation(patch) & (sat < 70) & (L > 80)
    out = base.copy()
    out[patch] = np.clip(sk * (L[patch] / lum(sk))[:, None], 0, 255)
    return out, int(patch.sum())


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    base_path, src_dir, out_dir, spec = sys.argv[1:]
    os.makedirs(out_dir, exist_ok=True)
    base, fixed = clean_base(load(base_path))
    if fixed: print(f'base: repainted {fixed} grey scalp pixels as skin')
    Image.fromarray(base.astype(np.uint8)).save(os.path.join(out_dir, 'base.png'))
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    base_bg = (lum(base) > 228) & ((base.max(-1) - base.min(-1)) < 30)
    # the base's ear: warm skin-coloured pixels (plus its outline) on the side of the head
    warm = (base[..., 0] > base[..., 1]) & (base[..., 1] >= base[..., 2]) & (base[..., 0] - base[..., 2] > 25) & (lum(base) > 70)
    ear_zone = (yy > 112) & (yy < 175) & (xx > 100) & (xx < 168)
    base_ear = ndi.binary_dilation(ndi.binary_fill_holes(ndi.binary_closing(warm & ear_zone, iterations=2)), iterations=2) & ear_zone
    for item in spec.split(','):
        kindname, fname = item.split('=')
        kind, name = kindname.split(':')
        src = load(os.path.join(src_dir, fname))
        m = mask_for(src, kind, base)
        if kind == 'hair':
            m &= ~base_ear                                     # the ear belongs to the base (and its skin tone)
            # where this player's head ends but the base's bald head continues, use the player's background
            src_bg = (lum(src) > 228) & ((src.max(-1) - src.min(-1)) < 30)
            beyond = src_bg & ~base_bg & (yy < 175) & (xx > 90) & (xx < 320)
            beyond &= ~((yy >= 108) & (xx >= 176) & (xx < 270))             # never cut into the face
            beyond = ndi.binary_opening(beyond, structure=np.ones((2, 2)))
            m |= beyond
        if kind == 'captain':                                 # the original art's C is mirrored; flip it to read correctly
            ys, xs = np.where(m); x0, x1 = xs.min(), xs.max() + 1
            src = src.copy(); src[:, x0:x1] = src[:, x0:x1][:, ::-1]; m[:, x0:x1] = m[:, x0:x1][:, ::-1]
        w = ndi.gaussian_filter(m.astype(float), 0.8)
        w[m] = 1
        out = base * (1 - w[..., None]) + src * w[..., None]
        fname_out = 'captain.png' if kind == 'captain' else f'{kind}_{name}.png'
        Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(os.path.join(out_dir, fname_out))
        print(f'{kind}:{name} <- {fname}  ({int(m.sum())} px)')


if __name__ == '__main__':
    main()
