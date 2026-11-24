"""Vegetation, props, decorations, waterfall (pixel_16 woods style)."""
import math
import numpy as np
from lib import *

K = {  # ASCII key shared by hand-drawn sprites
    'K': 'd_ol', 'k': 'd_dk2', 'D': 'd_dk', 'B': 'd_br', 'R': 'd_rd', 'L': 'd_md2', 'l': 'd_md', 'h': 'd_hi',
    'S': 's_ol', 's': 's_dk2', 't': 's_dk', 'm': 's_md', 'n': 's_wm', 'o': 's', 'p': 's_lt', 'q': 's_hi',
    'G': 'g_ol', 'g': 'g_dk', 'v': 'g_md', 'w': 'g', 'x': 'g_lt', 'z': 'g_hi',
    'y': 'y', 'Y': 'o', 'F': 'or_', 'r': 'c_red', 'e': 'c_red2', 'b': 'c_bld', 'E': 'c_red3',
    'u': 'w', 'U': 'w_lt', 'W': 'w_fo', 'i': 'w_md', 'j': 'w_dk',
    'P': 'pu', 'Q': 'pu_dk', 'a': 'blk', 'A': 'wht', 'c': 'c_wht', 'C': 'c_gry',
    '1': 'wd_lt', '2': 'wd', '3': 'wd_md', '4': 'wd_dk', '5': 'wd_ol', '6': 'pk', '7': 'sk',
    '#': 'blk', '-': 'c_blk',
}


def spr(w, h, rows, ox=None, oy=None, shadow=None, flip=False):
    c = Canvas(w, h)
    rw = max(len(r) for r in rows)
    ox = (w - rw) // 2 if ox is None else ox
    oy = h - len(rows) - 1 if oy is None else oy
    if shadow:
        cx, cy, rx, ry = shadow
        c.ellipse(cx, cy, rx, ry, SHADOW)
    tmp = Canvas(w, h)
    tmp.sprite(rows, K, ox, oy, flip)
    c.paste(tmp, 0, 0)
    return c


# ------------------------------------------------------------- shapes -----
def blob(c, circles, cols, outline, light=(-0.6, -0.8), dither=True, seed=0):
    """Union of circles shaded with top-left light (like the woods canopies).
    cols = (hi, base, mid, dark, deep)"""
    hi, base, mid, dark, deep = cols
    H, W = c.h, c.w
    m = np.zeros((H, W), bool)
    shade = np.full((H, W), -9.0)
    best = np.full((H, W), -9.0)
    for (cx, cy, r) in circles:
        for y in range(H):
            for x in range(W):
                dx, dy = (x + .5 - cx) / r, (y + .5 - cy) / r
                d2 = dx * dx + dy * dy
                if d2 <= 1:
                    m[y, x] = True
                    score = (1 - d2) * r - cy * .15  # front/top-most circle wins
                    if score > best[y, x]:
                        best[y, x] = score
                        nz = math.sqrt(1 - d2)
                        shade[y, x] = (dx * light[0] + dy * light[1]) * .9 + nz * .55
    tmp = Canvas(W, H)
    for y in range(H):
        for x in range(W):
            if not m[y, x]:
                continue
            s = shade[y, x] + (hash2(x, y, seed) - .5) * (.35 if dither else 0)
            col = hi if s > .95 else base if s > .45 else mid if s > .05 else dark if s > -.35 else deep
            tmp.px(x, y, col)
    tmp.outline(outline)
    c.paste(tmp, 0, 0)
    return m


def leaf_clumps(c, m, col, seed, n=10, ox=0):
    """little curved strokes inside canopies, like the woods tree texture"""
    r = rng(seed)
    ys, xs = np.nonzero(m)
    for i in range(n):
        k = r.integers(len(xs))
        x, y = xs[k], ys[k]
        for dx, dy in ((0, 0), (1, 0), (2, -1)):
            if 0 <= y + dy < c.h and 0 <= x + dx < c.w and m[y + dy, x + dx]:
                c.px(x + dx, y + dy, col)


