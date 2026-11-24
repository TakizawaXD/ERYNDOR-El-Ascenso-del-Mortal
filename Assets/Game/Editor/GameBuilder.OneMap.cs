// ONE SINGLE MAP (2026-11-21). Tools/GameGen/merge_world.py stamps the towns, Monte Ceniza and the underground caves
// into World2.txt; this file builds the parts that only exist in the merged map: the caves' props, lights and residents
// (PROP / ENEMY lines) and the per-town extras (Cute Fantasy tiles, townsfolk routines, adventurers) inside their areas.
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace WoodsGame.EditorTools
{
    public static partial class GameBuilder
    {
        /// <summary>True when Maps.txt describes the one merged map (TOWN / CAVE lines).</summary>
        static bool OneMap => MapDB.Places.Count > 0;

        static float Fl(string s) => float.Parse(s, CultureInfo.InvariantCulture);

        static readonly string[] SolidProps = { "sarcophagus", "coffin", "pillar", "column", "throne", "brazier", "armor_rack", "crate_stack",
                                                "post_", "urn_", "barrel", "rock", "pedestal", "stairs_arch", "chains" };

        /// <summary>Caves: catacomb props (torches, candles, braziers, sarcophagi, pillars, the throne, the stairs up), their
        /// light, and the creatures that live down there (bosses included). Surface ENEMY lines are the biome residents.</summary>
        static void BuildUnderground(LevelData d, Transform world, string[] lines)
        {
            var root = new GameObject("Underground").transform; root.SetParent(world);
            var actors = world.Find("Actors") ?? world;
            var cache = new Dictionary<string, Sprite[]>();
            Sprite[] Frames(string name)
            {
                if (cache.TryGetValue(name, out var f)) return f;
                string file = WA + "Catacombs/" + name + ".png";
                f = name.Contains("_anim_") ? Sheet(file) : new[] { One(file) };
                if (f == null || f.Length == 0 || f[0] == null) { Debug.LogWarning("[GameBuilder] missing catacomb art " + name); f = new Sprite[0]; }
                return cache[name] = f;
            }
            int props = 0, enemies = 0;
            foreach (var l in lines)
            {
                if (l.StartsWith("PROP "))
                {
                    var p = l.Split(' ');
                    var fr = Frames(p[1]);
                    if (fr.Length == 0) continue;
                    float x = Fl(p[2]), row = Fl(p[3]), fps = p.Length > 4 ? Fl(p[4]) : 0;
                    var foot = new Vector3(x, d.h - row - 0.35f, 0);
                    bool solid = SolidProps.Any(k => p[1].StartsWith(k));
                    float w = fr[0].rect.width / 16f;
                    var go = Deco(root, p[1], fr[0], foot, solid ? new Vector2(Mathf.Max(0.5f, w * 0.8f), 0.45f) : default, 0.2f,
                                  p[1].StartsWith("stairs") ? -5 : 0);
                    if (fps > 0 && fr.Length > 1) Loop(go, fr, fps * (0.85f + (props % 7) * 0.05f));
                    if (p[1].StartsWith("torch")) LightGlow.Attach(go.transform, new Vector2(0, 0.7f), 3.4f, new Color(1f, 0.66f, 0.3f), 0.8f, true);
                    else if (p[1].StartsWith("candle")) LightGlow.Attach(go.transform, new Vector2(0, 0.6f), 1.8f, new Color(1f, 0.8f, 0.45f), 0.6f, true);
                    else if (p[1].StartsWith("brazier")) LightGlow.Attach(go.transform, new Vector2(0, 1.0f), 4.2f, new Color(1f, 0.55f, 0.2f), 0.85f, true);
                    props++;
                }
                else if (l.StartsWith("ENEMY "))
                {
                    var p = l.Split(new[] { ' ' }, 5);
                    string type = p[1];
                    int x = int.Parse(p[2]), row = int.Parse(p[3]);
                    if (type == "Summoner") { PlaceSummoner(d, world, new Vector2Int(x, row)); continue; }
                    if (AssetDatabase.LoadAssetAtPath<GameObject>($"{Prefabs}/{type}.prefab") == null)
                    { Debug.LogWarning("[GameBuilder] no prefab for " + type); continue; }
                    var go = Spawn(type, actors, new Vector3(x + 0.5f, d.h - 1 - row + 0.3f, 0));
                    var e = go.GetComponent<EnemyController>();
                    if (e != null)
                    {
                        bool under = x >= MapDB.SurfaceW;
                        e.activeAt = under || e.isBoss ? ActiveTime.Always : ActiveTime.Day;    // map residents of the surface sleep at night
                        if (p.Length > 4 && !string.IsNullOrEmpty(p[4])) { e.displayName = p[4]; go.name = p[4]; }
                    }
                    enemies++;
                }
            }
            Debug.Log($"[GameBuilder] underground + biome residents: {props} props, {enemies} creatures");
        }

        /// <summary>Per-town extras of the one map, each inside its own area.</summary>
        static void BuildTownsInWorld(LevelData d, Transform world, string[] lines)
        {
            foreach (var t in MapDB.Places.Where(p => p.kind == "town"))
            {
                var area = t.cells;
                // no Cute Fantasy tile layer here: its bright grass and sand paths ended in hard rectangles at the town edges
                PlaceVillagers(t.id, lines, d, world, area);
                PlaceAdventurers(t.id, d, world, area);
            }
        }
    }
}
