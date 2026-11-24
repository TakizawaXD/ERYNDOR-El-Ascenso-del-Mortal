"""Campsites, gathering spots and crafting icons, in the same cozy top-down style (kit.py palette, 1 px dark outlines).

  python camp.py ->  Assets/Art/World/Props/camp_tent.png          canvas tent (rest / sleep)
                     Assets/Art/World/Props/camp_bedroll.png       bedroll by the fire
                     Assets/Art/World/Props/camp_workbench.png     crafting table with tools, mortar and vials
                     Assets/Art/World/Props/camp_stash.png         storage chest (almacén)
                     Assets/Art/World/Props/camp_log.png           log bench
                     Assets/Art/World/Props/camp_rack.png          drying rack with herbs and meat
                     Assets/Art/World/Props/camp_firepit_anim_24x24.png   stone ring fire with cooking pot
                     Assets/Art/World/Props/gather_anim_16x16.png  gathering nodes (see GATHER), 2 frames each (idle, picked)
                     Assets/Art/UI/Icons/ui_materials_16x16.png    material + consumable icons (CraftDB icon index)
                     Documentation/Previews/camp_preview.png
"""
import math, os
from PIL import Image
from kit import C, P, hx, save, sheet

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OL = (24, 20, 37, 255)
SH = (9, 27, 21, 70)

P.update({k: hx(v) for k, v in dict(
    cv='#ead4aa', cv_md='#d8b98a', cv_dk='#b48a62', cv_ol='#5a3a2c',            # canvas
    rope='#c8a46a', pole='#743f39',
    wool='#9e2835', wool_dk='#6e1d29', wool_hi='#c8424a', fur='#c28569', fur_dk='#8a5a44',
    iron='#5a6988', iron_dk='#3c4258', iron_hi='#c0cbdc',
    glass='#8fd3ff', glass_dk='#3a7bd5', vial_r='#e43b44', vial_g='#63c74d', vial_y='#feae34',
    fire1='#fef09f', fire2='#feae34', fire3='#f77622', fire4='#e43b44', soot='#262b44', ember='#9e2835',
    leaf='#3e8948', leaf_hi='#63c74d', leaf_dk='#26542c', meat='#c8424a', meat_dk='#7a1f2a', fat='#f4cca1',
).items()})


def col(c): return P[c] if isinstance(c, str) and not c.startswith('#') else (hx(c) if isinstance(c, str) else c)


_px = C.px
def _px2(self, x, y, c): _px(self, x, y, col(c))
C.px = _px2


def line(c, x0, y0, x1, y1, color):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) * 2 + 1
    for i in range(n + 1):
        t = i / n
        c.px(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), color)


def shadow(c, cx, cy, rx, ry=2.5): c.ellipse(cx, cy, rx, ry, SH)


def outlined(c):
    """outline everything that is not the soft shadow"""
    import numpy as np
    sh = (c.a[:, :, 3] > 0) & (c.a[:, :, 3] < 255)
    keep = c.a.copy()
    c.a[sh] = 0
    c.outline(OL)
    c.a[sh & (c.a[:, :, 3] == 0)] = keep[sh & (c.a[:, :, 3] == 0)]
    return c


