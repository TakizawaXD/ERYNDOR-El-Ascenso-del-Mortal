// Tools > Art > Build Tiles, Palette & Animations
//  * RuleTiles (47-tile blob) for Grass, TallGrass, Cliff, StonePath and animated Water.
//  * Random RuleTiles for the grass / dirt fill variants.
//  * Plain Tiles for fence & bridge pieces.
//  * A Tile Palette "Woods_Terrain" with all of the above.
//  * AnimationClips (SpriteRenderer.m_Sprite) for every "*_anim_*" sheet.
// RuleTile needs the "2D Tilemap Extras" package (com.unity.2d.tilemap.extras); without it only
// the animations and plain tiles are generated and a warning explains what to install.
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;
using UnityEngine.Tilemaps;
#if WOODS_HAS_TILEMAP_EDITOR
using UnityEditor.Tilemaps;
#endif

namespace WoodsArt.EditorTools
{
    public static class ArtAssetBuilder
    {
        const string Art = "Assets/Art";
        const string OutTiles = "Assets/Art/Tilesets/_Generated";
        const string OutAnims = "Assets/Art/Animations";

        // 47 canonical blob masks in sheet order. Bits: N=1 NE=2 E=4 SE=8 S=16 SW=32 W=64 NW=128 (N = +Y)
        public static readonly int[] BlobMasks =
        {
            0, 1, 4, 5, 7, 16, 17, 20, 21, 23, 28, 29, 31, 64, 65, 68, 69, 71, 80, 81, 84, 85, 87, 92, 93, 95,
            112, 113, 116, 117, 119, 124, 125, 127, 193, 197, 199, 209, 213, 215, 221, 223, 241, 245, 247, 253, 255
        };

        [MenuItem("Tools/Art/Build Tiles, Palette & Animations")]
        public static void BuildAll()
        {
            EnsureFolder(OutTiles); EnsureFolder(OutAnims);
            var paletteTiles = new List<List<TileBase>>();
            paletteTiles.Add(BuildRuleTiles());
            paletteTiles.Add(BuildPlainTiles("Assets/Art/Environments/Decorations/deco_fence_16x16.png"));
            paletteTiles.Add(BuildPlainTiles("Assets/Art/Environments/Decorations/deco_bridge_16x16.png"));
            paletteTiles.Add(BuildPlainTiles("Assets/Art/Environments/Terrain/terrain_grass_fill_16x16.png")
                .Concat(BuildPlainTiles("Assets/Art/Environments/Terrain/terrain_dirt_fill_16x16.png")).ToList());
            BuildPalette(paletteTiles);
            int clips = BuildAnimations();
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log($"[ArtAssetBuilder] Done. Animation clips: {clips}. Tiles in {OutTiles}.");
        }

        // ------------------------------------------------------------------ helpers
        public static Sprite[] SlicedSprites(string texPath)
        {
            return AssetDatabase.LoadAllAssetsAtPath(texPath).OfType<Sprite>()
                .OrderBy(s => { var m = Regex.Match(s.name, @"_(\d+)$"); return m.Success ? int.Parse(m.Groups[1].Value) : 0; })
                .ToArray();
        }

        static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;
            var parent = Path.GetDirectoryName(path).Replace('\\', '/');
            EnsureFolder(parent);
            AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
        }

        static T CreateOrReplace<T>(T obj, string path) where T : Object
        {
            var existing = AssetDatabase.LoadAssetAtPath<T>(path);
            if (existing != null)
            {
                EditorUtility.CopySerialized(obj, existing);
                EditorUtility.SetDirty(existing);
                return existing;
            }
            AssetDatabase.CreateAsset(obj, path);
            return obj;
        }

        static List<TileBase> BuildPlainTiles(string texPath)
        {
            var list = new List<TileBase>();
            foreach (var s in SlicedSprites(texPath))
            {
                var t = ScriptableObject.CreateInstance<Tile>();
                t.sprite = s;
                t.colliderType = Tile.ColliderType.None;
                list.Add(CreateOrReplace(t, $"{OutTiles}/{s.name}.asset"));
            }
            return list;
        }

