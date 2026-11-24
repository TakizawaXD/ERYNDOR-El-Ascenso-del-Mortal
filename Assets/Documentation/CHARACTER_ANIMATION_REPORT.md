# CHARACTER_ANIMATION_REPORT — Sistema de animación 2D de personajes

Fecha: 2026-11-18 · Destino: Unity 6 (scripts compilados contra 6000.6.4f1) · 16 PPU · Point · celdas 64×64

Previsualizaciones animadas: `G:\Juegos\Documentation\CharacterPreviews\<Personaje>_directional.gif` (Idle, Walk, Run, Attack, Heavy, Special y Hurt en las 4 direcciones) y `<Personaje>_states.gif` (resto de estados).

---

## 1. Personajes analizados

| Personaje | Pack original | Animaciones originales (fotogramas) | Mira hacia | Altura | Rasgos que se mantienen en todos los fotogramas |
|---|---|---|---|---|---|
| **Soldier** (jugador) | Tiny RPG 01 | Idle 6, Walk 8, Attack01 6 (espada), Attack02 6 (salto con espada), Attack03 9 (arco), Hurt 4, Death 4 | Derecha | 18 px + sombra | Casco de acero con nasal, ojos rojos, bufanda de malla gris azulada, túnica roja, carcaj cruzado a la espalda, espada de hoja de 4 px con guarda marrón, arco oscuro, sombra integrada `#534545` |
| **Orc** | Tiny RPG 01 | Idle 6, Walk 8, Attack01 6, Attack02 6, Hurt 4, Death 4 | Derecha | 15 px | Piel verde, orejas puntiagudas, ojos rojos, colmillos, hombrera de acero, correas de cuero en X, hacha de un filo con mango oscuro |
| **Demon** (Demon_A) | Tiny RPG 02 | Idle 6, Walk 8, Attack01 7 (estocada), Attack02 7 (tajo alto), Hurt 4, Death 4 | Derecha | 20 px | Cuernos grises, piel roja, ojo ámbar, cola, gran cuchilla gris llevada baja |
| **BloodMonster** (Blood Monster_A) | Tiny RPG 02 | Idle 6, Walk 8, Attack01 8 (garra), Attack02 8 (escupitajo), Hurt 4, Death 4 | Derecha | 15 px | Masa carmesí, boca vertical con dientes blancos, brazos largos con garras, patas cortas |

- Origen: hojas de 100×100 por fotograma, PNG RGBA, sin semitransparencias, contorno negro de 1 px.
- Hallazgos: solo el Soldier tiene la sombra dibujada en el sprite (las carpetas "with shadows" son idénticas a las normales). Los idle originales solo tienen 3 poses únicas de 6. **No existían vistas frontal ni trasera de ningún personaje.**
- No se ha modificado, movido ni sobrescrito ningún archivo original.

---

## 2. Cómo se han construido las animaciones

| Dirección | Fuente | Fidelidad |
|---|---|---|
| **Right** | Fotogramas originales cuando existen (Idle, Walk, Attack, Heavy, Special, Hurt, Death). Las animaciones nuevas se derivan de ellos con técnicas de pixel art: aplastar o estirar filas (*squash/stretch*), inclinar el torso, desplazar, rotar 90° sin pérdida, recolorear, siluetas e imágenes residuales | Cuerpo 100 % con píxeles originales |
| **Left** | Espejo exacto de Right | 100 % |
| **Down / Up** | **Vistas nuevas dibujadas a mano** (`Tools/CharAnim/designs.py`). Cada letra es un color muestreado del propio personaje y las armas se copian de sus fotogramas de ataque originales | Diseño deducido (decisión aprobada): mismas proporciones, colores, armas y contorno |

Lenguaje de movimiento común: anticipación (aplastar), acción (estirar, arma extendida, estela blanca `#f4edea` como en los originales), seguimiento (estela que se desvanece) y recuperación. La pisada alterna pierna apoyada y pierna levantada con balanceo de brazos y rebote de 1 px. El daño (Hurt) en Down/Up aplica **la misma transformación de color aprendida de los Hurt originales** de cada personaje.

