"""One-off patch: buildings & trees sized from the character height (Soldier = 18 px, doors = 20 px)."""
import os
HERE = os.path.dirname(__file__)
p = os.path.join(HERE, 'structures.py')
s = open(p, encoding='utf8').read()


def swap(s, a_marker, b_marker, new):
    a = s.index(a_marker); b = s.index(b_marker)
    return s[:a] + new + s[b:]


HOUSE = '''PERSON = 18          # Soldier body height in px: every door/opening is sized from it
DOOR_H, DOOR_W = 20, 10


def door(c, cx, bottom, cols=('w_ol', 'w_mid', 'w')):
    ol, fill, frame = cols
    c.rect(cx - DOOR_W // 2 - 1, bottom - DOOR_H - 1, cx + DOOR_W // 2, bottom, ol)
    c.rect(cx - DOOR_W // 2, bottom - DOOR_H, cx + DOOR_W // 2 - 1, bottom, fill)
    for y in range(bottom - DOOR_H + 3, bottom, 4):
        c.rect(cx - DOOR_W // 2, y, cx + DOOR_W // 2 - 1, y, frame)
    c.px(cx + DOOR_W // 2 - 3, bottom - DOOR_H // 2, 'yl_dk')


def window(c, x, y, w=8, h=8):
    c.rect(x, y, x + w - 1, y + h - 1, 'w_ol'); c.rect(x + 1, y + 1, x + w - 2, y + h - 2, 'yl')
    c.rect(x + 1, y + h // 2, x + w - 2, y + h // 2, 'w_ol'); c.rect(x + w // 2, y + 1, x + w // 2, y + h - 2, 'w_ol')
    c.px(x + 1, y + 1, 'sn')


def house(roof=('red', 'red_dk'), w=64, h=68):
    """log cabin: wall 32 px (door 20 px), roof 28 px - a person is 18 px"""
    c = C(w, h)
    c.ellipse(w / 2, h - 3, w / 2 - 1, 3.5, SHADOW)
    wall_top, ground = h - 36, h - 4
    for y in range(wall_top, ground):
        col = 'w' if ((y - wall_top) // 4) % 2 else 'w_dk'
        if (y - wall_top) % 4 == 0: col = 'w_ol'
        c.rect(6, y, w - 7, y, col)
    for x in (5, 6, w - 7, w - 6):
        c.rect(x, wall_top, x, ground, 'w_lt' if x in (5, w - 7) else 'w')
    door(c, w // 2, ground)
    window(c, 12, wall_top + 7); window(c, w - 20, wall_top + 7)
    rl, rd = roof
    rtop = wall_top - 28
    for y in range(rtop, wall_top + 2):
        p = (y - rtop) / (wall_top + 2 - rtop)
        half = 6 + (w / 2 - 1) * p
        for x in range(int(w / 2 - half), int(w / 2 + half) + 1):
            col = rl if x < w / 2 else rd
            if (y - rtop) % 5 == 4: col = rd if x < w / 2 else 'w_ol'
            c.px(x, y, col)
    c.rect(w // 2 - 1, rtop - 2, w // 2, rtop + 1, 'w_dk')
    c.rect(w - 20, rtop + 4, w - 16, rtop + 14, 'st_md'); c.rect(w - 20, rtop + 3, w - 16, rtop + 3, 'st_dk')
    return finish(c, 'w_ol')


'''

TOWER = '''def tower(roof=('wa_dp', 'st_ol'), w=40, h=100, flag=True):
    """stone tower: 20 px door, body ~3.5 persons tall, conical roof"""
    c = C(w, h)
    c.ellipse(w / 2, h - 3, w / 2 - 1, 3.5, SHADOW)
    body_top, ground = h - 64, h - 4
    c.rect(5, body_top, w - 6, ground, 'st')
    c.rect(5, body_top, 10, ground, 'st_lt'); c.rect(w - 11, body_top, w - 6, ground, 'st_md')
    for y in range(body_top + 2, ground, 5): c.rect(5, y, w - 6, y, 'st_dk')
    for y in range(body_top + 6, ground, 10):
        off = 0 if (y // 10) % 2 else 6
        for x in range(7 + off, w - 7, 12): c.rect(x, y - 4, x, y, 'st_dk')
    door(c, w // 2, ground, ('st_ol', 'w_mid', 'w'))
    for wy in (body_top + 8, body_top + 24):
        c.rect(w // 2 - 2, wy, w // 2 + 1, wy + 7, 'st_ol'); c.rect(w // 2 - 1, wy + 1, w // 2, wy + 6, 'yl')
    rl, rd = roof
    tri(c, 1, w - 2, body_top - 30, body_top, rl, rd)
    c.rect(2, body_top - 1, w - 3, body_top + 1, 'st_lt')
    if flag:
        c.rect(w // 2, body_top - 38, w // 2, body_top - 30, 'st_ol'); c.rect(w // 2 + 1, body_top - 38, w // 2 + 7, body_top - 35, 'red')
    return finish(c, 'st_ol')


'''

