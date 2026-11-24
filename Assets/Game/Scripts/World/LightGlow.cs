using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>An additive glow sprite that fades in with the dark.</summary>
    public class LightGlow : MonoBehaviour
    {
        static readonly List<LightGlow> All = new List<LightGlow>();
        static float _intensity;
        public Color color = new Color(1f, 0.7f, 0.35f);
        public float strength = 0.8f;
        public float flicker = 0.08f;
        [HideInInspector] public float extra = 1f;
        public bool alwaysOn;          // interiors: fireplaces glow even at noon
        SpriteRenderer _sr;
        float _seed;

        public static LightGlow Attach(Transform parent, Vector2 offset, float radius, Color color, float strength, bool alwaysOn = false)
        {
            var a = GameAssets.I;
            var go = new GameObject("Glow");
            go.transform.SetParent(parent, false);
            go.transform.localPosition = offset;
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = a ? a.lightSprite : null;
            if (a && a.matAdditive) sr.sharedMaterial = a.matAdditive;
            sr.sortingOrder = DayNightLighting.OverlayOrder + 1;
            float s = sr.sprite ? radius * 2f / (sr.sprite.rect.width / sr.sprite.pixelsPerUnit) : radius;
            go.transform.localScale = new Vector3(s / Mathf.Max(0.01f, parent.lossyScale.x), s / Mathf.Max(0.01f, parent.lossyScale.y), 1);
            var g = go.AddComponent<LightGlow>();
            g.color = color; g.strength = strength; g.alwaysOn = alwaysOn;
            return g;
        }

        void Awake() { _sr = GetComponent<SpriteRenderer>(); _seed = Random.value * 10f; }
        void OnEnable() { All.Add(this); Apply(); }
        void OnDisable() { All.Remove(this); }

        public static void SetIntensity(float v)
        {
            if (Mathf.Abs(v - _intensity) < 0.001f && Time.frameCount % 4 != 0) return;
            _intensity = v;
            for (int i = 0; i < All.Count; i++) All[i].Apply();
        }

        void Apply()
        {
            if (_sr == null) return;
            float k = alwaysOn ? Mathf.Max(0.55f, _intensity) : _intensity;
            float f = 1f + Mathf.Sin(Time.time * 9f + _seed) * flicker + Mathf.Sin(Time.time * 23f + _seed * 3f) * flicker * 0.5f;
            float a = Mathf.Clamp01(k * strength * f * extra);
            _sr.enabled = a > 0.02f;
            _sr.color = new Color(color.r, color.g, color.b, a);
        }
    }
}
