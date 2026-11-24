"""LAS CATACUMBAS DEL REY OLVIDADO - layout of the dungeon map (2026-11-21).

  python Tools/GameGen/catacombs.py
    -> Assets/Game/Levels/Dungeon_Catacumbas.txt   (map: ROOM / OBJ lines + TERRAIN / ENTITIES / REGIONS)
    -> Assets/Game/Levels/Maps_Dungeons.txt        (MAP / AREA / GATE lines appended to Maps.txt by the builder)

Six zones joined in a loop that climbs from the cemetery to the throne:
  k CEMENTERIO SUBTERRÁNEO      entrance, niches, the first traps and crypt guards
  l GALERÍAS DE LOS MINEROS     falling rocks, archers, the crumbling well
  m CRIPTAS DE LOS CABALLEROS   wall spears, cursed knights, shades, the sealed crypt
  n SANTUARIO DE LOS SACRIFICIOS runes, fire jets, funeral priests, the sacrifice key
  o PUENTE DE LOS CONDENADOS    a bridge over the abyss with crumbling planks
  p TRONO DEL REY SEPULTADO     the boss arena and the king's treasure

Terrain: '#' wall  '.' floor  ',' rubble floor  'O' pit / abyss  '=' bridge  'x' crumbling floor  's' stairs notch
         'D' door cell (floor under a door)  'S' secret passage (floor hidden behind a breakable wall)
OBJ lines: OBJ <type> <x> <row> key=value ... [| text]   (cell coordinates, x right, row down; .5 = cell centre)
"""
import os, sys
from collections import deque

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LV = os.path.join(ROOT, 'Assets', 'Game', 'Levels')
MAP_ID = 'Dungeon_Catacumbas'
W, H = 170, 130
WALK = set('.,=xsDS')

T = [['#'] * W for _ in range(H)]
R = [['k'] * W for _ in range(H)]
ROOMS, OBJS = [], []

ZONES = {
    'k': 'CEMENTERIO SUBTERRÁNEO', 'l': 'GALERÍAS DE LOS MINEROS', 'm': 'CRIPTAS DE LOS CABALLEROS',
    'n': 'SANTUARIO DE LOS SACRIFICIOS', 'o': 'PUENTE DE LOS CONDENADOS', 'p': 'TRONO DEL REY SEPULTADO',
}


# ---------------------------------------------------------------- carving
def cell(x, y, c, z=None):
    if 0 <= x < W and 0 <= y < H:
        T[y][x] = c
        if z: R[y][x] = z


def rect(x0, y0, x1, y1, z, c='.'):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            cell(x, y, c, z)


def ellipse(cx, cy, rx, ry, z, c='.'):
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1:
                cell(x, y, c, z)


