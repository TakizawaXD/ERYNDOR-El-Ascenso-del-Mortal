using UnityEngine;

namespace WoodsGame
{
    /// <summary>Region grid of the open world: names the area the player is in and marks it discovered.</summary>
    public class WorldInfo : MonoBehaviour
    {
        public static WorldInfo Current { get; private set; }

        [Tooltip("one string per tile row, top row first; each char is a region id")]
        public string[] regionRows;
        [Tooltip("\"id NAME\" entries")]
        public string[] regionNames;
        [Tooltip("terrain letters per row (same layout as regionRows) - used to find walkable spawn points")]
        public string[] terrainRows;
        public int width = 240, height = 160;
        public const string SolidTerrain = "wOcCLsk";
        public Sprite mapSprite;
        [Tooltip("map (scene) id from MapDB: World, City_Valle, City_Ciudadela, City_Puerto, Zone_MonteCeniza")]
        public string mapId = "World";
        public string kind = "world";              // world | city | zone
        [Tooltip("show a title card when you walk into another region (the overworld); towns show their own name on arrival")]
        public bool announceRegions = true;
        public bool IsWorld => kind == "world";
        [Tooltip("the overworld part of the one map (cells); the underground lies to its right")]
        public int surfaceWidth = 240, surfaceHeight = 160;

        /// <summary>Cave of the underground at this point (null on the surface).</summary>
        public MapDB.PlaceDef CaveAt(Vector2 pos) => pos.x >= surfaceWidth ? MapDB.PlaceAt(pos, "cave") : null;
        /// <summary>Town (or Monte Ceniza, kind "zone") at this point.</summary>
        public MapDB.PlaceDef TownAt(Vector2 pos) => pos.x < surfaceWidth ? MapDB.PlaceAt(pos, "town") : null;
        public bool Underground(Vector2 pos) => pos.x >= surfaceWidth;

        /// <summary>The player stands in a cave right now (caves behave like big interiors: dark, no weather, own map).</summary>
        public static MapDB.PlaceDef PlayerCave
        {
            get
            {
                var wi = Current; var p = PlayerController.Current;
                return wi != null && p != null ? wi.CaveAt(p.transform.position) : null;
            }
        }
        public static bool PlayerUnderground
        {
            get { var wi = Current; var p = PlayerController.Current; return wi != null && p != null && wi.Underground(p.transform.position); }
        }

        /// <summary>What the camera may show around this point: the surface, or only the cave you are in.</summary>
        public Rect ViewBounds(Vector2 pos)
        {
            var cave = CaveAt(pos);
            if (cave != null) { var b = cave.Bounds; return new Rect(b.xMin - 1, b.yMin - 1, b.width + 2, b.height + 2); }
            return new Rect(0, height - surfaceHeight, surfaceWidth, surfaceHeight);
        }

        char _current = '\0';
        float _next;

        void Awake() { Current = this; }
        void OnDestroy() { if (Current == this) Current = null; }

        public char RegionAt(Vector2 world)
        {
            int x = Mathf.FloorToInt(world.x), row = height - 1 - Mathf.FloorToInt(world.y);
            if (regionRows == null || row < 0 || row >= regionRows.Length || x < 0 || x >= regionRows[row].Length) return '\0';
            return regionRows[row][x];
        }

        /// <summary>Open ground (not water, cliff, lava, wall). Out of the map = false.</summary>
        public bool Walkable(Vector2 world)
        {
            int x = Mathf.FloorToInt(world.x), row = height - 1 - Mathf.FloorToInt(world.y);
            if (terrainRows == null || row < 0 || row >= terrainRows.Length || x < 0 || x >= terrainRows[row].Length) return false;
            return SolidTerrain.IndexOf(terrainRows[row][x]) < 0;
        }

        public string NameOf(char id)
        {
            if (regionNames != null)
                foreach (var n in regionNames) if (n.Length > 2 && n[0] == id) return n.Substring(2);
            return "";
        }

        void Update()
        {
            if (Time.time < _next) return;
            _next = Time.time + 0.3f;
            var p = PlayerController.Current;
            if (p == null || Interior.Current != null) return;
            char r = RegionAt(p.transform.position);
            if (r == '\0' || r == _current) return;
            bool first = _current == '\0';
            _current = r;
            bool isNew = GameManager.State.Set("region_" + r);
            if (announceRegions && (!first || isNew)) UIRoot.TitleCard(NameOf(r), isNew ? "NUEVA REGIÓN DESCUBIERTA" : "");
            else if (!announceRegions && isNew) UIRoot.Toast("NUEVA REGIÓN DESCUBIERTA: " + NameOf(r), 2.4f);
            if (isNew) { Quests.Refresh(); if (!first) Sfx.Jingle("discover"); }
        }
    }
}
