using System;
using System.Collections.Generic;
using System.Linq;

namespace WoodsGame
{
    /// <summary>A personal question with two answers. The NPC remembers which one you gave (memory note) and brings it up later.</summary>
    public class NpcChoice
    {
        public string ask;
        public string[] answers = new string[2];
        public string[] replies = new string[2];
        public int[] affinity = { 1, -1 };
        public string[] notes = new string[2];       // remembered as memory notes
        public string[] recall = new string[2];      // said in later greetings
    }

    /// <summary>A small job a townsperson gives you: bring materials, or defeat enemies (counted from the moment you accept).</summary>
    public class NpcQuest
    {
        public string title, offer, accepted, progress, done, reward;
        public string mat; public int n = 1;                     // deliver
        public Func<PlayerState, int> counter;                   // or: kill counter
        public Action<PlayerState> give;
        public bool Deliver => mat != null;
    }

    /// <summary>Who someone is: name, trade, personality, look (Assets/Art/Characters/&lt;sprite&gt;), lines and job.</summary>
    public class NpcDef
    {
        public string id, name, job, sprite, town, service = "", workAnim = "";
        public string personality, bio;
        public string[] first, again, friend, night, barks, busy;
        public (string q, string a)[] topics = new (string, string)[0];
        public NpcChoice choice;
        public NpcQuest quest;
        public string likes, likesThanks;
        // routine, resolved by the builder in the town map (town = map id):
        //   "a:<anchor>[#n]:dx,dy[:dir]"  next to a landmark: fire, well, shop, sign, mill, start, house:<template>[#n] (its door)
        //   "i:<template>[#n]:x,y[:dir]"  inside a house of that template (interior tiles, as in Interiors.txt)
        //   "m:x,row[:dir]"               a tile of the town map;   dir = ^ v < > (which way they face there)
        public string[] work = new string[0], social = new string[0];
        public string sleep;
        public bool nightOwl;        // guards: on duty at night instead of sleeping
    }

    public static class NpcDB
    {
        static string[] L(params string[] s) => s;

