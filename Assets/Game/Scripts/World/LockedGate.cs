using UnityEngine;

namespace WoodsGame
{
    /// <summary>A barred pass that needs a regional key (found in a hidden glade or a dungeon). Once opened it stays open.
    /// Also used for lever shortcuts: those have no key and open from their lever.</summary>
    public class LockedGate : Interactable
    {
        public string keyFlag;                 // key_torre, key_ruinas ... (empty = lever gate)
        public string keyName = "LLAVE";
        public string gateName = "PORTÓN";
        public string openFlag;                // saved once open
        public Sprite closed, opened;

        Collider2D _col; SpriteRenderer _sr;

        public bool IsOpen => GameManager.State.Has(openFlag);
        public override bool CanInteract => !IsOpen && !string.IsNullOrEmpty(keyFlag);

        void Awake() { _col = GetComponent<Collider2D>(); _sr = GetComponent<SpriteRenderer>(); }
        void Start() { Show(); }

        void Show()
        {
            bool open = IsOpen;
            if (_col) _col.enabled = !open;
            if (_sr && closed && opened) _sr.sprite = open ? opened : closed;
        }

        public override void Interact(PlayerController p)
        {
            if (IsOpen) return;
            if (!GameManager.State.Has(keyFlag))
            {
                Sfx.Play("block");
                UIRoot.ShowDialog(gateName + ". CERRADO CON UN CANDADO ANTIGUO. NECESITAS: " + keyName + ".");
                return;
            }
            OpenNow();
            UIRoot.TitleCard(gateName, "ABIERTO CON " + keyName);
        }

        public void OpenNow()
        {
            GameManager.State.Set(openFlag);
            Sfx.Play("chest", 0.9f);
            CameraFollow.Shake(0.15f, 0.06f);
            Show();
        }
    }
}
