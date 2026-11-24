using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>A named place of the overworld (dungeon entrance, cemetery, shrine, ruins, village, tower...). It is
    /// revealed on the map (M) the first time you get close; dungeons show their name and location only once found.</summary>
    public class WorldPOI : MonoBehaviour
    {
        public static readonly List<WorldPOI> All = new List<WorldPOI>();
        public string poiName = "LUGAR";
        public string kind = "ruin";              // city village tower dungeon cemetery shrine ruin secret tree volcano
        public float revealRadius = 7f;

        public string Id => "poi_" + MapDB.Key(kind, transform.position, gameObject.scene.name);
        public bool Discovered => GameManager.State.Has(Id);

        void OnEnable() { All.Add(this); }
        void OnDisable() { All.Remove(this); }

        void Update()
        {
            if (Discovered || Time.frameCount % 15 != 0) return;
            var p = PlayerController.Current;
            if (p == null || Vector2.Distance(p.transform.position, transform.position) > revealRadius) return;
            GameManager.State.Set(Id);
            if (kind == "dungeon" || kind == "secret" || kind == "tree" || kind == "cemetery")
                UIRoot.TitleCard(poiName, kind == "dungeon" ? "MAZMORRA DESCUBIERTA" : kind == "secret" ? "LUGAR SECRETO" : "LUGAR DESCUBIERTO");
            else UIRoot.Toast("Descubierto: " + UIRoot.Pretty(poiName), 2.2f);
        }
    }
}
