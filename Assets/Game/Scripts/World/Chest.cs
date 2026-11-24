using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    public class Chest : Interactable
    {
        public Sprite[] frames;          // closed ... open
        public int coins = 5;
        public int potions;
        public int arrows;
        [Tooltip("regional key inside (key_torre, key_ruinas...): opening the chest gives it")]
        public string keyId;
        public string keyName;
        bool _open;
        SpriteRenderer _sr;

        public bool IsOpen => _open;
        public override bool CanInteract => !_open;

        string Id => MapDB.Key("chest", transform.position, gameObject.scene.name);

        void Awake() { _sr = GetComponent<SpriteRenderer>(); }

        void Start()
        {
            // opened in this save already: show it open and empty
            if (GameManager.State.Has(Id)) { _open = true; if (frames != null && frames.Length > 0) _sr.sprite = frames[frames.Length - 1]; }
        }

        public override void Interact(PlayerController p)
        {
            if (_open) return;
            _open = true;
            GameManager.State.Set(Id);
            GameManager.State.chestsOpened++;
            Quests.Refresh();
            Sfx.Play("chest");
            StartCoroutine(OpenRoutine());
        }

        IEnumerator OpenRoutine()
        {
            if (frames != null)
                for (int i = 0; i < frames.Length; i++) { _sr.sprite = frames[i]; yield return new WaitForSeconds(0.08f); }
            var a = GameAssets.I;
            for (int i = 0; i < coins; i++) Pickup.Drop(a.coinPrefab, transform.position + Vector3.down * 0.4f);
            // no potions any more: chests hold medicine ingredients (and sometimes a finished remedy)
            for (int i = 0; i < potions; i++) Pickup.DropMat(i == 0 ? "venda" : "hierba", transform.position + Vector3.down * 0.4f, 2);
            if ((Mathf.RoundToInt(transform.position.x) + Mathf.RoundToInt(transform.position.y)) % 3 == 2) Pickup.DropMat("frasco", transform.position + Vector3.down * 0.4f, 2);
            if (arrows > 0) { var pk = Pickup.Drop(a.arrowsPickupPrefab, transform.position + Vector3.down * 0.4f); if (pk) pk.amount = arrows; }
            // half of the chests hold a weapon or armour (deterministic per chest so reloading does not reroll)
            int seed = Mathf.Abs(Mathf.RoundToInt(transform.position.x * 31 + transform.position.y * 17));
            if (seed % 2 == 0)
            {
                var old = Random.state; Random.InitState(seed);
                var item = ItemDB.Roll(ItemDB.RollRarity(GameManager.State.Threat, Rarity.Common), Rarity.Epic);
                Random.state = old;
                if (item != null) Pickup.DropItem(item, transform.position + Vector3.down * 0.5f);
            }
            Fx.Spawn(FxKind.Sparkle, transform.position + Vector3.up * 0.5f);
            if (!string.IsNullOrEmpty(keyId) && GameManager.State.Set(keyId))
                UIRoot.TitleCard("OBTIENES: " + keyName, "ABRE UN PASO CERRADO DEL MUNDO");
        }
    }
}
