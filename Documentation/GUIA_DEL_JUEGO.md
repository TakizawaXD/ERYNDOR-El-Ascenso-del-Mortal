# La Espada del Bosque — guía

Action-RPG de mundo abierto en pixel art (Unity 6000.6.4f1, 2D). Eliges un caballero; el Señor Demonio ha corrompido el reino.

## Cómo abrirlo
1. Unity Hub → **Add project from disk** → `G:\Juegos`.
2. Abre `Assets/Game/Scenes/MainMenu.unity` y pulsa **Play**.
3. Si cambias arte o mapa: menú **Tools ▸ Game ▸ Build Game** (lo regenera todo: animadores, fuente, prefabs, interiores y escenas).

## Controles
| Acción | Tecla |
|---|---|
| Mover / correr | WASD o flechas / Shift (con aceleración suave) |
| Espada (pulsa 2 veces = combo) | J o clic izquierdo |
| Golpe fuerte | K o clic derecho |
| Arco | L |
| Rodar (invulnerable) | Espacio |
| Usar, hablar, abrir, entrar, dormir | E |
| Beber poción | Q |
| **Ficha del héroe (atributos)** | **C** |
| Inventario (armas y armaduras) | I |
| Mapa (en un pueblo: ← → cambia entre mapa local y del mundo) / diario de misiones | M / Tab |
| Pausa | Esc |

## Clases (se eligen en NUEVA PARTIDA)
Pantalla **ELIGE TU HÉROE**: carrusel de 10 clases (A/D o el ratón), cada una con su propio personaje dibujado y su sexo; Enter pasa a escribir el **nombre del héroe** (Retroceso borra, Enter empieza, Esc vuelve). El nombre aparece en el HUD.

| Clase | Aspecto | Sexo | FUE | VIT | AGI | DES | DEF | Arma inicial | Habilidad |
|---|---|---|---|---|---|---|---|---|---|
| Caballero | Soldado | H | 3 | 4 | 3 | 3 | 3 | Espada larga | Versátil: +4 puntos por nivel |
| Caballero Real | HeroKnight | H | 4 | 4 | 2 | 2 | 5 | Espada del caballero | Baluarte: recibe 1 daño menos |
| Cruzado | HeroCrusader | H | 3 | 5 | 2 | 3 | 4 | Lanza | Sagrado: sus golpes castigan a los demonios |
| Guerrero del Hacha | HeroAxeKnight | H | 6 | 4 | 2 | 2 | 3 | Hacha de guerra | Sed de sangre: cada enemigo te cura |
| Mercenario | HeroSoldier | H | 4 | 3 | 4 | 3 | 2 | Espada corta | Codicia: +50 % de monedas |
| Mago | HeroWizard | H | 2 | 3 | 3 | 6 | 2 | Bastón de roble | Arcano: saetas +1 daño |
| Espadachina | HeroSwordswoman | M | 3 | 3 | 6 | 4 | 2 | Estoque | Filo certero: +10 % de crítico |
| Sacerdotisa | HeroPriestess | M | 2 | 6 | 3 | 3 | 4 | Maza sagrada | Fe: pociones +50 % y regenera vida |
| Arquera | HeroRanger | M | 2 | 3 | 5 | 6 | 2 | Daga + arco largo | Ojo de halcón: flechas perforantes |
| Samurái | Soldado lacado rojo y negro | H | 5 | 3 | 5 | 3 | 2 | Katana | Bushido: +2 daño con katana |

Los héroes dibujados llevan su arma en el propio sprite; el Caballero y el Samurái cambian de animación según el arma equipada.

**Reglas de armas**: la magia es del **Mago** (solo bastones; con L lanza una saeta mágica, sin flechas) y el arco es de la **Arquera** (solo arcos y su daga). El resto de clases usa cualquier arma cuerpo a cuerpo salvo los bastones, y no dispara. La bolsa avisa si intentas equipar algo que tu clase no puede usar.

**Acciones de los héroes dibujados**: `python Tools/CharAnim/hero_actions.py` les crea, a partir de sus propios fotogramas, las 19 acciones que solo tenía el Soldado (combo, crítico, ataque cargado, rodar, retroceso, recoger, interactuar, sentarse, dormir, nadar, trepar, saltar/caer/aterrizar, empujar/tirar, victoria y derrota). Vista previa: `Documentation/CharacterPreviews/hero_actions.png`.

