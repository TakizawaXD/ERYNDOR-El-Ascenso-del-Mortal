using System;
using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>The weapon's hitbox. It only exists between the HitOn and HitOff events of the attack animation; while
    /// open it is swept every physics step along the shape of the move (an arc in front for swings, a line for thrusts,
    /// a circle for spins and slams), so a target that walks into a swing still gets hit, and every target is damaged
    /// at most ONCE per swing. Size comes from the AttackAnimationData (measured on the drawn weapon) and the actor's
    /// scale.</summary>
    public class WeaponHitboxController : MonoBehaviour
    {
        public bool IsOpen { get; private set; }
        public int Hits { get; private set; }
        public int Opened { get; private set; }
        /// <summary>Total hits ever (tests).</summary>
        public int TotalHits { get; private set; }
        public Vector2 LastCenter { get; private set; }
        public float LastRadius { get; private set; }

        Actor _owner;
        AttackAnimationData _d;
        DamageInfo _info;
        float _reach, _radius;
        Action<Health, DamageInfo> _onHit;
        bool _breakables;
        readonly HashSet<UnityEngine.Object> _done = new HashSet<UnityEngine.Object>();
        static readonly Collider2D[] Buf = new Collider2D[48];

        void Awake() { _owner = GetComponent<Actor>(); }

        /// <summary>Opens the window. reach/radius in world units at scale 1 (multiplied by the actor's scale).</summary>
        public void Open(AttackAnimationData d, DamageInfo info, float reach, float radius, Action<Health, DamageInfo> onHit, bool breakables)
        {
            if (_owner == null) _owner = GetComponent<Actor>();
            _d = d; _info = info; _reach = reach; _radius = radius; _onHit = onHit; _breakables = breakables;
            _done.Clear();
            Hits = 0; IsOpen = true; Opened++;
            Sweep();
        }

        public int Close()
        {
            if (IsOpen) Sweep();
            IsOpen = false;
            return Hits;
        }

        void FixedUpdate() { if (IsOpen) Sweep(); }

        /// <summary>Centre points and radius of the hit shape this step (also drawn as gizmos).</summary>
        public void Shape(List<Vector2> pts, out float r)
        {
            pts.Clear();
            float s = _owner ? _owner.Scale : 1f;
            Vector2 body = _owner ? _owner.Body : (Vector2)transform.position;
            Vector2 f = _owner ? _owner.facing : Vector2.down;
            var shape = _d ? _d.shape : HitShape.Arc;
            r = _radius * s;
            switch (shape)
            {
                case HitShape.Thrust:
                    // three overlapping circles from the hands to the tip of the weapon
                    for (int i = 1; i <= 3; i++) pts.Add(body + f * (_reach * s * i / 3f));
                    r = Mathf.Max(0.25f * s, _radius * s * 0.6f);
                    break;
                case HitShape.Circle:
                    pts.Add(body + f * (_reach * s * 0.3f));
                    break;
                default:
                    // the swing: centre in front plus the two ends of the arc
                    pts.Add(body + f * (_reach * s * 0.75f));
                    float half = (_d ? _d.arc : 140f) * 0.5f * Mathf.Deg2Rad;
                    Vector2 side = new Vector2(-f.y, f.x);
                    float c = Mathf.Cos(Mathf.Min(half, 1.4f)), sn = Mathf.Sin(Mathf.Min(half, 1.4f));
                    pts.Add(body + (f * c + side * sn) * (_reach * s * 0.6f));
                    pts.Add(body + (f * c - side * sn) * (_reach * s * 0.6f));
                    r = _radius * s * 0.8f;
                    break;
            }
        }

        readonly List<Vector2> _pts = new List<Vector2>(4);

        void Sweep()
        {
            Shape(_pts, out float r);
            LastRadius = r;
            LastCenter = _pts.Count > 0 ? _pts[0] : (Vector2)transform.position;
            foreach (var c in _pts)
            {
                int n = Physics2D.OverlapCircle(c, r, ContactFilter2D.noFilter, Buf);
                for (int i = 0; i < n; i++)
                {
                    var col = Buf[i];
                    if (col == null || col.transform.IsChildOf(transform)) continue;
                    var h = col.GetComponentInParent<Health>();
                    if (h != null)
                    {
                        if (!_done.Add(h)) continue;
                        var d = _info;
                        if (d.attacker == null) d.attacker = transform;
                        Vector2 to = (Vector2)h.transform.position - (Vector2)transform.position;
                        d.direction = to.sqrMagnitude > 0.0001f ? to.normalized : (_owner ? _owner.facing : Vector2.down);
                        if (h.Damage(d))
                        {
                            Hits++; TotalHits++;
                            var e = h.GetComponent<EnemyController>();
                            Fx.Spawn(d.source == Team.Player && e != null && e.kind == EnemyKind.BloodMonster ? FxKind.Blood : FxKind.Hit,
                                     (Vector2)h.transform.position + Vector2.up * 0.6f);
                            string snd = Sfx.HitFor(d, h);
                            Sfx.PlayAt(snd == "hit" && _d != null && !string.IsNullOrEmpty(_d.sfxHit) ? _d.sfxHit : snd, (Vector2)h.transform.position, 0.9f);
                            _onHit?.Invoke(h, d);
                        }
                        continue;
                    }
                    if (_breakables)
                    {
                        var b = col.GetComponentInParent<Breakable>();
                        if (b != null && _done.Add(b)) { b.Break(); Hits++; TotalHits++; }
                    }
                }
            }
        }

        void OnDrawGizmos()
        {
            if (!IsOpen) return;
            Shape(_pts, out float r);
            Gizmos.color = new Color(1f, 0.2f, 0.2f, 0.8f);
            foreach (var p in _pts) Gizmos.DrawWireSphere(p, r);
        }
    }
}
