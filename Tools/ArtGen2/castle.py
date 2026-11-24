"""Castle walls that read as real fortifications (replace the stacked castle_wall blocks).

  python castle.py -> Assets/Art/World/Structures/fort_wall_h.png   (32x56) horizontal run, 2 tiles wide:
                                                                   rear parapet, walkway, front merlons, ashlar face,
                                                                   arrow slit, plinth and moss
                      Assets/Art/World/Structures/fort_wall_v.png   (32x32) vertical run seen from above, tiles vertically:
                                                                   walkway between two parapets, cast shadow
                      Assets/Art/World/Structures/fort_bastion.png  (48x84) square corner / gate tower: crenellated
                                                                   platform, flag, ashlar face with slits and a banner
                      Documentation/CharacterPreviews/castle.png    preview of a fort corner
Same stone ramp as castle_tower.png, light from the top-left.
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'Assets', 'Art', 'World', 'Structures')
PREV = os.path.join(ROOT, 'Documentation', 'CharacterPreviews')


def hx(s, a=255):
    s = s.lstrip('#'); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


OL = hx('#161a2a')
S = [hx('#262b44'), hx('#3c4258'), hx('#5a6988'), hx('#6c7c9d'), hx('#8e9ab4'), hx('#b4bfd2')]     # stone dark -> light
MORTAR = hx('#2e3348')
MOSS = [hx('#2a4a2c'), hx('#3e6a3a'), hx('#5a8a46')]
SLIT = hx('#0c0e18')
RED = [hx('#5a1420'), hx('#9e2835'), hx('#c84a4a')]
GOLD = hx('#feae34')
WOOD = hx('#743f39')


def blank(w, h):
    return np.zeros((h, w, 4), np.uint8)


def ashlar(a, x0, y0, x1, y1, seed=1, course=5, block=8, top_light=True):
    """front face of cut stone: courses of blocks with mortar, lit top-left, darker toward the ground"""
    rng = np.random.default_rng(seed)
    H = y1 - y0
    for y in range(y0, y1):
        k = (y - y0) // course
        off = (k % 2) * (block // 2)
        dark = (y - y0) / max(1, H)
        for x in range(x0, x1):
            in_row = (y - y0) % course
            in_blk = (x - x0 + off) % block
            if in_row == course - 1 or in_blk == block - 1:
                c = MORTAR
            else:
                lvl = 3 if dark < .35 else 2 if dark < .8 else 1
                if in_row == 0 and top_light: lvl += 1                     # lit top edge of each block
                if in_blk == 0: lvl += 1 if lvl < 4 else 0                # lit left edge
                if in_blk == block - 2: lvl -= 1                         # shaded right edge
                # per-block tone variation
                bid = (k * 31 + (x - x0 + off) // block * 7) % 5
                if bid == 0: lvl -= 1
                elif bid == 3 and rng.random() < .9: lvl += 0
                c = S[max(0, min(5, lvl))]
            a[y, x] = c
    # chips and cracks
    for _ in range((x1 - x0) * H // 60):
        x, y = int(rng.integers(x0, x1)), int(rng.integers(y0, y1))
        a[y, x] = S[1]


def moss(a, x0, x1, y, rng, depth=3):
    for x in range(x0, x1):
        h = int(rng.integers(0, depth + 1))
        for k in range(h):
            if a[y - k, x, 3]: a[y - k, x] = MOSS[min(2, h - k - 1)]


def outline(a):
    m = a[:, :, 3] > 0
    o = np.zeros_like(m)
    o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
    o &= ~m
    a[o] = OL


def merlons(a, x0, x1, y0, h, period=8, width=5, start=1):
    """front parapet: merlons (with lit caps) and crenels showing the walkway behind"""
    for x in range(x0, x1):
        p = (x - x0 - start) % period
        if p < width:
            for y in range(y0, y0 + h):
                lvl = 5 if y == y0 else 4 if y == y0 + 1 else 3 if p > 0 else 4
                if p == width - 1: lvl -= 1
                a[y, x] = S[max(0, lvl)]


def wall_h():
    W, H = 32, 56
    a = blank(W, H)
    rng = np.random.default_rng(3)
    # rear parapet (seen over the walkway)
    for x in range(W):
        a[4:7, x] = S[3] if x % 8 < 5 else S[2]
        a[4, x] = S[4] if x % 8 < 5 else S[3]
    a[2:4, :] = 0
    for x in range(W):
        if x % 8 < 5: a[2:4, x] = S[3]; a[2, x] = S[4]
    # walkway flags
    for y in range(7, 13):
        for x in range(W):
            a[y, x] = S[2] if (x + (y // 3) * 3) % 6 else S[1]
    a[7, :] = S[1]
    # front merlons
    a[13:21, :] = 0
    for x in range(W):
        a[13:21, x] = S[1]                                  # crenel floor (shadowed walkway)
    merlons(a, 0, W, 11, 10, period=8, width=5, start=1)
    # string course (thin ledge under the parapet)
    a[21, :] = S[4]; a[22, :] = S[2]
    # front face
    ashlar(a, 0, 23, W, H - 3, seed=5)
    # arrow slit
    for y in range(31, 39):
        a[y, 15:17] = SLIT
    a[30, 15:17] = S[1]; a[39, 14:18] = S[4]
    # plinth (wider batter at the foot) + moss
    a[H - 3:H, :] = S[1]; a[H - 3, :] = S[2]
    moss(a, 0, W, H - 3, rng)
    outline(a)
    a[0:2] = 0
    return a


def wall_v():
    W, H = 32, 32
    a = blank(W, H)
    # ground shadow cast to the east
    a[:, 26:31] = (10, 12, 24, 90)
    # parapet blocks on both edges, walkway between
    for y in range(H):
        for x in range(6, 26):
            a[y, x] = S[2] if (y // 4 + x // 6) % 2 else S[3] if x < 16 else S[2]
        a[y, 10] = S[1]; a[y, 21] = S[1]                     # walkway edges
    for y in range(H):
        on = (y % 8) < 5
        for x in range(6, 10):
            a[y, x] = S[4] if on and x == 6 else S[3] if on else S[2]
        for x in range(22, 26):
            a[y, x] = S[3] if on and x < 25 else S[2] if on else S[1]
        if on and y % 8 == 0:
            a[y, 6:10] = S[5]; a[y, 22:26] = S[4]
    for y in range(0, H, 8):
        a[y + 5, 6:10] = S[1]; a[y + 5, 22:26] = S[0]
    # outline only on the long sides (it tiles vertically)
    a[:, 5] = OL; a[:, 26] = OL
    return a


def bastion():
    W, H = 48, 84
    a = blank(W, H)
    rng = np.random.default_rng(9)
    top, face = 8, 30
    # platform floor
    for y in range(top + 4, face - 6):
        for x in range(4, W - 4):
            a[y, x] = S[2] if (x // 5 + y // 4) % 2 else S[1]
    # rear + side parapets
    for x in range(2, W - 2):
        on = (x - 2) % 8 < 5
        a[top:top + 4, x] = S[3] if on else S[2]
        if on: a[top, x] = S[4]
    for y in range(top, face - 4):
        on = (y - top) % 7 < 4
        for x in (2, 3, 4): a[y, x] = S[4] if on and x == 2 else S[3] if on else S[2]
        for x in (W - 5, W - 4, W - 3): a[y, x] = S[2] if on else S[1]
    # flag pole + flag
    for y in range(0, top + 8): a[y, 23] = WOOD
    for y in range(1, 8):
        for x in range(24, 24 + 11 - (y % 2)):
            a[y, x] = RED[1] if y > 1 else RED[2]
        a[y, 24 + 10 - (y % 2)] = RED[0]
    a[4, 28:30] = GOLD
    # front merlons, ledge
    a[face - 6:face + 2, 2:W - 2] = S[1]
    merlons(a, 2, W - 2, face - 8, 10, period=8, width=5, start=0)
    a[face + 2, 1:W - 1] = S[4]; a[face + 3, 1:W - 1] = S[2]
    # machicolation corbels
    for x in range(3, W - 3, 4):
        a[face + 4:face + 6, x:x + 2] = S[3]; a[face + 6, x:x + 2] = S[1]
    # face (slightly wider at the foot: a batter)
    ashlar(a, 3, face + 4, W - 3, H - 8, seed=11, course=5, block=9)
    for k, y in enumerate(range(H - 8, H - 2)):
        ashlar(a, 3 - k // 2 - 1, y, W - 3 + k // 2 + 1, y + 1, seed=12 + k, course=5, block=9, top_light=False)
    a[H - 2:H, 0:W] = S[1]; a[H - 2, 0:W] = S[2]
    # two slits + a hanging banner
    for (sx, sy) in ((12, face + 14), (34, face + 14)):
        a[sy:sy + 9, sx:sx + 2] = SLIT; a[sy + 9, sx - 1:sx + 3] = S[4]
    for y in range(face + 8, face + 30):
        w0, w1 = 19, 29
        if y > face + 26: w0, w1 = 19 + (y - face - 26) * 1, 29 - (y - face - 26) * 1
        for x in range(w0, w1):
            a[y, x] = RED[2] if x == w0 else RED[0] if x == w1 - 1 else RED[1]
    for y in range(face + 13, face + 20):
        a[y, 23:25] = GOLD
    a[face + 15, 21:27] = GOLD
    a[face + 7, 18:30] = WOOD
    moss(a, 0, W, H - 2, rng, 4)
    outline(a)
    return a


def save(a, name):
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(a, 'RGBA').save(os.path.join(OUT, name))


def preview():
    h, v, b = wall_h(), wall_v(), bastion()
    W, H = 200, 190
    img = Image.new('RGBA', (W, H), (176, 128, 84, 255))
    I = lambda arr: Image.fromarray(arr, 'RGBA')
    # left vertical run going down from a corner bastion, then a horizontal run to the right
    for k in range(4):
        img.alpha_composite(I(v), (8, 30 + 32 * k - 38))
    for k in range(4):
        img.alpha_composite(I(h), (48 + 32 * k, 100))
    img.alpha_composite(I(b), (0, 72))
    img.alpha_composite(I(b), (176, 72))
    os.makedirs(PREV, exist_ok=True)
    img.resize((W * 3, H * 3), Image.NEAREST).save(os.path.join(PREV, 'castle.png'))


if __name__ == '__main__':
    save(wall_h(), 'fort_wall_h.png')
    save(wall_v(), 'fort_wall_v.png')
    save(bastion(), 'fort_bastion.png')
    preview()
    print('ok')
