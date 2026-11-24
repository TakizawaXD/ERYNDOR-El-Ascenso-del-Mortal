"""Dark-fantasy ground (2026-11-20): repaints the world ground in the style of the user's second reference.

Worn blue-grey flagstones on every road ('_') and town plaza ('p'), moss and vivid grass invading them in organic
patches (and growing in the joints), dark wet puddles, damp dark hollows in the grass and small glowing blue flowers.
The 10 regions keep their identity (valley, forests, lake, swamp, snowy peaks, red sands, ash mountain, citadel, port)
but with a darker, more atmospheric palette.

Reuses painter.Painter (fields, water, cliffs, bridges...) with a swapped palette and new materials.
Output: Assets/Art/World/Ground/ground_<cx>_<cy>.png (512 px chunks), ground_full_preview.png and the 240x160
world_map.png used by the map screen.
usage: python Tools/ArtGen2/painter_dark.py
"""
import os, sys, time
import numpy as np
from PIL import Image
from scipy import ndimage as nd

sys.path.insert(0, os.path.dirname(__file__))
import painter as PT                     # noqa: E402
from kit import P as BASE, hx            # noqa: E402

DARK = dict(BASE)
DARK.update({k: hx(v) for k, v in dict(
    # greens: deep and cold in the shade, vivid where moss catches the light
    g_hi='#8fd14c', g_lt='#6aae38', g_md='#3d702c', g='#28492a', g_dk='#1f3d26', g_dk2='#152d1f', g_ol='#10221a',
    g_dp='#1a4034', g_dp2='#132b28', g_bk='#0d1f20', g_ol2='#07140f', g_mo='#55922f',
    # earth / beach / wood
    s_hi='#a99f86', s='#857b69', s_md='#73695b', s_dk='#5a5248', s_sh='#48423b',
    w_lt='#86583f', w='#694130', w_dk='#4d2f28', w_ol='#281a20', bank='#433630', bank_lt='#5d4a3b', w_mid='#5f412f',
    # water: dark teal lake, navy sea
    wa='#215f7c', wa_dk='#194b66', wa_dp='#10324f', foam='#a8c3c6', wa_lt='#3f8aa0',
    # stone (flagstones, cliffs)
    st_hi='#939fb0', st_lt='#737f92', st='#5a6577', st_md='#4b5567', st_dk='#353c4b', st_ol='#232834', st_bk='#14161f',
    # snow, corruption, ash
    sn='#c4cfd9', sn_md='#9eabbc', sn_dk='#6c7a8f',
    pu='#3c2641', pu_lt='#62385b', pu_dk='#24172a', pk='#a04f9a', pk_hi='#d79ad0',
    ash='#30384f', ash_dk='#20243a', ash_bk='#121220',
    # red sands
    ds='#8f5541', ds_hi='#a86e56', ds_dk='#713f33', ds_sh='#58302a',
    # glowing flowers
    bl_hi='#d9f7ff', bl='#62cdfc', bl_dk='#2f72d6', wh='#e6ecdf',
).items()})
PT.P = DARK                              # painter.col() reads the module-level palette
col = PT.col
OUT = PT.OUT
ROOT = PT.ROOT
T = PT.T


