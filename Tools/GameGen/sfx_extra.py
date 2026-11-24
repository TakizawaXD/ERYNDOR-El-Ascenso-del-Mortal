"""Extra sound effects for stamina combat, crafting, camps and NPCs (same synth as sfx.py, without touching the others).

  python sfx_extra.py G:/Juegos/Assets/Game/Audio
"""
import os, random, sys
sys.path.insert(0, os.path.dirname(__file__))
from sfx import write, tone, noise, mix, seq   # noqa: E402

random.seed(7)


def build(root):
    fx = {
        'parry': seq(mix(tone(1600, 1500, .05, .3, .125), noise(.04, .3, .95, .2)), tone(2100, 1900, .16, .22, .25)),
        'riposte': mix(noise(.25, .45, .5, .5), tone(260, 70, .25, .3)),
        'guard_break': seq(mix(tone(700, 300, .1, .3, .125), noise(.12, .4, .7, .4)), tone(200, 120, .2, .2)),
        'tired': seq(tone(330, 300, .07, .12, .5), tone(260, 240, .1, .1, .5)),
        'anvil': mix(tone(1800, 1700, .09, .25, .125), tone(900, 880, .18, .15, .25), noise(.03, .25, .95, .2)),
        'craft': seq(noise(.05, .2, .6, .3), tone(523, 523, .05, .2, .25), tone(784, 784, .12, .2, .25)),
        'gather': seq(noise(.07, .25, .5, .3), tone(740, 880, .08, .18, .25)),
        'eat': seq(noise(.05, .2, .3, .3), noise(.05, .2, .3, .3), tone(440, 520, .1, .15, .5)),
        'talk': seq(tone(520, 560, .04, .12, .5), tone(470, 430, .05, .12, .5)),
        'bomb': mix(noise(.5, .5, .2, .7), tone(120, 40, .45, .3)),
    }
    for k, v in fx.items():
        write(os.path.join(root, f'sfx_{k}.wav'), v)
    return len(fx)


if __name__ == '__main__':
    print(build(sys.argv[1]))
    import sfx2   # the second-generation effects replace these ones (variants, voices, surfaces)
    print(sfx2.build(sys.argv[1]), 'effects (sfx2)')
