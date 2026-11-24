"""Open world laid out like the user's reference map (240x160 tiles).

TERRAIN letters
  .  grass            _  sand (paths, beaches)   f  forest floor      w  river/lake water   O  ocean
  c  cliff            C  snowy cliff             k  ash cliff             n  snow              d  desert            a  volcanic ash
  L  lava             s  swamp water             v  corrupted ground  F  farmland          p  cobblestone
  =  bridge (horiz.)  H  bridge (vert.)          D  dock (over ocean)
ENTITY letters
  actors   P player  o orc  b blood monster  d demon  K orc chieftain  Q blood mother  B demon lord
  use      C chest  S sign  F campfire (save)  $ shop  X demonic seal  h potion  a arrows
  trees    T oak  U oak2  t small oak  A autumn  V corrupt  u corrupt small  i pine  I snowy pine  k dead  Y palm
  plants   g bush  G flower bush  q purple bush  y tulips  z daisies  M mushrooms  e cattails  l lilypad  Z stump  n log
  rocks    r small  R big  W snowy
  big      m ^ huge snowy mountains  1 2 snowy mountains  3 rock mountain  4 mesa  5 volcano  6 7 8 houses  9 castle tower  # castle wall
           0 watchtower  J windmill  j lighthouse  x dark tower  N ruin wall  ! pillar  ~ boat  + waterfall
  props    / fence  ( barrel  ) crate  * hay  ; wheat  @ well  | torch
"""
import math, os, random, sys
from collections import deque
from PIL import Image

W, H = 240, 160
BLOCK_T = set('wOcCLsk')
BLOCK_E = set('TUtAVuiIkYgGqrRW123456789#0JjxN!(|)@~X$CSF/*m^')
REGIONS = {
    'a': 'VALLE CENTRAL', 'b': 'BOSQUE DEL OESTE', 'c': 'LAGO ESPEJO', 'd': 'PANTANO CARMESÍ', 'e': 'PICOS NEVADOS',
    'f': 'ARENAS ROJAS', 'g': 'MONTE CENIZA', 'h': 'BOSQUE CORRUPTO', 'i': 'CIUDADELA DEL REY', 'j': 'COSTA DEL PUERTO',
}


def noise(x, y, s):
    v = 0
    for k, (f, a) in enumerate(((0.04, 1.0), (0.09, 0.5), (0.2, 0.25))):
        v += a * math.sin(x * f + s * 1.3 + k) * math.cos(y * f * 1.17 - s * 0.7 + k * 2)
    return v / 1.75


def U(fx, fy):
    """reference-map fraction -> tile coords"""
    return int(fx * W), int(fy * H)


