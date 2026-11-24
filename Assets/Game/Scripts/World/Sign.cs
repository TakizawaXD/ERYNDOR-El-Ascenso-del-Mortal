using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    public class Sign : Interactable
    {
        [TextArea] public string text = "...";
        public override void Interact(PlayerController p) { UIRoot.ShowDialog(text); }
    }
}
