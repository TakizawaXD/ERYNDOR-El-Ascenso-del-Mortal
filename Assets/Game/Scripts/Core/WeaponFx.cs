using UnityEngine;

namespace WoodsGame
{
    /// <summary>The swing trail of the equipped weapon: white arc sheets rotated to the facing and tinted by rarity/element.</summary>
    public static class WeaponFx
    {
        public static void Swing(string fx, Vector2 at, Vector2 facing, float radius, ItemDef w)
        {
            var a = GameAssets.I;
            var frames = a ? a.WeaponFxFrames(fx) : null;
            if (frames == null || frames.Length == 0) return;
            var go = new GameObject("swing_" + fx);
            go.transform.position = at;
            float ang = Mathf.Atan2(facing.y, facing.x) * Mathf.Rad2Deg;
            go.transform.rotation = Quaternion.Euler(0, 0, ang);
            float s = Mathf.Clamp(radius / 0.75f, 0.7f, 1.6f);
            go.transform.localScale = new Vector3(s, s, 1);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = frames[0];
            sr.sortingOrder = 120;
            sr.color = Tint(w);
            var an = go.AddComponent<SpriteAnim>();
            an.frames = frames; an.fps = fx == "greatsword" || fx == "impact" ? 16f : 22f;
        }

        /// <summary>One-shot effect sheet (Assets/Art/Effects/Weapons/fx_&lt;name&gt;_anim_32x32.png) at a point.</summary>
        public static GameObject Play(string fx, Vector2 at, Color color, float scale = 1f, float fps = 18f, int order = 119, float angle = 0f)
        {
            var a = GameAssets.I;
            var frames = a ? a.WeaponFxFrames(fx) : null;
            if (frames == null || frames.Length == 0) return null;
            var go = new GameObject("fx_" + fx);
            go.transform.position = at;
            go.transform.rotation = Quaternion.Euler(0, 0, angle);
            go.transform.localScale = new Vector3(scale, scale, 1);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = frames[0]; sr.sortingOrder = order; sr.color = color;
            var an = go.AddComponent<SpriteAnim>();
            an.frames = frames; an.fps = fps;
            return go;
        }

        /// <summary>Ground shockwave + dust of the heavy weapons (hammer, heavy axe, greatsword slams).</summary>
        public static void Shockwave(Vector2 at, float radius, ItemDef w)
        {
            var c = w != null && w.element != Element.None ? Tint(w) : new Color(0.95f, 0.9f, 0.82f, 0.9f);
            Play("shockwave", at + Vector2.down * 0.35f, c, Mathf.Clamp(radius * 1.6f, 1f, 2.4f), 16f, 5);
            Fx.Spawn(FxKind.Dust, at + Vector2.down * 0.4f, 6);
        }

        /// <summary>Sparks of metal on metal (blocks, parries, ripostes).</summary>
        public static void Spark(Vector2 at, Color c) => Play("spark", at, c, 1f, 22f, 121);

        public static Color Tint(ItemDef w)
        {
            switch (w.element)
            {
                case Element.Fire: return new Color(1f, 0.62f, 0.3f, 0.95f);
                case Element.Frost: return new Color(0.6f, 0.88f, 1f, 0.95f);
                case Element.Venom: return new Color(0.65f, 1f, 0.4f, 0.95f);
                case Element.Holy: return new Color(1f, 0.9f, 0.5f, 0.95f);
            }
            var c = w.RarityColor; c.a = 0.85f;
            return w.rarity == Rarity.Common ? new Color(1, 1, 1, 0.8f) : c;
        }
    }
}