# ============================================================== camp props
def tent():
    W, H = 48, 40
    c = C(W, H)
    shadow(c, 24, 37, 22, 3)
    # side walls: a triangle prism seen 3/4 from the front, door flap open
    for y in range(6, 36):
        t = (y - 6) / 30
        half = int(3 + t * 19)
        for x in range(24 - half, 24 + half + 1):
            left = x < 24
            k = abs(x - 24) / max(1, half)
            c.px(x, y, 'cv_md' if left else ('cv' if k < 0.8 else 'cv_md'))
    for y in range(8, 36, 5):                                   # seams
        t = (y - 6) / 30; half = int(3 + t * 19)
        for x in range(24 - half + 2, 24 + half - 1, 1):
            if (x + y) % 9 == 0: c.px(x, y, 'cv_dk')
    # ridge + poles
    line(c, 24, 3, 24, 35, 'cv_dk')
    c.rect(23, 1, 25, 4, 'pole'); c.px(24, 0, 'pole')
    # door: dark opening with flaps tied back
    for y in range(17, 36):
        t = (y - 17) / 18; half = int(1 + t * 7)
        for x in range(24 - half, 24 + half + 1): c.px(x, y, 'soot' if y > 19 else 'cv_ol')
    for y in range(17, 36):
        t = (y - 17) / 18
        c.px(24 - int(2 + t * 9), y, 'cv_dk'); c.px(24 + int(2 + t * 9), y, 'cv')
    line(c, 15, 27, 13, 33, 'rope'); line(c, 33, 27, 35, 33, 'rope')
    c.rect(20, 32, 28, 35, 'wool_dk')                          # bedroll peeking out
    c.rect(21, 32, 27, 32, 'wool')
    # guy ropes + pegs
    line(c, 6, 33, 1, 37, 'rope'); line(c, 42, 33, 47, 37, 'rope')
    c.px(1, 37, 'pole'); c.px(46, 37, 'pole')
    c.rect(2, 34, 45, 35, 'cv_dk')
    return outlined(c)


def bedroll():
    c = C(30, 14)
    shadow(c, 15, 11, 14, 2.5)
    c.rect(1, 3, 28, 10, 'wool'); c.rect(1, 3, 28, 4, 'wool_hi'); c.rect(1, 9, 28, 10, 'wool_dk')
    for x in range(6, 28, 5): c.rect(x, 4, x, 9, 'wool_dk')
    c.rect(1, 2, 8, 9, 'fur'); c.rect(2, 3, 7, 4, 'cv'); c.rect(1, 8, 8, 9, 'fur_dk')    # pillow / fur
    c.rect(22, 2, 24, 10, 'rope')
    return outlined(c)


def workbench():
    W, H = 36, 28
    c = C(W, H)
    shadow(c, 18, 25, 17, 2.5)
    # legs + top (3/4)
    for x in (3, 31): c.rect(x, 13, x + 2, 25, 'w_dk')
    c.rect(1, 9, 34, 15, 'w'); c.rect(1, 9, 34, 10, 'w_lt'); c.rect(1, 15, 34, 16, 'w_dk')
    for x in (9, 18, 27): c.rect(x, 10, x, 14, 'w_dk')
    c.rect(4, 20, 31, 21, 'w_dk')                                # lower shelf
    c.rect(7, 18, 12, 20, 'cv_md'); c.rect(20, 18, 24, 20, 'iron')
    # mortar + pestle
    c.ellipse(8, 8, 3.5, 2.5, 'st_md'); c.rect(5, 7, 11, 9, 'st_lt'); c.rect(6, 7, 10, 7, 'st_dk')
    line(c, 9, 7, 12, 2, 'w_lt')
    # vials
    for i, v in enumerate(('vial_r', 'vial_g', 'vial_y')):
        x = 15 + i * 4
        c.rect(x, 4, x + 2, 9, v); c.px(x, 4, 'iron_hi'); c.rect(x + 1, 2, x + 1, 3, 'glass'); c.px(x + 1, 1, 'w_dk')
    # hammer + herbs bundle
    c.rect(26, 6, 33, 7, 'w_dk'); c.rect(31, 4, 33, 9, 'iron')
    c.rect(24, 2, 25, 8, 'leaf'); c.px(23, 2, 'leaf_hi'); c.px(26, 3, 'leaf_hi'); c.px(25, 1, 'leaf_hi')
    return outlined(c)


