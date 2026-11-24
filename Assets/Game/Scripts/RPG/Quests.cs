using System;
using System.Collections.Generic;
using System.Linq;

namespace WoodsGame
{
    /// <summary>Quest list. Progress is derived from PlayerState, so quests survive save/load for free.</summary>
    public static class Quests
    {
        public class Quest
        {
            public string id, title, description;
            public bool main;
            public Func<PlayerState, int> progress;
            public int goal = 1;
            public string rewardText;
            public Action<PlayerState> reward;
            public Func<PlayerState, bool> visible = _ => true;

            public bool Done(PlayerState s) => progress(s) >= goal;
            public bool Rewarded(PlayerState s) => s.Has("quest_" + id);
        }

        static int Flag(PlayerState s, string f) => s.Has(f) ? 1 : 0;
        static int Regions(PlayerState s) => s.flags.Count(f => f.StartsWith("region_"));

        public static readonly List<Quest> All = new List<Quest>
        {
            new Quest { id = "m0", main = true, title = "EL INVOCADOR", description = "EN EL CLARO DEL BOSQUE CORRUPTO (NOROESTE) ALGUIEN LEVANTA A LOS MUERTOS. MATA A SUS SIERVOS: SOLO ASÍ PODRÁS HERIRLE.",
                progress = s => Flag(s, "boss_I"), rewardText = "LA MALDICIÓN DEL INVOCADOR (V)", reward = s => { } },
            new Quest { id = "m1", main = true, title = "GORGRAK EL CAUDILLO", description = "DERROTA A GORGRAK, EL JEFE ORCO, EN SU GUARIDA DE LAS ARENAS ROJAS (NORESTE).",
                progress = s => Flag(s, "boss_K"), rewardText = "+30 MONEDAS", reward = s => s.coins += 30 },
            new Quest { id = "m2", main = true, title = "LA MADRE DE SANGRE", description = "DESTRUYE A LA MADRE DE SANGRE JUNTO A LA TORRE OSCURA DEL PANTANO CARMESÍ (SURESTE).",
                progress = s => Flag(s, "boss_Q"), rewardText = "+2 MEDICINAS", reward = s => s.Give("medicina", 2) },
            new Quest { id = "m3", main = true, title = "EL SELLO DEMONÍACO", description = "CON AMBOS GUARDIANES CAÍDOS, EL SELLO DEL MONTE CENIZA (ESTE) SE ROMPERÁ.",
                progress = s => Flag(s, "boss_K") + Flag(s, "boss_Q"), goal = 2, rewardText = "EL CAMINO AL ALTAR",
                reward = s => { }, visible = s => s.Has("boss_K") || s.Has("boss_Q") },
            new Quest { id = "m4", main = true, title = "EL SEÑOR DEMONIO", description = "CRUZA EL SELLO DEL MONTE CENIZA Y DERROTA AL SEÑOR DEMONIO JUNTO AL VOLCÁN.",
                progress = s => Flag(s, "boss_B"), rewardText = "LA PAZ DEL BOSQUE", reward = s => { },
                visible = s => s.Has("boss_K") && s.Has("boss_Q") },
            new Quest { id = "s0", title = "EL CORAZÓN HELADO", description = "EN LOS PICOS NEVADOS, JUNTO AL CAMINO DEL NORTE, DESPIERTA EL COLOSO DE ESCARCHA. DERRÍBALO.",
                progress = s => Flag(s, "boss_F"), rewardText = "+60 MONEDAS Y +1 CORAZÓN", reward = s => { s.coins += 60; s.maxHP += 2; s.hp = s.maxHP; } },
            new Quest { id = "s1", title = "CAZADOR DE ORCOS", description = "DERROTA 15 ORCOS.", progress = s => s.orcKills, goal = 15,
                rewardText = "+40 MONEDAS", reward = s => s.coins += 40 },
            new Quest { id = "s2", title = "PURGA DE SANGRE", description = "DERROTA 15 MONSTRUOS DE SANGRE.", progress = s => s.bloodKills, goal = 15,
                rewardText = "+2 MEDICINAS Y 3 FLORES DE LUNA", reward = s => { s.Give("medicina", 2); s.Give("flor_luna", 3); } },
            new Quest { id = "s3", title = "EXORCISTA", description = "DERROTA 10 DEMONIOS.", progress = s => s.demonKills, goal = 10,
                rewardText = "ESPADA +1", reward = s => s.swordBonus++ },
            new Quest { id = "s4", title = "BUSCATESOROS", description = "ABRE 10 COFRES.", progress = s => s.chestsOpened, goal = 10,
                rewardText = "+1 CORAZÓN", reward = s => { s.maxHP += 2; s.hp = s.maxHP; } },
            new Quest { id = "s5", title = "EXPLORADOR", description = "DESCUBRE LAS 10 REGIONES DEL MUNDO.", progress = Regions, goal = 10,
                rewardText = "+50 MONEDAS Y 20 FLECHAS", reward = s => { s.coins += 50; s.arrows += 20; } },
        };

        /// <summary>Completes and rewards anything newly finished. Call after any state change.</summary>
        public static void Refresh()
        {
            var s = GameManager.State;
            foreach (var q in All)
            {
                if (q.Rewarded(s) || !q.Done(s)) continue;
                s.Set("quest_" + q.id);
                q.reward(s);
                var p = PlayerController.Current;
                if (p) p.health.Init(s.maxHP, s.hp);
                Sfx.Play("victory", 0.6f);
                UIRoot.TitleCard("MISIÓN COMPLETADA: " + q.title, q.rewardText);
            }
        }

        public static IEnumerable<Quest> Visible(PlayerState s) => All.Where(q => q.visible(s));
    }
}
