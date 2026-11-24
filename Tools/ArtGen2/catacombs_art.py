"""Art for LAS CATACUMBAS DEL REY OLVIDADO, built from the user's pack in G:/Juegos/Catacumbas (Szadi art, public domain).

  python Tools/ArtGen2/catacombs_art.py

  -> Assets/Art/World/Catacombs/*.png            props cut from the pack (sarcophagi, coffins, posts, urns, barrels,
                                                 chains, pillars, arches, grates) and its animations re-packed on a
                                                 uniform grid (torch, candles, spikes). A few mechanisms the pack does
                                                 not have (lever, pressure plate, runes, fire jets, wall spears, falling
                                                 rock, crumbling cracks, the throne, the king's relics) are drawn here
                                                 with the pack's own stone / iron / bone colours.
  -> Assets/Art/World/Maps/Dungeon_Catacumbas/ground_<cx>_<cy>.png   the painted floor of the dungeon in 512 px chunks
                                                 (floor slabs, brick faces with burial niches, mine rock, wall caps,
                                                 pits with their brick lip, bridges, cracked planks), 16 px per cell
  -> Assets/Art/World/Maps/Dungeon_Catacumbas/map.png                 1 px per cell for the M map
  -> Assets/Art/World/Catacombs/secret_<id>.png   how each hollow wall looks while it still stands
The pack is never modified; everything is copied / composed into Assets/Art.
"""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'Catacumbas')
OUT = os.path.join(ROOT, 'Assets', 'Art', 'World', 'Catacombs')
MAPDIR = os.path.join(ROOT, 'Assets', 'Art', 'World', 'Maps', 'Dungeon_Catacumbas')
LEVEL = os.path.join(ROOT, 'Assets', 'Game', 'Levels', 'Dungeon_Catacumbas.txt')
CELL = 16

MAIN = Image.open(os.path.join(SRC, 'mainlevbuild.png')).convert('RGBA')
DECO = Image.open(os.path.join(SRC, 'decorative.png')).convert('RGBA')


def crop(img, x, y, w, h):
    return img.crop((x, y, x + w, y + h))


def trim(im):
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def save(im, name):
    os.makedirs(OUT, exist_ok=True)
    im.save(os.path.join(OUT, name))


def sheet(frames, w, h, name, align='bottom'):
    """frames of different sizes on a uniform w x h grid, bottom-centred (the pack's animations are ragged)"""
    s = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        x = i * w + (w - f.width) // 2
        y = h - f.height if align == 'bottom' else (h - f.height) // 2
        s.alpha_composite(f, (x, y))
    save(s, f'{name}_anim_{w}x{h}.png')


# ---------------------------------------------------------------- palette sampled from the pack
STONE = [(14, 12, 12), (36, 31, 28), (58, 52, 44), (82, 74, 62), (112, 102, 86), (140, 130, 110)]
IRON = [(16, 15, 16), (38, 36, 40), (62, 60, 66), (96, 94, 102), (140, 138, 148)]
BONE = [(60, 52, 40), (120, 108, 88), (178, 168, 146), (222, 214, 196), (246, 242, 230)]
GOLD = [(70, 44, 12), (128, 88, 24), (196, 146, 44), (238, 200, 88), (255, 240, 170)]
VIOLET = [(40, 10, 60), (90, 30, 140), (150, 70, 220), (200, 140, 255), (240, 220, 255)]
FIRE = [(90, 20, 8), (180, 60, 14), (240, 120, 30), (255, 190, 70), (255, 245, 190)]
BLOOD = (110, 20, 24)
OUTL = (10, 8, 10, 255)


def blank(w, h):
    return Image.new('RGBA', (w, h), (0, 0, 0, 0))


def outline(im):
    a = np.array(im)
    s = a[:, :, 3] > 0
    o = np.zeros_like(s)
    o[1:] |= s[:-1]; o[:-1] |= s[1:]; o[:, 1:] |= s[:, :-1]; o[:, :-1] |= s[:, 1:]
    o &= ~s
    a[o] = OUTL
    return Image.fromarray(a, 'RGBA')