def stash():
    c = C(22, 20)
    shadow(c, 11, 17, 10, 2)
    c.rect(1, 6, 20, 17, 'w'); c.rect(1, 2, 20, 6, 'w_lt'); c.rect(1, 2, 20, 2, 's_hi')
    c.rect(1, 6, 20, 6, 'w_dk'); c.rect(1, 16, 20, 17, 'w_dk')
    for x in (1, 19): c.rect(x, 2, x + 1, 17, 'iron')
    c.rect(9, 5, 12, 9, 'iron_hi'); c.rect(10, 7, 11, 8, 'iron_dk')
    for x in range(4, 18, 4): c.rect(x, 9, x, 15, 'w_dk')
    return outlined(c)


def log_bench():
    c = C(26, 12)
    shadow(c, 13, 10, 12, 2)
    c.rect(2, 3, 23, 9, 'w'); c.rect(2, 3, 23, 4, 'w_lt'); c.rect(2, 9, 23, 9, 'w_dk')
    c.ellipse(2.5, 6, 2.5, 3.2, 's_hi'); c.px(2, 6, 's_dk'); c.px(3, 5, 's_dk')
    for x in (8, 15, 20): c.px(x, 6, 'w_dk'); c.px(x + 1, 6, 'w_dk')
    return outlined(c)


def rack():
    c = C(26, 30)
    shadow(c, 13, 27, 12, 2)
    for x in (2, 22): line(c, x, 27, x + 1, 2, 'w_dk')
    c.rect(1, 3, 24, 4, 'w')
    for i, x in enumerate(range(5, 22, 5)):
        if i % 2 == 0:   # herb bundle
            c.rect(x, 5, x + 2, 12, 'leaf'); c.rect(x, 5, x + 2, 5, 'rope'); c.px(x - 1, 11, 'leaf_hi'); c.px(x + 3, 10, 'leaf_dk')
        else:            # strip of meat
            c.rect(x, 5, x + 2, 13, 'meat'); c.rect(x, 5, x + 2, 5, 'rope'); c.px(x + 1, 8, 'fat'); c.rect(x, 12, x + 2, 13, 'meat_dk')
    c.rect(6, 19, 19, 21, 'cv_md'); c.rect(6, 19, 19, 19, 'cv')        # hide stretched below
    return outlined(c)


def firepit_frames(n=6):
    out = []
    for f in range(n):
        c = C(24, 24)
        shadow(c, 12, 21, 11, 2.5)
        for a in range(10):                                     # stone ring
            ang = a / 10 * 2 * math.pi
            x, y = 12 + math.cos(ang) * 8.5, 17 + math.sin(ang) * 3.6
            c.ellipse(x, y, 1.8, 1.4, 'st_lt' if a % 3 else 'st_md')
        c.ellipse(12, 17, 6, 2.4, 'soot')
        line(c, 7, 18, 16, 15, 'w_dk'); line(c, 8, 15, 17, 18, 'w')                # logs
        for i in range(9):                                      # flames
            x = 8 + i
            hgt = 4 + 4 * (0.5 + 0.5 * math.sin(f / n * 2 * math.pi + i * 1.7)) * (1 - abs(i - 4) / 5)
            for k in range(int(hgt)):
                y = 16 - k
                c.px(x, y, 'fire4' if k < 1 else 'fire3' if k < hgt * 0.45 else 'fire2' if k < hgt * 0.8 else 'fire1')
        if f % 2 == 0: c.px(10 + f % 5, 5 - f % 3, 'fire2')     # sparks
        else: c.px(14 - f % 4, 4, 'fire1')
        out.append(outlined(c))
    return out


