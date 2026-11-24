"""Kitten in the style of the Cute Fantasy animals (same sheet layout as Cow/Pig/Sheep/Chicken):
64x64 sheet, 32x32 cells, row 0 = idle (2 frames: tail sway + blink), row 1 = walk (2 frames), facing left.

  python cat.py -> Assets/Art/External/CuteFantasy/animal_cat_32x32.png  (+ Documentation/Previews/cat_preview.png)

Original art made for this project (only the palette rules follow the pack: #0e071b outline, two-tone fill,
soft black shadow).
"""
import os
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PAL = {
    'o': (14, 7, 27, 255),        # outline (pack colour)
    '#': (246, 160, 74, 255),     # orange fur
    'h': (255, 206, 138, 255),    # light fur
    'd': (204, 106, 48, 255),     # stripes
    'w': (255, 246, 230, 255),    # white muzzle / chest / paws
    'p': (246, 129, 135, 255),    # nose / inner ear (pack pink)
    'g': (120, 200, 90, 255),     # eye
    'k': (14, 7, 27, 255),        # pupil / closed eye
    's': (0, 0, 0, 100),          # shadow (pack: black at alpha 100)
    '.': (0, 0, 0, 0),
}

# 32x32 frames; the cat looks left, tail on the right
IDLE_A = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "........o...o...................",
    ".......o#o.o#o..........oo......",
    ".......opo.opo.........o#ho.....",
    "......o#######o........o##o.....",
    "......o#hh#hh#o.........o#o.....",
    ".....o#gk###gk#o........o#o.....",
    ".....o##########o......o#o......",
    ".....o#ww#p#ww#oooooooo#o.......",
    "......o#wwwww#o#h#hh#h##o.......",
    ".......o#www#o#d##dd##d#o.......",
    "........o###o##########o........",
    "........o#ww####d####d#o........",
    "........o#ww###########o........",
    "........o#wwoooooooo#ww#o.......",
    "........ow#wo......o#ww#o.......",
    "........oooo.......ooooo........",
    "........sssssssssssssssss.......",
    "..........sssssssssssss.........",
    "................................",
]

IDLE_B = [r for r in IDLE_A]
# tail sways right and the cat blinks
IDLE_B[8] = "................................"
IDLE_B[9] = ".......opo.opo...........oo.....".replace("opo.opo", "opo.opo")
IDLE_B[8] = ".......o#o.o#o...........oo....."
IDLE_B[9] = ".......opo.opo..........o#ho...."
IDLE_B[10] = "......o#######o.........o##o...."
IDLE_B[11] = "......o#hh#hh#o.........o#o....."
IDLE_B[12] = ".....o#kkk#kkk#o.......o#o......"

WALK_A = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "........o...o...................",
    ".......o#o.o#o...........oo.....",
    ".......opo.opo..........o#ho....",
    "......o#######o.........o##o....",
    "......o#hh#hh#o..........o#o....",
    ".....o#gk###gk#o.........o#o....",
    ".....o##########o.......o#o.....",
    ".....o#ww#p#ww#oooooooo#o.......",
    "......o#wwwww#o#h#hh#h##o.......",
    ".......o#www#o#d##dd##d#o.......",
    "........o###o##########o........",
    "........o#w#####d####d##o.......",
    ".......o#ww#oooooooo#ww#o.......",
    "......o#ww#o.........o#w#o......",
    "......oooo............oooo......",
    ".......sssssssssssssssssss......",
    ".........sssssssssssssss........",
    "................................",
]

WALK_B = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "........o...o...................",
    ".......o#o.o#o..........oo......",
    ".......opo.opo.........o#ho.....",
    "......o#######o........o##o.....",
    "......o#hh#hh#o.........o#o.....",
    ".....o#gk###gk#o.........o#o....",
    ".....o##########o.......o#o.....",
    ".....o#ww#p#ww#oooooooo#o.......",
    "......o#wwwww#o#h#hh#h##o.......",
    ".......o#www#o#d##dd##d#o.......",
    "........o###o##########o........",
    "........o#ww####d####d#o........",
    ".........o#w#oooooooo#ww#o......",
    "..........o#wo.......o#ww#o.....",
    "..........oooo........ooooo.....",
    "........ssssssssssssssssss......",
    "..........ssssssssssssss........",
    "................................",
    "................................",
]


