"""'Woods Serif HD' - stroke-drawn RPG font rendered at 2x density (each canvas pixel = 2x2 atlas texels).

Glyphs are defined as strokes (lines, arcs, curves) in canvas-pixel units:
  cap top y=0, x-height y=2, baseline y=5, descender y=6.3     (text cell = 10 canvas px, caps start at row 3)
and rasterised with a round pen of radius 0.55 px at 2x, so curves and diagonals come out smooth.
Capitals get small serifs (old-book feel); lower case stays clean for readability.

  python font_hd.py <out dir> [preview.png]   -> pixelfont.png + pixelfont.json (scale 2) for GameBuilder.BuildFont
"""
import json, math, os
import numpy as np
from PIL import Image

S = 2                     # atlas texels per canvas pixel
CELL_H = 10               # canvas px per text line cell
TOP = 3.5                 # canvas y of glyph y=0 (centre of row 3)
PEN = 0.5


def L(*pts): return [list(pts)]


def arc(cx, cy, rx, ry, a0, a1, n=None):
    n = n or max(8, int(abs(a1 - a0) / 8))
    return [[(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]]


def dot(x, y): return [[(x, y), (x, y + 0.01)]]


def serif(x, y, w=0.6): return L((x - w, y), (x + w, y))


def cat(*parts):
    out = []
    for p in parts: out += p
    return out


G = {}
# ---------------------------------------------------------------- capitals (with light serifs)
G['A'] = cat(L((0, 5), (1.75, 0), (3.5, 5)), L((0.7, 3.2), (2.8, 3.2)), serif(0, 5, .5), serif(3.5, 5, .5))
G['B'] = cat(L((0, 0), (0, 5)), L((0, 0), (2, 0)), arc(2, 1.2, 1.1, 1.2, -90, 90), L((2, 2.4), (0, 2.4)), L((0, 2.4), (2.1, 2.4)), arc(2.1, 3.7, 1.3, 1.3, -90, 90), L((2.1, 5), (0, 5)))
G['C'] = cat(arc(2, 2.5, 2, 2.5, 40, 320))
G['D'] = cat(L((0, 0), (0, 5)), L((0, 0), (1.3, 0)), arc(1.3, 2.5, 2.2, 2.5, -90, 90), L((1.3, 5), (0, 5)))
G['E'] = cat(L((3, 0), (0, 0), (0, 5), (3, 5)), L((0, 2.4), (2.2, 2.4)), L((3, 0), (3, 0.6)), L((3, 5), (3, 4.4)))
G['F'] = cat(L((3, 0), (0, 0), (0, 5)), L((0, 2.4), (2.2, 2.4)), L((3, 0), (3, 0.6)), serif(0, 5, .5))
G['G'] = cat(arc(2, 2.5, 2, 2.5, 30, 320), L((2.4, 3), (4, 3), (4, 4.3)))
G['H'] = cat(L((0, 0), (0, 5)), L((3.2, 0), (3.2, 5)), L((0, 2.5), (3.2, 2.5)), serif(0, 0, .5), serif(0, 5, .5), serif(3.2, 0, .5), serif(3.2, 5, .5))
G['I'] = cat(L((0.8, 0), (0.8, 5)), L((0, 0), (1.6, 0)), L((0, 5), (1.6, 5)))
G['J'] = cat(L((3, 0), (3, 3.5)), arc(1.5, 3.5, 1.5, 1.5, 0, 160), L((2.3, 0), (3.6, 0)))
G['K'] = cat(L((0, 0), (0, 5)), L((3, 0), (0.2, 3)), L((1.2, 2), (3.2, 5)), serif(0, 0, .5), serif(0, 5, .5))
G['L'] = cat(L((0, 0), (0, 5), (3, 5)), L((3, 5), (3, 4.4)), serif(0, 0, .5))
G['M'] = cat(L((0, 5), (0, 0), (2, 3.4), (4, 0), (4, 5)), serif(0, 5, .5), serif(4, 5, .5))
G['N'] = cat(L((0, 5), (0, 0), (3.2, 5), (3.2, 0)), serif(0, 5, .5), serif(3.2, 0, .5))
G['O'] = cat(arc(1.9, 2.5, 1.9, 2.5, 0, 360, 40))
G['P'] = cat(L((0, 5), (0, 0), (2, 0)), arc(2, 1.35, 1.2, 1.35, -90, 90), L((2, 2.7), (0, 2.7)), serif(0, 5, .5))
G['Q'] = cat(G['O'], L((2.2, 3.9), (3.8, 5.6)))
G['R'] = cat(G['P'][:-1], L((1.6, 2.7), (3.2, 5)), serif(0, 5, .5))
G['S'] = cat(arc(1.6, 1.25, 1.5, 1.25, -15, -270), arc(1.6, 3.75, 1.5, 1.25, -90, 165))
G['T'] = cat(L((0, 0), (4, 0)), L((2, 0), (2, 5)), L((1.3, 5), (2.7, 5)), L((0, 0), (0, 0.6)), L((4, 0), (4, 0.6)))
G['U'] = cat(L((0, 0), (0, 3.4)), arc(1.6, 3.4, 1.6, 1.6, 180, 0), L((3.2, 3.4), (3.2, 0)), serif(0, 0, .5), serif(3.2, 0, .5))
G['V'] = cat(L((0, 0), (1.9, 5), (3.8, 0)), serif(0, 0, .5), serif(3.8, 0, .5))
G['W'] = cat(L((0, 0), (1.1, 5), (2.3, 1.6), (3.5, 5), (4.6, 0)))
G['X'] = cat(L((0, 0), (3.4, 5)), L((3.4, 0), (0, 5)))
G['Y'] = cat(L((0, 0), (1.7, 2.6), (3.4, 0)), L((1.7, 2.6), (1.7, 5)), L((1, 5), (2.4, 5)))
G['Z'] = cat(L((0, 0.6), (0, 0), (3.2, 0), (0, 5), (3.2, 5), (3.2, 4.4)))
# ---------------------------------------------------------------- lower case
G['a'] = cat(arc(1.45, 3.55, 1.45, 1.45, 0, 360, 28), L((2.9, 2), (2.9, 5)))
G['b'] = cat(L((0, 0), (0, 5)), arc(1.5, 3.55, 1.5, 1.45, 0, 360, 28))
G['c'] = cat(arc(1.5, 3.5, 1.5, 1.5, 45, 315))
G['d'] = cat(L((3, 0), (3, 5)), arc(1.5, 3.55, 1.5, 1.45, 0, 360, 28))
G['e'] = cat(L((0.05, 3.4), (3, 3.4)), arc(1.5, 3.5, 1.5, 1.5, 0, -310))
G['f'] = cat(L((1, 5), (1, 1)), arc(2, 1, 1, 1, 180, 300), L((0, 2.2), (2.2, 2.2)))
G['g'] = cat(arc(1.45, 3.4, 1.45, 1.35, 0, 360, 28), L((2.9, 2), (2.9, 5.6)), arc(1.45, 5.6, 1.45, 0.7, 0, 170))
G['h'] = cat(L((0, 0), (0, 5)), arc(1.45, 3.3, 1.45, 1.3, 180, 360), L((2.9, 3.3), (2.9, 5)))
G['i'] = cat(L((0.5, 2), (0.5, 5)), dot(0.5, 0.5))
G['j'] = cat(L((1.3, 2), (1.3, 5.6)), arc(0.3, 5.6, 1, 0.7, 0, 130), dot(1.3, 0.5))
G['k'] = cat(L((0, 0), (0, 5)), L((2.7, 2), (0.1, 4)), L((1.1, 3.2), (2.9, 5)))
G['l'] = cat(L((0.5, 0), (0.5, 4.3)), arc(1.3, 4.3, 0.8, 0.7, 180, 90))
G['m'] = cat(L((0, 2), (0, 5)), arc(1.05, 3.1, 1.05, 1.1, 180, 360), L((2.1, 3.1), (2.1, 5)), arc(3.15, 3.1, 1.05, 1.1, 180, 360), L((4.2, 3.1), (4.2, 5)))
G['n'] = cat(L((0, 2), (0, 5)), arc(1.45, 3.3, 1.45, 1.3, 180, 360), L((2.9, 3.3), (2.9, 5)))
G['o'] = cat(arc(1.5, 3.5, 1.5, 1.5, 0, 360, 28))
G['p'] = cat(L((0, 2), (0, 6.3)), arc(1.5, 3.5, 1.5, 1.5, 0, 360, 28))
G['q'] = cat(L((3, 2), (3, 6.3)), arc(1.5, 3.5, 1.5, 1.5, 0, 360, 28))
G['r'] = cat(L((0, 2), (0, 5)), arc(1.7, 3.4, 1.7, 1.4, 180, 300))
G['s'] = cat(arc(1.3, 2.75, 1.2, 0.75, -10, -270), arc(1.3, 4.25, 1.25, 0.75, -90, 170))
G['t'] = cat(L((1, 0.6), (1, 4.3)), arc(1.9, 4.3, 0.9, 0.7, 180, 90), L((0, 2), (2.3, 2)))
G['u'] = cat(L((0, 2), (0, 3.7)), arc(1.45, 3.7, 1.45, 1.3, 180, 0), L((2.9, 2), (2.9, 5)))
G['v'] = cat(L((0, 2), (1.5, 5), (3, 2)))
G['w'] = cat(L((0, 2), (1, 5), (2.1, 2.8), (3.2, 5), (4.2, 2)))
G['x'] = cat(L((0, 2), (3, 5)), L((3, 2), (0, 5)))
G['y'] = cat(L((0, 2), (1.6, 4.9)), L((3, 2), (0.9, 6.3)))
G['z'] = cat(L((0, 2), (3, 2), (0, 5), (3, 5)))
# ---------------------------------------------------------------- digits
G['0'] = cat(arc(1.6, 2.5, 1.6, 2.5, 0, 360, 36))
G['1'] = cat(L((0.3, 1), (1.4, 0), (1.4, 5)), L((0.4, 5), (2.4, 5)))
G['2'] = cat(arc(1.6, 1.4, 1.5, 1.4, 190, 360), L((3.1, 1.4), (3.0, 2), (0, 5), (3.2, 5)))
G['3'] = cat(arc(1.5, 1.25, 1.4, 1.25, 200, 450), arc(1.5, 3.75, 1.55, 1.25, -90, 160))
G['4'] = cat(L((2.5, 5), (2.5, 0), (0, 3.5), (3.3, 3.5)))
G['5'] = cat(L((3, 0), (0.3, 0), (0.1, 2.3)), arc(1.5, 3.4, 1.55, 1.6, -150, 150))
G['6'] = cat(arc(1.6, 3.4, 1.55, 1.6, 0, 360, 28), arc(2.6, 2.8, 2.5, 2.8, 185, 262))
G['7'] = cat(L((0, 0), (3.2, 0), (1.1, 5)))
G['8'] = cat(arc(1.6, 1.2, 1.25, 1.2, 0, 360, 24), arc(1.6, 3.75, 1.55, 1.25, 0, 360, 28))
G['9'] = cat(arc(1.55, 1.6, 1.55, 1.6, 0, 360, 28), arc(0.5, 2.2, 2.6, 2.8, -5, 82))
# ---------------------------------------------------------------- punctuation
G['.'] = dot(0.5, 5)
G[','] = L((0.6, 5), (0.1, 6.1))
G[':'] = cat(dot(0.5, 2.3), dot(0.5, 5))
G[';'] = cat(dot(0.6, 2.3), L((0.6, 5), (0.1, 6.1)))
G['!'] = cat(L((0.5, 0), (0.5, 3.4)), dot(0.5, 5))
G['¡'] = cat(dot(0.5, 2.0), L((0.5, 3.3), (0.5, 6.3)))
G['?'] = cat(arc(1.5, 1.3, 1.45, 1.3, 190, 400), L((2.3, 2.5), (1.5, 3.4)), dot(1.5, 5))
G['¿'] = cat(dot(1.5, 2.0), L((1.5, 3.1), (1.0, 3.9)), arc(1.6, 5.0, 1.45, 1.2, 210, 10))
G['-'] = L((0, 2.8), (2, 2.8))
G['+'] = cat(L((0, 2.8), (2.4, 2.8)), L((1.2, 1.6), (1.2, 4)))
G['='] = cat(L((0, 2.1), (2.4, 2.1)), L((0, 3.6), (2.4, 3.6)))
G['/'] = L((0, 5.2), (2.6, -0.2))
G['%'] = cat(L((0, 5), (3, 0)), arc(0.6, 0.8, 0.6, 0.8, 0, 360, 12), arc(2.5, 4.2, 0.6, 0.8, 0, 360, 12))
G['('] = arc(2.2, 2.5, 2, 3.1, 130, 230)
G[')'] = arc(0, 2.5, 2, 3.1, -50, 50)
G['['] = L((1.2, -0.3), (0, -0.3), (0, 5.4), (1.2, 5.4))
G[']'] = L((0, -0.3), (1.2, -0.3), (1.2, 5.4), (0, 5.4))
G['<'] = L((2.2, 1.3), (0, 2.9), (2.2, 4.5))
G['>'] = L((0, 1.3), (2.2, 2.9), (0, 4.5))
G["'"] = L((0.4, 0), (0.3, 1.2))
G['"'] = cat(L((0.3, 0), (0.3, 1.2)), L((1.5, 0), (1.5, 1.2)))
G['·'] = dot(0.4, 2.7)
G['*'] = cat(L((0, 1), (2, 2.6)), L((2, 1), (0, 2.6)), L((1, 0.6), (1, 3)))
G['_'] = L((0, 6), (3, 6))
G['#'] = cat(L((1, 0.5), (0.6, 4.8)), L((2.6, 0.5), (2.2, 4.8)), L((0, 1.8), (3.2, 1.8)), L((0, 3.4), (3.2, 3.4)))
G['&'] = cat(arc(1.2, 1.1, 0.9, 1, 0, 360, 16), L((1.6, 2.0), (3.4, 5)), arc(1.4, 3.6, 1.4, 1.4, -60, 200), L((3.3, 3), (2.6, 4.4)))

ACUTE = {'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U', 'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u'}
TILDE = {'Ñ': 'N', 'ñ': 'n'}
DIA = {'Ü': 'U', 'ü': 'u'}


def accented():
    for ch, b in ACUTE.items():
        base = [s for s in G[b]]
        if b == 'i': base = [L((0.5, 2), (0.5, 5))[0]]
        xs = [p[0] for s in base for p in s]
        cx = (min(xs) + max(xs)) / 2
        y = -1.9 if ch.isupper() else 0.4
        G[ch] = base + L((cx - 0.3, y + 1.0), (cx + 0.6, y))
    for ch, b in TILDE.items():
        xs = [p[0] for s in G[b] for p in s]; x0, x1 = min(xs), max(xs)
        y = -1.6 if ch.isupper() else 0.6
        G[ch] = G[b] + L((x0, y + 0.6), (x0 + (x1 - x0) * 0.33, y), (x0 + (x1 - x0) * 0.66, y + 0.6), (x1, y))
    for ch, b in DIA.items():
        xs = [p[0] for s in G[b] for p in s]; x0, x1 = min(xs), max(xs)
        y = -1.4 if ch.isupper() else 0.6
        G[ch] = G[b] + dot(x0 + 0.3, y) + dot(x1 - 0.3, y)


accented()


def seg_dist(px, py, a, b):
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def render(ch):
    strokes = G[ch]
    xs = [p[0] for s in strokes for p in s]
    x0 = min(xs); w_units = max(xs) - x0
    width = int(math.ceil(w_units + 2 * PEN))                         # canvas px
    W, H = width * S, CELL_H * S
    a = np.zeros((H, W), bool)
    for ty in range(H):
        for tx in range(W):
            px = (tx + 0.5) / S - PEN + x0
            py = (ty + 0.5) / S - TOP
            for s in strokes:
                hit = False
                for i in range(len(s) - 1):
                    if seg_dist(px, py, s[i], s[i + 1]) <= PEN: hit = True; break
                if hit: a[ty, tx] = True; break
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px_ = im.load()
    for ty in range(H):
        for tx in range(W):
            if a[ty, tx]: px_[tx, ty] = (255, 255, 255, 255)
    return im, width


def build(out_png, out_json):
    chars = list(G.keys())
    imgs = [render(c) for c in chars]
    cw = max(w for _, w in imgs) * S
    cols = 16; rows = (len(chars) + cols - 1) // cols
    atlas = Image.new('RGBA', (cols * cw, (rows + 1) * CELL_H * S), (0, 0, 0, 0))
    meta = []
    for i, (ch, (im, w)) in enumerate(zip(chars, imgs)):
        x, y = (i % cols) * cw, (i // cols) * CELL_H * S
        atlas.alpha_composite(im, (x, y))
        meta.append(dict(c=ord(ch), x=x, y=y, w=w, adv=w + (1 if ch not in ".,:;!¡'·" else 1)))
    meta.append(dict(c=ord(' '), x=0, y=rows * CELL_H * S, w=0, adv=3))
    atlas.save(out_png)
    json.dump(dict(cellW=cw, cellH=CELL_H, ascent=3, size=CELL_H, scale=S, glyphs=meta), open(out_json, 'w'))
    return atlas.size, len(chars)


def preview(lines, out):
    imgs = {c: render(c) for c in G}
    W = max(sum((imgs[c][1] + 1) if c in imgs else 3 for c in t) for t in lines) + 8
    sheet = Image.new('RGBA', (W * S, (len(lines) * 12 + 4) * S), (24, 20, 34, 255))
    for li, t in enumerate(lines):
        x = 4
        for c in t:
            if c in imgs: sheet.alpha_composite(imgs[c][0], (x * S, (2 + li * 12) * S)); x += imgs[c][1] + 1
            else: x += 3
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(out)


if __name__ == '__main__':
    import sys
    root = sys.argv[1]
    print(build(os.path.join(root, 'pixelfont.png'), os.path.join(root, 'pixelfont.json')))
    if len(sys.argv) > 2:
        preview(["Herrería   Monedas: 120", "Espada del caballero  90", "Espadón 120  Katana 130  Estoque 110",
                 "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz ñ áéíóú",
                 "0123456789 .,:;!¡?¿-+=/%()[]<>'\"·*#&", "¡Nueva región descubierta! ¿Seguro?  Ñandú"], sys.argv[2])
