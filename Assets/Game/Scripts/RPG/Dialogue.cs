using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Conversation tree with a townsperson. Greetings depend on what they remember (first meeting, already talked today,
    /// friendship, your earlier answers, finished jobs, night). Options: who are you, topics, a personal question, their job,
    /// gifts, trade / forge / inn services, goodbye. Everything they remember is saved in PlayerState.npcs.</summary>
    public static class Dialogue
    {
        public static Villager Current { get; private set; }
        static PlayerState S => GameManager.State;

        static string Pick(string[] l) => l == null || l.Length == 0 ? "..." : l[UnityEngine.Random.Range(0, l.Length)];

        public static void Start(Villager v)
        {
            var d = v.Def; if (d == null) return;
            Current = v; v.Talking = true;
            var m = S.Memory(d.id);
            Sfx.Play("talk", 0.8f);
            Show(v, Greeting(d, m));
            m.talks++; m.lastDay = S.day;
        }

        public static void End()
        {
            if (Current != null) Current.Talking = false;
            Current = null;
        }

        /// <summary>What they say when you walk up to them.</summary>
        public static string Greeting(NpcDef d, NpcMemory m)
        {
            if (m.talks == 0) { m.Note("met"); return Pick(d.first); }
            if (d.quest != null && m.quest == 1 && Ready(d, m)) return "¡" + d.quest.title.Substring(0, 1) + d.quest.title.Substring(1).ToLowerInvariant() + "! ¿Lo tienes?";
            if (m.lastDay == S.day) return Pick(new[] { "¿Algo más?", "¿Otra vez por aquí? Dime.", "¿Sí?", "Te escucho." });
            if (d.choice != null)
                for (int k = 0; k < 2; k++)
                    if (m.Knows(d.choice.notes[k]) && UnityEngine.Random.value < 0.45f) return d.choice.recall[k];
            if (m.quest == 2 && !m.Knows("recalled_quest")) { m.Note("recalled_quest"); return "No he olvidado que me ayudaste con «" + d.quest.title.ToLowerInvariant() + "». Gracias otra vez."; }
            if (DayNight.IsNight && d.night != null && d.night.Length > 0) return Pick(d.night);
            if (m.affinity >= 4 && d.friend != null && d.friend.Length > 0) return Pick(d.friend);
            return Pick(d.again);
        }

        static void Show(Villager v, string text)
        {
            var d = v.Def; var m = S.Memory(d.id);
            var labels = new List<string>(); var acts = new List<Action>();
            void Opt(string l, Action a) { labels.Add(l); acts.Add(a); }

            if (!m.Knows("asked_who")) Opt("¿Quién eres?", () => { m.Note("asked_who"); Show(v, d.bio); });
            foreach (var (q, a) in d.topics) { var aa = a; Opt(q, () => { m.Note("topic_" + q.GetHashCode()); Show(v, aa); }); }
            if (d.choice != null && !m.Knows(d.choice.notes[0]) && !m.Knows(d.choice.notes[1]))
                Opt("Charlar", () => AskChoice(v));
            if (d.quest != null) QuestOption(v, d, m, Opt);
            if (!string.IsNullOrEmpty(d.likes) && S.InBag(d.likes) > 0 && !m.Knows("gift_day_" + S.day) && !string.IsNullOrEmpty(d.likesThanks))
                Opt("Regalar " + CraftDB.Get(d.likes).name.ToLowerInvariant(), () =>
                {
                    S.Consume(d.likes, 1, false); m.affinity += 2; m.Note("gift_day_" + S.day); m.Note("got_gift");
                    Sfx.Play("confirm"); Show(v, d.likesThanks);
                });
            Services(v, d, m, Opt);
            Opt("Adiós", () => { WorldUI.CloseAll(); End(); });
            WorldUI.Talk(v.portrait, d.name, d.job, text, labels.ToArray(), acts.ToArray());
        }

        static void AskChoice(Villager v)
        {
            var d = v.Def; var m = S.Memory(d.id); var c = d.choice;
            WorldUI.Talk(v.portrait, d.name, d.job, c.ask, new[] { c.answers[0], c.answers[1] }, new Action[]
            {
                () => Answer(v, 0), () => Answer(v, 1)
            });
        }

        static void Answer(Villager v, int k)
        {
            var d = v.Def; var m = S.Memory(d.id); var c = d.choice;
            m.Note(c.notes[k]); m.affinity += c.affinity[k];
            Show(v, c.replies[k]);
        }

        // ------------------------------------------------------------ jobs
        public static int Progress(NpcDef d, NpcMemory m)
        {
            var q = d.quest;
            if (q == null) return 0;
            if (q.Deliver) return Mathf.Min(q.n, S.InBag(q.mat));
            return Mathf.Clamp(q.counter(S) - m.questBase, 0, q.n);
        }

        public static bool Ready(NpcDef d, NpcMemory m) => d.quest != null && m.quest == 1 && Progress(d, m) >= d.quest.n;

        static void QuestOption(Villager v, NpcDef d, NpcMemory m, Action<string, Action> opt)
        {
            var q = d.quest;
            if (m.quest == 0)
                opt("¿Necesitas ayuda?", () => WorldUI.Talk(v.portrait, d.name, d.job, q.offer, new[] { "Cuenta conmigo.", "Ahora no puedo." }, new Action[]
                {
                    () => { Accept(d, m); Show(v, q.accepted); },
                    () => Show(v, "Lo entiendo. Si cambias de idea, aquí estaré."),
                }));
            else if (m.quest == 1)
            {
                if (Ready(d, m)) opt("Entregar: " + q.title.ToLowerInvariant(), () => { Complete(d, m); Show(v, q.done); });
                else opt($"{q.title.Substring(0, 1)}{q.title.Substring(1).ToLowerInvariant()} ({Progress(d, m)}/{q.n})", () => Show(v, q.progress));
            }
        }

        public static void Accept(NpcDef d, NpcMemory m)
        {
            m.quest = 1;
            m.questBase = d.quest.counter != null ? d.quest.counter(S) : 0;
            Sfx.Play("confirm");
            UIRoot.Toast("ENCARGO ACEPTADO: " + d.quest.title, 2.2f);
        }

        public static void Complete(NpcDef d, NpcMemory m)
        {
            var q = d.quest;
            if (q.Deliver) S.Consume(q.mat, q.n, false);
            m.quest = 2; m.affinity += 3; m.Note("helped");
            q.give(S);
            var p = PlayerController.Current; if (p) p.health.Init(S.maxHP, Mathf.Min(S.hp, S.maxHP));
            Progression.AddXP(10 + q.n * 2);
            Sfx.Play("victory", 0.6f);
            UIRoot.TitleCard("ENCARGO CUMPLIDO: " + q.title, q.reward);
        }

        // ------------------------------------------------------------ services
        static void Services(Villager v, NpcDef d, NpcMemory m, Action<string, Action> opt)
        {
            switch (d.service)
            {
                case "smith":
                    opt("Comprar", () => WorldUI.OpenTrade(WorldUI.TradeMode.Buy, d.id));
                    opt("Vender", () => WorldUI.OpenTrade(WorldUI.TradeMode.Sell, d.id));
                    opt("Mejorar equipo", () => WorldUI.OpenTrade(WorldUI.TradeMode.Upgrade, d.id));
                    opt("Reparar", () => WorldUI.OpenTrade(WorldUI.TradeMode.Repair, d.id));
                    break;
                case "shop": opt("Comerciar", () => WorldUI.OpenShop("general", d.id)); break;
                case "herbs": opt("Comprar ingredientes", () => WorldUI.OpenShop("herbs", d.id)); break;
                case "exotic": opt("Comerciar", () => WorldUI.OpenShop("exotic", d.id)); break;
                case "inn":
                    opt("Comer y descansar (10)", () =>
                    {
                        if (S.coins < 10) { Show(v, "Sin monedas no hay sopa, cariño. Vuelve cuando tengas diez."); return; }
                        S.coins -= 10;
                        var p = PlayerController.Current;
                        S.hp = S.maxHP; if (p) { p.health.Init(S.maxHP, S.hp); p.RestoreStamina(); }
                        GameManager.SetRestPoint((Vector2)v.transform.position + Vector2.down * 1.4f, v.gameObject.scene.name);
                        SaveSystem.Save(S);
                        Sfx.Play("eat");
                        Show(v, "¡Aquí tienes! Sopa caliente y pan del día. Descansa: tu cuarto está listo. (Vida y aguante restaurados · partida guardada)");
                    });
                    opt("Comerciar", () => WorldUI.OpenShop("general", d.id));
                    break;
                case "healer":
                    opt("Pedir una bendición", () =>
                    {
                        var p = PlayerController.Current;
                        S.hp = S.maxHP; if (p) { p.health.Init(S.maxHP, S.hp); p.RestoreStamina(); Fx.Spawn(FxKind.Heal, p.Body); }
                        Sfx.Play("levelup", 0.6f);
                        Show(v, "Que la luz cierre tus heridas. Ve en paz.");
                    });
                    break;
            }
        }

        /// <summary>NPC jobs in progress, for the journal.</summary>
        public static IEnumerable<string> JournalLines()
        {
            foreach (var d in NpcDB.All)
            {
                if (d.quest == null) continue;
                var m = S.npcs.FirstOrDefault(x => x.id == d.id);
                if (m == null || m.quest == 0) continue;
                string mark = m.quest == 2 ? "[X]" : Ready(d, m) ? "[!]" : "[ ]";
                yield return m.quest == 2 ? $"{mark} {d.quest.title} ({d.name.ToUpperInvariant()})"
                                          : $"{mark} {d.quest.title} ({d.name.ToUpperInvariant()}) {Progress(d, m)}/{d.quest.n}";
            }
        }
    }
}
