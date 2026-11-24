"""Contact sheet: every PNG under given Art sub-folders on a grass/dirt backdrop, scaled up."""
import os, sys, glob
from PIL import Image, ImageDraw
from lib import ROOT

out = sys.argv[1]
subs = sys.argv[2:]
k = 4
files = []
for s in subs:
    files += sorted(glob.glob(os.path.join(ROOT, s, '**', '*.png'), recursive=True))
ims = [Image.open(f).convert('RGBA') for f in files]
W = 1400
x = y = 0; rowh = 0; pos = []
for im in ims:
    w, h = im.width * k, im.height * k
    if x + w > W and x > 0:
        x = 0; y += rowh + 24; rowh = 0
    pos.append((x, y)); x += w + 16; rowh = max(rowh, h)
H = y + rowh + 24
canvas = Image.new('RGBA', (max(W, 1), H), (89, 193, 53, 255))
d = ImageDraw.Draw(canvas)
for (px, py), im, f in zip(pos, ims, files):
    bg = Image.new('RGBA', im.size, (219, 164, 99, 255) if 'Water' in f or 'UI' in f else (89, 193, 53, 255))
    bg.alpha_composite(im)
    canvas.alpha_composite(bg.resize((im.width * k, im.height * k), Image.NEAREST), (px, py + 12))
    d.text((px, py), os.path.basename(f)[:60], fill=(0, 0, 0, 255))
canvas.save(out)
print(out, canvas.size)
