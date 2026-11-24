s = open('world2.py', encoding='utf8').read()
# 1) roads fill swamp pools / lava instead of bridging them (only rivers & lakes get bridges)
old = "                if t in 'wsL': S.t[y][x] = '=' if abs(d[0]) >= abs(d[1]) else 'H'\n"
new = "                if t == 'w': S.t[y][x] = '=' if abs(d[0]) >= abs(d[1]) else 'H'\n                elif t in 'sL': S.t[y][x] = mat\n"
assert old in s; s = s.replace(old, new)
# 2) docks go straight out to open sea
old = "        sea = min(((x, y) for y in range(py_ - 4, py_ + 5) for x in range(px_ - 4, px_ + 5) if S.inb(x, y) and S.t[y][x] == 'O'),\n                  key=lambda p: (p[0] - px_) ** 2 + (p[1] - py_) ** 2)\n        ddx, ddy = (0, 1) if abs(sea[1] - py_) >= abs(sea[0] - px_) else ((1 if sea[0] > px_ else -1), 0)\n        if ddx == 0: ddy = 1 if sea[1] > py_ else -1\n"
new = ("        ocean_cells = [(x, y) for y in range(py_ - 9, py_ + 10) for x in range(px_ - 9, px_ + 10) if S.inb(x, y) and S.t[y][x] == 'O']\n"
       "        vx_ = sum(x - px_ for x, _ in ocean_cells); vy_ = sum(y - py_ for _, y in ocean_cells)\n"
       "        ddx, ddy = ((1 if vx_ > 0 else -1), 0) if abs(vx_) > abs(vy_) else (0, (1 if vy_ > 0 else -1))\n")
assert old in s; s = s.replace(old, new)
# 3) path pads at both ends of every bridge so the road meets the deck straight on
pad = '''    def bridge_pads(self):
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

'''
s = s.replace("    def densify(self):", pad + "    def densify(self):", 1)
old = "        self.straighten_bridges()\n        self.drop_stray_bridges()\n"
assert old in s
s = s.replace(old, old + "        self.bridge_pads()\n")
open('world2.py', 'w', encoding='utf8').write(s)
print('ok')
