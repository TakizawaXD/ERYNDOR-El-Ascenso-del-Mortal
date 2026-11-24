"""Small extra sprites the game needs (same palette): blob shadow, arrow projectile, spit projectile."""
import os, sys
from PIL import Image
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
def save(im, name): im.save(os.path.join(OUT, name))
# soft ground shadow (black, alpha like the woods pack shadows)
sh = Image.new('RGBA', (16, 8))
for y in range(8):
    for x in range(16):
        d = ((x + .5 - 8) / 6.5) ** 2 + ((y + .5 - 4) / 2.6) ** 2
        if d <= 1: sh.putpixel((x, y), (0, 0, 0, 55 if d > .55 else 70))
save(sh, 'shadow_blob.png')
# arrow (horizontal, pointing right) - colours from Soldier_Attack03 / Arrow01
A = {'a': (0, 0, 0, 255), 'h': (0xc9, 0xc0, 0xbe, 255), 'n': (0xb1, 0x9e, 0x9a, 255), 'Y': (0xff, 0xf0, 0xef, 255), 'X': (0x22, 0x02, 0x1d, 255), 'Z': (0x5e, 0x1e, 0x13, 255)}
rows = ["aa.........a....",
        "XXahhhhhhhhnYa..",
        "aa.........a....",]
ar = Image.new('RGBA', (16, 16))
for j, r in enumerate(rows):
    for i, c in enumerate(r):
        if c != '.': ar.putpixel((i, 7 + j), A[c])
save(ar, 'proj_arrow.png')
# spit blob: 2 frames, white like Blood Monster_A_Attack02 projectile
W = [(0xf4, 0xed, 0xea, 255), (0xd9, 0xd8, 0xd8, 255), (0xc0, 0xbf, 0xbf, 255)]
sp = Image.new('RGBA', (16, 8))
for f in range(2):
    for y in range(8):
        for x in range(8):
            dx, dy = x + .5 - 4.5, y + .5 - 4
            r = (dx * dx) / (3.2 + f * .4) ** 2 + (dy * dy) / (2.6 - f * .3) ** 2
            if r <= 1:
                c = W[0] if r < .35 else W[1] if r < .75 else W[2]
                sp.putpixel((f * 8 + x, y), c)
    sp.putpixel((f * 8 + 1, 3 + f), W[2]); sp.putpixel((f * 8, 4), W[2])
save(sp, 'proj_spit_anim_8x8.png')
print('ok')
