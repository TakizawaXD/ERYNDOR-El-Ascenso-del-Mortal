// Import rules for everything under Assets/Art (pixel_16 woods / Tiny RPG style).
//  * Sprite, 16 PPU, Point filter, uncompressed, no mipmaps, clamp.
//  * File-name conventions:
//      ..._<W>x<H>.png      -> Sprite Mode Multiple, uniform grid of W x H cells (left->right, top->bottom)
//      ..._9s<N>.png         -> 9-slice border of N px on every side
//      ...seamless...        -> Wrap Mode Repeat
//  * Pivot: bottom-centre for Vegetation / Props / Decorations (Y-sorting friendly),
//           centre for tiles, effects, UI, ambient and fences/bridges (they are grid tiles).
//  * Characters copied to Assets/Art/Characters/** (Tiny RPG packs, 100x100 cells) are sliced
//    100x100 with the pivot on the feet (0.5, 0.4).
// Rules are applied only the first time a texture is imported, so later manual tweaks in the
// Inspector are never overwritten. Use Tools > Art > Reapply Import Rules to force them again.
using System.IO;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;

namespace WoodsArt.EditorTools
{
    public class ArtImportPostprocessor : AssetPostprocessor
    {
        public const string ArtRoot = "Assets/Art/";
        public const int PixelsPerUnit = 16;
        public const string CharacterRoot = "Assets/Art/Characters/";
        public const int CharacterCell = 64;
        public static readonly Vector2 CharacterPivot = new Vector2(0.5f, 12f / 64f);

        [System.Serializable] class PivotManifest { public int cell; public float[] pivot; }

        /// <summary>Pivot (and cell) from Assets/Art/Characters/&lt;Name&gt;/&lt;Name&gt;_animations.json (also for weapon sets:
        /// WeaponSets/&lt;Class&gt;/&lt;Set&gt;/...). False when there is no manifest or it has no pivot.</summary>
        static bool ManifestPivot(string path, out Vector2 pivot, out int cell)
        {
            pivot = default; cell = 0;
            try
            {
                var rel = path.Substring(CharacterRoot.Length).Split('/');
                string dir = rel[0] == "WeaponSets" && rel.Length > 3 ? CharacterRoot + rel[0] + "/" + rel[1] + "/" + rel[2] : CharacterRoot + rel[0];
                var json = System.IO.Directory.Exists(dir) ? System.IO.Directory.GetFiles(dir, "*_animations.json") : new string[0];
                if (json.Length == 0) return false;
                var m = JsonUtility.FromJson<PivotManifest>(System.IO.File.ReadAllText(json[0]));
                if (m == null || m.pivot == null || m.pivot.Length < 2) return false;
                pivot = new Vector2(m.pivot[0], m.pivot[1]); cell = m.cell;
                return true;
            }
            catch { return false; }
        }
        static bool s_Force;