def hsh(a, b, s=0):
    """cheap integer hash -> [0,1)"""
    h = (a.astype(np.int64) * 73856093) ^ (b.astype(np.int64) * 19349663) ^ (s * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    return ((h ^ (h >> 16)) & 0xFFFF).astype(np.float32) / 65536.0


class DarkPainter(PT.Painter):
    # ------------------------------------------------------------ helpers
    def mix(self, mask, rgb, k):
        c = np.array(rgb, np.float32)
        self.img[mask] = (self.img[mask].astype(np.float32) * (1 - k) + c * k).astype(np.uint8)

    def shade(self, mask, k):
        self.img[mask] = (self.img[mask].astype(np.float32) * k).astype(np.uint8)

    def dots(self, mask, pattern):
        """stamp a small pixel pattern [(dx, dy, colour)] at every True pixel of mask"""
        ys, xs = np.nonzero(mask)
        for dx, dy, c in pattern:
            yy, xx = ys + dy, xs + dx
            ok = (yy >= 0) & (yy < self.H) & (xx >= 0) & (xx < self.W)
            self.img[yy[ok], xx[ok]] = col(c)

    # ------------------------------------------------------------ materials
    def grass(self, mask, light='g', mid='g_md', dark='g_dk', seed=10):
        din = self.dist_in(mask)
        big, small, wn = self.noise(64, seed), self.noise(10, seed + 1), self.white(seed + 2)
        g = mask
        self.put(g, light)
        self.put(g & (big > 0.7) & (small > 0.5), mid)
        self.put(g & (big > 0.84) & (small > 0.68), 'g_mo')
        self.put(g & (big < 0.26) & (small > 0.5), dark)
        self.put(g & (big < 0.14) & (small > 0.62), 'g_dk2')
        # dense blade strokes: dark root, bright tip
        tuft = g & (wn > 0.988) & (din > 3)
        self.dots(tuft, ((0, 0, 'g_dk2'), (-1, -1, dark), (1, -1, dark), (-1, -2, mid), (1, -3, 'g_mo')))
        tips = g & (wn < 0.004) & (din > 3) & (big > 0.5)
        self.dots(tips, ((0, 0, 'g_dk'), (0, -1, 'g_mo'), (0, -2, 'g_hi')))
        # rim + blades + cast shadow (as before, darker)
        dout = self.dist_out(mask)
        rimn = self.noise(5, seed + 3)
        self.put(g & (din <= 1.0), 'g_ol')
        self.put((~g) & (dout <= 1.5) & (rimn > 0.55), 'g_dk')
        below = np.zeros_like(mask); below[3:] = mask[:-3]
        shadow = (~mask) & below & (dout > 1.5) & (dout <= 3.2)
        self.shade(shadow, 0.7)

    def damp(self, mask, seed=300):
        """dark wet hollows in the grass (slightly blue), with a few reflective specks"""
        n, n2 = self.noise(44, seed), self.noise(9, seed + 1)
        wet = mask & (n > 0.74) & (n2 > 0.35)
        self.shade(wet, 0.74)
        self.mix(wet, (20, 40, 60), 0.12)
        self.mix(mask & (n > 0.8) & (n2 > 0.55), (10, 25, 35), 0.25)

    def flowers(self, near, seed=310):
        """little glowing blue flowers (soft halo) and a few pale ones"""
        wn = self.white(seed)
        fl = near & (wn > 0.9972)
        ys, xs = np.nonzero(fl)
        for y, x in zip(ys, xs):                                   # halo first: lighten a 5x5 diamond
            y0, y1, x0, x1 = max(0, y - 2), min(self.H, y + 3), max(0, x - 2), min(self.W, x + 3)
            self.img[y0:y1, x0:x1] = (self.img[y0:y1, x0:x1].astype(np.float32) * 0.78 + np.array([30, 70, 90]) * 0.22 + 14).clip(0, 255).astype(np.uint8)
        self.dots(fl, ((0, 1, 'g_dk2'), (-1, 0, 'bl'), (1, 0, 'bl'), (0, -1, 'bl'), (0, 1, 'bl_dk'), (0, 0, 'bl_hi')))
        pale = near & (wn < 0.0009)
        self.dots(pale, ((0, 1, 'g_dk'), (0, 0, 'wh')))

    def flagstones(self, mask, lush, w_rng=(13, 21), h_rng=(9, 13), seed=200, moss=1.0):
        """worn blue-grey slabs, running bond with jittered rows, warped joints, moss and puddles"""
        H, W = self.H, self.W
        Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
        Yw = Y + (self.noise(18, seed) - 0.5) * 5.0
        Xw = X + (self.noise(18, seed + 1) - 0.5) * 5.0
        r = np.random.default_rng(seed)
        hts = r.integers(h_rng[0], h_rng[1] + 1, size=H // h_rng[0] + 8)
        bounds = np.concatenate([[-8], np.cumsum(hts) - 8]).astype(np.float32)
        ri = np.clip(np.searchsorted(bounds, Yw, side='right') - 1, 0, len(bounds) - 2)
        top, bot = bounds[ri], bounds[ri + 1]
        bw = r.integers(w_rng[0], w_rng[1] + 1, size=len(bounds)).astype(np.float32)[ri]
        off = (r.random(len(bounds)) * 40).astype(np.float32)[ri]
        u = Xw + off
        # every vertical joint is shifted by up to +-30% of the slab width -> irregular slab lengths
        ri64 = ri.astype(np.int64)
        J = lambda k: (hsh(ri64, k.astype(np.int64), seed + 21) - 0.5) * 0.6 * bw
        b0 = np.floor(u / bw)
        jl = b0 * bw + J(b0)
        bi = np.where(u < jl, b0 - 1, b0)
        jr = (bi + 1) * bw + J(bi + 1)
        bi = np.where(u >= jr, bi + 1, bi)
        left, right = bi * bw + J(bi), (bi + 1) * bw + J(bi + 1)
        del jl, jr, b0
        dt, db, dl, dr = Yw - top, bot - Yw, u - left, right - u
        sid_r, sid_c = ri.astype(np.int64), bi.astype(np.int64)
        tone = hsh(sid_r, sid_c, seed)
        del Y, X, Xw, Yw, u, left, right, bounds

        m = mask
        din = self.dist_in(m)
        mortar = (dt < 1.0) | (dl < 1.0)
        corner = (np.minimum(dt, db) < 2.6) & (np.minimum(dl, dr) < 2.6) & (hsh(sid_r, sid_c, seed + 7) > 0.45)
        slab = m & ~mortar
        self.put(m, 'st')
        self.put(slab & (tone < 0.25), 'st_md')
        self.put(slab & (tone > 0.72), 'st_lt')
        self.put(slab & (tone > 0.93), 'st_hi')
        # per-slab grain, bevel (lit top-left, dark bottom-right)
        grain = self.white(seed + 3)
        self.put(slab & (grain > 0.965), 'st_md')
        self.put(slab & (grain < 0.02), 'st_lt')
        self.put(slab & (dt < 2.0) & (tone >= 0.25), 'st_hi')
        self.put(slab & (dt < 2.0) & (tone < 0.25), 'st_lt')
        self.put(slab & (dl < 2.0) & (tone > 0.5), 'st_lt')
        self.put(slab & ((db < 1.0) | (dr < 1.0)), 'st_dk')
        cracks = slab & (np.abs(self.noise(11, seed + 4) - 0.5) < 0.012) & (hsh(sid_r, sid_c, seed + 9) > 0.55)
        self.put(cracks, 'st_ol')
        self.put(m & mortar, 'st_ol')
        self.put(m & corner & ~mortar, 'st_dk')
        # missing / sunken slabs filled with earth
        gone = m & ~mortar & (hsh(sid_r, sid_c, seed + 11) > 0.985)
        self.put(gone, 'g_dk2'); self.put(gone & (grain > 0.55), 'g_dk'); self.put(gone & (grain > 0.93), 'g_mo')

        # moss: in the joints, tinting slabs, and full organic patches (stronger near the edges)
        lushm = m & lush
        big, small = self.noise(26, seed + 5), self.noise(6, seed + 6)
        edge = 1.0 - np.clip(din / 12.0, 0, 1)
        score = (big * 0.72 + edge * 0.6 + small * 0.22) * moss
        self.put(lushm & mortar & (big + small * 0.3 > 0.45), 'g_dk')
        self.put(lushm & mortar & (big + small * 0.3 > 0.65), 'g_mo')
        tint = lushm & (score > 0.58) & (score <= 0.7)
        self.mix(tint & slab, DARK['g_md'][:3], 0.5)
        self.put(tint & mortar, 'g_lt')
        patch = lushm & (score > 0.7)
        wn = self.white(seed + 8)
        self.put(patch, 'g_md')
        self.put(patch & (small > 0.55), 'g_mo')
        self.put(patch & (small > 0.78), 'g_lt')
        self.put(patch & (small < 0.2), 'g')
        self.dots(patch & (wn > 0.975), ((0, 0, 'g_dk'), (0, -1, 'g_lt'), (-1, -1, 'g_mo'), (1, -2, 'g_hi')))
        pd = self.dist_in(patch)
        self.put(patch & (pd <= 1.0) & (small > 0.6), 'g_dk')
        # snow / sand dust in the joints where nothing grows
        self.put(m & ~lush & mortar & (big > 0.5), 'st_dk')

        # puddles: dark, bluish, reflective streaks, a dark rim
        pud = m & (self.noise(22, seed + 12) > 0.78) & (small > 0.25) & ~patch & (din > 2)
        pud = nd.binary_opening(pud, iterations=1)
        if pud.any():
            self.img[pud] = (self.img[pud].astype(np.float32) * 0.42 + np.array([14, 24, 38])).clip(0, 255).astype(np.uint8)
            pdin = self.dist_in(pud)
            self.shade(pud & (pdin <= 1.0), 0.75)
            refl = pud & (pdin > 2) & (self.white(seed + 13) > 0.985)
            ys, xs = np.nonzero(refl)
            for y, x in zip(ys, xs):
                self.img[y, max(0, x - 2):x + 2] = (110, 134, 160)
            self.dots(pud & (pdin > 1.5) & (self.white(seed + 14) > 0.9985), ((0, 0, 'bl_hi'),))

        # edges: dark outline, grass blades leaning over the stones, cast shadow from the bank above
        self.put(m & (din <= 1.0) & ~patch, 'st_ol')
        self.put(m & (din <= 1.0) & patch, 'g_dk')
        rimn = self.noise(5, seed + 15)
        self.put(lushm & (din > 1.0) & (din <= 2.6) & (rimn > 0.6), 'g_dk')
        self.put(lushm & (din > 1.0) & (din <= 1.8) & (rimn > 0.72), 'g_mo')
        above = np.zeros_like(m); above[3:] = ~m[:-3]
        self.shade(m & above & (din <= 3.5), 0.78)
        return patch

    def desert(self, mask):
        din = self.dist_in(mask)
        n = self.noise(48, 40)
        yy = np.arange(self.H)[:, None].astype(np.float32)
        dune = np.sin(yy / 9.0 + n * 9.0)
        self.put(mask, 'ds')
        self.put(mask & (dune > 0.86), 'ds_hi')
        self.put(mask & (dune < -0.9), 'ds_dk')
        self.put(mask & (self.white(41) > 0.998), 'ds_sh')
        self.put(mask & (din <= 1.0), 'ds_sh')

    # ------------------------------------------------------------ compose
    def paint(self):
        F = self.field
        self.sand()
        land_grass = F('.fwcCFsvn=HDk_p', 7, 0.12, 28, 1)
        self.grass(land_grass)
        forest = F('f', 9, 0.16, 30, 2) & land_grass
        self.flat(forest, 'g_dk', 'g_dk2', 'g_dp2', 'g_dk', 2, ('g_md', .006))
        self.damp(land_grass)
        self.flat(F('v', 8, 0.14, 26, 3), 'pu', 'pu_lt', 'pu_dk', 'ash_bk', 3, ('pk', .003))
        snow = F('nC', 8, 0.12, 26, 4)
        self.flat(snow, 'sn', 'sn_md', 'sn', 'sn_dk', 4, ('sn_md', .004))
        desert = F('d', 9, 0.12, 30, 5)
        self.desert(desert)
        ash = F('aLk', 8, 0.12, 26, 6)
        self.ash(ash)
        self.farm(F('F', 3, 0.04, 12, 7))
        lush = land_grass & ~snow & ~desert & ~ash
        roads = F('_', 4, 0.10, 14, 8) & ~F('p', 4, 0.06, 14, 8)
        plaza = F('p', 4, 0.06, 14, 8)
        self.flagstones(roads, lush, seed=200)
        self.flagstones(plaza, lush, w_rng=(16, 27), h_rng=(11, 15), seed=230, moss=0.85)
        dpath = self.dist_out(roads | plaza)
        near = lush & ~roads & ~plaza & (dpath < 22)
        vivid = near & (dpath < 9) & (self.noise(12, 330) + (9 - dpath) / 18 > 0.85)
        self.put(vivid, 'g_md'); self.put(vivid & (self.noise(5, 331) > 0.6), 'g_mo')
        self.put(vivid & (self.white(332) > 0.97), 'g_lt')
        self.flowers(near, 310)
        self.flowers(lush & ~roads & ~plaza & forest, 320)
        self.water(F('w=H', 6, 0.10, 20, 9))
        self.swamp(F('s', 6, 0.12, 18, 10))
        self.lava(F('L', 6, 0.12, 18, 11))
        self.ocean(F('OD', 8, 0.10, 32, 12))
        self.cliff(F('c', 5, 0.08, 16, 13))
        self.cliff(F('C', 5, 0.08, 16, 14), top='snow', face=('st', 'st_dk', 'st_lt', 'st_ol'))
        self.cliff(F('k', 5, 0.08, 16, 15), top='ash', face=('st_md', 'st_dk', 'st', 'ash_bk'))
        self.bridges()
        return self.img


def world_map(img, ent_rows, out):
    """240x160 map: one pixel per tile, brightened for the UI, trees as dark dots, walls/towers in red"""
    h, w = len(ent_rows), len(ent_rows[0])
    small = np.array(Image.fromarray(img).resize((w, h), Image.BOX)).astype(np.float32)
    small = (small * 1.25 + 8).clip(0, 255)
    for y, row in enumerate(ent_rows):
        for x, c in enumerate(row):
            if c in 'TUtAVuiIkY':
                small[y, x] *= 0.55
            elif c in '#9x0':
                small[y, x] = (158, 40, 53)
    Image.fromarray(small.astype(np.uint8)).save(out)


if __name__ == '__main__':
    t = time.time()
    path = os.path.join(ROOT, 'Assets', 'Game', 'Levels', 'World2.txt')
    lines = open(path, encoding='utf-8').read().splitlines()
    ter = PT.parse(path)
    if len(sys.argv) > 1 and sys.argv[1] == '--crop':          # quick look: --crop x0 y0 w h out.png (tiles)
        x0, y0, w, h = map(int, sys.argv[2:6])
        img = DarkPainter([r[x0:x0 + w] for r in ter[y0:y0 + h]]).paint()
        Image.fromarray(img).save(sys.argv[6]); print('crop', img.shape, round(time.time() - t, 1)); sys.exit()
    e0 = lines.index('ENTITIES')
    ents = lines[e0 + 1:e0 + 1 + len(ter)]
    p = DarkPainter(ter)
    img = p.paint()
    n = p.save_chunks()
    Image.fromarray(img).save(os.path.join(OUT, '..', 'ground_full_preview.png'))
    world_map(img, ents, os.path.join(OUT, '..', 'world_map.png'))
    print('chunks', n, 'size', img.shape, 'secs', round(time.time() - t, 1))