# ------------------------------------------------------------ vegetation ---
def bush_berry():
    c = Canvas(16, 16)
    c.ellipse(8, 14, 6, 2, SHADOW)
    m = blob(c, [(5.5, 9, 4.2), (10.5, 9, 4.2), (8, 6.5, 4.5)], ('g_hi', 'g_lt', 'g', 'g_md', 'g_dk'), 'g_ol', seed=3)
    for (x, y) in [(5, 8), (10, 6), (11, 10), (7, 11), (8, 4)]:
        c.px(x, y, 'c_red'); c.px(x, y - 1 if (x + y) % 2 else y, 'pk')
        c.px(x + 1, y, 'c_red2')
    return c


def bush_large():
    c = Canvas(32, 24)
    c.ellipse(16, 21, 13, 3, SHADOW)
    m = blob(c, [(8, 14, 6.5), (16, 11, 8), (24.5, 14, 6.5), (12, 16, 5.5), (21, 16, 5.5)],
             ('g_hi', 'g_lt', 'g', 'g_md', 'g_dp'), 'g_ol', seed=5)
    leaf_clumps(c, m, 'g_md', 7, 9)
    return c


def bush_round_small():
    c = Canvas(16, 16)
    c.ellipse(8, 14, 5, 2, SHADOW)
    m = blob(c, [(8, 9, 5.2)], ('g_hi', 'g_lt', 'g', 'g_md', 'g_dk'), 'g_ol', seed=9)
    leaf_clumps(c, m, 'g_md', 9, 3)
    return c


def dead_tree():
    rows = [
        "......5..........5.....5........",
        ".....525........525...525.......",
        "......525.......525..525........",
        "..5....525..5...525.525....5....",
        ".525....525525...52525....525...",
        "..525...52235...5235....5235....",
        "...525..5235...52235...5235.....",
        "....5255235...52335..55235......",
        ".....522235..52335..52235.......",
        "......5223555233555522335.......",
        ".......522322233322223355.......",
        "........5222223332222355........",
        ".........55122233322355.........",
        "...........5122333235...........",
        "...........51223332345..........",
        "...........51223333345..........",
        "...........51223343345..........",
        "...........51223443345..........",
        "...........51223333345..........",
        "...........51233333345..........",
        "...........51223333345..........",
        "...........51223334345..........",
        "...........51223344345..........",
        "...........51223333345..........",
        "...........51223333345..........",
        "..........551223333345..........",
        "..........51223333334455........",
        ".........5512233333344445.......",
        "........52211233333334445.......",
        "........5555555555555555........",
    ]
    c = Canvas(32, 40)
    c.ellipse(16, 37.5, 10, 2.5, SHADOW)
    t = Canvas(32, 40); t.sprite(rows, K, 0, 9)
    c.paste(t, 0, 0)
    return c


def fallen_log():
    c = Canvas(32, 16)
    c.ellipse(16, 13, 14, 2.2, SHADOW)
    rows = [
        "...KKKKKKKKKKKKKKKKKKKKKKK....",
        "..KRRRRlRRRRRRlRRRRRlRRRRKKK..",
        ".KBRRBBBBRRBBBBBRRBBBBRRBKlhK.",
        ".KBBBDBBBBBDBBBBBBDBBBBBKlLLlK",
        ".KBBBBBBDBBBBBBDBBBBBDBBKLRRlK",
        ".KDBBDBBBBBBDBBBBBBBBBBBKlRRLK",
        ".KDDDDDBDDDDDDDBDDDDDDDDKLllLK",
        "..KkkkkkkkkkkkkkkkkkkkkkkKKKK.",
        "...KKKKKKKKKKKKKKKKKKKKKK.....",
    ]
    t = spr(32, 16, rows, ox=1, oy=4)
    c.paste(t, 0, 0)
    # moss
    for x in (6, 7, 14, 21, 22):
        c.px(x, 4, 'g_md'); c.px(x, 5, 'g') if x % 2 else None
    return c


