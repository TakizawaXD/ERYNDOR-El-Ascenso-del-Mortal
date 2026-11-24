# ART_ASSETS_REPORT — Dirección de arte y assets 2D

Fecha: 2026-11-18 · Destino: Unity 6 (scripts compilados contra 6000.6.4f1) · Render 2D, Tilemap

---

## 0. Punto de partida

En `G:\Juegos` **no existe todavía un proyecto de Unity** (no hay `ProjectSettings/`, escenas ni scripts). Hay tres asset packs sueltos.
Por eso todo lo nuevo está en `G:\Juegos\Assets\…`, con la estructura de un proyecto Unity: se puede abrir `G:\Juegos` como proyecto
o copiar la carpeta `Assets` dentro de un proyecto existente. **No se ha modificado, movido ni borrado ningún archivo original.**

---

## 1. Inventario de assets existentes

| Pack | Contenido | Formato |
|---|---|---|
| `pixel_16_woods v2 free/free_pixel_16_woods.png` | Hoja de 352×192 (cuadrícula 16 px, 22×12 celdas) | PNG RGBA, 76 colores |
| `Tiny RPG Character Asset Pack 01 …/` | Soldier (Idle, Walk, Attack01-03, Hurt, Death) + Orc (Idle, Walk, Attack01-02, Hurt, Death) + flecha | Celdas de 100×100, tiras horizontales |
| `Tiny RPG Character Asset Pack 02 …/` | Demon_A y Blood Monster_A (Idle, Walk, Attack01-02, Hurt, Death) | Celdas de 100×100 |
| Ambos packs de personajes | `.aseprite` originales | Aseprite |

**Clasificación**

- **Personajes:** Soldier (protagonista probable, armas: espada y arco).
- **Enemigos:** Orc (hacha), Demon_A (cuchilla), Blood Monster_A.
- **NPC:** ninguno.
- **Objetos/proyectiles:** Arrow01 (32×32 y 100×100).
- **Terrenos:** isla de césped sobre tierra, parche de tierra, isla con acantilado, isla rodeada de agua (formas de demostración, no son tilesets autotile completos).
- **Vegetación:** árbol grande, árbol pequeño, pino, arbusto, hierba, hojas, flores (amarillas, rosas, malva), setas rojas y azules, tocón, rama.
- **Agua:** relleno azul, ondas, roca en agua, juncos, nenúfares, rama en agua.
- **Decoración:** rocas, escalera/tablones de madera del acantilado.
- **Efectos:** sólo las estelas de ataque integradas en los sprites de personaje.
- **UI / iconos / fondos / ambientación:** **ninguno**.

**Duplicados e inconsistencias detectadas**

- `Arrow(Projectile)` está duplicado en dos carpetas del Pack 01 (idénticos).
- Las carpetas "with shadows" y sin sombra son **idénticas píxel a píxel** (0 píxeles de diferencia): ambas incluyen la sombra.
- `Orc.png`, `Soldier.png`, etc. son hojas combinadas con celdas vacías; para Unity es mejor usar los archivos por animación.
- El pack de bosque contorna con colores oscuros "de material"; los personajes con negro puro. Es una diferencia original y se respetó (entorno → contorno de color; personajes, efectos de combate e iconos de UI → negro).

---

## 2. Análisis del estilo artístico (guía visual)

| Aspecto | Regla extraída de los originales |
|---|---|
| Técnica | Pixel art puro, sin antialiasing, sin degradados suaves |
| Perspectiva | Cenital 3/4 (top-down RPG); personajes de perfil sobre suelo cenital |
| Celda | **16×16 px**; personajes de ~17-21 px de alto dentro de celdas de 100×100 |
| Escala | 1 tile = 1 unidad → **16 Pixels Per Unit** para todo (personajes incluidos) |
| Luz | Desde arriba-izquierda; luces en el borde superior-izquierdo, oscuros abajo-derecha |
| Contorno | 1 px. Entorno: oscuro del propio material (`#23674e` follaje, `#4e2428` tierra/madera, `#242234` piedra). Personajes: negro |
| Sombreado | 3-4 tonos por material, bandas duras, *dithering* mínimo |
| Sombras proyectadas | Elipses negras semitransparentes (alpha 37-139), sin contorno |
| Saturación | Alta en el entorno (verdes `#59c135`, azul `#249fde`), apagada en los personajes (rojos vino, grises acero) |
| Efectos | Blanco roto `#f4edea` / grises, sin contorno (como la estela de espada del Soldier) |
| Sensación | Bosque luminoso y amable con amenaza demoníaca (Demon, Blood Monster) |

