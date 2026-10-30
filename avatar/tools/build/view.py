# Render a 100px pixel image zoomed with a coordinate grid, for inspection.
from PIL import Image, ImageDraw
import sys
def view(img, out, box=(0,0,100,100), S=10, grid=5):
    img = img.convert('RGBA').crop(box)
    w, h = img.size
    bg = Image.new('RGBA', (w*S, h*S), (255,255,255,255))
    # checkerboard so transparency is visible
    d = ImageDraw.Draw(bg)
    for y in range(h):
        for x in range(w):
            if (x+y) % 2: d.rectangle([x*S, y*S, x*S+S-1, y*S+S-1], fill=(228,228,236,255))
    bg.alpha_composite(img.resize((w*S, h*S), Image.NEAREST))
    pad = 22
    out_im = Image.new('RGB', (w*S+pad, h*S+pad), 'white')
    out_im.paste(bg.convert('RGB'), (pad, pad))
    d = ImageDraw.Draw(out_im)
    for i in range(0, w+1):
        X = pad + i*S
        if (box[0]+i) % grid == 0:
            d.line([X, pad, X, pad+h*S], fill=(255,0,180), width=1)
            d.text((X+1, 2), str(box[0]+i), fill='black')
    for j in range(0, h+1):
        Y = pad + j*S
        if (box[1]+j) % grid == 0:
            d.line([pad, Y, pad+w*S, Y], fill=(255,0,180), width=1)
            d.text((1, Y+1), str(box[1]+j), fill='black')
    out_im.save(out)
if __name__ == '__main__':
    box = tuple(map(int, sys.argv[3].split(','))) if len(sys.argv) > 3 else (0,0,100,100)
    S = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    view(Image.open(sys.argv[1]), sys.argv[2], box, S)