def tall_grass_sway():
    """3 tufts x 4 frames, 16x16"""
    frames = []
    tufts = [
        [(-4, 7, 'g_md'), (-2, 9, 'g'), (0, 10, 'g_md'), (2, 8, 'g_lt'), (4, 6, 'g_md')],
        [(-3, 8, 'g_dk'), (-1, 11, 'g_md'), (1, 9, 'g'), (3, 7, 'g_md')],
        [(-5, 5, 'g_md'), (-3, 8, 'g'), (-1, 9, 'g_md'), (1, 11, 'g_lt'), (3, 8, 'g_md'), (5, 6, 'g_dk')],
    ]
    for tf in tufts:
        for f in range(4):
            sway = [0, 1, 0, -1][f]
            c = Canvas(16, 16)
            c.ellipse(8, 14.5, 5, 1.3, SHADOW)
            for (bx, ln, col) in tf:
                lean = bx * .18
                for i in range(ln):
                    p = i / max(1, ln - 1)
                    x = 8 + bx + (lean + sway * .9) * p * p * ln * .35
                    y = 14 - i
                    c.px(round(x), y, col if i > 1 else 'g_dk')
            frames.append(c)
    return frames


def flowers():
    sets = [('w_lt', 'w_bl', 'y'), ('pk', 'pu', 'y'), ('c_wht', 'c_gry', 'o'), ('o', 'or_', 'y')]
    out = []
    for (a, b, ctr) in sets:
        c = Canvas(16, 16)
        for (x, y) in [(4, 6), (10, 4), (8, 10)]:
            c.ellipse(x + .5, y + 3, 2.5, 1, (0, 0, 0, 37))
            c.px(x, y + 1, 'g_md'); c.px(x, y + 2, 'g_dk')
            for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                c.px(x + dx, y + dy - 1, a)
            c.px(x + 1, y, b); c.px(x - 1, y - 2, b) if False else None
            c.px(x, y - 1, ctr)
        out.append(c)
    return out


def sapling():
    c = Canvas(16, 16)
    c.ellipse(8, 14, 4, 1.5, SHADOW)
    rows = [
        "...GG.....",
        "..GxwG.GG.",
        "..GwvG.GxwG",
        "...GGD.GwvG",
        ".GG..D.GG.",
        "GxwG.DD...",
        "GwvGGD....",
        ".GG..D....",
        "....KDK...",
    ]
    c.paste(spr(16, 16, rows, ox=3, oy=4), 0, 0)
    return c


# ------------------------------------------------------------------ props --
def barrel():
    rows = [
        "...KKKKKKKK...",
        "..KhllllllLK..",
        ".KLlRRRRRRlLK.",
        ".KDLllllllLDK.",
        ".KsttttttttsK.",
        ".KBRllRRRBBDK.",
        ".KBRlRRRRBBDK.",
        ".KBRlRRRBBBDK.",
        ".KsttttttttsK.",
        ".KBRlRRRBBBDK.",
        ".KDBRRBBBBDDK.",
        "..KKKKKKKKKK..",
    ]
    return spr(16, 16, rows, shadow=(8, 14, 6.5, 2))


def crate():
    rows = [
        ".KKKKKKKKKKKK.",
        ".KhllllllllLK.",
        ".KlLLLLLLLLRK.",
        ".KKKKKKKKKKKK.",
        ".KRlKRRRRKlBK.",
        ".KRBlKRRKlBBK.",
        ".KRBBlKKlBBDK.",
        ".KRBBKllKBBDK.",
        ".KRBKlBBlKBDK.",
        ".KRKlBBBBlKDK.",
        ".KDDDDDDDDDDK.",
        ".KKKKKKKKKKKK.",
    ]
    return spr(16, 16, rows, shadow=(8, 14, 7, 2))


def pots():
    whole = [
        "....KKKK....",
        "...KlhhlK...",
        "....KDDK....",
        "...KRllRK...",
        "..KRlhlLRK..",
        "..KRlLLRBK..",
        "..KBRRRBBK..",
        "...KBBBDK...",
        "....KKKK....",
    ]
    broken = [
        "............",
        "............",
        "............",
        "............",
        "....K.......",
        "...KlK..KK..",
        "..KRlK.KRLK.",
        "..KBRRKKBBK.",
        "..K.KKKDK.K.",
    ]
    return [spr(16, 16, whole, shadow=(8, 14, 4.5, 1.6)), spr(16, 16, broken, shadow=(8, 14, 5, 1.4))]


