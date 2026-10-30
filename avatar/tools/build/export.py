# Export all avatar parts to avatar/parts.json (portable text pixel maps)
import sys, json; sys.path.insert(0, 'tools')
import numpy as np
from PIL import Image
import palettes as P
from feat import draw, EYES, EYES_POS, BROWS, BROWS_POS, MOUTHS, MOUTH_POS, FIX
from acc import cap, toque, GLASSES, EARRINGS, CAPTAIN, DIGITS
from beard import make as beard, STYLES as BEARDS
from hairset import HAIRSET
from head import build, with_nose
LEVEL_CHARS = '01234'
FIXED_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&*+<=>?@^~'
def hexc(c): return '#%02x%02x%02x' % tuple(int(v) for v in c[:3])
def from_levels(L):
    """level array (-1 transparent, 0..4 tinted) -> part"""
    ys, xs = np.where(L >= 0)
    if not len(ys): return None
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    rows = [''.join('.' if L[y, x] < 0 else LEVEL_CHARS[L[y, x]] for x in range(x0, x1+1)) for y in range(y0, y1+1)]
    return {'x': int(x0), 'y': int(y0), 'rows': rows}
def from_rgba(A):
    """RGBA array: pure grey (r=g=b) pixels at the 5 level values are tinted, everything else fixed colour"""
    a = A[..., 3] > 0
    ys, xs = np.where(a)
    if not len(ys): return None
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    pal, rows = [], []
    lv = {0: '0', 64: '1', 128: '2', 191: '3', 255: '4'}
    for y in range(y0, y1+1):
        r = ''
        for x in range(x0, x1+1):
            if not a[y, x]: r += '.'; continue
            R, G, B = map(int, A[y, x, :3])
            if R == G == B and R in lv: r += lv[R]; continue
            h = hexc((R, G, B))
            if h not in pal: pal.append(h)
            r += FIXED_CHARS[pal.index(h)]
        rows.append(r)
    assert len(pal) <= len(FIXED_CHARS), len(pal)
    part = {'x': int(x0), 'y': int(y0), 'rows': rows}
    if pal: part['pal'] = pal
    return part
def body_png(path):
    A = np.asarray(Image.open(path).convert('RGBA')).copy()
    g = (A[..., 0] == A[..., 1]) & (A[..., 1] == A[..., 2])
    A[g & (A[..., 3] > 0), 2] ^= 1          # body is never tinted: nudge accidental pure greys
    return from_rgba(A)
ramp = lambda d: {k: [hexc(c) for c in v] for k, v in d.items()}
labels = lambda k: k.replace('_', ' ').title()
parts = {
  'name': 'Three Bears avatar parts', 'version': 1, 'size': [100, 100],
  'crop': {'x': 18, 'y': 8, 'w': 40, 'h': 40},
  'note': "rows: '.' transparent, '0'-'4' shade levels tinted by the slot's colour ramp (dark->light), other chars index into pal",
  'ramps': {'skin': ramp(P.SKIN), 'hair': ramp(P.HAIR), 'eyes': ramp(P.EYES), 'gear': ramp(P.GEAR)},
  'order': ['body', 'number', 'captain', 'head', 'collar', 'eyes', 'facialHair', 'mouth', 'brows', 'earring', 'hair', 'glasses', 'hat'],
  'slots': {},
}
S = parts['slots']
S['body'] = {'label': 'Body', 'fixed': True, 'options': {'skater': body_png('parts/body.png'), 'goalie': body_png('parts/goalie_body.png')}}
S['head'] = {'label': 'Skin', 'tint': 'skin', 'options': {'default': from_levels(with_nose(build()))}}
S['collar'] = {'fixed': True, 'options': {'default': from_rgba(np.load('collar.npy'))}}
S['eyes'] = {'label': 'Eyes', 'tint': 'eyes', 'options': {k: from_rgba(draw(v, *EYES_POS)) for k, v in EYES.items()}}
S['brows'] = {'label': 'Eyebrows', 'tint': 'hair', 'options': {k: from_rgba(draw(v, *BROWS_POS[k])) for k, v in BROWS.items()}}
S['mouth'] = {'label': 'Mouth', 'tint': 'skin', 'options': {k: from_rgba(draw(v, *MOUTH_POS)) for k, v in MOUTHS.items()}}
S['facialHair'] = {'label': 'Facial Hair', 'tint': 'facialHair', 'optional': True, 'options': {k: from_levels(beard(k)) for k in BEARDS}}
S['hair'] = {'label': 'Hair', 'tint': 'hair', 'optional': True, 'noneLabel': 'Bald', 'options': {k: from_levels(np.load(f'parts/hair/{k}.npy')) for k, _ in HAIRSET}}
S['hat'] = {'label': 'Hat', 'tint': 'gear', 'optional': True, 'clipHairAbove': 21, 'options': {'cap': from_levels(cap()), 'toque': from_levels(toque())}}
S['glasses'] = {'label': 'Glasses', 'optional': True, 'options': {k: from_rgba(draw(v[0], *v[1])) for k, v in GLASSES.items()}}
S['earring'] = {'label': 'Earring', 'optional': True, 'options': {k.replace('earring_', ''): from_rgba(draw(v[0], *v[1])) for k, v in EARRINGS.items()}}
S['captain'] = {'fixed': True, 'options': {'C': from_rgba(draw(CAPTAIN[0], *CAPTAIN[1]))}}
S['number'] = {'fixed': True, 'digits': DIGITS, 'color': '#d64c1e', 'at': {'one': [21, 41], 'two': [19, 41]}, 'spacing': 4}
for k, v in S.items():
    for name, part in v.get('options', {}).items():
        part['label'] = labels(name)
import os; os.makedirs('out', exist_ok=True)
txt = json.dumps(parts, separators=(',', ':'))
open('out/parts.json', 'w').write(txt)
print('parts.json', len(txt) // 1024, 'KB')