## Atributos (ficha con C)
- **Fuerza** → daño de espada (1 + FUE/2 + mejoras de herrería).
- **Vitalidad** → vida máxima (4 + VIT×2) y curación de pociones.
- **Agilidad** → velocidad (+4 % por punto), esquiva (1,2 % por punto) y recarga de la voltereta.
- **Destreza** → daño del arco y probabilidad de crítico (3 % por punto, críticos ×2).
- **Defensa** → armadura: resta DEF/3 a cada golpe (mínimo 1).
- Al subir de nivel: vida completa + puntos de atributo (nivel máximo 30). En la ficha: W/S para elegir, Enter para subir.

## Experiencia y puntos
Cada enemigo da experiencia (verás "+3 XP" al derrotarlo; los poderosos dan ×3, los campeones ×8). La barra fina dorada del HUD es la experiencia; al subir de nivel aparece "+N puntos (C)": pulsa **C** y repártelos entre los atributos.

## Armas y armaduras (inventario con I)
33 objetos en 4 rarezas (**común**, **raro**, **épico**, **legendario**, cada una con su color). Cada tipo de arma se maneja distinto:
| Tipo | Ejemplos | Cómo se siente |
|---|---|---|
| Espada | Espada corta, larga, del caballero, Hoja de ceniza (fuego) | Equilibrada |
| Espadón | Espadón | Lento, barrido enorme, mucho daño |
| Katana | Katana, Katana lunar (escarcha), Espada rúnica (roba vida) | Muy rápida, críticos |
| Estoque | Estoque | Estocada larga y fina, muchos críticos |
| Daga | Daga, Daga venenosa | Rapidísima, corto alcance |
| Lanza | Lanza, Alabarda, Tridente del mar | El mayor alcance |
| Hacha | Hacha de guerra, Hacha de escarcha | Tajos anchos y fuertes |
| Martillo | Martillo de guerra, Maza sagrada (×1,5 a demonios) | Muy lento, aturde y empuja |
| Arcos | Arco corto, largo, de hueso, élfico (3 flechas), del dragón (2 flechas de fuego), Ballesta (perfora) | Distinto tensado y velocidad de flecha |
| Armaduras | Ropa de viaje, cuero, cota de malla, placas, sagrada, sombría, capa de montaraz, coraza de escarcha, dracónica | Defensa, vida extra y velocidad |

- Efectos elementales: **fuego** y **veneno** dañan con el tiempo, **escarcha** ralentiza, **sagrado** castiga a los demonios.
- Cómo conseguirlos: cofres (la mitad tienen equipo), enemigos (raro), **poderosos** (35 %), **campeones** y **jefes** (siempre, de calidad alta) y los **yunques de las herrerías** (tienda de armas y armaduras).
- Inventario (**I**): flechas para moverte, **Enter** para equipar; muestra la comparación (+/-) con lo que llevas.
- Cada clase empieza con su equipo: Caballero espada larga + cota; Paladín martillo + placas; Caballero Oscuro espadón + cuero; Montaraz daga + arco largo + capa.

## Interfaz
Fuente nueva (minúsculas y tildes) y HUD minimalista sin marcos: arriba a la izquierda clase y nivel, barra de vida, barra de experiencia y monedas/flechas/pociones; arriba a la derecha minimapa, reloj y amenaza; abajo cuatro casillas con tu arma, golpe fuerte, arco y pociones. Las ayudas de teclas desaparecen solas a los 20 segundos.

## Día y noche
- Reloj del mundo: **30 minutos reales de día (06:00–18:00) y 30 de noche (18:00–06:00)**. 1 hora del juego = 2,5 min reales.
- El HUD muestra el sol/luna, el día y la hora. Amanecer y atardecer tiñen el mundo; de noche todo oscurece y se encienden hogueras, antorchas, ventanas de las casas y tu farol.
- **De día** salen las criaturas de cada región; **de noche** los residentes diurnos duermen y aparecen **espectros** y **caballeros caídos**, que **arden al amanecer**.
- Dormir en una cama (E) salta hasta el amanecer (si es de noche) o hasta el anochecer (si es de día), cura y guarda.

