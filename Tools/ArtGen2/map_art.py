"""Illustrated map art (2026-11-20) for the map screen (M) and the minimap, in the style of the user's reference:
a drawn fantasy map instead of a flat satellite picture - tree clusters for forests, snowy peaks, purple corrupted land,
sandy desert, ash and lava around the volcano, dithered ocean with a foam coastline, beige roads - plus sprite icons,
an ornate frame and a compass.

All art is drawn at "2x density": 1 art pixel = half a UI canvas pixel (the UI canvas is 320x180), like the HD font.

Outputs
  Assets/Art/World/MapArt/mapart_<MapId>.png   one per map (World 2 px per tile, towns/zone 4-5 px per tile)
  Assets/Art/UI/Map/ui_map_icons_16x16.png       0 city  1 village  2 tower  3 dungeon  4 quest  5 player arrow (up)
                                                 6 camp  7 shop  8 gate  9 road  10 boss  11 house
  Assets/Art/UI/Map/ui_map_frame_9s12.png        ornate navy/purple frame (9-slice, 12 px border)
  Assets/Art/UI/Map/ui_map_compass.png           "N" compass rose with a purple needle
usage: python Tools/ArtGen2/map_art.py
"""
import math, os
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LV = os.path.join(ROOT, 'Assets', 'Game', 'Levels')
OUT_MAP = os.path.join(ROOT, 'Assets', 'Art', 'World', 'MapArt')
OUT_UI = os.path.join(ROOT, 'Assets', 'Art', 'UI', 'Map')


def hx(s):
    s = s.lstrip('#'); return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


C = {k: np.array(hx(v), np.float32) for k, v in dict(
    grass='#5c9a3c', grass2='#4d8a35', forest='#2f6d36', forest2='#245a2e', corrupt='#5e3d82', corrupt2='#4a2f6a',
    snow='#e6eef5', snow2='#c7d4e2', desert='#dcb66c', desert2='#c99e55', ash='#4f4144', ash2='#3f3336', lava='#ef6a1f',
    lava2='#ffb340', cliff='#7c7a68', cliff2='#5d5b4c', acliff='#3a2d31', water='#3f86d6', water2='#5ea4ea', ocean='#22417e',
    ocean2='#1b3569', foam='#bfe0ff', swamp='#3e5a3b', swamp2='#4f6b45', road='#e3cf98', road2='#c7ae76', cobble='#a9a191',
    cobble2='#8f877a', farm='#b5853f', farm2='#9a6d30', wood='#8a5a32', outline='#1a1622',
    tree='#1f5a2a', tree_hi='#3f8a3a', tree_dk='#143d1e', ctree='#6a3f8f', ctree_hi='#9566c0', pine='#1d4f44', pine_hi='#3b7a62',
    palm='#3f8f3a', rock='#8d8a7c', rock_dk='#5e5b50', snowcap='#ffffff', roof_r='#b8433a', roof_b='#47669e', roof_t='#c49a52',
    wall='#9a9488', wall_dk='#6a655c', volc='#4a3436', volc_hi='#6e4e4c',
).items()}

TERRAIN = {  # char -> (base, alt) colour for the dithered fill
    '.': ('grass', 'grass2'), 'f': ('forest', 'forest2'), 'v': ('corrupt', 'corrupt2'), 'n': ('snow', 'snow2'),
    'C': ('snow2', 'snow'), 'd': ('desert', 'desert2'), 'a': ('ash', 'ash2'), 'L': ('lava', 'lava2'), 'k': ('acliff', 'ash2'),
    'c': ('cliff', 'cliff2'), 'w': ('water', 'water2'), 'O': ('ocean', 'ocean2'), 's': ('swamp', 'swamp2'),
    '_': ('road', 'road2'), 'p': ('cobble', 'cobble2'), 'F': ('farm', 'farm2'), '=': ('wood', 'wood'), 'H': ('wood', 'wood'),
    'D': ('wood', 'wood'),
}
GROUP = {c: i for i, c in enumerate('.fvnCdaLkcwOs_pF=HD')}


def load(mid):
    path = os.path.join(LV, 'World2.txt' if mid == 'World' else mid + '.txt')
    L = open(path, encoding='utf-8').read().splitlines()
    t0, e0 = L.index('TERRAIN'), L.index('ENTITIES')
    T = L[t0 + 1:e0]
    E = L[e0 + 1:e0 + 1 + len(T)]
    return T, E


