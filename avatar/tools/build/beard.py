# Procedural facial hair fitted to the canonical head. Returns shade levels (-1 transparent).
import numpy as np, sys
sys.path.insert(0, 'tools')
from head import build
HEAD = build() >= 0
def spans_mask(spans):
    m = np.zeros((100, 100), bool)
    for y, segs in spans.items():
        for a, b in (segs if isinstance(segs[0], tuple) else [segs]): m[y, a:b+1] = True
    return m
# regions (inclusive x spans per row)
SIDEBURN = {y: (34, 35) for y in range(24, 31)}
CHEEK_JAW = {30: (34, 37), 31: (34, 39), 32: (34, 49), 33: (34, 49), 34: (34, 49), 35: (35, 49), 36: (36, 48), 37: (37, 48), 38: (39, 47), 39: (41, 46)}
BELOW_CHIN = {40: (38, 46), 41: (39, 45), 42: (40, 44)}
MUSTACHE = {31: (41, 47), 32: (40, 47)}
CHIN = {35: (41, 46), 36: (40, 46), 37: (40, 46), 38: (40, 46), 39: (41, 45), 40: (42, 44)}
STRAP = {**{y: (34, 35) for y in range(24, 34)}, 34: (35, 37), 35: (36, 39), 36: (37, 48), 37: (38, 48), 38: (39, 47), 39: (41, 46)}
STYLES = {
    'stubble':  [SIDEBURN, CHEEK_JAW, MUSTACHE],
    'short':    [SIDEBURN, CHEEK_JAW, MUSTACHE],
    'full':     [SIDEBURN, CHEEK_JAW, MUSTACHE, BELOW_CHIN],
    'goatee':   [MUSTACHE, CHIN],
    'mustache': [MUSTACHE],
    'chinstrap':[STRAP],
}
def make(style, seed=7):
    m = np.zeros((100, 100), bool)
    for part in STYLES[style]: m |= spans_mask(part)
    if style != 'full': m &= HEAD
    rng = np.random.default_rng(seed)
    L = np.full((100, 100), -1, int)
    if style == 'stubble':
        noise = rng.random((100, 100))
        L[m & (noise < 0.45)] = 3
        L[m & (noise < 0.15)] = 2
        return L
    noise = rng.random((100, 100))
    L[m] = 2
    L[m & (noise < 0.30)] = 1
    L[m & (noise > 0.80)] = 3
    # top edge of cheeks lighter/sparser so it blends into skin
    for y in range(100):
        xs = np.where(m[y])[0]
        for x in xs:
            if not m[y-1, x] and y < 34 and noise[y, x] < 0.5: L[y, x] = 3
    # outline the outer (lower/left) silhouette
    for y in range(1, 99):
        for x in range(1, 99):
            if m[y, x] and (not m[y+1, x] or not m[y, x-1]) and y >= 34: L[y, x] = 0
    # short beard: trim below-chin outline; full beard: wavy bottom
    return L
