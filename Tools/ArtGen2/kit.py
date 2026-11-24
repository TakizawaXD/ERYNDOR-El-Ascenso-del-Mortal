"""Style kit #2 - matches the user's reference (cozy top-down pixel art, 16 px tiles).

Colours are sampled from the reference screenshot; the blob-47 autotile engine is reused from Tools/ArtGen/tiles.py.
Output: Assets/Art/World/...
"""
import math, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ArtGen'))
import tiles as TL                      # noqa: E402  (blob engine: material, dist_to, MASKS, periodic_*)
from tiles import T, MASKS               # noqa: E402

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Assets', 'Art', 'World'))


def hx(s, a=255):
    s = s.lstrip('#'); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


P = {k: hx(v) for k, v in dict(
    # greens (reference)
    g_hi='#63c74d', g_lt='#5ac54f', g_md='#33984b', g='#3e8948', g_dk='#35743d', g_dk2='#26542c', g_ol='#265c42',
    g_dp='#1e6f50', g_dp2='#134c4c', g_bk='#193c3e', g_ol2='#091b15', g_mo='#50af5d',
    # earth / wood
    s_hi='#ead4aa', s='#e4a672', s_md='#e69c69', s_dk='#c57d5e', s_sh='#b86f50', w_lt='#b86f50', w='#91533b',
    w_dk='#743f39', w_ol='#3f2832', bank='#6d483b', bank_lt='#9c6754', w_mid='#8c5f40',
    # water
    wa='#0095e9', wa_dk='#006da8', wa_dp='#124e89', foam='#eff3eb', wa_lt='#2ce8f5',
    # stone
    st_hi='#c0cbdc', st_lt='#8e9ab4', st='#6c7c9d', st_md='#5a6988', st_dk='#3c4258', st_ol='#262b44', st_bk='#181425',
    # snow
    sn='#eff3eb', sn_md='#c0cbdc', sn_dk='#8b9bb4',
    # accents
    pk_hi='#fdd2ed', pk='#f389f5', pk_dk='#692a7e', yl='#fef09f', yl_dk='#feae34', red='#9e2835', red_dk='#7a1f2a',
    pu='#68386c', pu_lt='#b55088', pu_dk='#3e2731', lava='#f77622', lava_hi='#feae34', lava_dk='#e43b44', ash='#3a4466',
    ash_dk='#262b44', ash_bk='#181425', mesa='#be4a2f', mesa_lt='#d77643', mesa_dk='#733e39',
).items()}
CLEAR = (0, 0, 0, 0)
SHADOW = (9, 27, 21, 70)


