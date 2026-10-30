# Hand-drawn face features. Digits 0-4 = tinted shade levels, letters = fixed colours, '.' = transparent.
import numpy as np
FIX = {'X': (24, 16, 22), 'W': (238, 234, 228), 'T': (250, 248, 242), 'R': (176, 82, 74)}
def draw(rows, x0, y0, out=None):
    out = np.zeros((100, 100, 4), np.uint8) if out is None else out
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == '.' or ch == ' ': continue
            x, y = x0 + i, y0 + j
            if ch.isdigit():
                v = (0, 64, 128, 191, 255)[int(ch)]; out[y, x] = (v, v, v, 255)
            else: out[y, x] = (*FIX[ch], 255)
    return out
#            x: 37  41  45  49
EYES = {
  'normal':  [".XXXXX..XXXX", ".XW20X..W20X"],
  'happy':   ["..XXX....XX.", ".X...X..X..X"],
  'narrow':  [".XXXXX..XXXX", "..X20X...20X"],
  'wide':    ["..XXX....XX.", ".XW20X..W20X", "..XXX....XX."],
}
EYES_POS = (37, 24)
BROWS = {
  'normal':  ["..1111...111", ".11111..1111"],
  'thick':   [".111111.1111", "1111111.1111", ".1.........."],
  'angry':   [".11.......11", "..1111..111.", "....11......"],
  'raised':  ["..111....11.", ".1...1..1..1"],
  'thin':    ["..1111...111", ".1.........."],
}
BROWS_POS = {'normal': (37, 21), 'thick': (37, 20), 'angry': (37, 20), 'raised': (37, 20), 'thin': (37, 21)}
MOUTHS = {
  'grin':    ["0000000", "0TTTTT0", ".11111."],
  'smile':   ["1.....1", ".00000.", "..111.."],
  'neutral': [".......", ".11111.", "......."],
  'smirk':   ["......1", ".00000.", "..11..."],
}
MOUTH_POS = (40, 32)
