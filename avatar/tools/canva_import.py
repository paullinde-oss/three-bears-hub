#!/usr/bin/env python3
"""Build avatar parts from Canva exports by comparing each edited copy against the base image.

Every option is made in Canva by editing a copy of ONE base player image (never moving or resizing it)
and downloading it as a PNG. This script finds what changed in each copy and saves just that as a
layer, so all parts line up perfectly and keep the full quality of the original art.

  python3 canva_import.py <folder of Canva PNGs> <avatar folder>     e.g.  canva_import.py ~/canva ../

Files in the input folder (any image size; they're scaled to 500x500):
  base.png              bald, clean-shaven skater with the default face and a blank sleeve (required)
  goalie_base.png       the same bald player in goalie gear, head in the same place (optional)
  skin_<name>.png       base with only the skin tone changed, e.g. skin_tan.png
  hair_<name>.png       base + one hairstyle, in BROWN (other colours are generated)
  beard_<name>.png      base + one facial hair style, in BROWN
  hat_<name>.png        base + a hat (drawn in any one colour; other colours are generated)
  glasses_<name>.png, earring_<name>.png, captain.png (base + the captain's C)

Writes <avatar folder>/img/*.png and <avatar folder>/parts.json. Needs numpy, pillow and scipy.
"""
import json, os, re, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

SIZE = 500
# Where each kind of part may appear (x0, y0, x1, y1) on the 500x500 canvas. Generous on purpose:
# only pixels that actually changed are kept, these boxes just stop stray AI noise elsewhere.
REGIONS = {
    'skin':       (90, 10, 310, 260),
    'hair':       (80, 0, 330, 230),
    'beard':      (130, 110, 290, 240),
    'hat':        (70, 0, 340, 150),
    'glasses':    (140, 80, 290, 160),
    'earring':    (110, 110, 190, 200),
    'captain':    (90, 170, 220, 290),
}
SLOT_OF = {'skin': 'skin', 'hair': 'hair', 'beard': 'facialHair', 'hat': 'hat', 'glasses': 'glasses',
           'earring': 'earring', 'captain': 'captain'}
DIFF_T = 26          # per-channel difference that counts as "changed"
MIN_BLOB = 60        # ignore changed specks smaller than this (pixels)

# 5-stop colour ramps (dark -> light) used to recolour hair, facial hair and hats
HAIR = {
    'black': ['#0b0b0f', '#1c1c24', '#2e2e3a', '#474756', '#6e6e84'],
    'dark_brown': ['#1a100e', '#301e18', '#462c20', '#603e2c', '#805840'],
    'brown': ['#40281e', '#603c28', '#845434', '#a67046', '#c49260'],
    'light_brown': ['#543824', '#805838', '#a4784e', '#c29868', '#dcba8a'],
    'auburn': ['#3c140e', '#6e2818', '#963e22', '#b85830', '#d27c4c'],
    'ginger': ['#60280e', '#a04818', '#cc6828', '#e68c40', '#f4b068'],
    'blond': ['#5c401e', '#966e32', '#c49850', '#e0be70', '#f4dea0'],
    'platinum': ['#786e60', '#b0a692', '#d6ceba', '#eae4d4', '#faf8f0'],
    'grey': ['#38383c', '#6e6e74', '#96969c', '#babac0', '#dadae0'],
}
GEAR = {
    'navy': ['#0e1222', '#1e2846', '#303e68', '#465888', '#6e82b0'],
    'black': ['#08080a', '#16161a', '#24242a', '#36363e', '#545460'],
    'red': ['#280a0a', '#781814', '#aa2c1e', '#cc462c', '#e8785a'],
    'orange': ['#3c1406', '#963212', '#c6521e', '#e47634', '#f4a060'],
    'green': ['#0a1e10', '#184c28', '#28703c', '#409454', '#6eba7c'],
    'grey': ['#28282c', '#606068', '#888890', '#acacb4', '#cecee0'],
    'white': ['#5a5a60', '#b4b4bc', '#d6d6dc', '#ececf0', '#fcfcfc'],
}


def load(path):
    im = Image.open(path).convert('RGBA')
    if im.size != (SIZE, SIZE):
        im = im.resize((SIZE, SIZE), Image.LANCZOS)
    a = np.asarray(im).astype(np.int16)
    # treat fully transparent pixels as white so they match a white-background base
    a[a[..., 3] == 0, :3] = 255
    return a


def remove_background(a):
    """Base image: make the (white) background transparent, keeping enclosed whites like skate blades."""
    rgb = a[..., :3]
    lum = rgb @ np.array([0.299, 0.587, 0.114])
    sat = rgb.max(-1) - rgb.min(-1)
    bgish = (lum > 232) & (sat < 22)
    lab, _ = ndi.label(bgish)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    out = a.copy().astype(np.uint8)
    out[..., 3] = np.where(bg, 0, 255)
    # soften the light anti-aliased fringe next to the background
    fringe = ndi.binary_dilation(bg) & ~bg & (lum > 170) & (sat < 40)
    out[fringe, 3] = np.clip((255 - lum[fringe]) * 255 / 85, 0, 255).astype(np.uint8)
    return out


