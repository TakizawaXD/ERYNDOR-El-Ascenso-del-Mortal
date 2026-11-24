"""ONE SINGLE MAP (2026-11-21): merges every place of the game into the overworld grid.

  python Tools/GameGen/world3.py G:/Juegos        (the big 600x400 overworld with empty footprints)
  python Tools/GameGen/merge_world.py G:/Juegos   (this script)
  python Tools/ArtGen2/paint_world_merged.py      (paints the ground of the merged map)

What it does
  * stamps the towns (City_Valle, City_Ciudadela, City_Puerto) and Monte Ceniza into their footprints in World2.txt:
    terrain, entities, regions, signs, HOUSE and NPC lines - so walking into a town is just walking, no loading
  * joins every town gate to the overworld roads (a carved road, bridges over rivers, a cut through cliffs)
  * closes Monte Ceniza with cliffs: the only way in is its south gate, right behind the Seal of Drakmor
  * builds the UNDERGROUND to the right of the overworld (x >= SURFACE_W), in the same grid: LAS CATACUMBAS DEL REY
    OLVIDADO (Dungeon_Catacumbas.txt) and four generated caves, one behind each dungeon entrance of world3.py, each with
    its boss. The camera, the light and the map treat every cave like a big interior.
  * writes Maps.txt: one MAP (World) + SURFACE / TOWN / CAVE / MERGED lines + the gates (entrance <-> cave stairs)
  * writes Underground.txt: each cave's raw layout (catacomb alphabet + paint zone) for the ground painter

Extra lines in the merged World2.txt (read by the Unity builder):
  HOUSE x row template          NPC x row Class text          (from the town maps, in world cells)
  ENEMY Type x row [name]       a resident of the underground (prefab name; bosses included)
  PROP sprite x row [fps]       a prop from Assets/Art/World/Catacombs (cell coords, .5 = cell centre)
  LIGHT x row r g b radius      a coloured glow
"""
import heapq, json, math, os, random, sys
from collections import deque

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LV = os.path.join(ROOT, 'Assets', 'Game', 'Levels')
BLOCK_T = set('wOcCLsk')
BLOCK_E = set('TUtAVuiIkYgGqrRW123456789#0JjxN!(|)@~X$CSF/*m^5DHOEL')
TOWNS = ['City_Valle', 'City_Ciudadela', 'City_Puerto']
UNDER_X = 740                    # first column of the underground (overworld width + a rock strip)


# ====================================================================== io
def read_map(path):
    L = open(path, encoding='utf-8').read().splitlines()
    head = {'signs': [], 'houses': [], 'npcs': [], 'objs': [], 'rooms': [], 'names': {}}
    t0, e0, r0 = L.index('TERRAIN'), L.index('ENTITIES'), L.index('REGIONS')
    for l in L[:t0]:
        if l.startswith('SIZE '): head['w'], head['h'] = map(int, l.split()[1:3])
        elif l.startswith('TITLE '): head['title'] = l[6:]
        elif l.startswith('SUBTITLE '): head['subtitle'] = l[9:]
        elif l.startswith('SIGN '): p = l.split(' ', 3); head['signs'].append((int(p[1]), int(p[2]), p[3]))
        elif l.startswith('HOUSE '): p = l.split(' '); head['houses'].append((int(p[1]), int(p[2]), p[3]))
        elif l.startswith('NPC '): p = l.split(' ', 4); head['npcs'].append((int(p[1]), int(p[2]), p[3], p[4] if len(p) > 4 else ''))
        elif l.startswith('OBJ '):
            body, _, text = l.partition(' | ')
            p = body.split()
            kw = dict(q.split('=', 1) for q in p[4:] if '=' in q)
            head['objs'].append((p[1], float(p[2]), float(p[3]), kw, text))
        elif l.startswith('MERGED'): head['merged'] = True
    h = head.get('h', e0 - t0 - 1)
    head['T'] = [list(r) for r in L[t0 + 1:t0 + 1 + h]]
    head['E'] = [list(r) for r in L[e0 + 1:e0 + 1 + h]]
    head['R'] = [list(r) for r in L[r0 + 1:r0 + 1 + h]]
    for l in L[r0 + 1 + h:]:
        if l.startswith('REGIONNAME '): head['names'][l[11]] = l[13:]
    head['w'] = head.get('w', len(head['T'][0]))
    head['h'] = h
    return head