class World:
    def __init__(self):
        self.t = [['.'] * W for _ in range(H)]
        self.e = [[None] * W for _ in range(H)]
        self.r = [['a'] * W for _ in range(H)]
        self.signs = []
        self.rng = random.Random(7)

    # ---------------------------------------------------------------- utils
    def inb(self, x, y): return 0 <= x < W and 0 <= y < H

    def T(self, x, y, c):
        if self.inb(x, y): self.t[y][x] = c

    def E(self, x, y, c, text=None):
        if self.inb(x, y):
            self.e[y][x] = c
            if c == 'S': self.signs.append((x, y, text or '...'))

    def blob(self, cx, cy, rx, ry, fn, wob=0.25, seed=0):
        for y in range(max(0, int(cy - ry * 1.6)), min(H, int(cy + ry * 1.6) + 1)):
            for x in range(max(0, int(cx - rx * 1.6)), min(W, int(cx + rx * 1.6) + 1)):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if d <= 1 + wob * noise(x, y, seed) * 2:
                    fn(x, y)

    def line(self, pts, width, fn, wiggle=0.0, seed=0):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(abs(x1 - x0), abs(y1 - y0), 1)
            for i in range(n + 1):
                t = i / n
                ox = wiggle * noise(i * 3 + x0, y0, seed); oy = wiggle * noise(x0, i * 3 + y0, seed + 1)
                x = x0 + (x1 - x0) * t + ox; y = y0 + (y1 - y0) * t + oy
                for dy in range(-(width // 2), width - width // 2):
                    for dx in range(-(width // 2), width - width // 2):
                        fn(int(round(x)) + dx, int(round(y)) + dy, (x1 - x0, y1 - y0))

    def place(self, x, y, c, allow='._f', rad=7, text=None):
        for r_ in range(rad + 1):
            for dy in range(-r_, r_ + 1):
                for dx in range(-r_, r_ + 1):
                    if max(abs(dx), abs(dy)) != r_: continue
                    if self.free(x + dx, y + dy, allow) and not self.crowded(x + dx, y + dy, 0):
                        self.E(x + dx, y + dy, c, text); return (x + dx, y + dy)
        return None

    def free(self, x, y, allow):
        return self.inb(x, y) and self.t[y][x] in allow and self.e[y][x] is None

    def near(self, x, y, rad, chars):
        for yy in range(y - rad, y + rad + 1):
            for xx in range(x - rad, x + rad + 1):
                if self.inb(xx, yy) and self.t[yy][xx] in chars: return True
        return False

    def crowded(self, x, y, sp):
        for yy in range(y - sp, y + sp + 1):
            for xx in range(x - sp, x + sp + 1):
                if self.inb(xx, yy) and self.e[yy][xx] is not None: return True
        return False

    def scatter(self, area, chars, n, allow, spacing=2, seed=0, avoid='_p=HD', region=None):
        r = random.Random(seed)
        x0, y0, x1, y1 = area
        placed = tries = 0
        while placed < n and tries < n * 40:
            tries += 1
            x, y = r.randint(x0, x1), r.randint(y0, y1)
            if not self.free(x, y, allow): continue
            if region and self.r[y][x] not in region: continue
            if self.crowded(x, y, spacing): continue
            if avoid and self.near(x, y, 1, avoid): continue
            self.E(x, y, r.choice(chars)); placed += 1
        return placed

    # ---------------------------------------------------------------- build
    def build(self):
        S = self
        # ---- base: grass; ocean frame (west & south), mountains north
        for y in range(H):
            for x in range(W):
                fx, fy = x / W, y / H
                n = noise(x, y, 1) * 0.04
                coast_w = 0.075 + 0.03 * math.sin(fy * 9) + n
                coast_s = 0.9 + 0.04 * math.sin(fx * 11) + n
                sw_bay = ((fx - 0.12) / 0.22) ** 2 + ((fy - 0.95) / 0.3) ** 2 < 1 + n * 4
                ocean = (fx < coast_w and fy > 0.38) or fy > coast_s or sw_bay or (fx > 0.93 and fy > 0.82 + n)
                if ocean:
                    S.t[y][x] = 'O'; S.r[y][x] = 'j'
        # beaches: sand ring around the ocean
        beach = [(x, y) for y in range(H) for x in range(W) if S.t[y][x] != 'O' and S.near(x, y, 2, 'O')]
        for (x, y) in beach: S.t[y][x] = '_'
        # ---- regions (rough, like the reference)
        def region(cx, cy, rx, ry, rid, seed):
            S.blob(*U(cx, cy), rx * W, ry * H, lambda x, y: S.r[y].__setitem__(x, rid) if S.t[y][x] != 'O' else None, 0.3, seed)
        region(0.12, 0.30, 0.13, 0.17, 'b', 2)       # western forest
        region(0.30, 0.06, 0.20, 0.10, 'e', 3)       # snowy peaks
        region(0.10, 0.20, 0.09, 0.12, 'h', 4)       # corrupted forest
        region(0.68, 0.17, 0.12, 0.13, 'i', 5)       # citadel
        region(0.90, 0.25, 0.12, 0.26, 'f', 6)       # red sands
        region(0.92, 0.55, 0.08, 0.10, 'g', 7)       # ash mountain
        region(0.85, 0.72, 0.11, 0.10, 'd', 8)       # swamp
        region(0.52, 0.48, 0.12, 0.09, 'c', 9)       # mirror lake
        region(0.18, 0.72, 0.12, 0.10, 'j', 10)      # port coast
        # ---- biome terrain
        for y in range(H):
            for x in range(W):
                if S.t[y][x] in 'O_': continue
                rid = S.r[y][x]; nz = noise(x, y, 11)
                if rid == 'e':
                    S.t[y][x] = 'n' if y < H * 0.13 + 6 * noise(x, 0, 2) else ('n' if nz > 0.3 else '.')
                elif rid == 'f':
                    S.t[y][x] = 'd'
                elif rid == 'g':
                    S.t[y][x] = 'a'
                elif rid == 'h':
                    S.t[y][x] = 'v' if nz > -0.5 else 'f'
                elif rid == 'd':
                    S.t[y][x] = 'f' if nz > -0.2 else '.'
                elif rid == 'b':
                    S.t[y][x] = 'f' if nz > -0.1 else '.'
                else:
                    S.t[y][x] = 'f' if nz > 0.55 else '.'
        # northern wall of mountains: snowy cliffs along the top rows
        for x in range(W):
            depth = 3 + int(3 + 3 * noise(x, 0, 5))
            for y in range(depth):
                if S.t[y][x] not in 'O': S.t[y][x] = 'C' if S.r[y][x] in 'eh' or x < W * 0.6 else 'c'
        # snowy cliff plateaus in the peaks
        for k in range(9):
            cx, cy = S.rng.randint(int(W * .14), int(W * .48)), S.rng.randint(6, int(H * .14))
            S.blob(cx, cy, S.rng.uniform(4, 8), S.rng.uniform(2, 4), lambda x, y: S.T(x, y, 'C') if S.t[y][x] in 'n.' else None, 0.2, k)
        # western sea cliffs
        for y in range(int(H * .35), int(H * .62)):
            for x in range(W // 6):
                if S.t[y][x] in '_.f' and S.near(x, y, 3, 'O') and not S.near(x, y, 1, 'O'): S.t[y][x] = 'c'
        # mirror lake + island
        lx, ly = U(0.52, 0.48)
        S.blob(lx, ly, 17, 10, lambda x, y: S.T(x, y, 'w'), 0.15, 21)
        S.blob(lx - 2, ly, 4, 3, lambda x, y: S.T(x, y, '.'), 0.1, 22)
        # rivers: glacier -> waterfall -> lake ; lake -> south-east coast ; small creek west
        river = lambda x, y, d: S.T(x, y, 'w') if S.inb(x, y) and S.t[y][x] not in 'O' else None
        S.line([U(0.33, 0.10), U(0.33, 0.22), U(0.40, 0.33), U(0.47, 0.42)], 3, river, 2.5, 31)
        S.line([U(0.60, 0.52), U(0.66, 0.62), U(0.70, 0.74), U(0.72, 0.86), U(0.73, 0.95)], 3, river, 2.5, 32)
        S.line([U(0.24, 0.40), U(0.20, 0.50), U(0.14, 0.56), U(0.08, 0.60)], 2, river, 2.0, 33)
        # the glacier river springs from a snowy cliff (a waterfall will be placed under it)
        sx_, sy_ = U(0.33, 0.10)
        for yy in range(sy_ - 5, sy_ + 1):
            for xx in range(sx_ - 4, sx_ + 6):
                if S.inb(xx, yy): S.t[yy][xx] = 'C'
        for yy in range(sy_ + 1, sy_ + 4):
            for xx in range(sx_ - 1, sx_ + 3):
                if S.inb(xx, yy): S.t[yy][xx] = 'w'
        # swamp pools
        for k in range(22):
            cx, cy = S.rng.randint(int(W * .74), int(W * .95)), S.rng.randint(int(H * .63), int(H * .82))
            if S.r[cy][cx] == 'd' and S.t[cy][cx] != 'O':
                S.blob(cx, cy, S.rng.uniform(2, 4.5), S.rng.uniform(1.5, 3), lambda x, y: S.T(x, y, 's') if S.t[y][x] in '.f' else None, 0.3, 40 + k)
        # lava lakes around the volcano
        vx, vy = U(0.92, 0.55)
        for k in range(6):
            cx, cy = vx + S.rng.randint(-14, 14), vy + S.rng.randint(-8, 9)
            if abs(cx - vx) + abs(cy - vy) > 6:
                S.blob(cx, cy, S.rng.uniform(1.5, 3.5), S.rng.uniform(1.2, 2.5), lambda x, y: S.T(x, y, 'L') if S.t[y][x] == 'a' else None, 0.3, 60 + k)
        # farmland around the valley villages
        for (fx, fy, w_, h_) in [(0.60, 0.60, 8, 5), (0.68, 0.56, 7, 4), (0.62, 0.68, 6, 4), (0.44, 0.62, 6, 4), (0.72, 0.38, 6, 4)]:
            x0, y0 = U(fx, fy)
            for y in range(y0, y0 + h_):
                for x in range(x0, x0 + w_):
                    if S.t[y][x] in '.f': S.t[y][x] = 'F'
        # citadel: cobblestone court inside walls
        cx, cy = U(0.68, 0.17)
        for y in range(cy - 9, cy + 10):
            for x in range(cx - 15, cx + 16):
                if abs(x - cx) <= 1 or abs(y - cy) <= 1 or (abs(x - cx) <= 5 and abs(y - cy) <= 3) or y >= cy + 8:
                    S.T(x, y, 'p')
                elif S.t[y][x] in 'fd_': S.t[y][x] = '.'

        # ---- roads (sand), stone roads near the citadel, bridges on water
        def road(pts, width=2, mat='_', wig=1.5, seed=0):
            def put(x, y, d):
                if not S.inb(x, y): return
                t = S.t[y][x]
                if t == 'w': S.t[y][x] = '=' if abs(d[0]) >= abs(d[1]) else 'H'
                elif t in 'sL': S.t[y][x] = mat
                elif t in 'O=HD': return
                elif t == 'p': return
                else: S.t[y][x] = mat
                if S.e[y][x] in BLOCK_E: S.e[y][x] = None
            S.line(pts, width, put, wig, seed)
        hub = U(0.52, 0.68)                               # Valle Central village (start)
        road([hub, U(0.52, 0.60), U(0.47, 0.56), U(0.40, 0.48), U(0.38, 0.36), U(0.42, 0.25), U(0.55, 0.22), U(0.62, 0.20)], seed=1)
        road([U(0.62, 0.20), U(0.68, 0.24)], 3, 'p', 0.5, 2)                  # citadel gate road
        road([hub, U(0.60, 0.63), U(0.68, 0.58), U(0.76, 0.48), U(0.84, 0.40), U(0.90, 0.30)], seed=3)   # to the red sands
        road([U(0.76, 0.48), U(0.86, 0.52), U(0.89, 0.55)], seed=4)          # volcano path (sealed)
        road([hub, U(0.62, 0.74), U(0.74, 0.76), U(0.84, 0.72)], seed=5)       # to the swamp
        road([hub, U(0.40, 0.70), U(0.28, 0.70), U(0.18, 0.70)], seed=6)       # to the port
        road([U(0.28, 0.70), U(0.24, 0.55), U(0.20, 0.40), U(0.14, 0.26), U(0.10, 0.18)], seed=7)   # west forest -> corrupted
        road([U(0.20, 0.40), U(0.30, 0.20), U(0.30, 0.12)], seed=8)            # to the peaks
        # bridge to the island: straight, 2 wide, from the island's south shore to the lake's south shore
        y = ly
        while S.t[y][lx - 2] != 'w' and y < ly + 12: y += 1
        while S.inb(lx, y) and S.t[y][lx - 2] in 'wH':
            S.T(lx - 2, y, 'H'); S.T(lx - 1, y, 'H'); y += 1
        road([(lx - 2, y), (lx - 2, y + 4), U(0.47, 0.56)], 2, '_', 0.0, 9)
        self.straighten_bridges()
        self.drop_stray_bridges()
        self.bridge_pads()
        # port: the beach cell closest to the planned spot that has land behind it and sea in front
        tx, ty = U(0.20, 0.68)
        best = None
        for y in range(H):
            for x in range(W):
                if S.t[y][x] == '_' and S.near(x, y, 2, 'O') and S.t[max(0, y - 3)][x] in '.f':
                    d = (x - tx) ** 2 + (y - ty) ** 2
                    if best is None or d < best[0]: best = (d, x, y)
        _, px_, py_ = best
        # dock: walk toward the nearest sea cell and keep going for 7 tiles
        ocean_cells = [(x, y) for y in range(py_ - 9, py_ + 10) for x in range(px_ - 9, px_ + 10) if S.inb(x, y) and S.t[y][x] == 'O']
        vx_ = sum(x - px_ for x, _ in ocean_cells); vy_ = sum(y - py_ for _, y in ocean_cells)
        ddx, ddy = ((1 if vx_ > 0 else -1), 0) if abs(vx_) > abs(vy_) else (0, (1 if vy_ > 0 else -1))
        x, y = px_, py_
        for i in range(10):
            x += ddx; y += ddy
            for k in (0, 1):
                xx, yy = (x + k, y) if ddx == 0 else (x, y + k)
                if S.inb(xx, yy) and S.t[yy][xx] == 'O': S.t[yy][xx] = 'D'
        self.dock_end = (x + ddx * 2, y + ddy * 2)

        # ---------------------------------------------------------- landmarks
        P = lambda f, c, t=None: S.E(*U(*f), c, t)
        # start village (Valle Central)
        S.E(hub[0], hub[1] + 2, 'P')
        S.E(hub[0] + 3, hub[1] + 3, 'F')
        S.E(hub[0] - 4, hub[1] - 2, '$')
        S.E(hub[0] + 2, hub[1] - 3, '@')
        S.E(hub[0] - 2, hub[1] + 4, 'S', 'VALLE CENTRAL. DOS GUARDIANES MANTIENEN EL SELLO DEL MONTE CENIZA (ESTE): EL JEFE ORCO EN SU FUERTE DE LAS ARENAS ROJAS Y LA MADRE DE SANGRE EN EL PANTANO CARMESÍ (SURESTE).')
        S.E(hub[0] + 5, hub[1] + 1, 'S', 'HOGUERAS: PULSA E PARA DESCANSAR Y GUARDAR. M ABRE EL MAPA, TAB EL DIARIO.')
        for (dx, dy, c) in [(-8, -5, '6'), (6, -6, '7'), (-9, 3, '8'), (9, 2, '6'), (13, -9, 'J'), (-14, -8, 'J'), (4, 8, '8')]:
            S.E(hub[0] + dx, hub[1] + dy, c)
        for (dx, dy, c) in [(-6, 1, '('), (-5, 1, ')'), (7, -2, '*'), (8, -2, '*'), (2, 5, '|'), (-3, 5, '|')]:
            S.E(hub[0] + dx, hub[1] + dy, c)
        # citadel walls & towers
        cx, cy = U(0.68, 0.17)
        for x in range(cx - 15, cx + 16, 2):
            for y in (cy - 9, cy + 9):
                if not (y == cy + 9 and abs(x - cx) <= 2): S.E(x, y, '#')
        for y in range(cy - 9, cy + 10, 2):
            S.E(cx - 15, y, '#'); S.E(cx + 15, y, '#')
        for (dx, dy) in [(-15, -9), (15, -9), (-15, 9), (15, 9), (-4, -4), (4, -4), (0, -6)]:
            S.E(cx + dx, cy + dy, '9')
        for (dx, dy, c) in [(-9, -2, '7'), (-9, 4, '6'), (9, -2, '7'), (9, 4, '6'), (-4, 3, '8'), (4, 3, '7')]:
            S.E(cx + dx, cy + dy, c)
        S.E(cx, cy + 3, 'F'); S.E(cx + 2, cy + 6, '$'); S.E(cx - 2, cy + 6, '@')
        S.E(cx + 1, cy + 11, 'S', 'CIUDADELA DEL REY. EL REY OFRECE ESTE REFUGIO A QUIEN COMBATA A LOS DEMONIOS. AQUÍ PUEDES COMERCIAR Y DESCANSAR.')
        # lake island temple
        S.E(lx - 2, ly - 1, '0'); S.E(lx, ly, 'C'); S.E(lx - 4, ly, '!'); S.E(lx + 1, ly - 2, '!')
        # port town on land behind the beach
        inland = (px_, py_ - 5)
        for (dx, dy, c) in [(-4, -2, '6'), (2, -3, '7'), (7, -1, '8'), (-1, 2, '('), (0, 2, ')'), (3, 2, '('), (-3, 3, '|'), (5, 3, '|')]:
            S.place(inland[0] + dx, inland[1] + dy, c, '._f')
        S.place(inland[0] + 1, inland[1] + 1, 'F', '.f'); S.place(inland[0] + 8, inland[1] + 2, '$', '.f')
        bx, by = self.dock_end
        if S.inb(bx, by) and S.t[by][bx] == 'O': S.E(bx, by, '~')
        lhx, lhy = U(0.09, 0.90)
        S.blob(lhx, lhy, 4, 3, lambda x, y: S.T(x, y, '_'), 0.1, 70)
        S.blob(lhx, lhy, 2.5, 1.8, lambda x, y: S.T(x, y, '.'), 0.1, 71)
        S.E(lhx, lhy, 'j')
        # dark tower in the swamp + blood mother
        sx, sy = U(0.86, 0.73)
        for y in range(sy - 5, sy + 6):
            for x in range(sx - 7, sx + 8):
                if S.t[y][x] in 's': S.t[y][x] = 'f'
                S.e[y][x] = None
        S.E(sx, sy - 3, 'x'); S.E(sx, sy + 2, 'Q'); S.E(sx - 4, sy + 4, 'F')
        # orc fort in the red sands + chieftain
        ox, oy = U(0.90, 0.28)
        for x in range(ox - 7, ox + 8, 2):
            S.E(x, oy - 6, '#')
            if abs(x - ox) > 2: S.E(x, oy + 6, '#')
        for y in range(oy - 6, oy + 7, 2):
            S.E(ox - 7, y, '#'); S.E(ox + 7, y, '#')
        S.E(ox - 7, oy - 6, '0'); S.E(ox + 7, oy - 6, '0')
        S.E(ox, oy, 'K')
        for (dx, dy, c) in [(-4, -3, '('), (-3, -3, ')'), (4, 3, ')'), (3, -3, '|'), (-3, 3, '|')]:
            S.E(ox + dx, oy + dy, c)
        S.E(ox + 3, oy + 9, 'F'); S.E(ox - 3, oy + 2, 'C')
        # volcano + seal + demon lord
        S.E(vx, vy - 2, '5')
        S.E(vx, vy + 4, 'B')
        sealx, sealy = U(0.86, 0.52)
        for (dx, dy) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            S.E(sealx + dx, sealy + dy, 'X')
        # ring of rock mountains around the volcano so the seal is the only way in
        for k in range(360):
            a = k / 360 * 2 * math.pi
            for rr in (14.0, 15.0, 16.0):
                x = int(round(vx + math.cos(a) * rr)); y = int(round(vy + math.sin(a) * rr * 0.66))
                if abs(x - sealx) <= 1 + (sealx < x < sealx + 2) and abs(y - sealy) <= 1: continue
                if S.inb(x, y) and S.t[y][x] not in 'O' and not (sealx <= x <= sealx + 1 and sealy <= y <= sealy + 1):
                    S.t[y][x] = 'k'
                    if S.e[y][x] in BLOCK_E: S.e[y][x] = None
        # the only way in: a corridor right behind the seal
        n = 24
        for i in range(n + 1):
            x = round(sealx + 2 + (vx - 6 - sealx - 2) * i / n); y = round(sealy + (vy - sealy) * i / n)
            for dy in (0, 1):
                for dx in (0, 1):
                    if S.inb(x + dx, y + dy) and S.t[y + dy][x + dx] in 'ck': S.t[y + dy][x + dx] = 'a'
        S.E(sealx - 2, sealy + 3, 'S', 'EL SELLO DEL MONTE CENIZA. SOLO CAERÁ CUANDO EL JEFE ORCO Y LA MADRE DE SANGRE HAYAN SIDO DERROTADOS.')
        S.E(sealx - 4, sealy + 2, 'F')
        # corrupted forest shrine
        hx, hy = U(0.10, 0.18)
        S.E(hx, hy, 'x'); S.E(hx + 3, hy + 3, 'C'); S.E(hx - 3, hy + 4, 'N'); S.E(hx + 5, hy - 1, 'N')
        # campfires along the world (save points)
        for f in [(0.40, 0.47), (0.30, 0.22), (0.20, 0.40), (0.12, 0.26), (0.76, 0.48), (0.62, 0.74), (0.45, 0.30)]:
            x, y = U(*f)
            for k in range(8):
                xx, yy = x + k % 3, y + k // 3
                if S.free(xx, yy, '._fnd') and not S.near(xx, yy, 0, 'wOs'):
                    S.E(xx, yy, 'F'); break
        # waterfalls where the glacier river leaves the peaks
        # waterfalls only where a river leaves a cliff (river cell with a cliff right above it)
        for y in range(1, H):
            for x in range(W):
                if S.t[y][x] == 'w' and S.t[y - 1][x] in 'cC' and S.t[y][x - 1] == 'w' and S.t[y][x + 1] == 'w' and S.e[y][x] is None:
                    if not S.crowded(x, y, 3): S.E(x, y + 1, '+')

        # ---------------------------------------------------------- treasure & enemies (before decor)
        full = (2, 2, W - 3, H - 3)
        for rid, n in [('b', 6), ('e', 4), ('h', 4), ('f', 4), ('d', 4), ('c', 2), ('a', 5), ('j', 3), ('g', 2)]:
            S.scatter(full, 'C', n, '._fndav', 4, 100 + ord(rid), region=rid)
            S.scatter(full, 'h', max(1, n // 2), '._fndav', 4, 200 + ord(rid), region=rid)
            S.scatter(full, 'a', max(1, n // 2), '._fndav', 4, 300 + ord(rid), region=rid)
        for rid, chars, n in [('b', 'oooob', 40), ('e', 'oood', 22), ('h', 'ddddb', 26), ('f', 'oooo', 30), ('d', 'bbbbo', 32),
                              ('c', 'bbo', 12), ('a', 'ob', 14), ('j', 'ob', 12), ('g', 'dd', 10), ('i', '', 0)]:
            if n: S.scatter(full, chars, n, '._fndav', 3, 400 + ord(rid), avoid='p=HD', region=rid)
        # safe zones: villages, citadel, port
        for (zx, zy, rad) in [(hub[0], hub[1], 14), (cx, cy, 17), (px_ + 4, py_, 9)]:
            for y in range(zy - rad, zy + rad):
                for x in range(zx - rad, zx + rad):
                    if self.inb(x, y) and S.e[y][x] in ('o', 'b', 'd'): S.e[y][x] = None

        # ---------------------------------------------------------- decoration by biome
        S.scatter(full, 'TTUUtiggyyzZn', 900, '.f', 2, 1, region='b')
        S.scatter(full, 'TUtggGyyz', 260, '.f', 2, 2, region='a')
        S.scatter(full, 'TtGgyyze', 140, '.f', 2, 3, region='c')
        S.scatter(full, 'iiIIWr', 160, 'n.', 2, 4, region='e')
        S.scatter(full, '1122', 70, 'nC', 3, 5, avoid='', region='e')
        self.clear_near_roads('12m^3', 4)
        S.scatter(full, 'VVuuqMk', 260, 'vf.', 2, 6, region='h')
        S.scatter(full, '44Rrk', 110, 'd', 3, 7, region='f')
        S.scatter(full, '3Rrk', 40, 'a', 3, 8, region='g')
        S.scatter(full, 'kkMMegZn', 260, 'f.', 2, 9, region='d')
        S.scatter(full, 'YYgyz', 80, '_.', 3, 10, region='j')
        for y in range(H):
            for x in range(W):
                if S.e[y][x] == 'Y' and S.t[y][x] == '_' and not S.near(x, y, 4, 'O'): S.e[y][x] = None
        S.scatter(full, 'AATtG', 30, '.f', 2, 11, region='i')
        S.scatter(full, 'Y', 60, '_', 4, 12, avoid='p=HD')                        # palms on beaches everywhere
        for y in range(H):
            for x in range(W):
                if S.e[y][x] == 'Y' and not S.near(x, y, 4, 'O'): S.e[y][x] = None   # palms only by the sea
        S.scatter(full, '3', 40, 'c', 3, 13, avoid='_p')                          # rocks on cliff tops
        S.scatter(full, '1', 30, 'C', 4, 14, avoid='_p')
        S.scatter(full, ';', 120, 'F', 1, 15, avoid='')                           # wheat in the fields
        S.scatter(full, 'le', 120, 'w', 2, 16, avoid='')                          # lilies & cattails
        for y in range(H):
            for x in range(W):
                if S.e[y][x] == 'e' and not S.near(x, y, 1, '.f_'): S.e[y][x] = 'l'     # cattails only near the bank
        self.densify()
        self.clear_near_roads('12m^3', 4)
        S.border()

    def straighten_bridges(self):
        """turn every bridge crossing into a solid rectangle (no ragged strips)"""
        S = self
        seen = set()
        for y in range(H):
            for x in range(W):
                c = S.t[y][x]
                if c not in '=H' or (x, y) in seen: continue
                comp = []; q = [(x, y)]; seen.add((x, y))
                while q:
                    a, b = q.pop(); comp.append((a, b))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        n = (a + dx, b + dy)
                        if S.inb(*n) and n not in seen and S.t[n[1]][n[0]] == c:
                            seen.add(n); q.append(n)
                xs = [p[0] for p in comp]; ys = [p[1] for p in comp]
                for yy in range(min(ys), max(ys) + 1):
                    for xx in range(min(xs), max(xs) + 1):
                        if S.t[yy][xx] in 'wsL': S.t[yy][xx] = c

    def drop_stray_bridges(self):
        """a bridge must go from land to land across water; anything else goes back to water"""
        S = self
        seen = set()
        for y in range(H):
            for x in range(W):
                c = S.t[y][x]
                if c not in '=H' or (x, y) in seen: continue
                comp = []; q = [(x, y)]; seen.add((x, y))
                while q:
                    a, b = q.pop(); comp.append((a, b))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        n = (a + dx, b + dy)
                        if S.inb(*n) and n not in seen and S.t[n[1]][n[0]] == c:
                            seen.add(n); q.append(n)
                xs = [p[0] for p in comp]; ys = [p[1] for p in comp]
                land = lambda a, b: S.inb(a, b) and S.t[b][a] not in 'wsLO=HD'
                # grow the deck until both ends rest fully on land (shores are rarely straight)
                for _ in range(5):
                    if c == 'H':
                        cols = sorted(set(xs)); top, bot = min(ys), max(ys)
                        if not all(land(xx, top - 1) for xx in cols):
                            for xx in cols:
                                if S.inb(xx, top - 1) and S.t[top - 1][xx] in 'ws': S.t[top - 1][xx] = 'H'; comp.append((xx, top - 1))
                        if not all(land(xx, bot + 1) for xx in cols):
                            for xx in cols:
                                if S.inb(xx, bot + 1) and S.t[bot + 1][xx] in 'ws': S.t[bot + 1][xx] = 'H'; comp.append((xx, bot + 1))
                    else:
                        rows = sorted(set(ys)); lft, rgt = min(xs), max(xs)
                        if not all(land(lft - 1, yy) for yy in rows):
                            for yy in rows:
                                if S.inb(lft - 1, yy) and S.t[yy][lft - 1] in 'ws': S.t[yy][lft - 1] = '='; comp.append((lft - 1, yy))
                        if not all(land(rgt + 1, yy) for yy in rows):
                            for yy in rows:
                                if S.inb(rgt + 1, yy) and S.t[yy][rgt + 1] in 'ws': S.t[yy][rgt + 1] = '='; comp.append((rgt + 1, yy))
                    xs = [p[0] for p in comp]; ys = [p[1] for p in comp]
                if c == '=':
                    ok = all(land(min(xs) - 1, yy) for yy in set(ys)) and all(land(max(xs) + 1, yy) for yy in set(ys))
                    span = max(xs) - min(xs) + 1
                else:
                    ok = all(land(xx, min(ys) - 1) for xx in set(xs)) and all(land(xx, max(ys) + 1) for xx in set(xs))
                    span = max(ys) - min(ys) + 1
                if not ok or span < 2:
                    for (a, b) in comp:
                        S.t[b][a] = '_' if any(land(a + dx, b + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) and span < 3 else 'w'

    def bridge_pads(self):
        S = self
        seen = set()
        for y in range(H):
            for x in range(W):
                c = S.t[y][x]
                if c not in '=H' or (x, y) in seen: continue
                comp = []; q = [(x, y)]; seen.add((x, y))
                while q:
                    a, b = q.pop(); comp.append((a, b))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        n = (a + dx, b + dy)
                        if S.inb(*n) and n not in seen and S.t[n[1]][n[0]] == c:
                            seen.add(n); q.append(n)
                xs = [p[0] for p in comp]; ys = [p[1] for p in comp]
                ends = []
                if c == 'H':
                    for xx in set(xs):
                        ends += [(xx, min(ys) - k) for k in (1, 2, 3)] + [(xx, max(ys) + k) for k in (1, 2, 3)]
                else:
                    for yy in set(ys):
                        ends += [(min(xs) - k, yy) for k in (1, 2, 3)] + [(max(xs) + k, yy) for k in (1, 2, 3)]
                for (a, b) in ends:
                    if S.inb(a, b) and S.t[b][a] in '.f_dnva':
                        S.t[b][a] = '_'
                        if S.e[b][a] in BLOCK_E: S.e[b][a] = None

    def clear_near_roads(self, chars, rad):
        for y in range(H):
            for x in range(W):
                if self.e[y][x] and self.e[y][x] in chars and (self.near(x, y, rad, '_p=HD') or self.near(x, y + 1, rad, '_p=HD')):
                    self.e[y][x] = None

    def densify(self):
        """thick forests and a solid mountain range, like the reference map (roads stay clear)"""
        S = self
        r = random.Random(99)
        cells = [(x, y) for y in range(2, H - 2) for x in range(2, W - 2)]
        r.shuffle(cells)
        roads = '_p=HDO'
        for (x, y) in cells:
            if S.e[y][x] is not None: continue
            t, rid = S.t[y][x], S.r[y][x]
            if rid == 'e' and t in 'nC':
                if not S.near(x, y, 4, roads) and not S.near(x, y + 1, 4, roads) and not S.crowded(x, y, 2) and r.random() < 0.55:
                    S.E(x, y, r.choice('m^12'))
                continue
            if S.near(x, y, 1, roads) or S.crowded(x, y, 1): continue
            if any(S.inb(xx, yy) and S.e[yy][xx] is not None and S.e[yy][xx] in '6789J0#xj$@|('
                   for yy in range(y - 2, y + 5) for xx in range(x - 4, x + 5)): continue   # keep buildings clear
            p, pool = 0, ''
            if t == 'f':
                p, pool = {'b': (.55, 'TTUUti'), 'h': (.5, 'VVuT'), 'd': (.3, 'kkTt'), 'a': (.5, 'TUtA'), 'c': (.45, 'TUt'),
                           'j': (.45, 'TUtY'), 'i': (.4, 'TAU'), 'e': (.4, 'iiI')}.get(rid, (.4, 'TUt'))
            elif t == 'v':
                p, pool = .45, 'VVuuq'
            elif t == '.':
                p, pool = {'b': (.12, 'TUti'), 'a': (.05, 'TUt'), 'c': (.06, 'TUt'), 'e': (.1, 'iI'), 'j': (.04, 'TY')}.get(rid, (.03, 'Tt'))
            if pool and r.random() < p:
                S.E(x, y, r.choice(pool))

    def border(self):
        for x in range(W):
            for y in (0, H - 1):
                if self.t[y][x] != 'O': self.t[y][x] = 'c' if y else 'C'
        for y in range(H):
            for x in (0, W - 1):
                if self.t[y][x] != 'O': self.t[y][x] = 'c'

    # ---------------------------------------------------------- validation
    def walkable(self, x, y, seal_open):
        t = self.t[y][x]; e = self.e[y][x]
        if t in BLOCK_T: return False
        if e is None or e in 'PobdKQBhalyzMeZn;+': return True
        if e == 'X': return seal_open
        return e not in BLOCK_E

    def reach(self, seal_open):
        start = next((x, y) for y in range(H) for x in range(W) if self.e[y][x] == 'P')
        seen = {start}; q = deque([start])
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if self.inb(nx, ny) and (nx, ny) not in seen and self.walkable(nx, ny, seal_open):
                    seen.add((nx, ny)); q.append((nx, ny))
        return seen

    def validate(self):
        closed, opened = self.reach(False), self.reach(True)
        must = {}
        for y in range(H):
            for x in range(W):
                c = self.e[y][x]
                if c in ('o', 'b', 'd', 'K', 'Q', 'B', 'h', 'a'):
                    must[(x, y)] = c
                if c in ('C', 'S', 'F', '$'):
                    if not any((x + dx, y + dy) in opened for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))):
                        must[(x, y)] = c
        bad = [(c, p) for p, c in must.items() if p not in opened and c not in 'CSF$']
        bad += [(c, p) for p, c in must.items() if c in 'CSF$']
        behind = [c for p, c in must.items() if p in opened and p not in closed]
        return bad, len(closed), len(opened), behind

    def prune(self):
        bad, *_ = self.validate()
        for c, (x, y) in bad:
            if c in 'KQB':
                continue
            self.e[y][x] = None
        return len(bad)

    # ---------------------------------------------------------- output
    def dump(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f'TITLE MUNDO\nSUBTITLE \nSIZE {W} {H}\n')
            for (x, y, s) in self.signs:
                if self.e[y][x] == 'S': f.write(f'SIGN {x} {y} {s}\n')
            f.write('TERRAIN\n' + '\n'.join(''.join(r) for r in self.t) + '\n')
            f.write('ENTITIES\n' + '\n'.join(''.join(c or ' ' for c in r) for r in self.e) + '\n')
            f.write('REGIONS\n' + '\n'.join(''.join(r) for r in self.r) + '\n')
            for k, name in REGIONS.items(): f.write(f'REGIONNAME {k} {name}\n')


if __name__ == '__main__':
    w = World(); w.build()
    pruned = w.prune()
    bad, rc, ro, behind = w.validate()
    w.dump(os.path.join(sys.argv[1], 'Assets', 'Game', 'Levels', 'World2.txt'))
    cnt = {}
    for row in w.e:
        for c in row:
            if c: cnt[c] = cnt.get(c, 0) + 1
    print('pruned', pruned, 'still bad', [b for b in bad if b[0] in 'KQB'], 'reach', rc, 'with seal open', ro, 'behind seal', behind)
    print({k: cnt[k] for k in 'PobdKQBCF$SXh' if k in cnt})
