"""House interiors in the reference style (16 px tiles, 3/4 top-down, same palette and proportions as the houses).

  python interiors.py   ->  Assets/Art/World/Interiors/room_<template>.png      painted floor + walls (one per template)
                            Assets/Art/World/Interiors/Furniture/<name>.png   furniture (bottom-centre pivot, y-sorted)
                            Assets/Game/Levels/Interiors.txt                  layouts read by the Unity builder
                            Assets/Art/Effects/light_radial.png              pixel-stepped light for the night
                            Documentation/Previews/interiors_preview.png

Template legend:  W wall face (2 tiles tall, seen from the south)   B wall top / beam   D exit door
                  . wood planks   , stone flags   _ kitchen tiles   = rug (on planks)
"""
import math, os
import numpy as np
from PIL import Image
from kit import C, P, save, sheet, h2, hx

OUTI = 'Interiors/'
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
T = 16
FR = 6

P.update({k: hx(v) for k, v in dict(
    fl_hi='#c98a55', fl='#b07443', fl_md='#9a6238', fl_dk='#7d4c2c', fl_seam='#5a3524',
    pl='#eadbb8', pl_md='#d8c49a', pl_dk='#b9a47a',           # plaster
    tl_a='#e8cfa4', tl_b='#c8774f', tl_dk='#9c5a3c',          # kitchen tiles
    rug='#9e2835', rug_dk='#7a1f2a', rug_hi='#c8424a', rug_b='#feae34',
    rug2='#2a64b8', rug2_dk='#17458c',
    sheet='#eff3eb', sheet_dk='#c0cbdc', blanket='#3e8948', blanket_dk='#26542c', blanket2='#2a64b8', blanket2_dk='#17458c',
    book1='#9e2835', book2='#2a64b8', book3='#3e8948', book4='#feae34', book5='#68386c',
    gold='#feae34', gold_hi='#fef09f', iron='#5a6988', iron_dk='#3c4258', iron_hi='#8e9ab4',
    fire1='#fef09f', fire2='#feae34', fire3='#f77622', fire4='#e43b44', ember='#9e2835', soot='#262b44',
    glass='#8fd3ff', glass_dk='#3a7bd5', night='#124e89',
).items()})

# ============================================================== templates
TEMPLATES = {
    # family house: living room + kitchen + bedroom
    'casa': dict(floor='.', wall='log', rows=[
        "BWWWWWWWWWWBWWWWWB",
        "BWWWWWWWWWWBWWWWWB",
        "B..........B_____B",
        "B..........B_____B",
        "B..........._____B",
        "B...====...B_____B",
        "B...====...BWW_WWB",
        "B...====...BWW_WWB",
        "B..........B.....B",
        "B................B",
        "B..........B.....B",
        "BBBBBDBBBBBBBBBBBB"],
        items=[('fireplace', 5, 2), ('bookshelf', 2, 2), ('window', 8.5, 1, 'wall'), ('painting', 3, 0.6, 'wall'),
               ('table_round', 5.5, 5), ('chair', 4.2, 4.6), ('chair', 6.8, 4.6), ('plant', 9.5, 2), ('plant', 1.5, 10),
               ('stove', 13, 2), ('cupboard', 15.5, 2), ('barrel', 16.3, 5), ('sacks', 12.5, 5), ('window', 14.5, 0.9, 'wall'),
               ('bed_double', 15, 9), ('wardrobe', 12.7, 8), ('nightstand', 16.4, 8), ('chest', 13.5, 10.2),
               ('candle', 9.5, 9), ('crate', 1.6, 7)]),
    # thatched cabin: one cosy room
    'cabana': dict(floor='.', wall='log', rows=[
        "BWWWWWWWWWWWB",
        "BWWWWWWWWWWWB",
        "B...........B",
        "B...........B",
        "B...====....B",
        "B...====....B",
        "B...........B",
        "B...........B",
        "BBBBBBDBBBBBB"],
        items=[('bed_single', 10.5, 4), ('stove', 2.5, 2), ('table_long', 5.5, 3.6), ('stool', 4.5, 4.4), ('stool', 6.6, 4.4),
               ('sacks', 1.6, 6.5), ('barrel', 11.3, 6.7), ('chest', 8.4, 2.3), ('window', 6.5, 1, 'wall'), ('plant', 11.5, 2),
               ('hay', 2.2, 7.4)]),
    # inn: hall + bar + two bedrooms
    'posada': dict(floor='.', wall='plaster', rows=[
        "BWWWWWWWWWWWWWBWWWWWB",
        "BWWWWWWWWWWWWWBWWWWWB",
        "B.............B.....B",
        "B.............B.....B",
        "B...................B",
        "B.............B.....B",
        "B.............BWW.WWB",
        "B.....=====...BWW.WWB",
        "B.....=====...B.....B",
        "B.....=====.........B",
        "B.............B.....B",
        "BBBBBBBBDBBBBBBBBBBBB"],
        items=[('counter', 4.5, 3.4), ('kegs', 2.2, 2), ('cupboard', 7.5, 2), ('fireplace', 11, 2), ('window', 13.4, 1, 'wall'),
               ('table_round', 3, 6.5), ('chair', 1.8, 6.2), ('chair', 4.2, 6.2), ('table_round', 8.5, 9.6), ('chair', 7.2, 9.3),
               ('chair', 9.8, 9.3), ('table_long', 11.5, 6.2), ('stool', 10.6, 7), ('stool', 12.6, 7), ('barrel', 1.5, 10.3),
               ('candle', 13.5, 10.3), ('bed_single', 16.2, 3), ('bed_single', 18.6, 3), ('nightstand', 17.4, 2.2),
               ('bed_double', 18, 9), ('chest', 15.8, 10.2), ('plant', 19.4, 10.3), ('painting', 6.5, 0.6, 'wall')]),
    # blacksmith: forge + anvil + racks, small store room
    'herreria': dict(floor=',', wall='stone_brick', rows=[
        "BWWWWWWWWWWBWWWWB",
        "BWWWWWWWWWWBWWWWB",
        "B,,,,,,,,,,B....B",
        "B,,,,,,,,,,B....B",
        "B,,,,,,,,,,,....B",
        "B,,,,,,,,,,B....B",
        "B,,,,,,,,,,B....B",
        "B,,,,,,,,,,B....B",
        "B,,,,,,,,,,B....B",
        "BBBBBDBBBBBBBBBBB"],
        items=[('forge', 3, 2), ('anvil', 6, 4.4), ('weapon_rack', 8.8, 2), ('armor_stand', 9.8, 5.2), ('barrel', 1.5, 5.6),
               ('crate', 1.6, 7.6), ('cauldron', 6.6, 7.2), ('crate', 15.4, 2.6), ('crate', 15.4, 4.1), ('barrel', 13, 2.4),
               ('chest', 14.2, 7.6), ('sacks', 15.6, 7.6), ('window', 13.8, 0.9, 'wall')]),
    # citadel barracks
    'cuartel': dict(floor=',', wall='stone_brick', rows=[
        "BWWWWWWWWWWWWWWWWWWB",
        "BWWWWWWWWWWWWWWWWWWB",
        "B,,,,,,,,,,,,,,,,,,B",
        "B,,,,,,,,,,,,,,,,,,B",
        "B,,,,,,,,,,,,,,,,,,B",
        "B,,,,,,,,,,,,,,,,,,B",
        "B,,,,,,,,,,,,,,,,,,B",
        "B,,,,,,,,,,,,,,,,,,B",
        "B,,,,,,,,,,,,,,,,,,B",
        "B,,,,,,,,,,,,,,,,,,B",
        "BBBBBBBBBDBBBBBBBBBB"],
        items=[('bunk', 2, 3.5), ('bunk', 4, 3.5), ('bunk', 6, 3.5), ('weapon_rack', 9.5, 2), ('armor_stand', 11.5, 2.4),
               ('armor_stand', 13, 2.4), ('banner', 15.5, 0.9, 'wall'), ('dummy', 16, 5.5), ('dummy', 18, 5.5),
               ('table_long', 5, 7.5), ('stool', 4, 8.3), ('stool', 6, 8.3), ('chest', 1.6, 8.5), ('barrel', 18.4, 8.6),
               ('candle', 9, 8.4), ('window', 4, 1, 'wall'), ('window', 18, 1, 'wall')]),
    # chapel
    'capilla': dict(floor=',', wall='stone_brick', rows=[
        "BWWWWWWWWWWWWWWB",
        "BWWWWWWWWWWWWWWB",
        "B,,,,,,,,,,,,,,B",
        "B,,,,,,,,,,,,,,B",
        "B,,,,,,====,,,,B",
        "B,,,,,,====,,,,B",
        "B,,,,,,====,,,,B",
        "B,,,,,,====,,,,B",
        "B,,,,,,====,,,,B",
        "B,,,,,,====,,,,B",
        "B,,,,,,,,,,,,,,B",
        "BBBBBBBDBBBBBBBB"],
        items=[('stained', 7.5, 0.9, 'wall'), ('altar', 7.5, 3.2), ('candle', 5.3, 3.2), ('candle', 9.7, 3.2),
               ('pew', 3.5, 5.4), ('pew', 11.5, 5.4), ('pew', 3.5, 7.4), ('pew', 11.5, 7.4), ('pew', 3.5, 9.4), ('pew', 11.5, 9.4),
               ('plant', 1.5, 2.6), ('plant', 13.5, 2.6), ('lectern', 2.6, 10.3)]),
    # library / sage's house
    'biblioteca': dict(floor='.', wall='stone_brick', rows=[
        "BWWWWWWWWWWWWWWWWB",
        "BWWWWWWWWWWWWWWWWB",
        "B................B",
        "B................B",
        "B.....======.....B",
        "B.....======.....B",
        "B.....======.....B",
        "B................B",
        "B................B",
        "B................B",
        "BBBBBBBBDBBBBBBBBB"],
        items=[('bookshelf', 2, 2), ('bookshelf', 4, 2), ('bookshelf', 6, 2), ('bookshelf', 11, 2), ('bookshelf', 13, 2),
               ('bookshelf', 15, 2), ('window', 8.5, 1, 'wall'), ('table_long', 8.5, 5.5), ('chair', 7, 6.4), ('chair', 10, 6.4),
               ('lectern', 2.5, 7.5), ('globe', 15, 7.2), ('candle', 4.5, 8.5), ('candle', 12.5, 8.5), ('chest', 15.4, 9.3),
               ('plant', 1.5, 9.4)]),
}