# ====================================================================== the grid
class Grid:
    def __init__(self, world, W, H):
        self.W, self.H = W, H
        self.t = [['k'] * W for _ in range(H)]
        self.e = [[' '] * W for _ in range(H)]
        self.r = [['-'] * W for _ in range(H)]
        for y in range(world['h']):
            for x in range(world['w']):
                self.t[y][x] = world['T'][y][x]
                self.e[y][x] = world['E'][y][x] if x < len(world['E'][y]) else ' '
                self.r[y][x] = world['R'][y][x]
        self.signs = [s for s in world['signs']]
        self.houses, self.npcs, self.extra = [], [], []
        self.names = dict(world['names'])

    def inb(self, x, y): return 0 <= x < self.W and 0 <= y < self.H

    def stamp(self, m, x0, y0, region=None):
        for y in range(m['h']):
            for x in range(m['w']):
                X, Y = x0 + x, y0 + y
                if not self.inb(X, Y): continue
                self.t[Y][X] = m['T'][y][x]
                self.e[Y][X] = m['E'][y][x] if x < len(m['E'][y]) else ' '
                self.r[Y][X] = region or m['R'][y][x]
        self.signs = [s for s in self.signs if not (x0 <= s[0] < x0 + m['w'] and y0 <= s[1] < y0 + m['h'])]
        self.signs += [(x + x0, y + y0, t) for (x, y, t) in m['signs']]
        self.houses += [(x + x0, y + y0, t) for (x, y, t) in m['houses']]
        self.npcs += [(x + x0, y + y0, c, t) for (x, y, c, t) in m['npcs']]
        for k, v in m['names'].items(): self.names.setdefault(k, v)

    def clear_blockers(self, x, y):
        if self.inb(x, y) and self.e[y][x] in BLOCK_E and self.e[y][x] not in 'X': self.e[y][x] = ' '

    # ------------------------------------------------------------------ roads from a town gate to the road network
    def connect(self, start, forbid, mat='_', max_cost=4000):
        """cheapest path from the cell outside a gate to any road cell of the overworld; carve it as a 2-wide road"""
        cost_of = {'w': 7, 'c': 5, 'C': 5, 'k': 6, 's': 6, 'L': 12, 'O': 60}
        dist = {start: 0}
        prev = {}
        pq = [(0, start)]
        goal = None
        while pq:
            d, (x, y) = heapq.heappop(pq)
            if d > dist.get((x, y), 1e9): continue
            if d > max_cost: break
            if (x, y) != start and self.t[y][x] in '_p=H' and not forbid(x, y) and d > 3:
                goal = (x, y); break
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (2 <= nx < UNDER_X - 4 and 2 <= ny < self.H - 2) or forbid(nx, ny): continue
                t = self.t[ny][nx]
                c = 0.4 if t in '_p=H' else cost_of.get(t, 1.0)
                if self.e[ny][nx] in BLOCK_E: c += 1.5
                nd = d + c
                if nd < dist.get((nx, ny), 1e9):
                    dist[(nx, ny)] = nd; prev[(nx, ny)] = (x, y); heapq.heappush(pq, (nd, (nx, ny)))
        if goal is None: return 0
        path = [goal]
        while path[-1] != start: path.append(prev[path[-1]])
        path.reverse()
        for i, (x, y) in enumerate(path):
            nxt = path[min(i + 1, len(path) - 1)]; prv = path[max(i - 1, 0)]
            horizontal = abs(nxt[0] - prv[0]) >= abs(nxt[1] - prv[1])
            cells = [(x, y), (x, y + 1)] if horizontal else [(x, y), (x + 1, y)]
            for (cx, cy) in cells:
                if not self.inb(cx, cy) or forbid(cx, cy): continue
                t = self.t[cy][cx]
                if t in '_p=H': pass
                elif t == 'w': self.t[cy][cx] = '=' if horizontal else 'H'
                elif t == 'O': self.t[cy][cx] = '=' if horizontal else 'H'
                else: self.t[cy][cx] = mat
                for yy in range(cy - 1, cy + 2):
                    for xx in range(cx - 1, cx + 2): self.clear_blockers(xx, yy)
        return len(path)

    def dump(self, path, header):
        out = list(header)
        out += [f'SIGN {x} {y} {t}' for (x, y, t) in self.signs]
        out += [f'HOUSE {x} {y} {t}' for (x, y, t) in self.houses]
        out += [f'NPC {x} {y} {c} {t}'.rstrip() for (x, y, c, t) in self.npcs]
        out += self.extra
        out.append('TERRAIN'); out += [''.join(r) for r in self.t]
        out.append('ENTITIES'); out += [''.join(r) for r in self.e]
        out.append('REGIONS'); out += [''.join(r) for r in self.r]
        out += [f'REGIONNAME {k} {v}' for k, v in sorted(self.names.items())]
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out) + '\n')


def border_openings(m):
    """road cells on the border of a town map, grouped: [(side, [(x, row), ...]), ...] in map cells"""
    W, H, T = m['w'], m['h'], m['T']
    sides = {'N': [(x, 0) for x in range(W)], 'S': [(x, H - 1) for x in range(W)],
             'W': [(0, y) for y in range(H)], 'E': [(W - 1, y) for y in range(H)]}
    out = []
    for side, cells in sides.items():
        group = []
        for (x, y) in cells + [(-9, -9)]:
            ok = x >= 0 and T[y][x] in '_p=H'
            if ok: group.append((x, y))
            elif group: out.append((side, group)); group = []
    return out


# ====================================================================== caves
THEMES = {
    # id: (title, region letter, paint zone, enemies, boss, deco props, tint)
    'Dungeon_Orco': ('FOSOS DE GUERRA ORCOS', 'q', 'l', ['Orc', 'Orc', 'OrcBerserker', 'GoblinAxe', 'GoblinViking', 'GoblinShaman'],
                     'K', ['crate_stack', 'barrel', 'barrel_broken', 'post_skull', 'armor_rack', 'rock', 'rubble'], (1.05, 0.95, 0.82)),
    'Dungeon_Escarcha': ('CRIPTA DE ESCARCHA', 'r', 'm', ['OrcFrost', 'OrcFrost', 'SkeletonWarrior', 'Skeleton', 'WolfWarrior'],
                         'FrostColossus', ['pillar_b', 'column_broken', 'rock', 'urn_green', 'sarcophagus_cracked', 'post_stone'], (0.78, 0.92, 1.18)),
    'Dungeon_Invocador': ('CATACUMBA DE LOS CONDENADOS', 's', 'k', ['Skeleton', 'SkeletonSpear', 'SkeletonAxe', 'ScytheCultist', 'Reaper'],
                          'Summoner', ['sarcophagus', 'sarcophagus_broken', 'coffin', 'coffin_open', 'post_chains', 'urn_red', 'pillar_a'], (0.95, 0.88, 1.08)),
    'Dungeon_Sangre': ('CRIPTA CARMESÍ', 't', 'p', ['BloodMonster', 'BloodToxic', 'Tentacle', 'Maw', 'Bat', 'BloodMonster'],
                       'Q', ['urn_red', 'urn_red_broken', 'post_chain', 'chains', 'pedestal', 'pillar_c', 'rubble'], (1.12, 0.8, 0.84)),
}
CAVE_W, CAVE_H = 100, 76