## Clima: viento y lluvia
- **Suelo de fantasía oscura**: los caminos y las plazas de pueblos y Ciudadela son **losas de piedra gris azulada desgastadas**, con **musgo y hierba verde intensa** que las invade en manchas y crece entre las juntas, **charcos** oscuros, zonas húmedas en la hierba y **florecillas azules luminosas**. Las 10 regiones conservan su aspecto (lago, pantano, nieve, arenas rojas, ceniza…) con un tono más oscuro.
- **Viento**: árboles, arbustos, plantas, juncos y matas de hierba se mecen con una brisa constante y **ráfagas**; cada planta lleva su propio ritmo, así que el campo ondula. Con lluvia sopla más fuerte.
- **Lluvia**: cada pocos minutos (≈2,5–5,5 min de cielo despejado) llega un **chubasco** de 1–2,5 min: gotas inclinadas por el viento, **salpicaduras** en el suelo, cielo más oscuro, **sonido de lluvia** y algún **relámpago** en lo más fuerte. Convive con el día y la noche (de noche la lluvia también se oscurece). Dentro de las casas solo se oye amortiguada.
- **Esporas verdes** brillantes flotan sobre la hierba y los bosques, más de noche y menos cuando llueve (no en nieve, desierto ni ceniza).

## Música y sonido
Banda sonora **original, compuesta por código** (`Tools/GameGen/music.py`): progresiones de acordes y melodías hechas a partir
de motivos, en estilo RPG pixel/chiptune con instrumentos cálidos (pulsos suaves, arpa, laúd, flauta, celesta, cuerdas, órgano,
coro, metales). El **tema principal** (leitmotiv de 8 compases en re mayor) suena en la pantalla de título, en el Valle Central,
en el campamento y en la fanfarria de victoria. Todas las piezas son **bucles sin corte**: la cola de reverberación del final se
pliega sobre el principio. Escúchalas en `Documentation/Audio/` (`muestrario_musica.wav`, `muestrario_efectos.wav`,
`muestrario.md` con los minutos, e `index.html` con cada pista completa).

| Pieza | Dónde suena | Carácter | Archivos |
|---|---|---|---|
| Título | menú principal | tema principal lento: flauta, arpa, cuerdas (con entrada) | `music_menu_intro/_loop` |
| Elección de clase | NUEVA PARTIDA | marcha heroica suave, trompa y caja | `music_classselect_loop` |
| Valle Central (tema del mundo) | región a | tema principal a 104 BPM, pulso y laúd | `music_region_a_loop/_night` |
| Bosque del Oeste | región b | 6/8 dórico, flauta y laúd | `music_region_b_*` |
| Lago Espejo | región c | lidio, celesta y arpegios de arpa | `music_region_c_*` |
| Pantano Carmesí | región d | frigio con *swing*, clarinete grave y escobillas | `music_region_d_*` |
| Picos Nevados | región e | vals en la menor, carillón y cuerdas | `music_region_e_*` |
| Arenas Rojas | región f | frigio dominante, laúd árabe (oud) y tabla | `music_region_f_*` |
| Monte Ceniza | región g y su mapa | menor armónica, metales, coro y tambores | `music_region_g_*` |
| Bosque Corrupto | región h | acordes prestados inquietantes, campana y latido | `music_region_h_*` |
| Ciudadela del Rey | región i (camino real) | marcha mixolidia de metales | `music_region_i_*` |
| Costa del Puerto | región j | 6/8 marinero, acordeón | `music_region_j_*` |
| Villa del Valle | pueblo City_Valle | vals pastoral, flauta y laúd | `music_city_valle_*` |
| Ciudadela | pueblo City_Ciudadela | solemne y tranquila, trompa y órgano suave | `music_city_ciudadela_*` |
| Puerto | pueblo City_Puerto | giga alegre, acordeón y pandereta | `music_city_puerto_*` |
| Casa | casas y cabañas | caja de música y piano eléctrico | `music_int_casa_loop` |
| Posada | posadas | giga de taberna con jarras | `music_int_posada_loop` |
| Capilla | capilla y biblioteca | coral de órgano y coro | `music_int_capilla_loop` |
| Herrería | herrería y cuartel | ritmo de yunque | `music_int_herreria_loop` |
| Campamento | junto a una hoguera | tema principal a la guitarra | `music_camp_loop` |
| Combate | enemigos persiguiéndote cerca | mi menor, 152 BPM | `music_combat_loop` |
| Combate de élite | élites, campeones, jefes fuera de guarida | do# armónica, metales y coro | `music_combat_elite_loop` |
| El Invocador | su guarida sellada | ritual: coro y campanas | `music_boss_I_intro/_loop` |
| Gorgrak el Caudillo | su guarida | tambores de guerra | `music_boss_K_*` |
| Madre de Sangre | su guarida | vals macabro en 6/8, órgano | `music_boss_Q_*` |
| Coloso de Escarcha | su guarida | cristalino y pesado, timbales | `music_boss_F_*` |
| Señor Demonio | Monte Ceniza | batalla final: órgano, coro y percusión completa | `music_boss_B_*` |
| Fanfarrias | victoria, derrota, subir de nivel, región nueva | cortas, la música baja debajo | `jingle_victory/defeat/levelup/discover` |

