using UnityEngine;

namespace WoodsGame
{
    /// <summary>Sleep: at night until dawn, by day until dusk. Full health and the game is saved here.</summary>
    public class Bed : Interactable
    {
        public override void Interact(PlayerController p) { GameManager.Sleep((Vector2)transform.position + Vector2.down * 0.9f); }
    }
}