        // ------------------------------------------------------------- rule tiles
        static List<TileBase> BuildRuleTiles()
        {
            var made = new List<TileBase>();
#if WOODS_HAS_TILEMAP_EXTRAS
            made.Add(BlobRuleTile("RT_Grass", new[] { "Assets/Art/Tilesets/Grass/tileset_grass_blob47_16x16.png" }, Tile.ColliderType.None));
            made.Add(BlobRuleTile("RT_TallGrass", new[] { "Assets/Art/Tilesets/TallGrass/tileset_tallgrass_blob47_16x16.png" }, Tile.ColliderType.None));
            made.Add(BlobRuleTile("RT_Cliff", new[] { "Assets/Art/Tilesets/Cliff/tileset_cliff_blob47_16x16.png" }, Tile.ColliderType.None));
            made.Add(BlobRuleTile("RT_StonePath", new[] { "Assets/Art/Tilesets/StonePath/tileset_stonepath_blob47_16x16.png" }, Tile.ColliderType.None));
            made.Add(BlobRuleTile("RT_Water", Enumerable.Range(0, 4)
                .Select(f => $"Assets/Art/Tilesets/Water/tileset_water_blob47_f{f}_16x16.png").ToArray(), Tile.ColliderType.None));
            made.Add(RandomFill("RT_GrassFill_Random", "Assets/Art/Environments/Terrain/terrain_grass_fill_16x16.png"));
            made.Add(RandomFill("RT_DirtFill_Random", "Assets/Art/Environments/Terrain/terrain_dirt_fill_16x16.png"));
#else
            Debug.LogWarning("[ArtAssetBuilder] Install 'com.unity.2d.tilemap.extras' (2D Tilemap Extras) to generate the RuleTiles. " +
                             "Plain tiles, palette and animations are still generated.");
#endif
            return made.Where(t => t != null).ToList();
        }

#if WOODS_HAS_TILEMAP_EXTRAS
        static RuleTile BlobRuleTile(string name, string[] frameSheets, Tile.ColliderType collider)
        {
            var frames = frameSheets.Select(SlicedSprites).ToArray();
            if (frames.Any(f => f.Length < BlobMasks.Length))
            {
                Debug.LogError($"[ArtAssetBuilder] {name}: sheet not sliced into 47 sprites. Run Tools > Art > Reapply Import Rules.");
                return null;
            }
            var rt = ScriptableObject.CreateInstance<RuleTile>();
            rt.m_DefaultSprite = frames[0][BlobMasks.Length - 1];
            rt.m_DefaultColliderType = collider;
            const int N = 1, NE = 2, E = 4, SE = 8, S = 16, SW = 32, W = 64, NW = 128;
            for (int i = 0; i < BlobMasks.Length; i++)
            {
                int m = BlobMasks[i];
                int Edge(int b) => (m & b) != 0 ? RuleTile.TilingRuleOutput.Neighbor.This : RuleTile.TilingRuleOutput.Neighbor.NotThis;
                int Corner(int b, int a1, int a2) => ((m & a1) != 0 && (m & a2) != 0) ? Edge(b) : 0;
                var rule = new RuleTile.TilingRule
                {
                    // order matches RuleTile's default m_NeighborPositions:
                    // (-1,1) (0,1) (1,1) (-1,0) (1,0) (-1,-1) (0,-1) (1,-1)
                    m_Neighbors = new List<int>
                    {
                        Corner(NW, N, W), Edge(N), Corner(NE, N, E),
                        Edge(W), Edge(E),
                        Corner(SW, S, W), Edge(S), Corner(SE, S, E)
                    },
                    m_Sprites = frames.Select(f => f[i]).ToArray(),
                    m_ColliderType = collider,
                };
                if (frames.Length > 1)
                {
                    rule.m_Output = RuleTile.TilingRuleOutput.OutputSprite.Animation;
                    rule.m_MinAnimationSpeed = rule.m_MaxAnimationSpeed = 4f;
                }
                rt.m_TilingRules.Add(rule);
            }
            return CreateOrReplace(rt, $"{OutTiles}/{name}.asset");
        }