WIND = '''def windmill_frames():
    """tower 58 px with a 20 px door + 26 px blades"""
    out = []
    W_, H_ = 72, 104
    for f in range(4):
        c = C(W_, H_)
        cx, ground = W_ // 2, H_ - 4
        c.ellipse(cx, H_ - 3, 20, 3.5, SHADOW)
        top = ground - 58
        for y in range(top, ground):
            p = (y - top) / (ground - top)
            half = 11 + 7 * p
            for x in range(int(cx - half), int(cx + half) + 1):
                c.px(x, y, 'sn' if x < cx + 2 else 'sn_md')
        for y in range(top + 8, ground, 9): c.rect(int(cx - 10), y, int(cx + 10), y, 'sn_dk')
        door(c, cx, ground)
        window(c, cx - 4, top + 14)
        tri(c, cx - 14, cx + 14, top - 14, top + 1, 'red', 'red_dk', apex=cx)
        hx_, hy_ = cx, top - 2
        ang0 = f * math.pi / 8
        for k in range(4):
            a = ang0 + k * math.pi / 2
            for i in range(3, 30):
                x = hx_ + math.cos(a) * i; y = hy_ + math.sin(a) * i
                c.px(round(x), round(y), 'w_dk')
                if i > 8:
                    nx, ny = -math.sin(a), math.cos(a)
                    for j in (1, 2, 3, 4, 5):
                        c.px(round(x + nx * j), round(y + ny * j), 'sn' if j < 5 else 'sn_dk')
        c.ellipse(hx_, hy_, 2.2, 2.2, 'w_ol')
        out.append(finish(c, 'w_ol'))
    return out


'''

LIGHT = '''def lighthouse():
    W_, H_ = 36, 108
    c = C(W_, H_)
    cx, ground = W_ // 2, H_ - 4
    c.ellipse(cx, H_ - 3, 15, 3, SHADOW)
    top = ground - 76
    for y in range(top, ground):
        half = 8 + (y - top) * 0.07
        band = ((y - top) // 12) % 2
        for x in range(int(cx - half), int(cx + half) + 1):
            lit = x < cx
            col = ('sn' if lit else 'sn_md') if band == 0 else ('red' if lit else 'red_dk')
            c.px(x, y, col)
    door(c, cx, ground, ('st_ol', 'w_mid', 'w'))
    c.rect(cx - 9, top - 12, cx + 8, top, 'st_ol'); c.rect(cx - 8, top - 11, cx + 7, top - 1, 'yl'); c.rect(cx - 6, top - 9, cx - 3, top - 3, 'sn')
    c.rect(cx - 11, top - 1, cx + 10, top + 1, 'st_md')
    tri(c, cx - 10, cx + 10, top - 24, top - 12, 'red', 'red_dk')
    return finish(c, 'st_ol')


'''

DARK = '''def dark_tower_frames():
    out = []
    W_, H_ = 44, 120
    for f in range(4):
        c = C(W_, H_)
        cx, ground = W_ // 2, H_ - 4
        c.ellipse(cx, H_ - 3, 18, 3.5, SHADOW)
        top = ground - 84
        for y in range(top, ground):
            half = 10 + (y - top) * 0.09
            for x in range(int(cx - half), int(cx + half) + 1):
                lit = x < cx - 3
                col = 'st_md' if lit else 'st_dk'
                if (y % 7 == 0) or ((x + (y // 7) * 3) % 9 == 0 and y % 7 < 6): col = 'ash_dk'
                c.px(x, y, col)
        door(c, cx, ground, ('ash_bk', 'pu_dk', 'ash_dk'))
        for wy in (top + 14, top + 36):
            c.rect(cx - 2, wy, cx + 1, wy + 8, 'ash_bk'); c.rect(cx - 1, wy + 1, cx, wy + 7, 'g_hi' if f % 2 else 'g_lt')
        tri(c, cx - 14, cx + 14, top - 22, top, 'pu', 'pu_dk')
        glow = [4.5, 6, 7.5, 6][f]
        c.ellipse(cx, top - 26, glow, glow, (99, 199, 77, 90))
        c.ellipse(cx, top - 26, 2.2, 2.2, 'g_hi')
        out.append(finish(c, 'ash_bk'))
    return out


'''

s = swap(s, 'def house(', 'def stone_wall(', HOUSE)
s = swap(s, 'def tower(', 'def windmill_frames(', TOWER)
s = swap(s, 'def windmill_frames(', 'def lighthouse(', WIND)
s = swap(s, 'def lighthouse(', 'def dark_tower_frames(', LIGHT)
s = swap(s, 'def dark_tower_frames(', 'def ruin_wall(', DARK)
s = s.replace("tower(roof=('red', 'red_dk'), w=28, h=56)", "tower(roof=('red', 'red_dk'), w=34, h=88)")
s = s.replace("sheet(windmill_frames(), 40, 56), S + 'windmill_anim_40x56.png'", "sheet(windmill_frames(), 72, 104), S + 'windmill_anim_72x104.png'")
s = s.replace("sheet(dark_tower_frames(), 32, 72), S + 'dark_tower_anim_32x72.png'", "sheet(dark_tower_frames(), 44, 120), S + 'dark_tower_anim_44x120.png'")
open(p, 'w', encoding='utf8').write(s)

n_path = os.path.join(HERE, 'nature.py')
n = open(n_path, encoding='utf8').read()
n = n.replace("def oak(w=48, h=58, R=19, cols=GREEN, outline='g_ol2', seed=3):", "def oak(w=58, h=76, R=24, cols=GREEN, outline='g_ol2', seed=3):")
n = n.replace("    trunk(c, w // 2, h - 24, h - 4, 8)", "    trunk(c, w // 2, h - 30, h - 4, 10)")
n = n.replace("    c = C(32, 40)\n    c.ellipse(16, 35, 13, 4.5, SHADOW)\n    trunk(c, 16, 22, 37, 6)\n    canopy(c, 16, 14, 12.5, cols, outline, seed, bumps=10, bamp=1.2)",
              "    c = C(40, 52)\n    c.ellipse(20, 47, 15, 4.5, SHADOW)\n    trunk(c, 20, 28, 49, 7)\n    canopy(c, 20, 17, 15.5, cols, outline, seed, bumps=11, bamp=1.3)")
open(n_path, 'w', encoding='utf8').write(n)
print('patched')
