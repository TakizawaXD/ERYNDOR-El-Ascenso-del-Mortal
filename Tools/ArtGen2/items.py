"""Equipment art: item icons, weapon swing effects and the flat minimal UI kit.

  python items.py ->  Assets/Art/UI/Icons/ui_items_16x16.png        33 weapon/armour icons (order = ItemDB icon index)
                      Assets/Art/Effects/Weapons/fx_<kind>_anim_32x32.png  white swing arcs (tinted per weapon at runtime)
                      Assets/Art/UI/Flat/ui_flat_*.png                      9-slice panel / slot / bar pieces
                      Documentation/Previews/items_preview.png
"""
import math, os
import numpy as np
from PIL import Image
from kit import C, P, hx, sheet

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OL = (24, 20, 37, 255)

# accept '#rrggbb' strings as colours as well as palette keys
_px = C.px
def _px_hex(self, x, y, c):
    _px(self, x, y, hx(c) if isinstance(c, str) and c.startswith('#') else c)
C.px = _px_hex


def col(c): return P[c] if isinstance(c, str) else c


def line(c, x0, y0, x1, y1, color, w=1):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) * 2 + 1
    for i in range(n + 1):
        t = i / n
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        for dx in range(w):
            c.px(round(x) + dx, round(y), color)


def done(c):
    c.outline(OL)
    return c


# blade palettes: (light, mid, dark)
STEEL = ('#eff3eb', '#c0cbdc', '#8b9bb4')
DARKS = ('#c0cbdc', '#5a6988', '#3c4258')
MOON = ('#c4f0ff', '#6ab4dc', '#2f6496')
FIRE = ('#fef09f', '#f77622', '#9e2835')
FROST = ('#eff3eb', '#8fd3ff', '#3a7bd5')
VENOM = ('#d4f25a', '#7cb82a', '#2f6420')
GOLD = ('#fef09f', '#feae34', '#c57d5e')
RUNE = ('#fdd2ed', '#b55088', '#68386c')
BONE = ('#f4edea', '#d9d0bc', '#a89a80')


def sword(length=11, width=2, blade=STEEL, guard='#feae34', grip='#743f39', curve=0.0, pommel='#feae34', gem=None):
    c = C(16, 16)
    # diagonal from bottom-left (grip) to top-right (tip)
    hx0, hy0 = 3, 12
    for i in range(length):
        bend = curve * (i / length) ** 2 * 3
        x, y = hx0 + 2 + i, hy0 - 2 - i + bend
        for k in range(width):
            c.px(round(x + k), round(y + k), blade[1] if k else blade[0])
        if width > 1: c.px(round(x + width), round(y + width - 1), blade[2])
    c.px(hx0 + 2 + length, round(hy0 - 2 - length + curve * 3), blade[0])        # tip
    line(c, hx0 - 1, hy0 - 1, hx0 + 3, hy0 + 3, guard)                           # guard
    c.px(hx0 + 1, hy0 + 1, guard)
    line(c, hx0, hy0 + 1, hx0 - 2, hy0 + 3, grip)                                 # grip
    c.px(hx0 - 3, hy0 + 4, pommel)
    if gem: c.px(hx0 + 1, hy0 + 1, gem)
    return done(c)


def dagger(blade=STEEL, gem=None):
    c = C(16, 16)
    for i in range(6):
        c.px(6 + i, 9 - i, blade[0]); c.px(7 + i, 9 - i, blade[1]); c.px(7 + i, 10 - i, blade[2])
    c.px(12, 3, blade[0])
    line(c, 4, 8, 7, 11, '#feae34'); line(c, 5, 11, 3, 13, '#743f39')
    if gem: c.px(5, 10, gem)
    return done(c)


def rapier():
    c = C(16, 16)
    line(c, 5, 10, 14, 1, STEEL[0])
    c.ellipse(4.5, 11.5, 2.2, 2.2, '#feae34'); c.ellipse(4.5, 11.5, 1.2, 1.2, '#c57d5e')
    line(c, 3, 13, 1, 15, '#743f39')
    return done(c)