- **Capa de noche**: cada región y cada pueblo tiene una segunda versión (`_night`) con la misma armonía, tempo y duración
  pero otra instrumentación (sin batería, flauta, campana, arpa). Suenan a la vez y se funden según lo oscuro que esté el cielo.
- **Transiciones**: fundido cruzado al cambiar de región (la región tiene que mantenerse 1,5 s, para no saltar en las fronteras),
  de mapa o de interior; el combate entra en ~1,5 s y al acabar (4 s sin enemigos persiguiéndote) vuelve la música de la zona
  **por donde iba**. Las piezas con entrada la tocan una vez y enlazan el bucle sin hueco.
- **Ducking**: con la pausa, la bolsa, el mapa, la ficha, las tiendas o un diálogo la música baja al 45 %; con una fanfarria, al 15 %.
- **Volúmenes**: en **PAUSA** hay dos filas, **MÚSICA** y **EFECTOS** (← → de 10 en 10 %, Enter las recorre). Se guardan.

**Efectos** (`Tools/GameGen/sfx2.py`, 180 archivos): casi todos tienen 2–3 variantes y en cada uso cambian un poco de tono y
volumen, así que no se repiten igual. Los del mundo suenan **en su sitio**: más bajos con la distancia y a izquierda o derecha.
- Pasos por suelo: hierba, tierra, piedra, madera (interiores, puentes, muelles), arena, nieve, agua, barro, ceniza.
- Armas: tajo de espada, tajo ligero (daga, katana), estocada (estoque, lanza), golpe pesado (espadón, hacha, martillo);
  impactos de filo, contundente, perforante, crítico, fuego, escarcha, veneno, sagrado y golpe recibido.
- Bloqueo con escudo, parry, contraataque, rotura de guardia, voltereta, cansancio; arco, bola de fuego, escupitajo, conjuro,
  curación, teletransporte, bomba.
- Voces de enemigos por especie (orcos, demonios, monstruos de sangre): alerta, ataque, herido, muerte; los élites y jefes, más graves.
- Animales: gallina, cerdo, vaca, oveja (de vez en cuando y al asustarse), gato (maullido y **ronroneo** al acariciarlo).
- Interfaz: mover, aceptar, cancelar, abrir y cerrar menús, bolsa, equipar, comprar, vender, error. Mundo: puertas al entrar y
  salir, viaje entre mapas, cofre, monedas, pociones, comer, recoger, yunque, fabricar, romper, hablar, encender la hoguera.
- **Ambiente por zona** (`Tools/GameGen/ambience.py`): pájaros de día y grillos de noche, viento (fuerte en los picos, seco en el
  desierto), olas en la costa y el puerto, el lago, lava, ranas y burbujas en el pantano, el zumbido del bosque corrupto, el
  murmullo de los pueblos y la chimenea crepitando en casas, posada, herrería y junto a las hogueras. La lluvia es del clima.

## Enemigos por región (y su inteligencia)
| Región | De día | De noche |
|---|---|---|
| Valle Central | Orcos, limos tóxicos | Espectros, caballeros caídos, orcos |
| Bosque del Oeste | Orcos, orcos berserker | Espectros, limos, berserkers |
| Lago Espejo | Limos tóxicos, orcos | Espectros, limos |
| Pantano Carmesí | Monstruos de sangre, limos | Monstruos de sangre, espectros |
| Picos Nevados | Orcos de hielo, berserkers | Orcos de hielo, espectros |
| Arenas Rojas | Orcos del desierto, berserkers | Demonios de ceniza, orcos del desierto, espectros |
| Monte Ceniza | Demonios de ceniza, engendros de magma | + demonios |
| Bosque Corrupto | Demonios, monstruos de sangre | Demonios, espectros, caballeros caídos |
| Ciudadela del Rey | (segura de día) | Caballeros caídos, espectros |
| Costa del Puerto | Orcos corsarios | Corsarios, espectros |