# ======================================================================== props cut from the pack
def cut_props():
    P = {
        # decorative.png
        'post_skull': (DECO, 1, 20, 13, 44), 'post_chain': (DECO, 17, 16, 14, 48), 'post_chains': (DECO, 65, 16, 13, 48),
        'post_plain': (DECO, 49, 22, 13, 42), 'post_broken': (DECO, 33, 36, 13, 28),
        'brazier_hanging': (DECO, 81, 16, 14, 32), 'brazier_water': (DECO, 97, 16, 14, 32),
        'chains': (DECO, 113, 16, 14, 22), 'chain': (DECO, 148, 16, 7, 30),
        'sarcophagus_cracked': (DECO, 5, 69, 37, 27), 'sarcophagus': (DECO, 5, 101, 37, 27), 'sarcophagus_broken': (DECO, 5, 136, 37, 24),
        'coffin_open': (DECO, 55, 69, 18, 43), 'coffin': (DECO, 87, 69, 18, 43), 'coffin_broken': (DECO, 87, 122, 18, 38),
        'barrel': (DECO, 144, 71, 16, 25), 'barrel_broken': (DECO, 144, 96, 16, 16),
        'barrel_s': (DECO, 130, 75, 12, 21), 'barrel_s_broken': (DECO, 130, 97, 12, 15),
        'urn_red': (DECO, 144, 124, 16, 20), 'urn_red_broken': (DECO, 144, 147, 16, 13),
        'urn_red_s': (DECO, 162, 128, 12, 16), 'urn_red_s_broken': (DECO, 162, 148, 12, 12),
        'urn_green': (DECO, 144, 172, 16, 20), 'urn_green_broken': (DECO, 144, 195, 16, 13),
        'urn_green_s': (DECO, 162, 176, 12, 16), 'urn_green_s_broken': (DECO, 162, 196, 12, 12),
        # mainlevbuild.png
        'stairs_arch': (MAIN, 880, 0, 64, 105), 'door_arch': (MAIN, 640, 0, 80, 96),
        'pillar_a': (MAIN, 400, 112, 16, 80), 'pillar_b': (MAIN, 432, 112, 16, 75), 'pillar_c': (MAIN, 464, 112, 16, 80),
        'pillar_d': (MAIN, 640, 112, 16, 80), 'pedestal': (MAIN, 592, 135, 32, 57), 'post_stone': (MAIN, 672, 144, 16, 48),
        'pedestal_b': (MAIN, 704, 144, 32, 48), 'grate_big': (MAIN, 487, 202, 82, 79), 'grate': (MAIN, 496, 288, 32, 32),
        'grate_v': (MAIN, 544, 288, 16, 32), 'grate_moss': (MAIN, 496, 336, 32, 32), 'ledge': (MAIN, 496, 128, 64, 16),
        'gate_frame': (MAIN, 496, 32, 128, 80),
    }
    for name, (img, x, y, w, h) in P.items():
        save(trim(crop(img, x, y, w, h)), name + '.png')
    # a stack of crates/barrels for the mine: two barrels side by side
    st = blank(28, 25); st.alpha_composite(trim(crop(DECO, 144, 71, 16, 25)), (0, 0)); st.alpha_composite(trim(crop(DECO, 130, 75, 12, 21)), (16, 4))
    save(st, 'crate_stack.png')
    # an armour rack for the hall of arms: a stone post with a chain
    ar = blank(16, 48); ar.alpha_composite(trim(crop(MAIN, 672, 144, 16, 48)), (0, 0)); ar.alpha_composite(trim(crop(DECO, 148, 16, 7, 30)), (4, 2))
    save(ar, 'armor_rack.png')
    # the pack's animations, re-packed on a uniform grid
    sheet([Image.open(os.path.join(SRC, f'torch_{i}.png')).convert('RGBA') for i in range(1, 5)], 16, 16, 'torch')
    sheet([Image.open(os.path.join(SRC, f'candleA_0{i}.png')).convert('RGBA') for i in range(1, 5)], 8, 16, 'candleA')
    sheet([Image.open(os.path.join(SRC, f'candleB_0{i}.png')).convert('RGBA') for i in range(1, 5)], 14, 16, 'candleB')
    sheet([Image.open(os.path.join(SRC, f'spike_{i}.png')).convert('RGBA') for i in range(5)], 14, 14, 'spike')