def diff_layer(base, var, region):
    x0, y0, x1, y1 = region
    d = np.abs(var[..., :3] - base[..., :3]).max(-1)
    m = np.zeros(d.shape, bool)
    m[y0:y1, x0:x1] = d[y0:y1, x0:x1] > DIFF_T
    m = ndi.binary_opening(m, structure=np.ones((2, 2)))
    lab, n = ndi.label(m)
    if n:
        sizes = ndi.sum(m, lab, range(1, n + 1))
        m = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= MIN_BLOB])
    m = ndi.binary_closing(m, structure=np.ones((5, 5)))
    m = ndi.binary_fill_holes(m)
    core = m
    ring = ndi.binary_dilation(m, iterations=2) & ~m           # soft edge: partially-changed pixels
    out = np.zeros(var.shape, np.uint8)
    out[..., :3] = var[..., :3].clip(0, 255)
    alpha = np.zeros(d.shape)
    alpha[core] = 255
    alpha[ring] = np.clip(d[ring] / DIFF_T, 0, 1) * 255
    out[..., 3] = alpha.astype(np.uint8)
    return out


def crop_save(layer, path):
    ys, xs = np.where(layer[..., 3] > 0)
    if not len(ys):
        return None
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    Image.fromarray(layer[y0:y1, x0:x1]).save(path, optimize=True)
    return {'x': int(x0), 'y': int(y0), 'w': int(x1 - x0), 'h': int(y1 - y0)}


def lum_range(layer):
    m = layer[..., 3] > 200
    lum = layer[..., :3].astype(float) @ np.array([0.299, 0.587, 0.114])
    v = lum[m]
    return [round(float(np.percentile(v, 2)), 1), round(float(np.percentile(v, 98)), 1)] if len(v) else [0, 255]


def closest_ramp(layer, ramps):
    m = layer[..., 3] > 200
    med = np.median(layer[..., :3][m], 0) if m.any() else np.array([128, 128, 128])
    def dist(r):
        c = np.array([int(r[3][i:i + 2], 16) for i in (1, 3, 5)])
        return ((c - med) ** 2).sum()
    return min(ramps, key=lambda k: dist(ramps[k]))


def label(name):
    return name.replace('_', ' ').title()


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    img_dir = os.path.join(dst, 'img')
    os.makedirs(img_dir, exist_ok=True)
    files = {f.lower(): os.path.join(src, f) for f in os.listdir(src) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))}
    base_file = next((files[k] for k in files if re.fullmatch(r'base\.(png|jpe?g|webp)', k)), None)
    if not base_file:
        sys.exit('base.png is required')
    base = load(base_file)
    parts = {
        'version': 2, 'size': [SIZE, SIZE], 'crop': {'x': 90, 'y': 40, 'w': 200, 'h': 200},
        'note': 'Built by tools/canva_import.py from Canva exports. Parts are PNG layers at their x,y on the 500x500 canvas.',
        'ramps': {'hair': HAIR, 'gear': GEAR},
        'order': ['body', 'skin', 'number', 'captain', 'facialHair', 'hair', 'glasses', 'earring', 'hat'],
        # jersey number on the sleeve: centre point, rotation (degrees, clockwise) and pixel size, measured from the original art
        'number': {'color': '#d4511f', 'center': [106, 213], 'angle': 38, 'unit': 3},
        'slots': {
            'body': {'fixed': True, 'options': {}},
            'skin': {'label': 'Skin', 'options': {'default': {'label': 'Default', 'none': True}}},
            'hair': {'label': 'Hair', 'tint': 'hair', 'colorKey': 'hairColor', 'optional': True, 'noneLabel': 'Bald', 'options': {}},
            'facialHair': {'label': 'Facial Hair', 'tint': 'hair', 'colorKey': 'facialHairColor', 'optional': True, 'options': {}},
            'hat': {'label': 'Hat', 'tint': 'gear', 'colorKey': 'hatColor', 'optional': True, 'options': {}},
            'glasses': {'label': 'Glasses', 'optional': True, 'options': {}},
            'earring': {'label': 'Earring', 'optional': True, 'options': {}},
            'captain': {'fixed': True, 'options': {}},
        },
    }
    S = parts['slots']
    body = remove_background(base)
    S['body']['options']['skater'] = dict(src='img/body_skater.png', **crop_save(body, os.path.join(img_dir, 'body_skater.png')), label='Skater')
    print('body: skater')
    for k, path in sorted(files.items()):
        stem = os.path.splitext(k)[0]
        if stem == 'base':
            continue
        if stem == 'goalie_base':
            g = remove_background(load(path))
            S['body']['options']['goalie'] = dict(src='img/body_goalie.png', **crop_save(g, os.path.join(img_dir, 'body_goalie.png')), label='Goalie')
            print('body: goalie')
            continue
        m = re.fullmatch(r'(skin|hair|beard|hat|glasses|earring|captain)(?:_(.+))?', stem)
        if not m:
            print(f'skipped {k} (unknown name)')
            continue
        kind, name = m.group(1), (m.group(2) or m.group(1))
        name = re.sub(r'[^a-z0-9]+', '_', name).strip('_')
        layer = diff_layer(base, load(path), REGIONS[kind])
        out_name = f'{kind}_{name}.png'
        box = crop_save(layer, os.path.join(img_dir, out_name))
        if not box:
            print(f'skipped {k}: no change from base found')
            continue
        part = dict(src='img/' + out_name, **box, label=label(name))
        slot = SLOT_OF[kind]
        if kind in ('hair', 'beard'):
            part['lum'] = lum_range(layer); part['native'] = 'brown'
        if kind == 'hat':
            part['lum'] = lum_range(layer); part['native'] = closest_ramp(layer, GEAR)
            part['clipHairAbove'] = int(box['y'] + box['h'] * 0.75)   # hair is hidden under the crown of the hat
        S[slot]['options']['C' if kind == 'captain' else name] = part
        print(f'{slot}: {name}  ({box["w"]}x{box["h"]} at {box["x"]},{box["y"]})')
    json.dump(parts, open(os.path.join(dst, 'parts.json'), 'w'), indent=1)
    print('wrote', os.path.join(dst, 'parts.json'))


if __name__ == '__main__':
    main()