| IA | Quién | Cómo pelea |
|---|---|---|
| Manada | Orco, corsario | Avisa a los compañeros cercanos y te rodea por los flancos |
| Embestida | Orco berserker, Gorgrak el Caudillo | Se prepara temblando y carga en línea recta; si choca con un muro queda aturdido |
| Hostigador | Orco del desierto | Golpea y retrocede, te rodea mientras recarga y huye herido |
| Bruto | Orco de hielo, demonio de ceniza | Lento, golpes pesados, casi no retrocede |
| Tirador | Monstruo de sangre, Madre de Sangre | Mantiene la distancia y escupe |
| Emboscada | Limo tóxico | Casi invisible; salta cuando pasas cerca |
| Bomba | Engendro de magma | Dispara de lejos y explota al morir |
| Hechicero | Demonio, Señor Demonio | Se teletransporta a tu alrededor y lanza fuego |
| Espectro | Espectro (noche) | Atraviesa muros y árboles, se desvanece tras golpear |
| Duelista | Caballero caído (noche) | Bloquea golpes de frente, esquiva tus ataques y contraataca |

## Nuevo elenco: aventureros y monstruos
42 personajes nuevos (`Tools/CharAnim/roster.py`, recortados de las dos hojas de `Assets/Scripts` y reparados: las partes que tapaba otro personaje están dibujadas). Todos tienen animación en 4 direcciones: **quieto** (respiración, o flotando los voladores), caminar, ataque, ataque fuerte, especial/conjuro, herido y muerte.
- **Aventureros** en los pueblos (habla con E): Aria y Hermana Lucía (**cura** una vez al día) e Ivy (**8 flechas** al día) en la aldea; Sir Rodrigo, Hermano Tomás y Gunnar (**guardias**: atacan a los enemigos que se acercan), Merlina (**consejos** para cada jefe) y el Capitán Alonso (**patrulla**) en la Ciudadela; el soldado Bruno en el puerto.
- **Monstruos** por región, cada uno con su IA: goblins (manada, vikingo, chamán que lanza fuego, jinete que embiste), hombre lobo y lobo guerrero, limo verde (emboscada), murciélagos, esqueletos (de noche; lancero duelista), la Parca (espectro), diablillos, verdugo demoníaco, can infernal, gran demonio alado, segador, babosa de fuego (explota), calavera ígnea, tentáculo y fauces del pantano, minotauro, ojo vigía, lancero oscuro, bruto del escudo, enjambre, gólem de lava y reina demonio.

## Murallas
Las marcas de muralla del mapa forman ahora tramos continuos (`Tools/ArtGen2/castle.py`, `GameBuilder.Castle.cs`): muro de sillería con almenas, adarve y troneras; los tramos norte-sur se ven desde arriba; y en esquinas, extremos y puertas hay baluartes cuadrados con bandera y estandarte.

## Jefes y sus guaridas
Cada jefe tiene un **sprite propio de 128 px** (no es un recoloreado), animado en 4 direcciones (reposo, caminar, ataque, ataque pesado, ataque especial, conjuro, herido y muerte que se deshace en brasas), y una **guarida** con decorado propio: suelo de losas, círculo rúnico que late, pilares con estandartes y cadenas, braseros, columnas de luz, niebla y escombros, todo en el color del jefe.

| Jefe | Dónde | Aspecto | Movimientos especiales (fases 1 → 3) |
|---|---|---|---|
| **El Invocador** | Bosque Corrupto (claro al noroeste) | Encapuchado gigante con aureola de pinchos, orbe violeta y cadenas | Inmune mientras vivan sus siervos (al caer todos queda indefenso). Abanico de orbes → anillo de orbes y onda → espiral |
| **Gorgrak el Caudillo** | Arenas Rojas | Orco acorazado, yelmo de calavera con cuernos, hombreras de pinchos, cuchilla enorme | Golpe al suelo (onda) → llama a orcos del desierto y lanza hachas en abanico → doble onda y rocas que caen |
| **Madre de Sangre** | Pantano Carmesí | Masa carmesí con corona de hueso, muchos ojos y una boca enorme | Anillo de escupitajos → engendra limos tóxicos y onda → espiral de escupitajos |
| **Coloso de Escarcha** | Picos Nevados, junto al camino del norte | Titán de piedra y hielo con cristales en los hombros y un corazón helado | Onda de escarcha → carámbanos que caen (marcas en el suelo) → ráfaga de esquirlas y orcos de hielo |
| **Señor Demonio** | Monte Ceniza (mapa del volcán) | Alado, cuernos de carnero, corona de fuego, venas de lava, espadón ardiente | Abanico de bolas de fuego y meteoros → espiral de fuego → diablillos de ceniza y doble onda |

