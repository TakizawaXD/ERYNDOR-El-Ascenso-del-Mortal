using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

namespace WoodsGame.EditorTools
{
    /// <summary>Slices the copy of the original woods sheet into named sprites, and sets up the font atlas.</summary>
    public class GameArtPostprocessor : AssetPostprocessor
    {
        public const string WoodsPath = "Assets/Art/Original/free_pixel_16_woods.png";
        public const string FontPng = "Assets/Game/Fonts/pixelfont.png";

        // name -> (x0, y0, x1, y1) in image coordinates (top-left origin), measured from the sheet
        public static readonly Dictionary<string, RectInt> WoodsRects = new Dictionary<string, RectInt>
        {
            { "woods_tree_big", new RectInt(275, 10, 59, 70) },
            { "woods_tree_small", new RectInt(275, 92, 28, 36) },
            { "woods_pine", new RectInt(308, 97, 25, 31) },
            { "woods_rock", new RectInt(224, 36, 16, 12) },
            { "woods_bush", new RectInt(225, 52, 14, 12) },
            { "woods_mushrooms", new RectInt(228, 70, 10, 9) },
            { "woods_stump", new RectInt(231, 80, 19, 16) },
            { "woods_reeds", new RectInt(226, 132, 13, 12) },
            { "woods_lily", new RectInt(240, 132, 16, 12) },
        };

        public override int GetPostprocessOrder() => 10;   // after ArtImportPostprocessor

        void OnPreprocessTexture()
        {
            var ti = (TextureImporter)assetImporter;
            if (assetPath == WoodsPath)
            {
                ti.textureType = TextureImporterType.Sprite;
                ti.spritePixelsPerUnit = 16;
                ti.filterMode = FilterMode.Point;
                ti.textureCompression = TextureImporterCompression.Uncompressed;
                ti.mipmapEnabled = false;
                ti.spriteImportMode = SpriteImportMode.Multiple;
                const int H = 192;
                var metas = new List<SpriteMetaData>();
                foreach (var kv in WoodsRects)
                {
                    var r = kv.Value;
                    metas.Add(new SpriteMetaData
                    {
                        name = kv.Key,
                        rect = new Rect(r.x, H - r.y - r.height, r.width, r.height),
                        alignment = (int)SpriteAlignment.BottomCenter,
                        pivot = new Vector2(0.5f, 0f),
                    });
                }
#pragma warning disable 618
                ti.spritesheet = metas.ToArray();
#pragma warning restore 618
            }
            else if (assetPath == FontPng)
            {
                ti.textureType = TextureImporterType.Default;
                ti.filterMode = FilterMode.Point;
                ti.textureCompression = TextureImporterCompression.Uncompressed;
                ti.mipmapEnabled = false;
                ti.alphaIsTransparency = true;
                ti.wrapMode = TextureWrapMode.Clamp;
                ti.npotScale = TextureImporterNPOTScale.None;
            }
        }
    }
}