**Hojas sin relleno:** cada hoja guarda solo fotogramas únicos (los duplicados exactos se eliminan automáticamente). Las pausas y repeticiones van en la secuencia del clip (columna "Claves en el clip").

---

## 3. Animaciones creadas, fotogramas, dimensiones y FPS

D/U/L/R = Down/Up/Left/Right. Todas las hojas tienen 64 px de alto con celdas de 64×64 uniformes, fondo transparente y ningún fotograma tocando el borde (comprobado automáticamente en los 1.312 fotogramas).

### Soldier — 77 clips · 373 fotogramas únicos

| Animación | Direcciones | Fotogramas únicos (D/U/L/R) | Claves en el clip | Hoja (px) | FPS | Bucle |
|---|---|---|---|---|---|---|
| Attack | D/U/L/R | 6/6/6/6 | 6/6/6/6 | 384×64 | 12 | no |
| Block | L/R | 2/2 | 2/2 | 128×64 | 10 | no |
| BlockHit | L/R | 2/2 | 2/2 | 128×64 | 12 | no |
| ChargeEnergy | L/R | 4/4 | 4/4 | 256×64 | 10 | sí |
| ChargedAttack_Charge | L/R | 4/4 | 4/4 | 256×64 | 12 | sí |
| ChargedAttack_Release | L/R | 4/4 | 4/4 | 256×64 | 12 | no |
| Climb | U | 4 | 4 | 256×64 | 8 | sí |
| ComboAttack | L/R | 9/9 | 9/9 | 576×64 | 13 | no |
| CriticalAttack | L/R | 7/7 | 7/7 | 448×64 | 12 | no |
| Death | L/R | 4/4 | 4/4 | 256×64 | 8 | no |
| Defeat | L/R | 4/4 | 4/4 | 256×64 | 7 | no |
| Dodge | L/R | 4/4 | 5/5 | 256×64 | 14 | no |
| Fall | L/R | 2/2 | 2/2 | 128×64 | 10 | sí |
| HeavyAttack | D/U/L/R | 7/7/6/6 | 7/7/6/6 | 384×64, 448×64 | 11 | no |
| Hurt | D/U/L/R | 4/4/3/3 | 4/4/4/4 | 192×64, 256×64 | 10 | no |
| Idle | D/U/L/R | 3/2/3/3 | 6/4/6/6 | 128×64, 192×64 | 8 | sí |
| Interact | L/R | 3/3 | 5/5 | 192×64 | 10 | no |
| Jump | L/R | 4/4 | 4/4 | 256×64 | 12 | no |
| Knockback | L/R | 5/5 | 5/5 | 320×64 | 12 | no |
| Land | L/R | 3/3 | 3/3 | 192×64 | 12 | no |
| PickUp | L/R | 5/5 | 7/7 | 320×64 | 10 | no |
| Pull | L/R | 8/8 | 8/8 | 512×64 | 7 | sí |
| Push | L/R | 8/8 | 8/8 | 512×64 | 7 | sí |
| Roll | L/R | 6/6 | 7/7 | 384×64 | 14 | no |
| Run | D/U/L/R | 4/4/8/8 | 4/4/8/8 | 256×64, 512×64 | 12 | sí |
| Sit | L/R | 3/3 | 6/6 | 192×64 | 6 | sí |
| Sleep | L/R | 4/4 | 4/4 | 256×64 | 4 | sí |
| SpecialAttack | D/U/L/R | 6/6/9/9 | 8/8/9/9 | 384×64, 576×64 | 12 | no |
| Swim | D/U/L/R | 4/4/2/2 | 4/4/4/4 | 128×64, 256×64 | 8 | sí |
| Victory | L/R | 6/6 | 6/6 | 384×64 | 10 | no |
| Walk | D/U/L/R | 5/5/8/8 | 6/6/8/8 | 320×64, 512×64 | 10 | sí |

