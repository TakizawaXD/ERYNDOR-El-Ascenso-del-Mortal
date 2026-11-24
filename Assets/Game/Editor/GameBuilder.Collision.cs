// Shape-fitted colliders for solid world objects.
// The first pass gave buildings, walls and mountains a thin box at their base, so from the north you could walk
// "into" them. Here every solid sprite gets a polygon traced from its own opaque pixels, from the ground line up to
// just under its top edge (a small margin is left on tall objects so your head can still overlap the roof line).
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace WoodsGame.EditorTools
{
    public static partial class GameBuilder
    {
        // file name prefixes (under Assets/Art/World) that block movement with their whole silhouette
        static readonly string[] SolidShapes =
        {
            "Structures/house_", "Structures/castle_", "Structures/watchtower", "Structures/windmill", "Structures/lighthouse",
            "Structures/dark_tower", "Structures/mountain_", "Structures/mesa", "Structures/volcano", "Structures/ruin_",
            "Nature/rock_big", "Nature/rock_snow", "Nature/rock_small", "Nature/stump", "Nature/log",
            "Props/well", "Props/market_stall", "Props/camp_tent", "Props/camp_workbench", "Props/camp_rack", "Props/camp_stash",
        };

        static readonly Dictionary<string, Texture2D> _readable = new Dictionary<string, Texture2D>();

        /// <summary>Replaces the base boxes of solid sprites under <paramref name="root"/> with silhouette polygons.</summary>
        static int FitWorldColliders(Transform root)
        {
            int n = 0;
            foreach (var sr in root.GetComponentsInChildren<SpriteRenderer>(true))
            {
                if (sr.sprite == null) continue;
                string path = AssetDatabase.GetAssetPath(sr.sprite).Replace('\\', '/');
                int k = path.IndexOf("/Art/World/");
                if (k < 0) continue;
                string rel = path.Substring(k + "/Art/World/".Length);
                if (!SolidShapes.Any(rel.StartsWith)) continue;
                var go = sr.gameObject;
                var boxes = go.GetComponents<BoxCollider2D>().Where(b => !b.isTrigger).ToArray();
                if (boxes.Length == 0 && go.GetComponent<PolygonCollider2D>() != null) continue;
                var poly = Silhouette(sr.sprite, path);
                if (poly == null) continue;
                foreach (var b in boxes) Object.DestroyImmediate(b);
                var pc = go.AddComponent<PolygonCollider2D>();
                pc.pathCount = 1;
                pc.SetPath(0, poly);
                n++;
            }
            return n;
        }

        /// <summary>Outline of the opaque part of the sprite (alpha &gt; half, so soft shadows don't block), traced row by row
        /// from the ground up, in local units around a bottom-centre pivot.</summary>
        static Vector2[] Silhouette(Sprite s, string path)
        {
            // new scenes unload loose objects, so a cached texture can be destroyed between maps: reload it then
            if (!_readable.TryGetValue(path, out var tex) || tex == null)
            {
                tex = new Texture2D(2, 2, TextureFormat.RGBA32, false) { hideFlags = HideFlags.DontUnloadUnusedAsset };
                tex.LoadImage(File.ReadAllBytes(Path.Combine(ProjectRoot, path)));
                _readable[path] = tex;
            }
            var r = s.rect;
            int w = (int)r.width, h = (int)r.height, x0 = (int)r.x, y0 = (int)r.y;
            float ppu = s.pixelsPerUnit;
            // tall things keep their top ~14 px free (you can stand just behind a roof or a peak); small ones block fully
            int margin = h > 40 ? 14 : h > 24 ? 6 : 0;
            int top = h - margin;
            const int step = 2;
            var left = new List<Vector2>(); var right = new List<Vector2>();
            Vector2 piv = s.pivot;
            for (int row = 0; row < top; row += step)
            {
                int minX = int.MaxValue, maxX = -1;
                for (int dy = 0; dy < step && row + dy < top; dy++)
                    for (int x = 0; x < w; x++)
                        if (tex.GetPixel(x0 + x, y0 + row + dy).a > 0.5f) { if (x < minX) minX = x; if (x > maxX) maxX = x; }
                if (maxX < 0) continue;
                float yb = (row - piv.y) / ppu, yt = (Mathf.Min(row + step, top) - piv.y) / ppu;
                float xl = (minX + 0.5f - piv.x) / ppu, xr = (maxX + 0.5f - piv.x) / ppu;
                left.Add(new Vector2(xl, yb)); left.Add(new Vector2(xl, yt));
                right.Add(new Vector2(xr, yb)); right.Add(new Vector2(xr, yt));
            }
            if (left.Count < 2) return null;
            right.Reverse();
            var pts = left.Concat(right).ToList();
            // drop collinear points (keeps the physics shape light)
            var outPts = new List<Vector2>();
            for (int i = 0; i < pts.Count; i++)
            {
                var a = pts[(i - 1 + pts.Count) % pts.Count]; var b = pts[i]; var c = pts[(i + 1) % pts.Count];
                if (Mathf.Abs((b.x - a.x) * (c.y - b.y) - (b.y - a.y) * (c.x - b.x)) > 1e-5f) outPts.Add(b);
            }
            return outPts.Count >= 3 ? outPts.ToArray() : pts.ToArray();
        }
    }
}
