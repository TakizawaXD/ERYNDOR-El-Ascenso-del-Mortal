using UnityEngine;

namespace WoodsGame
{
    /// <summary>Swaps a sprite between day and night (interior windows show the dark sky at night).</summary>
    public class DayNightSprite : MonoBehaviour
    {
        public Sprite day, night;
        SpriteRenderer _sr;
        void Awake() { _sr = GetComponent<SpriteRenderer>(); }
        void Update() { if (_sr && Time.frameCount % 15 == 0) _sr.sprite = DayNight.IsNight ? night : day; }
    }
}
