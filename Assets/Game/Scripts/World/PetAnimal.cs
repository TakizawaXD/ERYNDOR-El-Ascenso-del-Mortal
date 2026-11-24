using UnityEngine;

namespace WoodsGame
{
    /// <summary>E next to the kitten: stroke it (it purrs and follows you around for a while).</summary>
    [RequireComponent(typeof(Animal))]
    public class PetAnimal : Interactable
    {
        Animal _a;
        void Awake() { _a = GetComponent<Animal>(); promptHeight = 1.1f; }
        public override bool CanInteract => _a != null && !_a.shy && !_a.Following && !_a.Petting;
        public override void Interact(PlayerController p) { _a.Pet(p); }
    }
}
