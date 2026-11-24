using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Crates, barrels, pots: break on hit, maybe drop something.</summary>
    public class Breakable : MonoBehaviour
    {
        public Sprite broken;
        public float coinChance = 0.4f;
        public float potionChance = 0.05f;
        bool _done;

        public void Break()
        {
            if (_done) return;
            _done = true;
            Sfx.PlayAt("break", transform.position);
            Fx.Spawn(FxKind.Poof, transform.position + Vector3.up * 0.3f);
            var a = GameAssets.I;
            if (Random.value < coinChance) Pickup.Drop(a.coinPrefab, transform.position);
            if (Random.value < potionChance) Pickup.Drop(a.potionPrefab, transform.position);
            foreach (var c in GetComponentsInChildren<Collider2D>()) c.enabled = false;
            var sr = GetComponent<SpriteRenderer>();
            if (broken && sr) { sr.sprite = broken; sr.sortingOrder = -1; }
            else Destroy(gameObject);
        }
    }
}