### Orc — 64 clips · 307 fotogramas únicos

| Animación | Direcciones | Fotogramas únicos (D/U/L/R) | Claves en el clip | Hoja (px) | FPS | Bucle |
|---|---|---|---|---|---|---|
| Attack | D/U/L/R | 6/6/6/6 | 6/6/6/6 | 384×64 | 12 | no |
| Block | L/R | 2/2 | 2/2 | 128×64 | 10 | no |
| BlockHit | L/R | 2/2 | 2/2 | 128×64 | 12 | no |
| ChargeEnergy | L/R | 4/4 | 4/4 | 256×64 | 10 | sí |
| ChargedAttack_Charge | L/R | 4/4 | 4/4 | 256×64 | 12 | sí |
| ChargedAttack_Release | L/R | 4/4 | 4/4 | 256×64 | 12 | no |
| ComboAttack | L/R | 9/9 | 9/9 | 576×64 | 13 | no |
| CriticalAttack | L/R | 7/7 | 7/7 | 448×64 | 12 | no |
| Death | L/R | 4/4 | 4/4 | 256×64 | 8 | no |
| Defeat | L/R | 4/4 | 4/4 | 256×64 | 7 | no |
| Dodge | L/R | 4/4 | 5/5 | 256×64 | 14 | no |
| Fall | L/R | 2/2 | 2/2 | 128×64 | 10 | sí |
| HeavyAttack | D/U/L/R | 7/7/6/6 | 7/7/6/6 | 384×64, 448×64 | 11 | no |
| Hurt | D/U/L/R | 4/4/3/3 | 4/4/4/4 | 192×64, 256×64 | 10 | no |
| Idle | D/U/L/R | 3/2/3/3 | 6/4/6/6 | 128×64, 192×64 | 8 | sí |
| Jump | L/R | 4/4 | 4/4 | 256×64 | 12 | no |
| Knockback | L/R | 5/5 | 5/5 | 320×64 | 12 | no |
| Land | L/R | 3/3 | 3/3 | 192×64 | 12 | no |
| Roll | L/R | 6/6 | 7/7 | 384×64 | 14 | no |
| Run | D/U/L/R | 4/4/8/8 | 4/4/8/8 | 256×64, 512×64 | 12 | sí |
| Sit | L/R | 3/3 | 6/6 | 192×64 | 6 | sí |
| Sleep | L/R | 4/4 | 4/4 | 256×64 | 4 | sí |
| SpecialAttack | D/U/L/R | 7/7/7/7 | 7/7/7/7 | 448×64 | 11 | no |
| Victory | L/R | 6/6 | 6/6 | 384×64 | 10 | no |
| Walk | D/U/L/R | 5/5/8/8 | 6/6/8/8 | 320×64, 512×64 | 10 | sí |

### Demon — 64 clips · 315 fotogramas únicos

