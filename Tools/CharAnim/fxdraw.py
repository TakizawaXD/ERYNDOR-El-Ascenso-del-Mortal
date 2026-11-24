"""In-sprite effects drawn with the characters' own effect colours (slash white #f4edea etc.)."""
import math
import numpy as np
from engine import *

SLASH = hx('#f4edea')     # main slash colour used by every original attack
SLASH2 = hx('#d9d8d8')    # slash edge
SLASH3 = hx('#c0bfbf')    # fading slash
RED = hx('#ed0d0d')       # hurt glow (Soldier_Hurt)
YEL = hx('#fffc40')
ORA = hx('#f9a31b')
WHT = hx('#ffffff')
DUST = hx('#c0bfbf')
DUST2 = hx('#d9d8d8')
PUR = hx('#793a80')
BLD = hx('#a22b4b')
BLD2 = hx('#ed0d0d')


def px(f, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < CELL and 0 <= y < CELL:
        f[y, x] = c


def arc(f, cx, cy, r_out, r_in, a0, a1, ry=1.0, fade=False, behind=None):
    """filled crescent between radii (degrees, 0 = right, 90 = down). Thick in the middle like the originals."""
    out = f.copy()
    for y in range(CELL):
        for x in range(CELL):
            dx, dy = x + .5 - cx, (y + .5 - cy) / ry
            r = math.hypot(dx, dy)
            a = math.degrees(math.atan2(dy, dx)) % 360
            lo, hi = a0 % 360, a1 % 360
            inside = (lo <= a <= hi) if lo <= hi else (a >= lo or a <= hi)
            if not inside:
                continue
            span = (hi - lo) % 360 or 360
            t = ((a - lo) % 360) / span
            thick = (r_out - r_in) * math.sin(math.pi * t)  # crescent profile
            if r_out - thick <= r <= r_out:
                edge = r > r_out - 1 or r < r_out - thick + 1
                col = SLASH3 if fade else (SLASH2 if edge else SLASH)
                if out[y, x, 3] == 0 or behind is None:
                    out[y, x] = col
    return out


def dust(f, x, y, t, side=1):
    """little ground puffs (t = 0..2)"""
    out = f.copy()
    r = [1, 2, 1][min(t, 2)]
    for k, (ox, oy) in enumerate(((0, 0), (-3 * side, 1), (3 * side, 1))):
        rr = r - (k > 0)
        if rr <= 0:
            continue
        for yy in range(-rr, rr + 1):
            for xx in range(-rr, rr + 1):
                if xx * xx + yy * yy <= rr * rr:
                    px(out, x + ox + xx, y + oy + yy, DUST if t else DUST2)
    return out


def ring(f, cx, cy, r, col, ry=.45):
    out = f.copy()
    seen = set()
    for i in range(360):
        a = math.radians(i)
        p = (int(math.floor(cx + math.cos(a) * r)), int(math.floor(cy + math.sin(a) * r * ry)))
        if p not in seen:
            seen.add(p); px(out, p[0], p[1], col)
    return out


def sparkle(f, x, y, size=2, col=WHT, col2=YEL):
    out = f.copy()
    for i in range(-size, size + 1):
        c = col if abs(i) < 1 else col2
        px(out, x + i, y, c); px(out, x, y + i, c)
    return out


def glow(f, col=YEL):
    """1-px aura around the silhouette (charging / power-up)"""
    return outline(f, col)


def orb(f, cx, cy, r, cols):
    out = f.copy()
    for k, c in enumerate(cols):
        rr = r - k * r / len(cols)
        for y in range(int(cy - rr - 1), int(cy + rr + 2)):
            for x in range(int(cx - rr - 1), int(cx + rr + 2)):
                if (x + .5 - cx) ** 2 + (y + .5 - cy) ** 2 <= rr * rr:
                    px(out, x, y, c)
    return out


def zzz(f, x, y, t):
    out = f.copy()
    Z = ["aaa", "..a", ".a.", "a..", "aaa"]
    for k in range(min(t + 1, 3)):
        ox, oy = x + k * 3, y - k * 4
        small = k < 2
        rows = ["aa", ".a", "aa"] if small else Z
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch == 'a':
                    px(out, ox + i, oy + j, WHT)
    return out


def afterimage(f, ghost, a=.35):
    return over(alpha(ghost, a), f)


def motion_lines(f, x0, x1, ys, col=SLASH2):
    out = f.copy()
    for y in ys:
        for x in range(min(x0, x1), max(x0, x1) + 1):
            if out[y, x, 3] == 0:
                out[y, x] = col
    return out
