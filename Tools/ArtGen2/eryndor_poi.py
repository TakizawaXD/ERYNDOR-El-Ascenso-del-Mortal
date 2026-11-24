"""Art for the redesigned Eryndor world (2026-11-21), drawn with the style kit (kit.py palette, 1 px dark outline,
lit from the upper left). Sizes follow the world's proportions (person 18 px, door 20 px).

  Props/bonfire_anim_32x40.png        8 frames: 0 unlit (cold ash + planted sword), 1-7 lit fire loop
  Structures/entrance_crypt.png        crypt stairway into the catacombs (48x56)
  Structures/entrance_cave.png         mine mouth with timber supports (56x44)
  Structures/entrance_cave_ice.png     frozen cave mouth (56x44)
  Structures/entrance_blood.png        crimson arch under the blood tower (40x48)
  Nature/gravestones_16x16.png         4 gravestones
  Structures/shrine_statue.png         robed statue on a rune pedestal (24x44)
  Structures/great_tree.png            the Great Tree of Eldoria (128x150)
  Structures/gate_locked_40x44.png     2 frames: closed portcullis, open
  Structures/gate_lever_32x44.png      2 frames: iron bars closed, open
  Props/lever_16x16.png                2 frames: lever up / down
usage: python Tools/ArtGen2/eryndor_poi.py
"""
import math
import numpy as np
from kit import C, P, save, sheet, h2, hx

P.update({k: hx(v) for k, v in dict(
    ember='#f77622', ember2='#feae34', flame='#fef09f', ash='#5a5a66', ash2='#3c3c48', char='#26212a',
    steel='#c0cbdc', steel2='#8e9ab4', steel3='#5a6988', rune='#7ad7ff', rune2='#2ca6d8', blood='#9e2835', blood2='#5e1420',
    ice='#c4f0ff', ice2='#8fd3ff', ice3='#3a7bd5', moss='#3e8948', bark='#5a3524', bark2='#3f2420',
).items()})
OL = 'w_ol'


def finish(c, col=OL):
    c.outline(col)
    return c


def shadow(c, cx, cy, rx, ry=3):
    c.ellipse(cx, cy, rx, ry, (9, 27, 21, 80))


