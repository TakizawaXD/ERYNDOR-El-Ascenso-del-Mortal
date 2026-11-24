"""Rebuilds a scene like the user's reference with the new kit, side by side with the reference."""
import os, sys
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ArtGen'))
from tiles import MASKS, DIRS, canon
from kit import OUT
T = 16
def L(rel): return Image.open(os.path.join(OUT, rel)).convert('RGBA')
def cell(s, i, w=16, h=16):
    cols = s.width // w; return s.crop(((i % cols) * w, (i // cols) * h, (i % cols) * w + w, (i // cols) * h + h))
def auto(img, H, W, pred, sheet, variants=0):
    for y in range(H):
        for x in range(W):
            if not pred(x, y): continue
            m = 0
            for b, (dx, dy) in DIRS.items():
                nx, ny = x + dx, y + dy
                if not (0 <= nx < W and 0 <= ny < H) or pred(nx, ny): m |= b
            i = MASKS.index(canon(m))
            if i == 46 and variants: i = [46, 47, 46, 48, 49, 46, 50, 51][(x * 7 + y * 13) % 8]
            img.alpha_composite(cell(sheet, i), (x * T, y * T))
MAP = [
 "gggggggggggggggggggggggggggggg",
 "..............gggggggggggg....",
 "gggggggggggggggggggggggggggggg",
 "ggggggggggggggggggwwwwwggggggg",
 "gggggggggggggggggwwwwwwwwggggg",
 "gggggffffgggggggggwwwwwwwggggg",
 "ggggffffffgggggggggwwwwgggggg.",
 "ggggfffffgggggggggggggggggg...",
 "gggggggggggggggggggggggggg....",
 "gggggggggggggggggggggggggg....",
 "ggwwwwwgggggggggggggggggggg...",
 "gwwwwwwwggggggggggggggggggggg.",
 "ggwwwwwwgggggggggggggggggggggg",
 "gggggggggggggggggggggggggggggg",
 "..............................",
 "gggggggggggggggggggggggggggggg",
]
H, W = len(MAP), len(MAP[0])
img = Image.new('RGBA', (W * T, H * T))
sand = L('Tilesets/world_sand_fill_16x16.png')
for y in range(H):
    for x in range(W): img.alpha_composite(cell(sand, (x * 3 + y) % 4 if (x + y) % 3 == 0 else 0), (x * T, y * T))
t = lambda x, y: MAP[y][x]
auto(img, H, W, lambda x, y: t(x, y) in 'gwf', L('Tilesets/world_grass_blob_16x16.png'), variants=1)
auto(img, H, W, lambda x, y: t(x, y) == 'f', L('Tilesets/world_forestfloor_blob_16x16.png'))
auto(img, H, W, lambda x, y: t(x, y) == 'w', L('Tilesets/world_water_blob_f0_16x16.png'))
def put(rel, x, y, i=None, w=16, h=16):
    s = L(rel) if i is None else cell(L(rel), i, w, h)
    img.alpha_composite(s, (int(x - s.width / 2), int(y - s.height)))
for (x, y) in [(40, 120), (330, 60), (130, 150), (420, 200), (60, 300), (210, 230)]: put('Nature/tree_oak.png', x, y)
put('Nature/tree_oak_b.png', 260, 150)
for (x, y) in [(150, 200), (180, 230), (120, 260), (230, 280), (100, 220), (270, 250)]: put('Nature/plants_16x16.png', x, y, 0)
put('Nature/plants_16x16.png', 400, 120, 1); put('Nature/plants_16x16.png', 350, 260, 2); put('Nature/plants_16x16.png', 450, 290, 3)
put('Nature/log.png', 350, 210); put('Nature/stump.png', 450, 150); put('Nature/rock_big.png', 400, 70)
put('Nature/rock_water.png', 330, 80); put('Nature/lilypads_16x16.png', 310, 70, 0); put('Nature/lilypads_16x16.png', 370, 95, 1)
put('Nature/cattails.png', 300, 104); put('Nature/lilypads_16x16.png', 60, 185, 1); put('Nature/rock_water.png', 90, 195)
for x in range(40, 120, 16): put('Nature/fence_16x16.png', x, 225, 1)
for x in range(200, 280, 16): put('Nature/fence_16x16.png', x, 30, 1)
put('Nature/bushes_20x18.png', 470, 250, 1, 20, 18); put('Nature/tree_pine.png', 470, 110)
ref = Image.open(sys.argv[2]).convert('RGBA')
img = img.crop((0, 0, 240, 300)).resize((480, 600), Image.NEAREST)   # same 2x zoom as the reference
out = Image.new('RGBA', (img.width + ref.width + 10, max(img.height, ref.height)), (40, 40, 40, 255))
out.alpha_composite(ref, (0, 0)); out.alpha_composite(img, (ref.width + 10, 0))
out.save(sys.argv[1])
