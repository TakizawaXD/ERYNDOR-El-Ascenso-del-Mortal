"""Splits the game into several loaded maps (2026-11-20).

World2.txt stays the overworld ("World" scene). Each town and the volcano get their own, bigger and more detailed map:
  City_Valle        ALDEA DEL VALLE     (start village, Valle Central)
  City_Ciudadela    CIUDADELA DEL REY   (walled royal city)
  City_Puerto       PUERTO DE LA COSTA  (harbour, docks, lighthouse)
  Zone_MonteCeniza  MONTE CENIZA        (volcano, lava fields, the Demon Lord)

Outputs (all under Assets/Game/Levels):
  Maps.txt          catalog read by the Unity builder and at runtime:
                      MAP  <id> <kind> <w> <h> <region> <title>|<subtitle>
                      AREA <id> <x0> <row0> <x1> <row1> <block>      footprint of a town/zone inside World (tile rect)
                      GATE <map> <gate> <cx> <cy> <w> <h> <ax> <ay> <fx> <fy> <toMap> <toGate>   (Unity units, y up)
  <id>.txt          same format as World2.txt + HOUSE x row template / NPC x row Class text lines

usage: python Tools/GameGen/maps.py <project root>
"""
import math, os, random, sys
from collections import deque

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LV = os.path.join(ROOT, 'Assets', 'Game', 'Levels')

BLOCK_T = set('wOcCLsk')
BLOCK_E = set('TUtAVuiIkYgGqrRW123456789#0JjxN!(|)@~X$CSF/*m^5')
# footprint of the big sprites (cells around the foot cell they cover): (left, right, up)
FOOT = {'6': (2, 2, 4), '7': (2, 2, 4), '8': (2, 2, 4), 'J': (2, 2, 6), '9': (1, 1, 6), '0': (1, 1, 5), 'j': (1, 1, 6),
        '#': (0, 1, 2), '@': (0, 1, 1), '$': (1, 1, 2), '5': (5, 5, 7), 'x': (1, 1, 7), 'N': (1, 1, 1), '!': (0, 0, 1),
        'T': (0, 0, 1), 'U': (0, 0, 1), 'A': (0, 0, 1), 'i': (0, 0, 1), 'Y': (0, 0, 1), '3': (1, 1, 1), 'R': (0, 1, 0),
        'C': (0, 0, 0)}


# ====================================================================== world
def load_world():
    L = open(os.path.join(LV, 'World2.txt'), encoding='utf-8').read().splitlines()
    t0, e0, r0 = L.index('TERRAIN'), L.index('ENTITIES'), L.index('REGIONS')
    T = L[t0 + 1:e0]
    E = L[e0 + 1:e0 + 1 + len(T)]
    return T, E


def detect_gates(T, rect):
    """road cells on the rect's border whose outside neighbour is open ground -> gates grouped per side"""
    x0, r0, x1, r1 = rect
    sides = {'N': [], 'S': [], 'W': [], 'E': []}
    for x in range(x0 + 1, x1):
        if T[r0][x] in '_p' and T[r0 - 1][x] not in BLOCK_T: sides['N'].append((x, r0))
        if T[r1][x] in '_p' and T[r1 + 1][x] not in BLOCK_T: sides['S'].append((x, r1))
    for r in range(r0 + 1, r1):
        if T[r][x0] in '_p' and T[r][x0 - 1] not in BLOCK_T: sides['W'].append((x0, r))
        if T[r][x1] in '_p' and T[r][x1 + 1] not in BLOCK_T: sides['E'].append((x1, r))
    gates = []
    for side, cells in sides.items():
        cells.sort(key=lambda c: (c[1], c[0]))
        groups = []
        for c in cells:
            k = 0 if side in 'NS' else 1
            if groups and abs(groups[-1][-1][k] - c[k]) == 1: groups[-1].append(c)
            else: groups.append([c])
        for i, g in enumerate(groups):
            gates.append((f'{side}{i}', side, g))
    return gates


def default_gate(m, gid):
    """a gate on a side the town layout did not plan for: 3 tiles in the middle of that side"""
    side = gid[0]
    mid = (m.w if side in 'NS' else m.h) // 2
    return side, mid - 1, mid + 1


def one_gate_per_side(gates):
    """keep the widest road crossing of each side (ids N0/S0/W0/E0) so every town map has a matching gate"""
    best = {}
    for (gid, side, cells) in gates:
        if side not in best or len(cells) > len(best[side][2]): best[side] = (side + '0', side, cells)
    return list(best.values())


