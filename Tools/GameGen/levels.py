"""Level design -> ASCII layouts (Assets/Game/Levels/*.txt) + reachability check.

Terrain:  ' ' dirt  '.' grass  '"' tall grass  'p' stone path  'w' water  'c' cliff (blocks)
          '=' bridge (horizontal, over water)  'H' bridge (vertical, over water)
Entities (ground under them = grass unless on path/dirt):
  P player  o orc  d demon  m blood monster  B boss  C chest  S sign  E exit
  T big tree  t small tree  i pine  D dead tree  b big bush  g small bush  r rock  x crate  k barrel
  u pot  L torch  F campfire  l lantern  R ruin wall  I pillar  O obelisk  G grave  f fence  y flowers
  v tall-grass tuft  n log  h potion  a arrows  $ coin  M mushrooms  Z stump
"""
import math, os, random, sys
from collections import deque

BLOCK_T = set('wc')                          # terrain that blocks
BLOCK_E = set('TtiDbrRIOGxkuLFlnCSZf')       # entities with colliders (trees, props...)


class Level:
    def __init__(self, w, h, ground='.'):
        self.w, self.h = w, h
        self.t = [[ground] * w for _ in range(h)]
        self.e = [[None] * w for _ in range(h)]
        self.signs = []

    def T(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.t[y][x] = c

    def E(self, x, y, c, text=None):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.e[y][x] = c
            if c == 'S':
                self.signs.append((x, y, text or '...'))

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.T(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c, wob=0.0, seed=0):
        r = random.Random(seed)
        for y in range(self.h):
            for x in range(self.w):
                a = math.atan2(y - cy, x - cx)
                k = 1 + wob * math.sin(3 * a + seed) + wob * 0.5 * math.cos(5 * a)
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= k * k:
                    self.T(x, y, c)

    def path(self, pts, c='p', width=2):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(abs(x1 - x0), abs(y1 - y0))
            for i in range(n + 1):
                x = round(x0 + (x1 - x0) * i / max(n, 1)); y = round(y0 + (y1 - y0) * i / max(n, 1))
                for dx in range(width):
                    for dy in range(width):
                        if self.t[min(self.h - 1, y + dy)][min(self.w - 1, x + dx)] not in 'w=H':
                            self.T(x + dx, y + dy, c)

    def border(self):
        for x in range(self.w):
            self.T(x, 0, 'c'); self.T(x, self.h - 1, 'c')
        for y in range(self.h):
            self.T(0, y, 'c'); self.T(self.w - 1, y, 'c')

    def free(self, x, y, allow='."'):
        return 0 <= x < self.w and 0 <= y < self.h and self.t[y][x] in allow and self.e[y][x] is None

    def scatter(self, chars, n, seed, area=None, allow='."', spacing=2):
        r = random.Random(seed)
        x0, y0, x1, y1 = area or (1, 1, self.w - 2, self.h - 2)
        placed = 0
        for _ in range(n * 40):
            if placed >= n:
                break
            x, y = r.randint(x0, x1), r.randint(y0, y1)
            if not self.free(x, y, allow):
                continue
            if any(self.e[yy][xx] for yy in range(max(0, y - spacing), min(self.h, y + spacing + 1))
                   for xx in range(max(0, x - spacing), min(self.w, x + spacing + 1))):
                continue
            # keep paths and their sides clear
            if any(self.t[yy][xx] in 'p=H' for yy in range(max(0, y - 1), min(self.h, y + 2)) for xx in range(max(0, x - 1), min(self.w, x + 2))):
                continue
            self.E(x, y, r.choice(chars))
            placed += 1

    def scatter_top(self, chars, n, seed, spacing=2):
        """decoration on cliff plateaus (only fully interior cells, so the cliff faces stay clean)"""
        r = random.Random(seed); placed = 0
        for _ in range(n * 60):
            if placed >= n: break
            x, y = r.randint(1, self.w - 2), r.randint(1, self.h - 2)
            if self.e[y][x] is not None: continue
            if not all(0 <= x + dx < self.w and 0 <= y + dy < self.h and self.t[y + dy][x + dx] == 'c'
                       for dx in (-1, 0, 1) for dy in (-2, -1, 0, 1, 2)):
                continue
            if any(self.e[yy][xx] for yy in range(max(0, y - spacing), min(self.h, y + spacing + 1))
                   for xx in range(max(0, x - spacing), min(self.w, x + spacing + 1))):
                continue
            self.E(x, y, r.choice(chars)); placed += 1

    def walkable(self, x, y):
        return self.t[y][x] not in BLOCK_T and (self.e[y][x] is None or self.e[y][x] not in BLOCK_E)

    def check(self):
        start = next((x, y) for y in range(self.h) for x in range(self.w) if self.e[y][x] == 'P')
        seen = {start}; q = deque([start])
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.w and 0 <= ny < self.h and (nx, ny) not in seen and self.walkable(nx, ny):
                    seen.add((nx, ny)); q.append((nx, ny))
        problems = []
        for y in range(self.h):
            for x in range(self.w):
                c = self.e[y][x]
                if c in ('o', 'd', 'm', 'B', 'E', 'h', 'a', '$'):
                    if (x, y) not in seen: problems.append((c, x, y))
                if c in ('C', 'S'):
                    if not any((x + dx, y + dy) in seen for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0))):
                        problems.append((c, x, y))
        return problems, len(seen)

    def dump(self, path, title, subtitle):
        rows = []
        for y in range(self.h):
            rows.append(''.join(self.e[y][x] if self.e[y][x] else self.t[y][x] for x in range(self.w)))
        terrain = [''.join(r) for r in self.t]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f'TITLE {title}\nSUBTITLE {subtitle}\nSIZE {self.w} {self.h}\n')
            for (sx, sy, s) in self.signs:
                f.write(f'SIGN {sx} {sy} {s}\n')
            f.write('TERRAIN\n' + '\n'.join(terrain) + '\nENTITIES\n' + '\n'.join(rows) + '\n')


