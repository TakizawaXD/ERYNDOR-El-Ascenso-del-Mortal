"""The five enemies of the Catacombs, recoloured from characters that already exist in the game (no new rigs):

  CryptGuard     guardia de cripta       <- Skeleton (sword and shield)        bone white, rusted shield, violet eyes
  BuriedArcher   arquero sepultado       <- KnightRanger + its Bow SpecialAttack   rotten leather, grave-green, bone
  CursedKnight   caballero maldito       <- KnightFallen                       blackened iron and rust
  CryptShade     sombra                  <- DemonWraith                        almost black, violet rim
  FuneralPriest  sacerdote funerario     <- Reaper                             violet robes, tarnished gold

  python Tools/CharAnim/crypt_enemies.py  -> Assets/Art/Characters/<Name>/ (sheets + <Name>_animations.json)

A gradient map: every pixel's luminance picks a colour on the new ramp; the brightest pixels (eyes, blades, magic)
become the glow colour. Alpha and the 64 px grid are kept, so the animator builder treats them like any character.
"""
import json, os, shutil
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CH = os.path.join(ROOT, 'Assets', 'Art', 'Characters')


def hx(s): s = s.lstrip('#'); return [int(s[i:i + 2], 16) for i in (0, 2, 4)]


SETS = {
    'CryptGuard': ('Skeleton', None, ['#0e0c10', '#3a3430', '#6e6658', '#a8a08a', '#d8d2be', '#f4f0e2'], '#c89cff', 0.0),
    'BuriedArcher': ('KnightRanger', 'WeaponSets/KnightRanger/Bow', ['#0a0c0a', '#26302a', '#46584a', '#788a70', '#b4bca0', '#e4e6d2'], '#a8ffb8', 0.0),
    'CursedKnight': ('KnightFallen', None, ['#060508', '#16141c', '#2c2632', '#4a3a3a', '#7a5a44', '#b08a5a'], '#c070ff', 0.0),
    'CryptShade': ('DemonWraith', None, ['#020104', '#0a0614', '#1a0e30', '#2e1a52', '#5a36a0', '#a07ae6'], '#e8d0ff', 0.25),
    'FuneralPriest': ('Reaper', None, ['#08040c', '#1e0e2a', '#3a1c4e', '#5e3472', '#a07a3a', '#e8cc7a'], '#ffe6a0', 0.0),
}


def recolor(im, ramp, glow, fade):
    a = np.array(im.convert('RGBA')).astype(np.float32)
    rgb, al = a[:, :, :3], a[:, :, 3]
    L = (rgb[:, :, 0] * 0.299 + rgb[:, :, 1] * 0.587 + rgb[:, :, 2] * 0.114) / 255.0
    r = np.array(ramp, np.float32)
    pos = np.clip(L * 1.15, 0, 1) * (len(r) - 1)
    i0 = np.floor(pos).astype(int); i1 = np.minimum(i0 + 1, len(r) - 1); t = (pos - i0)[..., None]
    out = r[i0] * (1 - t) + r[i1] * t
    mx, mn = rgb.max(2), rgb.min(2)
    sat = (mx - mn) / np.maximum(mx, 1)
    hot = (L > 0.82) | ((sat > 0.55) & (L > 0.6))
    out[hot] = np.array(glow, np.float32)
    a[:, :, :3] = out
    if fade: a[:, :, 3] = al * (1 - fade)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


def make(name, src, extra, ramp, glow, fade):
    ramp = [hx(c) for c in ramp]; glow = hx(glow)
    sdir = os.path.join(CH, src)
    man = json.load(open(os.path.join(sdir, f'{src}_animations.json')))
    dst = os.path.join(CH, name)
    if os.path.isdir(dst): shutil.rmtree(dst)
    clips = []
    extra_clips = {}
    if extra:
        em = json.load(open(os.path.join(CH, extra, os.path.basename(extra.rstrip('/')) and f"{extra.split('/')[1]}_{extra.split('/')[2]}_animations.json")))
        for c in em['clips']: extra_clips[(c['name'], c['dir'])] = (os.path.join(CH, extra), c)
    for c in man['clips']:
        base, cc = sdir, c
        if (c['name'], c['dir']) in extra_clips: base, cc = extra_clips[(c['name'], c['dir'])]
        im = Image.open(os.path.join(base, cc['file']))
        newfile = cc['file'].split('/')[0] + '/' + f"{name}_{c['name']}_{c['dir']}.png"
        os.makedirs(os.path.join(dst, os.path.dirname(newfile)), exist_ok=True)
        recolor(im, ramp, glow, fade).save(os.path.join(dst, newfile))
        n = dict(cc); n['name'] = c['name']; n['dir'] = c['dir']; n['file'] = newfile
        clips.append(n)
    man = dict(man); man['character'] = name; man['clips'] = clips
    json.dump(man, open(os.path.join(dst, f'{name}_animations.json'), 'w'), indent=1)
    return len(clips)


def preview():
    cells = []
    for name in SETS:
        im = Image.open(os.path.join(CH, name, 'Idle', f'{name}_Idle_Down.png' if os.path.exists(os.path.join(CH, name, 'Idle', f'{name}_Idle_Down.png')) else f'{name}_Idle_Right.png'))
        cells.append(im.crop((0, 0, 64, 64)))
    s = Image.new('RGBA', (64 * len(cells), 64), (40, 34, 46, 255))
    for i, c in enumerate(cells): s.alpha_composite(c, (i * 64, 0))
    s.resize((s.width * 4, 256), Image.NEAREST).save(os.path.join(ROOT, 'Documentation', 'CharacterPreviews', 'catacumbas_enemigos.png'))


if __name__ == '__main__':
    for name, (src, extra, ramp, glow, fade) in SETS.items():
        print(name, '<-', src, make(name, src, extra, ramp, glow, fade), 'clips')
    preview()
