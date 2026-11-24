s = open('world2.py', encoding='utf8').read()
old = "            if S.near(x, y, 1, roads) or S.crowded(x, y, 1): continue\n"
new = ("            if S.near(x, y, 1, roads) or S.crowded(x, y, 1): continue\n"
       "            if any(S.inb(xx, yy) and S.e[yy][xx] is not None and S.e[yy][xx] in '6789J0#xj$@|('\n"
       "                   for yy in range(y - 2, y + 5) for xx in range(x - 4, x + 5)): continue   # keep buildings clear\n")
assert old in s
s = s.replace(old, new)
open('world2.py', 'w', encoding='utf8').write(s)
print('ok')
