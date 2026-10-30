import numpy as np
from PIL import Image
SKIN = {
  'light':  [(58,30,28),(160,100,80),(212,150,115),(240,186,142),(252,214,176)],
  'tan':    [(52,26,20),(140,82,58),(190,124,88),(218,152,108),(236,182,136)],
  'brown':  [(40,20,16),(102,58,40),(148,92,62),(178,118,82),(204,146,104)],
  'dark':   [(26,14,12),(64,36,26),(96,58,40),(124,80,56),(150,104,74)],
}
def tint(levels, ramp):
    out = np.zeros(levels.shape + (4,), np.uint8)
    for i, c in enumerate(ramp):
        m = levels == i
        out[m, :3] = c; out[m, 3] = 255
    return out
def over(dst, src):
    m = src[..., 3] > 0
    dst[m] = src[m]
    return dst
def body_layer():
    return np.asarray(Image.open('parts/body.png').convert('RGBA')).copy()
if __name__ == '__main__':
    L = np.load('head_levels.npy')
    tiles = []
    for name, ramp in SKIN.items():
        im = body_layer(); over(im, tint(L, ramp)); tiles.append(im)
    row = np.concatenate(tiles, 1)
    Image.fromarray(row).resize((row.shape[1]*4, row.shape[0]*4), Image.NEAREST).save('preview.png')
