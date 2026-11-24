"""Detailed buildings + smooth 8-frame animations. Sizes keep the character proportions (person 18 px, doors 20 px)."""
import math
import numpy as np
from kit import C, P, SHADOW, save, sheet, h2
from structures import finish, tri, PERSON, DOOR_H, DOOR_W

FR = 8   # frames for every looping animation


def door_hd(c, cx, bottom, wood=('w_mid', 'w', 'w_dk'), frame='w_ol'):
    fill, lt, dk = wood
    x0, x1 = cx - DOOR_W // 2, cx + DOOR_W // 2 - 1
    c.rect(x0 - 2, bottom - DOOR_H - 2, x1 + 2, bottom, frame)
    c.rect(x0 - 1, bottom - DOOR_H - 1, x1 + 1, bottom, 'st_md')              # stone frame
    c.rect(x0, bottom - DOOR_H, x1, bottom, fill)
    for x in range(x0 + 2, x1, 3): c.rect(x, bottom - DOOR_H, x, bottom, dk)   # planks
    c.rect(x0, bottom - DOOR_H, x1, bottom - DOOR_H, lt)
    c.rect(x0, bottom - DOOR_H + 5, x1, bottom - DOOR_H + 5, 'st_dk'); c.rect(x0, bottom - 6, x1, bottom - 6, 'st_dk')
    c.px(x1 - 2, bottom - DOOR_H // 2, 'yl'); c.px(x1 - 2, bottom - DOOR_H // 2 + 1, 'yl_dk')
    c.rect(x0 - 3, bottom + 1, x1 + 3, bottom + 2, 'st_lt'); c.rect(x0 - 3, bottom + 2, x1 + 3, bottom + 2, 'st_md')  # step


def window_hd(c, x, y, w=10, h=9, box=True):
    c.rect(x - 2, y, x - 1, y + h - 1, 'g_md'); c.rect(x + w, y, x + w + 1, y + h - 1, 'g_md')      # shutters
    c.rect(x - 2, y, x - 2, y + h - 1, 'g_dp'); c.rect(x + w + 1, y, x + w + 1, y + h - 1, 'g_dp')
    c.rect(x, y, x + w - 1, y + h - 1, 'w_ol'); c.rect(x + 1, y + 1, x + w - 2, y + h - 2, 'yl')
    c.rect(x + 1, y + h - 3, x + w - 2, y + h - 2, 'yl_dk')
    c.rect(x + w // 2, y + 1, x + w // 2, y + h - 2, 'w_ol'); c.rect(x + 1, y + h // 2, x + w - 2, y + h // 2, 'w_ol')
    c.px(x + 1, y + 1, 'sn'); c.px(x + 2, y + 1, 'sn')
    if box:
        c.rect(x - 1, y + h, x + w, y + h + 2, 'w'); c.rect(x - 1, y + h + 2, x + w, y + h + 2, 'w_dk')
        for i in range(x, x + w, 2): c.px(i, y + h - 1, 'g_lt'); c.px(i + 1, y + h - 1, ['pk', 'red', 'yl', 'pk_hi'][i % 4])


def roof_hd(c, w, rtop, rbot, cols):
    rl, rd, ridge = cols
    for y in range(rtop, rbot + 1):
        p = (y - rtop) / max(1, rbot - rtop)
        half = 5 + (w / 2 + 2) * p
        row = (y - rtop) // 4
        for x in range(int(w / 2 - half), int(w / 2 + half) + 1):
            left = x < w / 2
            colr = rl if left else rd
            off = 0 if row % 2 else 3
            if (y - rtop) % 4 == 3: colr = rd if left else 'w_ol'               # shingle row shadow
            elif (x + off) % 6 == 0: colr = rd if left else 'w_ol'               # shingle joints
            elif (y - rtop) % 4 == 0 and left: colr = ridge                      # lit shingle edges
            c.px(x, y, colr)
    c.rect(w // 2 - 1, rtop - 1, w // 2 + 1, rtop + 2, ridge)


def house_hd(roof=('red', 'red_dk', 'lava_dk'), w=72, h=74, seed=1):
    c = C(w, h)
    c.ellipse(w / 2, h - 3, w / 2 - 1, 4, SHADOW)
    ground = h - 5
    found = ground - 4
    wall_top = ground - 34
    # stone foundation
    for y in range(found, ground + 1):
        for x in range(7, w - 7):
            colr = 'st' if ((x // 5 + y // 2) % 2) else 'st_lt'
            if (x + (y // 2) * 2) % 5 == 0 or y == ground: colr = 'st_dk'
            c.px(x, y, colr)
    # log walls with round log ends at the corners
    for y in range(wall_top, found):
        k = (y - wall_top) % 5
        colr = 'w_lt' if k == 1 else 'w' if k in (2, 3) else 'w_dk' if k == 4 else 'w_ol'
        c.rect(9, y, w - 10, y, colr)
        if k == 2:
            for x in range(14 + (y % 7), w - 12, 11): c.px(x, y, 'w_dk')        # knots
    for side in (6, w - 9):
        for y in range(wall_top, found, 5):
            c.ellipse(side + 1.5, y + 2.5, 2.4, 2.4, 's_hi'); c.px(side + 1, y + 2, 's_md'); c.px(side + 2, y + 3, 's_dk')
    door_hd(c, w // 2, ground - 1)
    window_hd(c, 14, wall_top + 8); window_hd(c, w - 24, wall_top + 8)
    # barrel and a little lantern by the door
    c.rect(w // 2 + 9, wall_top + 10, w // 2 + 10, wall_top + 11, 'yl'); c.px(w // 2 + 9, wall_top + 9, 'st_ol')
    roof_hd(c, w, wall_top - 30, wall_top + 2, roof)
    # chimney with bricks
    cx0 = w - 22
    c.rect(cx0, wall_top - 26, cx0 + 6, wall_top - 12, 'mesa_dk')
    for y in range(wall_top - 26, wall_top - 12, 2):
        for x in range(cx0, cx0 + 7):
            if (x + (y // 2) % 2 * 2) % 4 == 0: c.px(x, y, 'w_ol')
    c.rect(cx0 - 1, wall_top - 27, cx0 + 7, wall_top - 26, 'st_lt')
    return finish(c, 'w_ol')


def tower_hd(roof=('wa_dp', 'st_ol', 'wa'), w=44, h=104, flag='red'):
    c = C(w, h)
    c.ellipse(w / 2, h - 3, w / 2 - 1, 4, SHADOW)
    ground = h - 5
    body_top = ground - 66
    for y in range(body_top, ground + 1):
        row = (y - body_top) // 5
        off = 0 if row % 2 else 4
        for x in range(5, w - 5):
            rel = (x - 5) / (w - 10)
            v = h2(x // 8 + off, row, 7)
            colr = 'st_lt' if rel < .2 else 'st' if rel < .7 else 'st_md'
            if v > .8 and .2 < rel < .7: colr = 'st_lt'
            if v < .15 and rel > .3: colr = 'st_md'
            if (y - body_top) % 5 == 4 or (x + off) % 8 == 0: colr = 'st_dk'
            c.px(x, y, colr)
    # base course and crenellated top
    c.rect(4, ground - 3, w - 5, ground, 'st_md'); c.rect(4, ground - 3, w - 5, ground - 3, 'st_lt')
    for x in range(3, w - 3, 6):
        c.rect(x, body_top - 5, x + 3, body_top, 'st_lt'); c.rect(x, body_top - 5, x + 3, body_top - 5, 'st_hi')
    c.rect(3, body_top, w - 4, body_top + 1, 'st_md')
    door_hd(c, w // 2, ground - 1, ('w_mid', 'w', 'w_dk'), 'st_ol')
    for wy in (body_top + 10, body_top + 28):                          # arrow slits with warm light
        c.rect(w // 2 - 2, wy, w // 2 + 1, wy + 9, 'st_ol'); c.rect(w // 2 - 1, wy + 1, w // 2, wy + 8, 'yl_dk'); c.px(w // 2 - 1, wy + 1, 'yl')
    for sx in (9, w - 12):
        c.rect(sx, body_top + 18, sx + 2, body_top + 22, 'st_ol')
    # banner
    if flag:
        c.rect(w - 13, body_top + 6, w - 8, body_top + 22, flag); c.rect(w - 13, body_top + 6, w - 13, body_top + 22, 'red_dk')
        c.px(w - 11, body_top + 13, 'yl'); c.px(w - 10, body_top + 12, 'yl'); c.px(w - 10, body_top + 14, 'yl')
        for i in range(3): c.px(w - 13 + i * 2, body_top + 23, flag)
    rl, rd, rh = roof
    tri(c, 1, w - 2, body_top - 36, body_top - 5, rl, rd)
    for y in range(body_top - 30, body_top - 5, 4):
        c.rect(int(w / 2 - (y - body_top + 36) * 0.65), y, w // 2 - 1, y, rh)
    c.rect(w // 2, body_top - 44, w // 2, body_top - 36, 'st_ol'); c.rect(w // 2 + 1, body_top - 44, w // 2 + 8, body_top - 40, 'red')
    return finish(c, 'st_ol')


def windmill_hd():
    out = []
    W_, H_ = 76, 108
    for f in range(FR):
        c = C(W_, H_)
        cx, ground = W_ // 2, H_ - 5
        c.ellipse(cx, H_ - 3, 22, 4, SHADOW)
        top = ground - 60
        for y in range(top, ground):
            p = (y - top) / (ground - top)
            half = 11 + 8 * p
            for x in range(int(cx - half), int(cx + half) + 1):
                rel = (x - (cx - half)) / (2 * half)
                colr = 'sn' if rel < .55 else 'sn_md'
                if (y - top) % 10 == 9: colr = 'sn_dk'
                c.px(x, y, colr)
        for y in range(ground - 6, ground + 1):                      # stone base
            half = 20
            for x in range(cx - half, cx + half + 1):
                c.px(x, y, 'st_dk' if (x + y) % 5 == 0 or y == ground else 'st' if (x // 4) % 2 else 'st_lt')
        door_hd(c, cx, ground - 1)
        window_hd(c, cx - 5, top + 16, 9, 8, box=False)
        tri(c, cx - 15, cx + 15, top - 16, top + 1, 'red', 'red_dk', apex=cx)
        hx_, hy_ = cx, top - 3
        a0 = f * (math.pi / 2) / FR                     # 8 frames = a quarter turn (4 blades) -> seamless loop
        for k in range(4):
            a = a0 + k * math.pi / 2
            nx, ny = -math.sin(a), math.cos(a)
            for i in range(3, 31):
                x = hx_ + math.cos(a) * i; y = hy_ + math.sin(a) * i
                c.px(round(x), round(y), 'w_dk')
                if i > 8:
                    for j in range(1, 7):
                        colr = 'sn' if j < 6 else 'sn_dk'
                        if i % 5 == 0: colr = 'w'                # sail lattice
                        c.px(round(x + nx * j), round(y + ny * j), colr)
        c.ellipse(hx_, hy_, 2.5, 2.5, 'w_ol'); c.px(hx_, hy_, 'yl_dk')
        out.append(finish(c, 'w_ol'))
    return out


def flame(c, cx, base, h, half0, f, seed=0):
    for y in range(h):
        p = y / h
        half = half0 * (1 - p) ** 0.75
        sway = math.sin(f / FR * 2 * math.pi + y * 0.7 + seed) * p * 1.6
        for x in range(int(cx + sway - half - 1), int(cx + sway + half) + 2):
            d = abs(x + .5 - (cx + sway))
            if d > half + .3: continue
            q = d / max(half, .01) * .6 + p * .7
            c.px(x, base - y, 'sn' if q < .18 and p < .3 else 'yl' if q < .45 else 'lava_hi' if q < .75 else 'lava' if q < .95 else 'lava_dk')
    sp = (f * 3) % h
    c.px(cx + int(2 * math.sin(f + seed)), base - h - sp // 2, 'lava_hi')


def torch_hd():
    out = []
    for f in range(FR):
        c = C(16, 34)
        c.ellipse(8, 31, 3.5, 1.4, SHADOW)
        c.rect(7, 14, 8, 30, 'w'); c.rect(7, 14, 7, 30, 'w_lt'); c.rect(6, 29, 9, 30, 'w_dk')
        c.rect(5, 11, 10, 14, 'st_md'); c.rect(5, 11, 10, 11, 'st_lt'); c.rect(5, 14, 10, 14, 'st_dk')
        flame(c, 7.5, 10, 9 + (f % 3 == 0), 2.6, f)
        out.append(finish(c, 'w_ol'))
    return out


def campfire_hd():
    out = []
    for f in range(FR):
        c = C(20, 20)
        c.ellipse(10, 16, 9, 2.6, SHADOW)
        for k in range(7):
            a = k / 7 * 2 * math.pi
            x, y = 10 + math.cos(a) * 7, 15 + math.sin(a) * 2.6
            c.rect(int(x), int(y), int(x) + 1, int(y) + 1, 'st_lt' if k % 2 else 'st'); c.px(int(x) + 1, int(y) + 1, 'st_dk')
        for i in range(10):
            c.px(5 + i, 13 - (i % 3 == 0), 'w'); c.px(5 + i, 14, 'w_dk')
        c.rect(7, 12, 12, 13, 'lava_dk')
        flame(c, 10, 12, 9 + (f % 2), 3.4, f, 1.3)
        flame(c, 7, 12, 5, 1.6, (f + 3) % FR, 2.1)
        flame(c, 13, 12, 6, 1.6, (f + 5) % FR, 3.7)
        out.append(finish(c, 'w_ol'))
    return out


def waterfall_hd():
    out = []
    for f in range(FR):
        c = C(32, 32)
        for y in range(32):
            for x in range(2, 30):
                k = (y - f * 4 + (x * 7) % 13) % 32          # 8 frames x 4 px = 32: seamless vertical loop
                colr = 'wa'
                if x % 4 == 1 and k < 10: colr = 'foam' if k < 3 else 'wa_lt'
                elif x % 4 == 3 and k < 6: colr = 'wa_dk'
                c.px(x, y, colr)
            c.px(1, y, 'w_ol'); c.px(30, y, 'w_ol')
        for x in range(2, 30):
            c.px(x, 31 - ((x + f) % 3 == 0), 'foam')
        out.append(c)
    return out


def sparkle_hd():
    """water glint, placed on lakes/sea - 8 frames twinkle"""
    out = []
    for f in range(FR):
        c = C(8, 8)
        L = [0, 1, 2, 3, 2, 1, 0, 0][f]
        if L:
            for i in range(-L, L + 1):
                c.px(4 + i, 4, 'sn' if abs(i) < 2 else 'wa_lt'); c.px(4, 4 + i, 'sn' if abs(i) < 2 else 'wa_lt')
        out.append(c)
    return out


def build():
    made = []
    S, PR = 'Structures/', 'Props/'
    made.append(save(house_hd(), S + 'house_red.png'))
    made.append(save(house_hd(roof=('wa_dp', 'st_ol', 'wa')), S + 'house_blue.png'))
    made.append(save(house_hd(roof=('s_md', 's_sh', 's_hi')), S + 'house_thatch.png'))
    made.append(save(tower_hd(), S + 'castle_tower.png'))
    made.append(save(tower_hd(roof=('red', 'red_dk', 'lava_dk'), w=38, h=92, flag='wa_dp'), S + 'watchtower.png'))
    made.append(save(sheet(windmill_hd(), 76, 108), S + 'windmill_anim_76x108.png'))
    made.append(save(sheet(torch_hd(), 16, 34), PR + 'torch_anim_16x34.png'))
    made.append(save(sheet(campfire_hd(), 20, 20), PR + 'campfire_anim_20x20.png'))
    made.append(save(sheet(waterfall_hd(), 32, 32), S + 'waterfall_anim_32x32.png'))
    made.append(save(sheet(sparkle_hd(), 8, 8), 'Effects/water_glint_anim_8x8.png'))
    return made


if __name__ == '__main__':
    for p in build(): print(p)