| Animación | Direcciones | Fotogramas únicos (D/U/L/R) | Claves en el clip | Hoja (px) | FPS | Bucle |
|---|---|---|---|---|---|---|
| Attack | D/U/L/R | 6/6/6/6 | 6/6/7/7 | 384×64 | 12 | no |
| Block | L/R | 2/2 | 2/2 | 128×64 | 10 | no |
| BlockHit | L/R | 2/2 | 2/2 | 128×64 | 12 | no |
| CastSpell | L/R | 5/5 | 5/5 | 320×64 | 10 | sí |
| ChargeEnergy | L/R | 4/4 | 4/4 | 256×64 | 10 | sí |
| ChargedAttack_Charge | L/R | 4/4 | 4/4 | 256×64 | 12 | sí |
| ChargedAttack_Release | L/R | 5/5 | 5/5 | 320×64 | 12 | no |
| ComboAttack | L/R | 10/10 | 11/11 | 640×64 | 13 | no |
| CriticalAttack | L/R | 8/8 | 8/8 | 512×64 | 12 | no |
| Death | L/R | 4/4 | 4/4 | 256×64 | 8 | no |
| Defeat | L/R | 4/4 | 4/4 | 256×64 | 7 | no |
| Dodge | L/R | 4/4 | 5/5 | 256×64 | 14 | no |
| Fall | L/R | 2/2 | 2/2 | 128×64 | 10 | sí |
| HeavyAttack | D/U/L/R | 7/7/7/7 | 7/7/7/7 | 448×64 | 11 | no |
| Hurt | D/U/L/R | 4/4/3/3 | 4/4/4/4 | 192×64, 256×64 | 10 | no |
| Idle | D/U/L/R | 3/2/3/3 | 6/4/6/6 | 128×64, 192×64 | 8 | sí |
| Jump | L/R | 4/4 | 4/4 | 256×64 | 12 | no |
| Knockback | L/R | 5/5 | 5/5 | 320×64 | 12 | no |
| Land | L/R | 3/3 | 3/3 | 192×64 | 12 | no |
| Roll | L/R | 6/6 | 7/7 | 384×64 | 14 | no |
| Run | D/U/L/R | 4/4/7/7 | 4/4/8/8 | 256×64, 448×64 | 12 | sí |
| Sleep | L/R | 4/4 | 4/4 | 256×64 | 4 | sí |
| SpecialAttack | D/U/L/R | 6/6/8/8 | 7/7/8/8 | 384×64, 512×64 | 11 | no |
| Victory | L/R | 6/6 | 6/6 | 384×64 | 10 | no |
| Walk | D/U/L/R | 5/5/7/7 | 6/6/8/8 | 320×64, 448×64 | 10 | sí |

### BloodMonster — 62 clips · 317 fotogramas únicos

| Animación | Direcciones | Fotogramas únicos (D/U/L/R) | Claves en el clip | Hoja (px) | FPS | Bucle |
|---|---|---|---|---|---|---|
| Attack | D/U/L/R | 5/5/8/8 | 5/5/8/8 | 320×64, 512×64 | 12 | no |
| Block | L/R | 2/2 | 2/2 | 128×64 | 10 | no |
| BlockHit | L/R | 2/2 | 2/2 | 128×64 | 12 | no |
| ChargeEnergy | L/R | 4/4 | 4/4 | 256×64 | 10 | sí |
| ChargedAttack_Charge | L/R | 4/4 | 4/4 | 256×64 | 12 | sí |
| ChargedAttack_Release | L/R | 6/6 | 6/6 | 384×64 | 12 | no |
| ComboAttack | L/R | 12/12 | 13/13 | 768×64 | 13 | no |
| CriticalAttack | L/R | 9/9 | 9/9 | 576×64 | 12 | no |
| Death | L/R | 4/4 | 4/4 | 256×64 | 8 | no |
| Defeat | L/R | 4/4 | 4/4 | 256×64 | 7 | no |
| Dodge | L/R | 4/4 | 5/5 | 256×64 | 14 | no |
| Fall | L/R | 2/2 | 2/2 | 128×64 | 10 | sí |
| HeavyAttack | D/U/L/R | 6/6/8/8 | 6/6/8/8 | 384×64, 512×64 | 11 | no |
| Hurt | D/U/L/R | 4/4/3/3 | 4/4/4/4 | 192×64, 256×64 | 10 | no |
| Idle | D/U/L/R | 2/2/3/3 | 6/4/6/6 | 128×64, 192×64 | 8 | sí |
| Jump | L/R | 4/4 | 4/4 | 256×64 | 12 | no |
| Knockback | L/R | 5/5 | 5/5 | 320×64 | 12 | no |
| Land | L/R | 3/3 | 3/3 | 192×64 | 12 | no |
| Roll | L/R | 6/6 | 7/7 | 384×64 | 14 | no |
| Run | D/U/L/R | 4/4/8/8 | 4/4/8/8 | 256×64, 512×64 | 12 | sí |
| Sleep | L/R | 4/4 | 4/4 | 256×64 | 4 | sí |
| SpecialAttack | D/U/L/R | 7/6/7/7 | 7/7/8/8 | 384×64, 448×64 | 11 | no |
| Victory | L/R | 6/6 | 6/6 | 384×64 | 10 | no |
| Walk | D/U/L/R | 5/5/8/8 | 6/6/8/8 | 320×64, 512×64 | 10 | sí |