- **Fases**: a 2/3 y 1/3 de vida el jefe ruge, la arena se ilumina más y añade movimientos; cada fase empuja con una onda.
- **Ondas**: anillos que se expanden por el suelo; esquívalos con la voltereta (invulnerable) o aléjate. **Marcas** en el suelo: sal antes de que estallen.
- **La guarida se sella**: al empezar la pelea con el jugador dentro, un muro de runas cierra el círculo y suena la música de jefe. Se abre al vencer (o si mueres).
- **HUD de jefe**: barra ornamentada arriba en el centro con su nombre, daño “fantasma”, indicador de fase, y el **objetivo** arriba a la derecha (“Derrota a …”), que se marca como completado al ganar.

## Enemigos con silueta propia
Las variantes regionales parten de 4 cuerpos base pero ya no son solo recolores: cada tipo tiene rasgos propios y un **aura** (ojos que brillan, halo en el suelo y motas):
orco del desierto (cresta de hueso, ojos ámbar), orco de hielo (cuernos y cristales de hielo), corsario (tricornio), berserker (grandes cuernos, ojos rojos), demonio de ceniza (llamas en la cabeza), espectro (llamas azules), limo tóxico (púas), engendro de magma (llamas), caballero caído (penacho fantasmal, ojos cian).

## Atmósfera por zona
Cada región tiene su propia luz, niebla y partículas (y una arena de jefe tiene la suya mientras estás dentro):
Valle (luz cálida, luciérnagas) · Bosque del Oeste (verde, hojas que caen) · Lago Espejo (azulado, neblina) · **Pantano Carmesí** (rojizo, niebla roja, esporas) · **Picos Nevados** (frío, nieve) · **Arenas Rojas** (calima, arena que sopla) · **Monte Ceniza** (rojo, brasas que suben, humo) · **Bosque Corrupto** (morado oscuro, niebla violeta, fuegos fatuos; las antorchas brillan también de día) · Ciudadela (polvo en el aire) · Costa (bruma y salpicaduras).

## Amenaza: cuanto más matas, más aparecen
- **Nivel de amenaza** = 1 + enemigos derrotados / 12 (máx. 10), visible en el HUD y en la ficha.
- Más amenaza → más enemigos a la vez (2 + amenaza, +2 de noche), apariciones más rápidas, más vida/daño y más **PODEROSOS** (élites: ×2,5 vida, más daño, brillo dorado, triple botín).
- De noche, con amenaza ≥ 3, puede aparecer un **CAMPEÓN** (×5 vida, barra de jefe, gran botín).

## Un solo mapa: mundo, pueblos, Monte Ceniza y subsuelo
Desde el 21-11-2026 todo el juego es **un único mapa** (escena `World`, 970×480 casillas): no hay pantallas de carga entre lugares.
- **Superficie** (720×480, 10 biomas muy extensos): Valles de Valtherion, Bosque Eterno de Eldoria, Aurelith, Noxheim, Tierras Heladas de Valgrimm, Desierto de los Antiguos, Drakmor, la Torre Prohibida, el Reino de Valtherion y las Ruinas Eternas.
- **Pueblos dentro del mundo**: la Aldea del Valle (aquí empieza la partida), la Ciudadela del Rey y el Puerto de las Ruinas (en la costa sur) están en su sitio, con sus casas, vecinos, tiendas y caminos que salen de cada puerta hacia la red de caminos.
- **Monte Ceniza** está dentro de Drakmor, rodeado de acantilados; su única entrada es el **Sello de Drakmor**, que cae al derrotar a Gorgrak y a la Madre de Sangre.
- **Subsuelo**: cada entrada de mazmorra baja (fundido a negro) a una cueva o cripta del mismo mapa. Bajo tierra todo está oscuro salvo las antorchas, braseros y tu farol; no llueve; la cámara solo muestra la cueva en la que estás.

