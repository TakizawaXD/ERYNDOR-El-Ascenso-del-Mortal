using System.Collections;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Crafted bomb thrown with Q: flies in an arc and explodes (fire bomb: area damage; poison bomb: damage + venom).</summary>
    public class ThrownBomb : MonoBehaviour
    {
        string _id;
        Vector2 _from, _to;
        PlayerController _owner;

        public static void Throw(string id, Vector2 from, Vector2 dir, PlayerController owner)
        {
            var go = new GameObject("Bomb");
            go.transform.position = from;
            var sr = go.AddComponent<SpriteRenderer>();
            var m = CraftDB.Get(id);
            sr.sprite = GameAssets.I ? GameAssets.I.MatIcon(m != null ? m.icon : 25) : null;
            sr.sortingOrder = 60;
            var b = go.AddComponent<ThrownBomb>();
            b._id = id; b._from = from; b._owner = owner;
            // lands 3.2 units ahead, or on the first wall
            float dist = 3.2f;
            var hit = Physics2D.Raycast(from, dir, dist, ~0);
            if (hit.collider != null && !hit.collider.isTrigger && (owner == null || !hit.collider.transform.IsChildOf(owner.transform))) dist = Mathf.Max(0.6f, hit.distance - 0.2f);
            b._to = from + dir.normalized * dist;
        }

        IEnumerator Start()
        {
            const float T = 0.45f;
            for (float t = 0; t < T; t += Time.deltaTime)
            {
                float k = t / T;
                transform.position = Vector2.Lerp(_from, _to, k) + Vector2.up * Mathf.Sin(k * Mathf.PI) * 1.1f;
                transform.Rotate(0, 0, -720 * Time.deltaTime);
                yield return null;
            }
            transform.position = _to;
            Explode();
        }

        void Explode()
        {
            var s = GameManager.State;
            bool poison = _id == "bomba_veneno";
            Fx.Spawn(poison ? FxKind.Splash : FxKind.Explosion, _to);
            if (poison) { Fx.Spawn(FxKind.Poof, _to + Vector2.left * 0.5f); Fx.Spawn(FxKind.Poof, _to + Vector2.right * 0.5f); }
            Sfx.PlayAt("bomb", transform.position);
            CameraFollow.Shake(0.2f, 0.1f);
            int dmg = poison ? 4 + s.dex / 3 : 8 + s.str / 2;
            Combat.Hit(_to, poison ? 1.9f : 1.6f, new DamageInfo { amount = dmg, knockback = poison ? 2f : 9f, source = Team.Player, heavy = !poison, element = poison ? Element.Venom : Element.Fire }, _owner ? _owner.transform : null);
            Destroy(gameObject);
        }
    }
}