def chest_frames():
    base = [
        "KoBBBBKyKBBBoK",
        "KoRRRRKYKRRRoK",
        "KoBBBBBKBBBBoK",
        "KoDDDDDDDDDDoK",
        "KKKKKKKKKKKKKK",
    ]
    lids = [
        ["..KKKKKKKKKK..",
         ".KRllllllllRK.",
         ".KlRRRRRRRRlK.",
         ".KBBBBBBBBBBK.",
         "KKKKKKKKKKKKKK"],
        ["..KKKKKKKKKK..",
         ".KRllllllllRK.",
         ".KlRRRRRRRRlK.",
         "KKKKKKKKKKKKKK",
         "KaaaaaaaaaaaaK"],
        [".KKKKKKKKKKKK.",
         "KDkkkkkkkkkkDK",
         "KKKKKKKKKKKKKK",
         "KaYyaYyyaYyaaK",
         "KayYyyYyyyYyaK"],
        [".KKKKKKKKKKKK.",
         "KDkkkkkkkkkkDK",
         "KKKKKKKKKKKKKK",
         "KaYyAYyyaYyaaK",
         "KayYyyYyAyYyaK"],
    ]
    out = []
    for f, lid in enumerate(lids):
        c = spr(16, 16, lid + base, oy=4, shadow=(8, 14, 7.5, 2))
        if f == 3:
            for (x, y) in [(4, 3), (11, 2), (8, 1)]:
                c.px(x, y, 'wht'); c.px(x - 1, y, 'y'); c.px(x + 1, y, 'y'); c.px(x, y - 1, 'y'); c.px(x, y + 1, 'y')
        out.append(c)
    return out


def flame(c, cx, by, h, w, f, seed=0, cols=('y', 'o', 'or_', 'c_red2')):
    """procedural pixel flame, base at by, f = frame 0..3"""
    for i in range(h):
        p = i / h
        wob = math.sin(f * 1.57 + i * .9 + seed) * (p * 1.3)
        half = w * (1 - p) ** .8 * (.8 + .2 * math.sin(f * 1.57 + i))
        for x in range(int(cx - w - 2), int(cx + w + 3)):
            d = abs(x + .5 - (cx + wob))
            if d <= half:
                r = d / max(half, .01)
                q = r * .6 + p * .7
                col = cols[0] if q < .45 else cols[1] if q < .75 else cols[2] if q < 1.05 else cols[3]
                c.px(x, by - i, col)
    # flicker spark
    sx = cx + [-1, 1, 0, 2][f]
    sy = by - h - [1, 3, 2, 4][f]
    c.px(sx, sy, cols[1])


def torch_frames():
    out = []
    for f in range(4):
        c = Canvas(16, 32)
        c.ellipse(8, 30, 3, 1.2, SHADOW)
        pole = [
            "KlhK",
            "KlRK",
            "KlRK",
            "KlBK",
            "KRBK",
            "KRBK",
            "KRBK",
            "KRBK",
            "KRBK",
            "KRBK",
            "KRBK",
            "KRDK",
            "KBDK",
            "KBDK",
            "KBDK",
            "KKKK",
        ]
        bowl = ["KKKKKKKK", "KttttttK", ".KmmmmK.", "..KKKK.."]
        c.paste(spr(16, 32, pole, ox=6, oy=14), 0, 0)
        c.paste(spr(16, 32, bowl, ox=4, oy=11), 0, 0)
        flame(c, 8, 11, 9, 2.8, f)
        out.append(c)
    return out


def campfire_frames():
    out = []
    for f in range(4):
        c = Canvas(16, 16)
        c.ellipse(8, 13, 7, 2, SHADOW)
        stones = [".SoS.SpS.SoS.", "SpmSSomSSpmS."]
        logs = [
            "..KKK...KKK..",
            ".KlRBK.KBRlK.",
            "..KKBKKBKK...",
            "....KBBK.....",
            "..KKBKKBKK...",
            ".KlRBK.KBRlK.",
            "..KKK...KKK..",
        ]
        c.paste(spr(16, 16, logs, ox=2, oy=6), 0, 0)
        c.paste(spr(16, 16, stones, ox=2, oy=13), 0, 0)
        flame(c, 7.5, 11, 8, 3.2, f, seed=1)
        out.append(c)
    return out