# caves only to explore (no boss): one per biome, treasure and a strong guardian at the bottom.
# id: (title, region letter, paint zone, enemies, guardian, props, tint, biome of the entrance, entrance kind)
EXPLORE = {
    'Cave_Lobos':     ('GUARIDA DE LOS LOBOS', 'u', 'l', ['Werewolf', 'WolfWarrior', 'Werewolf', 'Bat'], 'WolfWarrior',
                       ['rock', 'rubble', 'post_broken', 'barrel_broken'], (0.95, 1.0, 0.85), 'b', 'cave'),
    'Cave_Minas':     ('MINAS ABANDONADAS', 'v', 'l', ['GoblinAxe', 'Orc', 'GoblinShaman', 'Bat'], 'OrcBerserker',
                       ['crate_stack', 'barrel', 'barrel_broken', 'post_plain', 'rock', 'chain'], (1.05, 0.97, 0.88), 'a', 'cave'),
    'Cave_Gruta':     ('GRUTA DEL LAGO SAGRADO', 'w', 'm', ['SlimeGreen', 'EyeWatcher', 'SlimeGreen', 'Skeleton'], 'ShieldBrute',
                       ['pillar_b', 'urn_green', 'pedestal', 'rock', 'column_broken'], (0.85, 1.0, 1.1), 'c', 'cave'),
    'Crypt_Real':     ('CRIPTA REAL DE VALTHERION', 'x', 'k', ['Skeleton', 'SkeletonWarrior', 'SkeletonSpear', 'Reaper'], 'KnightFallen',
                       ['sarcophagus', 'sarcophagus_cracked', 'coffin', 'pillar_a', 'urn_red', 'post_stone'], (0.98, 0.95, 1.05), 'i', 'crypt'),
    'Cave_Helada':    ('CAVERNA DE HIELO ETERNO', 'y', 'm', ['OrcFrost', 'WolfWarrior', 'OrcFrost'], 'Minotaur',
                       ['rock', 'pillar_d', 'column_broken', 'urn_green_s'], (0.75, 0.9, 1.2), 'e', 'cave'),
    'Crypt_Arena':    ('TUMBAS BAJO LA ARENA', 'z', 'n', ['Skeleton', 'SkeletonAxe', 'ImpTrident', 'Skeleton'], 'Minotaur',
                       ['sarcophagus_broken', 'urn_red_s', 'pillar_c', 'pedestal_b', 'rubble'], (1.12, 0.98, 0.78), 'f', 'crypt'),
    'Cave_Magma':     ('GRIETA DE MAGMA', 'A', 'p', ['FireSlug', 'FlameSkull', 'Hellhound', 'ImpBlade'], 'LavaGolem',
                       ['rock', 'rubble', 'brazier_hanging', 'post_skull'], (1.15, 0.82, 0.7), 'g', 'cave'),
    'Cave_Corsarios': ('CUEVA DE LOS CORSARIOS', 'B', 'l', ['OrcCorsair', 'GoblinViking', 'ImpCrossbow', 'OrcCorsair'], 'OrcCorsair',
                       ['barrel', 'crate_stack', 'barrel_s', 'chains', 'post_chain'], (0.9, 1.0, 1.08), 'j', 'cave'),
}


