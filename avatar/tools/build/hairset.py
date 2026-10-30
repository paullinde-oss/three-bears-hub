# Final hair catalogue: extract, apply per-style cleanup, save level arrays
import sys; sys.path.insert(0, 'tools')
import numpy as np
from extract import classify
HAIRSET = [('buzz',0),('swept',2),('messy',3),('textured',4),('slick',5),('crew',7),
           ('wavy',9),('short',10),('curly_short',13),('side_part',14),('mullet',16),('curly',17)]
LONG = {'messy', 'mullet', 'wavy', 'curly'}
def hair(name, src):
    L = classify(src, 'hair')
    L[18:, 51:] = -1                      # nothing right of the face edge below the hairline
    L[:, 54:] = -1
    if name not in LONG:
        L[24:33, 26:34] = -1              # keep the ear visible
    return L
if __name__ == '__main__':
    import os; os.makedirs('parts/hair', exist_ok=True)
    for name, src in HAIRSET:
        np.save(f'parts/hair/{name}.npy', hair(name, src))
    print('saved', len(HAIRSET))