def stamp(img, x, y, pattern, pal):
    """pattern: list of strings, '.' transparent; anchored at its bottom-centre on (x, y)"""
    h, w = len(pattern), len(pattern[0])
    H, W = img.shape[:2]
    x0, y0 = int(round(x - w / 2)), int(round(y - h))
    for j, row in enumerate(pattern):
        for i, ch in enumerate(row):
            if ch == '.' or ch not in pal: continue
            yy, xx = y0 + j, x0 + i
            if 0 <= yy < H and 0 <= xx < W: img[yy, xx] = pal[ch]


TREE_S = ['.o.', 'oho', 'odo']
TREE_L = ['..oo..', '.ohho.', 'ohhooo', 'oooodo', '.oddo.', '..t...']
PINE_S = ['.o.', 'oho', 'ooo']
PINE_L = ['..o..', '.oho.', '.ooo.', 'ohooo', 'ooood', '..t..']
MOUNT_S = ['...s...', '..sso..', '.srroo.', 'rrrrood']
MOUNT_L = ['.....s.....', '....sss....', '...ssrso...', '..srrrroo..', '.rrrrrrooo.', 'rrrrrrroooo', 'ddddddddddd']
VOLC = ['......ll......', '.....lLLl.....', '....vvvvvv....', '...vvhvvvvv...', '..vvhvvvvvvv..', '.vvhvvvvvvvvv.', 'vvvvvvvvvvvvvv']
HOUSE = ['..rrrr..', '.rrrrrr.', 'rrrrrrrr', '.wwwwww.', '.wwdwww.']
TOWER = ['o.o', 'www', 'www', 'wdw']