**Paleta maestra** (todos los nuevos assets usan sólo estos colores, muestreados de los originales; ver `Tools/ArtGen/lib.py`):

- Verdes: `#7de230 #65d53e #5fcb39 #59c135 #14a02e #1a7a3e #23674e #24523b`
- Tierra/madera: `#f4d29c #dba463 #c88b60 #bb7547 #ba756a #a65d3d #8c5036 #71413b #5b3138 #4e2428`
- Agua: `#bce0f2 #78c3e9 #249fde #1e7fb1 #446285 #294d73 #285cc4`
- Piedra: `#d5d4d1 #b8bbc4 #8b93af #7b7773 #5a5755 #4a5462 #333941 #242234`
- Madera muerta: `#a08662 #796755 #5a4e44 #423934 #322b28`
- Acentos: `#fffc40 #f9a31b #fa6a0a #e86a73 #793a80 #403353`
- De los personajes (efectos/UI): `#ed0d0d #a22b4b #6e1438 #311339 #f4edea #d9d8d8 #c0bfbf #000000`

---

## 3. Assets faltantes identificados

1. Tilesets autotile reales (el pack sólo trae islas de ejemplo) → césped, hierba alta, acantilado, camino, agua con orillas.
2. Variantes de relleno para romper la repetición.
3. Agua animada, cascada y espuma.
4. Vegetación adicional (arbusto con bayas, arbustos grandes, árbol muerto, tronco caído, hierba que se mece, más flores, brote).
5. Props interactivos: barril, caja, vasija rompible, cofre animado, cartel, antorcha, hoguera, farol.
6. Decoración: valla con puerta, puente, ruinas, lápida, obelisco demoníaco (vincula el bosque con los enemigos).
7. Efectos: polvo, salpicadura, impacto, sangre, humo, explosión, fuego, bola de fuego demoníaca, brillo de recogida, curación, círculo de invocación.
8. Ambientación: hojas cayendo, luciérnagas, lluvia, motas, sombra de nubes, niebla, rayo de luz.
9. UI completa: panel, diálogo, botones, ranuras de inventario, barras, corazones, 14 iconos, indicadores de interacción, cursores.
10. Fondo de menú.

---

## 4-6. Assets creados, ubicación y dimensiones

Todas las rutas son relativas a `G:\Juegos\Assets\Art\`. La convención `_<W>x<H>` del nombre indica el tamaño de celda.

### Tilesets (Rule Tile, plantilla blob de 47 tiles, 8 columnas × 6 filas)
| Archivo | Tamaño | Notas |
|---|---|---|
| `Tilesets/Grass/tileset_grass_blob47_16x16.png` | 128×96 | Césped sobre tierra; borde marrón, briznas, migas de tierra como el original |
| `Tilesets/TallGrass/tileset_tallgrass_blob47_16x16.png` | 128×96 | Hierba alta `#14a02e` con borde dentado (como la mancha oscura del pack) |
| `Tilesets/Cliff/tileset_cliff_blob47_16x16.png` | 128×96 | Meseta elevada: cara sur de 11 px con estratos y labio de hierba, laterales, cima de césped |
| `Tilesets/StonePath/tileset_stonepath_blob47_16x16.png` | 128×96 | Camino empedrado (Voronoi periódico → sin costuras) |
| `Tilesets/Water/tileset_water_blob47_f0..f3_16x16.png` | 4 × 128×96 | Agua animada: orilla marrón → espuma → banda profunda → agua con ondas |
| `Tilesets/blob47_masks.json` | — | Orden de las 47 máscaras (N=1 NE=2 E=4 SE=8 S=16 SW=32 W=64 NW=128) |

### Terreno
| `Environments/Terrain/terrain_grass_fill_16x16.png` | 64×16 | 4 variantes (liso, briznas, mata, flor) |
|---|---|---|
| `Environments/Terrain/terrain_dirt_fill_16x16.png` | 64×16 | 4 variantes (lisa, guijarros, más guijarros, piedra) |

### Agua
| `Environments/Water/water_waterfall_body_anim_32x16.png` | 4 fr × 32×16 | Cuerpo de cascada en bucle vertical (apilable) |
|---|---|---|
| `Environments/Water/water_waterfall_top_anim_32x16.png` | 4 fr | Labio superior |
| `Environments/Water/water_waterfall_foam_anim_48x16.png` | 4 fr | Espuma en la base |