        public static readonly NpcDef[] All =
        {
            // ======================================================== EL PUEBLO (Valle Central)
            new NpcDef
            {
                id = "bruna", name = "Bruna", job = "Herrera del pueblo", sprite = "NpcBruna", town = "City_Valle", service = "smith", workAnim = "Attack",
                personality = "Brusca, orgullosa de su oficio, buen corazón bajo el hollín.",
                bio = "Bruna. Hija de herrero y nieta de herrero. Si algo de este pueblo corta, lo forjé yo. Si se rompe, también lo arreglo... cobrando.",
                first = L("¡Eh, cuidado con las chispas! ...Un caballero. Hace años que no entraba uno con la armadura entera. Soy Bruna, la herrera."),
                again = L("¿Otra vez tú? Bien. Que el yunque no se enfría solo.", "Dime qué necesitas y no me hagas perder el ritmo.", "Huele a hierro caliente, ¿eh? Es el mejor olor del mundo."),
                friend = L("¡Mi caballero favorito! Siéntate si quieres, que te enseño la última hoja que he templado.", "Contigo da gusto trabajar. Siempre traes buen metal."),
                night = L("La forja no duerme, pero yo sí debería... ¿Qué quieres a estas horas?"),
                barks = L("¡Clang! ¡Clang!", "Este acero aún está blando...", "¡Más carbón!"),
                busy = L("Ahora no, que se me tuerce el filo."),
                topics = new[] { ("¿Cómo mejoro mi arma?", "Tráeme mineral. Hierro y cuero para empezar; plata y cristal de escarcha para lo bueno; obsidiana y un núcleo ígneo para lo legendario. Hasta +5. Más no, que se agrieta."),
                                 ("¿Se desgastan las armas?", "Todo se desgasta. Cada golpe mella el filo y cada tajo que recibes abolla la armadura. Rota pega la mitad. Tráemela antes de que pase.") },
                choice = new NpcChoice
                {
                    ask = "¿Qué te parece esta espada que acabo de forjar? Sé sincero.",
                    answers = new[] { "Es magnífica.", "He visto mejores en la Ciudadela." },
                    replies = new[] { "¡Ja! Lo sabía. Tienes buen ojo, caballero.", "¿Mejores? ¿Del estirado de Tordo? Hmph. Ya veremos quién forja mejor." },
                    affinity = new[] { 2, -1 }, notes = new[] { "bruna_praised", "bruna_insulted" },
                    recall = new[] { "Todavía me acuerdo de lo que dijiste de mi espada. Me alegró la semana.", "Ah, el que ha visto mejores espadas. Pasa, pasa..." },
                },
                quest = new NpcQuest
                {
                    title = "HIERRO PARA BRUNA", mat = "hierro", n = 4,
                    offer = "Me he quedado sin hierro y los carros de los Picos no llegan por culpa de los orcos. ¿Me traes 4 menas de hierro? Están en las rocas con vetas de los Picos y las Arenas.",
                    accepted = "Te debo una. Las rocas con vetas naranjas, ¿eh? Golpéalas con E.",
                    progress = "¿Y mi hierro? Necesito 4 menas.",
                    done = "¡Hierro del bueno! Toma: dos kits de reparación y desde hoy te cobro menos. Palabra de Bruna.",
                    reward = "2 KITS DE REPARACIÓN Y DESCUENTO EN LA HERRERÍA", give = s => { s.Give("kit_reparar", 2); s.Set("discount_bruna"); },
                },
                likes = "hierro", likesThanks = "¿Hierro? ¿Para mí? Esto es mejor que las flores, caballero.",
                work = L("i:herreria:4.7,4.6:>", "i:herreria:4.7,4.6:>", "i:herreria:3,3.6:^"),
                social = L("a:well:1,-1", "a:fire:2,1"),
                sleep = "i:herreria:14,5",
            },
            new NpcDef
            {
                id = "tomas", name = "Tomás", job = "Molinero", sprite = "NpcTomas", town = "City_Valle", workAnim = "PickUp",
                personality = "Alegre y charlatán, se ríe de todo, incluso del peligro.",
                bio = "¡Tomás, el del molino! Muelo el trigo de medio valle. Bueno, de todo el valle. Bueno, del único molino que queda.",
                first = L("¡Hola, hola! ¿Un caballero de verdad? ¡Qué alegría! Yo soy Tomás, el molinero. ¿Quieres harina? Es broma, no tengo bolsas."),
                again = L("¡Mi amigo el caballero! ¿Sabes el chiste del orco y la rueda del molino? ...Yo tampoco, se me olvidó.", "¡El viento sopla bien hoy! Buen día para moler.", "¿Qué tal la aventura? ¿Muchos monstruos? ¡Cuéntamelo todo!"),
                friend = L("¡Ya estás aquí! Mi mujer dice que hablo demasiado de ti. Yo digo que no hablo bastante."),
                night = L("Shh... de noche se oyen cosas en el campo. No me río tanto cuando se pone el sol."),
                barks = L("¡Buen día!", "¡Gira, gira, molinito!", "¡Ja, ja!"),
                topics = new[] { ("¿Qué pasa en el valle?", "Los orcos bajan del norte y de noche salen espectros. Pero aquí, con la guardia de Ramiro y la herrería de Bruna, aguantamos. ¡Y con harina! La harina lo cura todo."),
                                 ("¿Dónde encuentro hierbas?", "Las hierbas curativas crecen en los prados del valle y en los bosques. Elvira, la herbolaria, sabe mucho más que yo. Vive en la cabaña del oeste.") },
                choice = new NpcChoice
                {
                    ask = "Oye, ¿tú crees que los molinos le dan miedo a los orcos?",
                    answers = new[] { "Seguro que sí, son enormes.", "Lo dudo mucho." },
                    replies = new[] { "¡Lo sabía! Voy a ponerle cara de monstruo a las aspas.", "Ya... Bueno, por si acaso le pondré una cara de monstruo igualmente." },
                    affinity = new[] { 1, 0 }, notes = new[] { "tomas_mills_scary", "tomas_doubt" },
                    recall = new[] { "¡Le pinté la cara al molino! Como tú dijiste. Ningún orco se ha acercado. Ciencia.", "Ya sé que no crees en mis molinos asusta-orcos. ¡Pero funcionan!" },
                },
                quest = new NpcQuest
                {
                    title = "RATAS EN EL MOLINO", mat = "seta_roja", n = 3,
                    offer = "Tengo ratas del tamaño de gatos en el granero. Elvira dice que con setas rojas se hace un cebo que las ahuyenta. ¿Me traes 3? Crecen en el Bosque del Oeste.",
                    accepted = "¡Gracias! Mientras, yo les cantaré para distraerlas.",
                    progress = "Las ratas siguen bailando en mi granero. ¿Las setas rojas?",
                    done = "¡Setas rojas! Ahora verán esas ratas. Toma, me sobraron estas bombas del abuelo... y unas monedas.",
                    reward = "2 BOMBAS Y 30 MONEDAS", give = s => { s.Give("bomba", 2); s.coins += 30; },
                },
                work = L("a:mill#1:0,2:^", "a:mill#1:-3,3", "a:mill#2:0,2:^"),
                social = L("a:well:-1,1", "a:fire:1,2"),
                sleep = "i:casa#1:15,7.8",
            },
            new NpcDef
            {
                id = "elvira", name = "Elvira", job = "Herbolaria", sprite = "NpcElvira", town = "City_Valle", service = "herbs", workAnim = "PickUp",
                personality = "Tranquila, sabia, habla despacio y en metáforas de plantas.",
                bio = "Me llamo Elvira. Las plantas me lo enseñaron todo: qué cura, qué mata y qué hace las dos cosas según la dosis.",
                first = L("Te he visto llegar. Traes heridas que no ves. Soy Elvira; curo lo que se puede curar."),
                again = L("La raíz amarga, la flor de luna... todo tiene su hora. ¿Qué buscas hoy?", "Siéntate un momento. Hasta el roble descansa en invierno.", "Ya no queda poción que se compre en el mercado. Ahora la medicina se hace con las manos."),
                friend = L("Pasa, mi niño. Tengo infusión caliente y la flor de luna está abierta."),
                night = L("De noche se abre la flor de luna. Busca su brillo rosado en los bosques y en la orilla del lago."),
                barks = L("Hierba de prado... aquí.", "Mmm, aún no está madura.", "El rocío ayuda."),
                topics = new[] { ("¿Cómo me curo?", "Con una venda: tela y una hierba curativa. Con un ungüento: dos hierbas y aceite. La medicina de verdad lleva flor de luna, raíz amarga y un frasco. Fabrícalas en la mesa de cualquier campamento."),
                                 ("¿Y el aguante?", "Dos setas azules en un frasco: un tónico que te devuelve el aliento. Y el guiso del cazador, con carne, hierba y seta azul, te hace aguantar más tiempo.") },
                choice = new NpcChoice
                {
                    ask = "Dime, caballero: ¿matas por necesidad o por gusto?",
                    answers = new[] { "Solo por necesidad.", "Me gusta la batalla." },
                    replies = new[] { "Entonces el bosque te protegerá.", "Cuidado. La planta que crece demasiado rápido se pudre por dentro." },
                    affinity = new[] { 2, -1 }, notes = new[] { "elvira_need", "elvira_glory" },
                    recall = new[] { "Sigues matando solo por necesidad, ¿verdad? Lo veo en tus ojos.", "¿Sigues disfrutando de la batalla? Mira tus manos." },
                },
                quest = new NpcQuest
                {
                    title = "HIERBAS PARA LOS HERIDOS", mat = "hierba", n = 5,
                    offer = "Hay heridos en el pueblo y se me acaban las hierbas. ¿Me traes 5 hierbas curativas? Crecen en los prados; agáchate con E junto a la mata.",
                    accepted = "Gracias. Fíjate en las matas verdes de hojas redondas.",
                    progress = "Aún me faltan hierbas. Cinco, recuerda.",
                    done = "Huelen a lluvia. Perfectas. Toma dos medicinas y dos flores de luna que guardaba. Que te protejan.",
                    reward = "2 MEDICINAS Y 2 FLORES DE LUNA", give = s => { s.Give("medicina", 2); s.Give("flor_luna", 2); },
                },
                likes = "flor_luna", likesThanks = "Una flor de luna... para mí. Hacía años que nadie me regalaba flores.",
                work = L("a:mill#1:4,6", "a:house:cabana#1:-3,2", "a:house:cabana#1:3,3"),
                social = L("a:shop#1:0,2"),
                sleep = "i:cabana#1:10.5,2.8",
            },
            new NpcDef
            {
                id = "ramiro", name = "Ramiro", job = "Guardia del pueblo", sprite = "NpcRamiro", town = "City_Valle", service = "", nightOwl = true,
                personality = "Serio, disciplinado, desconfiado con los forasteros, leal hasta la muerte.",
                bio = "Ramiro, guardia del valle. Solo quedo yo desde que se llevaron a la milicia al norte. Así que vigilo yo. Siempre.",
                first = L("Alto. ...Bien, no eres un orco. Soy Ramiro, la guardia. Si causas problemas, me causas problemas a mí."),
                again = L("Sin novedad. Por ahora.", "Mantén la espada limpia y los ojos abiertos.", "Patrulla, patrulla... alguien tiene que hacerlo."),
                friend = L("Me alegra verte. De verdad. Con gente como tú, el valle duerme mejor."),
                night = L("De noche patrullo junto al fuego. Los espectros odian la luz. Quédate cerca si puedes."),
                barks = L("Todo en orden.", "Hmm.", "Atento al norte."),
                topics = new[] { ("¿Cómo lucho contra los orcos?", "No te lances a lo loco. Para su golpe con el escudo justo a tiempo (F) y quedarán aturdidos: ahí les clavas la espada a fondo. Y vigila tu aliento: sin aguante no hay bloqueo."),
                                 ("¿Algo raro últimamente?", "En las ruinas del Bosque Corrupto se ven luces violetas. Dicen que un hechicero levanta a los muertos. El Invocador, lo llaman. No vayas sin medicinas.") },
                choice = new NpcChoice
                {
                    ask = "¿Te quedarías a defender el pueblo si los orcos atacan esta noche?",
                    answers = new[] { "Por supuesto.", "Tengo cosas más importantes." },
                    replies = new[] { "...Gracias. No lo olvidaré.", "Ya. Los caballeros siempre tienen cosas más importantes." },
                    affinity = new[] { 2, -2 }, notes = new[] { "ramiro_stays", "ramiro_leaves" },
                    recall = new[] { "Dijiste que te quedarías a defendernos. Eso vale más que una espada.", "¿Hoy también tienes cosas más importantes?" },
                },
                quest = new NpcQuest
                {
                    title = "LIMPIAR EL CAMINO", counter = s => s.orcKills, n = 8,
                    offer = "Los orcos atacan a los carros del camino. Derrota a 8 orcos y el valle respirará. Te pagaré de mi bolsillo.",
                    accepted = "Bien. Cuéntalos. Yo también los contaré.",
                    progress = "Aún quedan orcos en el camino.",
                    done = "Ocho orcos. Se nota: hoy han pasado tres carros. Toma, lo prometido.",
                    reward = "60 MONEDAS Y 2 CUEROS", give = s => { s.coins += 60; s.Give("cuero", 2); },
                },
                work = L("a:well:-6,0:v", "a:well:7,2", "a:fire:0,5", "a:shop#2:3,-3"),
                social = L("a:fire:-2,1:>"),
                sleep = "a:fire:2,0:<",
            },
            new NpcDef
            {
                id = "lucia", name = "Lucía", job = "Comerciante", sprite = "NpcLucia", town = "City_Valle", service = "shop", workAnim = "Interact",
                personality = "Habladora, astuta para el negocio, cotilla, en el fondo generosa.",
                bio = "Lucía, la del puesto. Vendo de todo menos pociones: desde que el alquimista se fue al sur, nadie las prepara. Telas, aceite, frascos... lo que necesites para hacerte las tuyas.",
                first = L("¡Un cliente nuevo! ¡Y con armadura! Soy Lucía. Aquí se vende y se compra, y se cuentan cosas. Lo último es gratis."),
                again = L("¿Qué te pongo? Tengo tela recién llegada.", "¿Te has enterado? Dicen que Inés, la de la Ciudadela, tiene un pretendiente. ¡Pero no digas que te lo dije yo!", "Si traes cosas raras, te las compro. Bueno, según lo raras."),
                friend = L("¡Mi mejor cliente! Para ti siempre hay algo guardado debajo del mostrador."),
                night = L("Ya he recogido el puesto. Martín está con la caza. ¿Qué quieres?"),
                barks = L("¡Tela, aceite, frascos!", "¡Barato, barato!", "¡Pasen y vean!"),
                topics = new[] { ("¿Por qué no vendes pociones?", "Porque no hay quien las haga. Ahora cada uno se cura con lo que fabrica: vendas, ungüentos, medicinas. Yo te vendo la tela, el aceite y los frascos. Negocio redondo."),
                                 ("¿Algún cotilleo?", "Bruna y Tordo, el herrero de la Ciudadela, se odian desde que eran aprendices. Y Tomás le ha pintado una cara a su molino. Y mi Martín ronca. Eso no lo sabe nadie. Ahora sí.") },
                choice = new NpcChoice
                {
                    ask = "Entre tú y yo: ¿regateas o pagas lo que te piden?",
                    answers = new[] { "Pago lo justo.", "Siempre regateo." },
                    replies = new[] { "¡Ay, qué gusto da tratar con gente honrada!", "¡Ja! Me caes bien. Pero conmigo no funciona." },
                    affinity = new[] { 1, 1 }, notes = new[] { "lucia_fair", "lucia_haggle" },
                    recall = new[] { "Mi cliente honrado. Pasa, pasa.", "¿Vienes a regatear otra vez? Te veo venir." },
                },
                work = L("a:shop#1:0,1:^", "a:shop#1:0,1:^", "a:shop#1:1,1:^"),
                social = L("a:well:2,0", "a:fire:-2,-1"),
                sleep = "i:casa#2:14.5,7.8",
            },
            new NpcDef
            {
                id = "nico", name = "Nico", job = "Chico de los recados", sprite = "NpcNico", town = "City_Valle",
                personality = "Curioso, impaciente, sueña con ser caballero.",
                bio = "¡Soy Nico! Llevo recados a todo el pueblo. Algún día seré caballero como tú. Bueno, mejor que tú. Sin ofender.",
                first = L("¡¿Eres un caballero de verdad?! ¿Has matado un dragón? ¿Y un orco? ¿Cuántos? ¡Soy Nico!"),
                again = L("¡Cuéntame otra batalla!", "¿Me dejas tocar la espada? ...Vale, vale.", "Hoy he llevado tres cartas y un queso. Ser caballero debe de ser más fácil."),
                friend = L("¡Mi héroe! Le he contado a todo el mundo que somos amigos. ¿Somos amigos, verdad?"),
                night = L("Mi madre dice que vuelva antes de que salgan los espectros... ¡pero contigo no me dan miedo!"),
                barks = L("¡Corre, corre!", "¡Recado urgente!", "¡Hola, caballero!"),
                topics = new[] { ("¿Qué sabes del pueblo?", "¡Todo! Bruna es la más fuerte, Tomás el más gracioso, Elvira la más lista y Ramiro nunca duerme. ¡Nunca! Lo he comprobado."),
                                 ("¿Quieres ser caballero?", "¡Sí! Ya practico la voltereta: espacio para rodar, sin moverte para saltar atrás. ¡Y el escudo! Si lo levantas justo cuando te pegan, ¡pum!, parry.") },
                choice = new NpcChoice
                {
                    ask = "¿Me enseñarás a luchar algún día?",
                    answers = new[] { "Te lo prometo.", "Eres demasiado pequeño." },
                    replies = new[] { "¡¡SÍ!! ¡Voy a decírselo a todos!", "Hmph. Ya creceré. Y entonces verás." },
                    affinity = new[] { 2, -1 }, notes = new[] { "nico_promise", "nico_small" },
                    recall = new[] { "¡No te olvides de que me prometiste enseñarme a luchar!", "Hoy he crecido un poco. ¿A que sí?" },
                },
                quest = new NpcQuest
                {
                    title = "UNA HISTORIA DE VERDAD", counter = s => s.eliteKills + s.champions, n = 1,
                    offer = "¡Derrota a un enemigo PODEROSO, de esos que brillan! Y luego me lo cuentas. Por favor, por favor.",
                    accepted = "¡Bieeen! ¡Los poderosos brillan dorado, ten cuidado!",
                    progress = "¿Ya has derrotado a uno que brilla? ¿No? Vale, espero.",
                    done = "¡¿DE VERDAD?! ¡Qué pasada! Toma, mi tesoro: flechas de plata que encontré en el río. Para el mejor caballero del mundo.",
                    reward = "5 FLECHAS DE PLATA", give = s => s.Give("flecha_plata", 5),
                },
                work = L("a:well:3,3", "a:house:casa#1:0,2", "a:house:cabana#1:2,1", "a:shop#2:0,3", "a:mill#2:-2,2"),
                social = L("a:fire:-1,1"),
                sleep = "i:cabana#2:10.5,2.8",
            },
            new NpcDef
            {
                id = "martin", name = "Martín", job = "Cazador", sprite = "NpcMartin", town = "City_Valle", workAnim = "PickUp",
                personality = "Callado, práctico, generoso con la comida.",
                bio = "Martín. Cazo, curto pieles y llevo carne al pueblo. Lucía es mi mujer. Ella habla por los dos.",
                first = L("...Hola. Martín. Cazador. Si traes carne, hago guiso."),
                again = L("Buena caza hoy.", "El cuero de orco es duro, pero sirve.", "...¿Hambre?"),
                friend = L("Siéntate. Hay guiso. Siempre hay guiso para ti."),
                night = L("La caza de noche es para los espectros, no para mí. Mañana."),
                barks = L("...", "Huellas frescas.", "Hmm."),
                topics = new[] { ("¿Qué cazas?", "Lo que haya. Los orcos sueltan carne y cuero, aunque no me guste decirlo. Con cuero, Bruna mejora las armaduras."),
                                 ("¿Me enseñas a cocinar?", "Carne, una hierba y una seta azul en la mesa del campamento: guiso del cazador. Cura un poco y aguantas más corriendo y peleando.") },
                choice = new NpcChoice
                {
                    ask = "¿Prefieres cazar solo o acompañado?",
                    answers = new[] { "Solo.", "Acompañado." },
                    replies = new[] { "...Sí. El bosque habla más bajo cuando vas solo.", "Lucía dice lo mismo. Será verdad." },
                    affinity = new[] { 1, 1 }, notes = new[] { "martin_alone", "martin_company" },
                    recall = new[] { "Tú también cazas solo. Nos entendemos.", "Si quieres compañía de caza, avisa." },
                },
                quest = new NpcQuest
                {
                    title = "CARNE PARA EL INVIERNO", mat = "carne", n = 3,
                    offer = "El invierno viene. Necesito 3 piezas de carne para curar y guardar. Los orcos la llevan encima.",
                    accepted = "Bien.",
                    progress = "Faltan piezas.",
                    done = "Buena carne. Toma: dos guisos hechos y dos cueros curtidos.",
                    reward = "2 GUISOS Y 2 CUEROS", give = s => { s.Give("guiso", 2); s.Give("cuero", 2); },
                },
                work = L("a:house:casa#2:4,1", "a:mill#2:3,0", "a:house:cabana#2:4,-2"),
                social = L("a:fire:1,-1:^"),
                sleep = "i:casa#2:15.6,7.8",
            },

            // ======================================================== LA CIUDADELA DEL REY
            new NpcDef
            {
                id = "tordo", name = "Maese Tordo", job = "Herrero real", sprite = "NpcTordo", town = "City_Ciudadela", service = "smith", workAnim = "Attack",
                personality = "Perfeccionista, altivo, habla de sí mismo en tercera persona cuando se enfada.",
                bio = "Maese Tordo, herrero de la Corona. Mis hojas defienden al Rey. Las de Bruna... cortan pan, supongo.",
                first = L("Un caballero errante. Mm. Esa armadura está mal remachada. Soy Maese Tordo, herrero real. Podemos arreglar eso."),
                again = L("La perfección no se apresura. ¿Qué deseas?", "Acero de la Ciudadela: el mejor del reino. Lo digo yo, que lo forjo.", "No toques el yunque. Es más viejo que tu abuelo."),
                friend = L("Ah, mi cliente predilecto. Para ti, Tordo hace una excepción... y te escucha."),
                night = L("Tordo trabaja a la luz de la forja. Las mejores hojas nacen de noche."),
                barks = L("¡Clang!", "Imperfecto. Otra vez.", "Más temple..."),
                topics = new[] { ("¿Qué vendes?", "Hojas para gente seria: espadones, alabardas, katanas. Y armaduras de placas. Nada de juguetes de pueblo."),
                                 ("¿Conoces a Bruna?", "...Fuimos aprendices del mismo maestro. Ella siempre golpeaba demasiado fuerte. Yo, demasiado bien. No hablemos de eso.") },
                choice = new NpcChoice
                {
                    ask = "Dime: ¿quién forja mejor, Bruna o Tordo?",
                    answers = new[] { "Maese Tordo, sin duda.", "Bruna." },
                    replies = new[] { "Por supuesto. Tienes criterio, caballero.", "¡¿Bruna?! Tordo... Tordo necesita un momento." },
                    affinity = new[] { 2, -2 }, notes = new[] { "tordo_best", "tordo_bruna" },
                    recall = new[] { "Ah, el caballero con criterio. Pasa.", "El admirador de Bruna. Mm. Al menos pagas." },
                },
                quest = new NpcQuest
                {
                    title = "PLATA PARA LA CORONA", mat = "plata", n = 2,
                    offer = "La guardia necesita filos de plata contra los caballeros caídos. Tráeme 2 menas de plata de los Picos Nevados. Tordo te recompensará.",
                    accepted = "No me traigas plata sucia.",
                    progress = "¿La plata? Dos menas.",
                    done = "Plata pura. Excelente. Dos aceites benditos, para que tu arma castigue a los demonios, y monedas de la Corona.",
                    reward = "2 ACEITES BENDITOS Y 50 MONEDAS", give = s => { s.Give("aceite_sagrado", 2); s.coins += 50; },
                },
                work = L("i:herreria:4.7,4.6:>", "i:herreria:4.7,4.6:>", "i:herreria:3,3.6:^"),
                social = L("a:shop#2:2,1"),
                sleep = "i:herreria:14,5",
            },
            new NpcDef
            {
                id = "aurelio", name = "Capitán Aurelio", job = "Capitán de la guardia real", sprite = "HeroCrusader", town = "City_Ciudadela", nightOwl = false,
                personality = "Noble, cansado, carga con la culpa de los caballeros que cayeron.",
                bio = "Aurelio, capitán de la guardia del Rey. Lo que queda de ella. La mitad de mis hombres patrulla de noche... sin estar vivos.",
                first = L("Caballero. Se agradece una espada más. Soy el capitán Aurelio. Bienvenido a la Ciudadela, o a lo que queda."),
                again = L("El Rey no sale de la torre. Alguien debe mandar aquí abajo.", "¿Noticias del frente?", "Descansa en el cuartel si lo necesitas."),
                friend = L("Ojalá tuviera diez como tú. Con diez, recuperábamos el reino en un mes."),
                night = L("De noche patrullan los caballeros caídos. Eran mis hombres. No dudes al golpearlos: ya no son ellos."),
                barks = L("¡Firmes!", "Atentos a la muralla.", "Por el Rey."),
                topics = new[] { ("¿Qué son los caballeros caídos?", "Guardias muertos que la niebla levantó. Aún bloquean como les enseñé y esquivan tus golpes. Rodéalos, y si los paras con el escudo en el momento justo, quedan abiertos."),
                                 ("¿Y el Invocador?", "Un hechicero en las ruinas del Bosque Corrupto. Mientras sus siervos estén en pie, nada le hiere. Mátalos primero. Y luego a él, rápido, antes de que los levante otra vez.") },
                choice = new NpcChoice
                {
                    ask = "Si cayeras en combate, ¿querrías que te enterrasen en la Ciudadela?",
                    answers = new[] { "Sería un honor.", "No pienso caer." },
                    replies = new[] { "Entonces ya eres uno de los nuestros.", "Eso decían todos. Que tengas razón." },
                    affinity = new[] { 2, 0 }, notes = new[] { "aurelio_honor", "aurelio_proud" },
                    recall = new[] { "Uno de los nuestros. Bienvenido de nuevo.", "Sigues en pie, como prometiste. Bien." },
                },
                quest = new NpcQuest
                {
                    title = "DESCANSO PARA LOS CAÍDOS", counter = s => s.demonKills, n = 6,
                    offer = "Dale descanso a mis hombres. Derrota a 6 demonios o caballeros caídos. Te daré la espada que me dio el Rey.",
                    accepted = "Que los dioses guíen tu filo.",
                    progress = "Aún vagan almas por la Ciudadela.",
                    done = "Lo has hecho. Toma la espada del caballero. Úsala mejor que yo.",
                    reward = "ESPADA DEL CABALLERO Y 40 MONEDAS", give = s => { if (!s.AddItem("sword_knight")) s.coins += 60; s.coins += 40; },
                },
                work = L("i:cuartel:9.5,3.6:^", "a:fire:-3,-4", "a:fire:3,-4", "i:cuartel:16,7"),
                social = L("a:well:-2,1"),
                sleep = "i:cuartel:2,2.3",
            },
            new NpcDef
            {
                id = "ilmaro", name = "Ilmaro", job = "Sabio de la biblioteca", sprite = "NpcIlmaro", town = "City_Ciudadela", workAnim = "Interact",
                personality = "Distraído, erudito, habla con citas de libros que nadie más ha leído.",
                bio = "Ilmaro, guardián de la biblioteca. Trescientos años de crónicas, y sigo sin saber dónde dejé las gafas.",
                first = L("¿Eh? ¡Ah! Un visitante. «El caballero llega cuando la tinta se seca», decía el Códice Gris. Soy Ilmaro."),
                again = L("¿Sabías que la ceniza demoníaca no arde? Simplemente... recuerda haber ardido.", "Silencio, por favor. Los libros duermen.", "Pregunta, pregunta. Para eso estoy."),
                friend = L("¡Mi lector favorito! He encontrado un pasaje sobre el Monte Ceniza que te interesará."),
                night = L("La flor de luna solo se abre bajo la luna. Lo dice el Herbario de Vela, página trescientos doce."),
                barks = L("Mmm... interesante.", "¿Dónde puse ese tomo?", "Fascinante."),
                topics = new[] { ("¿Qué es la maldición del Invocador?", "Los textos dicen que quien derrota a un invocador hereda su don: alzar a los caídos como siervos. Cuatro a lo sumo; el alma no aguanta más. Y el que muere al servirte... no vuelve."),
                                 ("¿Qué hay en el Monte Ceniza?", "El Señor Demonio duerme bajo el volcán. Un sello lo contiene, sostenido por dos guardianes: Gorgrak el Caudillo y la Madre de Sangre. Si caen ambos, el sello cae.") },
                choice = new NpcChoice
                {
                    ask = "Una pregunta para mi tratado: ¿el conocimiento es poder o es peligro?",
                    answers = new[] { "Es poder.", "Es peligro." },
                    replies = new[] { "Bacón Cuarto estaría de acuerdo. Lo anoto.", "Ah, el Códice Gris también lo dice. Prudente." },
                    affinity = new[] { 1, 1 }, notes = new[] { "ilmaro_power", "ilmaro_danger" },
                    recall = new[] { "Mi tratado ya tiene tu respuesta: poder. Muy citada.", "He escrito tu nombre junto a «peligro». Es un honor, créeme." },
                },
                quest = new NpcQuest
                {
                    title = "LA FLOR DE LA LUNA", mat = "flor_luna", n = 3,
                    offer = "Para mi herbario necesito 3 flores de luna. Solo se abren de noche, en los bosques y junto al lago. Brillan rosadas.",
                    accepted = "Sal de noche. Lleva antorcha... y espada.",
                    progress = "Las flores, las flores. Tres.",
                    done = "¡Maravillosas! Toma este elixir que destilé hace un siglo. Debería seguir bien. Probablemente.",
                    reward = "ELIXIR DEL SABIO Y 30 MONEDAS", give = s => { s.Give("elixir", 1); s.coins += 30; },
                },
                likes = "cristal", likesThanks = "¡Un cristal de escarcha! Lo estudiaré durante años.",
                work = L("i:biblioteca:3.7,7.6:<", "i:biblioteca:4,3.3:^", "i:biblioteca:7,6.2:^"),
                social = L("a:house:biblioteca:0,2"),
                sleep = "i:biblioteca:7,6.2",
            },
            new NpcDef
            {
                id = "clara", name = "Hermana Clara", job = "Sacerdotisa de la capilla", sprite = "NpcClara", town = "City_Ciudadela", service = "healer", workAnim = "Interact",
                personality = "Dulce, firme, no tiene miedo de nada salvo de que alguien se quede sin ayuda.",
                bio = "Soy la hermana Clara. Cuido de la capilla y de quien entre por esa puerta, sea quien sea.",
                first = L("Bienvenido, hijo. Estás cansado; se te nota en los hombros. Soy la hermana Clara."),
                again = L("Que la luz te acompañe.", "Reza en el altar si lo necesitas. O siéntate, sin más.", "¿Te has curado bien esas heridas?"),
                friend = L("Siempre me alegra verte volver sano. Rezo por ti cada noche."),
                night = L("La capilla nunca cierra. Pasa."),
                barks = L("Luz y paz.", "Bendito sea.", "..."),
                topics = new[] { ("¿Puedes curarme?", "Puedo bendecirte: tu cuerpo sanará. Pero lo que llevas en la bolsa lo pones tú: vendas, ungüentos, medicina. La fe no sustituye a la venda."),
                                 ("¿Qué es la maldición del Invocador?", "Una herida del alma. Dicen que permite mandar a los muertos. Si alguna vez la llevas, úsala con compasión. Ellos también fueron alguien.") },
                choice = new NpcChoice
                {
                    ask = "¿Crees que hasta un demonio merece piedad?",
                    answers = new[] { "Sí, todos la merecen.", "No. Ninguno." },
                    replies = new[] { "Tienes un corazón más grande que tu espada.", "Lo entiendo. Has visto demasiado." },
                    affinity = new[] { 2, 0 }, notes = new[] { "clara_mercy", "clara_none" },
                    recall = new[] { "El caballero que cree en la piedad. Bienvenido.", "Rezo para que algún día encuentres piedad, aunque sea para ti." },
                },
                quest = new NpcQuest
                {
                    title = "VENDAS PARA LOS PEREGRINOS", mat = "venda", n = 3,
                    offer = "Llegan peregrinos heridos del camino. ¿Me traerías 3 vendas? Se hacen con tela y una hierba en la mesa de un campamento.",
                    accepted = "Que la luz te guíe.",
                    progress = "Los peregrinos aún esperan las vendas.",
                    done = "Gracias. Toma, la capilla guarda esto para quien da sin pedir: medicina y un elixir.",
                    reward = "2 MEDICINAS Y 1 ELIXIR", give = s => { s.Give("medicina", 2); s.Give("elixir", 1); },
                },
                work = L("i:capilla:7.5,4.5:^", "i:capilla:5.6,6.4", "i:capilla:9.6,8.4"),
                social = L("a:well:1,1"),
                sleep = "i:capilla:3.5,9.2",
            },
            new NpcDef
            {
                id = "galen", name = "Sir Galen", job = "Centinela de la muralla", sprite = "NpcGalen", town = "City_Ciudadela", nightOwl = true,
                personality = "Fanfarrón, valiente de boquilla, buen compañero.",
                bio = "¡Sir Galen, terror de los orcos, azote de los espectros! Bueno, centinela de la muralla sur. Pero con mucho estilo.",
                first = L("¡Alto, quién va! ...Ah, un colega. Sir Galen, a tu servicio. Seguramente hayas oído hablar de mí."),
                again = L("¿Te he contado cuando derroté a doce orcos con una sola mano? Eran pequeños, pero doce.", "Nada pasa por esta muralla sin que Galen lo vea.", "¡Ah, mi rival en gloria!"),
                friend = L("¡Hermano de armas! Esta noche cenamos juntos y te cuento lo de los doce orcos. Otra vez."),
                night = L("De noche la muralla es mía. Y de los espectros. Pero sobre todo mía."),
                barks = L("¡Nada que ver aquí!", "¡Por el Rey!", "*bostezo*"),
                topics = new[] { ("¿Algún consejo de combate?", "¡Corre! Pero no siempre: correr gasta aliento, y sin aliento no puedes ni rodar. Guarda un poco para la voltereta. Eso me lo enseñó... yo mismo."),
                                 ("¿Qué hay al sur?", "El Pantano Carmesí y la torre oscura. La Madre de Sangre. No he ido. No por miedo. Por... estrategia.") },
                choice = new NpcChoice
                {
                    ask = "Sé sincero: ¿te parezco el caballero más valiente de la Ciudadela?",
                    answers = new[] { "Sin duda, Sir Galen.", "Pareces más hablador que valiente." },
                    replies = new[] { "¡Lo sabía! Lo pondré en mi escudo.", "...Auch. Bueno. Algo de razón tienes. No se lo digas a nadie." },
                    affinity = new[] { 1, 1 }, notes = new[] { "galen_brave", "galen_talker" },
                    recall = new[] { "¡Mi admirador número uno!", "El único que me dice la verdad. Te lo agradezco, aunque duela." },
                },
                quest = new NpcQuest
                {
                    title = "LA RONDA DE GALEN", counter = s => s.kills, n = 12,
                    offer = "Te propongo un reto: a ver quién derrota más enemigos. Tú, 12. Yo... yo ya los he derrotado, claro. ¿Aceptas?",
                    accepted = "¡Ja! Empieza a contar.",
                    progress = "¿Ya vas por doce? Yo voy por trescientos.",
                    done = "¿Doce? Vale, vale, has ganado. Toma, el premio: flechas y un aceite ígneo. Mi secreto.",
                    reward = "20 FLECHAS Y 1 ACEITE ÍGNEO", give = s => { s.arrows += 20; s.Give("aceite_fuego", 1); },
                },
                work = L("a:fire:-8,6", "a:fire:8,6", "a:fire:0,12", "a:fire:0,-10"),
                social = L("a:shop#1:0,2"),
                sleep = "a:fire:-3,14:v",
            },
            new NpcDef
            {
                id = "ines", name = "Doña Inés", job = "Dama de la corte", sprite = "NpcInes", town = "City_Ciudadela",
                personality = "Elegante, aburrida, sarcástica, adora las joyas y los rumores.",
                bio = "Inés de Valdemora. Dama de la corte de un rey que ya no recibe a nadie. Así que paseo. Mucho.",
                first = L("Vaya, vaya. Barro en las botas, sangre en la capa... qué rústico. Inés de Valdemora. Encantada, supongo."),
                again = L("La corte está tan aburrida que hasta tú resultas interesante.", "¿Has visto el estado de esta plaza? Una vergüenza.", "Dicen que el pueblo tiene una herrera muy fuerte. Qué vulgaridad. Cuéntame más."),
                friend = L("¡Querido! Por fin alguien con quien hablar. Siéntate, cuéntame tus horrores."),
                night = L("No son horas, caballero. Ni para una dama ni para un héroe."),
                barks = L("Qué aburrimiento...", "¡Uf!", "Hmm, interesante."),
                topics = new[] { ("¿Qué pasa en la corte?", "Nada. El Rey se encierra en la torre desde que despertó el Señor Demonio. Los nobles fingimos que todo va bien. Se nos da de maravilla."),
                                 ("¿Tienes pretendiente?", "¿Quién te ha contado eso? ¿Lucía? Esa mujer sabría el color de la ropa interior del Rey. ...No, no tengo. Todavía.") },
                choice = new NpcChoice
                {
                    ask = "Dime, ¿qué te parece mi vestido?",
                    answers = new[] { "Precioso, digno de una reina.", "Poco práctico para la guerra." },
                    replies = new[] { "Por fin alguien con gusto en este reino.", "¿Para la guerra? Querido, mi guerra es la corte. Y la gano." },
                    affinity = new[] { 2, 0 }, notes = new[] { "ines_flattered", "ines_practical" },
                    recall = new[] { "Mi caballero galante. Hoy llevo otro vestido, por si lo preguntas.", "Hoy llevo algo más práctico. Mentira. Pero gracias por la sinceridad." },
                },
                quest = new NpcQuest
                {
                    title = "UNA JOYA NEGRA", mat = "obsidiana", n = 1,
                    offer = "Quiero un broche de obsidiana del Monte Ceniza. Nadie en la corte tendrá algo así. Tráeme una piedra y te pagaré generosamente.",
                    accepted = "Sin arañazos, por favor.",
                    progress = "¿Mi obsidiana? La corte no espera.",
                    done = "¡Perfecta! Negra como el humor del Rey. Toma, ciento cincuenta monedas. No las gastes en barro.",
                    reward = "150 MONEDAS", give = s => s.coins += 150,
                },
                likes = "flor_luna", likesThanks = "¿Una flor de luna? ...Qué detalle tan inesperado. Gracias.",
                work = L("a:well:-5,-6", "a:well:6,-6", "a:house:capilla:-3,2"),
                social = L("a:shop#2:-1,2"),
                sleep = "i:casa#1:15,7.8",
            },

            // ======================================================== LA COSTA DEL PUERTO
            new NpcDef
            {
                id = "marta", name = "Marta", job = "Posadera del Jabalí", sprite = "NpcMarta", town = "City_Puerto", service = "inn", workAnim = "Interact",
                personality = "Cálida, maternal, cotilla, no soporta las mesas sucias.",
                bio = "Marta, la del Jabalí. Mi abuela abrió esta posada y aquí sigo, sirviendo cerveza a marineros y héroes por igual.",
                first = L("¡Pasa, pasa, que entra el frío! Soy Marta. En el Jabalí hay sopa caliente, cama blanda y nada de peleas."),
                again = L("¿Lo de siempre?", "¡Limpia esas botas antes de pisar mi suelo!", "Hoy tengo sopa de pescado. Bartolo ha tenido suerte."),
                friend = L("¡Mi niño! Siéntate, que te pongo lo mejor de la cocina, invita la casa."),
                night = L("La posada está llena de marineros. Si quieres cama, subiendo a la derecha."),
                barks = L("¡Sopa caliente!", "¡Esa mesa!", "¿Otra ronda?"),
                topics = new[] { ("¿Qué se cuenta en el puerto?", "Los corsarios orcos asaltan los barcos. La capitana Rocío los combate, pero sola no puede. Y Hassan dice que trae especias de ultramar. Yo creo que son hierbas del pantano."),
                                 ("¿Me das de comer?", "Por 10 monedas te sirvo un plato caliente: te cura y te deja dormir en una cama. Aquí también puedes guardar tu viaje.") },
                choice = new NpcChoice
                {
                    ask = "¿Te gusta mi sopa? Y no me mientas, que lo noto.",
                    answers = new[] { "La mejor del reino.", "Le falta sal." },
                    replies = new[] { "¡Ay, qué zalamero! Toma, más pan.", "¿Sal? ¡Si lleva media salina! ...Bueno, le pondré más." },
                    affinity = new[] { 2, 1 }, notes = new[] { "marta_soup_good", "marta_salt" },
                    recall = new[] { "¡El que dice que mi sopa es la mejor del reino!", "Hoy le he puesto más sal. ¡Por tu culpa!" },
                },
                quest = new NpcQuest
                {
                    title = "EL TÓNICO DE LA ABUELA", mat = "seta_azul", n = 2,
                    offer = "Mi abuela hacía un tónico con setas azules que levantaba a un muerto. ¿Me traes 2? Crecen en la orilla del lago y en el pantano.",
                    accepted = "¡Te guardo la mejor mesa!",
                    progress = "¿Y mis setas azules?",
                    done = "¡Brillan como las de la abuela! Toma, dos tónicos de la casa y unas monedas.",
                    reward = "2 TÓNICOS Y 20 MONEDAS", give = s => { s.Give("tonico", 2); s.coins += 20; },
                },
                work = L("i:posada:4.5,2.3:v", "i:posada:4.5,2.3:v", "i:posada:8.5,8.4"),
                social = L("i:posada:3,7.6"),
                sleep = "i:posada:18,7.8",
            },
            new NpcDef
            {
                id = "bartolo", name = "Bartolo", job = "Pescador", sprite = "NpcBartolo", town = "City_Puerto", workAnim = "Interact",
                personality = "Viejo gruñón, supersticioso, cuenta historias del mar que nadie cree.",
                bio = "Bartolo. Cincuenta años en el mar. He visto serpientes, sirenas y una vez un pez que hablaba. Era muy maleducado.",
                first = L("¿Qué miras? ...Un caballero. Hmph. Los caballeros espantan a los peces con tanto ruido de chatarra. Bartolo."),
                again = L("Hoy no pican.", "El mar está raro. Huele a azufre.", "¿Vienes a espantarme los peces otra vez?"),
                friend = L("Ah, eres tú. Siéntate. Hoy pican. Será que traes suerte."),
                night = L("De noche el mar canta. No le hagas caso."),
                barks = L("Malditas gaviotas.", "Pica, pica...", "Hmph."),
                topics = new[] { ("¿Historias del mar?", "Una vez saqué un pez con una moneda de oro en la boca. Me la gasté en la posada. El pez se enfadó mucho."),
                                 ("¿Qué pasa con los corsarios?", "Orcos con barco. Lo peor de los dos mundos. Roban las redes y las cuerdas. Si los ves por la costa, dales recuerdos de mi parte. Con la espada.") },
                choice = new NpcChoice
                {
                    ask = "¿Crees en las sirenas?",
                    answers = new[] { "Claro que sí.", "Son cuentos de viejos." },
                    replies = new[] { "¡Por fin alguien sensato! Una me robó la caña, ¿sabes?", "¿Viejo? ¿Cuentos? Hmph. Ya verás cuando te robe una la espada." },
                    affinity = new[] { 2, -1 }, notes = new[] { "bartolo_sirens", "bartolo_tales" },
                    recall = new[] { "El único que me cree lo de las sirenas. Siéntate.", "El listo que no cree en sirenas. Hmph." },
                },
                quest = new NpcQuest
                {
                    title = "REDES ROTAS", mat = "tela", n = 4,
                    offer = "Los corsarios me rajaron las redes. Necesito 4 telas de lino para remendarlas. Lucía y Hassan las venden, o las llevan los corsarios encima.",
                    accepted = "Hmph. Gracias.",
                    progress = "Las redes no se remiendan solas.",
                    done = "Tela buena. Toma unas monedas y estas flechas ígneas que encontré en un barco corsario. A mí no me sirven.",
                    reward = "40 MONEDAS Y 5 FLECHAS ÍGNEAS", give = s => { s.coins += 40; s.Give("flecha_fuego", 5); },
                },
                work = L("m:19,42:v", "m:47,40:v", "m:18,38:v"),
                social = L("a:fire:2,1"),
                sleep = "i:cabana:10.5,2.8",
            },
            new NpcDef
            {
                id = "rocio", name = "Capitana Rocío", job = "Capitana de la Gaviota", sprite = "NpcRocio", town = "City_Puerto",
                personality = "Directa, temeraria, ríe fuerte, odia a los corsarios con toda su alma.",
                bio = "Rocío, capitana de la Gaviota. Bueno, de lo que dejaron los corsarios de la Gaviota. Ahora cazo corsarios desde tierra.",
                first = L("¡Ja! ¡Un caballero en mi puerto! Rocío, capitana. Si sabes usar esa espada, tengo trabajo para ti."),
                again = L("¿Has visto corsarios por la costa? ¡Dímelo!", "El mar es libre. Los corsarios no.", "¡Ja! ¿Una ronda en el Jabalí?"),
                friend = L("¡Mi segundo de a bordo! Cuando recupere la Gaviota, tendrás camarote propio."),
                night = L("De noche los corsarios desembarcan. Duermo con la espada en la mano."),
                barks = L("¡Corsarios!", "¡Ja!", "El viento rola..."),
                topics = new[] { ("¿Qué le pasó a tu barco?", "Los corsarios orcos la abordaron de noche. Mataron a medio pasaje. Yo salté al agua. Desde entonces, cada corsario que cae es un marinero vengado."),
                                 ("¿Cómo pelean los corsarios?", "En manada. Uno grita y vienen todos por los lados. No dejes que te rodeen: retrocede, para el golpe del primero y remátalo.") },
                choice = new NpcChoice
                {
                    ask = "¿Tú qué harías con los corsarios capturados?",
                    answers = new[] { "Juzgarlos con justicia.", "Echarlos al mar." },
                    replies = new[] { "...Tienes razón. Mi rabia no es justicia. Gracias por recordármelo.", "¡JA! ¡Así me gusta!" },
                    affinity = new[] { 1, 2 }, notes = new[] { "rocio_justice", "rocio_sea" },
                    recall = new[] { "Sigo pensando en lo que dijiste de la justicia.", "¡Al mar con ellos! ¿Te acuerdas? ¡Ja!" },
                },
                quest = new NpcQuest
                {
                    title = "CAZA DE CORSARIOS", counter = s => s.orcKills, n = 6,
                    offer = "Derrota a 6 orcos de la costa, corsarios sobre todo. Si lo haces, te doy la reliquia de mi familia: el tridente del mar.",
                    accepted = "¡Que tiemblen!",
                    progress = "¡Más corsarios!",
                    done = "¡Seis! ¡Ja! Toma el tridente. Mi abuelo pescaba tiburones con él. Tú pescarás orcos.",
                    reward = "TRIDENTE DEL MAR", give = s => { if (!s.AddItem("trident")) s.coins += 100; },
                },
                work = L("m:46,33", "m:30,30", "m:60,31"),
                social = L("i:posada:11.5,7.6"),
                sleep = "i:posada:16.2,1.9",
            },
            new NpcDef
            {
                id = "hassan", name = "Hassan", job = "Mercader de ultramar", sprite = "NpcHassan", town = "City_Puerto", service = "exotic", workAnim = "Interact",
                personality = "Sonriente, teatral, exagera la calidad de todo lo que vende.",
                bio = "¡Hassan, amigo mío! Comerciante de las Islas del Sol. Traigo lo raro, lo exótico y lo imposible. A buen precio. Casi.",
                first = L("¡Bienvenido, bienvenido, noble guerrero! Hassan, mercader de ultramar. ¡Mira, toca, compra! Bueno, tocar no."),
                again = L("¡Amigo! Hoy tengo cristal de los glaciares del norte. Del norte de verdad.", "Todo de calidad, todo garantizado. Garantía de Hassan.", "¿Vendes algo? Hassan compra de todo."),
                friend = L("¡Mi mejor amigo! Para ti, precio de familia. Bueno, de familia lejana."),
                night = L("La tienda cierra, pero para ti... Hassan siempre está abierto."),
                barks = L("¡Exótico!", "¡Precios de locura!", "¡Del otro lado del mar!"),
                topics = new[] { ("¿Qué traes de ultramar?", "Plata, cristal de escarcha, aceite fino, frascos de vidrio soplado... Todo lo que un caballero necesita para sus fórmulas y su forja."),
                                 ("¿Pip es tu hijo?", "Mi sobrino. Mi hermana me lo encargó. Le enseño el negocio, pero él solo quiere ser marinero como la capitana. Cosas de la juventud.") },
                choice = new NpcChoice
                {
                    ask = "Dime, amigo: ¿la plata de Hassan no es la mejor que has visto?",
                    answers = new[] { "La mejor del mundo.", "Esto parece estaño." },
                    replies = new[] { "¡Un hombre de buen gusto! Te haré una rebaja... algún día.", "¿Estaño? ¡Hassan está ofendido! ...Es una mezcla. Pequeña. Muy pequeña." },
                    affinity = new[] { 1, 1 }, notes = new[] { "hassan_best", "hassan_tin" },
                    recall = new[] { "¡El amigo de buen gusto ha vuelto!", "¡El experto en estaño! Ja, ja. Hoy la plata es pura, lo juro." },
                },
                quest = new NpcQuest
                {
                    title = "COLMILLOS PARA LAS ISLAS", mat = "colmillo", n = 2,
                    offer = "En las Islas del Sol pagan fortunas por colmillos de orco tallados. Tráeme 2 y compartimos ganancias.",
                    accepted = "¡Socio!",
                    progress = "¿Los colmillos, socio?",
                    done = "¡Magníficos! Toma tu parte: monedas y frascos de vidrio de las islas.",
                    reward = "60 MONEDAS Y 4 FRASCOS", give = s => { s.coins += 60; s.Give("frasco", 4); },
                },
                work = L("a:shop#2:0,1:^", "a:shop#2:0,1:^", "a:shop#2:1,1:^"),
                social = L("a:fire:-2,1"),
                sleep = "i:casa#1:15,7.8",
            },
            new NpcDef
            {
                id = "pip", name = "Pip", job = "Grumete", sprite = "NpcPip", town = "City_Puerto",
                personality = "Inquieto, soñador, imita a la capitana Rocío en todo.",
                bio = "¡Pip, grumete! Bueno, todavía no tengo barco. Pero cuando la capitana Rocío recupere la Gaviota, seré su grumete.",
                first = L("¡Ahoy! ¡Pip, grumete de la Gaviota! Bueno, de la futura Gaviota. ¿Tú también odias a los corsarios?"),
                again = L("¡Ahoy, caballero!", "He aprendido un nudo nuevo. ¿Quieres verlo? ...Se ha deshecho.", "¡Cuando sea capitán te llevaré de viaje!"),
                friend = L("¡Mi amigo de tierra firme! Te he guardado una concha, mira."),
                night = L("Mi tío Hassan dice que me acueste. Pero las estrellas se ven mejor desde el muelle."),
                barks = L("¡Ahoy!", "¡Iza la vela!", "¡A babor!"),
                topics = new[] { ("¿Qué se ve desde el muelle?", "¡El faro! Y a veces barcos corsarios lejos, lejos. Y una vez vi una ballena. O una roca. Una roca que se movía."),
                                 ("¿Tu tío te trata bien?", "Sí, pero me hace contar monedas todo el día. ¡Yo quiero contar olas!") },
                choice = new NpcChoice
                {
                    ask = "¿Me llevarías contigo en tu aventura?",
                    answers = new[] { "Cuando seas mayor.", "Ya eres todo un marinero." },
                    replies = new[] { "Eso dice todo el mundo... Vale.", "¡¿De verdad?! ¡Se lo voy a decir a la capitana!" },
                    affinity = new[] { 0, 2 }, notes = new[] { "pip_older", "pip_sailor" },
                    recall = new[] { "¿Ya soy mayor? ¿No? Vale...", "¡Todo un marinero, dijiste! ¡Ahoy!" },
                },
                quest = new NpcQuest
                {
                    title = "SETAS QUE BRILLAN", mat = "seta_azul", n = 3,
                    offer = "Quiero hacer un farolillo con setas que brillan, como las del lago. ¿Me traes 3 setas azules?",
                    accepted = "¡Ahoy! ¡Te espero en el muelle!",
                    progress = "¿Ya tienes las setas que brillan?",
                    done = "¡Brillan! ¡Mi farolillo! Toma, todo lo que tengo: quince monedas y mi mejor dibujo. Es la Gaviota. Y tú.",
                    reward = "15 MONEDAS Y EL DIBUJO DE PIP", give = s => { s.coins += 15; s.Set("pip_drawing"); },
                },
                work = L("m:19,36", "m:40,28", "m:47,35", "m:25,30"),
                social = L("a:shop#2:2,2"),
                sleep = "i:casa#1:5.5,6.2",
            },
        };

        static Dictionary<string, NpcDef> _byId;
        public static NpcDef Get(string id)
        {
            if (_byId == null) _byId = All.ToDictionary(n => n.id);
            return id != null && _byId.TryGetValue(id, out var d) ? d : null;
        }
    }
}
