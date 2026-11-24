// Several loaded maps (2026-11-20): the overworld plus one scene per town and for Monte Ceniza.
// Layouts come from Tools/GameGen/maps.py (Assets/Game/Levels/Maps.txt + <MapId>.txt), grounds from
// Tools/ArtGen2/paint_maps.py (Assets/Art/World/Maps/<MapId>/). BuildMapScene (GameBuilder.World.cs) builds each scene;
// this file holds the map-specific parts: catalog, gates, town footprints in the overworld, town NPCs.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace WoodsGame.EditorTools
{
    public static partial class GameBuilder
    {
        const string MapsCatalogRes = GameRoot + "/Resources/MapsCatalog.txt";

        /// <summary>Reads Levels/Maps.txt into MapDB and writes the runtime copy (plus the overworld regions for the world map).</summary>
        static void LoadMapCatalog()
        {
            var lines = File.ReadAllLines(Path.Combine(ProjectRoot, GameRoot, "Levels", "Maps.txt")).ToList();
            var world = File.ReadAllLines(Path.Combine(ProjectRoot, GameRoot, "Levels", "World2.txt"));
            var d = Parse($"{GameRoot}/Levels/World2.txt");
            int r0 = Array.IndexOf(world, "REGIONS");
            foreach (var l in world.Where(l => l.StartsWith("REGIONNAME "))) lines.Add("REGION " + l.Substring(11));
            lines.Add("WORLDREGIONS");
            lines.AddRange(world.Skip(r0 + 1).Take(d.h));
            File.WriteAllText(Path.Combine(ProjectRoot, MapsCatalogRes), string.Join("\n", lines) + "\n");
            AssetDatabase.ImportAsset(MapsCatalogRes, ImportAssetOptions.ForceUpdate);
            MapDB.Parse(lines.ToArray());
            Debug.Log($"[GameBuilder] maps: {string.Join(", ", MapDB.Maps.Select(m => m.id))} · gates {MapDB.Gates.Count}");
        }

        static bool MapHasSpawns(string id) => id == MapDB.World || id.StartsWith("Zone_") || id == "City_Ciudadela";

        // ---------------------------------------------------------------- town footprints inside the overworld
        static IEnumerable<(int x, int row)> GateCells(MapDB.GateDef g, int h)
        {
            int w = Mathf.RoundToInt(g.size.x), gh = Mathf.RoundToInt(g.size.y);
            int x0 = Mathf.RoundToInt(g.center.x - g.size.x / 2f);
            int row0 = h - Mathf.RoundToInt(g.center.y + g.size.y / 2f);
            for (int r = row0; r < row0 + gh; r++)
                for (int x = x0; x < x0 + w; x++) yield return (x, r);
        }

        static bool InArea(MapDB.MapDef m, int x, int row) =>
            m.hasArea && x >= m.area.xMin && x <= m.area.xMax && row >= m.area.yMin && row <= m.area.yMax;

        /// <summary>Cells of the walled towns that become solid in the overworld (everything but their gates).</summary>
        static HashSet<Vector2Int> TownBlockCells(LevelData d)
        {
            var set = new HashSet<Vector2Int>();
            foreach (var m in MapDB.Maps.Where(m => m.hasArea && m.blocksArea))
                for (int row = m.area.yMin; row <= m.area.yMax; row++)
                    for (int x = m.area.xMin; x <= m.area.xMax; x++) set.Add(new Vector2Int(x, row));
            foreach (var g in MapDB.Gates.Where(g => g.map == MapDB.World))
                foreach (var c in GateCells(g, d.h)) set.Remove(new Vector2Int(c.x, c.row));
            return set;
        }

        static string[] BlockTownAreas(LevelData d)
        {
            var rows = d.terrain.Select(r => r.ToCharArray()).ToArray();
            foreach (var m in MapDB.Maps.Where(m => m.hasArea && m.blocksArea))
                for (int row = m.area.yMin; row <= m.area.yMax; row++)
                    for (int x = m.area.xMin; x <= m.area.xMax; x++)
                        if (row >= 0 && row < rows.Length && x >= 0 && x < rows[row].Length) rows[row][x] = 'c';
            return rows.Select(r => new string(r)).ToArray();
        }

        /// <summary>Overworld entities that now live in their own map: the towns' people, shops, camps, chests and the
        /// player start; the volcano's monsters, treasure and the Demon Lord (the volcano itself stays as scenery).</summary>
        static Func<int, int, char, bool> SkipInWorld(LevelData d)
        {
            var areas = MapDB.Maps.Where(m => m.hasArea).ToArray();
            return (x, row, c) =>
            {
                foreach (var m in areas)
                {
                    if (!InArea(m, x, row)) continue;
                    if (m.kind == "city") return "PobdKQBhaCSF$X".IndexOf(c) >= 0;
                    return "obdBhaC".IndexOf(c) >= 0;
                }
                return false;
            };
        }

        /// <summary>Seen from the overworld a town is scenery: its roofs (lit at night), a fence where it had no wall,
        /// and torches at the gates.</summary>
        static void BuildTownSkylines(LevelData d, Transform world, List<(GameObject house, char c, int x, int row, Vector3 foot)> houses)
        {
            var root = new GameObject("TownWalls").transform; root.SetParent(world);
            foreach (var h in houses)
            {
                LightGlow.Attach(h.house.transform, new Vector2(-1.3f, 1.5f), 1.6f, new Color(1f, 0.75f, 0.35f), 0.6f);
                LightGlow.Attach(h.house.transform, new Vector2(1.3f, 1.5f), 1.6f, new Color(1f, 0.75f, 0.35f), 0.6f);
            }
            var fence = WSheet("Nature/fence_16x16.png");
            var gateCells = new HashSet<Vector2Int>(MapDB.Gates.Where(g => g.map == MapDB.World).SelectMany(g => GateCells(g, d.h)).Select(c => new Vector2Int(c.x, c.row)));
            foreach (var m in MapDB.Maps.Where(m => m.hasArea && m.blocksArea))
            {
                for (int row = m.area.yMin; row <= m.area.yMax; row++)
                    for (int x = m.area.xMin; x <= m.area.xMax; x++)
                    {
                        bool ring = row == m.area.yMin || row == m.area.yMax || x == m.area.xMin || x == m.area.xMax;
                        if (!ring || gateCells.Contains(new Vector2Int(x, row)) || WorldInfo.SolidTerrain.IndexOf(d.T(x, row)) >= 0) continue;
                        bool busy = false;                                   // walls/towers already close the ring here
                        for (int dy = -1; dy <= 1 && !busy; dy++)
                            for (int dx = -1; dx <= 1 && !busy; dx++)
                                busy = "#9670".IndexOf(d.E(x + dx, row + dy)) >= 0 && (dx == 0 || dy == 0);
                        if (busy || d.E(x, row) != ' ') continue;
                        bool vertical = x == m.area.xMin || x == m.area.xMax;
                        var s = fence.Length > 3 ? fence[vertical ? 0 : 1] : fence.FirstOrDefault();
                        Deco(root, "fence", s, new Vector3(x + 0.5f, d.h - 1 - row, 0), default, 0, 0);
                    }
            }
        }

        // ---------------------------------------------------------------- gates
        static readonly Dictionary<char, string> SideNames = new Dictionary<char, string> { { 'N', "NORTE" }, { 'S', "SUR" }, { 'W', "OESTE" }, { 'E', "ESTE" } };

        static void BuildGates(string id, LevelData d, Transform world)
        {
            var root = new GameObject("Gates").transform; root.SetParent(world);
            var torch = WSheet("Props/torch_anim_16x34.png");
            foreach (var g in MapDB.Gates.Where(g => g.map == id))
            {
                if (!MapDB.Exists(g.toMap)) continue;          // a boss dungeon not built yet: its entrance stays sealed
                var go = new GameObject("Gate_" + g.id);
                go.transform.SetParent(root, false);
                go.transform.position = g.center;
                var bc = go.AddComponent<BoxCollider2D>(); bc.isTrigger = true; bc.size = g.size;
                var mg = go.AddComponent<MapGate>();
                mg.id = g.id; mg.toMap = g.toMap; mg.toGate = g.toGate; mg.arrival = g.arrival; mg.facing = g.facing;
                var dest = MapDB.Get(g.toMap);
                char side = g.id.Contains(":") ? g.id[g.id.IndexOf(':') + 1] : g.id[0];
                if (g.toMap == id)          // one map: a cave mouth or the stairs back up
                {
                    var cave = MapDB.Place(g.id.Split(':')[0]);
                    mg.label = g.id.EndsWith(":IN") ? (cave != null ? cave.title : "CUEVA") : "SALIDA A LA SUPERFICIE";
                    continue;               // the entrance sprite and the stairs carry their own look: no torches on top
                }
                mg.label = id == MapDB.World ? (dest != null ? dest.title : g.toMap)
                         : "SALIDA " + (SideNames.TryGetValue(side, out var sn) ? sn : "");
                if (id != MapDB.World || torch.Length == 0) continue;
                // two torches flank every town gate in the overworld
                bool horizontal = g.size.x >= g.size.y;
                for (int k = -1; k <= 1; k += 2)
                {
                    Vector2 at = horizontal ? g.center + new Vector2(k * (g.size.x / 2f + 0.5f), -0.5f)
                                            : g.center + new Vector2(0, k * (g.size.y / 2f + 0.5f) - 0.5f);
                    var t = Deco(root, "torch_anim_16x34", torch[0], at, new Vector2(0.35f, 0.25f), 0.15f);
                    Loop(t, torch, 10);
                }
            }
        }

        static Vector2 DefaultArrival(string id)
        {
            var g = id == MapDB.World ? MapDB.Gate(MapDB.World, MapDB.StartMap + ":N0") : null;
            g = g ?? MapDB.Gates.FirstOrDefault(x => x.map == id);
            return g != null ? g.arrival : new Vector2(10, 10);
        }

        // ---------------------------------------------------------------- town contents
        static Dictionary<Vector2Int, string> HouseLines(string[] lines)
        {
            var dict = new Dictionary<Vector2Int, string>();
            foreach (var l in lines.Where(l => l.StartsWith("HOUSE ")))
            {
                var p = l.Split(' ');
                dict[new Vector2Int(int.Parse(p[1]), int.Parse(p[2]))] = p[3];
            }
            return dict;
        }

        // never the player's knights: the townsfolk have their own drawn characters
        static readonly string[] NpcFallback = { "HeroSoldier", "HeroSwordswoman", "HeroPriestess", "HeroRanger", "HeroCrusader", "HeroWizard" };

        /// <summary>Townsfolk from the map file ("NPC x row Class text"). Classes whose art is not built yet use a knight look.</summary>
        static void PlaceTownNpcs(string[] lines, LevelData d, Transform world, Dictionary<Vector2Int, Interior> interiors, string mapId)
        {
            var root = new GameObject("Townsfolk").transform; root.SetParent(world);
            int i = 0;
            foreach (var l in lines.Where(l => l.StartsWith("NPC ")))
            {
                var p = l.Split(new[] { ' ' }, 5);
                int x = int.Parse(p[1]), row = int.Parse(p[2]);
                string cls = p[3];
                if (cls.StartsWith("Npc")) continue;            // named townsfolk come from NpcDB with their routines (PlaceVillagers)
                bool ok = Cell($"{Chars}/{cls}/Idle/{cls}_Idle_Down.png", 0) != null &&
                          AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>($"{Anims}/{cls}/{cls}.controller") != null;
                if (!ok) cls = NpcFallback[i % NpcFallback.Length];
                PlaceNpc(root, cls, new Vector3(x + 0.5f, d.h - 1 - row, 0), p[4]);
                i++;
            }
        }
    }
}