### Vegetación
| `Environments/Vegetation/veg_bushes_small_16x16.png` | 3 × 16×16 | Arbusto con bayas, arbusto redondo, brote |
|---|---|---|
| `Environments/Vegetation/veg_bush_large_32x24.png` | 32×24 | Arbusto grande |
| `Environments/Vegetation/veg_tree_dead_32x40.png` | 32×40 | Árbol muerto (zona corrupta) |
| `Environments/Vegetation/veg_log_fallen_32x16.png` | 32×16 | Tronco caído con musgo |
| `Environments/Vegetation/veg_tallgrass_sway_anim_16x16.png` | 3 variantes × 4 fr | Hierba que se mece |
| `Environments/Vegetation/veg_flowers_16x16.png` | 4 × 16×16 | Azules, rosas/malva, blancas, naranjas |

### Props
| `Props/props_static_16x16.png` | 7 × 16×16 | Barril, caja, vasija, vasija rota, cartel, rocas, lápida |
|---|---|---|
| `Props/prop_chest_open_anim_16x16.png` | 4 fr | Cofre: cerrado → abierto con destello |
| `Props/prop_torch_anim_16x32.png` | 4 fr | Antorcha de pie |
| `Props/prop_campfire_anim_16x16.png` | 4 fr | Hoguera |
| `Props/prop_lantern_post_16x32.png` | 16×32 | Farol con halo cálido |

### Decoración
| `Environments/Decorations/deco_fence_16x16.png` | 9 tiles | Valla: extremo izq., tramo, extremo dcho., poste, vertical sup./medio/inf., puerta cerrada/abierta |
|---|---|---|
| `Environments/Decorations/deco_bridge_16x16.png` | 6 tiles | Puente horizontal (O, centro, E) y vertical (N, centro, S) |
| `Environments/Decorations/deco_ruin_pillar_16x32.png` | 16×32 | Columna rota con musgo |
| `Environments/Decorations/deco_ruin_wall_32x32.png` | 32×32 | Muro en ruinas |
| `Environments/Decorations/deco_demon_obelisk_anim_16x32.png` | 4 fr | Obelisco con runa roja pulsante |

### Efectos (`Effects/`)
| Archivo | Frames × celda | Uso |
|---|---|---|
| `fx_dust_walk_anim_16x16.png` | 5 × 16 | Polvo al caminar |
| `fx_water_splash_anim_32x32.png` | 5 × 32 | Salpicadura |
| `fx_hit_spark_anim_32x32.png` | 4 × 32 | Impacto (mismo blanco que la estela de espada) |
| `fx_blood_burst_anim_32x32.png` | 5 × 32 | Sangre (Blood Monster / daño) |
| `fx_smoke_poof_anim_32x32.png` | 6 × 32 | Muerte / aparición |
| `fx_explosion_anim_48x48.png` | 7 × 48 | Explosión |
| `fx_fire_loop_anim_16x24.png` | 4 × 16×24 | Fuego en bucle |
| `fx_demon_fireball_anim_16x16.png` | 4 × 16 | Proyectil demoníaco (mira a la derecha; voltear con flipX) |
| `fx_pickup_sparkle_anim_16x16.png` | 5 × 16 | Recogida |
| `fx_heal_anim_32x32.png` | 6 × 32 | Curación |
| `fx_demon_summon_circle_anim_32x32.png` | 4 × 32 | Círculo de invocación (plano de suelo) |

### Ambientación (`Environments/Ambient/`)
`amb_leaf_fall_anim_8x8` (4 fr), `amb_firefly_anim_8x8` (4 fr, halo alpha), `amb_rain_8x8` (gota + 3 fr de salpicadura),
`amb_motes_4x4` (2), `amb_cloud_shadow` (96×48, alpha), `amb_fog_tile_seamless` (64×64, repetible), `amb_light_ray` (32×64).

### Fondos
`Environments/Backgrounds/bg_menu_forest_320x180.png` — fondo de menú 16:9 (×6 = 1920×1080) compuesto **sólo** con los tiles nuevos y sprites originales del pack de bosque.

> Parallax: el juego es cenital, así que capas de montañas/cielo lejanas no tendrían sentido en el mundo jugable. La profundidad se consigue con capas superpuestas animadas (sombra de nubes desplazándose, niebla repetible, rayos de luz, partículas). Si más adelante hay escenas laterales, se documenta como pendiente.