        [MenuItem("Tools/Art/Reapply Import Rules")]
        static void Reapply()
        {
            s_Force = true;
            try
            {
                foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { "Assets/Art" }))
                    AssetDatabase.ImportAsset(AssetDatabase.GUIDToAssetPath(guid), ImportAssetOptions.ForceUpdate);
            }
            finally { s_Force = false; }
        }

        void OnPreprocessTexture()
        {
            if (!assetPath.StartsWith(ArtRoot) || !assetPath.EndsWith(".png")) return;
            if (!assetImporter.importSettingsMissing && !s_Force) return;

            var ti = (TextureImporter)assetImporter;
            string file = Path.GetFileNameWithoutExtension(assetPath);
            string path = assetPath.Replace('\\', '/');

            ti.textureType = TextureImporterType.Sprite;
            ti.spritePixelsPerUnit = PixelsPerUnit;
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            ti.alphaSource = TextureImporterAlphaSource.FromInput;
            ti.wrapMode = file.Contains("seamless") ? TextureWrapMode.Repeat : TextureWrapMode.Clamp;
            ti.npotScale = TextureImporterNPOTScale.None;
            if (file == "world_map") ti.isReadable = true;            // the map UI paints fog over it
            if (path.Contains("/UI/Title/"))
            {
                // the title screen illustration is shown scaled to the window: smooth filtering, full size kept
                ti.filterMode = FilterMode.Bilinear;
                ti.maxTextureSize = 4096;
            }

            var settings = new TextureImporterSettings();
            ti.ReadTextureSettings(settings);
            settings.spriteMeshType = SpriteMeshType.FullRect;   // exact quads -> no clipped pixels
            settings.spriteExtrude = 0;
            ti.SetTextureSettings(settings);

            Vector2 pivot = PivotFor(path, file);
            Vector4 border = Vector4.zero;
            var nine = Regex.Match(file, @"_9s(\d+)");
            if (nine.Success) { int b = int.Parse(nine.Groups[1].Value); border = new Vector4(b, b, b, b); }

            int cw = 0, ch = 0;
            var m = Regex.Matches(file, @"_(\d+)x(\d+)");
            if (m.Count > 0)
            {
                var last = m[m.Count - 1];
                cw = int.Parse(last.Groups[1].Value); ch = int.Parse(last.Groups[2].Value);
            }
            else if (path.StartsWith(CharacterRoot))
            {
                // generated character sheets: 64x64 cells, feet on row 52 -> pivot on the ground contact point
                cw = ch = CharacterCell; pivot = CharacterPivot;
                // big bosses (Tools/CharAnim/bosses.py): 128x128 cells, feet on row 112
                if (path.StartsWith(CharacterRoot + "Boss")) { cw = ch = 128; pivot = new Vector2(0.5f, 16f / 128f); }
                // the character's own manifest wins: its pivot sits on the measured feet (Tools/CharAnim/audit_sprites.py)
                if (ManifestPivot(path, out var mp, out int mcell)) { pivot = mp; if (mcell > 0) cw = ch = mcell; }
            }
            else if (path.Contains("/Characters/") && path.Contains("100x100"))
            {
                cw = ch = 100; pivot = new Vector2(0.5f, 0.4f);
            }

            if (!ReadPngSize(assetPath, out int w, out int h) || cw == 0 || (cw >= w && ch >= h))
            {
                ti.spriteImportMode = SpriteImportMode.Single;
                ti.spritePivot = pivot;
                ti.spriteBorder = border;
                var s = new TextureImporterSettings(); ti.ReadTextureSettings(s);
                s.spriteAlignment = (int)SpriteAlignment.Custom; ti.SetTextureSettings(s);
                return;
            }

            ti.spriteImportMode = SpriteImportMode.Multiple;
            var metas = new List<SpriteMetaData>();
            int cols = w / cw, rows = h / ch, i = 0;
            for (int r = 0; r < rows; r++)
                for (int c = 0; c < cols; c++)
                {
                    metas.Add(new SpriteMetaData
                    {
                        name = file + "_" + i++,
                        rect = new Rect(c * cw, h - (r + 1) * ch, cw, ch),
                        alignment = (int)SpriteAlignment.Custom,
                        pivot = pivot,
                        border = border,
                    });
                }
#pragma warning disable 618
            ti.spritesheet = metas.ToArray();
#pragma warning restore 618
        }

        static Vector2 PivotFor(string path, string file)
        {
            if (file.StartsWith("deco_fence") || file.StartsWith("deco_bridge")) return new Vector2(0.5f, 0.5f);
            if (path.Contains("/Vegetation/") || path.Contains("/Props/") || path.Contains("/Decorations/") ||
                path.Contains("/World/Nature/") || path.Contains("/World/Structures/") || path.Contains("/World/Interiors/Furniture/") || path.Contains("/External/CuteFantasy/"))
                return new Vector2(0.5f, 0f);
            // catacomb / cave props stand on their base like every other prop; flat floor pieces stay centred
            if (path.Contains("/World/Catacombs/") && !Regex.IsMatch(file, "^(rune|cracks|plate|hole|grate|ledge|spike_anim|runecircle|secret_)"))
                return new Vector2(0.5f, 0f);
            return new Vector2(0.5f, 0.5f);
        }

        static bool ReadPngSize(string assetPath, out int w, out int h)
        {
            w = h = 0;
            try
            {
                using (var fs = File.OpenRead(assetPath))
                {
                    var b = new byte[24];
                    if (fs.Read(b, 0, 24) < 24) return false;
                    w = (b[16] << 24) | (b[17] << 16) | (b[18] << 8) | b[19];
                    h = (b[20] << 24) | (b[21] << 16) | (b[22] << 8) | b[23];
                    return w > 0 && h > 0;
                }
            }
            catch { return false; }
        }
    }
}
