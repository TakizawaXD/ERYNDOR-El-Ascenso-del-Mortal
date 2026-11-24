"""Terrain tilesets (16x16, 47-tile blob layout for Unity RuleTiles)."""
import json, os
import numpy as np
from lib import *

T = 16
N, NE, E, SE, S, SW, W, NW = 1, 2, 4, 8, 16, 32, 64, 128
DIRS = {N: (0, -1), NE: (1, -1), E: (1, 0), SE: (1, 1), S: (0, 1), SW: (-1, 1), W: (-1, 0), NW: (-1, -1)}


def canon(m):
    if not (m & N and m & E): m &= ~NE
    if not (m & S and m & E): m &= ~SE
    if not (m & S and m & W): m &= ~SW
    if not (m & N and m & W): m &= ~NW
    return m


MASKS = sorted({canon(m) for m in range(256)})
assert len(MASKS) == 47

YY, XX = np.mgrid[0:48, 0:48].astype(np.float32)
PTS = np.stack([XX.ravel() + .5, YY.ravel() + .5], 1)


def dist_to(setmask):
    """Euclidean distance (48x48) from every pixel centre to nearest pixel of setmask."""
    q = PTS[setmask.ravel()]
    if len(q) == 0:
        return np.full((48, 48), 99, np.float32)
    out = np.empty(48 * 48, np.float32)
    for i in range(0, 48 * 48, 576):
        d = PTS[i:i + 576, None, :] - q[None, :, :]
        out[i:i + 576] = np.sqrt((d ** 2).sum(-1)).min(1)
    return out.reshape(48, 48)


def occupancy(m):
    occ = np.zeros((48, 48), bool)
    occ[16:32, 16:32] = True
    for b, (dx, dy) in DIRS.items():
        if m & b:
            occ[16 + dy * 16:32 + dy * 16, 16 + dx * 16:32 + dx * 16] = True
    return occ


def periodic_noise(seed, freqs=((1, 0), (0, 1), (1, 1), (2, 1), (1, 2)), amp=1.0):
    r = rng(seed)
    n = np.zeros((48, 48), np.float32)
    for fx, fy in freqs:
        ph = r.uniform(0, 2 * np.pi)
        n += np.sin(2 * np.pi * (fx * XX + fy * YY) / T + ph)
    return n / len(freqs) * 2 * amp


def periodic_hash(seed):
    r = rng(seed).random((T, T)).astype(np.float32)
    return np.tile(r, (3, 3))


COLH = periodic_hash(901)[0]   # per-column / per-row hashes (periodic)
ROWH = periodic_hash(902)[:, 0]


def material(m, thresh=1.0, noise=None, round_r=2.5, spikes=0.0, spike_seed=903):
    occ = occupancy(m)
    D = dist_to(~occ)
    t = thresh + (noise if noise is not None else 0)
    core = D > t + round_r
    mat = dist_to(core) <= round_r + .01 if core.any() else core  # opening -> rounded convex corners
    if spikes:
        # grass-blade protrusions: vertical on horizontal edges, horizontal on vertical edges
        L = periodic_hash(spike_seed) * spikes
        col = COLH[None, :] > .55
        row = ROWH[:, None] > .55
        Eo = dist_to(mat)
        sp = (Eo <= L) & (col | row) & occ
        up = np.zeros_like(mat); up[1:] = mat[:-1]
        dn = np.zeros_like(mat); dn[:-1] = mat[1:]
        lf = np.zeros_like(mat); lf[:, 1:] = mat[:, :-1]
        rt = np.zeros_like(mat); rt[:, :-1] = mat[:, 1:]
        mat = mat | (sp & (up | dn | lf | rt | (Eo <= L)))
    return mat