def level1():
    L = Level(48, 32)
    L.border()
    # northern ridge + eastern plateau
    L.rect(1, 1, 46, 3, 'c'); L.rect(30, 4, 46, 8, 'c'); L.rect(1, 4, 6, 6, 'c')
    L.ellipse(20, 4, 6, 2.2, 'c', 0.15, 3)
    # pond with a bridge
    L.ellipse(31, 17, 6.5, 4.5, 'w', 0.12, 1)
    # tall grass meadows
    L.ellipse(10, 11, 5, 3, '"', 0.2, 2); L.ellipse(40, 25, 4.5, 3, '"', 0.2, 5); L.ellipse(22, 25, 3, 2, '"', 0.3, 7)
    # main road: camp (SW) -> north across the bridge -> exit (NE, gap in plateau)
    L.path([(4, 27), (12, 27), (16, 22), (24, 22), (24, 17)])
    for x in range(24, 39):
        if L.t[17][x] == 'w': L.T(x, 17, '='); L.T(x, 18, '=')
    L.path([(38, 17), (42, 17), (42, 9)])
    L.rect(41, 4, 44, 8, 'p')      # pass through the plateau
    L.rect(41, 3, 44, 3, 'p')
    # camp
    L.E(5, 26, 'P')
    L.E(2, 26, 'F'); L.E(3, 28, 'k'); L.E(4, 29, 'x'); L.E(11, 29, 'x'); L.E(12, 29, 'u')
    L.E(7, 24, 'S', 'BIENVENIDO, SOLDADO. LOS DEMONIOS HAN CORROMPIDO EL BOSQUE. J ESPADA (PULSA DOS VECES PARA COMBO), K GOLPE FUERTE, L ARCO, ESPACIO RODAR, Q POCIÓN.')
    L.E(2, 24, 'L'); L.E(13, 24, 'L')
    for x in range(1, 15, 2):
        if L.t[30][x] == '.': L.E(x, 30, 'f')
    # enemies
    for (x, y, c) in [(18, 19, 'o'), (14, 15, 'o'), (9, 11, 'o'), (26, 26, 'o'),
                      (27, 12, 'm'), (36, 22, 'm'), (38, 13, 'm'),
                      (40, 24, 'o'), (44, 21, 'o'), (43, 13, 'o')]:
        L.E(x, y, c)
    # treasure
    L.E(3, 9, 'C'); L.E(45, 28, 'C'); L.E(21, 14, 'C')
    L.E(22, 18, 'S', 'CUIDADO CON LOS MONSTRUOS DE SANGRE: ESCUPEN DESDE LEJOS. ¡RUEDA CON ESPACIO PARA ESQUIVAR!')
    L.E(40, 11, 'S', 'AL NORTE, TRAS EL PASO: LAS RUINAS MALDITAS. LIMPIA EL CAMINO ANTES DE CRUZAR.')
    L.E(42, 2, 'E'); L.E(43, 2, 'E')
    L.T(42, 2, 'p'); L.T(43, 2, 'p'); L.T(42, 1, 'p'); L.T(43, 1, 'p')
    L.E(40, 5, 'l') if L.t[5][40] == 'c' else None
    L.E(45, 10, 'l'); L.E(39, 10, 'l')
    L.E(16, 26, 'h'); L.E(33, 27, 'a'); L.E(10, 19, '$'); L.E(11, 19, '$')
    # forest dressing
    L.scatter('TTtii', 18, 11, spacing=3)
    L.scatter('gbrZMy', 26, 12, spacing=2)
    L.scatter('yyvv', 30, 13, spacing=1)
    L.scatter('n', 3, 14, spacing=3)
    L.scatter_top('iiTt', 16, 15, spacing=2)
    return L


