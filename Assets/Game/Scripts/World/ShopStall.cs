namespace WoodsGame
{
    /// <summary>Market stall: opens the shop panel.</summary>
    public class ShopStall : Interactable
    {
        [UnityEngine.Tooltip("blacksmith: sells weapons and armour instead of potions")] public bool smith;
        public override void Interact(PlayerController p)
        {
            if (!smith) { WorldUI.OpenShop(); return; }
            // the anvil: the forge's services (the smith also offers them when you talk to them)
            WorldUI.Choice("Yunque", "Forja, mejora y repara tu equipo.", new[] { "Comprar", "Vender", "Mejorar equipo", "Reparar", "Salir" },
                new System.Action[] { () => WorldUI.OpenTrade(WorldUI.TradeMode.Buy, ""), () => WorldUI.OpenTrade(WorldUI.TradeMode.Sell, ""),
                                      () => WorldUI.OpenTrade(WorldUI.TradeMode.Upgrade, ""), () => WorldUI.OpenTrade(WorldUI.TradeMode.Repair, ""), WorldUI.CloseAll });
        }
    }
}