def paint(mid, s):
    T, E = load(mid)
    h, w = len(T), len(T[0])
    H, W = h * s, w * s
    ys, xs = np.mgrid[0:H, 0:W]
    ty, tx = ys // s, xs // s
    ter = np.array([[ch for ch in row] for row in T])
    cell = ter[ty, tx]
    img = np.zeros((H, W, 3), np.float32)
    rng = np.random.default_rng(len(mid))
    noise = rng.random((H, W))
    # base fill: two-tone dither per material (ordered on a 2x2 grid, broken up by noise)
    checker = ((xs + ys) % 2 == 0)
    for ch, (a, b) in TERRAIN.items():
        m = cell == ch
        if not m.any(): continue
        alt = m & ((checker & (noise < 0.35)) | (noise < 0.12))
        img[m] = C[a]; img[alt] = C[b]
    unknown = ~np.isin(cell, list(TERRAIN.keys()))
    img[unknown] = C['grass']
    # ocean: deeper further from land, foam line along the coast
    sea = cell == 'O'
    land = ~np.isin(cell, ['O', 'D'])
    from scipy import ndimage as nd
    dist = nd.distance_transform_edt(~land)
    img[sea & (dist > 6 * s / 2) & checker] = C['ocean2'] * 0.92
    img[sea & (dist <= 1.2)] = C['foam']
    img[sea & (dist > 1.2) & (dist <= 2.4) & checker] = C['water2'] * 0.8
    lake = np.isin(cell, ['w', 's'])
    dl = nd.distance_transform_edt(lake)
    img[lake & (dl <= 1)] = C['water2']
    # outlines between material groups (the hand-drawn look)
    grp = np.vectorize(lambda c: GROUP.get(c, 0))(cell)
    edge = np.zeros((H, W), bool)
    edge[1:, :] |= grp[1:, :] != grp[:-1, :]
    edge[:, 1:] |= grp[:, 1:] != grp[:, :-1]
    soft = np.isin(cell, ['.', 'f', '_', 'F', 'p', 'v', 'n', 'd', 'a'])
    img[edge & ~soft] *= 0.62
    img[edge & soft] *= 0.86
    # cliffs: dark lower lip
    cl = np.isin(cell, ['c', 'k', 'C'])
    below = np.zeros_like(cl); below[:-1] = cl[1:]
    img[cl & ~np.roll(cl, -s, axis=0)] *= 0.7
    out = img.clip(0, 255).astype(np.uint8)

    big = s >= 4
    pal = lambda *names: {k: tuple(int(v) for v in C[n]) for k, n in zip('ohdtsrlLvwbB', names)}
    p_tree = {'o': C['tree'], 'h': C['tree_hi'], 'd': C['tree_dk'], 't': C['wood']}
    p_ctree = {'o': C['ctree'], 'h': C['ctree_hi'], 'd': C['corrupt2'] * 0.7, 't': C['wood']}
    p_pine = {'o': C['pine'], 'h': C['pine_hi'], 'd': C['tree_dk'], 't': C['wood']}
    p_snowpine = {'o': C['pine'], 'h': C['snowcap'], 'd': C['tree_dk'], 't': C['wood']}
    p_dead = {'o': C['rock_dk'], 'h': C['rock'], 'd': C['acliff'], 't': C['wood']}
    p_palm = {'o': C['palm'], 'h': C['tree_hi'], 'd': C['tree_dk'], 't': C['wood']}
    p_mnt = {'s': C['snowcap'], 'r': C['rock'], 'o': C['rock_dk'], 'd': C['outline']}
    p_rock = {'s': C['rock'], 'r': C['rock'], 'o': C['rock_dk'], 'd': C['outline']}
    p_mesa = {'s': C['desert'], 'r': C['desert2'], 'o': C['farm2'], 'd': C['outline']}
    p_volc = {'l': C['lava2'], 'L': C['lava'], 'v': C['volc'], 'h': C['volc_hi']}
    p_wall = {'o': C['wall'], 'w': C['wall'], 'd': C['outline']}
    # forests read as tree clusters: a canopy on most forest / corrupted tiles
    r2 = np.random.default_rng(7)
    for y, row in enumerate(T):
        for x, t in enumerate(row):
            if t in 'fv' and E[y][x] == ' ' and r2.random() < 0.7:
                fx, fy = x * s + s / 2 + r2.integers(-1, 2), (y + 1) * s + r2.integers(0, 2)
                stamp(out, fx, fy, TREE_L if big else TREE_S, p_tree if t == 'f' else p_ctree)
    for y, row in enumerate(E):
        for x, c in enumerate(row):
            if c == ' ': continue
            fx, fy = x * s + s / 2, (y + 1) * s
            if c in 'TUtAGgq':
                stamp(out, fx, fy, TREE_L if big and c in 'TUA' else TREE_S, p_tree if c != 'A' else {**p_tree, 'o': C['roof_t'], 'h': C['lava2']})
            elif c in 'Vu':
                stamp(out, fx, fy, TREE_L if big and c == 'V' else TREE_S, p_ctree)
            elif c in 'iI':
                stamp(out, fx, fy, PINE_L if big else PINE_S, p_pine if c == 'i' else p_snowpine)
            elif c == 'k' and T[y][x] != 'k':
                stamp(out, fx, fy, TREE_S, p_dead)
            elif c == 'Y':
                stamp(out, fx, fy, TREE_S, p_palm)
            elif c in 'm^12':
                stamp(out, fx, fy, MOUNT_L if (c in 'm^' or big) else MOUNT_S, p_mnt)
            elif c in '3RW':
                stamp(out, fx, fy, MOUNT_S if c == '3' else ['.rr.', 'rroo'], p_rock if c != 'W' else p_mnt)
            elif c == '4':
                stamp(out, fx, fy, ['.rrrrr.', 'rrrrrrr', 'ooooooo'], p_mesa)
            elif c == '5':
                k = max(1, s // 2)
                pat = [''.join(ch * k for ch in r) for r in VOLC for _ in range(k)]
                stamp(out, fx, fy, pat, p_volc)
            elif c in '678':
                roof = {'6': 'roof_r', '7': 'roof_b', '8': 'roof_t'}[c]
                k = max(1, s // 3)
                pat = [''.join(ch * k for ch in r) for r in HOUSE for _ in range(k)]
                stamp(out, fx, fy, pat, {'r': C[roof], 'w': C['wall'], 'd': C['wood']})
            elif c in '#':
                stamp(out, fx + s / 2, fy, ['ww' * max(1, s // 2)] * max(2, s // 2), p_wall)
            elif c in '90xjJ':
                k = max(1, s // 3)
                pat = [''.join(ch * k for ch in r) for r in TOWER for _ in range(k)]
                stamp(out, fx, fy, pat, {'o': C['wall'], 'w': C['wall'] if c != 'x' else C['corrupt2'], 'd': C['outline']})
    os.makedirs(OUT_MAP, exist_ok=True)
    Image.fromarray(out).save(os.path.join(OUT_MAP, f'mapart_{mid}.png'))
    return out.shape


# ====================================================================== UI pieces
def icons():
    N, S_ = 12, 16
    im = np.zeros((S_, S_ * N, 4), np.uint8)
    O = (26, 22, 34, 255)

    def px(i, pts, col):
        for (x, y) in pts:
            if 0 <= x < S_ and 0 <= y < S_: im[y, i * S_ + x] = col

    def rect(i, x0, y0, x1, y1, col): px(i, [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)], col)

    def outline(i):
        a = im[:, i * S_:(i + 1) * S_, 3] > 0
        ring = np.zeros_like(a)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ring |= np.roll(np.roll(a, dy, 0), dx, 1)
        ring &= ~a
        im[:, i * S_:(i + 1) * S_][ring] = O

    stone, stone_d, blue, gold = (196, 192, 184, 255), (132, 126, 120, 255), (72, 140, 230, 255), (255, 208, 90, 255)
    # 0 city: castle with a blue lake
    rect(0, 2, 11, 13, 13, blue); rect(0, 3, 6, 12, 11, stone); rect(0, 3, 3, 5, 6, stone); rect(0, 10, 3, 12, 6, stone)
    rect(0, 6, 2, 9, 6, stone_d); px(0, [(3, 2), (5, 2), (10, 2), (12, 2), (6, 1), (9, 1)], stone); rect(0, 7, 8, 8, 11, (60, 40, 40, 255))
    px(0, [(7, 0), (8, 0)], gold); outline(0)
    # 1 village: house
    rect(1, 4, 8, 11, 13, (226, 210, 170, 255)); px(1, [(x, 7 - abs(x - 7) // 1 + 0) for x in range(3, 13)], (0, 0, 0, 0))
    for y in range(3, 8):
        rect(1, 7 - (y - 3), y, 8 + (y - 3), y, (186, 68, 58, 255))
    rect(1, 7, 10, 8, 13, (110, 70, 40, 255)); rect(1, 5, 9, 5, 9, (255, 220, 120, 255)); outline(1)
    # 2 tower
    rect(2, 5, 4, 10, 14, stone); rect(2, 4, 2, 11, 4, stone_d); px(2, [(4, 1), (6, 1), (9, 1), (11, 1)], stone_d)
    rect(2, 7, 7, 8, 8, (40, 30, 50, 255)); rect(2, 7, 11, 8, 14, (90, 60, 40, 255)); outline(2)
    # 3 dungeon: purple spiral
    cx, cy = 7.5, 7.5
    for k in range(120):
        a = k / 120 * 4.2 * math.pi; r = 0.6 + k / 120 * 6.2
        x, y = int(round(cx + math.cos(a) * r)), int(round(cy + math.sin(a) * r))
        px(3, [(x, y)], (176, 92, 255, 255) if k % 20 < 14 else (110, 50, 190, 255))
    outline(3)
    # 4 quest "!"
    rect(4, 6, 1, 9, 10, (232, 50, 50, 255)); rect(4, 6, 12, 9, 14, (232, 50, 50, 255)); rect(4, 7, 1, 8, 8, (255, 120, 110, 255)); outline(4)
    # 5 player arrow (points up)
    for y in range(1, 15):
        half = (y - 1) // 2 if y < 11 else 5 - (y - 11) * 2
        if half < 0: continue
        rect(5, 7 - half, y, 8 + half, y, (70, 160, 255, 255))
    rect(5, 7, 2, 8, 9, (190, 230, 255, 255)); outline(5)
    # 6 camp: fire
    rect(6, 4, 12, 11, 13, (110, 70, 40, 255))
    for y in range(3, 12):
        half = (y - 3) // 2
        rect(6, 7 - half, y, 8 + half, y, (255, 120, 40, 255))
    rect(6, 7, 6, 8, 11, (255, 220, 90, 255)); outline(6)
    # 7 shop: coin bag
    for y in range(5, 14):
        half = min(5, (y - 4) + 1) if y < 10 else 5 - (y - 10) // 2
        rect(7, 7 - half, y, 8 + half, y, (190, 140, 70, 255))
    rect(7, 6, 3, 9, 4, (150, 100, 50, 255)); rect(7, 7, 8, 8, 11, gold); outline(7)
    # 8 gate: arch door with an arrow
    rect(8, 3, 3, 12, 14, stone); rect(8, 5, 6, 10, 14, (60, 40, 60, 255)); rect(8, 6, 5, 9, 5, (60, 40, 60, 255))
    rect(8, 7, 8, 8, 12, (127, 230, 255, 255)); px(8, [(6, 9), (9, 9)], (127, 230, 255, 255)); outline(8)
    # 9 road: beige wiggle
    for x in range(1, 15):
        y = int(round(7.5 + 3 * math.sin(x / 14 * 2 * math.pi)))
        rect(9, x, y - 1, x, y + 1, (227, 207, 152, 255))
    outline(9)
    # 10 boss: skull
    rect(10, 4, 3, 11, 10, (236, 232, 220, 255)); rect(10, 5, 11, 10, 13, (236, 232, 220, 255))
    rect(10, 5, 6, 6, 8, (180, 30, 40, 255)); rect(10, 9, 6, 10, 8, (180, 30, 40, 255)); px(10, [(6, 12), (8, 12)], O); outline(10)
    # 11 house (town plan legend)
    rect(11, 3, 8, 12, 13, (226, 210, 170, 255))
    for y in range(3, 8): rect(11, 7 - (y - 3) - 1, y, 8 + (y - 3) + 1, y, (71, 102, 158, 255))
    rect(11, 7, 10, 8, 13, (110, 70, 40, 255)); outline(11)
    os.makedirs(OUT_UI, exist_ok=True)
    Image.fromarray(im, 'RGBA').save(os.path.join(OUT_UI, 'ui_map_icons_16x16.png'))


def frame():
    S_, B = 48, 12
    im = np.zeros((S_, S_, 4), np.uint8)
    navy, navy2, purple, purple_hi, gold = (24, 20, 44, 245), (34, 28, 62, 245), (96, 58, 150, 255), (170, 120, 230, 255), (226, 186, 96, 255)
    im[:, :] = navy
    im[1:-1, 1:-1] = navy2
    for k, col in ((0, (10, 8, 18, 255)), (2, purple), (3, purple_hi), (4, purple), (B - 2, (60, 40, 96, 255))):
        im[k, k:S_ - k] = col; im[S_ - 1 - k, k:S_ - k] = col; im[k:S_ - k, k] = col; im[k:S_ - k, S_ - 1 - k] = col
    im[B:S_ - B, B:S_ - B] = (18, 15, 32, 235)
    # ornate corners: a diamond with a gem
    for (cx, cy) in ((5, 5), (S_ - 6, 5), (5, S_ - 6), (S_ - 6, S_ - 6)):
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                d = abs(dx) + abs(dy)
                if d <= 4: im[cy + dy, cx + dx] = purple if d >= 3 else gold
        im[cy, cx] = purple_hi
    Image.fromarray(im, 'RGBA').save(os.path.join(OUT_UI, 'ui_map_frame_9s12.png'))


def compass():
    S_ = 32
    im = np.zeros((S_, S_, 4), np.uint8)
    c = 15.5
    for y in range(S_):
        for x in range(S_):
            r = math.hypot(x - c, y - c)
            if 9.5 < r < 11.5: im[y, x] = (196, 172, 120, 255)
            elif 11.5 <= r < 12.6: im[y, x] = (26, 22, 34, 255)
    # needle: purple north, grey south
    for y in range(4, 28):
        half = int((12 - abs(y - 16)) / 4)
        for x in range(int(c) - half, int(c) + half + 2):
            im[y, x] = (176, 92, 255, 255) if y < 16 else (150, 146, 160, 255)
    # "N" on top
    for y in range(0, 6):
        im[y, 12] = im[y, 19] = (255, 255, 255, 255)
        im[y, 12 + int(y * 7 / 5)] = (255, 255, 255, 255)
    Image.fromarray(im, 'RGBA').save(os.path.join(OUT_UI, 'ui_map_compass.png'))


if __name__ == '__main__':
    cat = open(os.path.join(LV, 'Maps.txt'), encoding='utf-8').read().splitlines()
    for l in cat:
        if not l.startswith('MAP '): continue
        p = l.split()
        mid, w, h = p[1], int(p[3]), int(p[4])
        s = 2 if mid == 'World' else max(2, min(448 // w, 298 // h))
        print(mid, 'px/tile', s, paint(mid, s))
    icons(); frame(); compass()
    print('ui map art ok')
