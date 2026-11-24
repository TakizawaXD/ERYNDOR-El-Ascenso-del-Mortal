using UnityEngine;

namespace WoodsGame
{
    /// <summary>The door mat inside a house: walk onto it (or press E) to go back outside.</summary>
    public class InteriorExit : Interactable
    {
        public Interior interior;
        public override bool CanInteract => Interior.Current == interior;
        public override void Interact(PlayerController p) { GameManager.ExitInterior(); }

        void OnTriggerEnter2D(Collider2D other)
        {
            if (Interior.Current != interior || Time.time - Interior.EnteredAt < 0.8f) return;
            var p = other.GetComponentInParent<PlayerController>();
            if (p != null && p.facing.y < 0) GameManager.ExitInterior();
        }
    }
}
