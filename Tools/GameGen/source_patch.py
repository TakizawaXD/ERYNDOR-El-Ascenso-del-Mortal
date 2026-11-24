s = open('GameGen/world2.py', encoding='utf8').read()
old = "        S.line([U(0.24, 0.40), U(0.20, 0.50), U(0.14, 0.56), U(0.08, 0.60)], 2, river, 2.0, 33)\n"
new = old + ("        # the glacier river springs from a snowy cliff (a waterfall will be placed under it)\n"
             "        sx_, sy_ = U(0.33, 0.10)\n"
             "        for yy in range(sy_ - 5, sy_ + 1):\n"
             "            for xx in range(sx_ - 4, sx_ + 6):\n"
             "                if S.inb(xx, yy): S.t[yy][xx] = 'C'\n"
             "        for yy in range(sy_ + 1, sy_ + 4):\n"
             "            for xx in range(sx_ - 1, sx_ + 3):\n"
             "                if S.inb(xx, yy): S.t[yy][xx] = 'w'\n")
assert old in s; s = s.replace(old, new)
old = "        S.scatter(full, 'Y', 60, '_', 4, 12, avoid='p=HD')                        # palms on beaches everywhere\n"
new = old + ("        for y in range(H):\n"
             "            for x in range(W):\n"
             "                if S.e[y][x] == 'Y' and not S.near(x, y, 4, 'O'): S.e[y][x] = None   # palms only by the sea\n")
assert old in s; s = s.replace(old, new)
s = s.replace("        S.scatter(full, 'YYgyz', 80, '_.', 3, 10, region='j')", "        S.scatter(full, 'YYgyz', 80, '_.', 3, 10, region='j')\n        for y in range(H):\n            for x in range(W):\n                if S.e[y][x] == 'Y' and S.t[y][x] == '_' and not S.near(x, y, 4, 'O'): S.e[y][x] = None")
open('GameGen/world2.py', 'w', encoding='utf8').write(s)
print('ok')
