using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Living world: spawns each region's own enemies around the player, different by day and by night.
    /// The more you kill the higher the threat level (PlayerState.Threat 1..10): more enemies at once, faster spawns,
    /// tougher stats and more "PODEROSO" elites; at night a "CAMPEÓN" can appear. Map residents of the day go to sleep at night.</summary>
    public class SpawnDirector : MonoBehaviour
    {
        public static SpawnDirector Current { get; private set; }
        public static bool Enabled = true;      // tests switch it off for deterministic fights

        /// <summary>region id -> (day types, night types). Type ids are prefab names (GameAssets.enemyPrefabs).</summary>
        public static readonly Dictionary<char, (string[] day, string[] night)> Table = new Dictionary<char, (string[], string[])>
        {
            // each biome its own creatures (2026-11-21, one big map); the night brings wraiths and fallen knights everywhere
            { 'a', (new[] { "Orc", "GoblinAxe", "GoblinRider", "SlimeGreen" },               new[] { "DemonWraith", "KnightFallen", "Werewolf" }) },        // Valles de Valtherion
            { 'b', (new[] { "Werewolf", "WolfWarrior", "GoblinShaman", "GoblinAxe" },         new[] { "Werewolf", "DemonWraith", "WolfWarrior" }) },         // Bosque Eterno
            { 'c', (new[] { "Skeleton", "SkeletonSpear", "EyeWatcher" },                      new[] { "DemonWraith", "Skeleton", "Reaper" }) },              // Aurelith
            { 'd', (new[] { "BloodMonster", "Tentacle", "Maw", "BloodToxic" },                new[] { "BloodMonster", "DemonWraith", "ScytheCultist", "Bat" }) }, // Noxheim
            { 'e', (new[] { "OrcFrost", "OrcFrost", "WolfWarrior", "Minotaur" },              new[] { "OrcFrost", "DemonWraith", "Werewolf" }) },            // Valgrimm
            { 'f', (new[] { "OrcDesert", "OrcDesert", "Minotaur", "ImpTrident", "FireSlug" }, new[] { "DemonAsh", "Skeleton", "DemonWraith" }) },             // Desierto
            { 'g', (new[] { "DemonAsh", "LavaGolem", "FireSlug", "Hellhound", "FlameSkull" }, new[] { "DemonAsh", "Hellhound", "FlameSkull", "Demon" }) },     // Drakmor
            { 'h', (new[] { "Demon", "DemonAxe", "EyeWatcher", "ImpChain", "DarkSpearman" },  new[] { "Demon", "DemonWraith", "KnightFallen", "HellBat" }) },  // Torre Prohibida
            { 'i', (new string[0],                                                            new[] { "KnightFallen", "DemonWraith" }) },                    // Reino (safe by day)
            { 'j', (new[] { "OrcCorsair", "GoblinViking", "ImpCrossbow" },                    new[] { "OrcCorsair", "DemonWraith", "SkeletonAxe" }) },       // Ruinas Eternas
            // the underground: the same creatures day and night
            { 'k', (new[] { "Skeleton", "SkeletonWarrior" },                                  new[] { "Skeleton", "SkeletonWarrior" }) },
            { 'l', (new[] { "Skeleton", "SkeletonSpear", "Bat" },                             new[] { "Skeleton", "SkeletonSpear", "Bat" }) },
            { 'm', (new[] { "SkeletonWarrior", "Reaper" },                                    new[] { "SkeletonWarrior", "Reaper" }) },
            { 'n', (new[] { "ScytheCultist", "Skeleton" },                                    new[] { "ScytheCultist", "Skeleton" }) },
            { 'q', (new[] { "Orc", "GoblinAxe", "OrcBerserker" },                             new[] { "Orc", "GoblinAxe", "OrcBerserker" }) },
            { 'r', (new[] { "OrcFrost", "SkeletonWarrior" },                                  new[] { "OrcFrost", "SkeletonWarrior" }) },
            { 's', (new[] { "Skeleton", "SkeletonAxe", "Reaper" },                            new[] { "Skeleton", "SkeletonAxe", "Reaper" }) },
            { 't', (new[] { "BloodMonster", "BloodToxic", "Bat" },                            new[] { "BloodMonster", "BloodToxic", "Bat" }) },
            { 'u', (new[] { "Werewolf", "WolfWarrior" }, new[] { "Werewolf", "WolfWarrior" }) },          // Guarida de los Lobos
            { 'v', (new[] { "GoblinAxe", "Bat" }, new[] { "GoblinAxe", "Bat" }) },                       // Minas Abandonadas
            { 'w', (new[] { "SlimeGreen", "EyeWatcher" }, new[] { "SlimeGreen", "EyeWatcher" }) },       // Gruta del Lago
            { 'x', (new[] { "Skeleton", "SkeletonSpear" }, new[] { "Skeleton", "SkeletonSpear" }) },     // Cripta Real
            { 'y', (new[] { "OrcFrost", "WolfWarrior" }, new[] { "OrcFrost", "WolfWarrior" }) },         // Caverna de Hielo
            { 'z', (new[] { "Skeleton", "SkeletonAxe" }, new[] { "Skeleton", "SkeletonAxe" }) },         // Tumbas bajo la Arena
            { 'A', (new[] { "FireSlug", "FlameSkull" }, new[] { "FireSlug", "FlameSkull" }) },           // Grieta de Magma
            { 'B', (new[] { "OrcCorsair", "GoblinViking" }, new[] { "OrcCorsair", "GoblinViking" }) },   // Cueva de los Corsarios
        };
        public static readonly HashSet<string> NightOnly = new HashSet<string> { "DemonWraith", "KnightFallen" };

        const float MinDist = 11f, MaxDist = 15f, DespawnDist = 28f;
        readonly List<EnemyController> _spawned = new List<EnemyController>();
        readonly List<EnemyController> _sleepingResidents = new List<EnemyController>();
        float _next;
        bool _championTonight;

        public int SpawnedCount { get { _spawned.RemoveAll(e => e == null); return _spawned.Count; } }
        public static int Cap(int threat, bool night) => 2 + threat + (night ? 2 : 0);
        public static float Interval(int threat, bool night) => Mathf.Max(2.5f, 8f - threat * 0.5f - (night ? 1.5f : 0f));
        public static float EliteChance(int threat) => 0.04f + 0.015f * threat;

        void Awake() { Current = this; }
        void OnDestroy() { if (Current == this) Current = null; DayNight.PhaseChanged -= OnPhase; }
        void Start() { DayNight.PhaseChanged += OnPhase; OnPhase(DayNight.IsNight); _next = Time.time + 4f; }

        void Update()
        {
            if (!Enabled || GameManager.Paused || GameManager.Ended || Interior.Current != null) return;
            var p = PlayerController.Current; var wi = WorldInfo.Current;
            if (p == null || wi == null || p.health.IsDead) return;
            // despawn far stragglers
            for (int i = _spawned.Count - 1; i >= 0; i--)
            {
                var e = _spawned[i];
                if (e == null) { _spawned.RemoveAt(i); continue; }
                if (!e.health.IsDead && !e.Engaged && Vector2.Distance(e.transform.position, p.transform.position) > DespawnDist)
                { Destroy(e.gameObject); _spawned.RemoveAt(i); }
            }
            if (Time.time < _next) return;
            var s = GameManager.State;
            bool night = DayNight.IsNight;
            _next = Time.time + Interval(s.Threat, night) * Random.Range(0.8f, 1.2f);
            if (SpawnedCount >= Cap(s.Threat, night)) return;
            TrySpawn(p, wi, s.Threat, night);
        }

        /// <summary>One spawn attempt near the player. Returns the enemy or null (no valid spot / peaceful region).</summary>
        public EnemyController TrySpawn(PlayerController p, WorldInfo wi, int threat, bool night, EnemyRank? force = null)
        {
            for (int attempt = 0; attempt < 10; attempt++)
            {
                Vector2 pos = (Vector2)p.transform.position + Random.insideUnitCircle.normalized * Random.Range(MinDist, MaxDist);
                char region = wi.RegionAt(pos);
                if (!Table.TryGetValue(region, out var t)) continue;
                var list = night ? t.night : t.day;
                if (wi.TownAt(pos) != null || wi.CaveAt(pos) != wi.CaveAt(p.transform.position)) continue;   // never in a town, never through rock
                if (list.Length == 0 || !wi.Walkable(pos) || Physics2D.OverlapCircle(pos + Vector2.up * 0.25f, 0.45f) != null) continue;
                string type = list[Random.Range(0, list.Length)];
                var prefab = GameAssets.I ? GameAssets.I.EnemyPrefab(type) : null;
                if (prefab == null) continue;
                var go = Instantiate(prefab, pos, Quaternion.identity, transform);
                var e = go.GetComponent<EnemyController>();
                e.spawned = true;
                var rank = force ?? EnemyRank.Normal;
                if (force == null)
                {
                    if (night && !_championTonight && threat >= 3 && Random.value < 0.06f) { rank = EnemyRank.Champion; _championTonight = true; }
                    else if (Random.value < EliteChance(threat)) rank = EnemyRank.Elite;
                }
                e.Setup(rank, threat, night);
                _spawned.Add(e);
                if (rank == EnemyRank.Champion) UIRoot.Toast("UN CAMPEÓN ACECHA EN LA OSCURIDAD...", 3f);
                return e;
            }
            return null;
        }

        void OnPhase(bool night)
        {
            if (!night) _championTonight = false;
            var p = PlayerController.Current;
            Vector2 pp = p ? (Vector2)p.transform.position : new Vector2(-999, -999);
            // the sun burns the night creatures; the night ones fade away when far
            for (int i = _spawned.Count - 1; i >= 0; i--)
            {
                var e = _spawned[i];
                if (e == null) { _spawned.RemoveAt(i); continue; }
                bool nightType = NightOnly.Contains(e.typeId);
                if (!night && nightType) { e.Burn(); _spawned.RemoveAt(i); }
                else if (night != nightType && Vector2.Distance(e.transform.position, pp) > 14f) { Destroy(e.gameObject); _spawned.RemoveAt(i); }
            }
            // map residents: day creatures sleep at night (only out of sight)
            if (night)
            {
                foreach (var e in EnemyController.Active.ToArray())
                    if (!e.spawned && !e.isBoss && e.activeAt == ActiveTime.Day && !e.Engaged && Vector2.Distance(e.transform.position, pp) > 14f)
                    { e.gameObject.SetActive(false); _sleepingResidents.Add(e); }
            }
            else
            {
                foreach (var e in _sleepingResidents) if (e != null && !e.health.IsDead) e.gameObject.SetActive(true);
                _sleepingResidents.Clear();
            }
        }
    }
}
