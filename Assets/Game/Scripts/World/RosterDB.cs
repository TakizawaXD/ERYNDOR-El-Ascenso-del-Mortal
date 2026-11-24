using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>The new roster (Tools/CharAnim/roster.py): where each new enemy lives (merged into SpawnDirector.Table at
    /// startup) and the adventurers that live in the towns with their job.</summary>
    public static class RosterDB
    {
        /// <summary>region -> (extra day types, extra night types)</summary>
        public static readonly Dictionary<char, (string[] day, string[] night)> Spawns = new Dictionary<char, (string[], string[])>
        {
            { 'a', (new[] { "GoblinAxe", "SlimeGreen" },               new[] { "Skeleton", "Bat" }) },                          // Valle Central
            { 'b', (new[] { "GoblinAxe", "GoblinShaman", "WolfWarrior" }, new[] { "Werewolf", "Bat", "Skeleton" }) },           // Bosque del Oeste
            { 'c', (new[] { "SlimeGreen", "GoblinAxe" },               new[] { "Bat", "Tentacle" }) },                          // Lago Espejo
            { 'd', (new[] { "Tentacle", "Maw" },                       new[] { "Maw", "EyeWatcher", "Bat" }) },                 // Pantano Carmesí
            { 'e', (new[] { "GoblinViking", "WolfWarrior" },           new[] { "Werewolf", "SkeletonWarrior" }) },              // Picos Nevados
            { 'f', (new[] { "GoblinRider", "Minotaur" },               new[] { "Hellhound", "SkeletonAxe" }) },                 // Arenas Rojas
            { 'g', (new[] { "ImpBlade", "FireSlug", "LavaGolem", "ShieldBrute" }, new[] { "FlameSkull", "HellBat", "ImpSwarm", "DemonAxe" }) }, // Monte Ceniza
            { 'h', (new[] { "ImpCrossbow", "ScytheCultist", "EyeWatcher" }, new[] { "Reaper", "DemonGreat", "DemonQueen", "ImpChain" }) }, // Bosque Corrupto
            { 'i', (new string[0],                                     new[] { "SkeletonSpear", "SkeletonWarrior" }) },         // Ciudadela
            { 'j', (new[] { "GoblinViking" },                          new[] { "Skeleton", "ImpTrident" }) },                   // Costa del Puerto
        };

        public static readonly string[] NightOnly = { "Skeleton", "SkeletonSpear", "SkeletonWarrior", "SkeletonAxe", "Reaper", "Werewolf", "Bat" };

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        public static void Register()
        {
            foreach (var kv in Spawns)
            {
                (string[] day, string[] night) cur = SpawnDirector.Table.TryGetValue(kv.Key, out var t) ? t : (new string[0], new string[0]);
                SpawnDirector.Table[kv.Key] = (cur.day.Union(kv.Value.day).ToArray(), cur.night.Union(kv.Value.night).ToArray());
            }
            foreach (var n in NightOnly) SpawnDirector.NightOnly.Add(n);
        }

        // ------------------------------------------------------------ adventurers
        public enum Job { Guard, Healer, Sage, Ranger, Patrol }

        public class Hero
        {
            public string id, name; public Job job; public string[] lines;
        }

        public static readonly Hero[] Heroes =
        {
            new Hero { id = "HeroSwordswoman", name = "Aria la espadachina", job = Job.Guard, lines = new[] { "Mientras yo esté aquí, ningún monstruo pisa la aldea.", "¿Has visto al Coloso del norte? Dicen que su corazón es de hielo puro." } },
            new Hero { id = "HeroWizard",      name = "Merlina la maga", job = Job.Sage, lines = new[] {
                "El Invocador es inmune mientras viva uno solo de sus siervos. Mátalos primero.",
                "Gorgrak golpea el suelo y la onda recorre su guarida: rueda a través de ella.",
                "La Madre de Sangre escupe en anillos. Busca los huecos entre los escupitajos.",
                "Cuando un jefe cambia de fase, la arena se enciende y empuja: aléjate un paso.",
                "El Señor Demonio marca el suelo antes de que caigan los meteoros. ¡No te quedes quieto!" } },
            new Hero { id = "HeroSoldier",     name = "Soldado Bruno", job = Job.Guard, lines = new[] { "Guardia del puerto. Los corsarios no desembarcan en mi turno." } },
            new Hero { id = "HeroKnight",      name = "Sir Rodrigo", job = Job.Guard, lines = new[] { "La Ciudadela no cae. Ni de día ni de noche." } },
            new Hero { id = "HeroCrusader",    name = "Hermano Tomás", job = Job.Guard, lines = new[] { "La luz guía mi lanza contra los muertos que se levantan de noche." } },
            new Hero { id = "HeroAxeKnight",   name = "Gunnar el hachero", job = Job.Guard, lines = new[] { "Mi hacha ha partido más escudos que tú panes." } },
            new Hero { id = "HeroRider",       name = "Capitán Alonso", job = Job.Patrol, lines = new[] { "Patrullo los caminos del reino. Si ves goblins a lomos de lobo, avísame." } },
            new Hero { id = "HeroPriestess",   name = "Hermana Lucía", job = Job.Healer, lines = new[] { "Que la luz cierre tus heridas, viajero." } },
            new Hero { id = "HeroRanger",      name = "Ivy la exploradora", job = Job.Ranger, lines = new[] { "Toma, unas flechas para el camino. Vuelve mañana si necesitas más." } },
        };

        public static Hero Get(string id) => Heroes.FirstOrDefault(h => h.id == id);
    }
}
