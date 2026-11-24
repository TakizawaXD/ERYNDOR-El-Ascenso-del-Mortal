using UnityEngine;

namespace WoodsGame
{
    public enum PickupKind { Coin, Potion, Arrows, Heart, Item, Material }

    /// <summary>Collectable: bobs, is pulled toward the nearby player, applies itself on touch.</summary>
    public class Pickup : MonoBehaviour
    {
        public PickupKind kind = PickupKind.Coin;
        public int amount = 1;
        public float magnetRadius = 1.4f;
        public string itemId;
        Transform _gfx;
        float _t0;
        Vector2 _scatter;
        float _scatterUntil;

        public static Pickup Drop(GameObject prefab, Vector2 at)
        {
            if (prefab == null) return null;
            var p = Instantiate(prefab, at, Quaternion.identity).GetComponent<Pickup>();
            p._scatter = Random.insideUnitCircle.normalized * Random.Range(1.5f, 3f);
            p._scatterUntil = Time.time + 0.25f;
            return p;
        }

        /// <summary>Drops a weapon or armour (uses the coin prefab with the item icon and a rarity glow).</summary>
        public static Pickup DropItem(ItemDef item, Vector2 at)
        {
            var a = GameAssets.I;
            var p = Drop(a.coinPrefab, at);
            if (p == null) return null;
            p.kind = PickupKind.Item; p.itemId = item.id; p.amount = 1; p.magnetRadius = 1.0f;
            var sr = p.GetComponentInChildren<SpriteRenderer>();
            if (sr) sr.sprite = a.ItemIcon(item.icon);
            LightGlow.Attach(p.transform, new Vector2(0, 0.3f), item.rarity >= Rarity.Epic ? 1.6f : 1.1f, item.RarityColor, 0.7f, true);
            return p;
        }

        /// <summary>Drops a crafting material or consumable (coin prefab with the material icon).</summary>
        public static Pickup DropMat(string id, Vector2 at, int amount = 1)
        {
            var m = CraftDB.Get(id); var a = GameAssets.I;
            if (m == null || a == null) return null;
            var p = Drop(a.coinPrefab, at);
            if (p == null) return null;
            p.kind = PickupKind.Material; p.itemId = id; p.amount = amount; p.magnetRadius = 1.6f;
            var sr = p.GetComponentInChildren<SpriteRenderer>();
            if (sr) sr.sprite = a.MatIcon(m.icon);
            return p;
        }

        void Awake()
        {
            _gfx = transform.childCount > 0 ? transform.GetChild(0) : transform;
            _t0 = Random.value * 6f;
        }

        void Update()
        {
            if (Time.time < _scatterUntil) transform.position += (Vector3)(_scatter * Time.deltaTime);
            if (_gfx != transform) _gfx.localPosition = new Vector3(0, Mathf.Round((Mathf.Sin((Time.time + _t0) * 4f) * 0.5f + 0.5f) * 2f) / 16f, 0);
            var p = PlayerController.Current;
            if (p != null && !p.health.IsDead && Time.time > _scatterUntil)
            {
                float d = Vector2.Distance(p.transform.position, transform.position);
                if (d < magnetRadius) transform.position = Vector2.MoveTowards(transform.position, p.transform.position, (5f - d * 2f) * Time.deltaTime);
                if (d < 0.35f) Collect(p);
            }
        }

        static void Give(PlayerState s, string id, int n)
        {
            var m = CraftDB.Get(id); if (m == null) return;
            int stored = s.Give(id, n);
            Sfx.Play("gather", 0.7f);
            UIRoot.MatToast(m, n, stored);
        }

        void Collect(PlayerController p)
        {
            var s = GameManager.State;
            switch (kind)
            {
                case PickupKind.Coin: s.coins += s.classId == "merc" ? amount + (amount + 1) / 2 : amount; Sfx.Play("coin", 0.7f); break;   // Mercenario: codicia
                case PickupKind.Potion: Give(s, "medicina", amount); break;      // old map potions are now medicine
                case PickupKind.Material: Give(s, itemId, amount); break;
                case PickupKind.Arrows: s.arrows += amount; Sfx.Play("coin", 0.7f); UIRoot.Toast("+" + amount + " FLECHAS"); break;
                case PickupKind.Heart: p.Heal(amount); break;
                case PickupKind.Item:
                {
                    var it = ItemDB.Get(itemId);
                    if (it == null) break;
                    if (!s.AddItem(it.id)) { s.coins += it.price / 4 + 5; UIRoot.Toast($"{it.name} (repetido): +{it.price / 4 + 5} monedas"); }
                    else UIRoot.ItemToast(it);
                    Sfx.Play("chest", 0.8f);
                    break;
                }
            }
            Fx.Spawn(FxKind.Sparkle, transform.position + Vector3.up * 0.3f);
            Destroy(gameObject);
        }
    }
}