# ============================================================== gathering nodes (frame 0 = ready, frame 1 = picked)
def herb(picked, leaf='leaf', hi='leaf_hi', dk='leaf_dk', flower=None):
    c = C(16, 16); shadow(c, 8, 14, 6, 1.6)
    if picked:
        for x in (5, 8, 11): c.rect(x, 12, x, 14, dk)
        return outlined(c)
    for a in range(5):
        ang = -math.pi / 2 + (a - 2) * 0.55
        x, y = 8 + math.cos(ang) * 4.2, 13 + math.sin(ang) * 5.5
        c.ellipse(x, y, 2.0, 2.6, leaf)
        c.px(x - 0.5, y - 1.5, hi)
    for a in range(5):
        ang = -math.pi / 2 + (a - 2) * 0.55
        line(c, 8, 14, 8 + math.cos(ang) * 4, 13 + math.sin(ang) * 5, dk)
    if flower:
        for (x, y) in ((4, 7), (12, 7), (8, 4), (6, 9), (10, 9)):
            c.px(x, y, flower); c.px(x + 1, y, flower); c.px(x, y - 1, 'yl')
    return outlined(c)


def mushroom(picked, cap='meat', cap_hi='wool_hi', glow=False):
    c = C(16, 16); shadow(c, 8, 14, 6, 1.6)
    spots = [(5, 12, 3), (10, 13, 2.4), (8, 10, 2)] if not picked else [(9, 13, 1.4)]
    for (x, y, r) in spots:
        c.rect(x - 0, y - 1, x, y + 1, 'cv')
        c.ellipse(x + .5, y - 1.5, r, r * 0.7, cap); c.px(x - 1, y - 2, cap_hi); c.px(x + 1, y - 2, 'sn')
    if glow and not picked:
        for (x, y) in ((3, 6), (13, 8), (8, 4)): c.px(x, y, 'glass')
    return outlined(c)


def ore(picked, vein='iron_hi', vein2='glass', rock=('st_md', 'st_lt', 'st_dk')):
    c = C(16, 16); shadow(c, 8, 14, 7, 1.8)
    c.ellipse(8, 10, 6.5 if not picked else 4.5, 4.5 if not picked else 3, rock[0])
    c.ellipse(7, 8.5, 4.5 if not picked else 3, 2.6 if not picked else 1.6, rock[1])
    c.rect(3, 12, 13, 13, rock[2]) if not picked else c.rect(5, 12, 11, 12, rock[2])
    if not picked:
        for (x, y) in ((5, 9), (9, 8), (11, 11), (6, 12)): c.px(x, y, vein); c.px(x + 1, y, vein2)
    return outlined(c)


def crystal(picked):
    c = C(16, 16); shadow(c, 8, 14, 6, 1.6)
    c.ellipse(8, 13, 5, 1.6, 'st_md')
    if not picked:
        for (x, h, w) in ((5, 7, 2), (8, 10, 2), (11, 6, 2)):
            c.rect(x, 13 - h, x + w - 1, 12, 'glass'); c.px(x, 13 - h, 'sn'); c.rect(x + w - 1, 13 - h + 1, x + w - 1, 12, 'glass_dk')
    else:
        c.rect(7, 11, 8, 12, 'glass_dk')
    return outlined(c)


GATHER = [   # order = Gatherable.kind index used by the builder
    ('hierba', lambda p: herb(p)),
    ('flor_luna', lambda p: herb(p, 'leaf_dk', 'leaf', 'g_bk', flower='pk_hi')),
    ('raiz', lambda p: herb(p, 'mesa_dk', 's_dk', 'w_ol', flower=None)),
    ('seta_roja', lambda p: mushroom(p)),
    ('seta_azul', lambda p: mushroom(p, 'glass_dk', 'glass', glow=True)),
    ('hierro', lambda p: ore(p, 's_dk', 'mesa_lt')),
    ('plata', lambda p: ore(p, 'sn', 'iron_hi')),
    ('obsidiana', lambda p: ore(p, 'pu_lt', 'lava_hi', ('ash', 'st_md', 'ash_dk'))),
    ('cristal', lambda p: crystal(p)),
]


# ============================================================== icons (16x16, CraftDB order)
def ic(): return C(16, 16)