def gen_cave(mid, seed):
    """organic cave: rooms joined by winding tunnels, smoothed by a cellular automaton; stairs at the bottom room,
    the boss chamber at the top. Returns dict like read_map() + objs/enemies in cave cells."""
    title, region, zone, enemies, boss, props, tint = THEMES[mid] if mid in THEMES else EXPLORE[mid][:7]
    explore = mid in EXPLORE
    rnd = random.Random(seed)
    W, H = CAVE_W, CAVE_H
    T = [['#'] * W for _ in range(H)]

    def ell(cx, cy, rx, ry, c='.'):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if 2 <= x < W - 2 and 2 <= y < H - 2:
                    q = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                    if q <= 1 + rnd.uniform(-0.15, 0.12): T[y][x] = c

    def tunnel(a, b, width):
        (x, y), (tx, ty) = a, b
        steps = 0
        while (abs(x - tx) > 1 or abs(y - ty) > 1) and steps < 900:
            steps += 1
            dx, dy = tx - x, ty - y
            if rnd.random() < 0.65:
                if abs(dx) > abs(dy): x += 1 if dx > 0 else -1
                else: y += 1 if dy > 0 else -1
            else:
                if rnd.random() < 0.5: x += rnd.choice((-1, 1))
                else: y += rnd.choice((-1, 1))
            x = max(3, min(W - 4, x)); y = max(3, min(H - 4, y))
            for yy in range(y - width // 2, y + (width + 1) // 2 + 1):
                for xx in range(x - width // 2, x + (width + 1) // 2 + 1):
                    if 2 <= xx < W - 2 and 2 <= yy < H - 2: T[yy][xx] = '.'

    # rooms: entrance (bottom), boss (top), side chambers in between
    entry = (W // 2 + rnd.randint(-6, 6), H - 10)
    bossc = (W // 2 + rnd.randint(-10, 10), 13)
    rooms = [entry]
    for k in range(9):
        for _ in range(40):
            c = (rnd.randint(12, W - 13), rnd.randint(24, H - 18))
            if all(abs(c[0] - r[0]) + abs(c[1] - r[1]) > 18 for r in rooms): rooms.append(c); break
    ell(*entry, 7, 5)
    ell(*bossc, 14, 9)
    sizes = {}
    for c in rooms[1:]:
        rx, ry = rnd.uniform(5, 9), rnd.uniform(4, 6.5); sizes[c] = (rx, ry)
        ell(*c, rx, ry)
    # tunnels: a chain bottom -> top through the rooms (nearest-neighbour order), plus a couple of loops
    order = [entry]
    left = rooms[1:]
    while left:
        nxt = min(left, key=lambda r: (r[0] - order[-1][0]) ** 2 + (r[1] - order[-1][1]) ** 2 * 1.6)
        order.append(nxt); left.remove(nxt)
    order.append(bossc)
    for a, b in zip(order, order[1:]): tunnel(a, b, rnd.choice((2, 3)))
    for _ in range(3):
        a, b = rnd.sample(order[:-1], 2); tunnel(a, b, 2)
    # cellular smoothing (organic walls), then re-carve the room cores so nothing important closes
    for it in range(3):
        N = [row[:] for row in T]
        for y in range(2, H - 2):
            for x in range(2, W - 2):
                walls = sum(T[y + j][x + i] == '#' for j in (-1, 0, 1) for i in (-1, 0, 1))
                if T[y][x] == '#' and walls <= 3: N[y][x] = '.'
                elif T[y][x] == '.' and walls >= 6: N[y][x] = '#'
        T = N
    for c in rooms[1:]:
        rx, ry = sizes[c]
        for y in range(int(c[1] - ry * .6), int(c[1] + ry * .6) + 1):
            for x in range(int(c[0] - rx * .6), int(c[0] + rx * .6) + 1): T[y][x] = '.'
    for y in range(bossc[1] - 7, bossc[1] + 8):
        for x in range(bossc[0] - 12, bossc[0] + 13):
            if ((x - bossc[0]) / 12.5) ** 2 + ((y - bossc[1]) / 7.6) ** 2 <= 1: T[y][x] = '.'
    for y in range(entry[1] - 3, entry[1] + 4):
        for x in range(entry[0] - 5, entry[0] + 6): T[y][x] = '.'
    # rubble floor patches
    for _ in range(26):
        cx, cy = rnd.randint(4, W - 5), rnd.randint(4, H - 5)
        for y in range(cy - 3, cy + 4):
            for x in range(cx - 4, cx + 5):
                if T[y][x] == '.' and rnd.random() < 0.6: T[y][x] = ','
    # stairs: a notch in the wall under the entrance room (the way back up)
    sx, sy = entry[0], entry[1] + 4
    while sy < H - 3 and T[sy][sx] != '#': sy += 1
    for x in (sx - 1, sx, sx + 1): T[sy][x] = 's'
    for x in (sx - 1, sx, sx + 1):
        for y in range(entry[1], sy): T[y][x] = '.'

    def reach():
        seen = {(sx, sy - 1)}; dq = deque(seen)
        while dq:
            x, y = dq.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if 0 <= n[0] < W and 0 <= n[1] < H and n not in seen and T[n[1]][n[0]] in '.,s':
                    seen.add(n); dq.append(n)
        return seen
    # chasms: a few pits in big chambers, kept only if everything stays connected
    base = len(reach())
    for c in rnd.sample(rooms[1:], min(4, len(rooms) - 1)):
        rx, ry = sizes[c]
        px, py = int(c[0] + rnd.choice((-1, 1)) * rx * .45), int(c[1] + rnd.choice((-1, 1)) * ry * .3)
        changed = []
        for y in range(py - 1, py + 2):
            for x in range(px - 2, px + 3):
                if T[y][x] in '.,' and rnd.random() < 0.85: changed.append((x, y)); T[y][x] = 'O'
        if len(reach()) < base - len(changed) - 2 or (bossc[0], bossc[1]) not in reach():
            for (x, y) in changed: T[y][x] = '.'
    seen = reach()
    for y in range(H):                      # pockets the smoothing cut off become wall
        for x in range(W):
            if T[y][x] in '.,' and (x, y) not in seen: T[y][x] = '#'
    assert (bossc[0], bossc[1]) in seen, mid + ': boss chamber unreachable'

    # ---- dressing (cells of this cave)
    E = [[' '] * W for _ in range(H)]
    objs, ens, used = [], [], set()

    def floor(x, y): return 0 <= x < W and 0 <= y < H and T[y][x] in '.,'
    def near_wall(x, y): return any(T[y + j][x + i] == '#' for j in (-1, 0, 1) for i in (-1, 0, 1))
    def free(x, y, rad=1): return floor(x, y) and all((x + i, y + j) not in used for j in range(-rad, rad + 1) for i in range(-rad, rad + 1))

    def put(x, y, c):
        E[y][x] = c; used.add((x, y))
    cells = [(x, y) for y in range(3, H - 3) for x in range(3, W - 3) if floor(x, y)]
    rnd.shuffle(cells)
    in_boss = lambda x, y: ((x - bossc[0]) / 13) ** 2 + ((y - bossc[1]) / 8.5) ** 2 <= 1
    in_entry = lambda x, y: abs(x - entry[0]) <= 7 and abs(y - entry[1]) <= 6
    # torches along the walls (the only light down here)
    n = 0
    for (x, y) in cells:
        if n >= 34: break
        if near_wall(x, y) and free(x, y, 4) and not in_boss(x, y):
            objs.append(('PROP', 'torch_anim_16x16', x + .5, y + .5, 8)); used.add((x, y)); n += 1
    # chests in the side chambers (away from the entrance), potions, arrows
    for c in rooms[1:]:
        if rnd.random() < 0.55:
            for (x, y) in cells:
                if abs(x - c[0]) <= 4 and abs(y - c[1]) <= 3 and free(x, y, 1): put(x, y, 'C'); break
    for ch, k in (('h', 6), ('a', 4)):
        m = 0
        for (x, y) in cells:
            if m >= k: break
            if free(x, y, 2) and not in_entry(x, y): put(x, y, ch); m += 1
    # props by theme
    m = 0
    for (x, y) in cells:
        if m >= 46: break
        if near_wall(x, y) and free(x, y, 2) and not in_boss(x, y) and not in_entry(x, y):
            objs.append(('PROP', rnd.choice(props), x + .5, y + .9, 0)); used.add((x, y)); m += 1
    # enemies: packs in the chambers, guards along the tunnels; the boss in the top chamber
    for c in rooms[1:]:
        for _ in range(rnd.randint(2, 3)):
            for (x, y) in cells:
                if abs(x - c[0]) <= 5 and abs(y - c[1]) <= 4 and free(x, y, 1):
                    ens.append((rnd.choice(enemies), x, y)); used.add((x, y)); break
    g = 0
    for (x, y) in cells:
        if g >= 8: break
        if free(x, y, 3) and not in_entry(x, y) and not in_boss(x, y): ens.append((rnd.choice(enemies), x, y)); used.add((x, y)); g += 1
    boss_cell = (bossc[0], bossc[1] - 2)
    if explore:                                   # no boss: a strong guardian over a hoard of chests
        ens.append((boss, boss_cell[0], boss_cell[1], 'GUARDIÁN DE ' + title))
        for dx in (-3, 3):
            if floor(bossc[0] + dx, bossc[1] - 4) and (bossc[0] + dx, bossc[1] - 4) not in used: put(bossc[0] + dx, bossc[1] - 4, 'C')
    elif len(boss) == 1: E[boss_cell[1]][boss_cell[0]] = boss
    else: ens.append((boss, boss_cell[0], boss_cell[1]))
    # the boss's reward chest behind him + braziers flanking the chamber
    put(bossc[0], bossc[1] - 6 if floor(bossc[0], bossc[1] - 6) else bossc[1] - 4, 'C')
    for dx in (-9, 9):
        if floor(bossc[0] + dx, bossc[1]): objs.append(('PROP', 'brazier', bossc[0] + dx + .5, bossc[1] + .9, 0))
    objs.append(('PROP', 'stairs_arch', sx + .5, sy + 1.0, 0))
    sign_at = (entry[0] + 3, entry[1] - 2)
    if floor(*sign_at): put(*sign_at, 'S')
    return {'id': mid, 'title': title, 'w': W, 'h': H, 'T': T, 'E': E, 'R': [[region] * W for _ in range(H)], 'zone': zone,
            'tint': tint, 'props': objs, 'enemies': ens, 'stairs': (sx, sy), 'sign': sign_at, 'names': {region: title}}


CRYPT_ENEMY = {'Skeleton': 'Skeleton', 'CryptGuard': 'SkeletonWarrior', 'BuriedArcher': 'SkeletonSpear', 'CursedKnight': 'KnightFallen',
               'FuneralPriest': 'ScytheCultist', 'CryptShade': 'Reaper', 'Bat': 'Bat', 'KingSepulcher': 'KnightFallen'}


def catacombs(path):
    """LAS CATACUMBAS DEL REY OLVIDADO (Tools/GameGen/catacombs.py): its layout and the objects the world builder can
    show (chests, enemies, signs, torches, candles, braziers, sarcophagi, pillars, the throne). Doors, levers and traps
    of the old dungeon map are left open / out: the passages stay walkable."""
    m = read_map(path)
    W, H = m['w'], m['h']
    E = [[' '] * W for _ in range(H)]
    props, ens, signs = [], [], []
    stairs = {}
    for (kind, x, y, kw, text) in m['objs']:
        cx, cy = int(x), int(y)
        if kind == 'chest' or kind == 'relic' or kind == 'key': E[cy][cx] = 'C'
        elif kind == 'enemy' or kind == 'boss':
            ens.append((CRYPT_ENEMY.get(kw.get('type', ''), 'Skeleton'), cx, cy, 'EL REY SEPULTADO' if kind == 'boss' else ''))
        elif kind in ('sign', 'lore'):
            if 0 <= cy < H and T_ok(m, cx, cy): E[cy][cx] = 'S'; signs.append((cx, cy, (text or kw.get('text', '...')).replace('_', ' ')))
        elif kind == 'torch': props.append(('PROP', 'torch_anim_16x16', x, y, 8))
        elif kind in ('candle', 'candles'): props.append(('PROP', 'candleA_anim_8x16' if kind == 'candle' else 'candleB_anim_14x16', x, y, 7))
        elif kind == 'brazier': props.append(('PROP', 'brazier', x, y, 0))
        elif kind == 'deco':
            spr = {'skeleton_post': 'post_skull', 'sarcophagus_open': 'coffin_open'}.get(kw.get('sprite', 'coffin'), kw.get('sprite', 'coffin'))
            props.append(('PROP', spr, x, y, 0))
        elif kind == 'pillar': props.append(('PROP', 'pillar_' + 'abcd'[int(x * 7 + y) % 4], x, y, 0))
        elif kind == 'column': props.append(('PROP', 'column_broken', x, y, 0))
        elif kind == 'breakable': props.append(('PROP', ['urn_green', 'urn_red', 'barrel'][int(x + y) % 3], x, y, 0))
        elif kind == 'throne': props.append(('PROP', 'throne', x, y, 0))
        elif kind in ('altar', 'altarstone'): props.append(('PROP', 'pedestal', x, y, 0))
        elif kind == 'spikes': props.append(('PROP', 'spike_anim_14x14', x, y, 6))
        elif kind == 'stairs':
            stairs[kw.get('gate', 'E0')] = (x, y)
            props.append(('PROP', 'stairs_arch', x, y + 0.6, 0))
    m['E'] = E
    m['props'] = props; m['enemies'] = ens; m['signs'] = signs; m['stairs'] = stairs
    m['zone'] = None
    return m


def T_ok(m, x, y): return 0 <= x < m['w'] and 0 <= y < m['h'] and m['T'][y][x] != '#'


def to_world_terrain(c):
    if c == '#': return 'k'
    if c == 'O': return 'c'          # pits: solid, painted as an abyss
    if c == '=': return '='
    return 'p'                       # every floor kind: stone (footsteps, spawns)



# ====================================================================== biome life
# every region has its own creatures (prefab names); the old generic residents (o / b / d) become these
ROSTER = {
    'a': ['Orc', 'GoblinAxe', 'GoblinRider', 'SlimeGreen', 'GoblinAxe'],                 # Valles de Valtherion
    'b': ['Werewolf', 'WolfWarrior', 'GoblinShaman', 'GoblinAxe', 'SlimeGreen'],          # Bosque Eterno de Eldoria
    'c': ['Skeleton', 'SkeletonSpear', 'EyeWatcher', 'ShieldBrute'],                       # Aurelith (ruin guardians)
    'd': ['BloodMonster', 'Tentacle', 'Maw', 'ScytheCultist', 'Bat', 'BloodToxic'],        # Noxheim, tierras de sombras
    'e': ['OrcFrost', 'WolfWarrior', 'Werewolf', 'Minotaur', 'OrcFrost'],                  # Valgrimm
    'f': ['OrcDesert', 'Minotaur', 'ImpTrident', 'FireSlug', 'Skeleton'],                  # Desierto de los Antiguos
    'g': ['LavaGolem', 'FireSlug', 'FlameSkull', 'Hellhound', 'DemonAsh', 'ImpBlade'],     # Drakmor
    'h': ['Demon', 'DemonAxe', 'DemonGreat', 'EyeWatcher', 'HellBat', 'ImpChain', 'DarkSpearman'],  # La Torre Prohibida
    'i': ['DarkSpearman', 'ShieldBrute', 'GoblinRider', 'Orc'],                            # Reino de Valtherion
    'j': ['OrcCorsair', 'GoblinViking', 'SkeletonAxe', 'ImpCrossbow', 'OrcCorsair'],       # Ruinas Eternas
}
# townsfolk drawn with the player's knight sprites get their own characters instead
NPC_LOOK = {'Soldier': ['HeroSoldier', 'HeroSwordswoman'], 'KnightPaladin': ['HeroCrusader', 'HeroPriestess'],
            'KnightRanger': ['HeroRanger', 'HeroSwordswoman'], 'KnightDark': ['HeroAxeKnight', 'HeroWizard']}
TALL = set('S|FCE@$X')
# a torch or a sign never stands against these (trees, bushes, fences, walls, buildings, other tall props)
CROWD = TALL | set('TUtAVuiIkYgGqRW/#0123456789Jjx!N(*)')


def biome_life(G, SW, SH, towns):
    rnd = random.Random(77)
    n = 0
    for y in range(SH):
        for x in range(SW):
            if G.e[y][x] not in 'obd': continue
            if any(x0 <= x <= x1 and y0 <= y <= y1 for (x0, y0, x1, y1) in towns): continue
            roster = ROSTER.get(G.r[y][x])
            if not roster: continue
            G.e[y][x] = ' '
            G.extra.append(f'ENEMY {rnd.choice(roster)} {x} {y}')
            n += 1
    for i, (x, y, c, t) in enumerate(G.npcs):
        if c in NPC_LOOK: G.npcs[i] = (x, y, NPC_LOOK[c][i % 2], t)
    return n


def separate(G, SW, SH):
    """two tall things never share a spot: a sign or a torch next to a bonfire, chest or entrance moves away"""
    moved = 0
    for y in range(1, G.H - 1):
        for x in range(1, G.W - 1):
            c = G.e[y][x]
            if c not in 'S|': continue
            clash = any(G.e[y + j][x + i] in CROWD for j in (-1, 0, 1) for i in (-1, 0, 1) if (i, j) != (0, 0))
            if not clash: continue
            spot = None
            for r in range(2, 5):
                for j in range(-r, r + 1):
                    for i in range(-r, r + 1):
                        X, Y = x + i, y + j
                        if not G.inb(X, Y) or G.e[Y][X] != ' ' or G.t[Y][X] in BLOCK_T: continue
                        if any(G.inb(X + a, Y + b) and G.e[Y + b][X + a] in CROWD for b in (-1, 0, 1) for a in (-1, 0, 1)): continue
                        spot = (X, Y); break
                    if spot: break
                if spot: break
            G.e[y][x] = ' '
            if spot:
                G.e[spot[1]][spot[0]] = c
                G.signs = [(spot[0], spot[1], t) if (sx, sy) == (x, y) else (sx, sy, t) for (sx, sy, t) in G.signs]
            moved += 1
    return moved


# ====================================================================== main
def main():
    w2 = os.path.join(LV, 'World2.txt')
    world = read_map(w2)
    if world.get('merged'):
        raise SystemExit('World2.txt is already merged: run Tools/GameGen/world3.py first')
    meta = json.load(open(os.path.join(LV, 'World3.json'), encoding='utf-8'))
    SW, SH = world['w'], world['h']
    WT, HT = UNDER_X + 460, max(SH, 360)
    G = Grid(world, WT, HT)
    for y in range(SH):                                     # the strip between the overworld and the underground
        for x in range(SW, WT): G.t[y][x] = 'k'; G.r[y][x] = '-'

    cat = []
    rects = []
    # ---------------------------------------------------------------- towns + Monte Ceniza
    for mid in TOWNS:
        x0, y0, x1, y1 = meta['towns'][mid]
        m = read_map(os.path.join(LV, mid + '.txt'))
        assert (x1 - x0 + 1, y1 - y0 + 1) == (m['w'], m['h']), (mid, m['w'], m['h'], (x0, y0, x1, y1))
        for y in range(y0, y1 + 1):                          # world start marks inside a town: the town brings its own
            for x in range(x0, x1 + 1): G.e[y][x] = ' '
        G.stamp(m, x0, y0)
        rects.append((mid, x0, y0, x1, y1, m))
        cat.append(f"TOWN {mid} {x0} {y0} {x1} {y1} {m['title']}|{m.get('subtitle', '')}")
        cat.append(f"MERGED {mid} {x0} {HT - y0 - m['h']}")
    zx0, zy0, zx1, zy1 = meta['zone']['rect']
    z = read_map(os.path.join(LV, 'Zone_MonteCeniza.txt'))
    assert (zx1 - zx0 + 1, zy1 - zy0 + 1) == (z['w'], z['h'])
    G.stamp(z, zx0, zy0)
    cat.append(f"ZONE Zone_MonteCeniza {zx0} {zy0} {zx1} {zy1} {z['title']}|{z.get('subtitle', '')}")
    cat.append(f"MERGED Zone_MonteCeniza {zx0} {HT - zy0 - z['h']}")
    # the zone is closed by cliffs; its south gate is 2 cells wide and the seal fills it
    sx, sy = meta['seal']['x'], meta['seal']['row']
    for x in range(zx0, zx1 + 1):
        if G.t[zy1][x] not in BLOCK_T and x not in (sx, sx + 1): G.t[zy1][x] = 'k'
    for x in range(zx0 - 1, zx1 + 2):
        for y in (zy0 - 1, zy1 + 1):
            if G.inb(x, y) and x not in (sx, sx + 1): G.t[y][x] = 'k'; G.clear_blockers(x, y)
    for y in range(zy0 - 1, zy1 + 2):
        for x in (zx0 - 1, zx1 + 1): G.t[y][x] = 'k'; G.clear_blockers(x, y)
    for y in range(zy1 + 1, zy1 + 4):
        for x in range(sx - 4, sx + 6):
            if x not in (sx, sx + 1): G.t[y][x] = 'k'; G.clear_blockers(x, y)
            else: G.t[y][x] = 'a'
    for (dx, dy) in [(0, 0), (0, 1), (1, 0), (1, 1)]: G.e[sy + dy][sx + dx] = 'X'

    # ---------------------------------------------------------------- town gates -> roads
    def forbid_for(own):
        def f(x, y):
            if zx0 - 1 <= x <= zx1 + 1 and zy0 - 1 <= y <= zy1 + 1: return True
            for (mid, x0, y0, x1, y1, _) in rects:
                if x0 <= x <= x1 and y0 <= y <= y1: return True
            return False
        return f
    for (mid, x0, y0, x1, y1, m) in rects:
        for side, cells in border_openings(m):
            cx, cy = cells[len(cells) // 2]
            out = {'N': (0, -1), 'S': (0, 1), 'W': (-1, 0), 'E': (1, 0)}[side]
            start = (x0 + cx + out[0], y0 + cy + out[1])
            if not G.inb(*start) or G.t[start[1]][start[0]] == 'O': continue
            for (gx, gy) in cells:                                   # the cells right outside the opening
                X, Y = x0 + gx + out[0], y0 + gy + out[1]
                if G.inb(X, Y) and G.t[Y][X] not in 'O': G.t[Y][X] = '_' if G.t[Y][X] not in 'wH=' else G.t[Y][X]; G.clear_blockers(X, Y)
            n = G.connect(start, forbid_for(mid), 'p' if mid == 'City_Ciudadela' else '_')
            print(f'  {mid} gate {side} at {start}: road {n} cells')

    # ---------------------------------------------------------------- underground
    caves = []
    cat_m = catacombs(os.path.join(LV, 'Dungeon_Catacumbas.txt'))
    slots = [(UNDER_X, 6), (UNDER_X, 150), (UNDER_X + 112, 150), (UNDER_X, 238), (UNDER_X + 112, 238)]
    cave_maps = [('Dungeon_ReySepultado', cat_m)]
    for k, mid in enumerate(['Dungeon_Orco', 'Dungeon_Escarcha', 'Dungeon_Invocador', 'Dungeon_Sangre']):
        cave_maps.append((mid, gen_cave(mid, 900 + k)))
    # exploration caves: a mouth in open ground of each biome (entity layer only, the painted surface does not change)
    rnd = random.Random(4242)
    town_rects = [(x0, y0, x1, y1) for (_, x0, y0, x1, y1, _) in rects]
    meta['entrances'] = [e for e in meta['entrances'] if e['map'] not in EXPLORE]
    for k, (mid, th) in enumerate(EXPLORE.items()):
        biome, kind = th[7], th[8]
        best = None
        for _ in range(6000):
            x, y = rnd.randint(8, SW - 9), rnd.randint(8, SH - 9)
            if G.r[y][x] != biome or any(x0 - 6 <= x <= x1 + 6 and y0 - 6 <= y <= y1 + 6 for (x0, y0, x1, y1) in town_rects): continue
            if zx0 - 4 <= x <= zx1 + 4 and zy0 - 4 <= y <= zy1 + 4: continue
            if any(abs(x - e['x']) + abs(y - e['row']) < 30 for e in meta['entrances']): continue
            ok = all(G.t[yy][xx] not in BLOCK_T and G.t[yy][xx] not in '=H' for yy in range(y - 2, y + 5) for xx in range(x - 3, x + 4))
            if ok: best = (x, y); break
        if not best: print('  no spot for', mid); continue
        x, y = best
        for yy in range(y - 2, y + 5):
            for xx in range(x - 3, x + 4): G.e[yy][xx] = ' '
        G.e[y][x] = 'E'
        meta['entrances'].append({'map': mid, 'kind': kind, 'name': th[0], 'x': x, 'row': y, 'boss': ''})
        cave_maps.append((mid, gen_cave(mid, 1300 + k)))
    for c in range(2):
        for r in range(4): slots.append((UNDER_X + 240 + c * 112, 6 + r * 88))
    json.dump(meta, open(os.path.join(LV, 'World3.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    entrances = {e['map']: e for e in meta['entrances']}
    under_lines = []
    for (mid, m), (ox, oy) in zip(cave_maps, slots):
        W, H = m['w'], m['h']
        assert ox + W <= WT and oy + H <= HT, mid
        for y in range(H):
            for x in range(W):
                G.t[oy + y][ox + x] = to_world_terrain(m['T'][y][x])
                G.e[oy + y][ox + x] = m['E'][y][x]
                G.r[oy + y][ox + x] = m['R'][y][x]
        for k, v in m['names'].items(): G.names[k] = v
        title = m['title'] if 'title' in m else mid
        if mid == 'Dungeon_ReySepultado': title = 'CATACUMBAS DEL REY OLVIDADO'
        dy = HT - oy - H                                            # local unity y -> world unity y
        for (kind, spr, x, y, fps) in m['props']:
            G.extra.append(f'PROP {spr} {ox + x:g} {oy + y:g} {fps:g}')
        for e in m['enemies']:
            typ, x, y = e[0], e[1], e[2]
            name = e[3] if len(e) > 3 else ''
            G.extra.append(f'ENEMY {typ} {ox + x} {oy + y} {name}'.rstrip())
        for (x, y, text) in m.get('signs', []):
            G.signs.append((ox + x, oy + y, text))
        if 'sign' in m and m['E'][m['sign'][1]][m['sign'][0]] == 'S':
            G.signs.append((ox + m['sign'][0], oy + m['sign'][1], f'{title}. LA ESCALERA DEL SUR SUBE A LA SUPERFICIE. AQUÍ ABAJO SOLO ALUMBRAN LAS ANTORCHAS.'))
        # gates: world entrance <-> stairs down here
        en = entrances[mid]
        ex, er = en['x'], en['row']
        ecx, ecy = ex + 0.5, HT - er - 0.5 + 0.2
        if mid == 'Dungeon_ReySepultado':
            stairs = [(gid, sx_, sy_) for gid, (sx_, sy_) in m['stairs'].items()]
            arr_dy = 4.5
        else:
            stairs = [('ARR', m['stairs'][0] + 0.5, m['stairs'][1] + 0.5)]
            arr_dy = -2.6
        first = None
        for gid, gx, gy in stairs:
            gid = 'ARR' if gid in ('E0', 'ARR') else gid
            cx, cy = ox + gx, HT - (oy + gy)
            ay = cy - arr_dy if arr_dy > 0 else cy - arr_dy           # arrival: away from the stairs, inside
            fy = -1 if arr_dy > 0 else 1
            ay = cy - 4.5 if arr_dy > 0 else cy + 2.6
            cat.append(f'GATE World {mid}:{gid} {cx:g} {cy:g} 3 1.6 {cx:g} {ay:g} 0 {fy} World {mid}:IN')
            first = first or gid
        cat.append(f'GATE World {mid}:IN {ecx:g} {ecy:g} 1.6 1.0 {ecx:g} {ecy - 1.5:g} 0 -1 World {mid}:{first}')
        cat.append(f"CAVE {mid} {ox} {oy} {ox + W - 1} {oy + H - 1} {m['R'][H // 2][W // 2]} {title}")
        caves.append(mid)
        under_lines.append(f"CAVE {mid} {ox} {oy} {W} {H} {m.get('zone') or '-'} " + (' '.join(f'{v:g}' for v in m['tint']) if 'tint' in m else '1 1 1'))
        under_lines.append('ROWS')
        under_lines += [''.join(r) for r in m['T']]
        under_lines.append('ZONES')
        under_lines += [''.join(r) for r in m['R']]
    with open(os.path.join(LV, 'Underground.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# generated by Tools/GameGen/merge_world.py - raw cave layouts for Tools/ArtGen2/paint_world_merged.py\n'
                + '\n'.join(under_lines) + '\n')

    # ---------------------------------------------------------------- creatures per biome, tidy props
    town_rects = [(x0, y0, x1, y1) for (_, x0, y0, x1, y1, _) in rects]
    print('  biome residents', biome_life(G, SW, SH, town_rects), '· props moved apart', separate(G, SW, SH))

    # ---------------------------------------------------------------- write
    header = ['TITLE MUNDO', 'SUBTITLE ', f'SIZE {WT} {HT}', 'MERGED 1', f'SURFACE {SW} {SH}']
    G.dump(w2, header)
    catalog = ['# generated by Tools/GameGen/merge_world.py - ONE map: the overworld with its towns, Monte Ceniza and the underground',
               f'MAP World world {WT} {HT} a MUNDO|', f'SURFACE {SW} {SH}'] + cat
    with open(os.path.join(LV, 'Maps.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(catalog) + '\n')
    np_ = sum(r.count('P') for r in G.e)
    print(f'merged world {WT}x{HT} (surface {SW}x{SH}) towns {len(rects)} caves {len(caves)} start marks {np_} '
          f'houses {len(G.houses)} npcs {len(G.npcs)} props/enemies {len(G.extra)}')


if __name__ == '__main__':
    main()
    # visual audit: nothing against buildings, on roads, in water, or blocking doors / chests (audit_world.py)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import audit_world
    audit_world.FIX = True
    audit_world.main()
