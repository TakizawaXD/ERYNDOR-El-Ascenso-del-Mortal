// ERYNDOR overworld (Tools/GameGen/world3.py -> World2.txt + World3.json): dungeon entrances, cemeteries, shrines, the
// Great Tree, locked passes with regional keys, lever shortcuts, points of interest for the map, and no main boss outdoors.
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace WoodsGame.EditorTools
{
    public static partial class GameBuilder
    {
        [System.Serializable] class W3Entrance { public string map, kind, name, boss; public int x, row; }
        [System.Serializable] class W3Gate { public string key, name; public int x, row; }
        [System.Serializable] class W3Key { public string key, name; public int x, row; public bool chest; }
        [System.Serializable] class W3Lever { public string id, name; public int x, row; }
        [System.Serializable] class W3Poi { public string kind, name; public int x, row; }
        [System.Serializable] class W3Meta { public W3Entrance[] entrances; public W3Gate[] gates; public W3Key[] keys; public W3Lever[] levers; public W3Poi[] pois; }

        static W3Meta _w3;
        static W3Meta Eryndor
        {
            get
            {
                if (_w3 != null) return _w3;
                string p = Path.Combine(ProjectRoot, GameRoot, "Levels", "World3.json");
                return _w3 = File.Exists(p) ? JsonUtility.FromJson<W3Meta>(File.ReadAllText(p)) : null;
            }
        }

        /// <summary>ERYNDOR rule: main bosses live in their dungeons, never on the overworld.</summary>
        static bool BossesIndoors => Eryndor != null;

        static Vector3 Foot(LevelData d, int x, int row) => new Vector3(x + 0.5f, d.h - 1 - row, 0);

        static void BuildEryndorWorld(LevelData d, Transform world)
        {
            var m = Eryndor;
            if (m == null) return;
            var root = new GameObject("Eryndor").transform; root.SetParent(world);
            var graves = WSheet("Nature/gravestones_16x16.png");
            var shrine = WOne("Structures/shrine_statue.png");
            var tree = WOne("Structures/great_tree.png");
            int n = 0;
            // gravestones, shrines and the Great Tree straight from the entity layer
            for (int row = 0; row < d.h; row++)
                for (int x = 0; x < d.w; x++)
                {
                    char c = d.E(x, row);
                    var foot = Foot(d, x, row);
                    if (c == 'H' && graves.Length > 0)
                    {
                        var g = Deco(root, "gravestone", graves[(x * 7 + row * 3) % graves.Length], foot, new Vector2(0.6f, 0.3f), 0.15f);
                        g.GetComponent<SpriteRenderer>().flipX = ((x + row) & 1) == 1; n++;
                    }
                    else if (c == 'O' && shrine != null)
                    {
                        var s = Deco(root, "shrine_statue", shrine, foot, new Vector2(1.0f, 0.5f), 0.25f);
                        LightGlow.Attach(s.transform, new Vector2(0, 1.6f), 2.2f, new Color(0.45f, 0.8f, 1f), 0.6f, true);
                        var sign = s.AddComponent<Sign>(); sign.promptHeight = 3f;
                        sign.text = "UN SANTUARIO DE LOS PRIMORDIALES. LA RUNA AÚN BRILLA: ALGO VIGILA ESTAS TIERRAS."; n++;
                    }
                    else if (c == 'D' && tree != null)
                    {
                        var t = Deco(root, "great_tree", tree, foot, new Vector2(1.8f, 0.8f), 0.4f);
                        LightGlow.Attach(t.transform, new Vector2(0, 2.4f), 3.6f, new Color(0.45f, 0.85f, 1f), 0.55f, true); n++;
                    }
                }
            // dungeon entrances (the MapGate in front is built from Maps.txt when the dungeon exists)
            foreach (var e in m.entrances ?? new W3Entrance[0])
            {
                string file = e.kind == "crypt" ? "Structures/entrance_crypt.png" : e.kind == "tower" ? "Structures/entrance_blood.png"
                            : e.map.Contains("Escarcha") || e.map.Contains("Helada") ? "Structures/entrance_cave_ice.png" : "Structures/entrance_cave.png";
                var s = WOne(file);
                if (s == null) continue;
                var go = Deco(root, "Entrance_" + e.map, s, Foot(d, e.x, e.row) + new Vector3(0, 0.1f, 0), new Vector2(s.rect.width / 16f * 0.9f, 1.2f), 1.0f);
                var de = go.AddComponent<DungeonEntrance>(); de.toMap = e.map; de.dungeonName = e.name; de.bossFlag = e.boss; de.promptHeight = 1.2f;
                var poi = go.AddComponent<WorldPOI>(); poi.poiName = e.name; poi.kind = "dungeon";
                LightGlow.Attach(go.transform, new Vector2(0, 0.9f), 2.0f, e.kind == "tower" ? new Color(1f, 0.3f, 0.3f) : new Color(0.5f, 0.6f, 1f), 0.6f, true);
                n++;
            }
            // locked passes and regional keys
            var gate = WSheet("Structures/gate_locked_40x44.png");
            foreach (var g in m.gates ?? new W3Gate[0])
            {
                if (gate.Length < 2) break;
                var go = Deco(root, "LockedGate", gate[0], Foot(d, g.x, g.row), new Vector2(1.1f, 0.9f), 0.45f);
                var lg = go.AddComponent<LockedGate>(); lg.keyFlag = g.key; lg.gateName = g.name; lg.openFlag = "open_" + g.key;
                lg.keyName = (m.keys ?? new W3Key[0]).FirstOrDefault(k => k.key == g.key)?.name ?? "LA LLAVE";
                lg.closed = gate[0]; lg.opened = gate[1]; lg.promptHeight = 2.8f;
                var poi = go.AddComponent<WorldPOI>(); poi.poiName = g.name; poi.kind = "gate";
            }
            foreach (var k in m.keys ?? new W3Key[0])
            {
                // the key's chest was placed by the generator on the key spot: give it the key
                var foot = Foot(d, k.x, k.row);
                var chest = world.GetComponentsInChildren<Chest>(true).OrderBy(c => Vector2.Distance(c.transform.position, foot)).FirstOrDefault();
                if (chest != null && Vector2.Distance(chest.transform.position, foot) < 1.5f) { chest.keyId = k.key; chest.keyName = k.name; chest.coins += 20; }
            }
            // lever shortcuts: iron bars across the gap + a lever on the near side
            var bars = WSheet("Structures/gate_lever_32x44.png");
            var lever = WSheet("Props/lever_16x16.png");
            foreach (var l in m.levers ?? new W3Lever[0])
            {
                if (bars.Length < 2 || lever.Length < 2) break;
                var foot = Foot(d, l.x, l.row);
                var go = Deco(root, "LeverGate", bars[0], foot + new Vector3(0, -1f, 0), default, 0);
                var bc = go.AddComponent<BoxCollider2D>(); bc.size = new Vector2(1f, 3f); bc.offset = new Vector2(0, 1.5f);
                var lg = go.AddComponent<LockedGate>(); lg.gateName = l.name; lg.openFlag = "open_" + l.id; lg.closed = bars[0]; lg.opened = bars[1];
                var lv = Deco(root, "Lever", lever[0], foot + new Vector3(1.6f, -0.6f, 0), new Vector2(0.5f, 0.3f), 0.15f);
                var sl = lv.AddComponent<ShortcutLever>(); sl.gate = lg; sl.shortcutName = l.name; sl.up = lever[0]; sl.down = lever[1]; sl.promptHeight = 1.0f;
            }
            // points of interest for the map (towns, villages, cemeteries, shrines, ruins, towers, secrets...)
            foreach (var p in m.pois ?? new W3Poi[0])
            {
                if (p.kind == "dungeon") continue;                     // the entrances carry their own
                var go = new GameObject("POI_" + p.kind); go.transform.SetParent(root, false);
                go.transform.position = Foot(d, p.x, p.row);
                var poi = go.AddComponent<WorldPOI>(); poi.poiName = p.name; poi.kind = p.kind;
            }
            Debug.Log($"[GameBuilder] Eryndor world: {n} landmarks, {m.entrances?.Length} dungeon entrances, {m.gates?.Length} locked gates, {m.levers?.Length} shortcuts, {m.pois?.Length} places");
        }

        /// <summary>A bonfire on the 'F' tile (replaces the camps): planted sword in the embers, kindled once by the player.</summary>
        static void BuildBonfire(Transform parent, Vector3 foot)
        {
            var frames = WSheet("Props/bonfire_anim_32x40.png");
            if (frames.Length < 2) { BuildCampLegacy(parent, foot); return; }
            var go = Deco(parent, "Bonfire", frames[0], foot, new Vector2(1.1f, 0.5f), 0.25f);
            var anim = go.AddComponent<SpriteAnim>(); anim.frames = frames.Skip(1).ToArray(); anim.fps = 10; anim.loop = true; anim.destroyAtEnd = false;
            var fire = go.AddComponent<Campfire>(); fire.promptHeight = 2.4f; fire.frames = frames; fire.campName = "HOGUERA";
            // its glow is added by AddWorldLights (one glow per bonfire, switched off while unlit)
        }
    }
}
