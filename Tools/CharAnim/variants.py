"""Palette variants of the four animated characters (same frames, same rig -> same animations).

  python variants.py            -> Assets/Art/Characters/<Variant>/... + <Variant>_animations.json

Knight classes (player) are recolours of the Soldier; regional enemies are recolours of Orc / Demon / BloodMonster
(and the Fallen Knight of the Soldier).  Only the listed colour groups change - FX colours (white slashes, yellow
sparks, red hit flashes) and outlines stay untouched, so every variant keeps the original look.
"""
import colorsys, json, os, shutil
from features import FEATURES
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Assets', 'Art', 'Characters'))


def hx(s):
    s = s.lstrip('#'); return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


# source colour groups per base character
GROUPS = {
    'Soldier': {
        'armor': ['#c5d0d5', '#9badb7', '#7f909a', '#6f828d', '#607581', '#425c6b'],
        'cloth': ['#8f3838', '#672020', '#621914', '#4c1a1a'],
        'under': ['#534545'],
        'skin': ['#f2dad2', '#be9b97'],
    },
    'Orc': {
        'skin': ['#b8d08a', '#a3be71', '#7d984b', '#5d772d', '#425916', '#243305'],
        'metal': ['#9badb7', '#6f828d', '#516d7d'],
        'leather': ['#8d6534', '#7b4e16', '#603a0a'],
    },
    'Demon': {
        'body': ['#a6483a', '#972f34', '#972f2f', '#7e222a', '#6f1a29', '#4a142c'],
        'horn': ['#a6aba8', '#929894', '#7e8881', '#738a74', '#596c5d', '#4d5a53', '#44534b'],
        'cloth': ['#793a80'],
    },
    'BloodMonster': {
        'body': ['#df3b48', '#cf4554', '#c02440', '#a22b4b', '#6e1438', '#5e0f30', '#311339'],
    },
}

# target ramps, dark -> light
R = lambda *c: [hx(x) for x in c]
VARIANTS = {
    # ---------------------------------------------------------------- knight classes (player)
    'KnightPaladin': ('Soldier', {
        'armor': R('#7a4a1c', '#a8682a', '#d08d34', '#f0b648', '#fcd77a', '#fff2b8'),
        'cloth': R('#0f2f63', '#17458c', '#2a64b8', '#4a8be0'),
        'under': R('#5c5a6e'),
    }),
    'KnightDark': ('Soldier', {
        'armor': R('#120f1c', '#1f1a2e', '#2d2742', '#3f3858', '#5a5276', '#7d73a0'),
        'cloth': R('#3a0f44', '#5a1766', '#7d2490', '#a63bbd'),
        'under': R('#2a2230'),
    }),
    'KnightRanger': ('Soldier', {
        'armor': R('#3d2814', '#5a3c1e', '#7a5530', '#97703f', '#b48c55', '#d2ae7a'),
        'cloth': R('#1d3d1a', '#2b5a25', '#3e7a33', '#5aa04a'),
        'under': R('#4a4033'),
    }),
    'KnightSamurai': ('Soldier', {     # lacquered red-and-black armour, gold trim (the katana comes from its weapon sets)
        'armor': R('#1a0a0c', '#3a0e12', '#6a1418', '#9a2020', '#c83a2a', '#f0c060'),
        'cloth': R('#0c0c10', '#16161e', '#24242e', '#3a3a48'),
        'under': R('#2a1a14'),
    }),
    # ---------------------------------------------------------------- regional enemies
    'KnightFallen': ('Soldier', {      # night: ghost knights of the citadel and the ruins
        'armor': R('#1b3340', '#2a5060', '#3f7383', '#5e9aa6', '#8cc4c8', '#c4eeea'),
        'cloth': R('#123a3a', '#1b5050', '#2a7070', '#3f9494'),
        'under': R('#2c3f48'),
        'skin': R('#9fe0dc', '#5fa8a8'),
    }),
    'OrcDesert': ('Orc', {
        'skin': R('#4a2410', '#6e3a18', '#9a5626', '#c27a3a', '#dc9c5a', '#f0c088'),
        'leather': R('#3a1a10', '#5e2a18', '#82402a'),
    }),
    'OrcFrost': ('Orc', {
        'skin': R('#1c3150', '#2d4a72', '#4a6e98', '#6e94bc', '#a0c0dc', '#d4e6f2'),
        'metal': R('#5e6a8a', '#8592b4', '#c0cbdc'),
    }),
    'OrcCorsair': ('Orc', {
        'skin': R('#0f3330', '#185048', '#227066', '#3a9486', '#64b8a6', '#9edac6'),
        'leather': R('#1a2a4a', '#24406e', '#345a94'),
    }),
    'OrcBerserker': ('Orc', {
        'skin': R('#2a0f0a', '#4a1a12', '#6e2a1a', '#93402a', '#b55a3a', '#d67a52'),
        'metal': R('#3c4258', '#5a6988', '#8e9ab4'),
        'leather': R('#1a1010', '#2e1a16', '#47271f'),
    }),
    'DemonAsh': ('Demon', {
        'body': R('#f7a23a', '#e06a22', '#c0461c', '#3a3a4a', '#2a2a36', '#181822'),
        'horn': R('#1a1410', '#2a2018', '#3a2c20', '#5a4030', '#e43b44', '#f77622', '#feae34'),
    }),
    'DemonWraith': ('Demon', {
        'body': R('#c4f0ff', '#94d6f0', '#6ab4dc', '#4a8cbc', '#2f6496', '#1c3c66'),
        'horn': R('#0e1a2a', '#16283e', '#203a56', '#2c4e70', '#3e668c', '#5a86aa', '#8aaecc'),
        'cloth': R('#5a3c96'),
    }),
    'BloodToxic': ('BloodMonster', {
        'body': R('#d4f25a', '#a8d63a', '#7cb82a', '#4f8f22', '#2f6420', '#1f4a1c', '#132e16'),
    }),
    'BloodMagma': ('BloodMonster', {
        'body': R('#fff09a', '#feae34', '#f77622', '#e43b44', '#9e2835', '#6a1a24', '#2a0e14'),
    }),
}

