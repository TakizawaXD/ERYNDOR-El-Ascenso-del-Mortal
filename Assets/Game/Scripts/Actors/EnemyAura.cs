using UnityEngine;

namespace WoodsGame
{
    /// <summary>What makes a regional enemy read as dangerous from afar: a coloured glow at the eyes, a faint halo on the ground
    /// and a few motes rising around it (embers, frost, spores, ghost wisps). Set up by the builder per enemy type.</summary>
    public class EnemyAura : MonoBehaviour
    {
        public Color color = new Color(1f, 0.4f, 0.2f);
        public float eyeHeight = 1.1f;       // world units above the feet (before the actor's scale)
        public float groundRadius = 0.9f;
        public int motes = 4;
        public float riseSpeed = 0.7f;
        public bool falling;                 // frost: motes drift down instead of up

        SpriteRenderer[] _m;
        float[] _t;
        EnemyController _e;

        void Start()
        {
            _e = GetComponent<EnemyController>();
            LightGlow.Attach(transform, new Vector2(0, eyeHeight), 0.7f, color, 0.9f, true);
            LightGlow.Attach(transform, new Vector2(0, 0.1f), groundRadius, color, 0.45f, true);
            var a = GameAssets.I;
            _m = new SpriteRenderer[motes]; _t = new float[motes];
            for (int i = 0; i < motes; i++)
            {
                var go = new GameObject("AuraMote");
                go.transform.SetParent(transform, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = DayNightLighting.White;
                if (a && a.matAdditive) sr.sharedMaterial = a.matAdditive;
                sr.sortingOrder = DayNightLighting.OverlayOrder + 2;
                go.transform.localScale = Vector3.one * (1f / 16f) / Mathf.Max(0.01f, transform.lossyScale.x) * (i % 3 == 0 ? 2 : 1);
                _m[i] = sr; _t[i] = Random.value;
            }
        }

        void Update()
        {
            if (_m == null) return;
            bool show = _e == null || (!_e.health.IsDead && !_e.Asleep && !_e.Hidden);
            float s = Mathf.Max(0.01f, transform.lossyScale.x);
            for (int i = 0; i < _m.Length; i++)
            {
                var sr = _m[i];
                sr.enabled = show;
                if (!show) continue;
                _t[i] += Time.deltaTime * riseSpeed / 1.6f;
                if (_t[i] > 1f) _t[i] -= 1f;
                float k = _t[i];
                float x = Mathf.Sin((i * 2.1f) + Time.time * 1.3f) * 0.45f;
                float y = falling ? 1.6f - k * 1.6f : k * 1.6f;
                sr.transform.localPosition = new Vector3(Mathf.Round(x * 16f) / 16f / s, (0.2f + y) / s, 0);
                sr.color = new Color(color.r, color.g, color.b, Mathf.Sin(k * Mathf.PI) * 0.9f);
            }
        }
    }
}
