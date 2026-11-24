"""python build.py [Char ...]  -> sheets + manifest under Assets/Art/Characters/<Char>/"""
import json, os, sys
from engine import *
from anims import Builder
from source import CHARS

CAT_DIR = {'Idle': 'Idle', 'Walk': 'Walk', 'Run': 'Run', 'Attack': 'Attack', 'Special': 'Special', 'Hurt': 'Hurt',
           'Death': 'Death', 'Combat': 'Combat', 'Dodge': 'Dodge', 'Jump': 'Jump', 'Emote': 'Emote', 'Other': 'Other'}


def build(key):
    out = Builder(key).build_all()
    root = os.path.join(OUT, key)
    man = []
    for (name, d), a in sorted(out.items()):
        rel = f'{CAT_DIR[a.cat]}/{key}_{name}_{d}.png'
        path = os.path.join(root, rel)
        save_sheet(a.frames, path)
        man.append(dict(name=name, dir=d, file=rel, frames=len(a.frames), seq=a.seq, fps=a.fps, loop=a.loop,
                        size=[CELL * len(a.frames), CELL]))
    with open(os.path.join(root, f'{key}_animations.json'), 'w') as fh:
        json.dump(dict(character=key, cell=CELL, pivot=[0.5, (CELL - FEET) / CELL], ppu=16, clips=man), fh, indent=1)
    return out, man


if __name__ == '__main__':
    keys = sys.argv[1:] or list(CHARS)
    for k in keys:
        out, man = build(k)
        print(k, len(man), 'clips,', sum(m['frames'] for m in man), 'unique frames')