        static RuleTile RandomFill(string name, string sheet)
        {
            var sprites = SlicedSprites(sheet);
            if (sprites.Length == 0) return null;
            var rt = ScriptableObject.CreateInstance<RuleTile>();
            rt.m_DefaultSprite = sprites[0];
            // base variant appears most often: weight by repeating it
            var weighted = new List<Sprite> { sprites[0], sprites[0], sprites[0], sprites[0] };
            weighted.AddRange(sprites.Skip(1));
            rt.m_TilingRules.Add(new RuleTile.TilingRule
            {
                m_Neighbors = new List<int> { 0, 0, 0, 0, 0, 0, 0, 0 },
                m_Sprites = weighted.ToArray(),
                m_Output = RuleTile.TilingRuleOutput.OutputSprite.Random,
                m_PerlinScale = 0.5f,
            });
            return CreateOrReplace(rt, $"{OutTiles}/{name}.asset");
        }
#endif

        // ---------------------------------------------------------------- palette
        static void BuildPalette(List<List<TileBase>> rows)
        {
#if WOODS_HAS_TILEMAP_EDITOR
            const string folder = "Assets/Art/Tilesets/_Generated";
            string path = folder + "/Woods_Terrain.prefab";
            if (AssetDatabase.LoadAssetAtPath<GameObject>(path) == null)
                GridPaletteUtility.CreateNewPalette(folder, "Woods_Terrain",
                    GridLayout.CellLayout.Rectangle, GridPalette.CellSizing.Automatic, Vector3.one, GridLayout.CellSwizzle.XYZ);
            var root = PrefabUtility.LoadPrefabContents(path);
            try
            {
                var tm = root.GetComponentInChildren<Tilemap>();
                tm.ClearAllTiles();
                for (int r = 0; r < rows.Count; r++)
                    for (int c = 0; c < rows[r].Count; c++)
                        tm.SetTile(new Vector3Int(c, -r * 2, 0), rows[r][c]);
                PrefabUtility.SaveAsPrefabAsset(root, path);
            }
            finally { PrefabUtility.UnloadPrefabContents(root); }
#else
            Debug.LogWarning("[ArtAssetBuilder] 2D Tilemap Editor package not found: palette not created (tiles are still generated).");
#endif
        }

        // ------------------------------------------------------------- animations
        static readonly string[] OneShot = { "dust", "splash", "hit_spark", "blood", "poof", "explosion", "sparkle", "heal", "chest", "rain" };

        static int BuildAnimations()
        {
            int count = 0;
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { Art }))
            {
                string p = AssetDatabase.GUIDToAssetPath(guid);
                string file = Path.GetFileNameWithoutExtension(p);
                if (!file.Contains("_anim")) continue;
                var sprites = SlicedSprites(p);
                if (sprites.Length < 2) continue;
                var cell = Regex.Matches(file, @"_(\d+)x(\d+)");
                var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(p);
                int perRow = sprites.Length;
                if (cell.Count > 0 && tex != null)
                    perRow = Mathf.Max(1, tex.width / int.Parse(cell[cell.Count - 1].Groups[1].Value));
                int rows = Mathf.CeilToInt(sprites.Length / (float)perRow);
                bool loop = !OneShot.Any(k => file.Contains(k));
                float fps = file.StartsWith("fx_") ? 12f : file.Contains("waterfall") ? 10f : 8f;
                string sub = p.Substring(Art.Length + 1);
                string folder = OutAnims + "/" + Path.GetDirectoryName(sub).Replace('\\', '/');
                EnsureFolder(folder);
                string baseName = Regex.Replace(file, @"_anim.*$", "");
                for (int r = 0; r < rows; r++)
                {
                    var frames = sprites.Skip(r * perRow).Take(perRow).ToArray();
                    string name = rows > 1 ? $"{baseName}_v{r}" : baseName;
                    CreateOrReplace(MakeClip(frames, fps, loop), $"{folder}/{name}.anim");
                    count++;
                }
            }
            return count;
        }

        static AnimationClip MakeClip(Sprite[] frames, float fps, bool loop)
        {
            var clip = new AnimationClip { frameRate = fps };
            var binding = EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite");
            int n = frames.Length;
            var keys = new ObjectReferenceKeyframe[loop ? n + 1 : n];
            for (int i = 0; i < n; i++) keys[i] = new ObjectReferenceKeyframe { time = i / fps, value = frames[i] };
            if (loop) keys[n] = new ObjectReferenceKeyframe { time = n / fps, value = frames[0] };
            AnimationUtility.SetObjectReferenceCurve(clip, binding, keys);
            var s = AnimationUtility.GetAnimationClipSettings(clip);
            s.loopTime = loop;
            AnimationUtility.SetAnimationClipSettings(clip, s);
            return clip;
        }
    }
}