def blob_sheet(render, name, frames=1):
    """render(mask)->list[Canvas16] per frame"""
    cols = 8
    outs = [Canvas(T * cols, T * 6) for _ in range(frames)]
    for i, m in enumerate(MASKS):
        tiles = render(m)
        for f in range(frames):
            outs[f].paste(tiles[f], (i % cols) * T, (i // cols) * T)
    return outs


# ---------------------------------------------------------------- grass ----
G_NOISE = periodic_noise(11, amp=1.6)
G_HASH = periodic_hash(12)
BLADE = periodic_hash(13)


def grass_like(m, base='g', blade=('g_md', 'g_dk'), outline='d_ol', crumbs=True, seed_off=0):
    mat = material(m, 3.0, G_NOISE, round_r=4.5, spikes=2.6)
    Ein = dist_to(~mat)
    Eout = dist_to(mat)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            Y, X = y + 16, x + 16
            h = G_HASH[Y, X]
            if mat[Y, X]:
                e = Ein[Y, X]
                bl = 1.5 + (2.2 if BLADE[Y, X] > .6 else 1.0 if BLADE[Y, X] > .3 else 0)
                if e < 1.5:
                    c.px(x, y, blade[1] if h < .5 else blade[0])
                elif e < bl:
                    c.px(x, y, blade[0])
                else:
                    c.px(x, y, base)
            else:
                o = Eout[Y, X]
                if o < 1.2 and outline:
                    c.px(x, y, outline)
                elif crumbs and o < 2.6 and h < .30:
                    c.px(x, y, 'd_cr')
                elif crumbs and o < 3.6 and h < .08:
                    c.px(x, y, 'd_pk')
    return [c]


def tallgrass(m):
    mat = material(m, 2.4, periodic_noise(23, amp=1.4), round_r=4.0, spikes=3.6, spike_seed=21)
    Ein = dist_to(~mat)
    hh = periodic_hash(24)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            Y, X = y + 16, x + 16
            if mat[Y, X]:
                col = 'g_md'
                if Ein[Y, X] > 2.5 and hh[Y, X] < .06:
                    col = 'g_dk'  # sparse inner blade strokes like the woods pack
                c.px(x, y, col)
    return [c]


# ---------------------------------------------------------------- water ----
def water(m):
    """Water body over land: bank -> foam -> deep band -> water.  4 animation frames."""
    mat = material(m, 1.5, periodic_noise(31, amp=1.3), round_r=4.5)
    Ein = dist_to(~mat)
    rip = periodic_hash(32)
    frames = []
    for f in range(4):
        c = Canvas(T, T)
        foam_shift = [0, .35, .6, .35][f]
        for y in range(T):
            for x in range(T):
                Y, X = y + 16, x + 16
                if not mat[Y, X]:
                    continue
                e = Ein[Y, X]
                if e < 1.5:
                    col = 'd_ol'
                elif e < 3.0:
                    col = 'd_br' if (x + y) % 5 else 'd_dk'
                elif e < 3.6:
                    col = 'd_dk2'
                elif e < 4.6 + foam_shift:
                    col = 'w_lt' if rip[Y, X] > .12 else 'w_fo'
                elif e < 6.6:
                    col = 'w_dk'
                elif e < 7.6:
                    col = 'w_md'
                else:
                    col = 'w'
                c.px(x, y, col)
        # ripple dashes (periodic -> seamless), grow & fade over 4 frames
        for k, (rx, ry) in enumerate([(3, 4), (10, 11), (12, 2)]):
            ph = (f + k) % 4
            ln = [1, 3, 3, 0][ph]
            colr = 'w_lt' if ph < 2 else 'w_fo'
            for i in range(ln):
                X, Y = (rx + i - ln // 2) % T + 16, ry + 16
                if mat[Y, X] and Ein[Y, X] > 7.6:
                    c.px(X - 16, ry, colr)
        frames.append(c)
    return frames


# ---------------------------------------------------------------- cliff ----
FACE = 11


def cliff(m):
    mat = material(m, 1.2, periodic_noise(41, amp=1.0), round_r=4.0)
    Ein = dist_to(~mat)
    # downward distance to non-mat
    dd = np.full((48, 48), 99, np.float32)
    for x in range(48):
        nxt = 99
        for y in range(47, -1, -1):
            if not mat[y, x]:
                nxt = 0
            else:
                nxt = nxt + 1
            dd[y, x] = nxt
    face = mat & (dd <= FACE)
    side = mat & ~face & (Ein < 3.5)
    top = mat & ~face & ~side
    E2 = dist_to(~top)
    stripes = periodic_hash(42)
    blade = periodic_hash(43)
    c = Canvas(T, T)
    for y in range(T):
        for x in range(T):
            Y, X = y + 16, x + 16
            if not mat[Y, X]:
                continue
            if face[Y, X]:
                k = dd[Y, X]
                if k <= 1 or Ein[Y, X] < 1.5:
                    col = 'd_ol'
                elif k >= FACE:
                    col = 'd_ol'
                else:
                    seam = stripes[Y, X % 48] > .78 or (X % 6 == 0 and stripes[Y, X] > .3)
                    if k <= 3:
                        col = 'd_dk2'
                    elif seam:
                        col = 'd_dk'
                    elif k >= FACE - 2:
                        col = 'd_rd'
                    else:
                        col = 'd_br'
                    if k == 6 and stripes[Y, X] > .5:  # horizontal strata
                        col = 'd_dk'
                    if k == FACE - 1 and blade[Y, X] > .45 or k == FACE - 2 and blade[Y, X] > .8:
                        col = 'g_md'  # grass lip hanging over the face
            elif side[Y, X]:
                col = 'd_ol' if Ein[Y, X] < 1.5 else ('d_dk' if Ein[Y, X] < 2.5 else 'd_br')
            else:
                e = E2[Y, X]
                bl = 1.5 + (2.0 if blade[Y, X] > .55 else 1.0 if blade[Y, X] > .3 else 0)
                col = 'g_ol' if e < 1.5 else ('g_md' if e < bl else 'g')
            c.px(x, y, col)
    return [c]


# --------------------------------------------------------------- cobble ----
def _voronoi():
    r = rng(51)
    seeds = [(1.5, 2), (8, 1.5), (13.5, 5), (4, 8), (10, 9), (2, 13.5), (7.5, 14), (14, 12.5)]
    seeds = [(sx + r.uniform(-.7, .7), sy + r.uniform(-.7, .7)) for sx, sy in seeds]
    cid = np.zeros((48, 48), int)
    mort = np.zeros((48, 48), bool)
    for Y in range(48):
        for X in range(48):
            x, y = X % T + .5, Y % T + .5
            ds = []
            for i, (sx, sy) in enumerate(seeds):
                for ox in (-T, 0, T):
                    for oy in (-T, 0, T):
                        ds.append((((x - sx - ox) ** 2 + (y - sy - oy) ** 2) ** .5, i))
            ds.sort()
            cid[Y, X] = ds[0][1]
            mort[Y, X] = ds[1][0] - ds[0][0] < 1.1
    return cid, mort


VCID, VMORT = _voronoi()


def cobble(m):
    mat = material(m, 1.5, periodic_noise(52, amp=1.0), round_r=3.5)
    Ein = dist_to(~mat)
    c = Canvas(T, T)
    tone = ['s_lt', 's', 's_lt', 's_wm', 's', 's_lt', 's', 's_wm']
    for y in range(T):
        for x in range(T):
            Y, X = y + 16, x + 16
            if not mat[Y, X]:
                continue
            if Ein[Y, X] < 1.5:
                col = 's_dk2'
            elif VMORT[Y, X]:
                col = 's_dk'
            else:
                col = tone[VCID[Y, X]]
                if VMORT[Y - 1, X] and not VMORT[Y, X]:
                    col = 's_hi'
                elif VMORT[Y + 1, X]:
                    col = 's_md'
            c.px(x, y, col)
    return [c]


# ---------------------------------------------------------------- fills ----
def fills():
    out = {}
    # grass fill variants (base identical to blob centre so they mix freely)
    gs = []
    for v in range(4):
        c = Canvas(T, T); c.rect(0, 0, 15, 15, 'g')
        r = rng(100 + v)
        if v == 1:
            for (x, y) in [(4, 5), (10, 11)]:
                c.sprite(['.a.a', 'a.ab', '.bb.'], {'a': 'g_md', 'b': 'g_dk'}, x, y)
        if v == 2:
            c.sprite(['..a..', 'a.a.a', '.aba.', '..b..'], {'a': 'g_md', 'b': 'g_dk'}, 6, 6)
            c.px(2, 12, 'g_lt'); c.px(13, 3, 'g_lt')
        if v == 3:
            for i in range(5):
                c.px(r.integers(1, 15), r.integers(1, 15), 'g_lt2')
            c.sprite(['.a.', 'aya', '.a.'], {'a': 'wht', 'y': 'y'}, 10, 4)
            c.sprite(['a.', '.b'], {'a': 'g_md', 'b': 'g_dk'}, 3, 10)
        gs.append(c)
    out['Terrain/terrain_grass_fill_16x16.png'] = sheet(gs, T, T)
    # dirt fill variants
    ds = []
    for v in range(4):
        c = Canvas(T, T); c.rect(0, 0, 15, 15, 'd')
        r = rng(200 + v)
        n = [0, 4, 7, 3][v]
        for i in range(n):
            x, y = r.integers(1, 14), r.integers(1, 14)
            c.px(x, y, 'd_md'); c.px(x + 1, y, 'd_md2') if i % 2 else None
            if i % 3 == 0: c.px(x, y - 1, 'd_hi')
        if v == 3:
            c.sprite(['.ab.', 'abbc', '.cc.'], {'a': 'd_hi', 'b': 'd_md', 'c': 'd_md2'}, 6, 6)
        ds.append(c)
    out['Terrain/terrain_dirt_fill_16x16.png'] = sheet(ds, T, T)
    # deep water fill (frames) = same as the blob centre of water
    return out


def build():
    os.makedirs(ROOT, exist_ok=True)
    made = []
    made.append(save(blob_sheet(grass_like, 'grass')[0], 'Tilesets/Grass/tileset_grass_blob47_16x16.png'))
    made.append(save(blob_sheet(tallgrass, 'tall')[0], 'Tilesets/TallGrass/tileset_tallgrass_blob47_16x16.png'))
    made.append(save(blob_sheet(cliff, 'cliff')[0], 'Tilesets/Cliff/tileset_cliff_blob47_16x16.png'))
    made.append(save(blob_sheet(cobble, 'cobble')[0], 'Tilesets/StonePath/tileset_stonepath_blob47_16x16.png'))
    for f, cnv in enumerate(blob_sheet(water, 'water', 4)):
        made.append(save(cnv, f'Tilesets/Water/tileset_water_blob47_f{f}_16x16.png'))
    for rel, cnv in fills().items():
        made.append(save(cnv, 'Environments/' + rel))
    with open(os.path.join(ROOT, 'Tilesets', 'blob47_masks.json'), 'w') as fh:
        json.dump({'bits': 'N=1,NE=2,E=4,SE=8,S=16,SW=32,W=64,NW=128 (Y-up: N is +Y)',
                   'columns': 8, 'masks': MASKS}, fh)
    return made


if __name__ == '__main__':
    for p in build():
        print(p)