def lantern_post():
    c = Canvas(16, 32)
    c.ellipse(8, 30, 4, 1.3, SHADOW)
    rows = [
        "...KKKKK.....",
        "..KtppptK....",
        "..KKKKKKK....",
        "..KyyAyyK....",
        "..KYyyyYK....",
        "..KYYyYYK....",
        "..KKKKKKK....",
        "....KK.......",
        "....KlKKKKK..",
        "....KlhllllK.",
        "....KlKKKKK..",
        "....KRK......",
        "....KRK......",
        "....KRK......",
        "....KRK......",
        "....KRK......",
        "....KRK......",
        "....KBK......",
        "....KBK......",
        "....KBK......",
        "....KBK......",
        "...KKBKK.....",
        "..KRRBBDK....",
        "..KKKKKKK....",
    ]
    t = spr(16, 32, rows, ox=3, oy=6, flip=False)
    # warm glow halo (semi-transparent)
    for y in range(4, 16):
        for x in range(1, 15):
            d = ((x + .5 - 7.5) ** 2 + (y + .5 - 10.5) ** 2) ** .5
            if d < 6.5:
                c.blend(x, y, (255, 252, 64, int(60 * (1 - d / 6.5))))
    c.paste(t, 0, 0)
    return c


def signpost():
    rows = [
        "KKKKKKKKKKKKK.",
        "KhllllllllllLK",
        "KlRKKRRKRKRRBK",
        "KlRRRRRRRRRRBK",
        "KlRKRKKRKRRRBK",
        "KDDDDDDDDDDDDK",
        "KKKKKKKKKKKKKK",
        ".....KRBK.....",
        ".....KRBK.....",
        ".....KRBK.....",
        "....KKRBKK....",
        "....KKKKKK....",
    ]
    return spr(16, 16, rows, shadow=(8, 14, 4, 1.4))


def fence_set():
    """horizontal: left-end, middle, right-end, single post; vertical: top, middle, bottom; gate closed/open"""
    def post(c, x, top=3):
        c.rect(x, top, x + 3, 13, 'd_rd'); c.rect(x + 1, top, x + 1, 12, 'd_md'); c.rect(x + 3, top + 1, x + 3, 13, 'd_br')
        c.hline(x, x + 3, top, 'd_hi'); c.hline(x + 1, x + 2, top, 'd_hi')

    def rails(c, x0, x1):
        for y in (5, 9):
            c.hline(x0, x1, y, 'd_md'); c.hline(x0, x1, y + 1, 'd_br')

    def fin(c, sh=True):
        t = Canvas(16, 16); t.paste(c, 0, 0); t.outline('d_ol')
        o = Canvas(16, 16)
        if sh:
            for x in range(16):
                if t.a[13, x, 3] or t.a[12, x, 3]:
                    o.px(x, 14, SHADOW); o.px(x, 15, (0, 0, 0, 30))
        o.paste(t, 0, 0)
        return o

    out = []
    c = Canvas(16, 16); rails(c, 6, 15); post(c, 2); out.append(fin(c))           # left end
    c = Canvas(16, 16); rails(c, 0, 15); post(c, 6); out.append(fin(c))           # middle
    c = Canvas(16, 16); rails(c, 0, 9); post(c, 10); out.append(fin(c))           # right end
    c = Canvas(16, 16); post(c, 6); out.append(fin(c))                            # single post
    # vertical (seen from the side: rails become a post column with a thin rail line)
    for kind in ('top', 'mid', 'bot'):
        c = Canvas(16, 16)
        y0 = 4 if kind == 'top' else 0
        y1 = 11 if kind == 'bot' else 15
        c.rect(7, y0, 8, y1, 'd_br'); c.vline(7, y0, y1, 'd_md')
        if kind != 'mid':
            post(c, 6, 3 if kind == 'top' else 3)
        else:
            c.rect(6, 6, 9, 9, 'd_rd'); c.hline(6, 9, 6, 'd_hi')
        out.append(fin(c, sh=kind != 'mid'))
    # gate closed / open
    c = Canvas(16, 16); post(c, 0); post(c, 12)
    for y in (5, 9):
        c.hline(4, 11, y, 'd_md'); c.hline(4, 11, y + 1, 'd_br')
    for x in (5, 8): c.vline(x, 4, 12, 'd_rd')
    c.px(10, 7, 'o'); c.px(10, 8, 's_dk')
    out.append(fin(c))
    c = Canvas(16, 16); post(c, 0); post(c, 12)
    c.rect(4, 4, 5, 12, 'd_md'); c.vline(5, 4, 12, 'd_br')
    out.append(fin(c))
    return out


