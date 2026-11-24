using UnityEngine;

namespace WoodsGame
{
    /// <summary>Front door of a house in the world: E to go inside.</summary>
    public class HouseDoor : Interactable
    {
        public Interior interior;
        public override bool CanInteract => interior != null && Interior.Current == null;
        public override void Interact(PlayerController p) { GameManager.EnterInterior(interior); }
    }
}