# ---------------------------------------------------------------- townsfolk (NPCs): every one has its own palette
# armour -> clothes / apron / robe, cloth -> sash and cape, under -> trousers, skin -> skin tone
SKIN = {'pale': R('#e0b8a8', '#f6dcd0'), 'tan': R('#b07a5a', '#dca582'), 'dark': R('#6e4430', '#9a6448'), 'olive': R('#a8845e', '#d0ac82')}
VILLAGERS = {
    'NpcBruna':   (R('#2a1810', '#3e2418', '#5a3622', '#74492c', '#8e5e3a', '#b07c52'), R('#4a2a1a', '#6a3a22', '#8a4e2c', '#a8683a'), '#2a2228', 'dark'),
    'NpcTomas':   (R('#6e5a36', '#8e7646', '#ae9458', '#ccb070', '#e2cc90', '#f4e6b8'), R('#7a5a20', '#9a7428', '#ba9034', '#d8ae48'), '#5a4a38', 'pale'),
    'NpcElvira':  (R('#1c3a24', '#28502e', '#3a6a3c', '#52864e', '#74a466', '#a0c48a'), R('#4a2a5a', '#643a78', '#7e4e96', '#9c6ab4'), '#3a3428', 'olive'),
    'NpcRamiro':  (R('#283444', '#3a4a60', '#566a84', '#7a8ea8', '#a6b6cc', '#d6e0ec'), R('#14305a', '#1c4278', '#2a5a9c', '#3e76bc'), '#3a3a48', 'tan'),
    'NpcLucia':   (R('#3a1840', '#52245a', '#6c3474', '#884890', '#a866ae', '#cc92cc'), R('#7a5a10', '#9a7418', '#c09024', '#e2b03a'), '#3a2a3a', 'pale'),
    'NpcNico':    (R('#6a4a10', '#8a6418', '#ac8222', '#cca232', '#e6c44e', '#f6e48a'), R('#2a5a2a', '#3a7a36', '#4e9a44', '#6cba5a'), '#4a3a2a', 'tan'),
    'NpcMartin':  (R('#3a2a16', '#52401f', '#6c562a', '#866e36', '#a48a4a', '#c6aa6a'), R('#5a1a14', '#7a241a', '#9c3224', '#bc4630'), '#3a3024', 'olive'),
    'NpcTordo':   (R('#14141c', '#22222e', '#343444', '#4a4a5e', '#66667e', '#9090a6'), R('#7a5210', '#a06c16', '#c88a20', '#eaae38'), '#22202a', 'pale'),
    'NpcIlmaro':  (R('#1a1438', '#28204e', '#3a2e6a', '#4e4088', '#6a58a8', '#9a88cc'), R('#6a5a10', '#8a7616', '#ae9620', '#d2b82e'), '#2a2440', 'pale'),
    'NpcClara':   (R('#8a8478', '#a8a296', '#c4beb2', '#dcd6cc', '#ece8e0', '#fbf8f2'), R('#7a5a10', '#a07a18', '#c89c28', '#ecc444'), '#8a8478', 'tan'),
    'NpcGalen':   (R('#3a3a40', '#52525a', '#6c6c76', '#8a8a96', '#aeaeb8', '#d8d8de'), R('#5a0f14', '#7a161c', '#9e2028', '#c43038'), '#2a2a30', 'dark'),
    'NpcInes':    (R('#0e3a3a', '#145050', '#1e6a68', '#2c8682', '#46a6a0', '#76c8c0'), R('#5a1a3a', '#7a2450', '#9c346a', '#c04a88'), '#2a2a3a', 'pale'),
    'NpcMarta':   (R('#5a2a10', '#7a3a16', '#9c4e1e', '#be6828', '#dc8a3e', '#f4b06a'), R('#c8beac', '#dcd4c4', '#ece6da', '#f8f4ec'), '#4a3428', 'tan'),
    'NpcBartolo': (R('#121c34', '#1a2846', '#24385e', '#324c7a', '#486698', '#6c8cbc'), R('#6a5a3a', '#8a764c', '#aa9462', '#c8b47e'), '#2a2a34', 'olive'),
    'NpcRocio':   (R('#141014', '#221a22', '#342834', '#4a3a4a', '#665066', '#8a708a'), R('#6a0f14', '#8e161c', '#b22028', '#d83a3a'), '#1a161a', 'tan'),
    'NpcHassan':  (R('#0e3a34', '#145048', '#1c6a5e', '#288678', '#3ea696', '#68c8b6'), R('#7a5210', '#a06c16', '#c88a20', '#eaae38'), '#3a2a20', 'dark'),
    'NpcPip':     (R('#2a4a6a', '#3a628a', '#4e7caa', '#6a9ac6', '#8cb8de', '#bcdcf4'), R('#8a2a14', '#aa3a1a', '#cc4e24', '#ec6a34'), '#3a3a48', 'pale'),
}
for _n, (_arm, _cl, _un, _sk) in VILLAGERS.items():
    VARIANTS[_n] = ('Soldier', {'armor': _arm, 'cloth': _cl, 'under': R(_un), 'skin': SKIN[_sk]})