def bridge_set():
    """horizontal bridge: west end, middle, east end ; vertical: north end, middle, south end (16x16)."""
    out = []
    for kind in ('w', 'm', 'e'):
        c = Canvas(16, 16)
        for x in range(16):
            col = 'd_md' if x % 4 == 0 else 'd_rd' if x % 4 in (1, 2) else 'd_br'
            c.vline(x, 3, 13, col)
            if x % 4 == 3: c.vline(x, 3, 13, 'd_dk')
            c.px(x, 13, 'd_dk')
        c.hline(0, 15, 2, 'd_br'); c.hline(0, 15, 1, 'd_md'); c.hline(0, 15, 14, 'd_dk2')
        if kind in ('w', 'e'):
            px = 0 if kind == 'w' else 12
            for y0 in (0, 10):
                c.rect(px, y0, px + 3, y0 + 4, 'd_rd'); c.hline(px, px + 3, y0, 'd_hi'); c.vline(px + 3, y0 + 1, y0 + 4, 'd_br')
        t = Canvas(16, 16); t.paste(c, 0, 0)
        # dark outline only on the open sides (keeps tiles seamless along the span)
        for x in range(16):
            for y in (0, 15):
                if not t.a[y, x, 3] and (t.a[min(15, y + 1), x, 3] or t.a[max(0, y - 1), x, 3]):
                    t.px(x, y, 'd_ol')
        for x in range(16):
            t.px(x, 15, (0, 0, 0, 70))
        out.append(t)
    for kind in ('n', 'm', 's'):
        c = Canvas(16, 16)
        for y in range(16):
            col = 'd_md' if y % 4 == 0 else 'd_rd' if y % 4 in (1, 2) else 'd_br'
            c.hline(3, 12, y, col)
            if y % 4 == 3: c.hline(3, 12, y, 'd_dk')
        c.vline(2, 0, 15, 'd_br'); c.vline(1, 0, 15, 'd_ol'); c.vline(13, 0, 15, 'd_dk'); c.vline(14, 0, 15, 'd_ol')
        if kind in ('n', 's'):
            y0 = 0 if kind == 'n' else 11
            for px in (0, 12):
                c.rect(px, y0, px + 3, y0 + 4, 'd_rd'); c.hline(px, px + 3, y0, 'd_hi'); c.vline(px + 3, y0 + 1, y0 + 4, 'd_br')
                c.hline(px, px + 3, y0 + 4, 'd_ol')
        out.append(c)
    return out


# ------------------------------------------------------------- ruins -------
def pillar_broken():
    rows = [
        "....SSS......",
        "...SqpS.SS...",
        "..SqppoSpoS..",
        "..SpootoooS..",
        "..SpoomtomS..",
        "..SpoomoomS..",
        "..SpootoomS..",
        "..SpvomoomS..",
        "..SpvvooomS..",
        "..SpooootmS..",
        "..SpoomoomS..",
        "..SpootoomS..",
        "..SpoomoomS..",
        "..SvvomovmS..",
        "..SpvvoovmS..",
        ".SSSSSSSSSSS.",
        ".SqppppppppmS",
        ".SoooooooootS",
        ".SSSSSSSSSSSS",
    ]
    c = spr(16, 32, rows, ox=1, shadow=(8, 30, 7, 2))
    c.px(2, 30, 's_md'); c.px(13, 29, 's_lt'); c.px(14, 30, 's_dk')  # rubble
    return c