### UI (`UI/`)
| Archivo | Tamaño | 9-slice |
|---|---|---|
| `ui_panel_wood_9s8.png` | 48×48 | 8 px |
| `ui_dialog_box_9s6.png` | 48×32 | 6 px |
| `ui_button_states_48x16_9s4.png` | 3 × 48×16 (normal, hover, pulsado) | 4 px |
| `ui_inventory_slot_20x20_9s4.png` | 3 × 20×20 (normal, seleccionado, desactivado) | 4 px |
| `ui_bar_frame_9s3.png` + `ui_bar_fills_8x6.png` | 64×10 + 4 rellenos (vida, estamina, maná, vacío) | 3 px |
| `ui_hearts_16x16.png` | lleno, medio, vacío | — |
| `Icons/ui_icons_items_16x16.png` | 14 iconos: espada, hacha, arco, flecha, escudo, poción roja, poción azul, moneda, llave, seta, carne, pergamino, calavera, gema demoníaca | — |
| `ui_prompts_16x16.png` | tecla E (2 fr), "!" , "?" | — |
| `ui_cursors_16x16.png` | puntero, retícula | — |

### Herramientas
- `Assets/Editor/ArtPipeline/ArtImportPostprocessor.cs` — reglas de importación automáticas.
- `Assets/Editor/ArtPipeline/ArtAssetBuilder.cs` — menú **Tools ▸ Art ▸ Build Tiles, Palette & Animations**.
- `Assets/Editor/ArtPipeline/WoodsArt.Editor.asmdef` — ensamblado de editor; activa el código de Rule Tiles sólo si está instalado *2D Tilemap Extras*.
- `G:\Juegos\Tools\ArtGen\*.py` — generadores reproducibles (Python + Pillow): `tiles.py`, `props.py`, `fx.py`, `background.py`, `preview.py` (escenas de prueba), `contact.py` (hojas de contacto).

---

## 7. Configuración recomendada para Unity

Aplicada automáticamente por `ArtImportPostprocessor` (sólo en la primera importación; nunca pisa ajustes manuales posteriores. Para forzarla: **Tools ▸ Art ▸ Reapply Import Rules**):

| Ajuste | Valor |
|---|---|
| Texture Type | Sprite (2D and UI) |
| Sprite Mode | Single, o Multiple con rejilla uniforme según `_<W>x<H>` |
| Pixels Per Unit | **16** |
| Mesh Type | Full Rect (sin recortes de píxeles) |
| Filter Mode | **Point (no filter)** |
| Compression | **None** |
| Generate Mip Maps | Off |
| Wrap Mode | Clamp (Repeat para `*seamless*`) |
| Pivote | Abajo-centro: Vegetation, Props, Decorations. Centro: tiles, vallas, puentes, efectos, UI, ambiente |
| Bordes 9-slice | Según `_9s<N>` |

**Otros ajustes del proyecto**
- Grid de Tilemap: Cell Size (1,1,0).
- Cámara: *Pixel Perfect Camera* (URP 2D) con Assets PPU = 16 y resolución de referencia 320×180 (o 384×216).
- Orden de dibujo cenital: *Transparency Sort Mode* = Custom Axis (0,1,0) y Tilemap Renderer en modo *Individual* para los objetos; así personajes y props con pivote abajo se ordenan por Y.
- Capas sugeridas (Sorting Layers): `Ground` (relleno, césped, agua, camino) → `GroundDecor` (flores, sombra de nubes) → `Objects` (props, árboles, personajes; orden por Y) → `Overlay` (niebla, rayos, lluvia) → `UI`.
- **Personajes Tiny RPG**: si se copian a `Assets/Art/Characters/...` (manteniendo "100x100" en la ruta) el postprocesador los corta en 100×100 con PPU 16 y pivote (0.5, 0.4) en los pies. Usar los archivos por animación, no las hojas combinadas.
- Sprite Atlas: un atlas por grupo (`Tilesets+Terrain`, `Environment`, `Effects`, `UI`), *Filter Mode Point*, *Padding 2*, *Tight Packing off* (los tiles necesitan el rectángulo completo).
- Paquetes: `com.unity.2d.tilemap` y `com.unity.2d.tilemap.extras` (Rule Tiles).

**Tras abrir el proyecto**: ejecutar **Tools ▸ Art ▸ Build Tiles, Palette & Animations**. Genera:
- `Assets/Art/Tilesets/_Generated/RT_Grass, RT_TallGrass, RT_Cliff, RT_StonePath, RT_Water (animada), RT_GrassFill_Random, RT_DirtFill_Random`.
- Tiles simples de vallas, puentes y rellenos.
- Tile Palette `Woods_Terrain.prefab`.
- Clips de animación en `Assets/Art/Animations/...` (bucle o un solo disparo según el tipo; 12 fps efectos, 10 fps cascada, 8 fps el resto).

**Uso de capas de terreno**: relleno de tierra (o césped) en la base → césped → camino/hierba alta → agua → acantilado. Cada Rule Tile se pinta en su propio Tilemap.

