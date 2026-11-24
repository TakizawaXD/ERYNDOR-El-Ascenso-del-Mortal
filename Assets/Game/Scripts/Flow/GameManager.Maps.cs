using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace WoodsGame
{
    /// <summary>Several loaded maps: travelling through gates, where you appear, what the save remembers and which map
    /// residents stay defeated when you come back to a map.</summary>
    public partial class GameManager
    {
        /// <summary>Gate id to appear at in the next loaded map (set by Travel, consumed by the player on Awake).</summary>
        public static string PendingGate { get; private set; }
        /// <summary>Map (scene) that is loaded right now.</summary>
        public static string CurrentMap => SceneManager.GetActiveScene().name;

        // ------------------------------------------------------------ loading
        public static void LoadMap(string map, string gate)
        {
            if (!MapDB.Exists(map)) map = MapDB.Exists(MapDB.StartMap) ? MapDB.StartMap : WorldScene;
            PendingGate = gate;
            State.map = map;
            I.StartCoroutine(I.LoadRoutine(map));
        }

        /// <summary>Walk through a gate: fade, load the destination map, appear on its matching gate. State travels with you.</summary>
        public static void Travel(string map, string gate)
        {
            if (_transitioning || _ended || string.IsNullOrEmpty(map)) return;
            var p = PlayerController.Current;
            if (p != null) State.hp = p.health.hp;
            if (map == CurrentMap) { I.StartCoroutine(I.Teleport(gate)); return; }   // one single map: stairs, cave mouths
            Sfx.Play("gate", 0.8f);
            LoadMap(map, gate);
        }

        /// <summary>A gate inside the same map (a cave entrance and its stairs): fade, move, fade back - no loading.</summary>
        IEnumerator Teleport(string gateId)
        {
            var g = MapGate.Find(gateId);
            if (g == null) yield break;
            _transitioning = true;
            var p = PlayerController.Current;
            bool down = WorldInfo.Current != null && WorldInfo.Current.Underground(g.arrival);
            Sfx.Play(down ? "door_open" : "gate", 0.8f);
            yield return UIRoot.Fade(1f, 0.3f);
            if (p != null)
            {
                var rb = p.GetComponent<Rigidbody2D>();
                rb.position = g.arrival; rb.linearVelocity = Vector2.zero; p.transform.position = g.arrival;
                p.Face(g.facing);
            }
            MapGate.BlockUntil = Time.time + 1.2f;
            CameraFollow.SnapTo(g.arrival + Vector2.up * 0.5f);
            yield return null;
            yield return UIRoot.Fade(0f, 0.3f);
            _transitioning = false;
            var cave = WorldInfo.Current != null ? WorldInfo.Current.CaveAt(g.arrival) : null;
            if (cave != null) UIRoot.TitleCard(cave.title, "BAJO TIERRA");
        }

        /// <summary>Map a saved game continues in: the map of its last rest point. Old single-map saves continue in the
        /// overworld, or in the start village if their rest point was inside a town (its houses moved to the town map).</summary>
        public static string ResumeMap(PlayerState s)
        {
            if (s == null || s.saveX < 0) return MapDB.StartMap;
            // saves from the time of several maps: a rest point in a town / Monte Ceniza moves to where that place now
            // lies in the one map; one in the old, smaller overworld cannot be placed again -> start at the village
            if (!string.IsNullOrEmpty(s.saveMap) && s.saveMap != WorldScene && MapDB.MergedOffset(s.saveMap, out var off))
            { s.saveX += off.x; s.saveY += off.y; s.saveMap = WorldScene; s.Set("world_v3"); return WorldScene; }
            if (!s.Has("world_v3")) { s.saveX = s.saveY = -1; s.saveMap = WorldScene; s.Set("world_v3"); return WorldScene; }
            if (MapDB.Exists(s.saveMap)) return s.saveMap;
            var area = MapDB.AreaAt(new Vector2(s.saveX, s.saveY));
            if (area != null && area.blocksArea) { s.saveX = s.saveY = -1; return MapDB.StartMap; }
            s.saveMap = WorldScene;
            return WorldScene;
        }

        /// <summary>Rest points (campfire, bed, altar): respawn and continue here.</summary>
        public static void SetRestPoint(Vector2 spot, string map)
        {
            State.saveX = spot.x; State.saveY = spot.y; State.Set("world_v3");
            State.saveMap = string.IsNullOrEmpty(map) ? CurrentMap : map;
            State.map = State.saveMap;
        }

        /// <summary>Where the player starts in a freshly loaded map: on the gate it came through, else on its rest point
        /// if it belongs to this map. False = keep the position placed by the builder.</summary>
        public static bool ArrivalPoint(string map, out Vector2 at, out Vector2 facing)
        {
            at = Vector2.zero; facing = Vector2.down;
            if (_resumeAt.HasValue && map == WorldScene)          // Continue after an autosave: right where you were
            {
                at = _resumeAt.Value; _resumeAt = null; PendingGate = null; State.map = map;
                return true;
            }
            if (!string.IsNullOrEmpty(PendingGate))
            {
                var g = MapGate.Find(PendingGate);
                PendingGate = null;
                if (g != null) { at = g.arrival; facing = g.facing; State.map = map; return true; }
            }
            var s = State;
            if (s.saveX >= 0 && (s.saveMap == map || (string.IsNullOrEmpty(s.saveMap) && map == WorldScene)))
            {
                at = new Vector2(s.saveX, s.saveY); State.map = map;
                return true;
            }
            State.map = map;
            return false;
        }

        // ------------------------------------------------------------ defeated map residents
        static string DefeatKey(string map, Vector2 home) =>
            map + "|" + home.x.ToString("0.0", CultureInfo.InvariantCulture) + "|" + home.y.ToString("0.0", CultureInfo.InvariantCulture);

        static void RecordDefeat(EnemyController e)
        {
            if (e == null || e.spawned || e.isBoss) return;
            string key = DefeatKey(e.gameObject.scene.name, e.Home);
            ForgetDefeat(key);
            float until = State.TotalMinutes + RespawnSeconds * DayNight.GameMinutesPerSecond;
            State.defeated.Add(key + "|" + until.ToString("0.0", CultureInfo.InvariantCulture));
        }

        static void ForgetDefeat(string key)
        {
            State.defeated.RemoveAll(d => d.StartsWith(key + "|"));
        }

        /// <summary>Real seconds until a resident killed earlier comes back (0 = not defeated / already back).</summary>
        public static float DefeatedFor(string map, Vector2 home)
        {
            string key = DefeatKey(map, home) + "|";
            foreach (var d in State.defeated)
                if (d.StartsWith(key) && float.TryParse(d.Substring(key.Length), NumberStyles.Float, CultureInfo.InvariantCulture, out var until))
                    return Mathf.Max(0, (until - State.TotalMinutes) / DayNight.GameMinutesPerSecond);
            return 0;
        }

        static void OnMapLoaded(Scene s)
        {
            if (s.name == MenuScene || !MapDB.Exists(s.name)) return;
            foreach (var sr in Object.FindObjectsByType<SpriteRenderer>(FindObjectsInactive.Include, FindObjectsSortMode.None))
                if (sr.sortingOrder > -50 && sr.sortingOrder < 50) sr.spriteSortPoint = SpriteSortPoint.Pivot;   // depth by the feet
            State.map = s.name;
            I.StartCoroutine(I.RestoreDefeated(s.name));
        }

        /// <summary>One frame after a map loads (enemies have run Start): residents still dead in this save stay dead
        /// and come back when their timer runs out, even if you left the map in between.</summary>
        IEnumerator RestoreDefeated(string map)
        {
            yield return null;
            var now = State.TotalMinutes;
            State.defeated.RemoveAll(d =>
            {
                int k = d.LastIndexOf('|');
                return k < 0 || !float.TryParse(d.Substring(k + 1), NumberStyles.Float, CultureInfo.InvariantCulture, out var u) || u <= now;
            });
            if (SceneManager.GetActiveScene().name != map) yield break;
            foreach (var e in new List<EnemyController>(EnemyController.Active))
            {
                if (e == null || e.spawned || e.isBoss) continue;
                float wait = DefeatedFor(map, e.Home);
                if (wait <= 0) continue;
                _enemies.Remove(e);
                e.gameObject.SetActive(false);
                StartCoroutine(RespawnRoutine(e, wait));
            }
        }

        IEnumerator RespawnRoutine(EnemyController e, float delay)
        {
            yield return new WaitForSeconds(delay);
            while (e != null)
            {
                var p = PlayerController.Current;
                if (p == null || Vector2.Distance(p.transform.position, e.Home) > 14f)
                {
                    ForgetDefeat(DefeatKey(e.gameObject.scene.name, e.Home));
                    e.Respawn();
                    yield break;
                }
                yield return new WaitForSeconds(5f);   // never pop in front of the player
            }
        }
    }
}
