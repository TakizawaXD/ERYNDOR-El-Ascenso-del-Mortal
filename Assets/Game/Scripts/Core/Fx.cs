using UnityEngine;

namespace WoodsGame
{
    public static class Fx
    {
        public static GameObject Spawn(FxKind kind, Vector2 pos, int order = 100, float fps = 14f)
        {
            var a = GameAssets.I;
            if (a == null) return null;
            var frames = a.Frames(kind);
            if (frames == null || frames.Length == 0) return null;
            var go = new GameObject("fx_" + kind);
            go.transform.position = pos;
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = frames[0];
            sr.sortingOrder = order;
            var an = go.AddComponent<SpriteAnim>();
            an.frames = frames; an.fps = fps;
            return go;
        }
    }
}