# ======================================================================== mechanisms drawn in the pack's colours
def draw_mechanisms():
    # lever: stone base + iron handle, 2 frames (left = closed, right = pulled)
    fr = []
    for k in (0, 1):
        im = blank(16, 16); d = ImageDraw.Draw(im)
        d.rectangle([3, 11, 12, 15], fill=STONE[2]); d.rectangle([3, 11, 12, 11], fill=STONE[4]); d.rectangle([4, 14, 11, 15], fill=STONE[1])
        x1, y1 = (4, 3) if k == 0 else (12, 3)
        d.line([(8, 12), (x1, y1)], fill=IRON[3], width=2); d.line([(8, 12), (x1, y1)], fill=IRON[1], width=1)
        d.ellipse([x1 - 2, y1 - 2, x1 + 2, y1 + 2], fill=BLOOD if k == 0 else GOLD[2])
        fr.append(outline(im))
    sheet(fr, 16, 16, 'lever')
    # pressure plate: a square slab, up and pressed
    fr = []
    for k in (0, 1):
        im = blank(16, 16); d = ImageDraw.Draw(im)
        d.rectangle([1, 3 + k, 14, 14], fill=STONE[1]); d.rectangle([2, 3 + k, 13, 12], fill=STONE[3 - k]); d.rectangle([2, 3 + k, 13, 3 + k], fill=STONE[5 - k])
        d.rectangle([5, 6 + k, 10, 9 + k], outline=STONE[1])
        fr.append(im)
    sheet(fr, 16, 16, 'plate')
    # rune: a glyph circle that charges (dim, glow, bright, blast)
    fr = []
    for k in range(4):
        im = blank(32, 32); d = ImageDraw.Draw(im)
        col = VIOLET[min(4, 1 + k)]
        a = (90, 150, 220, 255)[k]
        d.ellipse([3, 9, 28, 24], outline=col + (a,), width=1)
        d.ellipse([7, 11, 24, 22], outline=VIOLET[2] + (a,), width=1)
        for i in range(6):
            t = i * math.pi / 3 + k * 0.2
            x, y = 16 + math.cos(t) * 10, 16.5 + math.sin(t) * 5
            d.point([(x, y)], fill=VIOLET[4] + (a,)); d.point([(x + 1, y)], fill=col + (a,))
        d.line([(16, 12), (16, 21)], fill=col + (a,)); d.line([(11, 16), (21, 17)], fill=col + (a,))
        fr.append(im)
    sheet(fr, 32, 32, 'rune', align='center')
    # fire jet: an iron grate nozzle and a flame column (6 frames: sputter, burst, roar x2, fade x2)
    noz = blank(16, 16); d = ImageDraw.Draw(noz)
    d.rectangle([2, 4, 13, 13], fill=IRON[1]); d.rectangle([3, 5, 12, 12], fill=IRON[2])
    for x in (5, 8, 11): d.line([(x, 5), (x, 12)], fill=IRON[0])
    d.rectangle([3, 5, 12, 5], fill=IRON[3]); save(outline(noz), 'firejet_nozzle.png')
    fr = []
    rng = random.Random(4)
    for k in range(6):
        im = blank(16, 48); d = ImageDraw.Draw(im)
        hgt = (6, 30, 46, 46, 30, 10)[k]
        for y in range(48 - hgt, 48):
            t = (y - (48 - hgt)) / max(1, hgt)
            w = 2 + t * 5 + rng.random() * 1.5
            c = FIRE[min(4, int(t * 3) + (1 if k in (2, 3) else 0))]
            d.line([(8 - w, y), (8 + w, y)], fill=c + (230,))
            if rng.random() < .3: d.point([(8 + rng.randint(-5, 5), y - 2)], fill=FIRE[4])
        fr.append(im)
    sheet(fr, 16, 48, 'fire')
    # wall spear: a long iron spear with a bone-white tip (pointing right; the game flips / rotates it)
    sp = blank(48, 8); d = ImageDraw.Draw(sp)
    d.line([(0, 4), (38, 4)], fill=IRON[2], width=2); d.line([(0, 3), (38, 3)], fill=IRON[3])
    d.polygon([(38, 1), (47, 4), (38, 7)], fill=BONE[3]); d.line([(38, 2), (45, 4)], fill=BONE[4])
    save(outline(sp), 'spear.png')
    slot = blank(16, 16); d = ImageDraw.Draw(slot)
    d.rectangle([5, 3, 11, 12], fill=(6, 5, 6, 255)); d.rectangle([5, 3, 11, 3], fill=STONE[4]); save(slot, 'spear_slot.png')
    # falling rock + dust
    rk = blank(20, 18); d = ImageDraw.Draw(rk)
    d.polygon([(3, 6), (9, 1), (16, 3), (19, 10), (14, 17), (5, 16), (1, 11)], fill=STONE[2])
    d.polygon([(4, 7), (9, 2), (14, 4), (10, 8)], fill=STONE[4]); d.line([(9, 8), (13, 14)], fill=STONE[1])
    save(outline(rk), 'rock.png')
    rub = blank(24, 12); d = ImageDraw.Draw(rub)
    for (x, y, r) in ((5, 8, 4), (12, 7, 5), (19, 8, 4), (9, 4, 3)):
        d.ellipse([x - r, y - r // 2 - 1, x + r, y + r // 2 + 1], fill=STONE[2]); d.ellipse([x - r + 1, y - r // 2 - 1, x, y], fill=STONE[4])
    save(outline(rub), 'rubble.png')
    # crumbling floor: cracks over a cell (3 stages) and the hole it leaves
    fr = []
    for k in range(3):
        im = blank(16, 16); d = ImageDraw.Draw(im)
        rng = random.Random(9)
        for i in range(2 + k * 2):
            x, y = rng.randint(2, 13), rng.randint(2, 13)
            for j in range(3 + k):
                nx, ny = x + rng.randint(-4, 4), y + rng.randint(-4, 4)
                d.line([(x, y), (nx, ny)], fill=(8, 6, 6, 230)); x, y = nx, ny
        if k == 2: d.rectangle([4, 5, 11, 11], fill=(5, 4, 5, 200))
        fr.append(im)
    sheet(fr, 16, 16, 'cracks')
    hole = blank(16, 16); d = ImageDraw.Draw(hole)
    d.rectangle([0, 0, 15, 15], fill=(4, 3, 5, 255)); d.rectangle([0, 0, 15, 3], fill=(40, 30, 28, 255)); d.line([(0, 3), (15, 3)], fill=(20, 14, 14, 255))
    save(hole, 'hole.png')
    # standing brazier
    br = blank(16, 24); d = ImageDraw.Draw(br)
    d.rectangle([7, 9, 8, 21], fill=IRON[2]); d.rectangle([4, 21, 11, 23], fill=IRON[1])
    d.polygon([(2, 5), (13, 5), (11, 10), (4, 10)], fill=IRON[2]); d.line([(2, 5), (13, 5)], fill=IRON[4])
    save(outline(br), 'brazier.png')
    # key, crown, relic (pickups)
    k = blank(16, 16); d = ImageDraw.Draw(k)
    d.ellipse([2, 2, 8, 8], outline=BONE[3], width=2); d.line([(7, 7), (13, 13)], fill=BONE[3], width=2)
    d.line([(11, 13), (13, 11)], fill=BONE[2]); d.point([(10, 12)], fill=BONE[2]); save(outline(k), 'key_bone.png')
    k2 = blank(16, 16); d = ImageDraw.Draw(k2)
    d.ellipse([2, 2, 8, 8], outline=BLOOD + (255,), width=2); d.line([(7, 7), (13, 13)], fill=GOLD[2], width=2)
    d.line([(11, 13), (13, 11)], fill=GOLD[1]); save(outline(k2), 'key_blood.png')
    cr = blank(20, 14); d = ImageDraw.Draw(cr)
    d.rectangle([2, 8, 17, 12], fill=GOLD[2]); d.line([(2, 8), (17, 8)], fill=GOLD[4])
    for x in (2, 7, 12, 17): d.polygon([(x - 2, 9), (x + 2, 9), (x, 2 if x != 12 else 5)], fill=GOLD[3])
    d.line([(10, 8), (12, 12)], fill=(20, 10, 10)); d.point([(7, 10)], fill=VIOLET[3]); d.point([(14, 10)], fill=VIOLET[3])
    save(outline(cr), 'crown_broken.png')
    rl = blank(14, 16); d = ImageDraw.Draw(rl)
    d.ellipse([1, 3, 12, 14], fill=IRON[2]); d.ellipse([3, 5, 10, 12], fill=VIOLET[2]); d.ellipse([4, 6, 7, 9], fill=VIOLET[4])
    d.rectangle([5, 0, 8, 3], fill=GOLD[2]); save(outline(rl), 'relic_seal.png')
    # the king's throne: black stone and tarnished gold, a skull at the top of the back
    th = blank(48, 56); d = ImageDraw.Draw(th)
    d.rectangle([6, 4, 41, 40], fill=STONE[1]); d.rectangle([8, 6, 39, 38], fill=STONE[2])
    for x in (6, 38): d.rectangle([x, 2, x + 4, 52], fill=STONE[3]); d.rectangle([x, 2, x + 4, 3], fill=GOLD[3])
    d.rectangle([4, 34, 43, 44], fill=STONE[2]); d.rectangle([4, 34, 43, 35], fill=STONE[4])
    d.rectangle([2, 44, 45, 54], fill=STONE[1]); d.rectangle([2, 44, 45, 45], fill=STONE[3])
    d.rectangle([12, 10, 35, 30], fill=(60, 14, 22)); d.rectangle([13, 11, 34, 29], fill=(84, 20, 30))
    d.polygon([(16, 2), (24, -2), (32, 2), (30, 6), (18, 6)], fill=GOLD[2])
    d.ellipse([19, 0, 29, 9], fill=BONE[3]); d.rectangle([21, 4, 22, 5], fill=VIOLET[3]); d.rectangle([26, 4, 27, 5], fill=VIOLET[3])
    d.line([(16, 34), (31, 34)], fill=GOLD[3]); d.line([(8, 47), (39, 47)], fill=GOLD[1])
    save(outline(th), 'throne.png')
    # a broken column (its base and the fallen drum) for the arena
    col = trim(crop(MAIN, 400, 112, 16, 80))
    base = col.crop((0, col.height - 26, col.width, col.height))
    bc = blank(32, 30); bc.alpha_composite(base, (8, 4))
    drum = col.crop((0, 10, col.width, 26)).rotate(90, expand=True)
    bc.alpha_composite(drum, (0, 30 - drum.height))
    save(bc, 'column_broken.png')
    # the big rune circle of the throne room (phase 3 floor runes) - 2 frames
    fr = []
    for k in range(2):
        im = blank(64, 40); d = ImageDraw.Draw(im)
        a = (120, 230)[k]
        d.ellipse([2, 2, 61, 37], outline=VIOLET[3] + (a,), width=2); d.ellipse([10, 7, 53, 32], outline=VIOLET[2] + (a,), width=1)
        for i in range(8):
            t = i * math.pi / 4 + k * 0.4
            x, y = 32 + math.cos(t) * 26, 20 + math.sin(t) * 15
            d.line([(x - 2, y), (x + 2, y)], fill=VIOLET[4] + (a,)); d.line([(x, y - 2), (x, y + 2)], fill=VIOLET[4] + (a,))
        fr.append(im)
    sheet(fr, 64, 40, 'runecircle', align='center')
    # prison bars seen from the front (cells)
    bars = blank(48, 48); d = ImageDraw.Draw(bars)
    d.rectangle([0, 0, 47, 4], fill=IRON[2]); d.rectangle([0, 43, 47, 47], fill=IRON[1])
    for x in range(3, 47, 6): d.rectangle([x, 4, x + 1, 43], fill=IRON[3]); d.line([(x, 4), (x, 43)], fill=IRON[4])
    d.line([(0, 0), (47, 0)], fill=IRON[4])
    save(outline(bars), 'bars.png')
    # door sprites: a portcullis for horizontal openings (3 cells) and a barred side gate for vertical ones
    gate = trim(crop(MAIN, 496, 32, 128, 80))
    bars_only = gate.crop((16, 0, 80, gate.height))                # the barred middle of the pack's portcullis frame
    gh = blank(48, 64); g = bars_only.resize((48, bars_only.height), Image.NEAREST); gh.alpha_composite(g, (0, 64 - g.height))
    save(gh, 'door_bars_h.png')
    gv = blank(16, 64); d = ImageDraw.Draw(gv)
    d.rectangle([5, 0, 10, 63], fill=IRON[1]); d.rectangle([6, 0, 9, 63], fill=IRON[2]); d.line([(6, 0), (6, 63)], fill=IRON[4])
    for y in range(4, 64, 10): d.rectangle([3, y, 12, y + 1], fill=IRON[3])
    save(outline(gv), 'door_bars_v.png')
    # a sealing rune door (boss / victory doors): stone slab with a violet seal
    sd = blank(48, 64); d = ImageDraw.Draw(sd)
    d.rectangle([0, 6, 47, 63], fill=STONE[1]); d.rectangle([2, 8, 45, 61], fill=STONE[2]); d.line([(2, 8), (45, 8)], fill=STONE[4])
    d.line([(24, 8), (24, 61)], fill=STONE[0])
    d.ellipse([12, 22, 36, 46], outline=VIOLET[3], width=2); d.line([(24, 26), (24, 42)], fill=VIOLET[4]); d.line([(17, 34), (31, 34)], fill=VIOLET[4])
    save(outline(sd), 'door_seal_h.png')
    sv = blank(16, 64); d = ImageDraw.Draw(sv)
    d.rectangle([2, 0, 13, 63], fill=STONE[1]); d.rectangle([3, 1, 12, 62], fill=STONE[2]); d.line([(3, 1), (3, 62)], fill=STONE[4])
    for y in (16, 32, 48): d.ellipse([5, y - 3, 10, y + 3], outline=VIOLET[3])
    save(outline(sv), 'door_seal_v.png')


# ======================================================================== the painted dungeon floor
FLOORS = {     # zone -> list of (x, y, w, h) tiles in mainlevbuild.png
    'k': [(736, 272, 32, 32), (784, 272, 32, 32), (736, 320, 32, 32), (784, 320, 32, 32)],
    'l': [(736, 368, 32, 32), (784, 368, 32, 32), (784, 320, 32, 32)],
    'm': [(832, 272, 32, 32), (880, 272, 32, 32), (832, 320, 32, 32), (880, 320, 32, 32)],
    'n': [(928, 272, 32, 32), (976, 272, 32, 32), (928, 320, 32, 32), (976, 368, 32, 32)],
    'o': [(832, 368, 32, 32), (880, 368, 32, 32)],
    'p': [(736, 208, 32, 48), (784, 208, 32, 48)],
}
FACES = {      # zone -> brick / rock faces (48 px tall panels)
    'k': [(80, 272, 64, 48), (176, 272, 64, 48), (80, 496, 64, 48), (176, 496, 64, 48), (272, 208, 64, 48)],
    'l': [(304, 336, 64, 48), (384, 336, 64, 48), (304, 400, 64, 48), (384, 400, 64, 48)],
    'm': [(272, 208, 80, 48), (176, 272, 64, 48), (272, 208, 64, 48)],
    'n': [(368, 208, 64, 48), (80, 272, 64, 48), (368, 208, 64, 48)],
    'o': [(272, 272, 64, 48), (336, 272, 64, 48), (368, 208, 64, 48)],
    'p': [(272, 208, 80, 48), (272, 272, 160, 48)],
}
PIT = crop(MAIN, 619, 267, 74, 74)


def load_level():
    L = open(LEVEL, encoding='utf-8').read().split('\n')
    W, H = map(int, [l for l in L if l.startswith('SIZE ')][0].split()[1:3])
    t0, e0, r0 = L.index('TERRAIN'), L.index('ENTITIES'), L.index('REGIONS')
    T = [list(r) for r in L[t0 + 1:t0 + 1 + H]]
    Rg = L[r0 + 1:r0 + 1 + H]
    objs = []
    for l in L:
        if not l.startswith('OBJ '): continue
        head = l.split(' | ')[0].split()
        kw = dict(p.split('=', 1) for p in head[4:] if '=' in p)
        objs.append((head[1], float(head[2]), float(head[3]), kw))
    return W, H, T, Rg, objs


def tile_rgb(box):
    return np.array(crop(MAIN, *box).convert('RGBA'), np.float32)


def paint(W, H, T, Rg, seed=7):
    rng = random.Random(seed)
    img = np.zeros((H * CELL, W * CELL, 4), np.float32)
    img[:, :, 3] = 255
    solid = np.array([[T[y][x] == '#' for x in range(W)] for y in range(H)])
    pit = np.array([[T[y][x] == 'O' for x in range(W)] for y in range(H)])

    def S(x, y): return x < 0 or y < 0 or x >= W or y >= H or solid[y, x]
    def floorish(x, y): return 0 <= x < W and 0 <= y < H and not solid[y, x]

    # ---- floors: slabs on a 2-cell grid (3 cells tall for the throne slabs), random variant per slab
    tiles = {z: [tile_rgb(b) for b in bs] for z, bs in FLOORS.items()}
    for y in range(H):
        for x in range(W):
            if solid[y, x]: continue
            z = Rg[y][x]
            ts = tiles.get(z, tiles['k'])
            th = ts[0].shape[0] // CELL
            tx, ty = x // 2, y // th
            k = (tx * 7349 + ty * 1913 + (tx * ty) % 7) % len(ts)
            t = ts[k]
            sx, sy = (x % 2) * CELL, (y % th) * CELL
            img[y * CELL:(y + 1) * CELL, x * CELL:(x + 1) * CELL] = t[sy:sy + CELL, sx:sx + CELL]
    img[:, :, :3] *= 1.18                                   # the pack's slabs are very dark under the dungeon light
    # ---- faces: the bottom 3 wall cells above any floor show a brick / rock face
    face = np.zeros((H, W), bool)
    for x in range(W):
        for y in range(H - 1):
            if solid[y, x] and floorish(x, y + 1):
                for k in range(3):
                    if y - k >= 0 and solid[y - k, x]: face[y - k, x] = True
                    else: break
    panels = {z: [tile_rgb(b) for b in bs] for z, bs in FACES.items()}
    for y in range(H):
        x = 0
        while x < W:
            if not (face[y, x] and (y + 1 >= H or not solid[y + 1, x])):
                x += 1; continue
            x0 = x
            while x < W and face[y, x] and (y + 1 >= H or not solid[y + 1, x]): x += 1
            z = Rg[min(H - 1, y + 1)][x0]
            ps = panels.get(z, panels['k'])
            # paint the run of faces whose bottom is row y, panel after panel, 3 cells tall (cut when the wall is thinner)
            px0, bottom = x0 * CELL, (y + 1) * CELL
            cx, pi = px0, rng.randrange(len(ps))
            while cx < x * CELL:
                p = ps[pi % len(ps)]; pi += 1
                w = min(p.shape[1], x * CELL - cx)
                for col in range(w):
                    gx = (cx + col) // CELL
                    hcells = 0
                    while hcells < 3 and y - hcells >= 0 and face[y - hcells, gx]: hcells += 1
                    hpx = hcells * CELL
                    img[bottom - hpx:bottom, cx + col] = p[p.shape[0] - hpx:, col]
                cx += w
    # stone lip at the top of every face and a soft shadow on the floor below it
    lip = np.array([STONE[3] + (255,), STONE[4] + (255,), STONE[2] + (255,), STONE[1] + (255,)], np.float32)
    for y in range(H):
        for x in range(W):
            if face[y, x] and (y == 0 or not face[y - 1, x]):
                for k in range(4): img[y * CELL + k, x * CELL:(x + 1) * CELL] = lip[k]
            if not solid[y, x] and y > 0 and face[y - 1, x]:
                for k in range(5): img[y * CELL + k, x * CELL:(x + 1) * CELL, :3] *= 0.55 + k * 0.09
    # ---- caps: the top of the wall mass is the dark void with a carved stone rim along every floor / face edge
    void = np.array([11, 9, 11, 255], np.float32)
    cap = solid & ~face
    for y in range(H):
        for x in range(W):
            if not cap[y, x]: continue
            img[y * CELL:(y + 1) * CELL, x * CELL:(x + 1) * CELL] = void
    rim = [STONE[1], STONE[3], STONE[4], STONE[2], STONE[1]]
    for y in range(H):
        for x in range(W):
            if not cap[y, x]: continue
            X, Y = x * CELL, y * CELL
            open_s = not S(x, y + 1) or (y + 1 < H and face[y + 1, x])
            open_n = not S(x, y - 1)
            open_w = not S(x - 1, y) or (x > 0 and face[y, x - 1] and not cap[y, x - 1])
            open_e = not S(x + 1, y) or (x + 1 < W and face[y, x + 1] and not cap[y, x + 1])
            for k, c in enumerate(rim):
                c = np.array(c + (255,), np.float32)
                if open_s: img[Y + CELL - 1 - k, X:X + CELL] = c
                if open_n: img[Y + k, X:X + CELL] = c
                if open_w: img[Y:Y + CELL, X + k] = c
                if open_e: img[Y:Y + CELL, X + CELL - 1 - k] = c
            if (x + y) % 2 == 0 and (open_s or open_n):           # block seams along the rim
                yy = Y + CELL - 5 if open_s else Y
                img[yy:yy + 5, X, :3] = STONE[0]
    # side walls next to faces: the face edge gets a stone pilaster
    for y in range(H):
        for x in range(W):
            if not face[y, x]: continue
            for dx in (-1, 1):
                nx = x + dx
                if 0 <= nx < W and not solid[y, nx]:
                    X = x * CELL + (0 if dx < 0 else CELL - 4)
                    img[y * CELL:(y + 1) * CELL, X:X + 4, :3] = np.array(STONE[3], np.float32)
                    img[y * CELL:(y + 1) * CELL, X + (0 if dx < 0 else 3), :3] = np.array(STONE[1], np.float32)
    # ---- pits / the abyss: black depth, a brick lip on the far (north) side, a dark rim all round
    brick = np.array(PIT, np.float32)[6:30, 6:68]                       # the pit's inner brick wall from the pack
    for y in range(H):
        for x in range(W):
            if not pit[y, x]: continue
            X, Y = x * CELL, y * CELL
            depth = 0
            while y - depth - 1 >= 0 and pit[y - depth - 1, x]: depth += 1
            shade = max(0.0, 1 - depth * 0.35)
            img[Y:Y + CELL, X:X + CELL] = np.array([5, 4, 6, 255], np.float32)
            if depth <= 1:
                band = brick[depth * CELL: depth * CELL + CELL]
                bx = (x * CELL) % (brick.shape[1] - CELL)
                part = band[:, bx:bx + CELL].copy()
                part[:, :, :3] *= 0.8 * shade + 0.2
                img[Y:Y + part.shape[0], X:X + CELL] = part
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H and not pit[ny, nx] and not solid[ny, nx]:
                    if dy == -1: img[Y:Y + 2, X:X + CELL, :3] = (60, 46, 38)
                    if dy == 1: img[Y + CELL - 3:Y + CELL, X:X + CELL, :3] = (44, 34, 30)
                    if dx == -1: img[Y:Y + CELL, X:X + 2, :3] = (44, 34, 30)
                    if dx == 1: img[Y:Y + CELL, X + CELL - 2:X + CELL, :3] = (44, 34, 30)
    # ---- bridges: slabs with a carved stone edge (the pack's ledge strip) along the abyss
    ledge = np.array(crop(MAIN, 496, 128, 64, 16), np.float32)
    for y in range(H):
        for x in range(W):
            if T[y][x] != '=': continue
            X, Y = x * CELL, y * CELL
            if y + 1 < H and pit[y + 1, x]:
                img[Y + CELL - 5:Y + CELL, X:X + CELL] = ledge[11:16, (x * CELL) % 48:(x * CELL) % 48 + CELL]
            if y > 0 and pit[y - 1, x]:
                img[Y:Y + 4, X:X + CELL] = ledge[0:4, (x * CELL) % 48:(x * CELL) % 48 + CELL]
            if x > 0 and pit[y, x - 1]: img[Y:Y + CELL, X:X + 3, :3] = STONE[3]; img[Y:Y + CELL, X, :3] = STONE[1]
            if x + 1 < W and pit[y, x + 1]: img[Y:Y + CELL, X + CELL - 3:X + CELL, :3] = STONE[2]; img[Y:Y + CELL, X + CELL - 1, :3] = STONE[0]
    # ---- crumbling floor: rotten, cracked slabs (the warning is painted into the ground)
    for y in range(H):
        for x in range(W):
            if T[y][x] != 'x': continue
            X, Y = x * CELL, y * CELL
            img[Y:Y + CELL, X:X + CELL, :3] *= 0.7
            img[Y:Y + CELL, X:X + CELL, 0] += 8
            r2 = random.Random(x * 31 + y)
            for i in range(3):
                cx, cy = r2.randint(1, 14), r2.randint(1, 14)
                for j in range(4):
                    nx, ny = max(0, min(15, cx + r2.randint(-3, 3))), max(0, min(15, cy + r2.randint(-3, 3)))
                    for t in np.linspace(0, 1, 6):
                        img[Y + int(cy + (ny - cy) * t), X + int(cx + (nx - cx) * t), :3] = (14, 10, 10)
                    cx, cy = nx, ny
    # ---- soft ambient occlusion along the walls
    for y in range(H):
        for x in range(W):
            if solid[y, x] or pit[y, x]: continue
            X, Y = x * CELL, y * CELL
            if S(x - 1, y): img[Y:Y + CELL, X:X + 3, :3] *= 0.7
            if S(x + 1, y): img[Y:Y + CELL, X + CELL - 3:X + CELL, :3] *= 0.7
            if S(x, y + 1): img[Y + CELL - 2:Y + CELL, X:X + CELL, :3] *= 0.75
    return np.clip(img, 0, 255).astype(np.uint8), face


def main():
    os.makedirs(OUT, exist_ok=True)
    cut_props()
    draw_mechanisms()
    W, H, T, Rg, objs = load_level()
    # how every hollow wall looks while it stands: paint once with the secret cells as wall and cut each one out
    secret_cells = [(x, y) for y in range(H) for x in range(W) if T[y][x] == 'S']
    T2 = [r[:] for r in T]
    for x, y in secret_cells: T2[y][x] = '#'
    closed, _ = paint(W, H, T2, Rg)
    for kind, ox, oy, kw in objs:
        if kind != 'secretwall': continue
        x0, y0, x1, y1 = int(kw['x0']), int(kw['y0']), int(kw['x1']), int(kw['y1'])
        part = closed[y0 * CELL:(y1 + 1) * CELL, x0 * CELL:(x1 + 1) * CELL].copy()
        im = Image.fromarray(part, 'RGBA')
        d = ImageDraw.Draw(im)
        rng = random.Random(len(kw['id']))
        cx, cy = im.width // 2, im.height - 20          # a hollow crack, the hint that it can be broken
        for i in range(4):
            x, y = cx, cy
            for j in range(5):
                nx, ny = x + rng.randint(-5, 5), y + rng.randint(-6, 3)
                d.line([(x, y), (nx, ny)], fill=(10, 8, 8, 255)); d.line([(x + 1, y), (nx + 1, ny)], fill=(70, 60, 52, 255))
                x, y = nx, ny
        save(im, f"secret_{kw['id']}.png")
    img, face = paint(W, H, T, Rg)
    os.makedirs(MAPDIR, exist_ok=True)
    for f in os.listdir(MAPDIR):
        if f.startswith('ground_') and f.endswith('.png'): os.remove(os.path.join(MAPDIR, f))
    CH = 512
    for cy in range(0, img.shape[0], CH):
        for cx in range(0, img.shape[1], CH):
            Image.fromarray(img[cy:cy + CH, cx:cx + CH], 'RGBA').save(os.path.join(MAPDIR, f'ground_{cx // CH}_{cy // CH}.png'))
    # the M map: one pixel per cell, floors tinted per zone
    zc = {'k': (120, 110, 96), 'l': (118, 100, 76), 'm': (92, 110, 116), 'n': (96, 116, 92), 'o': (100, 96, 120), 'p': (128, 92, 100)}
    mp = Image.new('RGBA', (W, H), (16, 13, 16, 255))
    for y in range(H):
        for x in range(W):
            t = T[y][x]
            if t == '#': continue
            c = (8, 6, 8) if t == 'O' else (150, 110, 60) if t in '=x' else zc.get(Rg[y][x], (110, 110, 110))
            mp.putpixel((x, y), c + (255,))
    mp.save(os.path.join(MAPDIR, 'map.png'))
    Image.fromarray(img, 'RGBA').resize((img.shape[1] // 4, img.shape[0] // 4), Image.BOX).save(
        os.path.join(ROOT, 'Documentation', 'Screenshots', 'catacumbas_plano.png'))
    print('catacombs art:', len(os.listdir(OUT)), 'files in', OUT, '| ground', img.shape[1], 'x', img.shape[0])


if __name__ == '__main__':
    main()
