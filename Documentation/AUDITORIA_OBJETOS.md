# Auditoría de objetos, escenario, interfaz y efectos — 21-11-2026

Herramienta: `python Tools/ArtGen2/audit_objects.py` (informe) / `--fix`. Datos: `Documentation/auditoria_objetos.json`.
Complementa `AUDITORIA_SPRITES.md` (personajes y armas).

**Alcance:** las **932 imágenes** de `Assets/Art` que no son personajes: suelo pintado (499 trozos), utilería, estructuras,
naturaleza, muebles, catacumbas y cuevas, guaridas de jefes, casillas, iconos de objetos, interfaz y efectos. Cada una abierta
y medida, más las referencias del código a imágenes y los tamaños de colisión.

## Resultado

| Estado | Cuántas |
|---|---|
| Correctas (sin defectos medibles; **no probadas en juego**) | 909 |
| Corregidas, pendientes de prueba en juego | 76 (incluidas en el total: 56 de catacumbas + 7 de guaridas/jefe + 13 reimportadas) |
| Avisos revisados que no son defecto | 15 |
| Obsoletas (no se usan en el juego) | 8 |
| Referencias rotas (el código pide una imagen que no existe) | 0 |
| Colisiones más anchas que su dibujo (paredes invisibles) | 0 |

## Defectos reales encontrados y corregidos

| Problema | Causa | Corrección | Estado |
|---|---|---|---|
| **Pilares, estandartes, braseros y escombros de las guaridas de jefe** dibujados a medias (solo contornos: entre el 20 % y el 40 % de sus píxeles) | `arena.py` dibuja con polígonos sin color de relleno; con Pillow 13 (la versión instalada) eso no pinta nada | el generador rellena las figuras sin color; arte regenerado | Corregido; pendiente de verlo en juego |
| **Cresta de la barra de vida de los jefes** vacía (imagen transparente) y remate y el icono de objetivo incompletos | la misma causa | regenerados (la cresta pasa de 0 a 209 píxeles) | Corregido; pendiente de verlo en juego |
| **Utilería de catacumbas y cuevas** (antorchas, velas, braseros, sarcófagos, ataúdes, pilares, columnas, trono, urnas, barriles, escaleras…) con el pivote en el **centro** | la carpeta `World/Catacombs` no estaba en las reglas del importador → se importaban centradas, quedaban medio hundidas y se ordenaban mal respecto al jugador | el importador las apoya en su base (las piezas planas de suelo — runas, grietas, placas, agujeros, rejillas — siguen centradas) | Corregido; Unity las reimporta |
| Escaneo del resto de generadores por el mismo fallo de Pillow | — | análisis del código de todas las herramientas: solo `arena.py` lo tenía | Verificado |

## Avisos revisados que NO son defectos

- **Píxeles semitransparentes** en árboles, casas, muebles, muelles, murallas: son las **sombras dibujadas** en la base del objeto (capa oscura de alfa fijo 50–90). Intencionado.
- **Brillos** en farol, torre oscura, obelisco demoníaco, runas, sello y flores: luz suave dibujada. Intencionado.
- **Píxeles sueltos** en hoguera, antorcha y hierba alta: chispas, ascuas y briznas. Intencionado.
- **Celdas vacías** al final de efectos de un solo uso (chispa) y pausas del destello del agua: el efecto se apaga. Intencionado.
- **Nombres "sin usar"** de estelas de armas, animales de granja, fondos de habitaciones, suelos de guarida y casillas de agua/lava: el código compone el nombre (`fx_<arma>`, `room_<tipo>`…). Sí se usan.

## Obsoletas (no se usan; no se han borrado)

- `World/MapArt/mapart_*.png` (5): mapa ilustrado antiguo; el juego usa `world_map.png`.
- `World/Catacombs/secret_sw_*.png` (3): muros secretos del antiguo mapa de catacumbas; en el mapa único los pasadizos quedan abiertos.
- `World/Catacombs/door_bars_h.png`, `spear_slot.png`: puertas y trampas que el mapa único no coloca (además tienen filas vacías bajo el dibujo, que habría que recortar si se vuelven a usar).
- Carpetas `World/Maps/City_*`, `Zone_MonteCeniza`, `Dungeon_Catacumbas` (suelos de los mapas separados): ya no se usan; el suelo está en `World/Ground`.

## Pendiente de prueba en Unity

1. Al abrir Unity se reimportan las imágenes tocadas (catacumbas, guaridas, barra de jefe) con su pivote nuevo.
2. Pulsar Play (se reconstruye solo) y comprobar: utilería de una cueva apoyada en el suelo y ordenada bien al pasar por
   delante y por detrás; guarida de un jefe con pilares, estandartes y braseros completos; barra de vida del jefe con su cresta.
