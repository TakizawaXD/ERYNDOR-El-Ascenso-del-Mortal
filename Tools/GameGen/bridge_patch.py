s = open('GameGen/world2.py', encoding='utf8').read()
old = "        road([(lx - 2, y), U(0.47, 0.56)], 2, '_', 0.0, 9)\n        self.straighten_bridges()\n"
new = ("        road([(lx - 2, y), (lx - 2, y + 4), U(0.47, 0.56)], 2, '_', 0.0, 9)\n"
       "        self.straighten_bridges()\n        self.drop_stray_bridges()\n")
assert old in s; s = s.replace(old, new)
fn = '''    def drop_stray_bridges(self):
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
                if c == '=':
                    ok = all(land(min(xs) - 1, yy) for yy in set(ys)) and all(land(max(xs) + 1, yy) for yy in set(ys))
                    span = max(xs) - min(xs) + 1
                else:
                    ok = all(land(xx, min(ys) - 1) for xx in set(xs)) and all(land(xx, max(ys) + 1) for xx in set(xs))
                    span = max(ys) - min(ys) + 1
                if not ok or span < 2:
                    for (a, b) in comp:
                        S.t[b][a] = '_' if any(land(a + dx, b + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) and span < 3 else 'w'

'''
s = s.replace("    def densify(self):", fn + "    def densify(self):", 1)
open('GameGen/world2.py', 'w', encoding='utf8').write(s)

p = open('ArtGen2/painter.py', encoding='utf8').read()
old_w = "        self.put(mask, 'wa')\n        self.put(mask & (din > deep_d + (n - .5) * 6), 'wa_dk')\n"
new_w = ("        self.put(mask, 'wa')\n"
         "        dz = deep_d + (self.noise(40, seed + 5) - .5) * 24\n"
         "        Y, X = np.mgrid[0:self.H, 0:self.W]\n"
         "        checker = ((X + Y) % 2) == 0\n"
         "        self.put(mask & (din > dz + 4), 'wa_dk')\n"
         "        self.put(mask & (din > dz) & (din <= dz + 4) & checker, 'wa_dk')   # dithered, no hard ring\n")
assert old_w in p; p = p.replace(old_w, new_w)
old_o = ("        self.put(mask, 'wa')\n        self.put(mask & (din > 10 + n * 8), 'wa_dk')\n        self.put(mask & (din > 34 + n * 14), 'wa_dp')\n")
new_o = ("        self.put(mask, 'wa')\n"
         "        Y, X = np.mgrid[0:self.H, 0:self.W]\n"
         "        chk = ((X + Y) % 2) == 0\n"
         "        n2 = self.noise(60, 83)\n"
         "        d1, d2 = 16 + n2 * 24, 48 + n2 * 30\n"
         "        self.put(mask & (din > d1 + 4), 'wa_dk'); self.put(mask & (din > d1) & (din <= d1 + 4) & chk, 'wa_dk')\n"
         "        self.put(mask & (din > d2 + 4), 'wa_dp'); self.put(mask & (din > d2) & (din <= d2 + 4) & chk, 'wa_dp')\n")
assert old_o in p; p = p.replace(old_o, new_o)
open('ArtGen2/painter.py', 'w', encoding='utf8').write(p)
print('ok')