| Entrada | Bajo tierra | Jefe |
|---|---|---|
| Catacumbas del Rey Olvidado (Valles) | 6 zonas: cementerio, galerías, criptas, santuario, puente y trono | El Rey Sepultado |
| Fosos de Guerra Orcos (Desierto) | cueva de orcos y goblins | Gorgrak el Caudillo |
| Cripta de Escarcha (Valgrimm) | cueva helada | Coloso de Escarcha |
| Catacumba de los Condenados (Noxheim) | cripta de esqueletos y segadores | El Invocador |
| Torre Carmesí (Noxheim) | Cripta Carmesí | Madre de Sangre |

- **Criaturas por bioma**: cada región tiene la suya (goblins y jinetes en los valles, hombres lobo en el bosque, esqueletos y ojos vigía en Aurelith, tentáculos y fauces en Noxheim, orcos de hielo y minotauros en Valgrimm, orcos del desierto y diablillos en las arenas, gólems de lava y canes infernales en Drakmor, demonios en la Torre Prohibida, corsarios en las Ruinas). De noche se suman espectros y caballeros caídos.
- **Clima por bioma**: lluvia en praderas y bosques, **nieve** en Valgrimm, **tormentas de arena** en el desierto y **ceniza con ascuas** en Drakmor y la Torre Prohibida.
- **Mapa (M)**: muestra la superficie; bajo tierra te marca en la entrada de la cueva. El minimapa se oculta bajo tierra.
- **Partidas antiguas**: si guardaste en un pueblo o en el Monte Ceniza, apareces en ese mismo punto del mapa único; si guardaste en el mundo antiguo (más pequeño), empiezas en la Aldea del Valle con todo tu equipo.
- **Regenerar**: `python Tools/GameGen/world3.py G:/Juegos` → `python Tools/GameGen/merge_world.py G:/Juegos` → `python Tools/ArtGen2/paint_world_merged.py` → en Unity **Tools ▸ Game ▸ Build Game**.

## Casas con interior (18)
Todas las casas de los pueblos se pueden visitar (E en la puerta; sal pisando el felpudo):
- **Casa**: salón con chimenea, cocina y dormitorio. **Cabaña**: una estancia acogedora.
- **Posada del Jabalí**: barra (tienda), mesas, chimenea y habitaciones.
- **Herrería**: forja, yunque (tienda de mejoras), armería y almacén.
- **Cuartel del Rey**, **Capilla** (altar: vida y pociones + guardar), **Biblioteca del Sabio** (libros con pistas).
- Camas para dormir/guardar, cofres con botín, estanterías con historia y caballeros con los que hablar.

## El mundo (720×480 casillas de superficie, 10 regiones)
- **Campamentos** y **camas** (en el mundo y en cada pueblo): descansa → vida completa y partida guardada. Al morir vuelves al último sitio donde guardaste (pierdes ¼ de las monedas).
- **Tiendas**: puestos de la aldea, la ciudadela y el puerto, barra de la posada y yunques: pociones, flechas, espada +1 (×3), corazón extra (×3).
- **Cofres** (27 en el mundo + los de las casas).
- **Historia**: derrota a **Gorgrak el Caudillo** (Arenas Rojas) y a la **Madre de Sangre** (Pantano Carmesí); se rompe el **Sello del Monte Ceniza**, cruzas al mapa del volcán y te enfrentas al **Señor Demonio**. Después puedes seguir explorando.