# being stroked: sits down, eyes shut happily (^ ^), tail curls up; frame B leans into the hand with the tail swayed
PET_A = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "..........o...o.................",
    ".........o#o.o#o................",
    ".........opo.opo.......oo.......",
    "........o#######o.....o#ho......",
    "........o#hh#hh#o.....o##o......",
    ".......o#k#k#k#k#o.....o#o......",
    ".......o##########o....o#o......",
    ".......o#ww#p#ww##o...o#o.......",
    "........o#wwwww#oo#oo#o.........",
    ".........o#www#o#h#h##o.........",
    "........o#######d##d###o........",
    "........o#ww########d##o........",
    "........o#ww###########o........",
    "........o#ww#ooooo###ww#o.......",
    "........oowwo.....oowwwoo.......",
    "........sooo.......ooooo........",
    ".........ssssssssssssssss.......",
    "................................",
]
PET_B = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "..........o...o.................",
    ".........o#o.o#o........oo......",
    ".........opo.opo.......o#ho.....",
    "........o#######o......o##o.....",
    "........o#hh#hh#o.......o#o.....",
    ".......o#k#k#k#k#o......o#o.....",
    ".......o##########o....o#o......",
    ".......o#ww#p#ww##ooooo#o.......",
    "........o#wwwww#o#h#h##o........",
    ".........o#www#o#d##d##o........",
    "........o#######d######o........",
    "........o#ww###########o........",
    "........o#ww#ooooo###ww#o.......",
    "........oowwo.....oowwwoo.......",
    "........sooo.......ooooo........",
    ".........ssssssssssssssss.......",
    "................................",
]

HEART = [
    ".oo.oo.",
    "oppopho",
    "opppppo",
    ".opppo.",
    "..opo..",
    "...o...",
]


# grey & white kitten: grey coat with darker stripes, white chest and paws, amber eyes
GREY = dict(PAL, **{'#': (150, 157, 175, 255), 'h': (208, 213, 226, 255), 'd': (94, 101, 124, 255), 'g': (240, 190, 60, 255)})


def frame(rows, pal=PAL):
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    for y, r in enumerate(rows[:32]):
        for x, ch in enumerate(r[:32]):
            if ch in pal and ch != '.':
                im.putpixel((x, y), pal[ch])
    return im


def make_sheet(pal, name):
    # rows: idle, walk, pet (stroked)
    sheet = Image.new('RGBA', (64, 96), (0, 0, 0, 0))
    for i, f in enumerate([IDLE_A, IDLE_B, WALK_A, WALK_B, PET_A, PET_B]):
        sheet.alpha_composite(frame(f, pal), ((i % 2) * 32, (i // 2) * 32))
    sheet.save(os.path.join(ROOT, 'Assets', 'Art', 'External', 'CuteFantasy', name))
    return sheet


def build():
    make_sheet(GREY, 'animal_catgrey_32x32.png')
    sheet = make_sheet(PAL, 'animal_cat_32x32.png')
    out = 'animal_cat_32x32.png + animal_catgrey_32x32.png'
    heart = Image.new('RGBA', (8, 8), (0, 0, 0, 0))
    for y, r in enumerate(HEART):
        for x, ch in enumerate(r):
            if ch != '.': heart.putpixel((x, y + 1), PAL[ch] if ch != 'h' else (255, 214, 220, 255))
    heart.save(os.path.join(ROOT, 'Assets', 'Art', 'External', 'CuteFantasy', 'fx_heart.png'))
    grey = Image.open(os.path.join(ROOT, 'Assets', 'Art', 'External', 'CuteFantasy', 'animal_catgrey_32x32.png'))
    pv = Image.new('RGBA', (64 * 2 + 24, 96), (90, 140, 80, 255))
    pv.alpha_composite(sheet, (8, 0)); pv.alpha_composite(grey, (80, 0))
    pv.resize((pv.width * 6, pv.height * 6), Image.NEAREST).save(os.path.join(ROOT, 'Documentation', 'Previews', 'cat_preview.png'))
    print('cat sheet', out)


if __name__ == '__main__':
    build()