**Total: 267 hojas, 1.312 fotogramas únicos, 4 manifiestos JSON; los 4 Animator Controllers se generan en Unity.**

### Asignación de ataques por personaje

| | Attack | HeavyAttack | SpecialAttack | Efecto especial |
|---|---|---|---|---|
| Soldier | Attack01 (tajo) | Attack02 (salto + tajo) | Attack03 (arco) | Flecha en las 4 direcciones |
| Orc | Attack01 | Attack02 | Golpe al suelo | Onda expansiva de polvo |
| Demon | Attack01 (estocada) | Attack02 (tajo alto) | Orbe de fuego infernal | Orbe morado, rojo y amarillo que crece y se lanza |
| BloodMonster | Attack01 (garra) | Embestida derivada de Attack01 | Attack02 (escupitajo) | Proyectil blanco como el original |

ChargedAttack (carga en bucle y liberación), ComboAttack (Attack seguido de Heavy) y CriticalAttack (Heavy con destello de impacto y estrella) están hechos para Left y Right.

---

## 4. Estructura de archivos

```
Assets/Art/Characters/<Personaje>/
  Idle/ Walk/ Run/ Attack/ Special/ Hurt/ Death/ Combat/ Dodge/ Jump/ Emote/ Other/
    <Personaje>_<Animación>_<Down|Up|Left|Right>.png
  <Personaje>_animations.json      fotogramas, secuencia, fps, bucle, pivote
Assets/Art/Animations/Characters/<Personaje>/      lo genera Unity: .anim + .controller
Assets/Editor/ArtPipeline/CharacterAnimationBuilder.cs
Assets/Scripts/Animation/AnimatorStateFlag.cs, CharacterAnimatorDriver.cs, WoodsArt.Runtime.asmdef
Tools/CharAnim/      generador Python: engine, source, designs, rigs, anims, fxdraw, build, preview
Documentation/CharacterPreviews/*.gif
```

---

## 5. Configuración de importación (automática)

`ArtImportPostprocessor` la aplica a todo `Assets/Art/Characters/` en la primera importación (o con **Tools ▸ Art ▸ Reapply Import Rules**):

| Ajuste | Valor |
|---|---|
| Texture Type | Sprite (2D and UI) |
| Sprite Mode | Multiple, celdas 64×64 (sprites `<archivo>_0…n`) |
| Pixels Per Unit | 16 (igual que tiles y entorno: el personaje mide ≈ 1,1–1,25 tiles) |
| Pivot | Custom **(0.5, 0.1875)**: el punto donde los pies tocan el suelo, idéntico en todos los fotogramas y direcciones |
| Filter Mode | Point (no filter) |
| Compression | None |
| Mesh Type | Full Rect · Mip Maps desactivados · Wrap Clamp |

**Alineación:** el centro del cuerpo está entre las columnas 31 y 32 de cada celda (el espejo izquierda/derecha no desplaza al personaje) y los pies apoyan en la fila 51. Al cambiar de dirección o de animación no hay saltos. En los saltos la sombra del Soldier se queda en el suelo y se encoge con la altura.

---

## 6. Animator Controller

Lo genera **Tools ▸ Art ▸ Build Character Animations**: un `<Personaje>.controller` por personaje, con un clip por animación y dirección.

**Parámetros**

