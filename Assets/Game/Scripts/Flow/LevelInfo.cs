using UnityEngine;

namespace WoodsGame
{
    /// <summary>One per level scene: name, camera bounds, start-up (HUD, music, title card).</summary>
    public class LevelInfo : MonoBehaviour
    {
        public static LevelInfo Current { get; private set; }

        public string title = "EL BOSQUE";
        public string subtitle = "";
        [Tooltip("world-space rectangle the camera may show")]
        public Rect bounds = new Rect(0, 0, 40, 28);

        void Awake()
        {
            Current = this;
            GameManager.SetLevelFromScene(gameObject.scene.name);
        }
        void OnDestroy() { if (Current == this) Current = null; }

        void Start()
        {
            GameManager.Ensure();
            UIRoot.ShowHUD(true);
            UIRoot.TitleCard(title, subtitle);
            Sfx.Music(true);
        }
    }
}