def ruin_wall():
    c = Canvas(32, 32)
    c.ellipse(16, 29, 15, 2.5, SHADOW)
    t = Canvas(32, 32)
    heights = [14, 15, 15, 17, 18, 18, 18, 20, 20, 20, 20, 21, 21, 20, 18, 17, 16, 14, 13, 13, 12, 12, 10, 10, 10, 11, 11, 9, 8, 8]
    for i, hgt in enumerate(heights):
        x = i + 1
        for y in range(28 - hgt, 28):
            ry = 27 - y
            row = ry // 4
            off = 0 if row % 2 else 3
            mort = ry % 4 == 3 or (x + off) % 7 == 0
            col = 's_dk' if mort else ('s_lt' if (x + off) % 7 == 1 or ry % 4 == 2 else 's')
            if y == 28 - hgt:
                col = 's_hi'
            t.px(x, y, col)
    # moss + crack
    for (x, y) in [(5, 15), (6, 15), (6, 16), (12, 8), (13, 8), (13, 9), (20, 12), (24, 18), (25, 18)]:
        t.px(x, y, 'g_md')
    for (x, y) in [(10, 20), (11, 21), (11, 22), (12, 23)]:
        t.px(x, y, 's_ol')
    t.outline('s_ol')
    c.paste(t, 0, 0)
    for (x, y, col) in [(3, 29, 's'), (4, 29, 's_dk'), (28, 30, 's_lt'), (29, 30, 's_md')]:
        c.px(x, y, col)
    return c


def gravestone():
    rows = [
        "...SSSSSS...",
        "..SqpppppS..",
        ".SqpoooootS.",
        ".SpoSoSootS.",
        ".SpoooSootS.",
        ".SpoSoSootS.",
        ".SpoooooomS.",
        ".SpvoooovmS.",
        ".SvvooomvvS.",
        "SSSSSSSSSSSS",
        "SgvwvvgvwvgS",
        ".SSSSSSSSSS.",
    ]
    return spr(16, 16, rows, shadow=(8, 14, 7, 2))


def demon_obelisk_frames():
    """dark obelisk with pulsing rune (ties to Demon_A / Blood Monster_A palette)"""
    base = [
        ".....SS......",
        "....SqtS.....",
        "....SptS.....",
        "...SqoomS....",
        "...SpoomS....",
        "...Spo1mS....",
        "...Spo1mS....",
        "...So111S....",
        "...Spo1mS....",
        "...SpoomS....",
        "..SqoooomS...",
        "..SpoooomS...",
        "..SpoooomS...",
        ".SSSSSSSSSS..",
        "SqpppppppmtS.",
        "StttttttttsS.",
        "SSSSSSSSSSSS.",
    ]
    out = []
    glow = [('c_red2', 0), ('c_red', 40), ('c_bld', 80), ('c_red', 40)]
    for f in range(4):
        c = Canvas(16, 32)
        c.ellipse(8, 30, 7, 2, SHADOW)
        col, ga = glow[f]
        if ga:
            for y in range(6, 22):
                for x in range(2, 14):
                    d = ((x + .5 - 8) ** 2 * 1.6 + (y + .5 - 14) ** 2) ** .5
                    if d < 7:
                        c.blend(x, y, (237, 13, 13, int(ga * (1 - d / 7))))
        k = dict(K); k['1'] = col
        t = Canvas(16, 32); t.sprite(base, k, 2, 31 - len(base) - 1)
        c.paste(t, 0, 0)
        out.append(c)
    return out


def rock_cluster():
    rows = [
        "....SSSS.......",
        "...SqppoS......",
        "..SqpoootSSS...",
        "..SpoooomSpoS..",
        ".SSpootmmSoomS.",
        "SqpSmmmmSmotmS.",
        "SpoomSSSSmmmS..",
        ".SmmtS..SSSS...",
        "..SSS..........",
    ]
    return spr(16, 16, rows, shadow=(8, 14, 7, 2))


