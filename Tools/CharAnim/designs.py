"""Hand-drawn FRONT (facing down) and BACK (facing up) views.

Every colour letter maps to a colour sampled from the character's own original sprite,
so no new colours are introduced. Rows are drawn at the original scale (1:1).
"""
from engine import hx

# =========================================================== SOLDIER ======
SOLDIER_PAL = {k: hx(v) for k, v in dict(
    a='#000000', b='#425c6b', c='#607581', d='#c5d0d5', e='#9badb7', f='#6f828d', g='#7f909a',
    h='#c9c0be', i='#2d0704', j='#1f1a1a', k='#ffffff', l='#621914', m='#f2dad2', n='#b19e9a',
    o='#be9b97', p='#8d6534', q='#7b4e16', r='#672020', s='#431a0b', t='#8f3838', u='#946835',
    v='#b78c61', x='#4c1a1a',
    # sword (sampled from Soldier_Attack01) and bow (sampled from Soldier_Attack03)
    S='#e8f1f4', T='#c9d5d9', U='#a9c1c9', V='#8fa1ae', W='#805121',
    X='#22021d', Y='#fff0ef', Z='#5e1e13',
).items()}

SOLDIER_FRONT = [
    "......aaa......",
    ".....abcba.....",
    "....adcbcda....",
    "...aeddcddea...",
    "..afeddgddefa..",
    "..affeegeeffa..",
    ".aacffbbbffcaa.",
    ".abcbjjbjjbcba.",
    ".abbaklblkabba.",
    ".abaommmmmoaba.",
    "..aaceeceecaa..",
    ".aceqrrtrrrceca",
    ".acjrqrtrrrjca.",
    ".acejrrqtrrjeca",
    ".accjqquvuqjcca",
    "...abca.acba...",
    "...arra.arra...",
    "...arxa.axra...",
]
SOLDIER_BACK = [
    "......aaa......",
    ".....abcba.....",
    "....adcbcda....",
    "...aeddcddea...",
    "..afeddgddefa..",
    "..affeegeeffa..",
    ".aacffbbbffcaa.",
    ".ahncffbbbffca.",
    ".anhacfbbbfcba.",
    "..aapqcbbbcaa..",
    "..aacpqeceecaa.",
    ".acerrpqrrrceca",
    ".acjrrtpqrrjca.",
    ".acejrrtpqrjeca",
    ".accjqquuvqjcca",
    "...abca.acba...",
    "...arra.arra...",
    "...arxa.axra...",
]
# leg poses replace the last 3 rows. A = viewer-left leg planted / right foot lifted, B = mirror
SOLDIER_LEGS = {
    'stand': ["...abca.acba...", "...arra.arra...", "...arxa.axra..."],
    'A':     ["...abca.acba...", "...arra.axra...", "...arxa........"],
    'B':     ["...abca.acba...", "...arxa.arra...", "........axra..."],
}
SOLDIER_ARMS = ((1, 4), (11, 15), (11, 15))   # (left cols), (right cols), (rows) for arm swing