---

## 8. Recursos que requieren animación

Todos los `*_anim_*`: agua (tiles), cascada (cuerpo, labio, espuma), hierba que se mece, cofre, antorcha, hoguera, obelisco, todos los efectos, hojas, luciérnagas, indicador "E".
La sombra de nubes, la niebla y los rayos de luz se animan por código/Transform (desplazamiento lento, alfa oscilante), no por frames.

---

## 9. Recursos pendientes (fuera de alcance o requieren decisión)

- **NPCs y nuevos personajes**: no se crearon, por la regla de no sustituir ni inventar personajes; habría que diseñarlos en Aseprite partiendo de las proporciones de los Tiny RPG.
- **Interiores / mazmorra** y **bioma de nieve o arena**: no hay pistas de que el juego los tenga; se pueden derivar del mismo sistema (`tiles.py`) cuando se decida.
- **Fuente bitmap** para la UI y números de daño.
- **Sombra proyectada al pie del acantilado** (el tile de abajo no conoce al de arriba): se puede añadir una capa de sombra o un Rule Tile extra.
- **Colisiones**: los Rule Tiles se generan sin collider; activar `Grid` o añadir *Tilemap Collider 2D* + *Composite Collider 2D* en los Tilemaps de agua y acantilado.
- **Parallax lateral**: sólo si se añaden escenas no cenitales.

---

## 10. Problemas detectados y soluciones aplicadas

### Verificación técnica realizada

| Comprobación | Resultado |
|---|---|
| Compilación de `ArtImportPostprocessor.cs` + `ArtAssetBuilder.cs` con el Roslyn de Unity 6000.6.4f1 contra sus DLL (`UnityEngine.*`, `UnityEditor.*`) y el código fuente de *2D Tilemap Extras 9.0.1* | ✅ 0 errores, en 3 configuraciones: con Extras + Tilemap Editor, sólo Extras, sin paquetes |
| Firma de `GridPaletteUtility.CreateNewPalette` y nombres de ensamblado del `.asmdef` (`Unity.2D.Tilemap.Extras`, `Unity.2D.Tilemap.Editor`) | ✅ Coinciden con los paquetes de 6000.6.4f1 |
| Rejillas de todas las hojas `_WxH` | ✅ Dimensiones divisibles exactas; única celda vacía = hueco 48 de las hojas blob (intencionado, se usan 47) |
| Costuras de tiles | ✅ Escenas de prueba compuestas con autotiling (césped, camino, agua, acantilado, hierba alta) sin líneas visibles |
| **Importación real dentro del Editor de Unity (batchmode)** | ⚠️ **No completada**: los tres intentos se quedaron sin memoria ("archivo de paginación demasiado pequeño" / "Out of memory") con 12 GB de RAM y otro editor de Unity abierto. No hubo ningún `error CS`. Pendiente: abrir el proyecto y ejecutar el menú (ver sección 7) |

| Problema | Solución |
|---|---|
| No hay proyecto Unity | Estructura `Assets/` lista para abrir `G:\Juegos` como proyecto o copiar la carpeta a uno existente |
| El pack de bosque no trae autotiles | Generador de blob de 47 tiles basado en campo de distancias con ruido periódico de 16 px → los bordes coinciden entre tiles vecinos |
| Primer pase de bordes demasiado recto/geométrico | Más ruido, apertura morfológica para redondear esquinas y briznas que sobresalen en vertical/horizontal; segunda revisión aprobada |
| Hierba alta sin dentado | Picos generados después del redondeo |
| Cascada leída como "lluvia" | Rayas con fase y longitud distintas por columna |
| Árbol muerto procedural ilegible | Redibujado a mano píxel a píxel |
| Cruces de curación y anillos con huecos | Anillos por muestreo angular (sin huecos), cruces más grandes con contorno suave |
| Bola de fuego con una "cruz médica" en el centro | Núcleo de 1-2 px |
| Halos en los bordes | Los píxeles con alpha 0 se guardan como (0,0,0,0); filtro Point y sin compresión |
| Carpetas "with shadows" idénticas a las de sin sombra | Documentado; no se tocó nada |

**Revisión de dirección de arte (resumen)**: los nuevos assets comparten paleta, grosor de contorno, dirección de luz y escala con el pack de bosque; el fondo de menú mezcla tiles nuevos y árboles originales sin que se note el cambio de autor. Los efectos y la UI usan los tonos de los personajes (rojos vino, blanco roto, contorno negro) para que el combate se lea con la misma voz que los sprites Tiny RPG.
