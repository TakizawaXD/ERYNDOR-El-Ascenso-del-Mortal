using UnityEngine;

namespace WoodsGame
{
    /// <summary>The visible way into a boss dungeon. The trigger in front of it is a MapGate (built from Maps.txt) when the
    /// dungeon map exists; until a dungeon has been built the entrance stays sealed and says so.</summary>
    public class DungeonEntrance : Interactable
    {
        public string toMap;
        public string dungeonName = "MAZMORRA";
        public string bossFlag;

        MapGate _gate;
        MapGate Gate => _gate != null ? _gate : (_gate = MapGate.Find(toMap + ":IN"));
        public bool Open => Gate != null;
        public bool Cleared => !string.IsNullOrEmpty(bossFlag) && GameManager.State.Has(bossFlag);
        public override bool CanInteract => true;

        public override void Interact(PlayerController p)
        {
            if (Open) { GameManager.Travel(Gate.toMap, Gate.toGate); return; }
            UIRoot.ShowDialog(dungeonName + ". UNA FUERZA ANTIGUA SELLA LA ENTRADA. AÚN NO PUEDES DESCENDER.");
        }
    }
}