| Tipo | Parámetros |
|---|---|
| Float | `MoveX`, `MoveY` (última dirección; MoveY = -1 por defecto), `Speed` (0 idle, <0,6 andar, ≥0,6 correr) |
| Bool (los pone el juego) | `IsMoving`, `IsDead`, `IsGrounded` (true por defecto), `IsBlocking`, `IsCharging`, `IsClimbing`, `IsSwimming`, `IsSitting`, `IsSleeping`, `IsPushing`, `IsPulling`, `IsChargingEnergy` |
| Bool (solo lectura, los gestiona `AnimatorStateFlag`) | `IsAttacking`, `IsHurt`, `IsDodging` |
| Trigger | `Attack`, `HeavyAttack`, `SpecialAttack`, `ComboAttack`, `CriticalAttack`, `Hurt`, `Knockback`, `BlockHit`, `Dodge`, `Roll`, `Jump`, `Victory`, `Defeat`, `Interact`, `PickUp`, `CastSpell` |

**Estados y transiciones**
- **Locomoción**: Idle ⇄ Walk ⇄ Run, con *blend trees* 2D direccionales (MoveX/MoveY) de 4 clips.
- **Animaciones solo laterales**: *blend tree* 1D sobre MoveX. Si MoveX < 0 usa Left; en cualquier otro caso (también mirando arriba o abajo) usa Right.
- **Ataques y acciones puntuales**: desde Any State con su trigger. Bloqueados mientras `IsAttacking` o `IsDead`, y con *Can Transition To Self* desactivado, así que **un ataque nunca se reinicia a sí mismo**. Al terminar vuelven a Idle (exit time 1, duración 0).
- **ComboAttack** también se encadena desde Attack a partir de la mitad del golpe.
- **Hurt / Knockback** interrumpen los ataques, pero no durante Dodge ni Roll (fotogramas de invulnerabilidad).
- **Block**: se mantiene mientras `IsBlocking`; `BlockHit` reproduce el impacto y vuelve a la guardia.
- **ChargedAttack_Charge**: en bucle mientras `IsCharging`; al soltar pasa a `ChargedAttack_Release`.
- **Jump → Fall → Land**: Fall espera a `IsGrounded`.
- **Victory / Defeat**: mantienen la pose hasta que `IsMoving`.
- **Death**: con `IsDead`; vuelve a Idle si `IsDead` pasa a false (para revivir).
- Todas las transiciones duran 0 (pixel art: sin mezclas).

**Ayuda opcional**: `CharacterAnimatorDriver.SetMovement(dirección, velocidad01)` ajusta la dirección a 4 ejes, mantiene la orientación al pararse y rellena MoveX, MoveY, Speed e IsMoving. No mueve al personaje y no se ha conectado a ningún sistema: el proyecto no tenía scripts de movimiento.

---

## 7. Instrucciones de integración

1. Abre `G:\Juegos` como proyecto de Unity 6 (o copia `Assets/` a tu proyecto) e instala **2D Sprite**, **2D Tilemap** y **2D Tilemap Extras**.
2. Al importarse, los PNG se cortan solos. Si ya estaban importados: **Tools ▸ Art ▸ Reapply Import Rules**.
3. Ejecuta **Tools ▸ Art ▸ Build Character Animations**. Crea los clips y los 4 controllers en `Assets/Art/Animations/Characters/`.
4. Para cada personaje: GameObject con *SpriteRenderer* + *Animator* (Controller = `<Personaje>.controller`). Opcionalmente añade `CharacterAnimatorDriver`.
5. En tu código: llama a `SetMovement` cada frame, dispara los triggers y mantén los bools. Consulta `animator.GetBool("IsAttacking")` para bloquear el movimiento durante los golpes.
6. Las animaciones son **en el sitio** (sin *root motion*). El desplazamiento de esquivar, rodar, retroceder o saltar lo aplica el código del juego.
7. Orden de dibujo cenital: *Transparency Sort Mode* = Custom Axis (0, 1, 0). Como el pivote está en los pies, se ordenan correctamente por Y.

---

## 8. Animaciones que faltan o no aplican