# ------------------------------------------------------------ waterfall ----
def waterfall():
    """body (32x16, loops vertically, 4 frames), top lip (32x16 x4), foam base (48x16 x4)"""
    stripe = [3, 7, 12, 17, 21, 26, 29]
    body, top, foam = [], [], []
    for f in range(4):
        c = Canvas(32, 16)
        for y in range(16):
            for x in range(32):
                if x in (0, 31):
                    col = 'w_dp'
                elif x in (1, 30):
                    col = 'w_dk'
                else:
                    col = 'w'
                    if x in stripe:
                        k = stripe.index(x)
                        ph = (y - f * 4 + k * 7) % 16
                        ln = 5 + (k * 3) % 5
                        if ph < ln:
                            col = 'w_fo' if ph < 2 else 'w_lt'
                    elif x in (5, 10, 15, 19, 24):
                        ph = (y - f * 4 + x * 5) % 16
                        if ph < 6:
                            col = 'w_md'
                c.px(x, y, col)
        body.append(c)
        t = Canvas(32, 16)
        for y in range(16):
            for x in range(32):
                if y < 8:
                    continue  # upper half left free for the cliff/river tile above
                if y == 8:
                    col = 'w_fo' if (x + f) % 3 else 'w_lt'
                elif y == 9:
                    col = 'w_lt'
                else:
                    col = 'w'
                    ph = (y - f * 4) % 16
                    if x in stripe and ph < 6 and y > 10:
                        col = 'w_lt'
                if x in (0, 31): col = 'w_dp'
                elif x in (1, 30) and y > 8: col = 'w_dk'
                t.px(x, y, col)
        top.append(t)
        fo = Canvas(48, 16)
        for (cx, cy, r) in [(10, 8, 4), (18, 6, 5), (26, 7, 5), (34, 6, 5), (40, 9, 3.5), (24, 10, 6)]:
            rr = r + [0, .6, 1, .4][(f + int(cx)) % 4]
            fo.ellipse(cx + 1, cy, rr, rr * .7, 'w_lt')
            fo.ellipse(cx, cy - .6, rr - 1.2, (rr - 1.2) * .7, 'w_fo')
        for k in range(5):
            x = 8 + (k * 9 + f * 3) % 32
            y = 2 + (k * 5 + f) % 4
            fo.px(x, y, 'wht')
        fo.outline('w_md')
        foam.append(fo)
    return body, top, foam


# ---------------------------------------------------------------- build ---
def build():
    out = []
    S = save
    out.append(S(sheet([bush_berry(), bush_round_small(), sapling()], 16, 16), 'Environments/Vegetation/veg_bushes_small_16x16.png'))
    out.append(S(bush_large(), 'Environments/Vegetation/veg_bush_large_32x24.png'))
    out.append(S(dead_tree(), 'Environments/Vegetation/veg_tree_dead_32x40.png'))
    out.append(S(fallen_log(), 'Environments/Vegetation/veg_log_fallen_32x16.png'))
    out.append(S(sheet(tall_grass_sway(), 16, 16, 4), 'Environments/Vegetation/veg_tallgrass_sway_anim_16x16.png'))
    out.append(S(sheet(flowers(), 16, 16), 'Environments/Vegetation/veg_flowers_16x16.png'))
    out.append(S(sheet([barrel(), crate()] + pots() + [signpost(), rock_cluster(), gravestone()], 16, 16), 'Props/props_static_16x16.png'))
    out.append(S(sheet(chest_frames(), 16, 16), 'Props/prop_chest_open_anim_16x16.png'))
    out.append(S(sheet(torch_frames(), 16, 32), 'Props/prop_torch_anim_16x32.png'))
    out.append(S(sheet(campfire_frames(), 16, 16), 'Props/prop_campfire_anim_16x16.png'))
    out.append(S(lantern_post(), 'Props/prop_lantern_post_16x32.png'))
    out.append(S(sheet(fence_set(), 16, 16), 'Environments/Decorations/deco_fence_16x16.png'))
    out.append(S(sheet(bridge_set(), 16, 16), 'Environments/Decorations/deco_bridge_16x16.png'))
    out.append(S(pillar_broken(), 'Environments/Decorations/deco_ruin_pillar_16x32.png'))
    out.append(S(ruin_wall(), 'Environments/Decorations/deco_ruin_wall_32x32.png'))
    out.append(S(sheet(demon_obelisk_frames(), 16, 32), 'Environments/Decorations/deco_demon_obelisk_anim_16x32.png'))
    body, top, foam = waterfall()
    out.append(S(sheet(body, 32, 16), 'Environments/Water/water_waterfall_body_anim_32x16.png'))
    out.append(S(sheet(top, 32, 16), 'Environments/Water/water_waterfall_top_anim_32x16.png'))
    out.append(S(sheet(foam, 48, 16), 'Environments/Water/water_waterfall_foam_anim_48x16.png'))
    return out


if __name__ == '__main__':
    for p in build():
        print(p)
