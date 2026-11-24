"""Paints the whole world ground as one smooth pixel-art image (no tile staircases).

Every material comes from a continuous field: tile masks are upsampled, blurred and perturbed with
fractal noise, then thresholded at pixel resolution -> smooth organic shorelines, paths and biome edges.
Edges get pixel-precise outlines, banks, foam, cliff faces and cast shadows (distance transforms).
Output: Assets/Art/World/Ground/ground_<cx>_<cy>.png chunks (512 px) + a full preview.
"""
import os, sys, math
import numpy as np
from PIL import Image
from scipy import ndimage as nd

sys.path.insert(0, os.path.dirname(__file__))
from kit import P   # palette (sampled from the reference)

T = 16
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'Assets', 'Art', 'World', 'Ground')
CHUNK = 512


def col(name):
    return np.array(P[name][:3], np.uint8)


def parse(path):
    lines = open(path, encoding='utf-8').read().splitlines()
    t0, e0 = lines.index('TERRAIN'), lines.index('ENTITIES')
    return [l for l in lines[t0 + 1:e0]]


class Painter:
    def __init__(self, terrain, seed=1):
        self.ter = terrain
        self.h, self.w = len(terrain), len(terrain[0])
        self.H, self.W = self.h * T, self.w * T
        self.img = np.zeros((self.H, self.W, 3), np.uint8)
        self.rng = np.random.default_rng(seed)
        self._noise = {}

    # ------------------------------------------------------------ noise
    def noise(self, scale, seed):
        """fractal value noise in [0,1] at pixel resolution (cached)"""
        key = (scale, seed)
        if key in self._noise: return self._noise[key]
        r = np.random.default_rng(seed)
        acc = np.zeros((self.H, self.W), np.float32); amp = 1.0; tot = 0
        s = scale
        for _ in range(4):
            gh, gw = int(self.H / s) + 3, int(self.W / s) + 3
            g = r.random((gh, gw)).astype(np.float32)
            up = nd.zoom(g, s, order=3, mode='wrap')[:self.H, :self.W]
            acc += up * amp; tot += amp
            amp *= 0.5; s = max(2, s / 2)
        n = acc / tot
        n = (n - n.min()) / (n.max() - n.min() + 1e-6)
        self._noise[key] = n
        return n

    def white(self, seed):
        return np.random.default_rng(seed).random((self.H, self.W)).astype(np.float32)

    # ------------------------------------------------------------ fields
    def field(self, chars, blur=6.0, wob=0.13, wob_scale=24, seed=0):
        tm = np.array([[1.0 if c in chars else 0.0 for c in row] for row in self.ter], np.float32)
        tm = np.pad(tm, 2, mode='edge')
        up = nd.zoom(tm, T, order=1)[2 * T:-2 * T, 2 * T:-2 * T]
        up = nd.gaussian_filter(up, blur)
        up += (self.noise(wob_scale, 900 + seed) - 0.5) * 2 * wob
        return up > 0.5

    @staticmethod
    def dist_in(mask):
        return nd.distance_transform_edt(mask)

    @staticmethod
    def dist_out(mask):
        return nd.distance_transform_edt(~mask)

    def put(self, mask, name):
        self.img[mask] = col(name)

    # ------------------------------------------------------------ materials
    def sand(self):
        n1, n2, wn = self.noise(40, 1), self.noise(6, 2), self.white(3)
        self.img[:] = col('s')
        self.put((n1 > 0.62) & (n2 > 0.45), 's_md')
        self.put((n1 < 0.3) & (n2 > 0.6), 's_hi')
        peb = wn > 0.9985
        peb |= np.roll(peb, 1, 1)
        self.put(peb, 's_dk')
        self.put(np.roll(peb, 1, 0) & ~peb, 's_sh')

    def grass(self, mask, light='g', mid='g_md', dark='g_dk', seed=10):
        din = self.dist_in(mask)
        big, small, wn = self.noise(64, seed), self.noise(10, seed + 1), self.white(seed + 2)
        g = mask
        self.put(g, light)
        self.put(g & (big > 0.74) & (small > 0.55), mid if mid != light else light)
        self.put(g & (big < 0.2) & (small > 0.55), dark)
        # little "v" tufts and tiny flowers
        tuft = g & (wn > 0.9955) & (din > 4)
        ys, xs = np.nonzero(tuft)
        for y, x in zip(ys, xs):
            for dx, dy, c in ((0, 0, 'g_dk2'), (-1, -1, 'g_dk'), (1, -1, 'g_dk'), (-2, -2, 'g_md'), (2, -2, 'g_md')):
                if 0 <= y + dy < self.H and 0 <= x + dx < self.W: self.img[y + dy, x + dx] = col(c)
        fl = g & (wn < 0.0007) & (din > 5)
        for y, x in zip(*np.nonzero(fl)):
            c = ['pk_hi', 'yl', 'sn', 'pk'][(x + y) % 4]
            self.img[y, x] = col(c)
            if y + 1 < self.H: self.img[y + 1, x] = col('g_dk')
        # rim: thin dark line + soft blades, and a cast shadow on whatever is below the grass
        dout = self.dist_out(mask)
        rimn = self.noise(5, seed + 3)
        self.put(g & (din <= 1.0), 'g_ol')
        blades = (~g) & (dout <= 1.5) & (rimn > 0.55)
        self.put(blades, 'g_dk')
        below = np.zeros_like(mask); below[3:] = mask[:-3]
        shadow = (~mask) & below & (dout > 1.5) & (dout <= 3.2)
        self.img[shadow] = (self.img[shadow].astype(np.int16) * 0.78).astype(np.uint8)

    def flat(self, mask, base, alt, alt2, outline, seed, speck=None):
        din = self.dist_in(mask)
        n1, n2, wn = self.noise(36, seed), self.noise(8, seed + 1), self.white(seed + 2)
        self.put(mask, base)
        self.put(mask & (n1 > 0.72) & (n2 > 0.5), alt)
        self.put(mask & (n1 < 0.22) & (n2 > 0.55), alt2)
        if speck: self.put(mask & (wn > 1 - speck[1]) & (din > 3), speck[0])
        self.put(mask & (din <= 1.0), outline)

    def desert(self, mask):
        din = self.dist_in(mask)
        n = self.noise(48, 40)
        yy = np.arange(self.H)[:, None].astype(np.float32)
        dune = np.sin(yy / 9.0 + n * 9.0)
        self.put(mask, 's_md')
        self.put(mask & (dune > 0.86), 's_hi')
        self.put(mask & (dune < -0.9), 's_dk')
        self.put(mask & (self.white(41) > 0.998), 's_sh')
        self.put(mask & (din <= 1.0), 's_sh')

    def ash(self, mask):
        din = self.dist_in(mask)
        n = self.noise(40, 50)
        cracks = np.abs(n - 0.5) < 0.006
        self.put(mask, 'ash')
        self.put(mask & (self.noise(48, 51) > 0.65), 'ash_dk')
        self.put(mask & cracks, 'ash_bk')
        self.put(mask & (self.white(52) > 0.996), 'st_md')
        self.put(mask & (din <= 1.0), 'ash_bk')

    def lava(self, mask):
        din = self.dist_in(mask)
        n, n2 = self.noise(14, 60), self.noise(5, 61)
        self.put(mask, 'lava')
        self.put(mask & (n > 0.6), 'lava_hi')
        self.put(mask & (n2 > 0.72) & (n < 0.45), 'lava_dk')
        crust = np.abs(self.noise(22, 62) - 0.5) < 0.02
        self.put(mask & crust & (din > 3), 'mesa_dk')
        self.put(mask & (din <= 2.0), 'lava_dk')
        self.put(mask & (din <= 1.0), 'ash_bk')

    def water(self, mask, deep_d=30, seed=70):
        """fresh water: brown bank with grass blades over it, dark rim, two depth tones, sparkles"""
        din = self.dist_in(mask)
        n = self.noise(9, seed)
        self.put(mask, 'wa')
        dz = deep_d + (self.noise(40, seed + 5) - .5) * 24
        Y, X = np.mgrid[0:self.H, 0:self.W]
        checker = ((X + Y) % 2) == 0
        # fresh water stays one clear blue, like the reference (no depth rings)
        bank = mask & (din <= 4.0 + (n - .5) * 1.5)
        self.put(bank, 'bank_lt')
        self.put(bank & (self.noise(4, seed + 1) > 0.6), 'bank')
        self.put(mask & (din <= 1.0), 'w_ol')
        rim = mask & (din > 4.0 + (n - .5) * 1.5) & (din <= 5.2 + (n - .5) * 1.5)
        self.put(rim, 'w_ol')
        self.put(mask & (din > 5.2 + (n - .5) * 1.5) & (din <= 6.2 + (n - .5) * 1.5), 'wa_dk')
        # ripples: short horizontal dashes that follow a slow noise, plus sparkles
        wn = self.white(seed + 2)
        rip = mask & (din > 9) & (wn > 0.9975)
        for y, x in zip(*np.nonzero(rip)):
            self.img[y, max(0, x - 2):x + 2] = col('wa_dk')
        sp = mask & (din > 7) & (wn < 0.0006)
        for y, x in zip(*np.nonzero(sp)):
            self.img[y, x] = col('foam'); self.img[y, max(0, x - 1):x + 2][[0, -1]] = col('wa_lt')

    def ocean(self, mask):
        din = self.dist_in(mask)
        n = self.noise(14, 80)
        self.put(mask, 'wa')
        Y, X = np.mgrid[0:self.H, 0:self.W]
        chk = ((X + Y) % 2) == 0
        n2 = self.noise(60, 83)
        d1, d2 = 16 + n2 * 24, 48 + n2 * 30
        self.put(mask & (din > d1 + 4), 'wa_dk'); self.put(mask & (din > d1) & (din <= d1 + 4) & chk, 'wa_dk')
        self.put(mask & (din > d2 + 4), 'wa_dp'); self.put(mask & (din > d2) & (din <= d2 + 4) & chk, 'wa_dp')
        self.put(mask & (din <= 5 + n * 3), 'wa_lt')
        self.put(mask & (din <= 2.2 + n * 1.5), 'foam')
        # second foam line a bit offshore
        self.put(mask & (np.abs(din - (8 + n * 4)) < 0.6) & (self.noise(6, 81) > 0.5), 'foam')
        wn = self.white(82)
        for y, x in zip(*np.nonzero(mask & (din > 14) & (wn > 0.998))):
            self.img[y, max(0, x - 3):x + 3] = col('wa' if din[y, x] > 34 else 'wa_lt')

    def swamp(self, mask):
        din = self.dist_in(mask)
        n = self.noise(10, 90)
        self.put(mask, 'g_dp2')
        self.put(mask & (n > 0.62), 'g_bk')
        self.put(mask & (self.noise(4, 91) > 0.78) & (din > 3), 'g_dp')      # algae
        self.put(mask & (din <= 3.0), 'bank')
        self.put(mask & (din <= 1.0), 'w_ol')
        self.put(mask & (din > 3) & (din <= 4.2), 'w_ol')

    def farm(self, mask):
        din = self.dist_in(mask)
        yy = (np.arange(self.H)[:, None] % 6)
        xx = np.arange(self.W)[None, :]
        self.put(mask, 'w')
        self.put(mask & (yy == 0), 'w_dk'); self.put(mask & (yy == 3), 'w_lt')
        sprout = mask & (yy == 2) & ((xx % 5) == 2)
        self.put(sprout, 'g_lt'); self.put(np.roll(sprout, 1, 0) & mask, 'g_md')
        self.put(mask & (din <= 1.5), 'w_ol')

    def cobble(self, mask):
        din = self.dist_in(mask)
        # jittered-grid voronoi stones (~7 px)
        S = 7
        gy, gx = self.H // S + 2, self.W // S + 2
        r = np.random.default_rng(100)
        jy, jx = r.random((gy, gx)) * S, r.random((gy, gx)) * S
        Y, X = np.mgrid[0:self.H, 0:self.W]
        cy, cx = Y // S, X // S
        best = np.full((self.H, self.W), 1e9, np.float32); second = best.copy(); idx = np.zeros((self.H, self.W), np.int32)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny, nx = np.clip(cy + dy, 0, gy - 1), np.clip(cx + dx, 0, gx - 1)
                sy, sx = ny * S + jy[ny, nx], nx * S + jx[ny, nx]
                d = (Y - sy) ** 2 + (X - sx) ** 2
                upd = d < best
                second = np.where(upd, best, np.minimum(second, d))
                idx = np.where(upd, ny * gx + nx, idx)
                best = np.where(upd, d, best)
        mortar = (np.sqrt(second) - np.sqrt(best)) < 1.2
        tone = (idx * 2654435761 % 7)
        self.put(mask, 'st')
        self.put(mask & (tone < 2), 'st_lt'); self.put(mask & (tone == 6), 'st_md')
        top = mask & ~mortar & np.roll(mortar, 1, 0)
        self.put(top, 'st_hi')
        self.put(mask & mortar, 'st_dk')
        self.put(mask & (din <= 1.0), 'st_ol')

    def cliff(self, mask, top='grass', face=('w', 'w_dk', 'w_lt', 'w_ol'), height=10, seed=110):
        """raised plateau: face where the ground drops, lip, outline, cast shadow below"""
        f_main, f_dark, f_lit, f_ol = face
        drop = np.zeros_like(mask)
        for k in range(1, height + 1):
            sh = np.zeros_like(mask); sh[:-k] = mask[k:]
            drop |= mask & ~sh                     # within `height` px above the lower edge
        topm = mask & ~drop
        if top == 'grass': self.grass(topm, seed=seed)
        elif top == 'snow': self.flat(topm, 'sn', 'sn_md', 'sn', 'sn_dk', seed, ('sn_md', .004))
        else: self.ash(topm)
        n = self.noise(6, seed + 1)
        xx = np.arange(self.W)[None, :]
        strata = (xx + (n * 6).astype(int)) % 7
        self.put(drop, f_main)
        self.put(drop & (strata == 0), f_dark)
        self.put(drop & (strata == 1), f_lit)
        self.put(drop & (n > 0.7), f_dark)
        # lip and outlines
        lip = drop & ~np.roll(drop, 1, 0)
        self.put(lip, f_ol)
        bottom = drop & ~np.roll(drop, -1, 0)
        self.put(bottom, f_ol)
        din = self.dist_in(mask)
        self.put(mask & (din <= 1.0) & ~topm, f_ol)
        # shadow on the ground below the face
        below = np.zeros_like(mask)
        for k in range(1, 6):
            sh = np.zeros_like(mask); sh[k:] = mask[:-k]; below |= sh
        below &= ~mask
        self.img[below] = (self.img[below].astype(np.int16) * 0.72).astype(np.uint8)

    def bridges(self):
        """bridges and docks painted as single continuous decks (rails on the outer edges only)"""
        h, w = self.h, self.w
        seen = set()
        for y in range(h):
            for x in range(w):
                c = self.ter[y][x]
                if c not in '=HD' or (x, y) in seen: continue
                comp = []; st = [(x, y)]; seen.add((x, y))
                while st:
                    a, b = st.pop(); comp.append((a, b))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        n = (a + dx, b + dy)
                        if 0 <= n[0] < w and 0 <= n[1] < h and n not in seen and self.ter[n[1]][n[0]] == c:
                            seen.add(n); st.append(n)
                xs = [p[0] for p in comp]; ys = [p[1] for p in comp]
                X0, X1, Y0, Y1 = min(xs) * T, (max(xs) + 1) * T, min(ys) * T, (max(ys) + 1) * T
                horiz = c == '=' or (c == 'D' and (X1 - X0) >= (Y1 - Y0))
                img = self.img
                if horiz:
                    y0, y1 = Y0 + 3, Y1 - 3
                    for xx in range(X0, X1):
                        k = (xx - X0) % 5
                        img[y0:y1, xx] = col('w_lt' if k == 0 else 'w' if k < 3 else 'w_mid' if k == 3 else 'w_dk')
                    img[y0:y0 + 2, X0:X1] = col('w_dk'); img[y0, X0:X1] = col('w_lt')
                    img[y1 - 2:y1, X0:X1] = col('w_dk'); img[y1 - 1, X0:X1] = col('w_ol')
                    img[y1:y1 + 2, X0:X1] = (img[y1:y1 + 2, X0:X1].astype(np.int16) * 0.7).astype(np.uint8)
                    for px in list(range(X0, X1 - 3, 24)) + [X1 - 4]:
                        img[y0 - 2:y0 + 3, px:px + 4] = col('w'); img[y0 - 2, px:px + 4] = col('s')
                        img[y1 - 3:y1 + 1, px:px + 4] = col('w_dk')
                else:
                    x0, x1 = X0 + 3, X1 - 3
                    for yy in range(Y0, Y1):
                        k = (yy - Y0) % 5
                        img[yy, x0:x1] = col('w_lt' if k == 0 else 'w' if k < 3 else 'w_mid' if k == 3 else 'w_dk')
                    img[Y0:Y1, x0:x0 + 2] = col('w_dk'); img[Y0:Y1, x0] = col('w_ol')
                    img[Y0:Y1, x1 - 2:x1] = col('w_dk'); img[Y0:Y1, x1 - 1] = col('w_ol')
                    img[Y0:Y1, x1:x1 + 2] = (img[Y0:Y1, x1:x1 + 2].astype(np.int16) * 0.7).astype(np.uint8)
                    for py in list(range(Y0, Y1 - 3, 24)) + [Y1 - 4]:
                        img[py:py + 4, x0 - 2:x0 + 2] = col('w'); img[py, x0 - 2:x0 + 2] = col('s')
                        img[py:py + 4, x1 - 2:x1 + 2] = col('w'); img[py, x1 - 2:x1 + 2] = col('s')

    # ------------------------------------------------------------ compose
    def paint(self):
        F = self.field
        self.sand()
        land_grass = F('.fwcCFsvn=HDk', 7, 0.12, 28, 1)
        self.grass(land_grass)
        self.flat(F('f', 9, 0.16, 30, 2) & land_grass, 'g_dk', 'g_dk2', 'g_dk', 'g_dk', 2)
        self.flat(F('v', 8, 0.14, 26, 3), 'pu', 'pu_lt', 'pu_dk', 'ash_bk', 3, ('pk', .003))
        self.flat(F('nC', 8, 0.12, 26, 4), 'sn', 'sn_md', 'sn', 'sn_dk', 4, ('sn_md', .004))
        self.desert(F('d', 9, 0.12, 30, 5))
        self.ash(F('aLk', 8, 0.12, 26, 6))
        self.farm(F('F', 3, 0.04, 12, 7))
        self.cobble(F('p', 4, 0.06, 14, 8))
        self.water(F('w=H', 6, 0.10, 20, 9))
        self.swamp(F('s', 6, 0.12, 18, 10))
        self.lava(F('L', 6, 0.12, 18, 11))
        self.ocean(F('OD', 8, 0.10, 32, 12))
        self.cliff(F('c', 5, 0.08, 16, 13))
        self.cliff(F('C', 5, 0.08, 16, 14), top='snow', face=('st', 'st_dk', 'st_lt', 'st_ol'))
        self.cliff(F('k', 5, 0.08, 16, 15), top='ash', face=('st_md', 'st_dk', 'st', 'ash_bk'))
        self.bridges()
        return self.img

    def save_chunks(self):
        os.makedirs(OUT, exist_ok=True)
        n = 0
        for cy in range(0, self.H, CHUNK):
            for cx in range(0, self.W, CHUNK):
                Image.fromarray(self.img[cy:cy + CHUNK, cx:cx + CHUNK]).save(os.path.join(OUT, f'ground_{cx // CHUNK}_{cy // CHUNK}.png'))
                n += 1
        return n


if __name__ == '__main__':
    import time
    t = time.time()
    ter = parse(os.path.join(ROOT, 'Assets', 'Game', 'Levels', 'World2.txt'))
    p = Painter(ter)
    img = p.paint()
    n = p.save_chunks()
    Image.fromarray(img).save(os.path.join(OUT, '..', 'ground_full_preview.png'))
    print('chunks', n, 'size', img.shape, 'secs', round(time.time() - t, 1))
