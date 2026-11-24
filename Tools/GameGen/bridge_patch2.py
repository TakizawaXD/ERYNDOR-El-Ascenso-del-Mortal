s = open('GameGen/world2.py', encoding='utf8').read()
old = "                xs = [p[0] for p in comp]; ys = [p[1] for p in comp]\n                land = lambda a, b: S.inb(a, b) and S.t[b][a] not in 'wsLO=HD'\n"
new = ("                xs = [p[0] for p in comp]; ys = [p[1] for p in comp]\n"
       "                land = lambda a, b: S.inb(a, b) and S.t[b][a] not in 'wsLO=HD'\n"
       "                # grow the deck until both ends rest fully on land (shores are rarely straight)\n"
       "                for _ in range(5):\n"
       "                    if c == 'H':\n"
       "                        cols = sorted(set(xs)); top, bot = min(ys), max(ys)\n"
       "                        if not all(land(xx, top - 1) for xx in cols):\n"
       "                            for xx in cols:\n"
       "                                if S.inb(xx, top - 1) and S.t[top - 1][xx] in 'ws': S.t[top - 1][xx] = 'H'; comp.append((xx, top - 1))\n"
       "                        if not all(land(xx, bot + 1) for xx in cols):\n"
       "                            for xx in cols:\n"
       "                                if S.inb(xx, bot + 1) and S.t[bot + 1][xx] in 'ws': S.t[bot + 1][xx] = 'H'; comp.append((xx, bot + 1))\n"
       "                    else:\n"
       "                        rows = sorted(set(ys)); lft, rgt = min(xs), max(xs)\n"
       "                        if not all(land(lft - 1, yy) for yy in rows):\n"
       "                            for yy in rows:\n"
       "                                if S.inb(lft - 1, yy) and S.t[yy][lft - 1] in 'ws': S.t[yy][lft - 1] = '='; comp.append((lft - 1, yy))\n"
       "                        if not all(land(rgt + 1, yy) for yy in rows):\n"
       "                            for yy in rows:\n"
       "                                if S.inb(rgt + 1, yy) and S.t[yy][rgt + 1] in 'ws': S.t[yy][rgt + 1] = '='; comp.append((rgt + 1, yy))\n"
       "                    xs = [p[0] for p in comp]; ys = [p[1] for p in comp]\n")
assert old in s; s = s.replace(old, new)
open('GameGen/world2.py', 'w', encoding='utf8').write(s)

p = open('ArtGen2/painter.py', encoding='utf8').read()
old = ("        self.put(mask & (din > dz + 4), 'wa_dk')\n"
       "        self.put(mask & (din > dz) & (din <= dz + 4) & checker, 'wa_dk')   # dithered, no hard ring\n")
new = "        # fresh water stays one clear blue, like the reference (no depth rings)\n"
assert old in p; p = p.replace(old, new)
p = p.replace("        self.put(mask & (din > 5.2 + (n - .5) * 1.5) & (din <= 7 + (n - .5) * 1.5), 'wa_dk')\n",
              "        self.put(mask & (din > 5.2 + (n - .5) * 1.5) & (din <= 6.2 + (n - .5) * 1.5), 'wa_dk')\n")
open('ArtGen2/painter.py', 'w', encoding='utf8').write(p)
print('ok')