# ====================================================================== map grid
class Map:
    def __init__(self, mid, w, h, region, base='.'):
        self.id, self.w, self.h, self.region = mid, w, h, region
        self.t = [[base] * w for _ in range(h)]
        self.e = [[None] * w for _ in range(h)]
        self.signs, self.houses, self.npcs, self.gates = [], [], [], []
        self.reserved = [[False] * w for _ in range(h)]       # roads, plazas and doors: keep clear of decor
        self.rng = random.Random(sum(map(ord, mid)))
        self.path_mat = '_'

    def inb(self, x, y): return 0 <= x < self.w and 0 <= y < self.h

    def T(self, x, y, c):
        if self.inb(x, y): self.t[y][x] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1): self.T(x, y, c)

    def blob(self, cx, cy, rx, ry, c, wob=0.25, seed=0, only=None):
        r = random.Random(seed)
        ph = [r.uniform(0, 6.28) for _ in range(4)]
        for y in range(int(cy - ry - 2), int(cy + ry + 3)):
            for x in range(int(cx - rx - 2), int(cx + rx + 3)):
                if not self.inb(x, y): continue
                a = math.atan2(y - cy, x - cx)
                k = 1 + wob * (0.6 * math.sin(3 * a + ph[0]) + 0.4 * math.sin(5 * a + ph[1]))
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= k * k and (only is None or self.t[y][x] in only):
                    self.t[y][x] = c

    def road(self, pts, width=2, mat='_', keep='p'):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(abs(x1 - x0), abs(y1 - y0), 1)
            for i in range(n + 1):
                x = round(x0 + (x1 - x0) * i / n); y = round(y0 + (y1 - y0) * i / n)
                for dy in range(-((width - 1) // 2), width // 2 + 1):
                    for dx in range(-((width - 1) // 2), width // 2 + 1):
                        xx, yy = x + dx, y + dy
                        if not self.inb(xx, yy): continue
                        if self.t[yy][xx] == 'w': self.t[yy][xx] = '=' if abs(x1 - x0) >= abs(y1 - y0) else 'H'
                        elif self.t[yy][xx] not in keep + '=HDO': self.t[yy][xx] = mat
                        self.reserved[yy][xx] = True
                        if self.e[yy][xx] in BLOCK_E: self.e[yy][xx] = None

    # ---------------------------------------------------------------- entities
    def covers(self, c, x, y):
        l, r, u = FOOT.get(c, (0, 0, 0))
        return [(xx, yy) for yy in range(y - u, y + 1) for xx in range(x - l, x + r + 1)]

    def can(self, c, x, y, margin=0, allow='._fFpadn'):
        for (xx, yy) in self.covers(c, x, y):
            for my in range(-margin, margin + 1):
                for mx in range(-margin, margin + 1):
                    a, b = xx + mx, yy + my
                    if not self.inb(a, b): return False
                    if self.e[b][a] is not None: return False
            if not self.inb(xx, yy) or self.t[yy][xx] not in allow or self.reserved[yy][xx]: return False
        return True

    def put(self, x, y, c, text=None, force=False):
        if not self.inb(x, y): return False
        if not force and self.e[y][x] is not None: return False
        self.e[y][x] = c
        for (xx, yy) in self.covers(c, x, y):
            if self.inb(xx, yy) and (xx, yy) != (x, y) and self.e[yy][xx] is None: self.e[yy][xx] = '.'   # occupied marker
        if c == 'S': self.signs.append((x, y, text or '...'))
        return True

    def house(self, x, y, c, template, door_to=None):
        """house with its front door at (x, y+1); a short path joins the door to the nearest road"""
        if not self.can(c, x, y, 1): return False
        self.put(x, y, c)
        self.houses.append((x, y, template))
        self.reserved[y + 1][x] = True
        self.connect(x, y + 1)
        return True

    def house_near(self, x, y, c, template, rad=7):
        for r_ in range(rad + 1):
            for dy in range(-r_, r_ + 1):
                for dx in range(-r_, r_ + 1):
                    if max(abs(dx), abs(dy)) == r_ and self.inb(x + dx, y + dy + 1) and self.house(x + dx, y + dy, c, template): return True
        print('  house blocked', self.id, x, y, template)
        return False

    def connect(self, x, y, mat='_'):
        """carve the shortest path from (x, y) to any road/plaza cell"""
        seen = {(x, y): None}; q = deque([(x, y)]); end = None
        while q:
            cx, cy = q.popleft()
            if self.t[cy][cx] in '_p=HD' and (cx, cy) != (x, y): end = (cx, cy); break
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = cx + dx, cy + dy
                if self.inb(nx, ny) and (nx, ny) not in seen and self.t[ny][nx] not in BLOCK_T and self.e[ny][nx] is None:
                    seen[(nx, ny)] = (cx, cy); q.append((nx, ny))
        c = seen.get(end) if end else None
        mat = self.path_mat
        while c is not None:
            for (a, b) in ((c[0], c[1]), (c[0] + 1, c[1])):          # two tiles wide
                if self.inb(a, b) and self.e[b][a] is None and self.t[b][a] not in BLOCK_T:
                    if self.t[b][a] not in 'p=HD': self.t[b][a] = mat
                    self.reserved[b][a] = True
            c = seen[c]

    def scatter(self, chars, n, allow, spacing=1, seed=0, area=None, avoid_reserved=True):
        r = random.Random(seed)
        x0, y0, x1, y1 = area or (0, 0, self.w - 1, self.h - 1)
        placed = tries = 0
        while placed < n and tries < n * 60:
            tries += 1
            x, y = r.randint(x0, x1), r.randint(y0, y1)
            c = r.choice(chars)
            if not self.inb(x, y) or self.t[y][x] not in allow: continue
            if avoid_reserved and any(self.reserved[b][a] for (a, b) in self.covers(c, x, y) if self.inb(a, b)): continue
            if not all(self.inb(a, b) and self.e[b][a] is None and self.t[b][a] not in BLOCK_T for (a, b) in self.covers(c, x, y)): continue
            if any(self.inb(x + dx, y + dy) and self.e[y + dy][x + dx] not in (None, '.')
                   for dy in range(-spacing, spacing + 1) for dx in range(-spacing, spacing + 1)): continue
            if avoid_reserved and any(self.inb(x + dx, y + 1 + dy) and self.reserved[y + 1 + dy][x + dx] for dy in (0,) for dx in (-1, 0, 1)) and c in FOOT:
                continue
            self.put(x, y, c); placed += 1
        return placed

    def npc(self, x, y, cls, text):
        self.npcs.append((x, y, cls, text)); self.reserved[y][x] = True

    def river(self, pts, width=2):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(abs(x1 - x0), abs(y1 - y0), 1)
            for i in range(n + 1):
                x = round(x0 + (x1 - x0) * i / n); y = round(y0 + (y1 - y0) * i / n)
                for d in range(width):
                    self.T(x + d, y, 'w')

    def gate(self, gid, side, a, b, to_map, to_gate, mat='_'):
        """gate on the map edge: side N/S covers columns a..b, side W/E covers rows a..b. Road leads inward."""
        self.gates.append((gid, side, a, b, to_map, to_gate))
        for k in range(a, b + 1):
            for d in range(3):
                x, y = {'N': (k, d), 'S': (k, self.h - 1 - d), 'W': (d, k), 'E': (self.w - 1 - d, k)}[side]
                if self.t[y][x] != 'p': self.t[y][x] = mat
                self.reserved[y][x] = True
                self.e[y][x] = None

    def gate_mid(self, g):
        gid, side, a, b, *_ = g
        m = (a + b) / 2
        return {'N': (m, 0), 'S': (m, self.h - 1), 'W': (0, m), 'E': (self.w - 1, m)}[side]

    def frame(self, depth, trees, terr='f', seed=0, density=0.75):
        """thick wooded frame around the map; gates keep their road open"""
        r = random.Random(seed)
        for y in range(self.h):
            for x in range(self.w):
                d = min(x, y, self.w - 1 - x, self.h - 1 - y)
                if d < depth and not self.reserved[y][x] and self.t[y][x] in '.': self.t[y][x] = terr
        cells = [(x, y) for y in range(self.h) for x in range(self.w) if min(x, y, self.w - 1 - x, self.h - 1 - y) < depth]
        r.shuffle(cells)
        for (x, y) in cells:
            if r.random() > density or self.reserved[y][x] or self.e[y][x] is not None or self.t[y][x] in BLOCK_T: continue
            c = r.choice(trees)
            if all(self.inb(a, b) and self.e[b][a] is None and not self.reserved[b][a] for (a, b) in self.covers(c, x, y)):
                self.put(x, y, c)

    # ---------------------------------------------------------------- checks + output
    def walkable(self, x, y):
        return self.inb(x, y) and self.t[y][x] not in BLOCK_T and (self.e[y][x] in (None, 'P', 'o', 'b', 'd', 'B', 'h', 'a', 'y', 'z', 'M', 'e', 'l', ';', 'Z', 'n')
                                                                   or (self.e[y][x] == '.' and False))

    def validate(self):
        gx, gy = self.gate_mid(self.gates[0])
        start = (int(gx), int(gy))
        seen = {start}; q = deque([start])
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n not in seen and self.walkable(*n): seen.add(n); q.append(n)
        bad = []
        for g in self.gates:
            mx, my = self.gate_mid(g)
            if (int(mx), int(my)) not in seen: bad.append(('gate', g[0]))
        for (x, y, t) in self.houses:
            if (x, y + 1) not in seen: bad.append(('door', t, x, y))
        for y in range(self.h):
            for x in range(self.w):
                c = self.e[y][x]
                if c in ('$', 'F', 'C', 'S') and not any((x + dx, y + dy) in seen for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))):
                    bad.append((c, x, y))
                if c in ('o', 'b', 'd', 'B', 'h', 'a', 'P') and (x, y) not in seen: bad.append((c, x, y))
        return bad, len(seen)

    def dump(self, title):
        with open(os.path.join(LV, self.id + '.txt'), 'w', encoding='utf-8') as f:
            f.write(f'TITLE {title}\nSUBTITLE \nSIZE {self.w} {self.h}\n')
            for (x, y, s) in self.signs: f.write(f'SIGN {x} {y} {s}\n')
            for (x, y, t) in self.houses: f.write(f'HOUSE {x} {y} {t}\n')
            for (x, y, c, s) in self.npcs: f.write(f'NPC {x} {y} {c} {s}\n')
            f.write('TERRAIN\n' + '\n'.join(''.join(r) for r in self.t) + '\n')
            ents = [''.join(c if c not in (None, '.') else ' ' for c in r) for r in self.e]
            f.write('ENTITIES\n' + '\n'.join(ents) + '\n')
            f.write('REGIONS\n' + '\n'.join(self.region * self.w for _ in range(self.h)) + '\n')
            f.write(f'REGIONNAME {self.region} {REGION_NAMES[self.region]}\n')


REGION_NAMES = {'a': 'VALLES DE VALTHERION', 'i': 'REINO DE VALTHERION', 'j': 'RUINAS ETERNAS', 'g': 'DRAKMOR, TIERRAS DE FUEGO'}


def gate_units(m, g):
    """trigger box, arrival point and facing (Unity units) for a gate on map m's edge"""
    gid, side, a, b, to_map, to_gate = g
    H, n = m.h, b - a + 1
    if side in 'NS':
        cx = a + n / 2
        cy = H - 0.5 if side == 'N' else 0.5
        return cx, cy, n, 1.0, cx, (cy - 2.2 if side == 'N' else cy + 2.0), ((0, -1) if side == 'N' else (0, 1))
    cx = 0.5 if side == 'W' else m.w - 0.5
    cy = H - (a + b + 1) / 2
    return cx, cy, 1.0, n, (cx + 2.0 if side == 'W' else cx - 2.0), cy - 0.3, ((1, 0) if side == 'W' else (-1, 0))


# ====================================================================== the towns
def valle(wg):
    """ALDEA DEL VALLE: farming village around a market square, wooden palisade, windmills, pond"""
    m = Map('City_Valle', 76, 58, 'a')
    W, H = m.w, m.h
    # gates (ids match the world's detected gates)
    pos = {'N0': ('N', 36, 38), 'W0': ('W', 33, 35), 'E0': ('E', 12, 14), 'E1': ('E', 45, 47)}
    for gid in wg:
        side, a, b = pos.get(gid) or default_gate(m, gid)
        m.gate(gid, side, a, b, 'World', gid)
    cx, cy = 38, 29
    # pond + stream
    m.blob(58, 31, 5, 3.5, 'w', 0.2, 3)
    m.river([(58, 35), (60, 40), (62, 45), (64, 52), (64, 57)], 2)
    # farmland north-west and south-east
    m.rect(8, 8, 22, 16, 'F'); m.rect(50, 44, 60, 51, 'F'); m.rect(10, 41, 20, 49, 'F')
    # square
    m.rect(cx - 8, cy - 5, cx + 8, cy + 5, 'p')
    for y in range(cy - 5, cy + 6):
        for x in range(cx - 8, cx + 9): m.reserved[y][x] = True
    # roads from every gate to the square
    m.road([(37, 0), (37, 10), (cx, cy - 5)], 3)
    m.road([(0, 34), (14, 34), (cx - 8, cy + 2)], 3)
    m.road([(W - 1, 13), (54, 13), (46, 18), (cx + 6, cy - 5)], 3)
    m.road([(W - 1, 46), (60, 42), (52, 38), (cx + 8, cy + 3)], 3)
    m.road([(cx, cy + 5), (cx, 44)], 2)                                           # south lane
    m.road([(cx - 8, cy - 3), (24, 20), (16, 18)], 2)                             # to the farms
    # the square
    for (x, y, c) in [(cx, cy, '@'), (cx - 4, cy + 2, 'F'), (cx + 5, cy - 3, '$'), (cx - 5, cy - 3, '$'),
                      (cx + 7, cy + 4, '|'), (cx - 7, cy + 4, '|'), (cx + 7, cy - 4, '|'), (cx - 7, cy - 4, '|'),
                      (cx + 3, cy + 4, '('), (cx + 4, cy + 4, ')'), (cx - 3, cy - 4, ')')]:
        m.put(x, y, c, force=True)
    m.put(cx + 2, cy + 3, 'S', 'ALDEA DEL VALLE. LOS CAMINOS LLEVAN AL MUNDO: NORTE A LA CIUDADELA, OESTE AL PUERTO, ESTE A LAS ARENAS Y AL PANTANO.', force=True)
    m.put(cx - 2, cy + 3, 'S', 'HOGUERAS: PULSA E PARA DESCANSAR Y GUARDAR. M ABRE EL MAPA (IZQUIERDA/DERECHA: MAPA LOCAL O DEL MUNDO).', force=True)
    m.put(cx, cy + 6, 'P', force=True)
    # houses (front doors face south)
    for (x, y, c, t) in [(26, 23, '7', 'herreria'), (50, 22, '6', 'casa'), (25, 40, '8', 'cabana'), (50, 39, '6', 'casa'),
                         (31, 51, '8', 'cabana'), (45, 52, '7', 'posada')]:
        m.house_near(x, y, c, t)
    # windmills by the fields
    m.put(12, 7, 'J', force=True); m.put(56, 43, 'J', force=True)
    # palisade with gaps for the roads
    for y in range(3, H - 3):
        for x in range(3, W - 3):
            edge = x in (3, W - 4) or y in (3, H - 4)
            if edge and not m.reserved[y][x] and m.t[y][x] not in BLOCK_T and m.e[y][x] is None and (x + y) % 1 == 0:
                m.put(x, y, '/')
    # torches at the palisade gates
    for g in m.gates:
        gid, side, a, b, *_ = g
        for k in (a - 1, b + 1):
            x, y = {'N': (k, 3), 'S': (k, H - 4), 'W': (3, k), 'E': (W - 4, k)}[side]
            if m.inb(x, y): m.e[y][x] = '|'
    m.frame(3, 'TTUti', 'f', 1, 0.8)
    # gardens, crops, props
    m.scatter(';', 60, 'F', 0, 5); m.scatter('*', 6, 'F', 1, 6)
    m.scatter('yzG', 70, '.', 1, 7, (5, 5, W - 6, H - 6))
    m.scatter('TUtA', 26, '.', 2, 8, (5, 5, W - 6, H - 6))
    m.scatter('g', 20, '.', 1, 9, (5, 5, W - 6, H - 6))
    m.scatter('le', 14, 'w', 0, 10, avoid_reserved=False)
    m.scatter('()', 8, '.', 1, 11, (18, 18, 58, 48))
    m.put(62, 18, 'C', force=True); m.put(15, 22, 'C', force=True)
    for (x, y, cls, text) in [(cx + 3, cy - 1, 'Soldier', 'VECINA: ¡BIENVENIDO A LA ALDEA! EL MERCADO ABRE CADA DÍA. SI SALES AL CAMINO, LLEVA POCIONES.'),
                              (cx - 6, cy + 1, 'KnightRanger', 'GRANJERO: LOS ORCOS ROBAN EL GRANO DE LOS MOLINOS. AL NORTE, EL CAMINO LLEVA A LA CIUDADELA DEL REY.'),
                              (20, 19, 'Soldier', 'NIÑO: ¿HAS VISTO EL MAPA? PULSA M. CON IZQUIERDA Y DERECHA CAMBIAS ENTRE LA ALDEA Y EL MUNDO.'),
                              (52, 33, 'KnightRanger', 'PESCADORA: EL ESTANQUE ES MI SITIO FAVORITO. DICEN QUE AL OESTE, EN EL PUERTO, HAY BARCOS DE TIERRAS LEJANAS.')]:
        m.npc(x, y, cls, text)
    return m


def ciudadela(wg):
    """CIUDADELA DEL REY: stone walls with towers, avenues, a central plaza, the king's keep, gardens"""
    m = Map('City_Ciudadela', 86, 66, 'i')
    m.path_mat = 'p'
    W, H = m.w, m.h
    pos = {'S0': ('S', 41, 44), 'N0': ('N', 42, 43), 'W0': ('W', 37, 39), 'E0': ('E', 37, 39)}
    for gid in wg:
        side, a, b = pos.get(gid) or default_gate(m, gid)
        m.gate(gid, side, a, b, 'World', gid)
    # green outside the walls, cobbled inside
    m.rect(5, 5, W - 6, H - 6, '.')
    cx, cy = 43, 38
    m.rect(cx - 9, cy - 6, cx + 9, cy + 6, 'p')                                   # plaza
    m.rect(cx - 2, 5, cx + 2, H - 6, 'p')                                         # north-south avenue
    m.rect(5, cy - 1, W - 6, cy + 1, 'p')                                         # east-west avenue
    for y in range(H):
        for x in range(W):
            if m.t[y][x] == 'p': m.reserved[y][x] = True
    # gates' roads through the green belt
    m.road([(42, 0), (42, 5)], 2, 'p'); m.road([(42, H - 1), (42, H - 6)], 4, 'p')
    m.road([(0, cy), (6, cy)], 3, 'p'); m.road([(W - 1, cy), (W - 7, cy)], 3, 'p')
    # outer walls (every 2 tiles) and towers, leaving the gates open
    free = lambda c, x, y: not any(m.reserved[b][a] for (a, b) in m.covers(c, x, y) if m.inb(a, b))
    for x in range(4, W - 4, 2):
        for y in (4, H - 5):
            if free('#', x, y): m.put(x, y, '#', force=True)
    for y in range(6, H - 4, 2):
        for x in (4, W - 5):
            if free('#', x, y) and free('#', x, y - 1) and free('#', x, y + 1): m.put(x, y, '#', force=True)
    for (x, y) in [(4, 4), (W - 5, 4), (4, H - 5), (W - 5, H - 5), (38, H - 5), (47, H - 5), (39, 4), (46, 4), (4, 44), (4, 52)]:
        if m.inb(x, y) and free('9', x, y): m.put(x, y, '9', force=True)
    # the king's keep: an inner bailey of towers and walls north of the plaza
    kx0, ky0, kx1, ky1 = 31, 8, 55, 22
    for x in range(kx0, kx1 + 1, 2):
        if free('#', x, ky0): m.put(x, ky0, '#', force=True)
        if free('#', x, ky1): m.put(x, ky1, '#', force=True)
    for y in range(ky0, ky1 + 1, 2):
        m.put(kx0, y, '#', force=True); m.put(kx1, y, '#', force=True)
    for (x, y) in [(kx0, ky0), (kx1, ky0), (kx0, ky1), (kx1, ky1), (36, 15), (50, 15)]:
        m.put(x, y, '9', force=True)
    m.rect(kx0 + 1, ky0 + 1, kx1 - 1, ky1 - 1, 'p')
    # houses around the plaza and in the quarters
    for (x, y, c, t) in [(16, 24, '7', 'cuartel'), (68, 24, '7', 'biblioteca'), (58, 33, '7', 'capilla'),
                         (68, 50, '6', 'herreria'), (28, 33, '8', 'casa'), (16, 50, '6', 'casa'), (28, 52, '7', 'posada')]:
        m.house_near(x, y, c, t)
    # plaza furniture
    for (x, y, c) in [(cx, cy + 3, 'F'), (cx - 6, cy - 4, '$'), (cx + 6, cy - 4, '$'), (cx + 5, cy + 4, '@'),
                      (cx - 8, cy + 5, '|'), (cx + 8, cy + 5, '|'), (cx - 8, cy - 5, '|'), (cx + 8, cy - 5, '|')]:
        m.put(x, y, c, force=True)
    m.put(cx - 3, cy + 5, 'S', 'CIUDADELA DEL REY. EL REY OFRECE ESTE REFUGIO A QUIEN COMBATA A LOS DEMONIOS. AQUÍ PUEDES COMERCIAR Y DESCANSAR.', force=True)
    m.put(44, H - 8, 'S', 'PUERTA DEL SUR. LA GUARDIA CIERRA LOS OJOS DE NOCHE: LOS CABALLEROS CAÍDOS RONDAN LAS MURALLAS.', force=True)
    # torches along the avenues
    for y in range(8, H - 8, 6):
        for x in (cx - 3, cx + 3):
            if m.e[y][x] is None and not (cy - 6 <= y <= cy + 6): m.put(x, y, '|')
    # gardens
    m.scatter('AAG', 24, '.', 2, 21, (6, 6, W - 7, H - 7))
    m.scatter('yzG', 70, '.', 1, 22, (6, 6, W - 7, H - 7))
    m.scatter('g', 14, '.', 1, 23, (6, 6, W - 7, H - 7))
    m.frame(4, 'TUA', 'f', 2, 0.45)
    m.put(70, 12, 'C', force=True); m.put(13, 59, 'C', force=True)
    for (x, y, cls, text) in [(cx - 3, cy - 2, 'KnightPaladin', 'HERALDO: EL REY BUSCA HÉROES. DOS GUARDIANES SOSTIENEN EL SELLO DEL MONTE CENIZA: EL JEFE ORCO Y LA MADRE DE SANGRE.'),
                              (40, H - 9, 'KnightPaladin', 'GUARDIA: ALTO, VIAJERO... ADELANTE. LA PLAZA ESTÁ AL NORTE. DE NOCHE NO TE ALEJES DE LAS ANTORCHAS.'),
                              (cx + 4, cy + 1, 'Soldier', 'MERCADERA: EL HERRERO DEL ESTE FORJA LAS MEJORES ESPADAS DEL REINO. TAMBIÉN HAY UNA CAPILLA JUNTO A LA PLAZA.'),
                              (43, 18, 'KnightDark', 'CHAMBELÁN: EL REY NO RECIBE A NADIE HASTA QUE CAIGA EL SEÑOR DEMONIO. VUELVE CON SU CABEZA.')]:
        m.npc(x, y, cls, text)
    return m


def puerto(wg):
    """PUERTO DE LA COSTA: harbour town on a bay, wooden docks with boats, a lighthouse, fish market"""
    m = Map('City_Puerto', 74, 54, 'j')
    W, H = m.w, m.h
    pos = {'W0': ('W', 26, 28), 'E0': ('E', 18, 20), 'N0': ('N', 40, 42)}
    for gid in wg:
        side, a, b = pos.get(gid) or default_gate(m, gid)
        m.gate(gid, side, a, b, 'World', gid)
    # sea and beach
    for x in range(W):
        shore = 36 + int(2 * math.sin(x * 0.21) + 1.5 * math.sin(x * 0.07 + 1))
        for y in range(shore, H): m.t[y][x] = 'O'
        for y in range(shore - 5, shore): m.t[y][x] = '_'
    for y in range(H):
        for x in range(W):
            if m.t[y][x] == '_' and m.e[y][x] is None: pass
    # docks
    for dx in (18, 46):
        for y in range(28, H - 4):
            for k in (0, 1):
                if m.t[y][dx + k] == 'O': m.t[y][dx + k] = 'D'
                m.reserved[y][dx + k] = True
    m.put(21, H - 6, '~', force=True); m.put(49, H - 8, '~', force=True); m.put(15, H - 9, '~', force=True)
    # lighthouse on the eastern point
    m.blob(66, 41, 5, 3, '_', 0.15, 4); m.blob(66, 40, 3, 2, '.', 0.1, 5)
    m.put(66, 40, 'j', force=True)
    # market square
    cx, cy = 36, 21
    m.rect(cx - 9, cy - 4, cx + 9, cy + 4, 'p')
    for y in range(cy - 4, cy + 5):
        for x in range(cx - 9, cx + 10): m.reserved[y][x] = True
    m.road([(0, 27), (14, 27), (cx - 9, cy + 2)], 3)
    m.road([(W - 1, 19), (cx + 9, cy - 1)], 3)
    if 'N0' in wg: m.road([(41, 0), (cx + 4, cy - 4)], 3)
    m.road([(cx - 6, cy + 4), (19, 30)], 2); m.road([(cx + 6, cy + 4), (47, 30)], 2)    # down to the docks
    for (x, y, c) in [(cx, cy - 2, 'F'), (cx - 6, cy - 2, '$'), (cx + 5, cy - 2, '$'), (cx + 8, cy + 3, '('), (cx + 7, cy + 3, ')'),
                      (cx - 8, cy + 3, ')'), (cx - 8, cy - 3, '|'), (cx + 8, cy - 3, '|'), (cx + 2, cy + 3, '@')]:
        m.put(x, y, c, force=True)
    m.put(cx - 2, cy + 3, 'S', 'PUERTO DE LA COSTA. LOS CORSARIOS ORCOS ACECHAN LAS PLAYAS AL ANOCHECER. EL FARO GUÍA A LOS BARCOS.', force=True)
    for (x, y, c, t) in [(14, 14, '7', 'posada'), (27, 12, '6', 'casa'), (50, 12, '8', 'cabana'), (61, 22, '7', 'herreria'), (10, 22, '8', 'casa')]:
        m.house_near(x, y, c, t)
    # cargo on the docks and the beach
    for (x, y, c) in [(20, 31, '('), (17, 31, ')'), (48, 31, '('), (45, 31, ')'), (45, 32, '(')]:
        if m.t[y][x] in '_.': m.put(x, y, c, force=True)
    m.frame(3, 'TUtY', 'f', 3, 0.6)
    m.scatter('Y', 18, '_', 2, 31)
    m.scatter('yzg', 40, '.', 1, 32, (4, 4, W - 5, 30))
    m.scatter('TU', 10, '.', 2, 33, (4, 4, W - 5, 26))
    m.put(57, 30, 'C', force=True); m.put(6, 8, 'C', force=True)
    for (x, y, cls, text) in [(cx + 3, cy, 'Soldier', 'PESCADOR: ¡PESCADO FRESCO! BUENO, AYER LO ESTABA. LOS ORCOS CORSARIOS NOS ROBAN LAS REDES.'),
                              (20, 33, 'KnightRanger', 'MARINERO: VENGO DEL DESIERTO DE LAS ARENAS ROJAS. ALLÍ EL JEFE ORCO TIENE SU FUERTE.'),
                              (64, 36, 'KnightDark', 'FARERA: CADA NOCHE ENCIENDO EL FARO. DESDE ARRIBA SE VE EL HUMO DEL MONTE CENIZA, AL ESTE.')]:
        m.npc(x, y, cls, text)
    return m


def ceniza():
    """MONTE CENIZA: ash fields, lava rivers with rock bridges, ruined shrines, the volcano and the Demon Lord"""
    m = Map('Zone_MonteCeniza', 80, 72, 'g', base='a')
    W, H = m.w, m.h
    m.gate('S0', 'S', 39, 41, 'World', 'S0', 'a')
    r = random.Random(11)
    # cliff frame with a ragged edge
    for y in range(H):
        for x in range(W):
            d = min(x, y, W - 1 - x, H - 1 - y)
            if d < 3 + int(1.5 + 1.5 * math.sin(x * 0.3 + y * 0.17)) and not m.reserved[y][x]: m.t[y][x] = 'k'
    # the volcano's crater ridge on top, the arena below it
    m.blob(40, 10, 16, 7, 'k', 0.1, 1)
    m.blob(40, 22, 13, 7, 'a', 0.12, 2)
    # lava: a river across the middle and lakes
    pts = [(3, 40), (16, 37), (28, 42), (40, 39), (52, 43), (64, 38), (77, 41)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n); y = round(y0 + (y1 - y0) * i / n)
            for dy in range(-2, 2):
                if m.inb(x, y + dy) and m.t[y + dy][x] == 'a': m.t[y + dy][x] = 'L'
    for (x, y, rx, ry) in [(18, 54, 5, 3), (62, 55, 6, 3.5), (14, 24, 4, 3), (66, 24, 5, 3), (52, 30, 3, 2)]:
        m.blob(x, y, rx, ry, 'L', 0.25, x + y, only='a')
    # the path: entrance -> camp -> rock bridges over the lava -> arena
    m.road([(40, H - 1), (40, 62), (30, 56), (28, 46), (24, 40), (26, 34), (34, 30), (40, 26)], 3, 'a', keep='')
    m.road([(40, 62), (52, 52), (56, 44), (58, 38), (50, 33), (42, 27)], 2, 'a', keep='')
    # entrance camp
    m.put(36, 62, 'F', force=True)
    m.put(44, 63, 'S', 'MONTE CENIZA. EL SEÑOR DEMONIO DUERME BAJO EL VOLCÁN. NO HAY VUELTA ATRÁS PARA QUIEN NO ESTÉ PREPARADO.', force=True)
    m.put(42, 64, '|', force=True); m.put(38, 64, '|', force=True)
    # volcano + Demon Lord + shrine pillars
    m.put(40, 14, '5', force=True)
    m.put(40, 22, 'B', force=True)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        x, y = int(40 + math.cos(a) * 10), int(22 + math.sin(a) * 5.5)
        if m.t[y][x] == 'a' and not m.reserved[y][x]: m.put(x, y, '!', force=True)
    for (x, y) in [(31, 26), (49, 26)]: m.put(x, y, '|', force=True)
    # ruins, rocks, dead trees
    m.scatter('NN!', 10, 'a', 2, 41, (6, 30, W - 7, H - 8))
    m.scatter('3R', 22, 'a', 2, 42, (5, 5, W - 6, H - 6))
    m.scatter('rk', 30, 'a', 1, 43, (5, 5, W - 6, H - 6))
    # treasure and monsters
    for (x, y) in [(12, 46), (68, 47), (62, 30), (16, 32)]:
        if m.t[y][x] == 'a' and m.e[y][x] is None: m.put(x, y, 'C')
    m.scatter('h', 4, 'a', 2, 44, (5, 30, W - 6, H - 8)); m.scatter('a', 3, 'a', 2, 45, (5, 30, W - 6, H - 8))
    m.scatter('dddb', 24, 'a', 2, 46, (5, 28, W - 6, 58), avoid_reserved=False)
    m.scatter('dd', 4, 'a', 2, 47, (28, 16, 52, 28), avoid_reserved=False)
    m.npc(46, 60, 'KnightRanger', 'EXPLORADORA: HE VISTO AL SEÑOR DEMONIO JUNTO AL CRÁTER. LANZA FUEGO DESDE LEJOS: ACÉRCATE Y RUEDA ENTRE SUS GOLPES.')
    return m


# ====================================================================== main
def main():
    T, E = load_world()
    WH, WW = len(T), len(T[0])
    import json
    meta_path = os.path.join(LV, 'World3.json')
    meta = json.load(open(meta_path, encoding='utf-8')) if os.path.exists(meta_path) else None
    if meta:   # ERYNDOR world (world3.py): town footprints come from the generator, gates are found on their borders
        tw = meta['towns']
        cities = [
            ('City_Valle', tuple(tw['City_Valle']), valle, 'ALDEA DEL VALLE|VALLES DE VALTHERION', []),
            ('City_Ciudadela', tuple(tw['City_Ciudadela']), ciudadela, 'CIUDADELA DE VALTHERION|CAPITAL DEL REINO', []),
            ('City_Puerto', tuple(tw['City_Puerto']), puerto, 'PUERTO DE LAS RUINAS|RUINAS ETERNAS', []),
        ]
    else:
        cities = [
            ('City_Valle', (104, 96, 142, 118), valle, 'ALDEA DEL VALLE|VALLE CENTRAL', []),
            ('City_Ciudadela', (148, 18, 178, 36), ciudadela, 'CIUDADELA DEL REY|CAPITAL DEL REINO',
             [('N0', 'N', [(x, 18) for x in range(162, 165)]), ('S0', 'S', [(x, 36) for x in range(161, 166)]),
              ('W0', 'W', [(148, r) for r in range(26, 35)]), ('E0', 'E', [(178, r) for r in range(26, 29)])]),
            ('City_Puerto', (40, 95, 58, 103), puerto, 'PUERTO DE LA COSTA|COSTA DEL PUERTO',
             [('W0', 'W', [(40, 100), (40, 101)]), ('E0', 'E', [(58, 99), (58, 100)])]),
        ]
    cat = [f'MAP World world {WW} {WH} a MUNDO|']
    worldgates = []
    maps = []
    for (mid, rect, fn, title, manual) in cities:
        gates = manual or one_gate_per_side(detect_gates(T, rect))
        print(mid, 'world gates', [(g[0], g[2][0], len(g[2])) for g in gates])
        m = fn([g[0] for g in gates])
        maps.append((m, title))
        cat.append(f'AREA {mid} {rect[0]} {rect[1]} {rect[2]} {rect[3]} 1')
        for (gid, side, cells) in gates:
            xs = [c[0] for c in cells]; rs = [c[1] for c in cells]
            x0, x1, r0, r1 = min(xs), max(xs), min(rs), max(rs)
            cx = (x0 + x1 + 1) / 2; cy = WH - (r0 + r1 + 1) / 2
            w, h = x1 - x0 + 1, r1 - r0 + 1
            out = {'N': (0, 1), 'S': (0, -1), 'W': (-1, 0), 'E': (1, 0)}[side]
            ax, ay = cx + out[0] * 1.8, cy + out[1] * 1.8 - (0.3 if side in 'WE' else 0)
            worldgates.append(f'GATE World {mid}:{gid} {cx} {cy} {w} {h} {ax} {ay} {out[0]} {out[1]} {mid} {gid}')
    # the volcano: the corridor right behind the seal (seal cells X in World2) leads into Monte Ceniza
    xs = [(x, r) for r in range(WH) for x in range(WW) if E[r][x] == 'X']
    sx = max(x for x, _ in xs); sr0 = min(r for _, r in xs); sr1 = max(r for _, r in xs)
    gx0, gx1, gr0, gr1 = sx + 1, sx + 2, sr0 - 1, sr1 + 2
    cx, cy = (gx0 + gx1 + 1) / 2, WH - (gr0 + gr1 + 1) / 2
    worldgates.append(f'GATE World Zone_MonteCeniza:S0 {cx} {cy} {gx1 - gx0 + 1} {gr1 - gr0 + 1} {sx - 3.5} {WH - (sr0 + sr1 + 1) / 2 - 0.3} -1 0 Zone_MonteCeniza S0')
    if meta and meta.get('seal'):
        vx, vy = meta['seal']['volcano']
        cat.append(f'AREA Zone_MonteCeniza {vx - 14} {vy - 9} {vx + 14} {vy + 10} 0')
    else:
        cat.append(f'AREA Zone_MonteCeniza {sx + 3} 76 234 99 0')
    # boss dungeons: the entrance (E) in the world leads to the dungeon's gate IN; the dungeon maps themselves are
    # written by the dungeon tools (Assets/Game/Levels/Dungeons.txt is merged below when it exists)
    if meta:
        for en in meta['entrances']:
            x, r = en['x'], en['row']
            cx, cy = x + 0.5, WH - r - 0.5 + 0.2
            worldgates.append(f"GATE World {en['map']}:IN {cx} {cy} 1.6 1.0 {cx} {cy - 1.5} 0 -1 {en['map']} IN")
    z = ceniza()
    maps.append((z, 'MONTE CENIZA|LA MORADA DEL SEÑOR DEMONIO'))

    for (m, title) in maps:
        bad, n = m.validate()
        print(m.id, f'{m.w}x{m.h}', 'reach', n, 'houses', len(m.houses), 'npcs', len(m.npcs), 'gates', [g[0] for g in m.gates], 'BAD' if bad else 'ok', bad[:8])
        kind = 'zone' if m.id.startswith('Zone') else 'city'
        cat.insert(1, f'MAP {m.id} {kind} {m.w} {m.h} {m.region} {title}')
        for g in m.gates:
            cx, cy, w, h, ax, ay, f = gate_units(m, g)
            cat.append(f'GATE {m.id} {g[0]} {cx} {cy} {w} {h} {ax} {ay} {f[0]} {f[1]} World {m.id}:{g[0]}')
        m.dump(title.split('|')[0])
    cat += worldgates
    extra = os.path.join(LV, 'Dungeons.txt')          # boss dungeons (MAP / GATE lines from the dungeon generator)
    if os.path.exists(extra):
        cat += [l for l in open(extra, encoding='utf-8').read().splitlines() if l.startswith(('MAP ', 'GATE ', 'AREA '))]
    with open(os.path.join(LV, 'Maps.txt'), 'w', encoding='utf-8') as f:
        f.write('# generated by Tools/GameGen/maps.py\n' + '\n'.join(cat) + '\n')
    print('wrote', len(maps), 'maps +', len(worldgates), 'world gates')


if __name__ == '__main__':
    main()