| Animación | Personajes | Motivo |
|---|---|---|
| Interact, PickUp, Push, Pull, Climb, Swim | Orc, Demon, BloodMonster | Son enemigos: no interactúan con objetos ni trepan o nadan (regla "no forzar animaciones sin sentido") |
| CastSpell | Soldier, Orc, BloodMonster | Su diseño no tiene rasgos mágicos; el Soldier usa ChargeEnergy para el ataque cargado |
| Sit | Demon, BloodMonster | Su anatomía no tiene una pose de sentado legible |
| Estados no direccionales (Death, Knockback, Block, Dodge, Roll, Jump/Fall/Land, Victory, Defeat, Charged, Combo, Critical, extras) en **Down/Up** | Todos | La petición solo los pedía direccionales para Hurt. Hay versiones Left y Right; mirando arriba o abajo el Animator usa Right |
| Climb solo Up | Soldier | Trepar solo se ve de espaldas |

---

## 9. Problemas encontrados y soluciones

| Problema | Solución |
|---|---|
| Ningún personaje tenía vista frontal ni trasera | Dibujadas a mano con la paleta exacta de cada personaje (aprobado) |
| Celdas de 100×100 con el personaje descentrado y los pies a distinta altura (57–60) | Normalización a 64×64: centro del cuerpo medido por personaje (corrigiendo cuando el arma cae en la zona de las piernas) y pies en la fila 51 |
| La sombra del Soldier está pintada en el sprite | Se separa por color: se queda en el suelo en saltos y caídas y no recibe brillos ni destellos |
| Demon de frente: la cuchilla tapaba todo el cuerpo | Vista rehecha con la altura del perfil (cuerpo y piernas completos); la cuchilla queda 2 px por debajo de los pies, como en el original |
| Blood Monster de frente: la boca no se leía | Columna de dientes de 5 px de ancho con los blancos originales |
| Armas alzadas flotando (Orc) o tapando la cara (Demon) | Alturas y desplazamientos relativos a la altura de cada personaje |
| El brillo de carga y el destello crítico afectaban a la sombra o formaban un manchón blanco | Efectos solo sobre el cuerpo; el destello conserva el contorno negro |
| Arco y flecha poco visibles hacia abajo y hacia arriba | Arco a la altura del pecho o por encima de la cabeza; flecha dentro de la celda |
| Escupitajo frontal invisible y de un color distinto al original | Sale de la boca hacia el suelo, en el blanco del proyectil original |
| Un fotograma con la flecha cortada en el borde | Recorrido acortado; 0 fotogramas tocan el borde |
| Bloqueo que no se podía mantener | Separado en `Block` (mantiene la guardia) y `BlockHit` (impacto) |

### Limitaciones conocidas
- Idle Down/Up tiene 2–3 poses únicas (respiración y parpadeo). Es la misma cantidad que los idle originales, que repiten 3 poses en 6 fotogramas.
- Las vistas Down/Up son 3–4 px más anchas que el perfil, como es normal en un personaje visto de frente.
- Swim de lado solo tiene 2 poses únicas, porque fuera del agua solo asoman la cabeza y el casco.

### Verificación
- ✅ Revisión visual de todas las categorías con hojas ampliadas y GIF animados (carpeta de previsualizaciones).
- ✅ Validación automática: 267 hojas de 64 px de alto, celdas uniformes, transparencia limpia (los píxeles transparentes se guardan como RGBA 0) y 0 fotogramas cortados.
- ✅ `CharacterAnimationBuilder.cs`, `ArtImportPostprocessor.cs`, `AnimatorStateFlag.cs` y `CharacterAnimatorDriver.cs` compilan sin errores con el Roslyn de Unity 6000.6.4f1 contra sus DLL.
- ⚠️ **No probado dentro del Editor de Unity.** El equipo tenía unos 2,4 GB de RAM libre con otro editor abierto y las pruebas anteriores en batchmode se quedaron sin memoria. La creación real de clips y controllers queda pendiente del paso 3 de la sección 7.

### Regenerar
`python Tools/CharAnim/build.py` (o con un personaje: `python Tools/CharAnim/build.py Orc`) reescribe hojas y manifiestos. Después, en Unity: **Tools ▸ Art ▸ Build Character Animations**. Los clips se actualizan en el sitio y se conservan las referencias.