def i_leaf(main='leaf', hi='leaf_hi', dk='leaf_dk', flower=None):
    c = ic()
    c.ellipse(8, 8, 5, 3, main)
    for x in range(4, 12): c.px(x, 8 + (1 if x > 8 else 0) - (1 if x < 6 else 0), dk)
    c.px(5, 6, hi); c.px(7, 6, hi); line(c, 12, 9, 14, 12, 'w_dk')
    if flower: c.ellipse(5, 5, 2, 2, flower); c.px(5, 5, 'yl')
    return outlined(c)


def i_root():
    c = ic()
    line(c, 3, 3, 12, 12, 's_dk'); line(c, 4, 3, 13, 12, 'mesa_dk'); line(c, 8, 8, 5, 13, 's_dk'); line(c, 10, 9, 13, 6, 's_dk')
    c.rect(2, 1, 4, 3, 'leaf'); c.px(1, 1, 'leaf_hi')
    return outlined(c)


def i_mush(cap, hi):
    c = ic()
    c.rect(7, 8, 9, 14, 'cv'); c.rect(7, 13, 9, 14, 'cv_md')
    c.ellipse(8, 7, 6, 3.5, cap); c.px(5, 5, hi); c.px(10, 6, 'sn'); c.px(7, 4, 'sn')
    return outlined(c)


def i_meat():
    c = ic()
    c.ellipse(7, 8, 5, 4, 'meat'); c.ellipse(6, 7, 3, 2, 'wool_hi'); c.px(8, 10, 'fat'); c.px(4, 8, 'fat')
    c.rect(11, 9, 14, 10, 'sn'); c.px(14, 8, 'sn'); c.px(14, 11, 'sn')
    return outlined(c)


def i_leather():
    c = ic()
    c.rect(3, 3, 12, 12, 'fur'); c.rect(3, 3, 12, 4, 's_dk'); c.px(2, 6, 'fur'); c.px(13, 9, 'fur'); c.px(3, 12, 'fur_dk'); c.px(12, 12, 'fur_dk')
    for x in range(4, 12, 3): c.px(x, 7, 'fur_dk'); c.px(x + 1, 10, 'fur_dk')
    return outlined(c)