def level2():
    L = Level(48, 34, ground=' ')
    L.border()
    # patches of dying grass
    L.ellipse(10, 26, 7, 5, '.', 0.25, 2); L.ellipse(38, 24, 6, 5, '.', 0.25, 4); L.ellipse(24, 14, 5, 3, '.', 0.3, 6)
    L.ellipse(8, 12, 4, 3, '"', 0.2, 8)
    # cliffs framing the altar plateau
    L.rect(1, 1, 46, 2, 'c'); L.rect(1, 3, 12, 7, 'c'); L.rect(35, 3, 46, 7, 'c')
    # boss arena (stone floor) up north
    L.rect(14, 3, 33, 10, 'p')
    # road from the south gate to the arena
    L.path([(23, 31), (23, 24), (14, 20), (14, 14), (23, 12), (23, 10)], 'p', 2)
    L.path([(23, 24), (33, 20), (33, 14), (24, 12)], 'p', 2)
    # cursed pool
    L.ellipse(38, 30, 4, 2.2, 'w', 0.1, 9)
    L.E(23, 30, 'P')
    L.E(25, 29, 'S', 'LAS RUINAS MALDITAS. EL SEÑOR DEMONIO AGUARDA EN EL ALTAR DEL NORTE. DERRÓTALO PARA PURIFICAR EL BOSQUE.')
    # ruins & graves along the road
    for (x, y) in [(18, 27), (29, 27), (17, 17), (30, 17), (10, 21), (37, 19)]:
        L.E(x, y, 'R')
    for (x, y) in [(20, 25), (27, 25), (19, 15), (28, 15)]:
        L.E(x, y, 'I')
    for (x, y) in [(5, 29), (7, 30), (9, 29), (41, 15), (43, 16), (40, 17)]:
        L.E(x, y, 'G')
    for (x, y) in [(12, 25), (36, 25), (21, 20), (26, 20)]:
        L.E(x, y, 'O')
    # arena dressing: torches + obelisks around the boss
    for (x, y) in [(15, 4), (32, 4), (15, 9), (32, 9)]:
        L.E(x, y, 'L')
    L.E(18, 6, 'O'); L.E(29, 6, 'O')
    L.E(23, 6, 'B')
    # enemies
    for (x, y, c) in [(15, 27, 'd'), (31, 27, 'm'), (8, 22, 'o'), (39, 22, 'd'), (16, 18, 'm'), (31, 18, 'o'),
                      (12, 15, 'd'), (35, 14, 'm'), (23, 16, 'o'), (20, 12, 'd'), (27, 12, 'm')]:
        L.E(x, y, c)
    L.E(4, 18, 'C'); L.E(44, 28, 'C'); L.E(44, 10, 'C')
    L.E(23, 22, 'h'); L.E(6, 15, 'a'); L.E(42, 20, 'h')
    L.scatter('DDDr', 22, 21, spacing=3, allow=' ."')
    L.scatter('GMZn', 12, 22, spacing=2, allow=' .')
    L.scatter('vy', 10, 23, spacing=1, allow='."')
    L.scatter_top('DDr', 10, 24, spacing=2)
    return L


if __name__ == '__main__':
    out = sys.argv[1]
    for name, fn, title, sub in [('Level1_Forest', level1, 'EL BOSQUE SUSURRANTE', 'NIVEL 1'),
                                 ('Level2_Ruins', level2, 'LAS RUINAS MALDITAS', 'NIVEL 2')]:
        L = fn()
        problems, reach = L.check()
        L.dump(os.path.join(out, name + '.txt'), title, sub)
        print(name, 'reachable cells', reach, 'problems', problems)
