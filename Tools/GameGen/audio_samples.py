"""Listening samples of the soundtrack and the effects for Documentation/Audio/:

  muestrario_musica.wav   every piece in turn (intro + start of the loop; regions and towns crossfade day -> night layer)
  muestrario_efectos.wav  the effects grouped by family, with a short pause between them
  muestrario.md           what plays at each minute
  index.html              a page with a player for every full track (reads them from Assets/Game/Audio)

  python Tools/GameGen/audio_samples.py
"""
import math, os, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth import SR, write_wav   # noqa: E402
from music import PIECES, JINGLES   # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
AUD = os.path.join(ROOT, 'Assets', 'Game', 'Audio')
OUT = os.path.join(ROOT, 'Documentation', 'Audio')

NAMES = {
    'menu': 'Pantalla de título (tema principal)', 'classselect': 'Elección de clase',
    'region_a': 'Valle Central — tema del mundo', 'region_b': 'Bosque del Oeste', 'region_c': 'Lago Espejo',
    'region_d': 'Pantano Carmesí', 'region_e': 'Picos Nevados', 'region_f': 'Arenas Rojas', 'region_g': 'Monte Ceniza',
    'region_h': 'Bosque Corrupto', 'region_i': 'Ciudadela del Rey (camino real)', 'region_j': 'Costa del Puerto',
    'city_valle': 'Villa del Valle', 'city_ciudadela': 'Ciudadela (dentro de la muralla)', 'city_puerto': 'Puerto',
    'int_casa': 'Interior: casa / cabaña', 'int_posada': 'Interior: posada', 'int_capilla': 'Interior: capilla / biblioteca',
    'int_herreria': 'Interior: herrería / cuartel', 'camp': 'Campamento y descanso', 'combat': 'Combate',
    'combat_elite': 'Combate contra élite o campeón', 'boss_I': 'Jefe: el Invocador', 'boss_K': 'Jefe: Gorgrak el Caudillo',
    'boss_Q': 'Jefe: la Madre de Sangre', 'boss_B': 'Jefe final: el Señor Demonio', 'boss_F': 'Jefe: el Coloso de Escarcha',
    'jingle_victory': 'Fanfarria: victoria', 'jingle_defeat': 'Fanfarria: derrota', 'jingle_levelup': 'Fanfarria: subir de nivel',
    'jingle_discover': 'Fanfarria: región descubierta',
}


def read(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float64) / 32767


def fade(x, fin=0.02, fout=1.5):
    x = x.copy(); a = int(fin * SR); b = min(len(x), int(fout * SR))
    if a: x[:a] *= np.linspace(0, 1, a)
    if b: x[-b:] *= np.linspace(1, 0, b)
    return x


def ts(sec):
    return f'{int(sec // 60)}:{int(sec % 60):02d}'


def music_reel():
    parts, lines, t = [], [], 0.0
    gap = np.zeros(int(0.8 * SR))
    for p in PIECES:
        mdir = os.path.join(AUD, 'Music')
        loop = read(os.path.join(mdir, f'music_{p.id}_loop.wav'))
        intro_p = os.path.join(mdir, f'music_{p.id}_intro.wav')
        night_p = os.path.join(mdir, f'music_{p.id}_night.wav')
        seg = []
        if os.path.exists(intro_p): seg.append(read(intro_p))
        if os.path.exists(night_p):
            night = read(night_p)
            n1, xf, n2 = int(13 * SR), int(3 * SR), int(9 * SR)
            w = np.linspace(0, 1, xf)
            day_part = loop[:n1 + xf].copy()
            day_part[n1:] = loop[n1:n1 + xf] * np.cos(w * math.pi / 2) + night[n1:n1 + xf] * np.sin(w * math.pi / 2)
            seg += [day_part, night[n1 + xf:n1 + xf + n2]]
            note = ' (día → capa de noche a los 13 s)'
        else:
            seg.append(loop[:int(18 * SR)])
            note = ''
        x = fade(np.concatenate(seg))
        lines.append(f'| {ts(t)} | {NAMES.get(p.id, p.id)}{note} | `music_{p.id}_*` | {p.bpm} | {p.key.mode} |')
        parts += [x, gap]; t += (len(x) + len(gap)) / SR
    for j in JINGLES:
        x = read(os.path.join(AUD, 'Music', f'jingle_{j}.wav'))
        lines.append(f'| {ts(t)} | {NAMES["jingle_" + j]} | `jingle_{j}` | | |')
        parts += [x, gap]; t += (len(x) + len(gap)) / SR
    return np.concatenate(parts), lines


