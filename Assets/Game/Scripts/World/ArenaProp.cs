using UnityEngine;

namespace WoodsGame
{
    /// <summary>Cheap ambient motion for arena and zone dressing: pulsing rune circles, flickering light beams, drifting fog,
    /// rising motes. Brightness follows BossArena.Flare (fight state) through <see cref="boost"/>.</summary>
    public class ArenaProp : MonoBehaviour
    {
        public enum Mode { Pulse, Flicker, Drift, Rise }
        public Mode mode = Mode.Pulse;
        public float speed = 1f, amount = 0.3f;
        public Vector2 drift = new Vector2(0.4f, 0f);
        [HideInInspector] public float boost = 1f;
        SpriteRenderer _sr;
        Color _base;
        Vector3 _home;
        float _seed;

        void Awake()
        {
            _sr = GetComponent<SpriteRenderer>();
            _base = _sr ? _sr.color : Color.white;
            _home = transform.localPosition;
            _seed = Random.value * 10f;
        }

        void Update()
        {
            if (_sr == null) return;
            float t = Time.time * speed + _seed;
            float a = _base.a;
            switch (mode)
            {
                case Mode.Pulse:
                    a *= 1f - amount + amount * (0.5f + 0.5f * Mathf.Sin(t * 2f));
                    break;
                case Mode.Flicker:
                    a *= 1f - amount * (0.5f + 0.5f * Mathf.Sin(t * 7f) * Mathf.Sin(t * 2.3f));
                    break;
                case Mode.Drift:
                    transform.localPosition = _home + (Vector3)(drift * Mathf.Sin(t * 0.3f));
                    a *= 1f - amount + amount * (0.5f + 0.5f * Mathf.Sin(t * 0.7f));
                    break;
                case Mode.Rise:
                    float k = Mathf.Repeat(t * 0.25f, 1f);
                    transform.localPosition = _home + new Vector3(Mathf.Sin(t * 1.3f) * 0.3f, k * 3f, 0);
                    a *= Mathf.Sin(k * Mathf.PI);
                    break;
            }
            _sr.color = new Color(_base.r, _base.g, _base.b, Mathf.Clamp01(a * boost));
        }
    }
}
