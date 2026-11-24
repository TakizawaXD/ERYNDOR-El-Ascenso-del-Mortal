using UnityEngine;

namespace WoodsGame
{
    /// <summary>Arrow / fireball / spit. Trigger collider; stops on walls (solid colliders) and on the first target hit.</summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public class Projectile : MonoBehaviour
    {
        public int damage = 2;
        public Team team = Team.Player;
        public float life = 2.5f;
        public bool rotateToDirection = true;
        public FxKind impactFx = FxKind.Hit;
        [HideInInspector] public int pierce;       // extra targets it passes through (Ranger perk)
        [HideInInspector] public bool crit;
        [HideInInspector] public Element element;
        Transform _owner;
        Rigidbody2D _rb;
        float _born;

        public static Projectile Fire(GameObject prefab, Vector2 pos, Vector2 dir, float speed, int dmg, Team team, Transform owner)
        {
            if (prefab == null) return null;
            var go = Instantiate(prefab, pos, Quaternion.identity);
            var p = go.GetComponent<Projectile>();
            p.damage = dmg; p.team = team; p._owner = owner;
            p._rb = go.GetComponent<Rigidbody2D>();
            p._rb.gravityScale = 0;
            p._rb.linearVelocity = dir.normalized * speed;
            if (p.rotateToDirection)
            {
                // sprites face right; snap to 90 degrees for crisp pixels when shot along an axis
                float ang = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
                if (Mathf.Abs(Mathf.DeltaAngle(ang, Mathf.Round(ang / 90f) * 90f)) < 8f) ang = Mathf.Round(ang / 90f) * 90f;
                go.transform.rotation = Quaternion.Euler(0, 0, ang);
            }
            return p;
        }

        void Awake() { _rb = GetComponent<Rigidbody2D>(); _born = Time.time; }

        void Update()
        {
            if (Time.time - _born > life) Destroy(gameObject);
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            if (_owner != null && other.transform.IsChildOf(_owner)) return;
            if (other.GetComponentInParent<Projectile>() || other.GetComponentInParent<Pickup>() || other.GetComponentInParent<LevelExit>()) return;
            var h = other.GetComponentInParent<Health>();
            if (h != null)
            {
                if (h.team == team || h.IsDead) return;
                if (h.Invulnerable) return;    // rolling through arrows / fireballs
                h.Damage(new DamageInfo { amount = damage, direction = _rb.linearVelocity.normalized, knockback = 4f, source = team, crit = crit, element = element, ranged = true, attacker = _owner });
                if (pierce-- > 0) { Fx.Spawn(impactFx, transform.position); return; }
                Impact();
                return;
            }
            var b = other.GetComponentInParent<Breakable>();
            if (b != null && team == Team.Player) { b.Break(); Impact(); return; }
            if (!other.isTrigger) Impact();   // trees, rocks, walls, water edge
        }

        void Impact()
        {
            Fx.Spawn(impactFx, transform.position);
            Sfx.PlayAt("hit", transform.position, 0.6f);
            Destroy(gameObject);
        }
    }
}