EFFECT_GROUPS = [
    ('Pasos por superficie', ['step_grass_1', 'step_grass_2', 'step_dirt_1', 'step_stone_1', 'step_wood_1', 'step_sand_1', 'step_snow_1', 'step_water_1', 'step_mud_1', 'step_ash_1']),
    ('Armas: tajos', ['swing_1', 'swing_light_1', 'swing_thrust_1', 'heavy_swing_1']),
    ('Impactos', ['hit_blade_1', 'hit_blunt_1', 'hit_pierce_1', 'hit_crit_1', 'hit_fire_1', 'hit_frost_1', 'hit_venom_1', 'hit_holy_1', 'hit_flesh_1']),
    ('Defensa y movimiento', ['block_1', 'parry_1', 'riposte_1', 'guard_break', 'roll_1', 'tired']),
    ('Arco y conjuros', ['arrow_1', 'fireball_1', 'spit_1', 'spell', 'heal', 'blink', 'bomb']),
    ('Orcos', ['vox_orc_alert_1', 'vox_orc_attack_1', 'vox_orc_hurt_1', 'vox_orc_die_1']),
    ('Demonios', ['vox_demon_alert_1', 'vox_demon_attack_1', 'vox_demon_hurt_1', 'vox_demon_die_1']),
    ('Monstruos de sangre', ['vox_blood_alert_1', 'vox_blood_attack_1', 'vox_blood_hurt_1', 'vox_blood_die_1']),
    ('Caballero', ['player_hurt_1', 'player_die']),
    ('Animales', ['chicken_1', 'pig_1', 'cow_1', 'sheep_1', 'cat_meow_1', 'cat_meow_2', 'cat_purr']),
    ('Interfaz', ['select', 'confirm', 'cancel', 'menu_open', 'menu_close', 'inv_open', 'equip', 'buy', 'sell', 'error', 'page']),
    ('Mundo', ['door_open', 'door_close', 'gate', 'chest', 'coin_1', 'potion', 'eat', 'gather_1', 'anvil_1', 'craft', 'break_1', 'talk', 'fire_ignite', 'splash']),
]


def effects_reel():
    parts, lines, t = [], [], 0.0
    for title, names in EFFECT_GROUPS:
        lines.append(f'| {ts(t)} | {title} | {", ".join(names)} |')
        for n in names:
            p = os.path.join(AUD, f'sfx_{n}.wav')
            if not os.path.exists(p): continue
            x = read(p)
            parts += [x, np.zeros(int(0.35 * SR))]; t += len(x) / SR + 0.35
        parts.append(np.zeros(int(0.9 * SR))); t += 0.9
    amb = os.path.join(AUD, 'Ambience')
    lines.append(f'| {ts(t)} | Ambientes (6 s de cada uno) | viento, viento fuerte, desierto, pájaros, grillos, olas, lago, lava, pantano, hoguera, corrupción, pueblo |')
    for n in ('wind', 'wind_strong', 'desert', 'birds', 'crickets', 'waves', 'lake', 'lava', 'swamp', 'fire', 'corrupt', 'town'):
        x = fade(read(os.path.join(amb, f'amb_{n}.wav'))[:int(6 * SR)], 0.3, 0.8) * 2.5
        parts += [x, np.zeros(int(0.4 * SR))]; t += 6.4
    return np.concatenate(parts), lines


def html():
    rows = []
    for p in PIECES:
        for kind in ('intro', 'loop', 'night'):
            f = f'music_{p.id}_{kind}.wav'
            if os.path.exists(os.path.join(AUD, 'Music', f)):
                label = {'intro': 'entrada', 'loop': 'bucle' if kind == 'loop' and not p.night else 'día', 'night': 'noche'}[kind]
                rows.append(f'<tr><td>{NAMES.get(p.id, p.id)}</td><td>{label}</td><td><audio controls preload="none" '
                            f'{"loop " if kind != "intro" else ""}src="../../Assets/Game/Audio/Music/{f}"></audio></td></tr>')
    for j in JINGLES:
        rows.append(f'<tr><td>{NAMES["jingle_" + j]}</td><td>fanfarria</td><td><audio controls preload="none" src="../../Assets/Game/Audio/Music/jingle_{j}.wav"></audio></td></tr>')
    return ('<!doctype html><meta charset="utf-8"><title>Banda sonora</title>'
            '<style>body{font-family:sans-serif;background:#1b1626;color:#f4edea;max-width:900px;margin:24px auto;padding:0 16px}'
            'td{padding:4px 10px}tr:nth-child(odd){background:#251e33}audio{height:28px}h1{color:#ffc85a}</style>'
            '<h1>La Espada del Bosque — banda sonora</h1><p>Cada pista completa, tal como suena en el juego (los bucles se repiten sin corte). '
            'Abre este archivo desde la carpeta del proyecto.</p><table>' + ''.join(rows) + '</table>')


def build():
    os.makedirs(OUT, exist_ok=True)
    m, ml = music_reel()
    write_wav(os.path.join(OUT, 'muestrario_musica.wav'), m)
    e, el = effects_reel()
    write_wav(os.path.join(OUT, 'muestrario_efectos.wav'), e)
    with open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8') as f: f.write(html())
    with open(os.path.join(OUT, 'muestrario.md'), 'w', encoding='utf-8') as f:
        f.write('# Muestrario de audio\n\n`muestrario_musica.wav` (' + ts(len(m) / SR) + '): el principio de cada pieza. '
                'Las regiones y los pueblos pasan a los 13 s a su **capa de noche** (misma armonía y tempo, otra instrumentación), '
                'como en el juego al anochecer. Las piezas completas se escuchan en `index.html`.\n\n'
                '| Minuto | Pieza | Archivos | BPM | Modo |\n|---|---|---|---|---|\n' + '\n'.join(ml) +
                '\n\n`muestrario_efectos.wav` (' + ts(len(e) / SR) + '): los efectos por familias (en el juego cada uno tiene 2–3 '
                'variantes y cambia un poco de tono y volumen cada vez).\n\n| Minuto | Familia | Efectos |\n|---|---|---|\n' + '\n'.join(el) + '\n')
    print('music reel', ts(len(m) / SR), ' effects reel', ts(len(e) / SR))


if __name__ == '__main__':
    build()
