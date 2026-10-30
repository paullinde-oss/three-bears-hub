# Featureless head base (boxy 3/4 view, facing right) as skin shade levels 0..4, -1 transparent
import numpy as np
HL = {(y, x) for y in range(15, 19) for x in range(44, 48)} | {(19, 45), (19, 46)} | {(y, x) for y in range(28, 31) for x in (46, 47)}
def build():
    L = np.full((100, 100), -1, int)
    spans = {12:(36,44),13:(34,46),14:(32,48),15:(31,49),16:(30,50)}
    for y in range(17, 34): spans[y] = (30, 50)
    spans.update({34:(31,50),35:(33,50),36:(35,49),37:(37,49),38:(39,48),39:(41,47)})
    for y,(a,b) in spans.items(): L[y, a:b+1] = 3
    for y in range(24, 32): L[y, 28:30] = 3                     # ear
    for y,(a,b) in {35:(32,34),36:(33,36),37:(33,38),38:(34,40),39:(35,40),40:(35,40),41:(36,40),42:(36,39),43:(37,39)}.items():
        L[y, a:b+1] = np.where(L[y, a:b+1] < 0, 2, L[y, a:b+1])  # neck
    mask = L >= 0
    edge = np.zeros_like(mask)
    for y in range(1, 99):
        for x in range(1, 99):
            if mask[y, x] and not (mask[y-1,x] and mask[y+1,x] and mask[y,x-1] and mask[y,x+1]): edge[y, x] = True
    edge[40:45] = False                                         # neck bottom hidden by collar
    for y in range(100):
        for x in range(100):
            if not mask[y, x]: continue
            if x <= 33 and y >= 19: L[y, x] = 2                 # side of head by the ear
            elif x == 34 and 22 <= y <= 34: L[y, x] = 2
            if (y, x) in HL: L[y, x] = 4                        # highlights
            if x == 49 and 18 <= y <= 34: L[y, x] = 3
    for y in range(24, 32): L[y, 28] = 2; L[y, 29] = 2
    for (x, y) in [(29,26),(29,27),(29,28),(29,29),(30,27),(30,28)]: L[y, x] = 1   # inner ear
    for (x, y) in [(36,34),(37,35),(36,35),(38,36),(37,36)]: L[y, x] = 2   # jaw line
    for x in range(38, 50):                                      # under-jaw shading
        if mask[37, x] and x < 44: L[37, x] = 2
        if mask[38, x]: L[38, x] = 2
    for y in range(36, 44):                                      # neck in shadow
        for x in range(32, 41):
            if mask[y, x] and (y >= 38 or x <= 36): L[y, x] = 1
    L[edge] = 0
    return L
def with_nose(L):
    for (x, y, v) in [(45,27,2),(45,28,2),(44,29,2),(45,29,2),(43,30,2),(44,30,1)]: L[y, x] = v
    return L
if __name__ == '__main__':
    np.save("head_levels.npy", with_nose(build()))
