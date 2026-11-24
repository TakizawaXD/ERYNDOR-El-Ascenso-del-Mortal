using UnityEngine;

namespace WoodsGame
{
    /// <summary>A lever beside an iron gate: pull it (E) to open a shortcut for good.</summary>
    public class ShortcutLever : Interactable
    {
        public LockedGate gate;
        public string shortcutName = "ATAJO";
        public Sprite up, down;
        SpriteRenderer _sr;

        public override bool CanInteract => gate != null && !gate.IsOpen;

        void Start() { _sr = GetComponent<SpriteRenderer>(); if (_sr && gate && gate.IsOpen && down) _sr.sprite = down; }

        public override void Interact(PlayerController p)
        {
            if (gate == null || gate.IsOpen) return;
            if (_sr && down) _sr.sprite = down;
            gate.OpenNow();
            UIRoot.TitleCard("ATAJO ABIERTO", shortcutName);
        }
    }
}