# El Invocador has his own hand-built sheet: Tools/ArtGen2/summoner_art.py (not a recolour)


def build_map(base, ramps):
    m = {}
    for g, src in GROUPS[base].items():
        if g not in ramps: continue
        tgt = ramps[g]
        srcs = sorted((hx(c) for c in src), key=lum, reverse=True)       # light -> dark
        tg = list(reversed(tgt))                                          # light -> dark
        n, k = len(srcs), len(tg)
        for i, c in enumerate(srcs):
            j = 0 if n == 1 else round(i * (k - 1) / (n - 1))
            m[c] = tg[j]
    return m


def recolour(img, cmap):
    im = img.convert('RGBA'); px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a and (r, g, b) in cmap: px[x, y] = cmap[(r, g, b)] + (a,)
    return im


BODY_GROUP = {'Orc': 'skin', 'Demon': 'body', 'BloodMonster': 'body', 'Soldier': 'armor'}


def with_features(im, name, base, cmap):
    import numpy as np
    from features import FEATURES, apply
    a = np.array(im.convert('RGBA'))
    body = [cmap.get(hx(c), hx(c)) for c in GROUPS[base][BODY_GROUP[base]]]
    for i in range(a.shape[1] // 64):
        a[:, i * 64:(i + 1) * 64] = apply(a[:, i * 64:(i + 1) * 64].copy(), FEATURES[name], body, i)
    return Image.fromarray(a, 'RGBA')


def make(name, base, ramps):
    cmap = build_map(base, ramps)
    src_root, dst_root = os.path.join(ROOT, base), os.path.join(ROOT, name)
    man = json.load(open(os.path.join(src_root, f'{base}_animations.json')))
    man['character'] = name
    for clip in man['clips']:
        src = os.path.join(src_root, clip['file'])
        rel = clip['file'].replace(f'{base}_', f'{name}_', 1)
        dst = os.path.join(dst_root, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        im = recolour(Image.open(src), cmap)
        if name in FEATURES:       # own silhouette: horns, crests, crystals, flames, glowing eyes (features.py)
            im = with_features(im, name, base, cmap)
        im.save(dst)
        clip['file'] = rel
    with open(os.path.join(dst_root, f'{name}_animations.json'), 'w') as fh:
        json.dump(man, fh, indent=1)
    return len(man['clips'])


def preview(names, out):
    """first frame of Idle_Down of each variant side by side (x3)"""
    ims = []
    for n in names:
        f = os.path.join(ROOT, n, 'Idle', f'{n}_Idle_Down.png')
        ims.append(Image.open(f).crop((0, 0, 64, 64)))
    sheet = Image.new('RGBA', (64 * len(ims), 64), (60, 120, 70, 255))
    for i, im in enumerate(ims): sheet.alpha_composite(im, (64 * i, 0))
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(out)


if __name__ == '__main__':
    import sys
    only = sys.argv[1:]          # e.g. "python variants.py Npc" builds only the names starting with Npc
    for n, (base, ramps) in VARIANTS.items():
        if only and not any(n.startswith(o) for o in only): continue
        print(n, make(n, base, ramps), 'clips')
    docs = os.path.join(ROOT, '..', '..', '..', 'Documentation', 'CharacterPreviews')
    preview(['Soldier', 'KnightPaladin', 'KnightDark', 'KnightRanger', 'KnightSamurai', 'KnightFallen'], os.path.join(docs, 'knight_classes.png'))
    preview(['Orc', 'OrcDesert', 'OrcFrost', 'OrcCorsair', 'OrcBerserker', 'Demon', 'DemonAsh', 'DemonWraith',
             'BloodMonster', 'BloodToxic', 'BloodMagma'], os.path.join(docs, 'enemy_variants.png'))
    preview(list(VILLAGERS), os.path.join(docs, 'townsfolk.png'))
