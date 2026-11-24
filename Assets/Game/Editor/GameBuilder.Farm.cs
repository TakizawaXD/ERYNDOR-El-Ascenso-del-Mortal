// Farm life from the user's "Cute Fantasy (Free)" pack (Assets/Art/External/CuteFantasy, non-commercial licence):
// animals with their own behaviour, crop fields on farmland, street lamps in towns, wild flowers and oaks.
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace WoodsGame.EditorTools
{
    public static partial class GameBuilder
    {
        const string CF = "Assets/Art/External/CuteFantasy/";

        // species -> (hp, collider radius, walk speed, drops, count, biomes (region ids), herd size)
        static readonly (string id, int hp, float r, float speed, string[] drops, int n, string regions, int herd)[] Animals =
        {
            ("chicken", 2, 0.16f, 1.1f, new[] { "carne" }, 1, "aj", 4),
            ("pig", 4, 0.26f, 0.8f, new[] { "carne" }, 2, "ab", 3),
            ("cow", 6, 0.34f, 0.6f, new[] { "carne", "cuero" }, 1, "acb", 3),
            ("sheep", 4, 0.28f, 0.7f, new[] { "tela", "carne" }, 1, "abe", 4),
            ("cat", 3, 0.16f, 0.9f, new string[0], 0, "", 1),          // the kittens: friends, never loot
            ("catgrey", 3, 0.16f, 0.9f, new string[0], 0, "", 1),
        };

        /// <summary>Orange or grey-and-white, tame or shy (roughly half of the cats will not let you touch them).</summary>
        static string CatKind(int x, int row) => (Rand01(x, row, 61) < 0.5f ? "cat" : "catgrey") + (Rand01(x, row, 62) < 0.45f ? "_shy" : "");

        static string Sound(string id) => Sfx.AnimalSound(id);      // cow, pig, chicken, sheep, cat_meow (Tools/GameGen/sfx2.py)

        /// <summary>Animal prefabs (called while building prefabs).</summary>
        static void BuildAnimalPrefabs()
        {
            foreach (var a in Animals)
            {
                var sheet = Sheet(CF + $"animal_{a.id}_32x32.png");
                if (sheet.Length < 4) { Debug.LogWarning("[GameBuilder] missing animal sheet " + a.id); continue; }
                var go = new GameObject("Animal_" + a.id);
                var rb = go.AddComponent<Rigidbody2D>(); rb.gravityScale = 0; rb.freezeRotation = true; rb.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
                var col = go.AddComponent<CircleCollider2D>(); col.radius = a.r; col.offset = new Vector2(0, a.r);
                go.AddComponent<Health>();
                var spr = new GameObject("Sprite"); spr.transform.SetParent(go.transform, false);
                var sr = spr.AddComponent<SpriteRenderer>(); sr.sprite = sheet[0];
                var an = go.AddComponent<Animal>();
                an.species = a.id; an.idle = new[] { sheet[0], sheet[1] }; an.walk = new[] { sheet[2], sheet[3] };
                an.maxHP = a.hp; an.walkSpeed = a.speed; an.drops = a.drops; an.dropCount = a.n; an.sound = Sound(a.id);
                an.roam = a.id == "chicken" ? 2f : 3.5f;
                if (a.id.StartsWith("cat"))
                {
                    an.species = "cat"; an.friendly = true; an.fleeSpeed = 3.8f; an.roam = 2.5f;
                    if (sheet.Length >= 6) an.pet = new[] { sheet[4], sheet[5] };
                    an.heart = One(CF + "fx_heart.png");
                    go.AddComponent<PetAnimal>();
                    // a second, shy version of each coat: same cat, never lets you near
                    var shy = Object.Instantiate(go); shy.name = "Animal_" + a.id + "_shy";
                    shy.GetComponent<Animal>().shy = true;
                    SavePrefab(shy, "Animal_" + a.id + "_shy");
                }
                SavePrefab(go, "Animal_" + a.id);
            }
        }

        static bool OpenGround(LevelData d, int x, int row) =>
            x > 1 && row > 1 && x < d.w - 2 && row < d.h - 2 && d.E(x, row) == ' ' && ".fna_".IndexOf(d.T(x, row)) >= 0;

        static uint Hash(int x, int y, int s) { unchecked { uint h = (uint)(x * 374761393 + y * 668265263 + s * 974634761); h = (h ^ (h >> 13)) * 1274126177; return h ^ (h >> 16); } }
        static float Rand01(int x, int y, int s) => (Hash(x, y, s) & 0xffff) / 65535f;

        /// <summary>Places the farm-life layer in one map.</summary>
        static void BuildFarmLife(string id, LevelData d, Transform world, string[] regionRows, bool town)
        {
            var root = new GameObject("FarmLife").transform; root.SetParent(world);
            var farm = Sheet(CF + "cf_farmland_16x16.png");
            var crops = Sheet(CF + "cf_crops_16x16.png");
            var flora = Sheet(CF + "cf_flora_16x16.png");
            var oaks = Sheet(CF + "cf_oak_small_32x48.png");
            var oak = One(CF + "cf_oak_tree.png");
            var lamp = One(CF + "cf_lamp.png");
            var log = One(CF + "cf_log.png"); var stump = One(CF + "cf_stump.png");
            char R(int x, int row) => regionRows != null && row >= 0 && row < regionRows.Length && x >= 0 && x < regionRows[row].Length ? regionRows[row][x] : 'a';
            int animals = 0, cropsN = 0, lamps = 0, plants = 0;
            var farmTiles = new List<Vector2Int>();

            for (int row = 0; row < d.h; row++)
                for (int x = 0; x < d.w; x++)
                {
                    char t = d.T(x, row);
                    var foot = new Vector3(x + 0.5f, d.h - 1 - row, 0);
                    // farmland plots (3x3 autotile) + crops in rows
                    if (t == 'F' && farm.Length >= 9)
                    {
                        int c = d.T(x - 1, row) != 'F' ? 0 : d.T(x + 1, row) != 'F' ? 2 : 1;
                        int r = d.T(x, row - 1) != 'F' ? 0 : d.T(x, row + 1) != 'F' ? 2 : 1;
                        Deco(root, "farmland", farm[r * 3 + c], foot, default, 0, -90);
                        farmTiles.Add(new Vector2Int(x, row));
                        if (d.E(x, row) == ' ' && crops.Length >= 8 && (x + row) % 2 == 0)
                        {
                            bool wheat = (x / 4 + row / 3) % 2 == 0;
                            int stage = 1 + (int)(Rand01(x, row, 3) * 3);
                            var cr = Deco(root, wheat ? "wheat" : "carrot", crops[(wheat ? 4 : 0) + stage], foot + new Vector3(0, 0.1f, 0), default, 0, 0);
                            cropsN++;
                        }
                        continue;
                    }
                    // street lamps along town streets (warm light at night)
                    if (town && lamp != null && "p_".IndexOf(t) >= 0 && d.E(x, row) == ' ' && ".fn".IndexOf(d.T(x, row + 1)) >= 0 && (x % 7 == 0))
                    {
                        var l = Deco(root, "lamp", lamp, foot, new Vector2(0.3f, 0.2f), 0.1f, 0);
                        LightGlow.Attach(l.transform, new Vector2(0, 2.4f), 3.4f, new Color(1f, 0.78f, 0.4f), 0.75f);
                        lamps++;
                        continue;
                    }
                    if (!OpenGround(d, x, row)) continue;
                    char reg = R(x, row);
                    float h = Rand01(x, row, 11);
                    bool temperate = "abcij".IndexOf(reg) >= 0;
                    // wild flowers and grass tufts in the temperate lands, mushrooms in the woods
                    if (temperate && h < 0.07f && flora.Length >= 15)
                    {
                        int k = reg == 'b' && h < 0.012f ? 14 : (int)(Rand01(x, row, 12) * 14);
                        var f = Deco(root, "flora", flora[k], foot + new Vector3(Rand01(x, row, 13) - 0.5f, Rand01(x, row, 14) * 0.6f, 0), default, 0, -10);
                        f.GetComponent<SpriteRenderer>().flipX = (x & 1) == 1;
                        plants++;
                    }
                    // a few extra oaks in the valley and the west wood, logs and stumps in the forest
                    else if (!town && (reg == 'a' || reg == 'b') && h > 0.996f && oak != null)
                        Deco(root, "oak", Rand01(x, row, 15) < 0.5f ? oak : oaks.ElementAtOrDefault(1 + (int)(Rand01(x, row, 16) * 2)) ?? oak, foot, new Vector2(0.8f, 0.4f), 0.2f, 0);
                    else if (!town && reg == 'b' && h > 0.992f)
                        Deco(root, "log", Rand01(x, row, 17) < 0.5f ? log : stump, foot, new Vector2(0.8f, 0.35f), 0.18f, 0);
                }

            // animals: chickens and pigs around the farms, cows and sheep in herds on the meadows
            var placed = new List<Vector2>();
            bool Free(Vector2 p) => placed.All(q => Vector2.Distance(p, q) > 0.9f);
            void Herd(string sp, Vector2 c, int n)
            {
                for (int i = 0, tries = 0; i < n && tries < n * 6; tries++)
                {
                    var p = c + new Vector2(Rand01((int)c.x + tries, (int)c.y, 21) * 3 - 1.5f, Rand01((int)c.x, (int)c.y + tries, 22) * 3 - 1.5f);
                    int x = Mathf.FloorToInt(p.x), row = d.h - 1 - Mathf.FloorToInt(p.y);
                    if (!OpenGround(d, x, row) || !Free(p)) continue;
                    Spawn("Animal_" + sp, root, p); placed.Add(p); animals++; i++;
                }
            }
            // farm animals near each farm plot (one group per ~9 farm tiles)
            for (int i = 0; i < farmTiles.Count; i += 9)
            {
                var ft = farmTiles[i];
                var c = new Vector2(ft.x + 0.5f, d.h - 1 - ft.y) + new Vector2(0, -2.5f);
                Herd(i % 18 == 0 ? "chicken" : "pig", c, i % 18 == 0 ? 4 : 2);
            }
            if (!town)
            {
                // meadow herds: scan a coarse grid for open land in each species' biomes
                for (int row = 6; row < d.h - 6; row += 9)
                    for (int x = 6; x < d.w - 6; x += 11)
                    {
                        if (Rand01(x, row, 31) > 0.16f || !OpenGround(d, x, row)) continue;
                        char reg = R(x, row);
                        var sp = Animals.Where(a => a.id != "chicken" && a.regions.IndexOf(reg) >= 0).ToArray();
                        if (sp.Length == 0) continue;
                        var a = sp[(int)(Rand01(x, row, 32) * sp.Length) % sp.Length];
                        Herd(a.id, new Vector2(x + 0.5f, d.h - 1 - row), a.herd);
                    }
            }
            else if (farmTiles.Count == 0)
            {
                // towns without fields still have hens pecking around
                for (int k = 0, row = 4; row < d.h - 4 && k < 3; row += 7)
                    for (int x = 4; x < d.w - 4 && k < 3; x += 9)
                        if (OpenGround(d, x, row) && Rand01(x, row, 41) < 0.3f) { Herd("chicken", new Vector2(x + 0.5f, d.h - 1 - row), 3); k++; }
            }
            // kittens: four in every town (one tame right by the arrival point), one by every third farm in the wild
            int cats = 0;
            if (town)
            {
                // around where you arrive (the start mark, else the middle of town): the first one tame and a few steps
                // away so you meet it, the others spread over the streets 6-16 tiles out
                var start = d.entities.SelectMany((r, rr) => r.Select((c, xx) => (c, xx, rr))).FirstOrDefault(t => t.c == 'P');
                Vector2Int hub = start.c == 'P' ? new Vector2Int(start.xx, start.rr) : new Vector2Int(d.w / 2, d.h / 2);
                var spots = new List<Vector2Int>();
                for (int row = 2; row < d.h - 2; row++)
                    for (int x = 2; x < d.w - 2; x++)
                    {
                        float dist = Vector2.Distance(new Vector2(x, row), hub);
                        if (dist >= 2.5f && dist <= 16f && OpenGround(d, x, row)) spots.Add(new Vector2Int(x, row));
                    }
                var chosen = new List<Vector2Int>();
                var near = spots.Where(v => Vector2.Distance(v, hub) <= 5f).OrderBy(v => Hash(v.x, v.y, 52)).FirstOrDefault();
                if (spots.Count > 0 && Vector2.Distance(near, hub) <= 5f) chosen.Add(near);
                foreach (var v in spots.OrderBy(v => Hash(v.x, v.y, 53)))
                {
                    if (chosen.Count >= 4) break;
                    if (Vector2.Distance(v, hub) >= 6f && chosen.All(c => Vector2.Distance(c, v) >= 6f)) chosen.Add(v);
                }
                for (int i = 0; i < chosen.Count; i++)
                {
                    var v = chosen[i];
                    string kind = i == 0 ? (Rand01(v.x, v.y, 61) < 0.5f ? "cat" : "catgrey") : CatKind(v.x, v.y);   // the first is always tame
                    Herd(kind, new Vector2(v.x + 0.5f, d.h - 1 - v.y), 1); cats++;
                }
            }
            else
                for (int i = 0; i < farmTiles.Count; i += 27)
                { var ft = farmTiles[i]; Herd(CatKind(ft.x, ft.y), new Vector2(ft.x + 0.5f, d.h - 1 - ft.y) + new Vector2(2.5f, -1.5f), 1); cats++; }
            animals += cats;
            Debug.Log($"[GameBuilder] {id}: farm life — {animals} animals, {cropsN} crops, {lamps} lamps, {plants} flowers");
        }
    }
}