# ------------------------------------------------------------------ bonfire
def bonfire_frames():
    out = []
    for f in range(8):
        c = C(32, 40)
        shadow(c, 16, 36, 13, 3)
        # stone ring
        for k in range(9):
            a = math.pi * (0.05 + 0.9 * k / 8)
            x, y = 16 + math.cos(a + math.pi) * 11, 33 + math.sin(a) * 3.2
            c.ellipse(x, y, 2.6, 2.0, 'st_md'); c.ellipse(x - 0.6, y - 0.6, 1.5, 1.1, 'st_lt')
        # ash bed and charred logs
        c.ellipse(16, 32, 8, 2.6, 'ash2'); c.ellipse(16, 31.5, 6, 1.8, 'ash')
        for (x0, y0, x1, y1) in ((9, 33, 22, 29), (11, 29, 23, 33)):
            for t in np.linspace(0, 1, 18):
                x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                c.px(x, y, 'char'); c.px(x, y - 1, 'bark2')
        # the coiled sword planted in the embers
        for y in range(6, 30):
            c.px(16, y, 'steel'); c.px(17, y, 'steel3')
            if (y // 2) % 2 == 0 and y > 14: c.px(15, y, 'steel2'); c.px(18, y, 'steel2')      # the coil
        c.rect(13, 9, 20, 10, 'steel3'); c.rect(13, 9, 20, 9, 'steel')                          # guard
        c.rect(16, 3, 17, 8, 'bark'); c.px(16, 2, 'steel2')                                     # grip + pommel
        if f > 0:
            ph = (f - 1) / 7 * 2 * math.pi
            for i in range(11):
                x = 9 + i * 1.4
                hgt = (8 + 7 * (0.5 + 0.5 * math.sin(ph + i * 1.9))) * (1 - abs(i - 5) / 7)
                for y in range(int(hgt)):
                    k = y / max(1, hgt)
                    col = 'blood' if k < 0.15 else 'ember' if k < 0.5 else 'ember2' if k < 0.82 else 'flame'
                    c.px(x, 31 - y, col); c.px(x + 0.7, 31 - y, col)
            for e in range(4):                                                                 # embers drifting up
                ey = 24 - ((f * 3 + e * 5) % 18); ex = 10 + (e * 7 + f * 2) % 13
                c.px(ex, ey, 'ember2' if e % 2 else 'flame')
        out.append(finish(c))
    return out


# ------------------------------------------------------------------ dungeon entrances
def entrance_crypt():
    c = C(48, 56)
    shadow(c, 24, 52, 22, 4)
    c.rect(4, 20, 43, 51, 'st_md'); c.rect(4, 20, 43, 21, 'st_lt')                            # facade
    for y in range(24, 51, 5):
        for x in range(4 + (y // 5 % 2) * 4, 44, 8): c.px(x, y, 'st_dk')
        c.rect(5, y, 42, y, 'st')
    c.rect(0, 14, 47, 21, 'st_dk'); c.rect(1, 15, 46, 19, 'st'); c.rect(1, 15, 46, 15, 'st_hi')   # lintel
    for x in (2, 41): c.rect(x, 20, x + 4, 51, 'st_lt'); c.rect(x + 3, 20, x + 4, 51, 'st_md')    # pillars
    c.rect(14, 28, 33, 51, 'st_bk'); c.rect(15, 29, 32, 51, 'char')                            # doorway
    for k, y in enumerate(range(36, 51, 3)):                                                   # stairs going down
        c.rect(16 + k, y, 31 - k, y + 1, 'st_dk'); c.rect(16 + k, y, 31 - k, y, 'st_md')
    c.ellipse(24, 8, 6, 6, 'st_lt'); c.ellipse(24, 8, 4, 4, 'st_md')                         # skull emblem
    c.rect(22, 7, 22, 8, 'char'); c.rect(26, 7, 26, 8, 'char'); c.rect(23, 11, 25, 11, 'char')
    for (x, y) in ((6, 50), (40, 49), (10, 22), (37, 23)): c.ellipse(x, y, 2, 1.5, 'moss')
    c.rect(18, 24, 29, 26, 'rune2'); c.rect(19, 25, 28, 25, 'rune')                           # glowing glyph line
    return finish(c)


def entrance_cave(ice=False):
    c = C(56, 44)
    shadow(c, 28, 41, 26, 3)
    rock, rock2, rock3 = ('ice', 'ice2', 'ice3') if ice else ('st_lt', 'st_md', 'st_dk')
    c.ellipse(28, 26, 27, 17, rock3); c.ellipse(27, 24, 25, 15, rock2); c.ellipse(24, 20, 16, 9, rock)
    for k in range(18):
        x, y = 6 + h2(k, 1) * 44, 14 + h2(k, 2) * 22
        c.ellipse(x, y, 3, 2, rock if h2(k, 3) > 0.5 else rock3)
    c.ellipse(28, 33, 11, 10, 'st_bk'); c.rect(17, 33, 39, 42, 'st_bk'); c.ellipse(28, 33, 9, 8, 'char')
    if not ice:                                                                                # mine timbers
        for x in (16, 38): c.rect(x, 24, x + 2, 42, 'bark'); c.rect(x, 24, x, 42, 'w_lt')
        c.rect(15, 22, 41, 25, 'bark'); c.rect(15, 22, 41, 22, 'w_lt')
        c.rect(30, 38, 36, 42, 'st_md'); c.rect(31, 39, 35, 41, 'bark')                       # ore cart
    else:
        for x in range(18, 40, 3): c.rect(x, 24, x + 1, 24 + int(3 + 3 * h2(x, 7)), 'ice')    # icicles
    return finish(c)


def entrance_blood():
    c = C(40, 48)
    shadow(c, 20, 45, 18, 3)
    c.rect(2, 10, 37, 44, 'blood2'); c.rect(3, 11, 36, 43, 'blood')
    for y in range(14, 44, 6):
        for x in range(3 + (y // 6 % 2) * 5, 37, 10): c.rect(x, y, x, y + 5, 'blood2')
    c.ellipse(20, 14, 18, 8, 'blood2'); c.ellipse(20, 14, 16, 6, 'blood')
    c.ellipse(20, 26, 9, 9, 'st_bk'); c.rect(11, 26, 29, 44, 'st_bk'); c.ellipse(20, 26, 7, 7, 'char'); c.rect(13, 26, 27, 44, 'char')
    for (x, y) in ((6, 40), (34, 38), (8, 20)): c.ellipse(x, y, 2.4, 1.6, 'pu')                # tendrils
    c.ellipse(20, 8, 3, 3, 'ember'); c.px(20, 8, 'flame')                                     # red eye on the keystone
    return finish(c)


# ------------------------------------------------------------------ graves, shrine, great tree
def gravestones():
    out = []
    for k in range(4):
        c = C(16, 16)
        shadow(c, 8, 14, 6, 2)
        if k == 0:                                         # cross
            c.rect(7, 2, 8, 13, 'st_lt'); c.rect(4, 5, 11, 6, 'st_lt'); c.rect(8, 2, 8, 13, 'st_md')
        elif k == 1:                                       # rounded stone
            c.rect(4, 6, 11, 13, 'st_lt'); c.ellipse(7.5, 6, 3.6, 3.4, 'st_lt'); c.rect(9, 5, 11, 13, 'st_md')
            c.rect(6, 8, 9, 8, 'st_dk'); c.rect(6, 10, 9, 10, 'st_dk')
        elif k == 2:                                       # broken
            c.rect(4, 7, 11, 13, 'st_md'); c.px(4, 6, 'st_md'); c.px(5, 5, 'st_md'); c.px(9, 6, 'st_md'); c.rect(4, 7, 6, 13, 'st_lt')
            c.ellipse(12, 13, 2, 1, 'moss')
        else:                                              # celtic
            c.rect(6, 4, 9, 13, 'st_lt'); c.ellipse(7.5, 5, 3.5, 3.5, 'st_md'); c.ellipse(7.5, 5, 2.2, 2.2, 'st_lt'); c.rect(9, 4, 9, 13, 'st_md')
        c.rect(3, 13, 12, 14, 'g_dk')
        out.append(finish(c))
    return out


def shrine_statue():
    c = C(24, 44)
    shadow(c, 12, 41, 10, 3)
    c.rect(3, 32, 20, 41, 'st_md'); c.rect(3, 32, 20, 33, 'st_lt'); c.rect(6, 35, 17, 38, 'rune2'); c.rect(7, 36, 16, 37, 'rune')
    c.rect(7, 12, 16, 32, 'st_lt'); c.rect(13, 12, 16, 32, 'st_md')                          # robe
    for y in range(20, 32, 3): c.px(9, y, 'st_md'); c.px(12, y + 1, 'st_md')
    c.ellipse(11.5, 9, 4, 4.5, 'st_lt'); c.ellipse(13, 9, 2.4, 3.5, 'st_md')                 # hooded head
    c.rect(4, 16, 7, 24, 'st_lt'); c.rect(16, 16, 19, 24, 'st_md')                            # arms
    c.ellipse(11.5, 25, 3, 3, 'rune'); c.px(11, 24, 'sn')                                      # glowing orb in hands
    return finish(c)


def great_tree():
    W, H = 128, 150
    c = C(W, H)
    shadow(c, 64, 144, 56, 6)
    for k, (ang, ln) in enumerate([(-2.6, 34), (-2.2, 26), (-0.6, 30), (-0.25, 36), (-1.6, 22)]):        # roots
        for t in np.linspace(0, 1, 60):
            x = 64 + math.cos(ang) * ln * t * 1.3; y = 136 + math.sin(-ang) * 6 * t + t * 6
            w = 6 * (1 - t) + 1
            c.ellipse(x, y, w, w * 0.7, 'bark2' if t > 0.5 else 'bark')
            if k in (1, 3) and t > 0.6 and int(t * 60) % 5 == 0: c.px(x, y - 1, 'rune')
    c.rect(52, 70, 76, 138, 'bark2'); c.rect(54, 70, 72, 138, 'bark'); c.rect(55, 70, 59, 138, 'w_lt')     # trunk
    for y in range(76, 136, 6): c.rect(62 + (y // 6 % 3), y, 63 + (y // 6 % 3), y + 3, 'bark2')
    c.ellipse(64, 112, 4, 6, 'char'); c.ellipse(64, 112, 2, 3.5, 'rune2'); c.px(64, 111, 'rune')            # hollow with light
    for (x, y, r) in [(64, 46, 40), (30, 62, 24), (98, 62, 24), (44, 26, 24), (86, 26, 24), (64, 14, 20), (18, 80, 14), (110, 80, 14)]:
        c.ellipse(x, y, r, r * 0.82, 'g_dk2')
    for (x, y, r) in [(64, 44, 36), (30, 60, 21), (98, 60, 21), (44, 24, 21), (86, 24, 21), (64, 12, 17), (18, 78, 11), (110, 78, 11)]:
        c.ellipse(x, y, r, r * 0.78, 'g_dk')
    for (x, y, r) in [(56, 36, 22), (26, 54, 12), (90, 52, 12), (40, 18, 12), (80, 18, 12), (58, 8, 9)]:
        c.ellipse(x, y, r, r * 0.7, 'g_md')
    for k in range(60):                                                                       # leaf highlights + glowing seeds
        x, y = 10 + h2(k, 1) * 108, 4 + h2(k, 2) * 80
        if c.get(int(x), int(y))[3]: c.px(x, y, 'g_lt' if k % 4 else 'rune')
    return finish(c)


# ------------------------------------------------------------------ gates and lever
def gate_locked(open_):
    c = C(40, 44)
    shadow(c, 20, 41, 18, 3)
    for x in (0, 31):
        c.rect(x, 6, x + 8, 42, 'st_md'); c.rect(x, 6, x + 8, 7, 'st_lt'); c.rect(x + 6, 8, x + 8, 42, 'st_dk')
    c.rect(0, 2, 39, 8, 'st'); c.rect(0, 2, 39, 3, 'st_hi')
    c.rect(9, 9, 30, 42, 'st_bk')
    drop = 26 if open_ else 0
    for x in range(10, 30, 4): c.rect(x, 9, x + 1, 42 - drop, 'steel3'); c.px(x, 9, 'steel')
    for y in range(14, 42 - drop, 6): c.rect(10, y, 29, y, 'steel3')
    if not open_:
        c.rect(17, 24, 22, 30, 'ember2'); c.rect(18, 25, 21, 29, 'w'); c.ellipse(19.5, 23, 2.2, 2.2, 'ember2')  # padlock
    return finish(c)


def gate_lever(open_):
    c = C(32, 44)
    shadow(c, 16, 41, 14, 3)
    c.rect(0, 4, 31, 8, 'w_dk'); c.rect(0, 4, 31, 5, 'w_lt')
    drop = 30 if open_ else 0
    for x in range(2, 31, 4): c.rect(x, 8, x + 1, 42 - drop, 'steel3'); c.px(x, 8, 'steel')
    c.rect(1, 22 - drop // 2, 30, 23 - drop // 2, 'steel3')
    return finish(c)


def lever(down):
    c = C(16, 16)
    shadow(c, 8, 14, 6, 2)
    c.rect(3, 10, 12, 14, 'st_md'); c.rect(3, 10, 12, 10, 'st_lt')
    if down:
        for i in range(7): c.px(8 + i * 0.7, 10 - i, 'w_dk'); c.px(9 + i * 0.7, 10 - i, 'w_dk')
        c.ellipse(13, 3, 1.6, 1.6, 'ember')
    else:
        for i in range(7): c.px(7 - i * 0.7, 10 - i, 'w_dk'); c.px(8 - i * 0.7, 10 - i, 'w_dk')
        c.ellipse(3, 3, 1.6, 1.6, 'red')
    return finish(c)


if __name__ == '__main__':
    save(sheet(bonfire_frames(), 32, 40), 'Props/bonfire_anim_32x40.png')
    save(entrance_crypt(), 'Structures/entrance_crypt.png')
    save(entrance_cave(False), 'Structures/entrance_cave.png')
    save(entrance_cave(True), 'Structures/entrance_cave_ice.png')
    save(entrance_blood(), 'Structures/entrance_blood.png')
    save(sheet(gravestones(), 16, 16), 'Nature/gravestones_16x16.png')
    save(shrine_statue(), 'Structures/shrine_statue.png')
    save(great_tree(), 'Structures/great_tree.png')
    save(sheet([gate_locked(False), gate_locked(True)], 40, 44), 'Structures/gate_locked_40x44.png')
    save(sheet([gate_lever(False), gate_lever(True)], 32, 44), 'Structures/gate_lever_32x44.png')
    save(sheet([lever(False), lever(True)], 16, 16), 'Props/lever_16x16.png')
    # preview sheet
    from PIL import Image
    import os
    from kit import OUT
    files = ['Props/bonfire_anim_32x40.png', 'Structures/entrance_crypt.png', 'Structures/entrance_cave.png', 'Structures/entrance_cave_ice.png',
             'Structures/entrance_blood.png', 'Nature/gravestones_16x16.png', 'Structures/shrine_statue.png', 'Structures/great_tree.png',
             'Structures/gate_locked_40x44.png', 'Structures/gate_lever_32x44.png', 'Props/lever_16x16.png']
    ims = [Image.open(os.path.join(OUT, f)) for f in files]
    Wt = sum(i.width for i in ims[:6]) + 70; Ht = 160 + max(i.height for i in ims[6:]) + 20
    pv = Image.new('RGBA', (max(Wt, 520), Ht), (52, 98, 60, 255)); x = 6
    for im in ims[:6]: pv.alpha_composite(im, (x, 6)); x += im.width + 10
    x = 6
    for im in ims[6:]: pv.alpha_composite(im, (x, 70)); x += im.width + 10
    pv.resize((pv.width * 2, pv.height * 2), Image.NEAREST).save(os.path.join(OUT, '..', '..', '..', 'Documentation', 'Previews', 'eryndor_poi.png'))
    print('ok')
