// Builds Assets/Game/Scenes/World.unity from Assets/Game/Levels/World2.txt and the painted art in Assets/Art/World.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace WoodsGame.EditorTools
{
    public static partial class GameBuilder
    {
        const string WA = "Assets/Art/World/";

        // entity char -> (sprite file, frame, cell w, cell h, collider w, collider h, collider y, anim fps, sorting order)
        struct Spec
        {
            public string file; public int frame, cw, ch; public float colW, colH, colY, fps; public int order;
            public Spec(string f, float cw_ = 0, float chh = 0, float cy = 0, int frame = -1, int w = 0, int h = 0, float fps = 0, int order = 0)
            { file = f; colW = cw_; colH = chh; colY = cy; this.frame = frame; cw = w; ch = h; this.fps = fps; this.order = order; }
        }

        static readonly Dictionary<char, Spec> Specs = new Dictionary<char, Spec>
        {
            { 'T', new Spec("Nature/tree_oak.png", 0.9f, 0.45f, 0.25f) }, { 'U', new Spec("Nature/tree_oak_b.png", 0.9f, 0.45f, 0.25f) },
            { 't', new Spec("Nature/tree_oak_small.png", 0.7f, 0.4f, 0.2f) }, { 'A', new Spec("Nature/tree_autumn.png", 0.9f, 0.45f, 0.25f) },
            { 'V', new Spec("Nature/tree_corrupt.png", 0.9f, 0.45f, 0.25f) }, { 'u', new Spec("Nature/tree_corrupt_small.png", 0.7f, 0.4f, 0.2f) },
            { 'i', new Spec("Nature/tree_pine.png", 0.6f, 0.4f, 0.2f) }, { 'I', new Spec("Nature/tree_pine_snow.png", 0.6f, 0.4f, 0.2f) },
            { 'k', new Spec("Nature/tree_dead.png", 0.7f, 0.4f, 0.2f) }, { 'Y', new Spec("Nature/tree_palm.png", 0.4f, 0.3f, 0.15f) },
            { 'g', new Spec("Nature/bushes_26x22.png", 1.0f, 0.45f, 0.25f, 0, 26, 22) }, { 'G', new Spec("Nature/bushes_26x22.png", 1.0f, 0.45f, 0.25f, 1, 26, 22) },
            { 'q', new Spec("Nature/bushes_26x22.png", 1.0f, 0.45f, 0.25f, 2, 26, 22) },
            { 'y', new Spec("Nature/plants_16x16.png", 0, 0, 0, 0, 16, 16, 0, -10) }, { 'z', new Spec("Nature/plants_16x16.png", 0, 0, 0, 1, 16, 16, 0, -10) },
            { 'M', new Spec("Nature/plants_16x16.png", 0, 0, 0, 3, 16, 16, 0, -10) }, { 'e', new Spec("Nature/cattails.png", 0, 0, 0, -1, 0, 0, 0, -5) },
            { 'l', new Spec("Nature/lilypads_16x16.png", 0, 0, 0, 0, 16, 16, 0, -20) },
            { 'Z', new Spec("Nature/stump.png", 0.7f, 0.35f, 0.2f) }, { 'n', new Spec("Nature/log.png", 1.6f, 0.45f, 0.25f) },
            { 'r', new Spec("Nature/rock_small.png", 0.7f, 0.4f, 0.2f) }, { 'R', new Spec("Nature/rock_big.png", 1.2f, 0.5f, 0.3f) },
            { 'W', new Spec("Nature/rock_snow.png", 1.2f, 0.5f, 0.3f) },
            { '1', new Spec("Structures/mountain_snow_a.png", 3.0f, 1.2f, 0.6f) }, { '2', new Spec("Structures/mountain_snow_b.png", 2.6f, 1.0f, 0.5f) },
            { '3', new Spec("Structures/mountain_rock.png", 2.4f, 1.0f, 0.5f) }, { 'm', new Spec("Structures/mountain_big_a.png", 4.8f, 1.6f, 0.8f) },
            { '^', new Spec("Structures/mountain_big_b.png", 5.6f, 1.8f, 0.9f) }, { '4', new Spec("Structures/mesa.png", 2.4f, 1.2f, 0.6f) },
            { '5', new Spec("Structures/volcano_big_anim_160x128.png", 8f, 3f, 1.5f, 0, 160, 128, 6) },
            { '6', new Spec("Structures/house_red.png", 4.0f, 1.3f, 0.65f) }, { '7', new Spec("Structures/house_blue.png", 4.0f, 1.3f, 0.65f) },
            { '8', new Spec("Structures/house_thatch.png", 4.0f, 1.3f, 0.65f) }, { '9', new Spec("Structures/castle_tower.png", 2.3f, 1.0f, 0.5f) },
            { '#', new Spec("Structures/castle_wall.png", 2.0f, 0.8f, 0.4f) }, { '0', new Spec("Structures/watchtower.png", 2.0f, 1.0f, 0.5f) },
            { 'J', new Spec("Structures/windmill_anim_76x108.png", 2.4f, 1.0f, 0.5f, 0, 76, 108, 8) },
            { 'j', new Spec("Structures/lighthouse.png", 1.8f, 0.9f, 0.45f) },
            { 'x', new Spec("Structures/dark_tower_anim_44x120.png", 2.4f, 1.0f, 0.5f, 0, 44, 120, 6) },
            { 'N', new Spec("Structures/ruin_wall.png", 2.2f, 0.7f, 0.35f) }, { '!', new Spec("Structures/ruin_pillar.png", 0.8f, 0.5f, 0.25f) },
            { '~', new Spec("Structures/boat.png") },
            { '+', new Spec("Structures/waterfall_anim_32x32.png", 0, 0, 0, 0, 32, 32, 10, -4) },
            { '*', new Spec("Props/props_16x16.png", 0.8f, 0.5f, 0.25f, 3, 16, 16) }, { ';', new Spec("Props/props_16x16.png", 0, 0, 0, 4, 16, 16, 0, -10) },
            { '|', new Spec("Props/torch_anim_16x34.png", 0.35f, 0.25f, 0.15f, 0, 16, 34, 10) },
            { '@', new Spec("Props/well.png", 1.2f, 0.6f, 0.3f) }, { '/', new Spec("Nature/fence_16x16.png", 1f, 0.3f, 0.15f, 1, 16, 16) },
        };

        static Sprite[] WSheet(string rel) => Sheet(WA + rel);
        static Sprite WOne(string rel) => One(WA + rel);

        static void BuildWorldScene() => BuildMapScene(MapDB.World);

        /// <summary>Builds one map scene: the overworld (World2.txt) or a town / zone (Levels/&lt;id&gt;.txt, see GameBuilder.Maps).</summary>
        static void BuildMapScene(string id)
        {
            bool isWorld = id == MapDB.World;
            var def = MapDB.Get(id);
            string file = isWorld ? "World2.txt" : id + ".txt";
            var d = Parse($"{GameRoot}/Levels/{file}");
            var lines = File.ReadAllLines(Path.Combine(ProjectRoot, GameRoot, "Levels", file));
            int r0 = Array.IndexOf(lines, "REGIONS");
            var regionRows = lines.Skip(r0 + 1).Take(d.h).ToArray();
            var regionNames = lines.Where(l => l.StartsWith("REGIONNAME ")).Select(l => l.Substring(11)).ToArray();

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var cam = MakeCamera(def != null && def.kind == "zone" ? new Color32(0x1a, 0x14, 0x1c, 0xff) : new Color32(0x12, 0x4e, 0x89, 0xff));
            cam.gameObject.AddComponent<CameraFollow>();
            cam.gameObject.AddComponent<DayNightLighting>();
            var info = new GameObject("Level").AddComponent<LevelInfo>();
            info.title = isWorld || def == null ? "" : def.title; info.subtitle = isWorld || def == null ? "" : def.subtitle;
            info.bounds = new Rect(0, 0, d.w, d.h);
            var wi = info.gameObject.AddComponent<WorldInfo>();
            wi.regionRows = regionRows; wi.regionNames = regionNames; wi.width = d.w; wi.height = d.h;
            bool one = isWorld && OneMap;                                  // towns, volcano and caves are part of this map
            wi.terrainRows = isWorld && !one ? BlockTownAreas(d) : d.terrain;      // spawns never land inside a town's walls
            wi.surfaceWidth = one ? MapDB.SurfaceW : d.w; wi.surfaceHeight = one ? MapDB.SurfaceH : d.h;
            wi.mapId = id; wi.kind = def != null ? def.kind : "world"; wi.announceRegions = isWorld;
            info.gameObject.AddComponent<DayNight>();
            if (MapHasSpawns(id)) info.gameObject.AddComponent<SpawnDirector>();
            string mapPng = isWorld ? WA + "world_map.png" : WA + $"Maps/{id}/map.png";
            AssetDatabase.ImportAsset(mapPng, ImportAssetOptions.ForceUpdate);
            wi.mapSprite = One(mapPng);

            BuildGround(d, isWorld ? WA + "Ground" : WA + $"Maps/{id}");
            if (id.StartsWith("City_")) BuildCityTiles(d, id);      // towns: Cute Fantasy terrain tiles (GameBuilder.CityTiles.cs)
            BuildCollision(d, isWorld && !one ? TownBlockCells(d) : null);
            var world = new GameObject("World").transform;
            var houses = PlaceWorldEntities(d, world, regionRows, isWorld && !one ? SkipInWorld(d) : null);
            if (one) BuildUnderground(d, world, lines);                         // caves + biome residents (GameBuilder.OneMap.cs)
            AddWaterGlints(d, world);
            if (isWorld && !one) BuildTownSkylines(d, world, houses);           // houses of the towns stay as scenery
            var interiors = isWorld && !one ? new Dictionary<Vector2Int, Interior>()                  // house foot (x,row) -> its room
                                            : BuildInteriors(houses, world, HouseLines(lines), d.w + 40);
            if (!isWorld || one) PlaceTownNpcs(lines, d, world, interiors, id);
            BuildRpgExtras(id, d, world, lines, regionRows, isWorld && !one ? SkipInWorld(d) : null);
            if (one) BuildTownsInWorld(d, world, lines);
            if (isWorld || id.StartsWith("City_")) BuildFarmLife(id, d, world, regionRows, !isWorld);   // wild zones (Monte Ceniza) have no farm animals       // animals, crops, lamps, flowers (GameBuilder.Farm.cs)   // gathering, townsfolk, the Summoner (GameBuilder.Camps.cs)
            BuildGates(id, d, world);
            AddWorldLights(world);
            BuildWeather(d, world);                 // wind sway, grass tufts, rain + spores (GameBuilder.Weather.cs)
            BuildBossArenas(id, d, world);          // boss lairs + the Frost Colossus (GameBuilder.Bosses.cs)
            if (isWorld) BuildEryndorWorld(d, world);               // entrances, graves, shrines, gates, levers, places (GameBuilder.Eryndor.cs)
            Debug.Log($"[GameBuilder] {id}: silhouette colliders: " + FitWorldColliders(world));

            var start = d.entities.SelectMany((r, row) => r.Select((c, x) => (c, x, row))).FirstOrDefault(t => t.c == 'P');
            // the start mark can sit in an area that this map skips (the start village lives in its own town map now),
            // so place the player whenever none was spawned, not only when there is no 'P'
            bool placed = world.GetComponentInChildren<PlayerController>(true) != null;
            Vector2 camAt = start.c == 'P' && placed ? new Vector2(start.x + 0.5f, d.h - 1 - start.row + 0.5f) : DefaultArrival(id);
            if (!placed) Spawn("Player", world.Find("Actors"), camAt);  // no start mark here: the player waits by the first gate
            cam.transform.position = new Vector3(camAt.x, camAt.y + 0.5f, -10);
            EditorSceneManager.SaveScene(scene, $"{ScenesDir}/{id}.unity");
        }

        static void BuildGround(LevelData d, string folder)
        {
            var root = new GameObject("Ground").transform;
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { folder }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                var name = Path.GetFileNameWithoutExtension(path).Split('_');      // ground_cx_cy
                if (name.Length != 3) continue;
                int cx = int.Parse(name[1]), cy = int.Parse(name[2]);
                var s = One(path);
                if (s == null) continue;
                float wU = s.rect.width / 16f, hU = s.rect.height / 16f;
                var go = new GameObject($"ground_{cx}_{cy}");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector3(cx * 32 + wU / 2f, d.h - cy * 32 - hU / 2f, 0);   // 512 px chunks = 32 units
                var sr = go.AddComponent<SpriteRenderer>(); sr.sprite = s; sr.sortingOrder = -100;
            }
        }

        static void BuildCollision(LevelData d, HashSet<Vector2Int> extraSolid = null)
        {
            var grid = new GameObject("Grid", typeof(Grid)).transform;
            var block = Layer(grid, "Collision", 0, render: false);
            var t = BlockTile();
            const string solid = "wOcCLsk";
            const int M = 4;
            for (int row = -M; row < d.h + M; row++)
                for (int x = -M; x < d.w + M; x++)
                {
                    bool outside = x < 0 || row < 0 || x >= d.w || row >= d.h;
                    if (outside || solid.IndexOf(d.T(x, row)) >= 0 || (extraSolid != null && extraSolid.Contains(new Vector2Int(x, row))))
                    {
                        // deep rock / open sea (every neighbour solid too) never touches the player: leave it out, the
                        // composite collider of the one big map stays small
                        bool deep = !outside;
                        for (int dy = -1; dy <= 1 && deep; dy++)
                            for (int dx = -1; dx <= 1 && deep; dx++)
                                if (solid.IndexOf(d.T(x + dx, row + dy)) < 0) deep = false;
                        if (deep && x > 1 && row > 1 && x < d.w - 2 && row < d.h - 2) continue;
                        block.SetTile(new Vector3Int(x, d.h - 1 - row, 0), t);
                    }
                }
            var body = block.gameObject.AddComponent<Rigidbody2D>(); body.bodyType = RigidbodyType2D.Static;
            var tc = block.gameObject.AddComponent<TilemapCollider2D>();
            tc.compositeOperation = Collider2D.CompositeOperation.Merge;
            block.gameObject.AddComponent<CompositeCollider2D>().geometryType = CompositeCollider2D.GeometryType.Polygons;
        }

        static List<(GameObject house, char c, int x, int row, Vector3 foot)> PlaceWorldEntities(LevelData d, Transform world, string[] regionRows,
            Func<int, int, char, bool> skip = null)
        {
            var houses = new List<(GameObject, char, int, int, Vector3)>();
            GameObject Resident(char kind, int x, int row, Vector3 at, Transform parent)
            {
                var go = Spawn(RegionalType(kind, regionRows[row][x]), parent, at);
                go.GetComponent<EnemyController>().activeAt = ActiveTime.Day;     // map residents sleep at night
                return go;
            }
            var actors = new GameObject("Actors").transform; actors.SetParent(world);
            var nature = new GameObject("Nature").transform; nature.SetParent(world);
            var build = new GameObject("Buildings").transform; build.SetParent(world);
            var items = new GameObject("Items").transform; items.SetParent(world);
            var props = WSheet("Props/props_16x16.png");
            var chest = WSheet("Props/chest_anim_16x16.png");
            var fire = WSheet("Props/campfire_anim_20x20.png");
            var seal = Sheet(FX + "fx_demon_summon_circle_anim_32x32.png");
            var cache = new Dictionary<string, Sprite[]>();
            Sprite[] Frames(Spec s)
            {
                if (!cache.TryGetValue(s.file, out var f)) cache[s.file] = f = s.cw > 0 ? WSheet(s.file) : new[] { WOne(s.file) };
                return f;
            }

            for (int row = 0; row < d.h; row++)
                for (int x = 0; x < d.w; x++)
                {
                    char c = d.E(x, row);
                    if (c == ' ' || (skip != null && skip(x, row, c))) continue;
                    if (IsClearing(d, x, row, c)) continue;                             // camps and arenas are clear of trees
                    var foot = new Vector3(x + 0.5f, d.h - 1 - row, 0);
                    var mid = foot + new Vector3(0, 0.3f, 0);
                    switch (c)
                    {
                        case 'P': Spawn("Player", actors, mid); continue;
                        case 'o': case 'b': case 'd': Resident(c, x, row, mid, actors); continue;
                        case 'K': Spawn("OrcChieftain", actors, mid); continue;
                        case 'Q': Spawn("BloodMother", actors, mid); continue;
                        case 'B': Spawn("DemonLord", actors, mid); continue;
                        case 'h': Spawn("Potion", items, mid); continue;
                        case 'a': { var p = Spawn("ArrowBundle", items, mid); p.GetComponent<Pickup>().amount = 6; continue; }
                        case '(': Breakable(Deco(build, "Barrel", props[0], foot, new Vector2(0.75f, 0.55f), 0.3f), null, 0.5f); continue;
                        case ')': Breakable(Deco(build, "Crate", props[1], foot, new Vector2(0.8f, 0.55f), 0.3f), null, 0.5f); continue;
                        case 'S':
                        {
                            var go = Deco(build, "Sign", props[2], foot, new Vector2(0.7f, 0.35f), 0.2f);
                            go.AddComponent<Sign>().text = d.signs.TryGetValue(new Vector2Int(x, row), out var t) ? t : "...";
                            continue;
                        }
                        case 'C':
                        {
                            var go = Deco(build, "Chest", chest[0], foot, new Vector2(0.85f, 0.55f), 0.3f);
                            var ch = go.AddComponent<Chest>();
                            ch.frames = chest; ch.coins = 5 + (x * 7 + row) % 6;
                            ch.potions = (x + row) % 3 == 0 ? 1 : 0; ch.arrows = (x + row) % 3 == 1 ? 8 : 0;
                            if (ch.potions == 0 && ch.arrows == 0) ch.coins += 6;
                            continue;
                        }
                        case 'F': BuildCamp(build, foot); continue;            // campsite (GameBuilder.Camps.cs)
                        case '$':
                        {
                            var go = Deco(build, "Shop", WOne("Props/market_stall.png"), foot, new Vector2(2.2f, 0.6f), 0.3f);
                            go.AddComponent<ShopStall>().promptHeight = 2.5f;
                            continue;
                        }
                        case 'X':
                        {
                            var go = Deco(build, "Seal", seal[0], foot + new Vector3(0, 0.5f, 0), new Vector2(1f, 1f), 0f, -2);
                            Loop(go, seal, 8);
                            go.AddComponent<SealBarrier>();
                            continue;
                        }
                    }
                    if (CastleNode(d, x, row)) continue;                                // walls are joined into runs (GameBuilder.Castle.cs)
                    if (!Specs.TryGetValue(c, out var spec)) continue;
                    var fr = Frames(spec);
                    if (fr == null || fr.Length == 0 || fr[0] == null) { Debug.LogWarning("[GameBuilder] missing sprite " + spec.file); continue; }
                    var parent = "123m^456789#0JjxN!~+".IndexOf(c) >= 0 ? build : nature;
                    var deco = Deco(parent, Path.GetFileNameWithoutExtension(spec.file), fr[Mathf.Max(0, spec.frame)], foot,
                        spec.colW > 0 ? new Vector2(spec.colW, spec.colH) : default, spec.colY, spec.order);
                    if (spec.fps > 0 && fr.Length > 1) Loop(deco, fr, spec.fps * (0.85f + ((x * 13 + row * 7) % 30) / 100f));
                    if (c == '/' && fr.Length > 1 && (d.E(x, row - 1) == '/' || d.E(x, row + 1) == '/') && d.E(x - 1, row) != '/' && d.E(x + 1, row) != '/')
                    {   // a fence running north-south: the vertical post piece, and a thin upright collider
                        var vsr = deco.GetComponent<SpriteRenderer>(); vsr.sprite = fr[0];
                        var vbc = deco.GetComponent<BoxCollider2D>(); if (vbc) { vbc.size = new Vector2(0.3f, 1f); vbc.offset = new Vector2(0, 0.5f); }
                    }
                    if (c == 'l' || c == 'y' || c == 'z' || c == 'g' || c == 'G' || c == 'q')
                        deco.GetComponent<SpriteRenderer>().flipX = ((x + row) & 1) == 1;      // cheap variety
                    if (c == '6' || c == '7' || c == '8') houses.Add((deco, c, x, row, foot));
                }
            BuildCastleWalls(d, build, (x, row, c) => (skip != null && skip(x, row, c)) || IsClearing(d, x, row, c));
            return houses;
        }

        static void AddWaterGlints(LevelData d, Transform world)
        {
            var glint = WSheet("Effects/water_glint_anim_8x8.png");
            if (glint.Length == 0) return;
            var root = new GameObject("WaterGlints").transform; root.SetParent(world);
            var rnd = new System.Random(5);
            for (int row = 0; row < d.h; row++)
                for (int x = 0; x < d.w; x++)
                {
                    char t = d.T(x, row);
                    if ((t != 'w' && t != 'O') || rnd.NextDouble() > 0.035) continue;
                    var go = new GameObject("glint");
                    go.transform.SetParent(root, false);
                    go.transform.position = new Vector3(x + (float)rnd.NextDouble(), d.h - 1 - row + (float)rnd.NextDouble(), 0);
                    var sr = go.AddComponent<SpriteRenderer>(); sr.sprite = glint[0]; sr.sortingOrder = -50;
                    var an = go.AddComponent<SpriteAnim>(); an.frames = glint; an.fps = 6 + (float)rnd.NextDouble() * 6; an.loop = true; an.destroyAtEnd = false;
                }
        }
    }
}
