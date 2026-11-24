// The new character roster (2026-11-20): 33 monsters and 9 heroes cut from the two sheets in Assets/Scripts and animated
// by Tools/CharAnim/roster.py. Monsters become regional enemies (stats + AI profile here, regions in RosterDB.Spawns);
// heroes live in the towns as Adventurers with a job (guard, healer, sage, ranger, patrol).
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace WoodsGame.EditorTools
{
    public static partial class GameBuilder
    {
        // id, name, kind, ai, hp, damage, chase speed, aggro, ranged, xp
        static readonly (string id, string name, EnemyKind kind, AIProfile ai, int hp, int dmg, float speed, float aggro, bool ranged, int xp)[] RosterEnemies =
        {
            ("Werewolf",        "HOMBRE LOBO",          EnemyKind.Orc,          AIProfile.Brute,      16, 3, 3.0f, 6.5f, false, 9),
            ("WolfWarrior",     "LOBO GUERRERO",        EnemyKind.Orc,          AIProfile.Pack,       10, 2, 2.8f, 6f,   false, 6),
            ("SlimeGreen",      "LIMO VERDE",           EnemyKind.BloodMonster, AIProfile.Ambusher,    6, 1, 2.0f, 4f,   false, 3),
            ("GoblinAxe",       "GOBLIN",               EnemyKind.Orc,          AIProfile.Pack,        6, 1, 2.7f, 5.5f, false, 3),
            ("GoblinViking",    "GOBLIN VIKINGO",       EnemyKind.Orc,          AIProfile.Brute,      11, 2, 2.1f, 5.5f, false, 6),
            ("GoblinShaman",    "CHAMÁN GOBLIN",        EnemyKind.Demon,        AIProfile.Caster,      8, 2, 2.0f, 7f,   true,  7),
            ("GoblinRider",     "JINETE GOBLIN",        EnemyKind.Orc,          AIProfile.Charger,    12, 3, 3.2f, 7f,   false, 8),
            ("Bat",             "MURCIÉLAGO",           EnemyKind.Demon,        AIProfile.Skirmisher,  4, 1, 3.4f, 6f,   false, 2),
            ("Skeleton",        "ESQUELETO",            EnemyKind.Demon,        AIProfile.Pack,        7, 2, 2.3f, 6f,   false, 4),
            ("SkeletonSpear",   "ESQUELETO LANCERO",    EnemyKind.Demon,        AIProfile.Duelist,    11, 3, 2.3f, 6f,   false, 8),
            ("SkeletonWarrior", "ESQUELETO GUERRERO",   EnemyKind.Demon,        AIProfile.Brute,      12, 3, 2.0f, 6f,   false, 8),
            ("SkeletonAxe",     "ESQUELETO HACHERO",    EnemyKind.Demon,        AIProfile.Charger,    12, 3, 2.4f, 6.5f, false, 8),
            ("Reaper",          "LA PARCA",             EnemyKind.Demon,        AIProfile.Wraith,     14, 4, 2.6f, 8f,   false, 12),
            ("ImpBlade",        "DIABLILLO",            EnemyKind.Demon,        AIProfile.Skirmisher,  6, 2, 3.0f, 6f,   false, 4),
            ("ImpCrossbow",     "DIABLILLO BALLESTERO", EnemyKind.Demon,        AIProfile.Kiter,       6, 2, 2.4f, 7.5f, true,  5),
            ("ImpTrident",      "DIABLILLO ALADO",      EnemyKind.Demon,        AIProfile.Skirmisher,  7, 2, 3.2f, 7f,   false, 5),
            ("DemonAxe",        "VERDUGO DEMONÍACO",    EnemyKind.Demon,        AIProfile.Brute,      18, 4, 2.0f, 6f,   false, 11),
            ("Hellhound",       "CAN INFERNAL",         EnemyKind.Demon,        AIProfile.Charger,    12, 3, 3.6f, 7.5f, false, 9),
            ("DemonGreat",      "GRAN DEMONIO ALADO",   EnemyKind.Demon,        AIProfile.Caster,     22, 4, 2.2f, 8f,   true,  16),
            ("ScytheCultist",   "SEGADOR",              EnemyKind.Demon,        AIProfile.Duelist,    13, 3, 2.5f, 6.5f, false, 9),
            ("ImpChain",        "DIABLILLO DE CADENAS", EnemyKind.Demon,        AIProfile.Pack,        8, 2, 2.9f, 6.5f, false, 5),
            ("FireSlug",        "BABOSA DE FUEGO",      EnemyKind.BloodMonster, AIProfile.Bomber,      9, 2, 1.4f, 6f,   true,  6),
            ("FlameSkull",      "CALAVERA ÍGNEA",       EnemyKind.Demon,        AIProfile.Kiter,       7, 2, 2.6f, 8f,   true,  7),
            ("HellBat",         "MURCIÉLAGO INFERNAL",  EnemyKind.Demon,        AIProfile.Skirmisher,  6, 2, 3.6f, 7f,   false, 4),
            ("Tentacle",        "TENTÁCULO",            EnemyKind.BloodMonster, AIProfile.Ambusher,   10, 2, 1.8f, 4.5f, false, 6),
            ("Maw",             "FAUCES",               EnemyKind.BloodMonster, AIProfile.Skirmisher,  8, 3, 3.0f, 6f,   false, 6),
            ("Minotaur",        "MINOTAURO",            EnemyKind.Orc,          AIProfile.Charger,    24, 4, 2.6f, 7f,   false, 14),
            ("EyeWatcher",      "OJO VIGÍA",            EnemyKind.Demon,        AIProfile.Kiter,       9, 2, 1.8f, 9f,   true,  7),
            ("DarkSpearman",    "LANCERO OSCURO",       EnemyKind.Demon,        AIProfile.Duelist,    14, 3, 2.3f, 6.5f, false, 9),
            ("ShieldBrute",     "BRUTO DEL ESCUDO",     EnemyKind.Demon,        AIProfile.Brute,      22, 3, 1.7f, 5.5f, false, 11),
            ("ImpSwarm",        "ENJAMBRE DE DIABLILLOS", EnemyKind.Demon,      AIProfile.Pack,       14, 2, 2.6f, 6.5f, false, 9),
            ("LavaGolem",       "GÓLEM DE LAVA",        EnemyKind.Demon,        AIProfile.Brute,      30, 5, 1.5f, 6f,   false, 18),
            ("DemonQueen",      "REINA DEMONIO",        EnemyKind.Demon,        AIProfile.Caster,     20, 3, 2.0f, 8f,   true,  16),
        };

        static readonly Dictionary<string, Color> RosterGlow = new Dictionary<string, Color>
        {
            { "Reaper", new Color(0.5f, 0.9f, 1f) }, { "FlameSkull", new Color(1f, 0.5f, 0.15f) }, { "LavaGolem", new Color(1f, 0.45f, 0.1f) },
            { "DemonQueen", new Color(1f, 0.8f, 0.3f) }, { "EyeWatcher", new Color(0.8f, 0.5f, 1f) }, { "Werewolf", new Color(1f, 0.85f, 0.3f) },
            { "Hellhound", new Color(1f, 0.4f, 0.1f) }, { "FireSlug", new Color(1f, 0.55f, 0.15f) }, { "DemonGreat", new Color(1f, 0.35f, 0.15f) },
            { "GoblinShaman", new Color(0.6f, 1f, 0.3f) }, { "SkeletonSpear", new Color(0.5f, 0.9f, 1f) },
        };

        /// <summary>Called from BuildRpgAssets: prefabs of the new monsters, added to GameAssets.enemyPrefabs.</summary>
        static IEnumerable<GameObject> RosterEnemyPrefabs()
        {
            foreach (var r in RosterEnemies)
            {
                if (!System.IO.File.Exists($"{ProjectRoot}/{Chars}/{r.id}/{r.id}_animations.json"))
                { Debug.LogError($"[GameBuilder] roster art missing for {r.id} (python Tools/CharAnim/roster.py)"); continue; }
                yield return ActorPrefab(r.id, r.id, true, 1, go =>
                {
                    var e = go.AddComponent<EnemyController>();
                    e.kind = r.kind; e.typeId = r.id; e.ai = r.ai; e.displayName = r.name;
                    e.maxHP = r.hp; e.damage = r.dmg; e.walkSpeed = r.speed * 0.6f; e.chaseSpeed = r.speed; e.aggroRange = r.aggro;
                    e.attackRange = r.ai == AIProfile.Charger || r.ai == AIProfile.Brute ? 1.1f : 1.0f;
                    e.attackCooldown = r.ai == AIProfile.Brute ? 1.4f : 1.1f; e.heavyChance = r.ai == AIProfile.Brute ? 0.5f : 0.3f;
                    e.knockbackResist = r.hp >= 20 ? 0.6f : 0f;
                    e.ranged = r.ranged; e.rangedMin = 2.5f; e.rangedMax = 7.5f; e.rangedCooldown = 3f; e.rangedDamage = Mathf.Max(1, r.dmg - 1);
                    e.xpReward = r.xp; e.coins = 1 + r.xp / 3; e.potionChance = 0.15f; e.arrowChance = 0.2f;
                    if (RosterDB.NightOnly.Contains(r.id)) e.activeAt = ActiveTime.Night;
                    if (r.hp >= 20) { var col = go.GetComponent<CircleCollider2D>(); col.radius = 0.4f; }
                    if (RosterGlow.TryGetValue(r.id, out var c))
                    {
                        var a = go.AddComponent<EnemyAura>(); a.color = c; a.motes = 4; a.eyeHeight = 0.9f; a.groundRadius = 0.8f;
                    }
                });
            }
        }

        static GameObject HeroPrefab(string id)
        {
            return ActorPrefab(id, id, true, 1, go =>
            {
                Object.DestroyImmediate(go.GetComponent<Health>());
                var rb = go.GetComponent<Rigidbody2D>(); rb.bodyType = RigidbodyType2D.Kinematic;
                var ad = go.AddComponent<Adventurer>(); ad.heroId = id;
            });
        }

        /// <summary>Which hero stands where (map id -> heroes). Spots are picked on open ground near the map centre.</summary>
        static readonly Dictionary<string, string[]> HeroPosts = new Dictionary<string, string[]>
        {
            { "City_Valle", new[] { "HeroSwordswoman", "HeroPriestess", "HeroRanger" } },
            { "City_Ciudadela", new[] { "HeroKnight", "HeroCrusader", "HeroAxeKnight", "HeroWizard", "HeroRider" } },
            { "City_Puerto", new[] { "HeroSoldier" } },
        };

        static void PlaceAdventurers(string id, LevelData d, Transform world, RectInt? area = null)
        {
            if (!HeroPosts.TryGetValue(id, out var heroes)) return;
            var root = new GameObject("Adventurers").transform; root.SetParent(world, false);
            var rng = new System.Random(id.GetHashCode());
            int cx = area.HasValue ? (area.Value.xMin + area.Value.xMax) / 2 : d.w / 2, crow = area.HasValue ? (area.Value.yMin + area.Value.yMax) / 2 : d.h / 2, placed = 0;
            foreach (var h in heroes)
            {
                if (AssetDatabase.LoadAssetAtPath<GameObject>($"{Prefabs}/{h}.prefab") == null && HeroPrefab(h) == null) continue;
                for (int tries = 0; tries < 400; tries++)
                {
                    int x = cx + rng.Next(-14, 15), row = crow + rng.Next(-10, 11);
                    if (!Walkable(d, x, row) || !Walkable(d, x + 1, row) || !Walkable(d, x - 1, row) || !Walkable(d, x, row + 1) || !Walkable(d, x, row - 1)) continue;
                    if (d.E(x, row) != ' ') continue;
                    Spawn(h, root, new Vector3(x + 0.5f, d.h - 1 - row + 0.3f, 0));
                    placed++;
                    break;
                }
            }
            Debug.Log($"[GameBuilder] {id}: {placed} adventurers");
        }

        /// <summary>Hero prefabs are (re)made every build.</summary>
        static void BuildHeroPrefabs() { foreach (var h in RosterDB.Heroes) HeroPrefab(h.id); }
    }
}