class C:
    """tiny canvas helper"""
    def __init__(self, w, h):
        self.a = np.zeros((h, w, 4), np.uint8); self.w, self.h = w, h

    def px(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = P[c] if isinstance(c, str) else c

    def get(self, x, y):
        return self.a[y, x] if 0 <= x < self.w and 0 <= y < self.h else np.zeros(4, np.uint8)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.px(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c, only_empty=False):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1:
                    if not only_empty or self.get(x, y)[3] == 0:
                        self.px(x, y, c)

    def outline(self, c, diag=False):
        m = self.a[:, :, 3] == 255
        o = np.zeros_like(m)
        o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
        if diag:
            o[1:, 1:] |= m[:-1, :-1]; o[:-1, :-1] |= m[1:, 1:]; o[1:, :-1] |= m[:-1, 1:]; o[:-1, 1:] |= m[1:, :-1]
        o &= self.a[:, :, 3] == 0
        self.a[o] = P[c] if isinstance(c, str) else c

    def paste(self, o, ox, oy):
        src = o.a if isinstance(o, C) else o
        for y in range(src.shape[0]):
            for x in range(src.shape[1]):
                if src[y, x, 3] and 0 <= ox + x < self.w and 0 <= oy + y < self.h:
                    if src[y, x, 3] == 255 or self.a[oy + y, ox + x, 3] == 0:
                        self.a[oy + y, ox + x] = src[y, x]
                    else:
                        a = src[y, x, 3] / 255
                        self.a[oy + y, ox + x, :3] = (src[y, x, :3] * a + self.a[oy + y, ox + x, :3] * (1 - a)).astype(np.uint8)

    def img(self):
        return Image.fromarray(self.a, 'RGBA')


def save(c, rel):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = c.img() if isinstance(c, C) else c
    a = np.array(im); a[a[:, :, 3] == 0] = 0
    Image.fromarray(a, 'RGBA').save(path)
    return path


def sheet(frames, cw, ch, cols=None):
    cols = cols or len(frames)
    rows = (len(frames) + cols - 1) // cols
    s = C(cw * cols, ch * rows)
    for i, f in enumerate(frames):
        s.paste(f, (i % cols) * cw, (i // cols) * ch)
    return s


def h2(x, y, s=0):
    h = (int(x) * 374761393 + int(y) * 668265263 + s * 2654435761) & 0xffffffff
    h = ((h ^ (h >> 13)) * 1274126177) & 0xffffffff
    return ((h ^ (h >> 16)) & 0xffff) / 65535.0


# ============================================================== terrain ====
# every material renders the 16x16 centre tile of a 48x48 neighbourhood (see tiles.material)
ZIG = TL.periodic_hash(701)
TOOTH = np.array([[((X % 3) == 1) for X in range(48)] for _ in range(48)])    # grass-tooth comb, period 3


def blob(render, frames=1, variants=None):
    """47 rule tiles (+ optional extra centre variants appended after index 46)"""
    n = len(MASKS) + (len(variants) if variants else 0)
    rows = (n + 7) // 8
    outs = [C(T * 8, T * rows) for _ in range(frames)]
    for i, m in enumerate(MASKS):
        tiles = render(m)
        for f in range(frames):
            outs[f].paste(tiles[f], (i % 8) * T, (i // 8) * T)
    for k, v in enumerate(variants or []):
        i = len(MASKS) + k
        for f in range(frames):
            outs[f].paste(v[f] if isinstance(v, list) else v, (i % 8) * T, (i // 8) * T)
    return outs


def grass_tile(m, base='g', edge_dark='g_bk', shadow='s_sh', tufts=True):
    """grass over sand: toothed edge, dark rim line, cast shadow on the sand below/right"""
    mat = TL.material(m, 2.5, TL.periodic_noise(702, amp=1.3), round_r=3.5, spikes=1.6, spike_seed=703)
    Ein, Eout = TL.dist_to(~mat), TL.dist_to(mat)
    c = C(T, T)
    for y in range(T):
        for x in range(T):
            Y, X = y + 16, x + 16
            if mat[Y, X]:
                e = Ein[Y, X]
                col = base
                if e < 1.5: col = 'g_ol'
                elif e < 2.5 and TOOTH[Y, X]: col = 'g_dk'
                c.px(x, y, col)
            else:
                o = Eout[Y, X]
                # the grass is a few pixels higher than the sand: dark line + soft shadow under it
                above = Y > 0 and mat[Y - 1, X]
                if o < 1.2:
                    c.px(x, y, edge_dark if (above or TOOTH[Y, X]) else 'g_ol')
                elif o < 2.4 and mat[max(0, Y - 2), X]:
                    c.px(x, y, shadow)
    return [c]


def grass_variants():
    out = []
    for v in range(5):
        c = C(T, T); c.rect(0, 0, 15, 15, 'g')
        rnd = np.random.default_rng(900 + v)
        for k in range([2, 1, 3, 0, 2][v]):
            x, y = rnd.integers(1, 13), rnd.integers(2, 14)
            # little "v" tuft like the reference
            c.px(x, y, 'g_dk'); c.px(x + 2, y, 'g_dk'); c.px(x + 1, y + 1, 'g_dk2'); c.px(x, y - 1, 'g_md'); c.px(x + 2, y - 1, 'g_md')
        out.append(c)
    return out


def path_fill():
    out = []
    for v in range(4):
        c = C(T, T); c.rect(0, 0, 15, 15, 's')
        rnd = np.random.default_rng(950 + v)
        for k in range([0, 2, 3, 1][v]):
            x, y = rnd.integers(1, 14), rnd.integers(1, 14)
            c.px(x, y, 's_dk'); c.px(x + 1, y, 's_md')
            if k % 2: c.px(x, y - 1, 's_hi')
        out.append(c)
    return out


def forest_floor(m):
    """darker forest ground: big soft blobs, flat colour (same tone as the tree shadows of the reference)"""
    mat = TL.material(m, 2.5, TL.periodic_noise(710, amp=2.2), round_r=5.5)
    c = C(T, T)
    for y in range(T):
        for x in range(T):
            if mat[y + 16, x + 16]:
                c.px(x, y, 'g_dk')
    return [c]


def water_tile(m, kind='pond'):
    """pond/lake/river: thick brown bank with grass teeth hanging over it, dark rim, flat blue + ripples (4 frames)"""
    mat = TL.material(m, 1.5, TL.periodic_noise(720, amp=1.9), round_r=5.0)
    Ein = TL.dist_to(~mat)
    frames = []
    for f in range(4):
        c = C(T, T)
        for y in range(T):
            for x in range(T):
                Y, X = y + 16, x + 16
                if not mat[Y, X]: continue
                e = Ein[Y, X]
                if e < 1.5: col = 'g_ol' if TOOTH[Y, X] else 'w_ol'
                elif e < 2.5 and TOOTH[Y, X]: col = 'g'                      # grass blades over the bank
                elif e < 4.3: col = 'bank_lt' if (X * 3 + Y) % 5 else 'bank'
                elif e < 5.3: col = 'w_ol'
                elif e < 6.3: col = 'wa_dk'
                else: col = 'wa'
                c.px(x, y, col)
        for (rx, ry) in [(9, 7)]:
            for i in range(3):
                X = (rx + i + f) % 16 + 16; Y = ry + 16
                if mat[Y, X] and Ein[Y, X] > 6.5:
                    c.px(X - 16, ry, 'wa_dk')
        frames.append(c)
    return frames


def ocean_tile(m):
    """sea against a sandy beach: white foam line, turquoise shallows, deep blue"""
    mat = TL.material(m, 1.0, TL.periodic_noise(730, amp=1.6), round_r=4.0)
    Ein = TL.dist_to(~mat)
    frames = []
    for f in range(4):
        c = C(T, T)
        fo = [0, .5, 1, .5][f]
        for y in range(T):
            for x in range(T):
                Y, X = y + 16, x + 16
                if not mat[Y, X]: continue
                e = Ein[Y, X]
                if e < 1.5 + fo: col = 'foam'
                elif e < 2.5 + fo: col = 'wa_lt' if (X + f) % 5 == 0 else 'wa'
                elif e < 5.5: col = 'wa'
                elif e < 7.5: col = 'wa_dk'
                else: col = 'wa_dp'
                c.px(x, y, col)
        for (rx, ry) in [(11, 10)]:
            for i in range(2):
                X = (rx + i + f) % 16 + 16; Y = ry + 16
                if mat[Y, X] and Ein[Y, X] > 8: c.px(X - 16, ry, 'wa_dk')
        frames.append(c)
    return frames


FACE = 8


def cliff_tile(m, top='g', face=('w', 'w_dk', 'w_lt'), outline='w_ol', top_ol='g_ol', snow=False, top_edge='g_dk'):
    mat = TL.material(m, 1.2, TL.periodic_noise(740, amp=1.0), round_r=3.5)
    Ein = TL.dist_to(~mat)
    dd = np.full((48, 48), 99, np.float32)
    for x in range(48):
        k = 99
        for y in range(47, -1, -1):
            k = 0 if not mat[y, x] else k + 1
            dd[y, x] = k
    stri = TL.periodic_hash(741)
    c = C(T, T)
    f_main, f_dark, f_lit = face
    for y in range(T):
        for x in range(T):
            Y, X = y + 16, x + 16
            if not mat[Y, X]: continue
            k = dd[Y, X]
            if k <= FACE:
                if k <= 1 or Ein[Y, X] < 1.5: col = outline
                elif k == FACE: col = top_ol if not snow else 'sn_dk'
                elif k == FACE - 1 and TOOTH[Y, X]: col = top if not snow else 'sn_md'   # grass lip hanging over
                elif k <= 2: col = f_dark
                elif X % 4 == 0 or stri[Y, X] > .85: col = f_dark
                elif X % 4 == 1: col = f_lit
                else: col = f_main
            else:
                e = Ein[Y, X]
                if e < 1.5: col = top_ol if not snow else 'sn_dk'
                elif e < 2.5 and TOOTH[Y, X]: col = top_edge if not snow else 'sn_md'
                else: col = top if not snow else 'sn'
            c.px(x, y, col)
    return [c]


def cobble_tile(m):
    mat = TL.material(m, 1.5, TL.periodic_noise(750, amp=1.0), round_r=3.0)
    Ein = TL.dist_to(~mat)
    tone = ['st_lt', 'st', 'st_lt', 'st_md', 'st', 'st_lt', 'st', 'st_md']
    c = C(T, T)
    for y in range(T):
        for x in range(T):
            Y, X = y + 16, x + 16
            if not mat[Y, X]: continue
            if Ein[Y, X] < 1.5: col = 'st_ol'
            elif TL.VMORT[Y, X]: col = 'st_dk'
            else:
                col = tone[TL.VCID[Y, X]]
                if TL.VMORT[Y - 1, X]: col = 'st_hi'
            c.px(x, y, col)
    return [c]


def flat_overlay(m, fill, edge, outline, seed, noise_amp=1.4, speck=None, spikes=0.0):
    mat = TL.material(m, 2.0, TL.periodic_noise(seed, amp=noise_amp), round_r=3.5, spikes=spikes, spike_seed=seed + 1)
    Ein = TL.dist_to(~mat)
    hh = TL.periodic_hash(seed + 2)
    c = C(T, T)
    for y in range(T):
        for x in range(T):
            Y, X = y + 16, x + 16
            if not mat[Y, X]: continue
            e = Ein[Y, X]
            col = outline if e < 1.5 else edge if e < 2.5 else fill
            if speck and e >= 2.5 and hh[Y, X] < speck[1]: col = speck[0]
            c.px(x, y, col)
    return [c]


def lava_tile(m):
    mat = TL.material(m, 1.5, TL.periodic_noise(760, amp=1.2), round_r=3.5)
    Ein = TL.dist_to(~mat)
    hh = TL.periodic_hash(761)
    frames = []
    for f in range(4):
        c = C(T, T)
        for y in range(T):
            for x in range(T):
                Y, X = y + 16, x + 16
                if not mat[Y, X]: continue
                e = Ein[Y, X]
                if e < 1.5: col = 'ash_bk'
                elif e < 2.5: col = 'lava_dk'
                else:
                    v = (hh[Y, X] + f * 0.25) % 1
                    col = 'lava_hi' if v < .12 else 'lava' if v < .8 else 'lava_dk'
                c.px(x, y, col)
        frames.append(c)
    return frames


def swamp_tile(m):
    mat = TL.material(m, 1.5, TL.periodic_noise(770, amp=1.5), round_r=3.5)
    Ein = TL.dist_to(~mat)
    frames = []
    for f in range(4):
        c = C(T, T)
        for y in range(T):
            for x in range(T):
                Y, X = y + 16, x + 16
                if not mat[Y, X]: continue
                e = Ein[Y, X]
                col = 'w_ol' if e < 1.5 else 'g_bk' if e < 2.5 else 'g_ol' if e < 4 else 'g_dp2'
                c.px(x, y, col)
        for (rx, ry) in [(4, 5), (11, 11)]:
            for i in range(2):
                X = (rx + i + f) % 16 + 16
                if mat[ry + 16, X] and Ein[ry + 16, X] > 4: c.px(X - 16, ry, 'g_dp')
        frames.append(c)
    return frames


def farm_tile(m):
    mat = TL.material(m, 1.5, None, round_r=1.0)
    Ein = TL.dist_to(~mat)
    c = C(T, T)
    for y in range(T):
        for x in range(T):
            Y, X = y + 16, x + 16
            if not mat[Y, X]: continue
            if Ein[Y, X] < 1.5: col = 'w_ol'
            else:
                r = Y % 4
                col = 'w_dk' if r == 0 else 'w' if r in (1, 3) else 'w_lt'
                if r == 2 and X % 4 == 1: col = 'g_lt'       # sprouts
                if r == 1 and X % 4 == 1: col = 'g_md'
            c.px(x, y, col)
    return [c]


def build_terrain():
    made = []
    TS = 'Tilesets/'
    made.append(save(sheet(path_fill(), T, T), TS + 'world_sand_fill_16x16.png'))
    made.append(save(blob(grass_tile, variants=grass_variants())[0], TS + 'world_grass_blob_16x16.png'))
    made.append(save(blob(forest_floor)[0], TS + 'world_forestfloor_blob_16x16.png'))
    for f, s in enumerate(blob(water_tile, 4)):
        made.append(save(s, TS + f'world_water_blob_f{f}_16x16.png'))
    for f, s in enumerate(blob(ocean_tile, 4)):
        made.append(save(s, TS + f'world_ocean_blob_f{f}_16x16.png'))
    made.append(save(blob(cliff_tile)[0], TS + 'world_cliff_blob_16x16.png'))
    made.append(save(blob(lambda m: cliff_tile(m, face=('st', 'st_dk', 'st_lt'), outline='st_ol', snow=True))[0], TS + 'world_snowcliff_blob_16x16.png'))
    made.append(save(blob(cobble_tile)[0], TS + 'world_cobble_blob_16x16.png'))
    made.append(save(blob(lambda m: flat_overlay(m, 'sn', 'sn_md', 'sn_dk', 780, speck=('sn_md', .03)))[0], TS + 'world_snow_blob_16x16.png'))
    made.append(save(blob(lambda m: flat_overlay(m, 's_md', 's_dk', 's_sh', 790, speck=('s_hi', .03)))[0], TS + 'world_desert_blob_16x16.png'))
    made.append(save(blob(lambda m: flat_overlay(m, 'ash', 'ash_dk', 'ash_bk', 800, speck=('st_md', .04)))[0], TS + 'world_ash_blob_16x16.png'))
    made.append(save(blob(lambda m: flat_overlay(m, 'pu', 'pu_dk', 'ash_bk', 810, speck=('pu_lt', .03), spikes=1.5))[0], TS + 'world_corrupt_blob_16x16.png'))
    for f, s in enumerate(blob(lava_tile, 4)):
        made.append(save(s, TS + f'world_lava_blob_f{f}_16x16.png'))
    for f, s in enumerate(blob(swamp_tile, 4)):
        made.append(save(s, TS + f'world_swamp_blob_f{f}_16x16.png'))
    made.append(save(blob(farm_tile)[0], TS + 'world_farm_blob_16x16.png'))
    return made


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'ashcliff':
        print(save(blob(lambda m: cliff_tile(m, top='ash', face=('st_md', 'st_dk', 'st'), outline='ash_bk', top_ol='ash_bk', top_edge='ash_dk'))[0], 'Tilesets/world_ashcliff_blob_16x16.png'))
    elif len(sys.argv) > 1 and sys.argv[1] == 'waters':
        for f, s_ in enumerate(blob(water_tile, 4)): print(save(s_, f'Tilesets/world_water_blob_f{f}_16x16.png'))
        for f, s_ in enumerate(blob(ocean_tile, 4)): print(save(s_, f'Tilesets/world_ocean_blob_f{f}_16x16.png'))
    elif len(sys.argv) > 1 and sys.argv[1] == 'water':
        for f, s_ in enumerate(blob(water_tile, 4)): print(save(s_, f'Tilesets/world_water_blob_f{f}_16x16.png'))
        print(save(blob(forest_floor)[0], 'Tilesets/world_forestfloor_blob_16x16.png'))
    else:
        for p in build_terrain():
            print(p)
