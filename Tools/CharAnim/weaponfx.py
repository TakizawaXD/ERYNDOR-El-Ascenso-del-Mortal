"""Weapon impact / magic effects for the combat animations (white-ish, tinted at run time like the old swing sheets).

  python weaponfx.py   -> Assets/Art/Effects/Weapons/fx_<name>_anim_32x32.png  (spark, shockwave, spear_sweep, magic,
                          legend, runes, whiff)
                          Assets/Art/Effects/fx_magic_bolt_anim_16x16.png       (the staff's projectile, flies to the right)
"""
import math, os
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
WFX = os.path.join(ROOT, 'Assets', 'Art', 'Effects', 'Weapons')
FX = os.path.join(ROOT, 'Assets', 'Art', 'Effects')
W, C1, C2, C3 = (255, 255, 255, 255), (244, 237, 234, 255), (217, 216, 216, 255), (192, 191, 191, 255)
GOLD = (255, 236, 150, 255)


def canvas(n=32):
    return np.zeros((n, n, 4), np.uint8)


def px(a, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < a.shape[1] and 0 <= y < a.shape[0]:
        a[y, x] = c


def save(frames, path):
    n = frames[0].shape[0]
    s = np.zeros((n, n * len(frames), 4), np.uint8)
    for i, f in enumerate(frames):
        s[:, i * n:(i + 1) * n] = f
    Image.fromarray(s, 'RGBA').save(path)


def spark():
    out = []
    for t in range(5):
        a = canvas()
        L = [3, 7, 10, 9, 6][t]
        inner = [0, 1, 3, 5, 6][t]
        for k in range(8):
            ang = k * math.pi / 4 + (0.2 if k % 2 else 0)
            ln = L if k % 2 == 0 else L * 0.6
            for r in np.arange(inner, ln, 0.5):
                px(a, 16 + math.cos(ang) * r, 16 + math.sin(ang) * r, W if r < ln * 0.5 else GOLD if t < 3 else C2)
        if t < 2:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    px(a, 16 + dx, 16 + dy, W)
        out.append(a)
    return out


def ring(a, r, ry, col, thick=1):
    for i in range(720):
        ang = math.radians(i / 2)
        for k in range(thick):
            px(a, 16 + math.cos(ang) * (r - k), 16 + math.sin(ang) * (r - k) * ry, col)


def shockwave():
    out = []
    for t in range(6):
        a = canvas()
        r = 3 + t * 2.6
        ring(a, r, .45, C1 if t < 3 else C2 if t < 5 else C3, 2 if t < 4 else 1)
        if t < 4:
            ring(a, r * 0.6, .45, C2)
        # flying pebbles
        for k in range(6):
            ang = k * math.pi / 3 + .3
            px(a, 16 + math.cos(ang) * (r + 2), 16 + math.sin(ang) * (r + 2) * .45 - (3 - abs(t - 2)), C3)
        out.append(a)
    return out


def arc_sheet(r_out, thick, sweep, frames, cols, sparkle=False):
    out = []
    for t in range(frames):
        a = canvas()
        head = -sweep / 2 + sweep * (t + 1) / frames
        tail = max(-sweep / 2, head - sweep * 0.7)
        for y in range(32):
            for x in range(32):
                dx, dy = x + .5 - 16, y + .5 - 16
                r = math.hypot(dx, dy)
                ang = math.degrees(math.atan2(dy, dx))
                if not (tail <= ang <= head):
                    continue
                k = (ang - tail) / max(1e-3, head - tail)
                th = thick * (0.3 + 0.7 * k)
                if r_out - th <= r <= r_out:
                    a[y, x] = cols[0] if r > r_out - th * .5 else cols[1]
        if sparkle:
            for k in range(3):
                ang = math.radians(head - k * 25)
                px(a, 16 + math.cos(ang) * (r_out + 1), 16 + math.sin(ang) * (r_out + 1), W)
        if t == frames - 1:
            a[a[:, :, 3] > 0] = cols[2]
        out.append(a)
    return out


def magic():
    """swirling crescent with motes (staff swings)"""
    fr = arc_sheet(11, 3, 150, 5, ((200, 240, 255, 255), (120, 200, 255, 255), (90, 150, 230, 255)), sparkle=True)
    for t, a in enumerate(fr):
        for k in range(4):
            ang = t * 0.9 + k * math.pi / 2
            px(a, 16 + math.cos(ang) * 6, 16 + math.sin(ang) * 6, (230, 250, 255, 255))
    return fr


def runes():
    out = []
    for t in range(6):
        a = canvas()
        ring(a, 11, .5, (120, 200, 255, 255))
        for k in range(6):
            ang = k * math.pi / 3 + t * 0.35
            x, y = 16 + math.cos(ang) * 11, 16 + math.sin(ang) * 5.5
            for dx, dy in ((0, 0), (1, 0), (0, -1), (1, -1)):
                px(a, x + dx, y + dy, (220, 245, 255, 255) if (k + t) % 2 else (120, 200, 255, 255))
        out.append(a)
    return out


def whiff():
    out = []
    for t in range(4):
        a = canvas()
        for k, oy in enumerate((-3, 0, 3)):
            L = 8 - abs(oy) - t * 2
            x0 = 8 + t * 4
            for i in range(max(0, L)):
                px(a, x0 + i, 16 + oy, C2 if k != 1 else C1)
        out.append(a)
    return out


def magic_bolt():
    out = []
    for t in range(4):
        a = canvas(16)
        cx, cy = 10, 8
        # tail
        for i in range(6):
            r = 1.6 - i * 0.22
            for y in range(16):
                for x in range(16):
                    if (x + .5 - (cx - 2 - i)) ** 2 + (y + .5 - cy - math.sin(t + i) * 0.6) ** 2 <= r * r:
                        a[y, x] = (90, 170, 240, 255) if i > 2 else (150, 215, 255, 255)
        for y in range(16):
            for x in range(16):
                d = (x + .5 - cx) ** 2 + (y + .5 - cy) ** 2
                if d <= 7.5:
                    a[y, x] = (120, 200, 255, 255)
                if d <= 3.5:
                    a[y, x] = (220, 245, 255, 255)
                if d <= 1:
                    a[y, x] = W
        px(a, cx + 1 + (t % 2), cy - 3, W); px(a, cx - 3, cy + 3 - (t % 2), (220, 245, 255, 255))
        # dark outline
        m = a[:, :, 3] > 0
        o = np.zeros_like(m)
        o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
        a[o & ~m] = (20, 40, 90, 255)
        out.append(a)
    return out


def build():
    os.makedirs(WFX, exist_ok=True)
    sheets = {
        'spark': spark(), 'shockwave': shockwave(), 'runes': runes(), 'whiff': whiff(), 'magic': magic(),
        'spear_sweep': arc_sheet(13, 3, 120, 5, (C1, C2, C3)),
        'legend': arc_sheet(12, 4, 160, 5, ((220, 250, 255, 255), (110, 200, 250, 255), (60, 130, 220, 255)), sparkle=True),
    }
    for k, fr in sheets.items():
        save(fr, os.path.join(WFX, f'fx_{k}_anim_32x32.png'))
    save(magic_bolt(), os.path.join(FX, 'fx_magic_bolt_anim_16x16.png'))
    # preview for the docs
    allf = [f for fr in sheets.values() for f in fr]
    pv = np.zeros((32 * len(sheets), 32 * 6, 4), np.uint8); pv[:] = (50, 60, 52, 255)
    for r, fr in enumerate(sheets.values()):
        for c, f in enumerate(fr[:6]):
            m = f[:, :, 3] > 0
            pv[r * 32:(r + 1) * 32, c * 32:(c + 1) * 32][m] = f[m]
    os.makedirs(os.path.join(ROOT, 'Documentation', 'CombatAnimations'), exist_ok=True)
    Image.fromarray(pv, 'RGBA').resize((pv.shape[1] * 4, pv.shape[0] * 4), Image.NEAREST).save(
        os.path.join(ROOT, 'Documentation', 'CombatAnimations', 'weapon_effects.png'))
    print(len(sheets), 'weapon effects + magic bolt')


if __name__ == '__main__':
    build()