def polearm(head='spear', shaft='#91533b', metal=STEEL, accent=None):
    c = C(16, 16)
    line(c, 1, 15, 11, 5, shaft)
    line(c, 2, 15, 11, 6, '#743f39')
    if head == 'spear':
        for i in range(4):
            c.px(11 + i, 4 - i, metal[0]); c.px(12 + i, 4 - i, metal[1]); c.px(11 + i, 5 - i, metal[2])
        c.px(10, 6, accent or '#feae34'); c.px(11, 6, accent or '#feae34')
    elif head == 'halberd':
        line(c, 11, 5, 14, 2, metal[0])
        for y in range(4, 10):
            for x in range(9, 9 + max(0, 4 - abs(y - 7))):
                c.px(x + 3, y - 1, metal[1])
        c.px(13, 8, metal[2]); c.px(14, 6, metal[2])
    else:   # trident
        for dx in (-2, 0, 2):
            line(c, 11 + dx // 2, 5 - dx // 2, 14 + dx // 2, 2 - dx // 2, metal[0])
        line(c, 10, 6, 13, 3, metal[1])
        c.px(11, 6, accent or '#2ce8f5')
    return done(c)


def axe(metal=STEEL, double=False, shaft='#91533b'):
    c = C(16, 16)
    line(c, 3, 14, 11, 4, shaft)
    for y in range(1, 9):
        span = 4 - abs(y - 4.5) * 0.6
        for x in range(int(span) + 1):
            c.px(11 + x, y, metal[1] if x < span - 1 else metal[0])
            if double: c.px(10 - x, y + 1, metal[1] if x < span - 1 else metal[0])
    line(c, 11, 2, 11, 7, metal[2])
    return done(c)


def hammer(metal=DARKS, holy=False):
    c = C(16, 16)
    line(c, 3, 14, 10, 5, '#91533b')
    c.rect(8, 1, 14, 6, metal[1]); c.rect(8, 1, 14, 2, metal[0]); c.rect(8, 6, 14, 6, metal[2])
    if holy:
        c.rect(10, 0, 12, 7, '#feae34'); c.rect(9, 3, 13, 4, '#feae34'); c.px(11, 3, '#fef09f')
    return done(c)


def bow(wood='#91533b', string='#eff3eb', tip=None, glow=None):
    c = C(16, 16)
    for t in range(-6, 7):
        x = 4 + int(round(5 * (1 - (t / 6.5) ** 2)))
        c.px(x, 8 + t, wood); c.px(x + 1, 8 + t, '#743f39' if abs(t) < 6 else wood)
    line(c, 4, 2, 4, 14, string)
    if tip:
        c.px(4, 1, tip); c.px(4, 15, tip)
    if glow:
        c.px(9, 8, glow); c.px(10, 7, glow); c.px(10, 9, glow)
    line(c, 4, 8, 13, 8, '#c0cbdc'); c.px(14, 8, '#eff3eb'); c.px(5, 7, '#9e2835'); c.px(5, 9, '#9e2835')
    return done(c)


def crossbow():
    c = C(16, 16)
    line(c, 2, 8, 13, 8, '#91533b'); line(c, 2, 9, 12, 9, '#743f39')
    for t in range(-5, 6):
        c.px(10 + int(round(2 * (1 - (t / 5.5) ** 2))), 8 + t, '#5a6988')
    line(c, 10, 3, 6, 8, '#eff3eb'); line(c, 10, 13, 6, 8, '#eff3eb')
    line(c, 7, 7, 14, 7, '#c0cbdc')
    c.rect(2, 9, 4, 11, '#743f39')
    return done(c)


def armor(body, trim, dark, light=None, pauldron=None, cape=None, emblem=None):
    c = C(16, 16)
    if cape:
        c.rect(3, 4, 12, 14, cape)
    for y in range(3, 14):
        half = 5 if y < 9 else 4
        for x in range(8 - half, 8 + half):
            c.px(x, y, body)
    c.rect(6, 3, 9, 4, dark)                          # neck hole
    for y in range(4, 13): c.px(7, y, dark) if y > 8 else None
    c.rect(3, 9, 12, 9, trim)                          # belt
    if pauldron:
        c.ellipse(3.5, 4.5, 2.2, 2, pauldron); c.ellipse(12.5, 4.5, 2.2, 2, pauldron)
    if light:
        c.rect(5, 5, 6, 8, light)
    if emblem:
        c.rect(9, 5, 9, 8, emblem); c.rect(8, 6, 10, 6, emblem)
    return done(c)


ICONS = [
    ('sword_short', lambda: sword(8)),
    ('sword_long', lambda: sword(11)),
    ('sword_knight', lambda: sword(11, 2, STEEL, '#feae34', '#2a64b8', gem='#2a64b8')),
    ('greatsword', lambda: sword(12, 3, STEEL, '#8b9bb4', '#3f2832')),
    ('katana', lambda: sword(12, 1, STEEL, '#262b44', '#9e2835', curve=1.2, pommel='#262b44')),
    ('katana_moon', lambda: sword(12, 1, MOON, '#c0cbdc', '#124e89', curve=1.2, pommel='#c4f0ff')),
    ('rapier', rapier),
    ('dagger', lambda: dagger()),
    ('dagger_venom', lambda: dagger(VENOM, gem='#d4f25a')),
    ('spear', lambda: polearm('spear')),
    ('halberd', lambda: polearm('halberd')),
    ('trident', lambda: polearm('trident', '#124e89', FROST)),
    ('axe', lambda: axe()),
    ('axe_frost', lambda: axe(FROST, True, '#3c4258')),
    ('hammer', lambda: hammer()),
    ('mace_holy', lambda: hammer(GOLD, True)),
    ('blade_ash', lambda: sword(11, 2, FIRE, '#262b44', '#262b44', gem='#f77622')),
    ('sword_rune', lambda: sword(12, 2, RUNE, '#fef09f', '#68386c', gem='#fdd2ed')),
    ('bow_short', lambda: bow()),
    ('bow_long', lambda: bow('#b86f50', tip='#feae34')),
    ('crossbow', crossbow),
    ('bow_elf', lambda: bow('#33984b', '#fef09f', '#fef09f', '#63c74d')),
    ('bow_bone', lambda: bow('#d9d0bc', '#c0cbdc', '#9e2835')),
    ('bow_dragon', lambda: bow('#9e2835', '#feae34', '#f77622', '#feae34')),
    ('armor_cloth', lambda: armor('#b86f50', '#743f39', '#743f39')),
    ('armor_leather', lambda: armor('#91533b', '#3f2832', '#3f2832', '#b86f50')),
    ('armor_chain', lambda: armor('#8b9bb4', '#5a3524', '#5a6988', '#c0cbdc')),
    ('armor_plate', lambda: armor('#c0cbdc', '#feae34', '#5a6988', '#eff3eb', '#8b9bb4')),
    ('armor_paladin', lambda: armor('#feae34', '#2a64b8', '#c57d5e', '#fef09f', '#fef09f', emblem='#eff3eb')),
    ('armor_shadow', lambda: armor('#3f3858', '#a63bbd', '#1f1a2e', '#5a5276', '#2d2742', cape='#5a1766')),
    ('armor_ranger', lambda: armor('#7a5530', '#2b5a25', '#3d2814', '#97703f', cape='#3e7a33')),
    ('armor_dragon', lambda: armor('#9e2835', '#feae34', '#4a142c', '#e43b44', '#feae34', emblem='#feae34')),
    ('armor_frost', lambda: armor('#8fd3ff', '#eff3eb', '#3a7bd5', '#eff3eb', '#c4f0ff')),
]


# ============================================================== swing effects (white, tinted at runtime)
def arc_frames(radius=11, thick=3, sweep=150, frames=5, thin_tail=True):
    out = []
    for f in range(frames):
        c = C(32, 32)
        a_end = -sweep / 2 + sweep * (f + 1) / frames
        a_start = max(-sweep / 2, a_end - sweep * 0.7)
        fade = 1 - f / frames * 0.55
        for y in range(32):
            for x in range(32):
                dx, dy = x + 0.5 - 12, y + 0.5 - 16
                r = math.hypot(dx, dy); a = math.degrees(math.atan2(dy, dx))
                if a_start <= a <= a_end and radius - thick <= r <= radius:
                    k = (a - a_start) / max(1, a_end - a_start)            # 0 tail .. 1 head
                    if thin_tail and r < radius - thick * k: continue
                    v = int(255 * fade * (0.35 + 0.65 * k))
                    c.a[y, x] = (255, 255, 255, v)
                    if r > radius - 1.2: c.a[y, x] = (255, 255, 255, min(255, v + 60))
        out.append(c)
    return out


def thrust_frames(length=20, frames=4):
    out = []
    for f in range(frames):
        c = C(32, 32)
        L = int(length * (0.5 + 0.5 * (f + 1) / frames))
        a = 1 - f / frames * 0.6
        for x in range(6, 6 + L):
            k = (x - 6) / max(1, L)
            w = 1 if k < 0.7 else 2 - int((k - 0.7) * 5)
            for dy in range(-w, w + 1):
                c.a[16 + dy, x] = (255, 255, 255, int(255 * a * (0.4 + 0.6 * k)))
        for i in range(3):
            c.a[16 + (i - 1) * 4, 6 + L - 6 + i] = (255, 255, 255, int(160 * a))
        out.append(c)
    return out


def impact_frames(frames=5):
    out = []
    for f in range(frames):
        c = C(32, 32)
        r = 4 + f * 2.6
        for y in range(32):
            for x in range(32):
                d = math.hypot(x + 0.5 - 18, (y + 0.5 - 16) * 1.5)
                if r - 1.6 <= d <= r:
                    c.a[y, x] = (255, 255, 255, int(255 * (1 - f / frames)))
        for i in range(6):
            ang = i * math.pi / 3 + f * 0.2
            px, py = 18 + math.cos(ang) * (r + 2), 16 + math.sin(ang) * (r + 2) / 1.5
            if 0 <= px < 32 and 0 <= py < 32: c.a[int(py), int(px)] = (255, 255, 255, int(220 * (1 - f / frames)))
        out.append(c)
    return out


FX = {
    'sword': lambda: arc_frames(11, 3, 150),
    'katana': lambda: arc_frames(13, 2, 190, 5),
    'greatsword': lambda: arc_frames(14, 5, 170, 6),
    'dagger': lambda: arc_frames(8, 2, 120, 4),
    'axe': lambda: arc_frames(12, 4, 130, 5),
    'thrust': lambda: thrust_frames(20),
    'impact': lambda: impact_frames(5),
}


# ============================================================== flat UI kit
def flat_panel():
    c = C(12, 12)
    c.rect(0, 0, 11, 11, (14, 12, 22, 215))
    c.rect(0, 0, 11, 0, (255, 255, 255, 46)); c.rect(0, 11, 11, 11, (0, 0, 0, 90))
    c.rect(0, 0, 0, 11, (255, 255, 255, 30)); c.rect(11, 0, 11, 11, (0, 0, 0, 70))
    for p in ((0, 0), (11, 0), (0, 11), (11, 11)): c.a[p[1], p[0]] = (0, 0, 0, 0)          # rounded corners
    return c


def flat_slot(sel=False):
    c = C(12, 12)
    c.rect(0, 0, 11, 11, (255, 255, 255, 120 if sel else 34))
    c.rect(1, 1, 10, 10, (10, 8, 16, 170))
    if sel: c.rect(1, 1, 10, 1, (254, 174, 52, 255))
    for p in ((0, 0), (11, 0), (0, 11), (11, 11)): c.a[p[1], p[0]] = (0, 0, 0, 0)
    return c


def build():
    icons = [f() for _, f in ICONS]
    s = sheet(icons, 16, 16, cols=8)
    # item icons are now drawn by weapons_hd.py (16 + 32 px); this sheet is only kept for the preview
    fxdir = os.path.join(ROOT, 'Assets', 'Art', 'Effects', 'Weapons'); os.makedirs(fxdir, exist_ok=True)
    for k, f in FX.items():
        fr = f(); sheet(fr, 32, 32).img().save(os.path.join(fxdir, f'fx_{k}_anim_32x32.png'))
    ui = os.path.join(ROOT, 'Assets', 'Art', 'UI', 'Flat'); os.makedirs(ui, exist_ok=True)
    flat_panel().img().save(os.path.join(ui, 'ui_flat_panel_9s3.png'))
    sheet([flat_slot(False), flat_slot(True)], 12, 12).img().save(os.path.join(ui, 'ui_flat_slot_12x12_9s3.png'))
    # preview
    pv = Image.new('RGBA', (8 * 20 + 4, 5 * 20 + 4 + 40), (30, 26, 40, 255))
    for i, ic in enumerate(icons):
        pv.alpha_composite(ic.img(), (4 + (i % 8) * 20, 4 + (i // 8) * 20))
    x = 4
    for k, f in FX.items():
        fr = f()[2].img(); pv.alpha_composite(fr.resize((20, 20), Image.NEAREST) if False else fr.crop((4, 6, 28, 26)), (x, 5 * 20 + 10)); x += 24
    pv.resize((pv.width * 4, pv.height * 4), Image.NEAREST).save(os.path.join(ROOT, 'Documentation', 'Previews', 'items_preview.png'))
    print(len(icons), 'icons', len(FX), 'fx')


if __name__ == '__main__':
    build()