# =============================================================== ORC ======
ORC_PAL = {k: hx(v) for k, v in dict(
    a='#000000', b='#425916', c='#a3be71', d='#b8d08a', e='#7d984b', f='#5d772d', g='#7b0808',
    h='#4c3029', i='#d7d5d2', j='#6f828d', k='#9badb7', l='#243305', m='#516d7d', n='#d5cac5',
    o='#1f1a1a', p='#f4edea', q='#603a0a', r='#5e433d', s='#7b4e16', t='#8d6534', u='#b7a59b',
).items()}
ORC_FRONT = [
    "....aaaaaaa....",
    "...abccddcba...",
    "..abeccddccea..",
    "..afeeecccefa..",
    "aaafeaeeeaefaaa",
    "aceffgeeegffeca",
    ".aafeieeeiefaa.",
    "..aalbbbbblaa..",
    ".akkaqfcdfqeaa.",
    "ajjjaoqedeqoeea",
    "aaaabsqoeqsbaea",
    ".aebqqstsqqbea.",
    "..aalbsstsbla..",
    "...affa.affa...",
    "...afa...afa...",
]
ORC_BACK = [
    "....aaaaaaa....",
    "...abccddcba...",
    "..abeccddccea..",
    "..afeeecccefa..",
    "aaafeeeeeeefaaa",
    "aceffeeeeeffeca",
    ".aafefeeefefaa.",
    "..aafbbbbbfaa..",
    ".akkaqeeeeqeaa.",
    "ajjjaeqeeqeeeea",
    "aaaabeeqqeebaea",
    ".aebeeqsqeebea.",
    "..aalbsstsbla..",
    "...affa.affa...",
    "...afa...afa...",
]
ORC_LEGS = {
    'stand': ["...affa.affa...", "...afa...afa..."],
    'A':     ["...affa.affa...", "...afa...aa...."],
    'B':     ["...affa.affa...", "....aa...afa..."],
}
# axe held upright at the orc's side (front: viewer's right hand side, back: viewer's left)
ORC_AXE_UP = [
    "..aaa.",
    ".ajkpa",
    "ajjknpa",
    "ajmjkpa",
    ".aamaa.",
    "..aha..",
    "..aha..",
    "..ara..",
    "..aha..",
    "...a...",
]
ORC_ARMS = ((0, 4), (11, 15), (8, 12))

# ============================================================= DEMON ======
DEMON_PAL = {k: hx(v) for k, v in dict(
    a='#000000', b='#655457', c='#9a918f', d='#7b6a6b', e='#8d8080', f='#6f1a29', g='#7e222a',
    h='#972f34', i='#a6483a', j='#4a142c', k='#d79970', l='#44534b', m='#596c5d', n='#738a74',
    o='#4d5a53', p='#972f2f', q='#5c2c26', r='#7e8881', s='#754b38', t='#a6aba8', u='#929894',
).items()}
DEMON_FRONT = [
    ".aa.........aa.",
    ".aba.......aca.",
    ".aba.......aca.",
    ".abdaa...aaeda.",
    "..adeeaaaeeda..",
    "...abdagaedba..",
    "....aghhihga...",
    "...aghakahkhga.",
    "....afghhhgfa..",
    ".....agjhjga...",
    "...aalfgfgflaa.",
    "..almnafhfanmla",
    "...alagfgfgala.",
    "....agaghgaga..",
    "....afgafagfa..",
    "....agfa.afga..",
    "....afa...afa..",
]
DEMON_BACK = [
    ".aa.........aa.",
    ".aba.......aca.",
    ".aba.......aca.",
    ".abdaa...aaeda.",
    "..adeeaaaeeda..",
    "...abdagaedba..",
    "....agghhgga...",
    "...aggfhhfgga..",
    "....afgghggfa..",
    ".....aggggga...",
    "...aalfgggflaa.",
    "..almnagfganmla",
    "...alagfgfgala.",
    "....agaghgaga..",
    "....afgaga.gfa.",
    "....agfaha.fga.",
    "....afa.aga.afa",
]
DEMON_LEGS = {
    'stand': ["....afa...afa.."],
    'A':     ["....afa...aa..."],
    'B':     [".....aa...afa.."],
}
DEMON_BODY_DY = -2   # the cleaver is held in front of the legs and reaches 2 px lower (as in the side view)
# the big cleaver held low across the body (front) - same greys as the original blade
DEMON_BLADE_FRONT = [
    "aaa..........aaa",
    "aorraaaaaaaaarta",
    "arrooooooooorrta",
    ".aarrrooooruutta",
    "...auurrrruttta.",
    "....auuuuttuaa..",
    ".....aaaaaaa....",
]
DEMON_TAIL_FRONT = ["a..", "ga.", "aha", ".ag"]
DEMON_ARMS = ((1, 5), (10, 15), (10, 13))