def i_fang():
    c = ic()
    for y in range(3, 13):
        w = max(0, (13 - y) // 3)
        c.rect(7 - w + (y - 3) // 4, y, 8 + w + (y - 3) // 4, y, 'cv')
    c.rect(6, 3, 10, 4, 'cv_md'); c.px(10, 12, 'cv_dk')
    return outlined(c)


def i_blob(main, hi, dk):
    c = ic()
    c.ellipse(8, 10, 5.5, 3.5, main); c.ellipse(8, 8, 3.5, 3, main); c.px(6, 7, hi); c.px(7, 6, hi); c.rect(4, 12, 12, 12, dk)
    c.px(12, 5, main)
    return outlined(c)


def i_ash():
    c = ic()
    c.ellipse(8, 10, 6, 3, 'ash'); c.ellipse(8, 9, 4, 2, 'st_md'); c.px(6, 8, 'lava'); c.px(10, 9, 'lava_hi'); c.px(8, 5, 'st_lt'); c.px(11, 4, 'st_md')
    return outlined(c)


def i_ore(vein, vein2, rock='st_md', lt='st_lt'):
    c = ic()
    c.ellipse(8, 9, 6, 4.5, rock); c.ellipse(7, 7.5, 4, 2.5, lt)
    for (x, y) in ((5, 8), (9, 7), (10, 10), (6, 11)): c.px(x, y, vein); c.px(x + 1, y, vein2)
    return outlined(c)


def i_core():
    c = ic()
    c.ellipse(8, 8, 5, 5, 'lava_dk'); c.ellipse(8, 8, 3.5, 3.5, 'lava'); c.ellipse(7.5, 7.5, 2, 2, 'lava_hi'); c.px(7, 7, 'yl')
    return outlined(c)


def i_crystal():
    c = ic()
    for (x, h) in ((4, 8), (7, 11), (10, 7)):
        c.rect(x, 14 - h, x + 2, 13, 'glass'); c.px(x, 14 - h, 'sn'); c.rect(x + 2, 15 - h, x + 2, 13, 'glass_dk')
    return outlined(c)


def i_cloth():
    c = ic()
    c.rect(3, 4, 12, 11, 'cv'); c.rect(3, 4, 12, 5, 'sn'); c.rect(3, 10, 12, 11, 'cv_md')
    for x in range(4, 12, 2): c.px(x, 8, 'cv_dk')
    c.rect(6, 12, 9, 13, 'cv_md')
    return outlined(c)


def i_flask(liquid, liquid_dk, cork='w_lt', shape='round', fill=0.6):
    c = ic()
    if shape == 'round':
        c.ellipse(8, 10, 4.5, 4, 'glass')
        for y in range(6, 15):
            for x in range(3, 13):
                if ((x + .5 - 8) / 4.5) ** 2 + ((y + .5 - 10) / 4) ** 2 <= 1 and y >= 14 - 8 * fill:
                    c.px(x, y, liquid)
        c.rect(5, 13, 11, 13, liquid_dk) if fill > 0 else None
    else:   # tall vial
        c.rect(5, 5, 10, 14, 'glass')
        if fill > 0: c.rect(5, int(14 - 9 * fill), 10, 14, liquid); c.rect(5, 14, 10, 14, liquid_dk)
    c.rect(7, 3, 8, 5, 'glass'); c.rect(6, 1, 9, 2, cork)
    c.px(5 if shape == 'round' else 6, 8, 'sn')
    return outlined(c)


def i_bandage():
    c = ic()
    c.ellipse(7, 8, 5, 5, 'sn'); c.ellipse(7, 8, 3, 3, 'cv'); c.ellipse(7, 8, 1.2, 1.2, 'cv_md')
    c.rect(11, 9, 14, 12, 'sn'); c.rect(11, 12, 14, 12, 'cv_md'); c.px(12, 10, 'vial_r'); c.px(13, 10, 'vial_r')
    return outlined(c)


def i_jar(main, lid='w'):
    c = ic()
    c.rect(4, 6, 11, 13, 'cv'); c.rect(4, 8, 11, 12, main); c.rect(4, 13, 11, 13, 'cv_md')
    c.rect(3, 4, 12, 5, lid); c.rect(3, 4, 12, 4, 'w_lt')
    c.px(5, 9, 'sn')
    return outlined(c)


def i_stew():
    c = ic()
    c.ellipse(8, 10, 6, 3.5, 'iron_dk'); c.ellipse(8, 8.5, 5, 2, 'fire3'); c.px(6, 8, 'meat'); c.px(9, 9, 'leaf'); c.px(10, 8, 'fat')
    c.px(5, 4, 'cv'); c.px(8, 3, 'cv'); c.px(11, 5, 'cv')
    return outlined(c)


def i_bomb(body='iron_dk', hi='iron', fuse='rope', spark='fire1', band=None):
    c = ic()
    c.ellipse(7.5, 9.5, 5, 5, body); c.ellipse(6, 8, 1.5, 1.5, hi)
    if band: c.rect(3, 9, 12, 10, band)
    c.rect(9, 3, 10, 5, 'iron_hi'); line(c, 10, 3, 13, 1, fuse); c.px(14, 0, spark); c.px(13, 0, 'fire2')
    return outlined(c)


def i_arrows(tip, fletch, glow=None):
    c = ic()
    for k in range(3):
        o = k * 3 - 3
        line(c, 2 + o, 13, 12 + o, 3, 'w_lt')
        c.px(12 + o, 3, tip); c.px(13 + o, 2, tip); c.px(12 + o, 2, tip)
        c.px(2 + o, 13, fletch); c.px(3 + o, 13, fletch); c.px(2 + o, 12, fletch)
    if glow:
        for (x, y) in ((14, 1), (11, 0), (15, 4)): c.px(x, y, glow)
    return outlined(c)


def i_kit():
    c = ic()
    c.rect(2, 6, 13, 13, 'w'); c.rect(2, 6, 13, 7, 'w_lt'); c.rect(7, 5, 8, 6, 'iron')
    c.rect(4, 2, 5, 9, 'iron_hi'); c.rect(3, 2, 6, 3, 'iron'); c.rect(10, 3, 11, 9, 'w_dk'); c.rect(9, 2, 12, 3, 'iron')
    return outlined(c)


ICONS = [
    # ---- materials (0..19)
    ('hierba', lambda: i_leaf()),
    ('flor_luna', lambda: i_leaf('leaf_dk', 'leaf', 'g_bk', flower='pk_hi')),
    ('raiz', i_root),
    ('seta_roja', lambda: i_mush('meat', 'wool_hi')),
    ('seta_azul', lambda: i_mush('glass_dk', 'glass')),
    ('carne', i_meat),
    ('cuero', i_leather),
    ('colmillo', i_fang),
    ('limo', lambda: i_blob('leaf_hi', 'yl', 'leaf_dk')),
    ('sangre', lambda: i_blob('fire4', 'wool_hi', 'meat_dk')),
    ('ceniza', i_ash),
    ('hierro', lambda: i_ore('s_dk', 'mesa_lt')),
    ('plata', lambda: i_ore('sn', 'iron_hi', 'st_dk', 'st_md')),
    ('obsidiana', lambda: i_ore('pu_lt', 'lava_hi', 'ash_dk', 'ash')),
    ('nucleo', i_core),
    ('tela', i_cloth),
    ('aceite', lambda: i_flask('yl_dk', 's_dk', shape='round', fill=0.7)),
    ('frasco', lambda: i_flask('glass', 'glass', shape='tall', fill=0)),
    ('cristal', i_crystal),
    ('madera', lambda: (lambda c: (c.rect(2, 6, 13, 10, 'w'), c.rect(2, 6, 13, 6, 'w_lt'), c.ellipse(2.5, 8, 1.6, 2.4, 's_hi'), outlined(c))[-1])(ic())),
    # ---- consumables (20..)
    ('venda', i_bandage),
    ('unguento', lambda: i_jar('leaf_hi')),
    ('medicina', lambda: i_flask('vial_r', 'meat_dk', shape='round', fill=0.75)),
    ('tonico', lambda: i_flask('vial_g', 'leaf_dk', shape='tall', fill=0.8)),
    ('guiso', i_stew),
    ('bomba', lambda: i_bomb()),
    ('bomba_veneno', lambda: i_bomb('leaf_dk', 'leaf_hi', band='leaf')),
    ('aceite_fuego', lambda: i_flask('fire3', 'fire4', shape='tall', fill=0.85)),
    ('aceite_hielo', lambda: i_flask('glass', 'glass_dk', shape='tall', fill=0.85)),
    ('aceite_sagrado', lambda: i_flask('yl', 'yl_dk', shape='tall', fill=0.85)),
    ('flecha_fuego', lambda: i_arrows('fire3', 'fire4', 'fire1')),
    ('flecha_veneno', lambda: i_arrows('leaf_hi', 'leaf_dk')),
    ('flecha_plata', lambda: i_arrows('sn', 'glass_dk', 'iron_hi')),
    ('elixir', lambda: i_flask('pk', 'pk_dk', shape='round', fill=0.8)),
    ('kit_reparar', i_kit),
]


def summoner_halo():
    """crown of dark spikes with violet glints, worn behind El Invocador's hood (reference: spiked halo)"""
    c = C(32, 22)
    cx, cy = 16, 18
    for k in range(11):
        ang = math.pi + k / 10 * math.pi              # upper half circle
        r0, r1 = 7, 13 if k % 2 == 0 else 10
        x0, y0 = cx + math.cos(ang) * r0, cy + math.sin(ang) * r0
        x1, y1 = cx + math.cos(ang) * r1, cy + math.sin(ang) * r1
        line(c, x0, y0, x1, y1, 'st_md'); c.px(x1, y1, 'st_hi')
    for k in range(40):
        ang = math.pi + k / 39 * math.pi
        c.px(cx + math.cos(ang) * 7, cy + math.sin(ang) * 7, 'st_dk')
    for (x, y) in ((cx, cy - 13), (cx - 12, cy - 3), (cx + 12, cy - 3)): c.px(x, y, 'pk')
    return outlined(c)


def rune_circle_frames(n=6):
    """violet ritual circle on the floor of the Summoner's clearing"""
    out = []
    for f in range(n):
        c = C(64, 36)
        for ring, (r, col) in enumerate(((30, 'pu_lt'), (24, 'pu'), (12, 'pu_lt'))):
            for k in range(160):
                a = k / 160 * 2 * math.pi
                if ring == 1 and (k + f * 3) % 8 < 2: continue
                c.px(32 + math.cos(a) * r, 18 + math.sin(a) * r * 0.55, col)
        for k in range(6):                                   # runes
            a = k / 6 * 2 * math.pi + f / n * 0.4
            x, y = 32 + math.cos(a) * 18, 18 + math.sin(a) * 18 * 0.55
            c.rect(x - 1, y - 1, x + 1, y + 1, 'pk' if (k + f) % 3 == 0 else 'pu_lt')
        for k in range(3):                                   # inner star
            a0 = k / 3 * 2 * math.pi + f / n * 0.6; a1 = a0 + math.pi
            line(c, 32 + math.cos(a0) * 12, 18 + math.sin(a0) * 6.6, 32 + math.cos(a1) * 12, 18 + math.sin(a1) * 6.6, 'pu')
        out.append(c)
    return out


def build():
    props = 'Props/'
    # El Invocador's art (halo, ritual circle) now lives in summoner_art.py
    save(tent(), props + 'camp_tent.png')
    save(bedroll(), props + 'camp_bedroll.png')
    save(workbench(), props + 'camp_workbench.png')
    save(stash(), props + 'camp_stash.png')
    save(log_bench(), props + 'camp_log.png')
    save(rack(), props + 'camp_rack.png')
    fire = firepit_frames()
    save(sheet(fire, 24, 24), props + 'camp_firepit_anim_24x24.png')
    g = []
    for _, f in GATHER: g += [f(False), f(True)]
    save(sheet(g, 16, 16), props + 'gather_anim_16x16.png')
    icons = [f() for _, f in ICONS]
    ui = os.path.join(ROOT, 'Assets', 'Art', 'UI', 'Icons'); os.makedirs(ui, exist_ok=True)
    sheet(icons, 16, 16, cols=8).img().save(os.path.join(ui, 'ui_materials_16x16.png'))

    # preview: a camp scene on grass + the icon sheet
    pv = Image.new('RGBA', (220, 150), (62, 137, 72, 255))
    def put(c, x, y): pv.alpha_composite(c.img(), (x, y))
    put(tent(), 10, 10); put(fire[0], 70, 36); put(bedroll(), 100, 48); put(workbench(), 130, 20)
    put(stash(), 175, 28); put(log_bench(), 60, 62); put(rack(), 185, 52)
    for i, f in enumerate(g): put(f, 6 + (i % 13) * 16, 82 + (i // 13) * 16)
    for i, f in enumerate(icons): put(f, 6 + (i % 13) * 16, 114 + (i // 13) * 16)
    pv.resize((pv.width * 4, pv.height * 4), Image.NEAREST).save(os.path.join(ROOT, 'Documentation', 'Previews', 'camp_preview.png'))
    print(len(icons), 'icons', len(GATHER), 'gather nodes')


if __name__ == '__main__':
    build()
