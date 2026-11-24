// Town maps get the terrain tiles of the user's "Cute Fantasy (Free)" pack (Assets/Art/External/CuteFantasyTiles,
// non-commercial licence) instead of the painted ground: grass, sandy paths, water with grass banks, beaches, cliffs.
// The open world keeps its painted ground. Bridges and docks keep the painted deck (holes in this layer).
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace WoodsGame.EditorTools
{
    public static partial class GameBuilder
    {
        const string CFT = "Assets/Art/External/CuteFantasyTiles/";
        static readonly Dictionary<Sprite, Tile> _cfTiles = new Dictionary<Sprite, Tile>();

        enum Mat { Grass, Sand, Water, Cliff, Keep }

        static Mat MatOf(char t)
        {
            switch (t)
            {
                case 'w': case 'O': case 's': return Mat.Water;
                case '_': case 'p': case 'd': case 'a': return Mat.Sand;
                case 'c': case 'C': case 'k': return Mat.Cliff;
                case '=': case 'H': case 'D': return Mat.Keep;          // bridges / docks stay painted
                default: return Mat.Grass;
            }
        }

        static Tile CFTile(Sprite s)
        {
            if (s == null) return null;
            if (_cfTiles.TryGetValue(s, out var t) && t != null) return t;
            string dir = GameRoot + "/Tiles/CuteFantasy";
            Ensure(dir);
            string p = $"{dir}/{s.name}.asset";
            t = AssetDatabase.LoadAssetAtPath<Tile>(p);
            if (t == null) { t = ScriptableObject.CreateInstance<Tile>(); AssetDatabase.CreateAsset(t, p); }
            t.sprite = s; t.colliderType = Tile.ColliderType.None;
            EditorUtility.SetDirty(t);
            return _cfTiles[s] = t;
        }

        /// <summary>13-piece autotile of the pack sheets (3 columns: 3x3 border block, 2x2 inner corners, 3 fills).
        /// in(x,y) says whether a neighbour belongs to the same material.</summary>
        static Sprite AutoTile(Sprite[] sheet, System.Func<int, int, bool> inside, int x, int row, int cols, int innerCol, int innerRow, int fillRow, int seed)
        {
            bool N = inside(x, row - 1), S = inside(x, row + 1), W = inside(x - 1, row), E = inside(x + 1, row);
            int c = !W && E ? 0 : !E && W ? 2 : 1;
            int r = !N && S ? 0 : !S && N ? 2 : 1;
            if (c != 1 || r != 1) return sheet[r * cols + c];
            // inner corners: the other material only on a diagonal
            if (!inside(x + 1, row + 1)) return sheet[innerRow * cols + innerCol];          // grass at bottom-right
            if (!inside(x - 1, row + 1)) return sheet[innerRow * cols + innerCol + 1];      // bottom-left
            if (!inside(x + 1, row - 1)) return sheet[(innerRow + 1) * cols + innerCol];    // top-right
            if (!inside(x - 1, row - 1)) return sheet[(innerRow + 1) * cols + innerCol + 1];// top-left
            if (fillRow >= 0 && Rand01(x, row, seed) < 0.18f)                               // decorated fills now and then
                return sheet[fillRow * cols + (int)(Rand01(x, row, seed + 1) * 3) % 3];
            return sheet[cols + 1];
        }

        static void BuildCityTiles(LevelData d, string id, RectInt? area = null)
        {
            var path = Sheet(CFT + "cf_path_16x16.png"); var water = Sheet(CFT + "cf_water_16x16.png");
            var cliff = Sheet(CFT + "cf_cliff_16x16.png"); var beach = Sheet(CFT + "cf_beach_16x16.png");
            var grass = One(CFT + "cf_grass.png"); var waterMid = One(CFT + "cf_water_mid.png");
            if (path.Length < 18 || water.Length < 18 || cliff.Length < 18 || beach.Length < 10 || grass == null)
            { Debug.LogWarning("[GameBuilder] Cute Fantasy tiles missing - run Tools/ArtGen2/import_cute_fantasy.py"); return; }

            var grid = new GameObject("TownTiles_" + id, typeof(Grid)).transform;
            var ground = Layer(grid, "TownGround", -97);
            var over = Layer(grid, "TownEdges", -96);
            Mat M(int x, int row) => MatOf(d.T(x, row));
            int n = 0;
            int ry0 = area.HasValue ? area.Value.yMin : -2, ry1 = area.HasValue ? area.Value.yMax + 1 : d.h + 2;   // one map: only the town's cells
            int rx0 = area.HasValue ? area.Value.xMin : -2, rx1 = area.HasValue ? area.Value.xMax + 1 : d.w + 2;
            for (int row = ry0; row < ry1; row++)
                for (int x = rx0; x < rx1; x++)
                {
                    var cell = new Vector3Int(x, d.h - 1 - row, 0);
                    var m = M(x, row);
                    if (m == Mat.Keep) continue;
                    ground.SetTile(cell, CFTile(grass));
                    Sprite s = null;
                    switch (m)
                    {
                        case Mat.Sand:
                        {
                            bool nearWater = M(x + 1, row) == Mat.Water || M(x - 1, row) == Mat.Water || M(x, row + 1) == Mat.Water || M(x, row - 1) == Mat.Water;
                            if (nearWater)      // a beach: sand island edges over water
                                s = AutoTile(beach, (a, b) => M(a, b) != Mat.Water, x, row, 5, 3, 0, -1, 71);
                            else                // a path through the grass (water counts as path so no grass rim appears there)
                                s = AutoTile(path, (a, b) => { var k = M(a, b); return k == Mat.Sand || k == Mat.Water || k == Mat.Keep; }, x, row, 3, 0, 3, 5, 72);
                            break;
                        }
                        case Mat.Water:
                        {
                            bool nearGrass = false;
                            for (int dy = -1; dy <= 1 && !nearGrass; dy++)
                                for (int dx = -1; dx <= 1; dx++) if (M(x + dx, row + dy) == Mat.Grass || M(x + dx, row + dy) == Mat.Cliff) { nearGrass = true; break; }
                            s = nearGrass ? AutoTile(water, (a, b) => { var k = M(a, b); return k == Mat.Water || k == Mat.Sand || k == Mat.Keep; }, x, row, 3, 0, 3, 5, 73)
                                          : (Rand01(x, row, 74) < 0.12f ? water[15 + (int)(Rand01(x, row, 75) * 3) % 3] : waterMid);
                            break;
                        }
                        case Mat.Cliff:
                            s = AutoTile(cliff, (a, b) => M(a, b) == Mat.Cliff, x, row, 3, 0, 3, 5, 76);
                            break;
                        default: break;                    // plain grass (flowers come from the farm-life layer)
                    }
                    if (s != null) { over.SetTile(cell, CFTile(s)); n++; }
                }
            AssetDatabase.SaveAssets();
            Debug.Log($"[GameBuilder] {id}: Cute Fantasy town tiles ({n} edge/terrain tiles)");
        }
    }
}
