using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    public static class Combat
    {
        static readonly List<Collider2D> Buffer = new List<Collider2D>(32);
        static readonly HashSet<Object> Seen = new HashSet<Object>();

        /// <summary>Damages every Health / Breakable of another team inside the circle. Returns hits.</summary>
        public static int Hit(Vector2 center, float radius, DamageInfo info, Transform attacker)
        {
            int n = Physics2D.OverlapCircle(center, radius, ContactFilter2D.noFilter, Buffer);
            int hits = 0;
            Seen.Clear();
            for (int i = 0; i < n; i++)
            {
                var c = Buffer[i];
                if (c == null || (attacker != null && c.transform.IsChildOf(attacker))) continue;
                var h = c.GetComponentInParent<Health>();
                if (h != null && Seen.Add(h))
                {
                    var d = info;
                    if (d.attacker == null) d.attacker = attacker;
                    Vector2 to = (Vector2)h.transform.position - (attacker ? (Vector2)attacker.position : center);
                    d.direction = to.sqrMagnitude > 0.0001f ? to.normalized : info.direction;
                    if (h.Damage(d))
                    {
                        hits++;
                        Fx.Spawn(info.source == Team.Player && h.GetComponent<EnemyController>() is EnemyController e && e.kind == EnemyKind.BloodMonster
                            ? FxKind.Blood : FxKind.Hit, (Vector2)h.transform.position + Vector2.up * 0.6f);
                        Sfx.PlayAt(Sfx.HitFor(d, h), (Vector2)h.transform.position, 0.9f);
                    }
                    continue;
                }
                var b = c.GetComponentInParent<Breakable>();
                if (b != null && Seen.Add(b) && info.source == Team.Player) { b.Break(); hits++; }
            }
            return hits;
        }

        /// <summary>4-way snapped direction (sprites exist for down/up/left/right only).</summary>
        public static Vector2 Snap4(Vector2 v)
        {
            if (v.sqrMagnitude < 0.0001f) return Vector2.down;
            return Mathf.Abs(v.x) >= Mathf.Abs(v.y) ? new Vector2(Mathf.Sign(v.x), 0) : new Vector2(0, Mathf.Sign(v.y));
        }
    }
}
