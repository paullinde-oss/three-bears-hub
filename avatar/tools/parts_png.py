#!/usr/bin/env python3
"""Move avatar parts between parts.json and PNG files, so parts can be drawn in any image editor.

  Export a part to a PNG (100x100, transparent background):
    python3 parts_png.py export ../parts.json hair crew crew.png

  Import a PNG as a new or replacement part:
    python3 parts_png.py import ../parts.json hair pompadour pompadour.png

PNG rules (see README.md):
  * Canvas is 100x100 (or an exact multiple like 500x500, which is shrunk by sampling block centres).
    Draw the part in the same position it sits on the body; use the exported body/head PNGs as a guide layer.
  * Transparent pixels are ignored.
  * Pure greys at exactly these values are recoloured by the slot's colour (hair colour, skin tone, ...):
        0 = outline/darkest, 64 = shadow, 128 = mid, 191 = base, 255 = highlight
  * Any other colour is drawn exactly as-is (eye whites, teeth, metal, logos...).
Requires Pillow (pip install pillow).
"""
import json, sys
from PIL import Image

FIXED_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&*+<=>?@^~'
LEVELS = {0: '0', 64: '1', 128: '2', 191: '3', 255: '4'}
LEVEL_VALUES = [0, 64, 128, 191, 255]


def load_png(path, size):
    im = Image.open(path).convert('RGBA')
    if im.size != tuple(size):
        fx, fy = im.width / size[0], im.height / size[1]
        if fx != int(fx) or fy != int(fy):
            sys.exit(f'{path}: size {im.size} must be {size} or an exact multiple of it')
        # sample the centre of each block so pixel-art edges stay crisp
        px = im.load()
        out = Image.new('RGBA', tuple(size))
        for y in range(size[1]):
            for x in range(size[0]):
                out.putpixel((x, y), px[int((x + .5) * fx), int((y + .5) * fy)])
        im = out
    return im


def png_to_part(path, size):
    im = load_png(path, size)
    px = im.load()
    pts = [(x, y) for y in range(size[1]) for x in range(size[0]) if px[x, y][3] >= 128]
    if not pts:
        sys.exit(f'{path}: image is empty')
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    pal, rows = [], []
    for y in range(y0, y1 + 1):
        row = ''
        for x in range(x0, x1 + 1):
            r, g, b, a = px[x, y]
            if a < 128:
                row += '.'
            elif r == g == b and r in LEVELS:
                row += LEVELS[r]
            else:
                h = '#%02x%02x%02x' % (r, g, b)
                if h not in pal:
                    pal.append(h)
                if len(pal) > len(FIXED_CHARS):
                    sys.exit(f'{path}: too many fixed colours (max {len(FIXED_CHARS)})')
                row += FIXED_CHARS[pal.index(h)]
        rows.append(row)
    part = {'x': x0, 'y': y0, 'rows': rows}
    if pal:
        part['pal'] = pal
    return part


def part_to_png(part, size, path):
    im = Image.new('RGBA', tuple(size), (0, 0, 0, 0))
    pal = part.get('pal', [])
    for j, row in enumerate(part['rows']):
        for i, ch in enumerate(row):
            if ch == '.':
                continue
            if ch in '01234':
                v = LEVEL_VALUES[int(ch)]
                c = (v, v, v, 255)
            else:
                h = pal[FIXED_CHARS.index(ch)]
                c = (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), 255)
            im.putpixel((part['x'] + i, part['y'] + j), c)
    im.save(path)


def main():
    if len(sys.argv) != 6 or sys.argv[1] not in ('export', 'import'):
        sys.exit(__doc__)
    cmd, parts_path, slot, name, png = sys.argv[1:]
    parts = json.load(open(parts_path))
    if slot not in parts['slots']:
        sys.exit(f'unknown slot {slot}; slots: {", ".join(parts["slots"])}')
    opts = parts['slots'][slot].setdefault('options', {})
    if cmd == 'export':
        if name not in opts:
            sys.exit(f'no part {slot}/{name}; options: {", ".join(opts)}')
        part_to_png(opts[name], parts['size'], png)
        print(f'wrote {png}')
    else:
        part = png_to_part(png, parts['size'])
        existed = name in opts
        part['label'] = opts.get(name, {}).get('label') or name.replace('_', ' ').title()
        opts[name] = part
        json.dump(parts, open(parts_path, 'w'), separators=(',', ':'))
        print(f'{"replaced" if existed else "added"} {slot}/{name}')


if __name__ == '__main__':
    main()
