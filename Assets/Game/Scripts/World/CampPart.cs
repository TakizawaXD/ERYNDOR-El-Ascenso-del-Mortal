using UnityEngine;

namespace WoodsGame
{
    /// <summary>One piece of a campsite. Each opens its own part of the camp directly.</summary>
    public class CampPart : Interactable
    {
        public enum Role { Tent, Workbench, Stash }
        public Role role;
        public Campfire camp;

        public override void Interact(PlayerController p)
        {
            if (camp != null) camp.Rest(p);
            switch (role)
            {
                case Role.Tent: GameManager.Sleep(camp != null ? camp.Spot : (Vector2)transform.position + Vector2.down); break;
                case Role.Workbench: WorldUI.OpenCraft(false); break;
                case Role.Stash: WorldUI.OpenStash(); break;
            }
        }
    }
}
