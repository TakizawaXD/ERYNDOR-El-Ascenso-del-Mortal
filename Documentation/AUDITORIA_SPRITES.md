# Auditoría de sprites y animaciones — 21-11-2026

Herramienta: `python Tools/CharAnim/audit_sprites.py` (informe) / `--fix` (correcciones seguras). Datos completos: `Documentation/auditoria_sprites.json`.

**Alcance:** 89 personajes (14 jugables, 51 enemigos, 7 jefes, 17 vecinos) + 70 juegos de armas del jugador · **11807 animaciones · 54031 fotogramas**, cada uno abierto y medido.

## Estado por categoría

| Estado | Qué significa | Cuántos |
|---|---|---|
| Correcto (verificado por análisis) | sin defectos medibles; **no jugado** todavía | 124 de 159 |
| Revisado: falso positivo | el aviso del medidor no es un defecto (ver abajo) | 35 de 159 |
| Corregido, pendiente de prueba en juego | ver "Correcciones" | todo lo de este informe |
| Incompleto | — | 0 |
| Incorrecto (archivos rotos, fotogramas vacíos, referencias) | — | 0 |
| Bloqueado / decisión de diseño | 8 direcciones (ver abajo) | 1 tema |

## Correcciones hechas

| Problema | Causa | Corrección | Estado |
|---|---|---|---|
| 695 animaciones sin vista de frente/espaldas (muerte, guardia, esquiva, rodar, retroceso, saltar, victoria, ataque cargado, combo, crítico, sentarse, dormir, recoger, interactuar, empujar, conjurar...) en enemigos, vecinos y la familia del Soldado | el generador de esqueletos (`anims.py`) las creaba solo de lado; mirando arriba/abajo el motor ponía la de lado | nuevo `build_vertical()`: frente y espalda dibujados con los mismos esqueletos frontal/trasero (cuerpo, brazos y arma se mueven juntos); regenerados Soldado, Orco, Demonio, Monstruo de Sangre, todas sus variantes (clases, 17 vecinos, enemigos regionales), enemigos de la cripta y El Invocador | 0 animaciones sin sus 4 direcciones. Pendiente de prueba |
| 9 héroes dibujados sin 19 acciones | el arte original no las traía | `hero_actions.py`: creadas desde sus propios fotogramas, en 4 direcciones (77 animaciones por héroe) | Pendiente de prueba |
| Sombra separada de los pies (Madre de Sangre, Señor Demonio, Diablillo de cadena, Rey Sepultado) | el importador usaba un pivote fijo e ignoraba el de cada personaje | el importador lee el pivote de la lista de animaciones; pivotes medidos sobre los pies | Pendiente de reimportar/probar |
| El Rey Sepultado "saltaba" 15 px al empezar a correr | su carrera estaba dibujada 15 px más alta que su pose de pie | carrera bajada a la línea del suelo | Pendiente de prueba |
| Fotogramas de impacto de los ataques nuevos | sin eventos de golpe | `events_patch.py` midió el fotograma del tajo en 860 ataques | Pendiente de prueba |
| 100 píxeles sueltos / casi transparentes en ciclos de andar/estar | suciedad | eliminados (no se toca a fantasmas, brillos ni efectos) | Pendiente de prueba |

## Avisos revisados que NO son defectos

- **Cambio de altura al correr** (goblins, limos, esqueletos, héroes): rebote de las piernas en cada zancada.
- **Espadón / Legendaria al andar**: se mueve el arma, no el cuerpo.
- **"Pies que saltan" en Señor Demonio y demonios**: el medidor tomaba la punta del arma que cuelga por debajo de los pies; los pies no se mueven.
- **Píxeles sueltos en El Invocador**: motas de su llama de almas, dibujadas a propósito.

## Armas y manos

- **Caballero, Samurái** (y las variantes): cada arma es un juego de animaciones completo dibujado sobre el esqueleto (`weaponsets.py`), con la empuñadura en la mano en cada fotograma y las 4 direcciones (36 animaciones por arma). No hay arma flotante: el sprite de "arma en mano" se oculta cuando hay juego propio.
- **Héroes dibujados**: el arma forma parte del dibujo original (manos y arma ya integradas); no se les pinta otra arma encima.
- **Enemigos**: sus ataques de lado vienen de los packs originales (brazo y arma animados); los de frente/espalda los dibuja el esqueleto con el arma en la mano (anticipación, golpe, seguimiento y recuperación).
- Revisado por **muestras visuales** (Samurái con katana, héroes, Soldado, Orco, Demonio), no fotograma a fotograma de los 54 000: no hay una medida automática fiable de "mano sobre empuñadura".

## Bloqueado / decisión de diseño

- **8 direcciones**: el juego usa **4 direcciones** (árbol de mezcla MoveX/MoveY; en diagonal se usa la más cercana). Pasar a 8 exigiría dibujar el doble de animaciones de todos los personajes y cambiar el controlador; no se ha hecho. Las 4 direcciones están completas en todos.

## Pendiente de prueba en Unity

1. Abrir Unity: importa ~1 700 imágenes nuevas (crea sus .meta) y aplica los pivotes nuevos.
2. Pulsar Play: se reconstruye solo (las animaciones cambiaron) y regenera los controladores con las direcciones nuevas.
3. Comprobar en juego: guardia, esquiva, rodar, muerte y combos mirando arriba/abajo; sombras de los jefes; carrera del Rey Sepultado.
