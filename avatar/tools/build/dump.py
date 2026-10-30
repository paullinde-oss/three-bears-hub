# Print a region of a 100px image as a letter map (k-means palette), plus the palette.
import numpy as np, sys
from PIL import Image
def dump(a, box, k=14, seed=0):
    x0,y0,x1,y1 = box
    reg = a[y0:y1, x0:x1].reshape(-1,3).astype(float)
    rng = np.random.default_rng(seed)
    C = reg[rng.choice(len(reg), k, replace=False)]
    for _ in range(30):
        lab = ((reg[:,None,:]-C[None])**2).sum(-1).argmin(1)
        for i in range(k):
            if (lab==i).any(): C[i] = reg[lab==i].mean(0)
    # sort clusters by luminance; letters a(dark)..; white-ish background -> '.'
    lum = C @ [0.299,0.587,0.114]
    order = np.argsort(lum); rank = np.empty(k,int); rank[order] = np.arange(k)
    chars = 'abcdefghijklmnopqrstuvwxyz'
    lines = []
    lab = lab.reshape(y1-y0, x1-x0)
    hdr = '    ' + ''.join(str((x0+i)%10) for i in range(x1-x0))
    lines.append(hdr)
    for j,row in enumerate(lab):
        s = ''.join('.' if lum[c] > 235 else chars[rank[c]] for c in row)
        lines.append(f'{y0+j:3d} {s}')
    pal = [f'{chars[rank[i]]}={tuple(int(v) for v in C[i])}' for i in order]
    return '\n'.join(lines) + '\n' + '  '.join(pal)
if __name__ == '__main__':
    s = np.load(sys.argv[1]); i = int(sys.argv[2]); box = tuple(map(int, sys.argv[3].split(',')))
    print(dump(s[i], box, int(sys.argv[4]) if len(sys.argv)>4 else 14))
