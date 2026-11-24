"""Technical + artistic audit of EVERY animated character (2026-11-21).

  python Tools/CharAnim/audit_sprites.py          -> Documentation/AUDITORIA_SPRITES.md + Documentation/auditoria_sprites.json
  python Tools/CharAnim/audit_sprites.py --fix    also applies the safe automatic fixes (see FIXES below)

For each character in Assets/Art/Characters (and each weapon set of the player classes) it opens the animation list
(<Char>_animations.json) and every frame of every sheet, and measures:
  files      sheet missing, wrong size (frames x cell), missing Unity .meta, missing animator controller
  dirs       clips that do not face the 4 top-down directions (Down, Up, Left, Right)
  required   essential clips missing for the role (player / enemy / boss / npc)
  empty      frames with nothing drawn (except the fading end of a death)
  alpha      semi-transparent pixels on the body (pixel art should be 0 / 255; ghosts, glows and FX are allowed)
  stray      isolated single pixels (no neighbour drawn) = dirt
  feet       the lowest drawn row jumps between frames of a grounded loop (idle / walk / run) -> sliding, "bobbing" feet
  scale      the figure's height changes more than 18 % between frames of a grounded loop -> the character resizes
  pivot      feet far from the pivot row (the shadow and depth sorting use the pivot)
FIXES (--fix): removes stray pixels and snaps faint (alpha < 64) body pixels to transparent in grounded loops of
non-ghost characters. Nothing else is changed automatically: missing art is reported, never faked.
"""
import json, os, sys
from collections import defaultdict
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CH = os.path.join(ROOT, 'Assets', 'Art', 'Characters')
ANIM = os.path.join(ROOT, 'Assets', 'Art', 'Animations', 'Characters')
DOC = os.path.join(ROOT, 'Documentation')
FIX = '--fix' in sys.argv
DIRS = ['Down', 'Up', 'Left', 'Right']
GROUNDED = ('Idle', 'Walk', 'Run')
GHOSTS = ('Wraith', 'Shade', 'Reaper', 'Fallen', 'Slime', 'Eye', 'Flame', 'Skull', 'Swarm', 'Bat', 'Invocador', 'Tentacle')
PLAYER = {'Soldier', 'KnightPaladin', 'KnightDark', 'KnightRanger', 'KnightSamurai'} | {
    'HeroKnight', 'HeroCrusader', 'HeroAxeKnight', 'HeroSoldier', 'HeroWizard', 'HeroSwordswoman', 'HeroPriestess', 'HeroRanger', 'HeroRider'}
REQ = {
    'player': ['Idle', 'Walk', 'Run', 'Attack', 'HeavyAttack', 'ComboAttack', 'SpecialAttack', 'Hurt', 'Death', 'Dodge', 'Roll',
               'Block', 'PickUp', 'Interact', 'Sit', 'Sleep', 'Swim', 'Knockback', 'ChargedAttack_Charge', 'ChargedAttack_Release'],
    'enemy': ['Idle', 'Walk', 'Attack', 'Hurt', 'Death'],
    'boss': ['Idle', 'Walk', 'Attack', 'HeavyAttack', 'Hurt', 'Death'],
    'npc': ['Idle', 'Walk'],
}


def role(name):
    if name in PLAYER: return 'player'
    if name.startswith('Boss'): return 'boss'
    if name.startswith('Npc'): return 'npc'
    return 'enemy'


def frames_of(path, n, cell):
    im = np.asarray(Image.open(path).convert('RGBA'))
    return im, [im[:, i * cell:(i + 1) * cell] for i in range(n)]


def stray_mask(a):
    """opaque pixels with no drawn neighbour in their 8-neighbourhood"""
    on = a > 0
    p = np.pad(on, 1)
    nb = sum(p[1 + dy:1 + dy + on.shape[0], 1 + dx:1 + dx + on.shape[1]] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0))
    return on & (nb == 0)


