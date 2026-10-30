# Collar overlay (fixed colours): orange V-trim drawn over the neck, jersey black outside the V
import numpy as np, sys
sys.path.insert(0, 'tools')
from head import build
O, o, K = (191, 57, 25), (137, 39, 23), (22, 18, 26)
left  = {35:31, 36:31, 37:32, 38:32, 39:33, 40:33, 41:34, 42:35, 43:35, 44:36}
right = {40:43, 41:42, 42:40, 43:39, 44:38}
head = build() >= 0
C = np.zeros((100, 100, 4), np.uint8)
def put(x, y, c): C[y, x, :3] = c; C[y, x, 3] = 255
for y, x in left.items():
    put(x, y, O)
    if y <= 36: put(x, y, o)
    for xx in range(26, x):
        if head[y, xx]: put(xx, y, K)
for y, x in right.items():
    put(x, y, O)
    if y == 41: put(41, 41, O)
    for xx in range(x+1, 53):
        if head[y, xx]: put(xx, y, K)
put(37, 44, O)
for y in range(45, 47):
    for xx in range(26, 53):
        if head[y, xx]: put(xx, y, K)
np.save('collar.npy', C)