## Cómo está hecho
| Parte | Dónde |
|---|---|
| Diseño del mapa | `Tools/GameGen/world2.py` → `Assets/Game/Levels/World2.txt` |
| Pueblos y Monte Ceniza (trazado, puertas, casas, vecinos) | `Tools/GameGen/maps.py` → `Assets/Game/Levels/Maps.txt` (catálogo de mapas y puertas) + `City_*.txt`, `Zone_MonteCeniza.txt` |
| Suelo de los pueblos y del volcán | `Tools/ArtGen2/paint_maps.py` (mismo pintor que el mundo) → `Assets/Art/World/Maps/<Mapa>/` (trozos + `map.png`); vistas previas en `Tools/ArtGen2/previews/` |
| Viajes entre mapas | `Assets/Game/Scripts/Flow/MapDB.cs` (catálogo), `GameManager.Maps.cs` (viajar, llegada, guardar el mapa, enemigos derrotados), `World/MapGate.cs` (puertas), `UI/WorldUI.Maps.cs` (mapa M); constructor `GameBuilder.Maps.cs` |
| Suelo pintado (estilo oscuro: losas con musgo, charcos, flores azules) | `Tools/ArtGen2/painter_dark.py` (usa `painter.py`) → `Assets/Art/World/Ground/` + `world_map.png` |
| Viento y lluvia | `Assets/Game/Shaders/SpriteWind.shader` (balanceo anclado en el pie), `Assets/Game/Scripts/World/WeatherSystem.cs`, constructor `GameBuilder.Weather.cs`; arte y sonido `Tools/ArtGen2/weather_art.py` |
| Iconos de armas, efectos de golpe, interfaz plana | `Tools/ArtGen2/items.py` |
| Fuente | `Tools/GameGen/font.py` → `Assets/Game/Fonts/` |
| Interiores y muebles | `Tools/ArtGen2/interiors.py` → `Assets/Art/World/Interiors/` + `Assets/Game/Levels/Interiors.txt` |
| Clases y enemigos regionales (paleta + rasgos propios) | `Tools/CharAnim/variants.py` + `features.py` → `Assets/Art/Characters/<Variante>/` |
| Jefes (sprites de 128 px, 4 direcciones) | `Tools/CharAnim/bosses.py` (pintor `bossart.py`) → `Assets/Art/Characters/Boss*/`; vista previa `Documentation/CharacterPreviews/bosses.png` |
| Guaridas y HUD de jefe | `Tools/ArtGen2/arena.py` → `Assets/Art/World/Arena/`, `Assets/Art/UI/Boss/`; constructor `GameBuilder.Bosses.cs`; código `BossBrain`, `BossArena`, `BossHazards`, `ArenaProp`, `UI/BossHud` |
| Música (todas las piezas, capas de noche, entradas, fanfarrias) | `Tools/GameGen/music.py` (sintetizador `synth.py`, teoría `theory.py`) → `Assets/Game/Audio/Music/` |
| Efectos y ambientes | `Tools/GameGen/sfx2.py` → `Assets/Game/Audio/sfx_*`; `Tools/GameGen/ambience.py` → `Assets/Game/Audio/Ambience/`; muestras `Tools/GameGen/audio_samples.py` → `Documentation/Audio/` |
| Sistema de audio | `Scripts/Core/Sfx.cs` (efectos, variantes, posición, volúmenes), `MusicDirector.cs` (pieza por zona, fundidos, noche, combate, jefes, ducking), `AmbienceDirector.cs`, `UI/VolumeOptions.cs`; los enganches se aplicaron con `Tools/GameGen/audio_patch.py`; importación `Editor/GameAudioPostprocessor.cs` |
| Sonidos de jefe (fase, terremoto, onda, hielo, invocación) | `Tools/GameGen/music_boss.py` → `Assets/Game/Audio/` |
| Atmósfera por zona y auras | `World/ZoneAtmosphere.cs` (en la cámara), `Actors/EnemyAura.cs` |
| Código | `Assets/Game/Scripts/` — RPG (`KnightClass`, `PlayerState`, `Progression`), World (`DayNight`, `DayNightLighting`, `SpawnDirector`, `Interior`…), Actors (`EnemyController` con perfiles de IA), UI (`Hud`, `ClassSelect`, `WorldUI` ficha) |
| Luz nocturna | `Assets/Game/Shaders/SpriteMultiply.shader` + `SpriteAdditive.shader` |
| Constructor | `Assets/Game/Editor/GameBuilder*.cs` (`GameBuilder.Rpg.cs`: clases, enemigos, interiores, luces) |
| Pruebas + capturas | `Assets/Game/Tests/` → `Documentation/Screenshots` |

Para regenerar: `python Tools/GameGen/world2.py G:/Juegos`, `python Tools/GameGen/maps.py G:/Juegos`, `python Tools/ArtGen2/painter_dark.py`, `python Tools/ArtGen2/paint_maps.py`, `python Tools/ArtGen2/weather_art.py`, `python Tools/ArtGen2/interiors.py`, `python Tools/CharAnim/variants.py`, `python Tools/CharAnim/bosses.py`, `python Tools/ArtGen2/arena.py`, `python Tools/GameGen/music_boss.py`, `python Tools/GameGen/music.py`, `python Tools/GameGen/sfx2.py`, `python Tools/GameGen/ambience.py`, y en Unity **Tools ▸ Game ▸ Build Game**.