# ============================================================== shell (floor + walls)
def floor_px(kind, x, y):
    tx, ty = x // T, y // T
    if kind == ',':                                      # flagstones, 8x8 staggered
        sx = (x + (4 if (y // 8) % 2 else 0)) % 8; sy = y % 8
        if sx == 0 or sy == 0: return 'st_md'
        n = h2(x // 8 + (4 if (y // 8) % 2 else 0), y // 8, 3)
        base = 'st_lt' if n > 0.66 else 'st' if n > 0.2 else 'st_md'
        if sx == 1 or sy == 1: return 'st_hi' if base == 'st_lt' else 'st_lt'
        return base if h2(x, y, 9) > 0.04 else 'st_md'
    if kind == '_':                                      # checker tiles
        a = ((x // 8) + (y // 8)) % 2
        if x % 8 == 0 or y % 8 == 0: return 'tl_dk'
        return 'tl_a' if a else 'tl_b'
    # planks: horizontal boards 5 px tall, staggered joints
    board = y // 5
    off = int(h2(board, 0, 21) * 32)
    if y % 5 == 4: return 'fl_seam'
    if (x + off) % 32 == 0: return 'fl_seam'
    if (x + off) % 32 == 1: return 'fl_md'
    n = h2(board, (x + off) // 32, 22)
    base = 'fl_hi' if n > 0.75 else 'fl' if n > 0.25 else 'fl_md'
    if y % 5 == 0: return 'fl_hi' if base != 'fl_hi' else 'fl'
    if h2(x, y, 23) < 0.03: return 'fl_dk'               # grain
    if (x + off) % 32 == 30 and y % 5 == 2: return 'fl_seam'   # nail
    return base


def wall_face_px(style, x, yy):
    """yy = 0..31 inside the 2-tile face (0 = top)"""
    if yy < 3: return 'w_ol' if yy == 0 else ('w_dk' if yy == 1 else 'w')                 # top beam
    if yy >= 29: return 'w_ol' if yy == 31 else 'w_dk'                                      # baseboard
    if style == 'log':
        band = (yy - 3) // 6; k = (yy - 3) % 6
        n = h2(band, x // 24, 41)
        if k == 0: return 'w_ol'
        if k == 1: return 'w_lt'
        if k == 5: return 'w_dk'
        if (x + band * 7) % 24 == 0: return 'w_dk'
        return 'w' if n > 0.4 else 'w_mid'
    if style == 'plaster':
        if yy in (3, 4) or yy in (27, 28): return 'w'                                     # timber rails
        if x % 32 in (0, 1): return 'w' if x % 32 == 0 else 'w_dk'                          # posts
        if yy > 20: return 'pl_md' if (x // 4 + yy) % 7 else 'pl_dk'                        # wainscot
        return 'pl' if h2(x, yy, 43) > 0.06 else 'pl_md'
    # stone bricks
    row = (yy - 3) // 6; k = (yy - 3) % 6
    sx = (x + (6 if row % 2 else 0)) % 12
    if k == 5 or sx == 0: return 'st_dk'
    n = h2((x + (6 if row % 2 else 0)) // 12, row, 44)
    if k == 0: return 'st_hi' if n > 0.5 else 'st_lt'
    return 'st_lt' if n > 0.7 else 'st' if n > 0.2 else 'st_md'


def beam_px(x, y, grid, gx, gy):
    """wall tops: dark beam with a lit rim where it meets the floor"""
    return 'w_ol'


def solid(ch): return ch in 'WB'


def render_shell(name, t):
    rows = t['rows']; H, W = len(rows), len(rows[0])
    assert all(len(r) == W for r in rows), name
    c = C(W * T, H * T)
    for gy in range(H):
        for gx in range(W):
            ch = rows[gy][gx]
            for y in range(T):
                for x in range(T):
                    X, Y = gx * T + x, gy * T + y
                    if ch == 'W':
                        # face rows: find the first row of this face block
                        top = gy
                        while top > 0 and rows[top - 1][gx] == 'W': top -= 1
                        col = wall_face_px(t['wall'], X, (gy - top) * T + y)
                    elif ch == 'B':
                        col = 'w_ol'
                        if t['wall'] == 'stone_brick': col = 'st_ol'
                    else:
                        fk = ch if ch in ',_' else ('.' if ch in '.=D' else t['floor'])
                        col = floor_px(fk, X, Y)
                    c.px(X, Y, col)
    # beams: lit edge facing walkable floor, dark inner line
    beam_lt = 'st_md' if t['wall'] == 'stone_brick' else 'w_dk'
    beam_md = 'st_dk' if t['wall'] == 'stone_brick' else 'w_ol'
    for gy in range(H):
        for gx in range(W):
            if rows[gy][gx] != 'B': continue
            for y in range(T):
                for x in range(T):
                    X, Y = gx * T + x, gy * T + y
                    c.px(X, Y, beam_md if (x + y) % 9 else beam_lt)
            def flo(dx, dy):
                xx, yy = gx + dx, gy + dy
                return 0 <= xx < W and 0 <= yy < H and not solid(rows[yy][xx])
            if flo(1, 0): c.rect(gx * T + 13, gy * T, gx * T + 15, gy * T + 15, beam_lt); c.rect(gx * T + 15, gy * T, gx * T + 15, gy * T + 15, 'w_ol')
            if flo(-1, 0): c.rect(gx * T, gy * T, gx * T + 2, gy * T + 15, beam_lt); c.rect(gx * T, gy * T, gx * T, gy * T + 15, 'w_ol')
            if flo(0, -1): c.rect(gx * T, gy * T, gx * T + 15, gy * T + 2, beam_lt); c.rect(gx * T, gy * T, gx * T + 15, gy * T, 'w_ol')
    # rugs
    rugs = [(gx, gy) for gy in range(H) for gx in range(W) if rows[gy][gx] == '=']
    if rugs:
        groups = []
        for p in rugs:
            for g in groups:
                if any(abs(p[0] - q[0]) + abs(p[1] - q[1]) == 1 for q in g): g.append(p); break
            else: groups.append([p])
        for gi, g in enumerate(groups):
            x0 = min(p[0] for p in g) * T + 3; x1 = (max(p[0] for p in g) + 1) * T - 4
            y0 = min(p[1] for p in g) * T + 3; y1 = (max(p[1] for p in g) + 1) * T - 4
            main, dk = ('rug', 'rug_dk') if gi % 2 == 0 else ('rug2', 'rug2_dk')
            c.rect(x0, y0 + 1, x1, y1 + 1, (0, 0, 0, 60))
            c.rect(x0, y0, x1, y1, dk); c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, main)
            c.rect(x0 + 3, y0 + 3, x1 - 3, y1 - 3, 'rug_b'); c.rect(x0 + 4, y0 + 4, x1 - 4, y1 - 4, main)
            for x in range(x0 + 6, x1 - 5, 6):
                for y in range(y0 + 6, y1 - 5, 6): c.px(x, y, 'rug_b'); c.px(x + 1, y + 1, dk)
            for x in range(x0, x1 + 1, 2): c.px(x, y0 - 1, 'rug_b'); c.px(x, y1 + 1, 'rug_b')      # fringe
    # contact shadows under faces and beams
    sh = np.zeros((H * T, W * T), np.float32)
    for gy in range(H):
        for gx in range(W):
            if solid(rows[gy][gx]): continue
            above = gy > 0 and solid(rows[gy - 1][gx])
            left = gx > 0 and solid(rows[gy][gx - 1])
            right = gx < W - 1 and solid(rows[gy][gx + 1])
            for y in range(T):
                for x in range(T):
                    s = 0
                    if above: s = max(s, (5 - y) / 5 * 0.45 if y < 5 else 0)
                    if left: s = max(s, (3 - x) / 3 * 0.3 if x < 3 else 0)
                    if right: s = max(s, (x - 12) / 3 * 0.2 if x > 12 else 0)
                    sh[gy * T + y, gx * T + x] = s
    a = c.a.astype(np.float32); a[:, :, :3] *= (1 - sh[:, :, None]); c.a = a.astype(np.uint8)
    # exit door: dark doorway + mat + daylight spill
    for gy in range(H):
        for gx in range(W):
            if rows[gy][gx] != 'D': continue
            X, Y = gx * T, gy * T
            c.rect(X, Y + 6, X + 15, Y + 15, (24, 20, 37, 255))
            c.rect(X + 1, Y + 7, X + 14, Y + 15, (40, 34, 56, 255))
            c.rect(X - 1, Y, X - 1, Y + 15, 'w_ol'); c.rect(X + 16, Y, X + 16, Y + 15, 'w_ol')
            c.rect(X + 1, Y - 6, X + 14, Y + 4, 'rug_dk'); c.rect(X + 2, Y - 5, X + 13, Y + 3, 'tl_a')
            for x in range(X + 3, X + 13, 2): c.px(x, Y - 1, 'tl_b'); c.px(x + 1, Y - 3, 'tl_b')
    save(c, f'{OUTI}room_{name}.png')
    return c


# ============================================================== furniture
def box(c, x0, y0, x1, y1, top_h, top, front, ol='w_ol', side=None):
    """3/4 block: lit top face (top_h px) above a darker front face, 1 px outline"""
    c.rect(x0, y0, x1, y1, ol)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y0 + top_h, top)
    c.rect(x0 + 1, y0 + top_h + 1, x1 - 1, y1 - 1, front)
    c.rect(x0 + 1, y0 + top_h + 1, x1 - 1, y0 + top_h + 1, ol)
    if side: c.rect(x1 - 2, y0 + top_h + 2, x1 - 1, y1 - 1, side)


def shadow(c, cx, cy, rx, ry=2):
    c.ellipse(cx, cy, rx, ry, (9, 27, 21, 70))


def F(name, c): save(c, f'{OUTI}Furniture/{name}.png'); return c


def bed(double=False, blanket=('blanket', 'blanket_dk')):
    w = 32 if double else 20; h = 40
    c = C(w, h); shadow(c, w / 2, h - 2, w / 2 - 1)
    box(c, 0, 2, w - 1, h - 3, 6, 'w', 'w_dk')                                   # frame + headboard
    c.rect(1, 3, w - 2, 4, 'w_lt')
    c.rect(2, 9, w - 3, h - 6, 'sheet'); c.rect(2, h - 7, w - 3, h - 6, 'sheet_dk')
    pil = [(3, w - 4)] if not double else [(3, w // 2 - 2), (w // 2 + 1, w - 4)]
    for a, b in pil: c.rect(a, 10, b, 14, 'sn'); c.rect(a, 14, b, 14, 'sheet_dk')
    bl, bd = blanket
    c.rect(2, 17, w - 3, h - 6, bl); c.rect(2, 17, w - 3, 17, 'sheet')
    for y in range(20, h - 6, 4): c.rect(2, y, w - 3, y, bd)
    c.rect(2, h - 7, w - 3, h - 6, bd)
    c.rect(0, h - 5, 1, h - 3, 'w_ol'); c.rect(w - 2, h - 5, w - 1, h - 3, 'w_ol')
    return c


def bunk():
    c = C(22, 44); shadow(c, 11, 42, 10)
    for x in (1, 19): c.rect(x, 2, x + 1, 41, 'w_dk'); c.px(x, 2, 'w_lt')
    for y0 in (6, 24):
        c.rect(1, y0, 20, y0 + 12, 'w_ol'); c.rect(2, y0 + 1, 19, y0 + 9, 'sheet')
        c.rect(3, y0 + 1, 18, y0 + 3, 'sn'); c.rect(2, y0 + 5, 19, y0 + 9, 'blanket2'); c.rect(2, y0 + 9, 19, y0 + 9, 'blanket2_dk')
        c.rect(1, y0 + 10, 20, y0 + 12, 'w')
    return c


def table_round():
    c = C(30, 24); shadow(c, 15, 21, 12, 3)
    c.ellipse(15, 9, 14, 8, 'w_ol'); c.ellipse(15, 8.5, 13, 7, 'w_mid'); c.ellipse(15, 8, 12, 5.5, 'w_lt')
    c.rect(13, 16, 17, 21, 'w_dk'); c.rect(13, 16, 13, 21, 'w_ol'); c.rect(17, 16, 17, 21, 'w_ol')
    c.rect(10, 21, 20, 22, 'w_ol')
    c.rect(9, 5, 11, 7, 'sn'); c.px(10, 5, 'sheet_dk')                          # mug
    c.ellipse(19, 7, 3, 2, 'st_hi'); c.px(19, 6, 'red'); c.px(20, 7, 'g_lt')    # plate
    return c


def table_long():
    c = C(46, 24); shadow(c, 23, 21, 21, 3)
    box(c, 0, 2, 45, 14, 8, 'w_lt', 'w_dk')
    for x in range(1, 45, 9): c.rect(x, 3, x, 10, 'w')
    for x in (2, 41): c.rect(x, 14, x + 2, 21, 'w_dk'); c.rect(x, 14, x, 21, 'w_ol')
    c.rect(8, 4, 12, 7, 'sheet'); c.rect(9, 3, 11, 3, 'sheet_dk')                   # bowl
    c.rect(30, 3, 32, 7, 'sn'); c.px(31, 2, 'fire2')                                 # candle
    c.rect(20, 5, 26, 7, 'yl_dk'); c.rect(21, 5, 25, 5, 'yl')                       # bread
    return c


def chair():
    c = C(14, 20); shadow(c, 7, 18, 6)
    c.rect(2, 0, 11, 9, 'w_ol'); c.rect(3, 1, 10, 8, 'w'); c.rect(3, 1, 10, 1, 'w_lt')
    c.rect(5, 3, 8, 6, 'w_dk')
    box(c, 1, 9, 12, 14, 2, 'w_lt', 'w_dk')
    for x in (2, 10): c.rect(x, 14, x + 1, 18, 'w_dk')
    return c


def stool():
    c = C(12, 12); shadow(c, 6, 10, 5)
    c.ellipse(6, 4, 5, 3, 'w_ol'); c.ellipse(6, 3.6, 4, 2, 'w_lt')
    for x in (2, 8): c.rect(x, 6, x + 1, 10, 'w_dk')
    return c


def bookshelf():
    c = C(30, 40); shadow(c, 15, 38, 14)
    box(c, 0, 0, 29, 38, 3, 'w_lt', 'w_dk')
    for i, y in enumerate((6, 15, 24)):
        c.rect(2, y, 27, y + 7, 'w_ol')
        x = 3
        while x < 26:
            bw = 2 + int(h2(x, y, 51) * 2)
            col = ['book1', 'book2', 'book3', 'book4', 'book5', 'sheet'][int(h2(x, y, 52) * 6)]
            top = y + 1 + int(h2(x, y, 53) * 2)
            if h2(x, y, 54) < 0.12: x += 2; continue
            c.rect(x, top, min(26, x + bw - 1), y + 7, col); c.rect(x, top, x, y + 7, (0, 0, 0, 70))
            x += bw
        c.rect(1, y + 8, 28, y + 8, 'w')
    c.rect(2, 33, 27, 36, 'w'); c.rect(12, 34, 17, 35, 'gold')
    return c


def wardrobe():
    c = C(28, 40); shadow(c, 14, 38, 13)
    box(c, 0, 0, 27, 38, 4, 'w_lt', 'w')
    c.rect(2, 7, 12, 35, 'w_mid'); c.rect(15, 7, 25, 35, 'w_mid')
    c.rect(2, 7, 12, 7, 'w_lt'); c.rect(15, 7, 25, 7, 'w_lt'); c.rect(13, 6, 14, 36, 'w_ol')
    c.px(11, 21, 'gold'); c.px(16, 21, 'gold')
    c.rect(4, 10, 10, 15, 'w'); c.rect(17, 10, 23, 15, 'w')
    return c


def cupboard():
    c = C(28, 38); shadow(c, 14, 36, 13)
    box(c, 0, 0, 27, 36, 3, 'w_lt', 'w')
    c.rect(2, 5, 25, 18, 'w_ol')
    for i, x in enumerate(range(4, 24, 5)):
        c.ellipse(x + 1.5, 9, 2, 2, 'st_hi' if i % 2 else 'sn'); c.px(x + 1, 9, 'rug2')
        c.rect(x, 13, x + 3, 17, ['sn', 'rug2', 'tl_b', 'sheet'][i % 4])
    c.rect(1, 19, 26, 19, 'w_lt')
    c.rect(2, 21, 12, 34, 'w_mid'); c.rect(15, 21, 25, 34, 'w_mid'); c.px(11, 27, 'gold'); c.px(16, 27, 'gold')
    return c


def stove():
    c = C(28, 34); shadow(c, 14, 32, 13)
    box(c, 0, 6, 27, 32, 5, 'st_lt', 'st', 'st_ol')
    c.rect(11, 0, 16, 6, 'st_dk'); c.rect(11, 0, 16, 0, 'st_md')                  # chimney pipe
    c.rect(6, 16, 21, 28, 'st_ol'); c.rect(7, 17, 20, 27, 'soot')
    c.rect(8, 23, 19, 27, 'fire3'); c.rect(10, 21, 17, 24, 'fire2'); c.rect(12, 20, 15, 22, 'fire1')
    c.ellipse(8, 9, 4, 2, 'iron_dk'); c.ellipse(20, 9, 4, 2, 'iron_dk'); c.ellipse(8, 8, 3, 1.5, 'iron')       # pots
    return c


def fireplace_frames():
    out = []
    for f in range(FR):
        c = C(40, 46)
        box(c, 0, 0, 39, 44, 4, 'st_lt', 'st', 'st_ol')
        for y in range(6, 44, 5):                                        # bricks
            for x in range((y // 5 % 2) * 4, 40, 8): c.px(x, y, 'st_dk')
            c.rect(1, y, 38, y, 'st_md')
        c.rect(0, 14, 39, 17, 'w'); c.rect(0, 14, 39, 14, 'w_lt'); c.rect(0, 17, 39, 17, 'w_ol')   # mantel
        c.rect(6, 10, 9, 13, 'gold'); c.rect(29, 9, 33, 13, 'rug2')                                 # trinkets
        c.rect(8, 21, 31, 44, 'st_ol'); c.rect(10, 23, 29, 44, 'soot')
        c.rect(11, 40, 28, 43, 'w_dk'); c.rect(11, 40, 28, 40, 'w')                               # logs
        for i in range(9):
            ph = f / FR * 2 * math.pi
            x = 12 + i * 2
            hgt = 8 + 6 * (0.5 + 0.5 * math.sin(ph + i * 1.7)) * (1 - abs(i - 4) / 6)
            for y in range(int(hgt)):
                k = y / max(1, hgt)
                col = 'fire4' if k < 0.25 else 'fire3' if k < 0.55 else 'fire2' if k < 0.85 else 'fire1'
                c.px(x, 39 - y, col); c.px(x + 1, 39 - y, col)
        c.rect(12, 42, 27, 43, 'ember')
        out.append(c)
    return out


def forge_frames():
    out = []
    for f in range(FR):
        c = C(42, 44)
        c.ellipse(21, 41, 20, 3, (9, 27, 21, 70))
        box(c, 0, 14, 41, 41, 6, 'st_lt', 'st_md', 'st_ol')
        c.rect(14, 0, 27, 14, 'st_ol'); c.rect(15, 1, 26, 14, 'st_dk'); c.rect(15, 1, 26, 1, 'st_md')   # hood
        c.rect(4, 16, 37, 20, 'soot')
        for x in range(5, 37):
            v = 0.5 + 0.5 * math.sin(f / FR * 2 * math.pi + x * 0.9)
            c.px(x, 17, 'fire1' if v > 0.75 else 'fire2'); c.px(x, 18, 'fire3' if v > 0.4 else 'fire2'); c.px(x, 19, 'fire4')
        c.rect(5, 26, 36, 38, 'st_dk')
        for y in range(28, 38, 3): c.rect(6, y, 35, y, 'st_ol')
        c.rect(30, 8, 40, 12, 'w_dk'); c.rect(32, 6, 40, 8, 'w')                                        # bellows
        out.append(c)
    return out


def anvil():
    c = C(24, 18); shadow(c, 12, 16, 10)
    c.rect(8, 9, 15, 16, 'w_dk'); c.rect(8, 9, 15, 9, 'w')                       # stump
    c.rect(2, 3, 21, 7, 'iron_dk'); c.rect(3, 3, 19, 4, 'iron_hi'); c.rect(0, 4, 3, 6, 'iron')
    c.rect(9, 7, 14, 9, 'iron_dk')
    c.rect(15, 1, 21, 2, 'w_dk'); c.rect(19, 0, 21, 3, 'iron')                  # hammer
    return c


def weapon_rack():
    c = C(32, 36); shadow(c, 16, 34, 15)
    c.rect(0, 26, 31, 33, 'w_ol'); c.rect(1, 27, 30, 32, 'w'); c.rect(1, 27, 30, 27, 'w_lt')
    c.rect(1, 6, 30, 8, 'w_dk')
    for i, x in enumerate((5, 12, 19, 26)):
        if i % 2 == 0:                                                           # sword
            c.rect(x, 0, x + 1, 24, 'iron_hi'); c.rect(x + 1, 0, x + 1, 24, 'iron'); c.rect(x - 2, 20, x + 3, 21, 'gold')
            c.rect(x, 22, x + 1, 26, 'w_dk')
        else:                                                                    # spear
            c.rect(x, 4, x, 27, 'w_mid'); c.rect(x - 1, 0, x + 1, 4, 'iron_hi')
    return c


def armor_stand():
    c = C(20, 36); shadow(c, 10, 34, 8)
    c.rect(9, 20, 10, 33, 'w_dk'); c.rect(5, 32, 14, 33, 'w_ol')
    c.ellipse(10, 6, 4, 4, 'iron_dk'); c.ellipse(10, 5.5, 3, 3, 'iron_hi'); c.rect(8, 6, 12, 6, 'soot')     # helm
    c.rect(4, 10, 15, 21, 'iron_dk'); c.rect(5, 11, 14, 20, 'iron'); c.rect(6, 11, 9, 16, 'iron_hi')
    c.rect(4, 12, 15, 13, 'iron_dk'); c.rect(9, 14, 10, 20, 'red')
    return c


def dummy():
    c = C(20, 32); shadow(c, 10, 30, 7)
    c.rect(9, 12, 10, 30, 'w_dk'); c.rect(2, 13, 17, 14, 'w')
    c.ellipse(10, 6, 5, 5, 'w_ol'); c.ellipse(10, 6, 4, 4, 'yl_dk'); c.rect(7, 5, 8, 5, 'w_ol'); c.rect(12, 5, 13, 5, 'w_ol')
    c.rect(5, 14, 14, 24, 'w_ol'); c.rect(6, 15, 13, 23, 'yl_dk'); c.rect(6, 18, 13, 18, 'w_mid'); c.rect(6, 21, 13, 21, 'w_mid')
    c.rect(4, 28, 15, 30, 'w_ol')
    return c


def altar():
    c = C(40, 30); shadow(c, 20, 28, 18)
    box(c, 0, 10, 39, 28, 5, 'st_hi', 'st_lt', 'st_ol')
    c.rect(2, 11, 37, 13, 'sheet'); c.rect(14, 16, 25, 28, 'rug'); c.rect(14, 16, 25, 17, 'rug_b')
    c.rect(19, 0, 20, 10, 'gold'); c.rect(16, 3, 23, 4, 'gold'); c.px(19, 0, 'gold_hi')          # holy symbol
    c.rect(5, 6, 7, 11, 'sn'); c.px(6, 5, 'fire2'); c.rect(32, 6, 34, 11, 'sn'); c.px(33, 5, 'fire2')
    return c


def pew():
    c = C(46, 16); shadow(c, 23, 14, 21)
    c.rect(0, 0, 45, 6, 'w_ol'); c.rect(1, 1, 44, 5, 'w'); c.rect(1, 1, 44, 1, 'w_lt')
    box(c, 0, 6, 45, 12, 2, 'w_lt', 'w_dk')
    for x in (2, 42): c.rect(x, 12, x + 1, 14, 'w_ol')
    return c


def lectern():
    c = C(16, 24); shadow(c, 8, 22, 6)
    c.rect(6, 10, 9, 22, 'w_dk'); c.rect(3, 21, 12, 22, 'w_ol')
    c.rect(1, 4, 14, 10, 'w_ol'); c.rect(2, 5, 13, 9, 'w')
    c.rect(2, 2, 13, 6, 'sheet'); c.rect(7, 2, 8, 6, 'sheet_dk'); c.rect(3, 3, 6, 3, 'st_md'); c.rect(9, 3, 12, 3, 'st_md')
    return c


def globe():
    c = C(18, 26); shadow(c, 9, 24, 7)
    c.rect(8, 15, 9, 23, 'w_dk'); c.rect(4, 22, 13, 23, 'w_ol')
    c.ellipse(9, 8, 7, 7, 'w_ol'); c.ellipse(9, 8, 6, 6, 'wa'); c.ellipse(7, 6, 3, 2, 'g_lt'); c.ellipse(11, 10, 2, 2, 'g_md')
    c.px(6, 4, 'sn')
    return c


def candle_frames():
    out = []
    for f in range(FR):
        c = C(10, 24); shadow(c, 5, 22, 4)
        c.rect(4, 8, 5, 21, 'iron_dk'); c.rect(1, 20, 8, 22, 'iron_dk'); c.rect(1, 7, 8, 8, 'iron')
        c.rect(3, 3, 6, 7, 'sn'); c.rect(3, 3, 3, 7, 'sheet_dk')
        fl = 1 + (f % 3 == 0)
        c.px(4 + (f % 2), 2 - fl, 'fire1'); c.rect(4, 1, 5, 2, 'fire2'); c.px(4, 0, 'fire1') if f % 2 else None
        out.append(c)
    return out


def cauldron_frames():
    out = []
    for f in range(FR):
        c = C(22, 22); shadow(c, 11, 20, 9)
        c.ellipse(11, 13, 10, 7, 'st_ol'); c.ellipse(11, 12, 9, 6, 'iron_dk')
        c.ellipse(11, 8, 9, 3, 'st_ol'); c.ellipse(11, 8, 8, 2, 'g_lt')
        for i in range(3):
            y = 6 - ((f + i * 2) % FR) // 2
            c.px(6 + i * 4, y, 'g_hi')
        for x in (5, 9, 13, 17): c.px(x, 20, 'fire3'); c.px(x, 19, 'fire2')
        out.append(c)
    return out


def kegs():
    c = C(30, 30); shadow(c, 15, 28, 14)
    c.rect(1, 8, 28, 28, 'w_ol'); c.rect(2, 9, 27, 27, 'w_dk')
    for (x, y) in ((8, 15), (21, 15), (14.5, 22)):
        c.ellipse(x, y, 6, 6, 'w_ol'); c.ellipse(x, y, 5, 5, 'w'); c.ellipse(x, y, 3, 3, 'w_lt'); c.px(int(x), int(y), 'iron_dk')
    c.rect(1, 6, 28, 8, 'w'); c.rect(1, 6, 28, 6, 'w_lt')
    return c


def counter():
    c = C(64, 26); shadow(c, 32, 24, 30)
    box(c, 0, 4, 63, 24, 7, 'w_lt', 'w')
    for x in range(4, 62, 10): c.rect(x, 13, x, 23, 'w_dk')
    c.rect(8, 0, 11, 6, 'sn'); c.rect(8, 0, 11, 1, 'yl'); c.rect(20, 1, 23, 6, 'sn')                  # mugs
    c.rect(40, 0, 42, 6, 'g_md'); c.rect(41, -1, 41, 0, 'w_dk'); c.rect(50, 2, 56, 6, 'yl_dk')
    return c


def nightstand():
    c = C(14, 18); shadow(c, 7, 16, 6)
    box(c, 0, 4, 13, 16, 3, 'w_lt', 'w'); c.rect(2, 9, 11, 9, 'w_dk'); c.px(6, 11, 'gold')
    c.rect(5, 0, 7, 4, 'sn'); c.px(6, 0, 'fire2')
    return c


def plant():
    c = C(16, 22); shadow(c, 8, 20, 6)
    c.rect(4, 13, 11, 20, 'tl_dk'); c.rect(4, 13, 11, 14, 'tl_b')
    for (x, y, r) in ((8, 8, 5), (5, 10, 3), (11, 10, 3), (8, 4, 3)):
        c.ellipse(x, y, r, r, 'g_dk2'); c.ellipse(x - 0.5, y - 0.5, r - 1, r - 1, 'g_md')
    for (x, y) in ((6, 6), (10, 8), (8, 3)): c.px(x, y, 'g_lt')
    c.px(7, 9, 'pk'); c.px(10, 5, 'pk')
    return c


def sacks():
    c = C(22, 18); shadow(c, 11, 16, 10)
    for (x, y) in ((7, 10), (15, 11), (11, 6)):
        c.ellipse(x, y, 5, 5, 'w_ol'); c.ellipse(x, y, 4, 4, 'pl_md'); c.ellipse(x - 1, y - 1, 2, 2, 'pl')
        c.rect(x - 1, y - 5, x + 1, y - 4, 'w_dk')
    return c


def hay():
    c = C(26, 18); shadow(c, 13, 16, 12)
    box(c, 0, 2, 25, 16, 5, 'yl', 'yl_dk', 'w_dk')
    for x in range(2, 24, 3): c.px(x, 4, 'w_lt'); c.rect(x, 9, x, 14, 'w_lt')
    c.rect(7, 2, 8, 16, 'w_dk'); c.rect(17, 2, 18, 16, 'w_dk')
    return c


def chest_closed():
    return None   # the world's chest_anim_16x16 is reused


def window():
    c = C(22, 20)
    c.rect(0, 0, 21, 19, 'w_ol'); c.rect(1, 1, 20, 18, 'w')
    c.rect(3, 3, 18, 15, 'glass_dk'); c.rect(4, 4, 17, 14, 'glass')
    c.rect(10, 3, 11, 15, 'w'); c.rect(3, 9, 18, 9, 'w')
    c.px(5, 5, 'sn'); c.px(6, 5, 'sn'); c.px(5, 6, 'sn'); c.px(13, 5, 'sn')
    c.rect(0, 16, 21, 19, 'w_lt'); c.rect(0, 19, 21, 19, 'w_dk')
    c.px(4, 15, 'pk'); c.px(8, 15, 'g_lt'); c.px(15, 15, 'yl'); c.px(17, 15, 'g_lt')
    return c


def window_night():
    c = window()
    c.rect(4, 4, 9, 8, 'night'); c.rect(12, 4, 17, 8, 'night'); c.rect(4, 10, 9, 14, 'night'); c.rect(12, 10, 17, 14, 'night')
    c.px(6, 5, 'sn'); c.px(15, 11, 'yl')
    return c


def painting():
    c = C(22, 16)
    c.rect(0, 0, 21, 15, 'gold'); c.rect(1, 1, 20, 14, 'yl_dk')
    c.rect(2, 2, 19, 13, 'wa'); c.rect(2, 9, 19, 13, 'g_md'); c.ellipse(8, 9, 5, 3, 'g_dk'); c.ellipse(15, 8, 4, 3, 'st')
    c.ellipse(15, 6.5, 2, 1, 'sn'); c.px(16, 4, 'yl')
    return c


def banner():
    c = C(18, 28)
    c.rect(0, 0, 17, 1, 'w_dk')
    c.rect(2, 2, 15, 22, 'rug'); c.rect(2, 2, 15, 3, 'rug_dk')
    for y in range(22, 27): c.rect(2 + (y - 22), y, 15 - (y - 22), y, 'rug')
    c.rect(8, 7, 9, 18, 'gold'); c.rect(5, 10, 12, 11, 'gold')
    return c


def stained():
    c = C(30, 30)
    c.ellipse(15, 15, 14, 14, 'st_ol'); c.ellipse(15, 15, 13, 13, 'st_dk')
    cols = ['rug', 'rug2', 'gold', 'g_md', 'pu_lt', 'glass']
    for y in range(3, 28):
        for x in range(3, 28):
            if (x - 15) ** 2 + (y - 15) ** 2 <= 144:
                a = math.atan2(y - 15, x - 15); r = math.hypot(x - 15, y - 15)
                seg = int((a + math.pi) / (2 * math.pi) * 8)
                c.px(x, y, 'gold_hi' if r < 3 else cols[(seg + (r > 8)) % len(cols)])
                if int(r) in (3, 8) or (int((a + math.pi) / (2 * math.pi) * 64) % 8 == 0): c.px(x, y, 'st_ol')
    return c


def crate():
    c = C(16, 16); shadow(c, 8, 14, 7)
    box(c, 0, 1, 15, 14, 4, 'w_lt', 'w'); c.rect(1, 6, 14, 6, 'w_dk'); c.rect(1, 10, 14, 10, 'w_dk')
    c.rect(1, 6, 14, 13, 'w'); c.rect(2, 7, 13, 12, 'w_dk'); c.rect(3, 8, 12, 11, 'w')
    return c


def barrel():
    c = C(16, 18); shadow(c, 8, 16, 7)
    c.rect(1, 3, 14, 16, 'w_ol'); c.rect(2, 3, 13, 15, 'w'); c.rect(2, 3, 4, 15, 'w_lt'); c.rect(11, 3, 13, 15, 'w_dk')
    c.rect(1, 6, 14, 6, 'iron_dk'); c.rect(1, 12, 14, 12, 'iron_dk')
    c.ellipse(7.5, 3, 6, 2, 'w_ol'); c.ellipse(7.5, 2.8, 5, 1.4, 'w_mid')
    return c


# ============================================================== light + UI bits
def light_radial(n=64):
    c = C(n, n)
    for y in range(n):
        for x in range(n):
            r = math.hypot(x + 0.5 - n / 2, y + 0.5 - n / 2) / (n / 2)
            if r >= 1: continue
            v = (1 - r) ** 1.6
            v = round(v * 6) / 6                               # pixel-art banding (6 steps)
            if v > 0: c.a[y, x] = (255, 255, 255, int(255 * v))
    return c


def icons():
    """16x16: sun, moon, sword, bow, potion slot, shield, boot, star(dex), heart(vit), skull"""
    out = []
    def ic(): return C(16, 16)
    s = ic(); s.ellipse(8, 8, 4, 4, 'fire2'); s.ellipse(7.5, 7.5, 3, 3, 'fire1')
    for a in range(8):
        dx, dy = math.cos(a * math.pi / 4), math.sin(a * math.pi / 4)
        s.px(8 + dx * 6.5, 8 + dy * 6.5, 'fire2')
    out.append(s)
    m = ic(); m.ellipse(8, 8, 5, 5, 'sn'); m.ellipse(10.5, 6.5, 4, 4, (0, 0, 0, 0)); m.px(5, 8, 'sn_md'); m.px(6, 11, 'sn_md')
    # moon: clear the bite properly
    for y in range(16):
        for x in range(16):
            if (x - 10.5) ** 2 + (y - 6.5) ** 2 <= 14: m.a[y, x] = 0
    m.outline('st_dk'); out.append(m)
    sw = ic()
    for i in range(9): sw.px(4 + i, 11 - i, 'iron_hi'); sw.px(5 + i, 11 - i, 'iron')
    sw.rect(2, 10, 6, 11, 'gold'); sw.rect(3, 12, 4, 13, 'w_dk'); sw.outline('st_ol'); out.append(sw)
    sh = ic(); sh.rect(4, 3, 11, 9, 'iron');
    for y in range(9, 14): sh.rect(4 + (y - 9), y, 11 - (y - 9), y, 'iron')
    sh.rect(7, 4, 8, 11, 'gold'); sh.rect(5, 6, 10, 6, 'gold'); sh.outline('st_ol'); out.append(sh)
    bt = ic(); bt.rect(5, 3, 9, 10, 'w'); bt.rect(5, 10, 12, 12, 'w'); bt.rect(5, 3, 9, 4, 'w_lt'); bt.outline('w_ol'); out.append(bt)
    st = ic()
    pts = [(8 + 6 * math.cos(-math.pi / 2 + k * math.pi * 4 / 5), 8 + 6 * math.sin(-math.pi / 2 + k * math.pi * 4 / 5)) for k in range(5)]
    for y in range(16):
        for x in range(16):
            inside = 0
            for i in range(5):
                (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % 5]
                if (y1 > y + .5) != (y2 > y + .5) and x + .5 < x1 + (y + .5 - y1) * (x2 - x1) / (y2 - y1): inside ^= 1
            if inside: st.px(x, y, 'gold_hi' if y < 7 else 'gold')
    st.outline('w_ol'); out.append(st)
    ht = ic()
    for y in range(16):
        for x in range(16):
            X, Y = (x - 7.5) / 6, (y - 6) / 6
            if (X * X + Y * Y - 0.6) ** 3 - X * X * Y ** 3 * 1.2 < 0 and y < 14: ht.px(x, y, 'red' if y > 5 else 'rug_hi')
    ht.outline('st_ol'); out.append(ht)
    bow = ic()
    for t in range(-6, 7): bow.px(6 + int(4 * (1 - (t / 6) ** 2)), 8 + t, 'w_mid')
    bow.rect(6, 2, 6, 14, 'sn'); bow.outline('w_ol'); out.append(bow)
    return out


# ============================================================== build
def build():
    for n, t in TEMPLATES.items(): render_shell(n, t)
    F('bed_double', bed(True)); F('bed_single', bed(False, ('blanket2', 'blanket2_dk'))); F('bunk', bunk())
    F('table_round', table_round()); F('table_long', table_long()); F('chair', chair()); F('stool', stool())
    F('bookshelf', bookshelf()); F('wardrobe', wardrobe()); F('cupboard', cupboard()); F('stove', stove())
    save(sheet(fireplace_frames(), 40, 46), f'{OUTI}Furniture/fireplace_anim_40x46.png')
    save(sheet(forge_frames(), 42, 44), f'{OUTI}Furniture/forge_anim_42x44.png')
    save(sheet(candle_frames(), 10, 24), f'{OUTI}Furniture/candle_anim_10x24.png')
    save(sheet(cauldron_frames(), 22, 22), f'{OUTI}Furniture/cauldron_anim_22x22.png')
    F('anvil', anvil()); F('weapon_rack', weapon_rack()); F('armor_stand', armor_stand()); F('dummy', dummy())
    F('altar', altar()); F('pew', pew()); F('lectern', lectern()); F('globe', globe()); F('kegs', kegs())
    F('counter', counter()); F('nightstand', nightstand()); F('plant', plant()); F('sacks', sacks()); F('hay', hay())
    F('crate', crate()); F('barrel', barrel())
    save(sheet([window(), window_night()], 22, 20), f'{OUTI}Furniture/window_22x20.png')
    F('painting', painting()); F('banner', banner()); F('stained', stained())
    # light + icons
    lp = os.path.join(ROOT, 'Assets', 'Art', 'Effects', 'light_radial.png'); light_radial().img().save(lp)
    ip = os.path.join(ROOT, 'Assets', 'Art', 'UI', 'Icons', 'ui_icons_rpg_16x16.png'); sheet(icons(), 16, 16).img().save(ip)
    write_layouts()
    preview()


def write_layouts():
    lines = ['# generated by Tools/ArtGen2/interiors.py  -  INTERIOR name w h floor wall / rows / ITEM name x y [wall]']
    for n, t in TEMPLATES.items():
        rows = t['rows']
        lines.append(f'INTERIOR {n} {len(rows[0])} {len(rows)}')
        lines += rows
        for it in t['items']:
            lines.append(f'ITEM {it[0]} {it[1]} {it[2]}' + (' wall' if len(it) > 3 else ''))
        lines.append('END')
    p = os.path.join(ROOT, 'Assets', 'Game', 'Levels', 'Interiors.txt')
    open(p, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')


def preview():
    """every room with its furniture at 2x"""
    from kit import OUT
    furn = {}
    for f in os.listdir(os.path.join(OUT, OUTI, 'Furniture')):
        if f.endswith('.png'):
            im = Image.open(os.path.join(OUT, OUTI, 'Furniture', f)).convert('RGBA')
            nm = f[:-4]
            if '_anim_' in nm or nm.startswith('window_'):
                w = int(nm.split('_')[-1].split('x')[0]); im = im.crop((0, 0, w, im.height)); nm = nm.split('_anim_')[0].replace('_22x20', '')
            furn[nm] = im
    chest = Image.open(os.path.join(OUT, 'Props', 'chest_anim_16x16.png')).convert('RGBA').crop((0, 0, 16, 16))
    furn['chest'] = chest
    rooms = []
    for n, t in TEMPLATES.items():
        room = Image.open(os.path.join(OUT, OUTI, f'room_{n}.png')).convert('RGBA')
        items = sorted(t['items'], key=lambda it: (0 if len(it) > 3 else 1, it[2]))
        for it in items:
            im = furn[it[0]]
            x = int(it[1] * T - im.width / 2); y = int(it[2] * T + T - im.height) if len(it) < 4 else int(it[2] * T - im.height / 2)
            room.alpha_composite(im, (max(0, x), max(0, y)))
        rooms.append(room)
    W = sum(r.width for r in rooms[:4]) + 8 * 4; H = max(r.height for r in rooms[:4]) + max(r.height for r in rooms[4:]) + 16
    sheet_ = Image.new('RGBA', (W, H), (12, 10, 20, 255))
    x = 4
    for r in rooms[:4]: sheet_.alpha_composite(r, (x, 4)); x += r.width + 8
    x = 4; y0 = max(r.height for r in rooms[:4]) + 12
    for r in rooms[4:]: sheet_.alpha_composite(r, (x, y0)); x += r.width + 8
    sheet_.resize((W * 2, H * 2), Image.NEAREST).save(os.path.join(ROOT, 'Documentation', 'Previews', 'interiors_preview.png'))


if __name__ == '__main__':
    build()