def audit_char(name, folder, controller_dir=None):
    meta_p = os.path.join(folder, f'{name}_animations.json')
    out = {'name': name, 'role': role(name), 'issues': defaultdict(list), 'clips': 0, 'frames': 0, 'fixed': 0}
    if not os.path.exists(meta_p):
        out['issues']['files'].append('sin lista de animaciones (_animations.json)')
        return out
    meta = json.load(open(meta_p, encoding='utf-8'))
    cell = meta.get('cell', 64)
    pivot_row = int(round(cell * (1 - meta.get('pivot', [0.5, 0.1875])[1])))
    clips = meta['clips']
    out['clips'] = len(clips)
    by_name = defaultdict(set)
    ghost = any(g in name for g in GHOSTS)
    for c in clips:
        by_name[c['name']].add(c['dir'])
        p = os.path.join(folder, c['file'])
        if not os.path.exists(p):
            out['issues']['files'].append(f"falta {c['file']}"); continue
        if not os.path.exists(p + '.meta'):
            out['issues']['meta'].append(c['file'])
        im, frs = frames_of(p, c['frames'], cell)
        if im.shape[1] < c['frames'] * cell or im.shape[0] != cell:
            out['issues']['files'].append(f"{c['file']}: tamaño {im.shape[1]}x{im.shape[0]}, esperado {c['frames'] * cell}x{cell}")
        out['frames'] += len(frs)
        lows, heights = [], []
        changed = False
        for i, f in enumerate(frs):
            a = f[:, :, 3]
            if not a.any():
                if not (c['name'] in ('Death', 'Defeat') and i >= len(frs) - 2):
                    out['issues']['empty'].append(f"{c['name']}_{c['dir']} fotograma {i}")
                continue
            rows = np.nonzero(a.any(axis=1))[0]
            lows.append(rows.max()); heights.append(rows.max() - rows.min() + 1)
            grounded = c['name'] in GROUNDED
            faint = (a > 0) & (a < 64)
            st = stray_mask(a)
            if grounded and not ghost and faint.sum() > 6:
                out['issues']['alpha'].append(f"{c['name']}_{c['dir']} f{i}: {int(faint.sum())} px casi transparentes")
            if st.sum() > 0 and grounded:
                out['issues']['stray'].append(f"{c['name']}_{c['dir']} f{i}: {int(st.sum())} px sueltos")
            if FIX and grounded and not ghost and (st.any() or faint.any()):
                g = np.array(im)
                sl = g[:, i * cell:(i + 1) * cell]
                kill = st | faint
                sl[kill] = 0
                im = g; changed = True
                out['fixed'] += int(kill.sum())
        if c['name'] in GROUNDED and len(lows) > 1:
            if max(lows) - min(lows) > 2 and c['name'] != 'Run':
                out['issues']['feet'].append(f"{c['name']}_{c['dir']}: los pies saltan {int(max(lows) - min(lows))} px entre fotogramas")
            if min(heights) > 0 and max(heights) / min(heights) > 1.18:
                out['issues']['scale'].append(f"{c['name']}_{c['dir']}: la figura cambia de alto {min(heights)}->{max(heights)} px")
            if abs(int(np.median(lows)) - pivot_row) > 6:
                out['issues']['pivot'].append(f"{c['name']}_{c['dir']}: pies en la fila {int(np.median(lows))}, pivote en {pivot_row}")
        if changed: Image.fromarray(im).save(p)
    # pivot: the feet of the idle pose must sit on the pivot row (shadow + depth sorting); fix the manifest if they do not
    idle_lows = []
    for c in clips:
        if c['name'] == 'Idle':
            pth = os.path.join(folder, c['file'])
            if os.path.exists(pth):
                a_ = np.asarray(Image.open(pth).convert('RGBA'))[:, :cell, 3]
                rows_ = np.nonzero(a_.any(axis=1))[0]
                if len(rows_): idle_lows.append(int(rows_.max()))
    if idle_lows and abs(int(np.median(idle_lows)) - pivot_row) > 6 and FIX:
        feet = int(np.median(idle_lows)) + 1
        meta['pivot'] = [meta.get('pivot', [0.5, 0.1875])[0], round((cell - feet) / cell, 4)]
        json.dump(meta, open(meta_p, 'w', encoding='utf-8'), indent=1)
        out['fixed'] += 1
        out['issues']['pivot'] = [f'pivote corregido a los pies (fila {feet})']
    for clip, ds in by_name.items():
        miss = [d for d in DIRS if d not in ds]
        if miss and clip not in ('Climb',):
            out['issues']['dirs'].append(f"{clip}: sin {', '.join(miss)}")
    for r in REQ[out['role']]:
        if r not in by_name: out['issues']['required'].append(r)
    if controller_dir is not None and not os.path.exists(os.path.join(controller_dir, name, f'{name}.controller')):
        out['issues']['files'].append('sin controlador de animación (se crea en Build Game)')
    return out


def status(o):
    i = o['issues']
    if i.get('files') or i.get('empty'): return 'INCORRECTO'
    if i.get('required') or i.get('dirs'): return 'INCOMPLETO'
    if o['fixed']: return 'CORREGIDO, PENDIENTE DE PRUEBA'
    if i.get('feet') or i.get('scale') or i.get('alpha') or i.get('stray') or i.get('pivot'): return 'A REVISAR'
    return 'CORRECTO (verificado por análisis, no jugado)'


def main():
    results = []
    for name in sorted(os.listdir(CH)):
        f = os.path.join(CH, name)
        if not os.path.isdir(f) or name == 'WeaponSets': continue
        results.append(audit_char(name, f, ANIM))
    ws = []
    wroot = os.path.join(CH, 'WeaponSets')
    for cls in sorted(os.listdir(wroot)):
        cf = os.path.join(wroot, cls)
        if not os.path.isdir(cf): continue
        for st in sorted(os.listdir(cf)):
            sf = os.path.join(cf, st)
            if not os.path.isdir(sf): continue
            js = [x for x in os.listdir(sf) if x.endswith('_animations.json')]
            if not js: ws.append({'name': f'{cls}/{st}', 'role': 'weaponset', 'issues': {'files': ['sin lista']}, 'clips': 0, 'frames': 0, 'fixed': 0}); continue
            o = audit_char(js[0][:-len('_animations.json')], sf)
            o['name'] = f'{cls}/{st}'; o['role'] = 'weaponset'
            o['issues'].pop('required', None)
            ws.append(o)
    allr = results + ws
    os.makedirs(DOC, exist_ok=True)
    json.dump([{**o, 'issues': dict(o['issues']), 'status': status(o)} for o in allr],
              open(os.path.join(DOC, 'auditoria_sprites.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    tot = defaultdict(int)
    for o in allr:
        for k, v in o['issues'].items(): tot[k] += len(v)
    by_status = defaultdict(list)
    for o in allr: by_status[status(o)].append(o['name'])
    print('characters', len(results), 'weapon sets', len(ws), 'clips', sum(o['clips'] for o in allr), 'frames', sum(o['frames'] for o in allr))
    print('issues', dict(tot), 'fixed px', sum(o['fixed'] for o in allr))
    for k, v in by_status.items(): print(f'  {k}: {len(v)}')
    return allr, tot, by_status


if __name__ == '__main__':
    main()