def room(rid, z, x0, y0, x1, y1, name, shape='rect'):
    if shape == 'rect':
        rect(x0, y0, x1, y1, z)
    elif shape == 'ellipse':
        ellipse((x0 + x1 + 1) / 2, (y0 + y1 + 1) / 2, (x1 - x0 + 1) / 2, (y1 - y0 + 1) / 2, z)
    elif shape == 'cross':                     # a plus-shaped hall: the corners stay solid
        w, h = x1 - x0 + 1, y1 - y0 + 1
        rect(x0 + w // 4, y0, x1 - w // 4, y1, z)
        rect(x0, y0 + h // 4, x1, y1 - h // 4, z)
    elif shape == 'octagon':
        k = min(x1 - x0, y1 - y0) // 4
        for y in range(y0, y1 + 1):
            d = max(0, k - (y - y0), k - (y1 - y))
            rect(x0 + d, y, x1 - d, y, z)
    ROOMS.append((rid, z, x0, y0, x1, y1, name))


def obj(otype, x, y, text=None, **kw):
    OBJS.append((otype, x, y, kw, text))


# ======================================================================== ZONE k: CEMENTERIO SUBTERRÁNEO
# R1 - entrance hall: stairs up to the world in the north wall, the first altar (rest + save), no enemies
room('R1', 'k', 34, 110, 47, 119, 'ESCALERA DE ENTRADA')
rect(39, 108, 42, 109, 'k', 's')                        # the stairs notch in the north wall
obj('stairs', 41.0, 109.9, gate='E0')
obj('altar', 44.5, 113.5)
obj('lore', 36.5, 112.5, id='lore_entrada', text_title='LÁPIDA DE LA ENTRADA',
    text='AQUÍ YACE EL REY OLVIDADO, QUE QUISO REINAR SOBRE LA MUERTE. QUIEN BAJE ESTAS ESCALERAS QUE NO ESPERE VOLVER... SALVO QUE SU ESPADA SEA MÁS FIEL QUE SU MIEDO.')
obj('sign', 37.5, 117.5, text='LOS ALTARES BENDICEN Y GUARDAN TU PARTIDA. SI MUERES, DESPERTARÁS JUNTO AL ÚLTIMO QUE TOCASTE.')
for x, y in ((35, 111), (46, 111), (35, 118), (46, 118)): obj('candle', x + .5, y + .5)
obj('torch', 37.5, 109.6); obj('torch', 44.5, 109.6)
obj('deco', 46.5, 117.0, sprite='coffin')
obj('breakable', 35.5, 115.5, sprite='urn_red'); obj('breakable', 46.5, 115.5, sprite='urn_red_s')

# corridor R1 -> R3 (west): the first trap - spikes that rise slowly after a long warning, with a sign before them
rect(24, 113, 33, 115, 'k')
obj('sign', 32.5, 112.6, text='CUIDADO: LAS BALDOSAS CON AGUJEROS ESCUPEN PINCHOS. ESPERA A QUE SE HUNDAN Y CRUZA. (ESPACIO: RODAR)')
for y in (113, 114, 115): obj('spikes', 30.5, y + .5, period=2.6, up=1.0, offset=0)

# R3 - the underground graveyard: sarcophagi rows, urns to break, the first skeletons
room('R3', 'k', 6, 100, 27, 116, 'CAMPOSANTO SUBTERRÁNEO', 'octagon')
for i, x in enumerate((10, 14, 18, 22)):
    obj('deco', x + .5, 104.0, sprite='sarcophagus' if i % 2 == 0 else 'sarcophagus_broken')
    obj('deco', x + .5, 110.0, sprite='sarcophagus_broken' if i % 2 == 0 else 'sarcophagus')
obj('enemy', 12.5, 107.5, type='Skeleton'); obj('enemy', 20.5, 107.5, type='Skeleton'); obj('enemy', 16.5, 113.5, type='Skeleton')
for x, y in ((8, 102), (25, 102), (8, 114), (25, 114)): obj('breakable', x + .5, y + .5, sprite='urn_red')
obj('chest', 7.5, 108.5, tier='normal')
obj('torch', 12.5, 99.6); obj('torch', 21.5, 99.6)
obj('candles', 16.5, 101.5)
obj('lore', 16.5, 115.5, id='lore_sepulturero', text_title='DIARIO DEL SEPULTURERO',
    text='DÍA 40. LOS MUERTOS YA NO SE QUEDAN EN SUS NICHOS. EL REY OLVIDADO LOS LLAMA DESDE ABAJO Y ELLOS RESPONDEN. HE TAPIADO LA CAPILLA DE LAS VELAS CON MI LLAVE DE HUESO DENTRO. QUE NADIE LA BUSQUE.')

# R2 - side route A: the candle chapel (bone key, a chest, the gravedigger's fate)
rect(11, 117, 13, 120, 'k')
room('R2', 'k', 8, 121, 17, 127, 'CAPILLA DE LAS VELAS')
for x in (9, 16):
    for y in (122, 126): obj('candle', x + .5, y + .5)
obj('candles', 12.5, 122.0)
obj('key', 12.5, 124.5, id='key_hueso', name='LLAVE DE HUESO')
obj('chest', 16.5, 124.5, tier='normal')
obj('enemy', 10.5, 125.5, type='Skeleton')
obj('deco', 9.5, 124.0, sprite='skeleton_post')

# corridor R3 -> R4 (east)
rect(21, 99, 31, 101, 'k')
# R4 - the ossuary: crypt guards appear for the first time (shield up: hit them from the side or parry), a lever opens
#      the mine gate; the north wall has a hollow crack (first secret)
room('R4', 'k', 32, 92, 47, 102, 'OSARIO')
obj('enemy', 38.5, 96.5, type='CryptGuard'); obj('enemy', 42.5, 98.5, type='CryptGuard')
obj('lever', 46.5, 93.4, id='lv_osario', targets='door_mina')
obj('sign', 33.5, 101.5, text='LOS GUARDIAS DE LA CRIPTA SE CUBREN CON EL ESCUDO. RODÉALOS, GOLPÉALOS POR LA ESPALDA O DESVÍA SU ESTOCADA (F) Y CONTRAATACA.')
obj('torch', 35.5, 91.6); obj('torch', 44.5, 91.6)
for x in (33, 46): obj('breakable', x + .5, 101.5, sprite='barrel')
obj('deco', 33.5, 94.0, sprite='skeleton_post')
# secret ossuary behind the cracked wall
rect(38, 89, 40, 91, 'k', 'S')
obj('secretwall', 39.5, 91.0, id='sw_osario', x0=38, y0=89, x1=40, y1=91)
room('R4s', 'k', 35, 84, 44, 88, 'OSARIO OCULTO')
obj('chest', 39.5, 85.5, tier='hidden')
obj('lore', 36.5, 87.5, id='lore_osario', text_title='HUESOS CON NOMBRE',
    text='CADA CALAVERA LLEVA UN NOMBRE GRABADO. TODOS SON CABALLEROS DE LA GUARDIA REAL. EL REY LOS ENTERRÓ VIVOS PARA QUE LE SIRVIERAN SIEMPRE.')
obj('candle', 43.5, 85.5)

# ======================================================================== ZONE l: GALERÍAS DE LOS MINEROS
rect(48, 95, 55, 97, 'l')
obj('door', 48.0, 96.0, id='door_mina', axis='v', len=3, kind='lever')
room('R5', 'l', 56, 90, 69, 100, 'BOCA DE LA MINA')
obj('sign', 58.5, 95.0, text='EL TECHO DE LAS GALERÍAS SE DESPRENDE. SI VES POLVO CAER Y UNA SOMBRA EN EL SUELO, APÁRTATE.')
obj('rocks', 64.5, 95.5, w=5, h=5, period=3.2)
obj('enemy', 66.5, 92.5, type='BuriedArcher'); obj('enemy', 66.5, 98.5, type='Skeleton')
for x, y in ((57, 91), (68, 99), (57, 99)): obj('breakable', x + .5, y + .5, sprite='barrel')
obj('torch', 60.5, 89.6); obj('torch', 66.5, 89.6)
obj('deco', 68.5, 91.2, sprite='crate_stack')

# R6 - the long gallery: an L that bends south, falling rocks, archers behind guards
rect(70, 94, 71, 96, 'l')
room('R6', 'l', 72, 92, 109, 98, 'GALERÍA LARGA')
rect(100, 99, 109, 106, 'l')
for x in (78, 86, 94):
    obj('pillar', x + .5, 92.9); obj('pillar', x + .5, 98.9)
obj('rocks', 82.5, 95.5, w=6, h=5, period=2.8, offset=0.6)
obj('rocks', 104.5, 102.5, w=6, h=6, period=3.0, offset=1.4)
obj('enemy', 88.5, 95.5, type='CryptGuard'); obj('enemy', 98.5, 94.5, type='BuriedArcher'); obj('enemy', 98.5, 97.5, type='BuriedArcher')
obj('enemy', 106.5, 100.5, type='CryptGuard')
obj('torch', 74.5, 91.6); obj('torch', 90.5, 91.6); obj('torch', 106.5, 91.6)
for x, y in ((73, 97), (108, 105), (101, 105)): obj('breakable', x + .5, y + .5, sprite='barrel_s')
obj('lore', 75.5, 93.5, id='lore_minero', text_title='NOTA DEL CAPATAZ',
    text='CAVAMOS BUSCANDO PLATA Y ENCONTRAMOS UNA PUERTA. DETRÁS HABÍA ESCALERAS QUE BAJABAN MÁS DE LO QUE NINGÚN POZO DEBERÍA. LOS QUE BAJARON VOLVIERON... PERO YA NO RESPIRABAN.')

# R6b - side route B: the abandoned vein (from R5 south), with the miner's hidden chamber behind it
rect(60, 101, 62, 105, 'l')
room('R6b', 'l', 56, 106, 68, 116, 'VETA ABANDONADA', 'cross')
obj('enemy', 62.5, 110.5, type='Skeleton'); obj('enemy', 58.5, 111.5, type='Bat'); obj('enemy', 66.5, 111.5, type='Bat')
obj('chest', 67.5, 111.0, tier='normal')
obj('deco', 57.5, 110.5, sprite='crate_stack')
obj('lore', 62.5, 114.5, id='lore_veta', text_title='GRIETA EN LA ROCA',
    text='ALGUIEN HA RASCADO UNA FLECHA EN LA PIEDRA, SEÑALANDO HACIA ABAJO: «LA PARED SUENA HUECA».')
rect(60, 117, 62, 120, 'l', 'S')
obj('secretwall', 61.5, 120.0, id='sw_minero', x0=60, y0=117, x1=62, y1=120)
room('R6s', 'l', 57, 121, 66, 126, 'CÁMARA DEL MINERO')
obj('chest', 61.5, 123.5, tier='hidden', item='hammer')
obj('lore', 58.5, 125.5, id='lore_camara', text_title='EL ÚLTIMO MINERO',
    text='ME ESCONDÍ AQUÍ CON EL MARTILLO DE LA COMPAÑÍA. OIGO A LOS GUARDIAS DEL REY MARCHAR AL OTRO LADO. TIENEN ESCUDOS: SOLO EL MARTILLO LOS HACE TAMBALEAR.')

# R7 - the collapsed well: a crumbling path over a pit (shortcut to a chest), the safe way runs along the edges
rect(103, 107, 105, 110, 'l')
room('R7', 'l', 86, 111, 109, 124, 'POZO DERRUMBADO')
rect(90, 114, 105, 121, 'l', 'O')
rect(90, 117, 99, 117, 'l', 'x')                                  # crumbling floor across the pit
rect(100, 116, 102, 118, 'l', '.')                                # a little island with a chest
obj('chest', 101.5, 117.5, tier='normal')
obj('sign', 88.5, 112.5, text='EL SUELO AGRIETADO CRUJE Y SE HUNDE SI TE QUEDAS QUIETO. CRUZA RÁPIDO O RODEA EL POZO.')
obj('enemy', 107.5, 122.5, type='BuriedArcher'); obj('enemy', 88.5, 122.5, type='CryptGuard')
obj('torch', 92.5, 110.6); obj('torch', 104.5, 110.6)
obj('breakable', 108.5, 112.5, sprite='urn_green'); obj('breakable', 87.5, 123.5, sprite='urn_green_s')

# R8 - the lift shaft: a pressure plate opens the portcullis north (stand on it... or put a crate on it? no: it stays down)
rect(110, 115, 111, 117, 'l')
room('R8', 'l', 112, 104, 125, 118, 'POZO DEL MONTACARGAS')
obj('plate', 114.5, 116.5, id='pl_montacargas', targets='door_criptas', latch=1)
obj('door', 118.5, 103.0, id='door_criptas', axis='h', len=3, kind='plate')
obj('sign', 121.5, 116.5, text='UNA LOSA SUELTA EN EL SUELO... LAS PLACAS DE PRESIÓN MUEVEN MECANISMOS. ALGUNAS ABREN PUERTAS; OTRAS, TRAMPAS.')
obj('plate', 118.5, 110.5, id='pl_trampa', targets='fire_montacargas')
obj('firejet', 118.5, 106.0, id='fire_montacargas', dir='S', period=0, length=4)       # only fires when its plate is pressed
obj('enemy', 123.5, 106.5, type='CryptGuard'); obj('enemy', 114.5, 106.5, type='BuriedArcher')
obj('torch', 114.5, 103.6); obj('torch', 122.5, 103.6)

# ======================================================================== ZONE m: CRIPTAS DE LOS CABALLEROS
# corridor north with wall spears thrusting in sequence (a rhythm you can read: they go off one after another)
rect(117, 84, 119, 103, 'm')
obj('sign', 120.0, 101.0, text='LANZAS EN LAS PAREDES: SALEN UNA TRAS OTRA. MIRA EL RITMO Y AVANZA DETRÁS DE LA ÚLTIMA.')
for i, y in enumerate(range(98, 86, -3)):
    obj('spears', 117.0, y + .5, dir='E', group='sp_corredor', index=i, period=3.2, length=3)
room('R9', 'm', 108, 68, 127, 83, 'SALÓN DE ARMAS')
for x in (111, 124):
    for y in (71, 80): obj('pillar', x + .5, y + .9)
obj('enemy', 117.5, 72.5, type='CursedKnight')
obj('enemy', 112.5, 76.5, type='CryptGuard'); obj('enemy', 122.5, 76.5, type='CryptGuard')
obj('sign', 118.5, 82.5, text='LOS CABALLEROS MALDITOS SON LENTOS PERO UN GOLPE SUYO DUELE COMO TRES. CUANDO LEVANTEN EL ARMA, RUEDA HACIA UN LADO Y CASTIGA SU ESPALDA.')
obj('torch', 113.5, 67.6); obj('torch', 121.5, 67.6)
obj('deco', 109.5, 69.2, sprite='armor_rack'); obj('deco', 126.5, 69.2, sprite='armor_rack')
obj('chest', 126.5, 82.5, tier='normal')

# R10 - gallery of sarcophagi: shades come out of the dark; one sarcophagus is a hidden chest
rect(128, 74, 130, 76, 'm')
room('R10', 'm', 131, 70, 160, 80, 'GALERÍA DE LOS SARCÓFAGOS')
for x in range(134, 159, 5):
    obj('deco', x + .5, 72.2, sprite='sarcophagus' if x % 2 else 'sarcophagus_open')
    if x != 149: obj('deco', x + .5, 79.6, sprite='sarcophagus_broken' if x % 2 else 'sarcophagus')
obj('chest', 149.5, 79.0, tier='hidden', look='sarcophagus')
obj('enemy', 140.5, 75.5, type='CryptShade'); obj('enemy', 152.5, 75.5, type='CryptShade'); obj('enemy', 157.5, 77.5, type='CryptGuard')
obj('sign', 133.5, 79.5, text='LAS SOMBRAS ATACAN DE LADO Y SE DESVANECEN. NO LES DES LA ESPALDA: GIRA CON ELLAS Y GOLPEA CUANDO REAPAREZCAN.')
obj('torch', 137.5, 69.6); obj('torch', 147.5, 69.6); obj('torch', 156.5, 69.6)
obj('rune', 145.5, 75.5, period=3.6, radius=1.4)

# R11 - the sealed crypt (bone key): special equipment
rect(151, 65, 153, 69, 'm')
obj('door', 152.5, 69.0, id='door_cripta', axis='h', len=3, kind='key', key='key_hueso')
room('R11', 'm', 146, 52, 158, 64, 'CRIPTA SELLADA', 'octagon')
obj('chest', 152.5, 54.5, tier='special', item='armor_crypt')
obj('deco', 148.5, 57.0, sprite='sarcophagus'); obj('deco', 156.5, 57.0, sprite='sarcophagus')
for x, y in ((148, 62), (156, 62), (148, 54), (156, 54)): obj('candle', x + .5, y + .5)
obj('lore', 152.5, 60.5, id='lore_cripta', text_title='SIR ALDRIC, PRIMER ESCUDO',
    text='YO JURÉ PROTEGER AL REY Y NO AL REINO. CUANDO SE CORONÓ CON HUESOS DE SUS SÚBDITOS, LE DI LA ESPALDA. ME ENCERRÓ AQUÍ CON MI ARMADURA. TÓMALA: QUE AL MENOS ELLA LE PLANTE CARA.')
obj('enemy', 152.5, 58.5, type='CursedKnight', rank='elite')

# R12 - guard house: the hardest mixed fight so far, then an altar
rect(116, 63, 118, 67, 'm')
room('R12', 'm', 108, 46, 126, 62, 'CUERPO DE GUARDIA')
obj('enemy', 117.5, 50.5, type='CursedKnight'); obj('enemy', 112.5, 49.5, type='BuriedArcher'); obj('enemy', 122.5, 49.5, type='BuriedArcher')
obj('enemy', 117.5, 55.5, type='CryptGuard')
obj('encounter', 117.0, 54.0, id='enc_guardia', x0=108, y0=46, x1=126, y1=62, doors='door_guardia_s,door_guardia_w')
obj('door', 117.5, 63.0, id='door_guardia_s', axis='h', len=3, kind='encounter', open=1)
obj('altar', 124.5, 60.0)
obj('torch', 112.5, 45.6); obj('torch', 122.5, 45.6)
obj('breakable', 109.5, 61.5, sprite='barrel'); obj('breakable', 125.5, 47.5, sprite='barrel_s')
obj('lore', 110.5, 60.5, id='lore_guardia', text_title='ÓRDENES DEL CAPITÁN',
    text='NADIE CRUZA AL SANTUARIO. LOS SACERDOTES PREPARAN EL ÚLTIMO SACRIFICIO: CUANDO EL REY TENGA BASTANTES ALMAS, SE LEVANTARÁ DEL TRONO Y SUBIRÁ AL MUNDO.')

# ======================================================================== ZONE n: SANTUARIO DE LOS SACRIFICIOS
rect(98, 52, 107, 54, 'n')
obj('door', 107.0, 53.0, id='door_guardia_w', axis='v', len=3, kind='encounter', open=1)
room('R13', 'n', 80, 44, 97, 58, 'ATRIO DE LAS RUNAS')
obj('sign', 96.0, 56.5, text='LAS RUNAS DEL SUELO SE CARGAN, BRILLAN Y ESTALLAN. CUENTA SUS LATIDOS: CUANDO SE APAGAN, PISA.')
for i, (x, y) in enumerate(((84, 48), (88, 51), (92, 48), (84, 54), (92, 54), (88, 45))):
    obj('rune', x + .5, y + .5, period=3.0, offset=i * 0.5, radius=1.3)
obj('enemy', 86.5, 50.5, type='FuneralPriest'); obj('enemy', 90.5, 47.5, type='Skeleton'); obj('enemy', 90.5, 55.5, type='Skeleton')
obj('torch', 84.5, 43.6); obj('torch', 92.5, 43.6)
obj('candles', 88.5, 57.0)

rect(71, 50, 79, 52, 'n')
# R14 - the sacrifice altar (round hall): fire jets on a timer around the altar, priests behind guards
room('R14', 'n', 46, 45, 70, 63, 'ALTAR DEL SACRIFICIO', 'ellipse')
obj('altarstone', 58.0, 54.0)
for x, y, d in ((52.5, 49.0, 'S'), (63.5, 49.0, 'S'), (52.5, 59.0, 'N'), (63.5, 59.0, 'N')):
    obj('firejet', x, y, dir=d, period=3.4, length=3, offset=0 if x < 58 else 1.7)
obj('enemy', 54.5, 52.5, type='FuneralPriest'); obj('enemy', 62.5, 56.5, type='FuneralPriest')
obj('enemy', 58.5, 50.5, type='CryptGuard'); obj('enemy', 58.5, 58.5, type='CryptGuard'); obj('enemy', 66.5, 54.5, type='BuriedArcher')
obj('encounter', 58.0, 54.0, id='enc_sacrificio', x0=46, y0=45, x1=70, y1=63, doors='door_sacrificio_e', reward='key_sacrificio')
obj('door', 71.0, 51.0, id='door_sacrificio_e', axis='v', len=3, kind='encounter', open=1)
obj('lore', 66.5, 60.0, id='lore_altar', text_title='LIBRO DE LOS RITOS',
    text='SIETE VECES SIETE ALMAS PARA EL REY OLVIDADO. QUE SU CORONA SE PARTA EN TANTOS PEDAZOS COMO JURAMENTOS ROMPIÓ, Y QUE CADA PEDAZO LO ATE A SU TRONO.')
obj('torch', 52.5, 44.6); obj('torch', 63.5, 44.6)
# the secret room: the high priest's treasure, west of the altar behind a hollow wall (the wall has a crack and a draft)
rect(41, 51, 46, 53, 'n', 'S')
obj('secretwall', 45.5, 52.0, id='sw_sumo', x0=41, y0=51, x1=46, y1=53, side=1)
room('R14s', 'n', 30, 47, 40, 57, 'TESORO DEL SUMO SACERDOTE')
obj('chest', 33.5, 52.0, tier='hidden', item='dagger_venom')
obj('chest', 37.5, 49.5, tier='normal')
obj('lore', 35.5, 55.5, id='lore_sumo', text_title='CONFESIÓN DEL SUMO SACERDOTE',
    text='EL REY NO PUEDE MORIR MIENTRAS SU CORONA ESTÉ ENTERA. YO LA ROMPÍ EN SECRETO LA NOCHE DEL ÚLTIMO RITO. CUANDO SU ARMADURA CEDA, SU MAGIA SE VOLVERÁ CONTRA ÉL: GOLPEA ENTONCES.')
for x, y in ((31, 48), (39, 48), (31, 56), (39, 56)): obj('candle', x + .5, y + .5)

# side route C: the cells of the condemned (south of the altar), opened by a hidden plate in the altar hall
rect(56, 64, 58, 67, 'n')
obj('door', 57.5, 64.0, id='door_celdas', axis='h', len=3, kind='plate')
obj('plate', 48.5, 54.5, id='pl_celdas', targets='door_celdas', latch=1, hidden=1)
room('R14c', 'n', 48, 68, 66, 76, 'CELDAS DE LOS CONDENADOS')
for x in (51, 56, 61):
    obj('bars', x + .5, 71.0)
obj('deco', 50.5, 69.4, sprite='skeleton_post'); obj('deco', 60.5, 69.4, sprite='chains')
obj('enemy', 53.5, 73.5, type='CryptShade'); obj('enemy', 62.5, 73.5, type='Skeleton')
obj('chest', 64.5, 69.5, tier='normal')
obj('lore', 49.5, 74.5, id='lore_celdas', text_title='GRABADO EN LA PARED',
    text='ME LLAMO ELARA. MAÑANA ME TOCA EL ALTAR. SI ALGUIEN LEE ESTO: EL REY TEME LA LUZ DE LAS RUNAS QUE ÉL MISMO GRABÓ. CUANDO PIERDE LA ARMADURA, SUS PROPIOS HECHIZOS LO QUEMAN.')

# north: the sacrifice key opens the way to the bridge
rect(56, 38, 58, 44, 'n')
obj('door', 57.5, 44.0, id='door_sacrificio_n', axis='h', len=3, kind='key', key='key_sacrificio')

# ======================================================================== ZONE o: PUENTE DE LOS CONDENADOS
room('R15', 'o', 48, 27, 66, 37, 'ANTESALA DEL ABISMO')
obj('enemy', 52.5, 31.5, type='CryptGuard'); obj('enemy', 62.5, 31.5, type='CryptGuard'); obj('enemy', 57.5, 29.5, type='FuneralPriest')
obj('torch', 52.5, 26.6); obj('torch', 62.5, 26.6)
obj('lore', 50.5, 35.5, id='lore_puente', text_title='EL PUENTE DE LOS CONDENADOS',
    text='A LOS TRAIDORES SE LES HACÍA CRUZAR EL PUENTE CON LAS MANOS ATADAS. LAS TABLAS PODRIDAS DECIDÍAN. DICEN QUE AÚN SE OYEN CAER.')
rect(60, 20, 62, 26, 'o')
rect(60, 22, 69, 24, 'o')
room('R16', 'o', 70, 14, 118, 34, 'PUENTE DE LOS CONDENADOS')
rect(74, 15, 114, 33, 'o', 'O')                                  # the abyss
rect(74, 22, 114, 25, 'o', '=')                                  # the main bridge, 4 wide
rect(84, 22, 86, 25, 'o', 'x'); rect(100, 22, 101, 25, 'o', 'x')  # rotten planks
rect(87, 15, 96, 18, 'o', '.'); rect(91, 19, 92, 21, 'o', '=')    # north platform (chest) on a narrow walkway
rect(104, 29, 112, 33, 'o', '.'); rect(107, 26, 108, 28, 'o', '=')  # south platform (archers)
obj('chest', 91.5, 16.5, tier='normal', item='bow_bone')
obj('enemy', 106.5, 31.5, type='BuriedArcher'); obj('enemy', 110.5, 31.5, type='BuriedArcher')
obj('enemy', 93.5, 23.5, type='CryptShade'); obj('enemy', 110.5, 23.5, type='CryptShade')
obj('rocks', 79.5, 23.5, w=4, h=4, period=3.4)
obj('rocks', 96.5, 23.5, w=4, h=4, period=3.4, offset=1.7)
obj('sign', 71.5, 21.5, text='LAS TABLAS PODRIDAS SE HUNDEN TRAS PISARLAS. SI CAES AL ABISMO PERDERÁS VIDA Y VOLVERÁS AL ÚLTIMO SUELO FIRME.')
obj('torch', 72.5, 13.6); obj('torch', 116.5, 13.6)
obj('enemy', 116.5, 23.5, type='CursedKnight')

rect(119, 23, 121, 25, 'o')
room('R17', 'o', 122, 20, 133, 30, 'PUERTA DEL REY')
obj('altar', 125.5, 27.5)
obj('lore', 131.5, 28.5, id='lore_rey', text_title='LAS ÚLTIMAS PALABRAS DEL HERALDO',
    text='«ARRODILLAOS ANTE EL REY SEPULTADO, SEÑOR DE LOS NICHOS, PORTADOR DE LA CORONA FRAGMENTADA». MÁS ABAJO, CON OTRA LETRA: «SU ESPADA PESA. CUANDO LA LEVANTA SOBRE LA CABEZA, TIENES UN LATIDO PARA APARTARTE».')
for x, y in ((123, 21), (132, 21)): obj('candle', x + .5, y + .5)
obj('torch', 125.5, 19.6); obj('torch', 130.5, 19.6)

# ======================================================================== ZONE p: TRONO DEL REY SEPULTADO
rect(134, 24, 137, 26, 'p')
obj('door', 137.0, 25.0, id='door_trono', axis='v', len=3, kind='boss', open=1)
room('R18', 'p', 138, 4, 166, 30, 'SALA DEL TRONO')
obj('throne', 152.0, 6.6)
obj('boss', 152.0, 9.5, type='KingSepulcher')
obj('arena', 152.0, 17.0, x0=138, y0=4, x1=166, y1=30)
for (x, y) in ((143, 10), (161, 10), (143, 24), (161, 24), (147, 17), (157, 17)):
    obj('column', x + .5, y + .5)
for i, (x, y) in enumerate(((141, 15), (163, 15), (150, 27), (154, 27))):
    obj('collapse', x + .5, y + .5, w=3, h=3, index=i)
for i, (x, y) in enumerate(((145, 7), (159, 7), (145, 27), (159, 27), (152, 21))):
    obj('arenarune', x + .5, y + .5, index=i)
obj('torch', 144.5, 3.6); obj('torch', 159.5, 3.6)
obj('brazier', 140.5, 6.5); obj('brazier', 163.5, 6.5); obj('brazier', 140.5, 28.5); obj('brazier', 163.5, 28.5)
# the king's treasure behind the throne hall (opens when he falls)
rect(151, 31, 153, 34, 'p')
obj('door', 152.5, 31.0, id='door_tesoro', axis='h', len=3, kind='victory')
room('R19', 'p', 144, 35, 160, 44, 'CÁMARA DEL REY')
rect(156, 33, 159, 34, 'p', 's')
obj('stairs', 158.0, 34.9, gate='X0')
obj('chest', 148.5, 38.5, tier='legendary', item='king_blade')
obj('relic', 152.5, 37.5, id='corona_fragmentada', name='LA CORONA FRAGMENTADA')
obj('relic', 145.5, 42.5, id='reliquia_juramento', name='SELLO DEL JURAMENTO')
obj('lore', 154.5, 42.5, id='lore_final', text_title='EL REY OLVIDADO',
    text='FUE UN REY JUSTO DURANTE TREINTA INVIERNOS. EL TRIGÉSIMO PRIMERO TUVO MIEDO DE MORIR. ESTAS CATACUMBAS SON SU MIEDO HECHO PIEDRA. AHORA, POR FIN, DUERME DE VERDAD.')
for x, y in ((145, 36), (159, 36), (145, 43), (159, 43)): obj('candle', x + .5, y + .5)


# ======================================================================== validation + output
def neighbours(x, y):
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < W and 0 <= ny < H: yield nx, ny


def reach(start, blocked=lambda x, y: False):
    seen = {start}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for nx, ny in neighbours(x, y):
            if (nx, ny) in seen or T[ny][nx] not in WALK or blocked(nx, ny): continue
            seen.add((nx, ny)); q.append((nx, ny))
    return seen


def validate():
    start = (41, 113)
    allr = reach(start)
    bad = [r[0] for r in ROOMS if (int((r[2] + r[4]) / 2), int((r[3] + r[5]) / 2)) not in allr
           and not any((x, y) in allr for y in range(r[3], r[5] + 1) for x in range(r[2], r[4] + 1))]
    # the main path never needs a secret wall
    main = reach(start, lambda x, y: T[y][x] == 'S')
    boss_ok = (152, 17) in main
    secrets = sum(1 for o in OBJS if o[0] == 'secretwall')
    return bad, boss_ok, secrets


def fmt(v):
    return f'{v:g}' if isinstance(v, (int, float)) else str(v).replace(' ', '_')


def main():
    bad, boss_ok, secrets = validate()
    print(MAP_ID, f'{W}x{H}', 'rooms', len(ROOMS), 'objects', len(OBJS), 'unreachable', bad, 'boss reachable', boss_ok, 'secrets', secrets)
    if bad or not boss_ok:
        raise SystemExit('layout broken')
    out = ['TITLE LAS CATACUMBAS DEL REY OLVIDADO', 'SUBTITLE BAJO EL BOSQUE CORRUPTO', f'SIZE {W} {H}']
    for (rid, z, x0, y0, x1, y1, name) in ROOMS:
        out.append(f'ROOM {rid} {z} {x0} {y0} {x1} {y1} {name}')
    for (kind, x, y, kw, text) in OBJS:
        extra = dict(kw)
        tt = extra.pop('text', None) or text
        line = f'OBJ {kind} {x:g} {y:g} ' + ' '.join(f'{k}={fmt(v)}' for k, v in extra.items())
        if tt: line += ' | ' + tt
        out.append(line.rstrip())
    out.append('TERRAIN')
    out += [''.join(r) for r in T]
    out.append('ENTITIES')
    out += [' ' * W for _ in range(H)]
    out.append('REGIONS')
    out += [''.join(r) for r in R]
    for z, n in ZONES.items(): out.append(f'REGIONNAME {z} {n}')
    with open(os.path.join(LV, MAP_ID + '.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')

    # catalog: the entrance sits where the road through the Corrupt Forest ends (World2 x23-24, row 25)
    WH = 160
    cat = ['# generated by Tools/GameGen/catacombs.py (appended to Maps.txt by the builder)',
           f'MAP {MAP_ID} dungeon {W} {H} k LAS CATACUMBAS DEL REY OLVIDADO|BAJO EL BOSQUE CORRUPTO',
           f'AREA {MAP_ID} 21 23 26 26 0',
           # world -> dungeon: the dark opening of the arch; arrival in front of it
           f'GATE World {MAP_ID}:S0 24.0 {WH - 25 - 0.5} 2 1 24.0 {WH - 28 - 0.3:.1f} 0 -1 {MAP_ID} E0',
           # dungeon stairs (entrance) and the exit stairs behind the throne, both lead to the arch in the forest
           f'GATE {MAP_ID} E0 41.0 {H - 109.0} 4 2 41.0 {H - 113.5} 0 -1 World {MAP_ID}:S0',
           f'GATE {MAP_ID} X0 158.0 {H - 34.0} 4 2 158.0 {H - 38.5} 0 -1 World {MAP_ID}:S0']
    with open(os.path.join(LV, 'Maps_Dungeons.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(cat) + '\n')
    print('wrote', MAP_ID + '.txt', 'and Maps_Dungeons.txt')


if __name__ == '__main__':
    main()