# ===================================================== BLOOD MONSTER ======
BLOOD_PAL = {k: hx(v) for k, v in dict(
    a='#000000', b='#6e1438', c='#d9d8d8', d='#a22b4b', e='#311339', f='#c0bfbf', g='#1f1a1a', h='#cf4554',
).items()}
BLOOD_FRONT = [
    ".......aaaaa.......",
    "......abbdbba......",
    ".....abdacadba.....",
    ".....abacecaba.....",
    "....abdafefadba....",
    "....abdacecadba....",
    "...abddafefaddba...",
    "...abdbacecabdba...",
    "..aabdbdafadbdbaa..",
    ".abddadddadddaddba.",
    ".ahdabdddddddbadha.",
    "adbdadddddddddadbda",
    "adbdaddddbddddadbda",
    "abadabdbaaabdbadaba",
    ".a.a..aba.aba..a.a.",
]
BLOOD_BACK = [
    ".......aaaaa.......",
    "......abdddba......",
    ".....abddhddba.....",
    ".....abdbhbdba.....",
    "....abddbhbddba....",
    "....abdbdhdbdba....",
    "...abddbdhdbddba...",
    "...abdbddhddbdba...",
    "..aabdbdbhbdbdbaa..",
    ".abddadddbdddaddba.",
    ".ahdabdddddddbadha.",
    "adbdadddddddddadbda",
    "adbdaddddbddddadbda",
    "abadabdbaaabdbadaba",
    ".a.a..aba.aba..a.a.",
]
_MOUTH = ["aaaaa", "accca", "aeeea", "affca", "aeeea", "accfa", "aeeea", "acfca", "aaaaa"]
BLOOD_FRONT = [r[:7] + _MOUTH[i - 1] + r[12:] if 1 <= i <= len(_MOUTH) else r for i, r in enumerate(BLOOD_FRONT)]
BLOOD_LEGS = {
    'stand': [".a.a..aba.aba..a.a."],
    'A':     [".a.a..aba..aa..a.a."],
    'B':     [".a.a..aa..aba..a.a."],
}
BLOOD_ARMS = ((0, 5), (14, 19), (9, 14))

# ----- weapons in front/back attack poses (pixels copied from the original attack frames) -----
SOLDIER_SWORD_UP = [      # Soldier_Attack01 frame 1, blade raised
    ".a...",
    "aSa..",
    "aSSa.",
    "aTSa.",
    "aTSa.",
    "aUSa.",
    "aUSa.",
    "aUSa.",
    "aUSa.",
    "aUTa.",
    "aVTa.",
    "aVUa.",
    "aVUa.",
    "WWWWa",
    ".aqa.",
]
SOLDIER_SWORD_DOWN = SOLDIER_SWORD_UP[::-1]
SOLDIER_BOW_H = [         # Soldier_Attack03 bow, turned 90 degrees (seen from above while aiming down/up)
    "..XXXXXXXXX..",
    ".XZZZZZZZZZX.",
    "XZZ.......ZZX",
    "XY.........YX",
    ".YYYYYYYYYYY.",
]
SOLDIER_ARROW_V = [       # arrow from Arrow01(32x32), turned 90 degrees
    ".a.",
    "aYa",
    "ahn",
    ".h.",
    ".h.",
    ".h.",
    ".h.",
    "aXa",
    "aXa",
    ".a.",
]
ORC_AXE_DOWN = ORC_AXE_UP[::-1]
DEMON_BLADE_UP = [        # Demon_A_Attack02 frame 1, cleaver raised
    ".aaaa.",
    "artta.",
    "aortta",
    "aoruta",
    "aoruta",
    "aoruua",
    "aoruua",
    "aooura",
    ".aoura",
    ".aoura",
    ".aoua.",
    "..aaa.",
    "..aqa.",
    "..aqa.",
]
DEMON_BLADE_DOWN = DEMON_BLADE_UP[::-1]
BLOOD_CLAW = [            # Blood Monster_A_Attack01 frame 3, claw raised
    "..aa.",
    ".abcaa",
    "abbbcba",
    "aababa.",
    ".adaa.a",
]
