using UnityEngine;

namespace WoodsGame
{
    /// <summary>Expanding ground ring (boss shockwave). Hurts whoever stands on the ring's edge when it passes,
    /// once per wave - jump through it with a dodge (i-frames) or outrun it.</summary>
    public class BossWave : MonoBehaviour
    {
        public float speed = 6f, maxRadius = 9f, band = 0.45f;
        public int damage = 2;
        public Team team = Team.Enemy;
        public Transform owner;
        public float Radius { get; private set; } = 0.4f;
        bool _hit;
        SpriteRenderer _sr;
        Color _col;

        public static BossWave Spawn(Vector2 at, Color col, float speed, float maxRadius, int damage, Transform owner)
        {
            var go = new GameObject("BossWave");
            go.transform.position = at;
            var w = go.AddComponent<BossWave>();
            w.speed = speed; w.maxRadius = maxRadius; w.damage = damage; w.owner = owner; w._col = col;
            w._sr = go.AddComponent<SpriteRenderer>();
            var ba = BossAssets.I; var ga = GameAssets.I;
            w._sr.sprite = ba ? ba.wave : null;
            if (ga && ga.matAdditive) w._sr.sharedMaterial = ga.matAdditive;
            w._sr.sortingOrder = -30;
            w._sr.color = col;
            w.Apply();
            return w;
        }

        void Apply()
        {
            if (_sr == null || _sr.sprite == null) return;
            var s = _sr.sprite.bounds.size;            // the wave sprite is 2:1 - stretch it back into a circle on the ground
            transform.localScale = new Vector3(Radius * 2f / s.x, Radius * 2f / s.y, 1);
            float k = 1f - Radius / maxRadius;
            _sr.color = new Color(_col.r, _col.g, _col.b, Mathf.Clamp01(0.25f + k));
        }

        void Update()
        {
            if (GameManager.Paused) return;
            Radius += speed * Time.deltaTime;
            Apply();
            if (!_hit)
            {
                var p = PlayerController.Current;
                if (p != null && team == Team.Enemy && !p.health.IsDead)
                {
                    float d = Vector2.Distance(p.transform.position, transform.position);
                    if (Mathf.Abs(d - Radius) < band)
                    {
                        _hit = true;
                        Combat.Hit(p.transform.position + Vector3.up * 0.3f, 0.3f,
                            new DamageInfo { amount = damage, knockback = 7f, source = team, heavy = true }, owner);
                    }
                }
            }
            if (Radius >= maxRadius) Destroy(gameObject);
        }
    }

    /// <summary>Telegraphed impact: a pulsing marker on the ground, then an explosion that hurts everything inside it.</summary>
    public class BossMarker : MonoBehaviour
    {
        public float delay = 1.1f, radius = 1.1f;
        public int damage = 2;
        public FxKind fx = FxKind.Explosion;
        public Transform owner;
        float _born;
        SpriteRenderer _sr;
        Color _col;

        public static BossMarker Spawn(Vector2 at, Color col, float radius, float delay, int damage, Transform owner, FxKind fx = FxKind.Explosion)
        {
            var go = new GameObject("BossMarker");
            go.transform.position = at;
            var m = go.AddComponent<BossMarker>();
            m.radius = radius; m.delay = delay; m.damage = damage; m.owner = owner; m.fx = fx; m._col = col; m._born = Time.time;
            m._sr = go.AddComponent<SpriteRenderer>();
            var ba = BossAssets.I;
            m._sr.sprite = ba ? ba.telegraph : null;
            m._sr.sortingOrder = -29;
            if (m._sr.sprite) { float s = radius * 2f / m._sr.sprite.bounds.size.x; go.transform.localScale = new Vector3(s, s, 1); }
            m._sr.color = col;
            return m;
        }

        void Update()
        {
            float k = (Time.time - _born) / delay;
            if (_sr) _sr.color = new Color(_col.r, _col.g, _col.b, 0.35f + 0.5f * Mathf.Abs(Mathf.Sin(k * 14f)) * k);
            if (k < 1f) return;
            Fx.Spawn(fx, transform.position);
            Sfx.Play("quake", 0.5f);
            Combat.Hit(transform.position, radius, new DamageInfo { amount = damage, knockback = 6f, source = Team.Enemy, heavy = true }, owner);
            Destroy(gameObject);
        }
    }
}
