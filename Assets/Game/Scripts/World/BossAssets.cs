using UnityEngine;

namespace WoodsGame
{
    /// <summary>Art and audio for boss fights and zone atmosphere (Resources/BossAssets, filled by GameBuilder.Bosses).
    /// Kept apart from GameAssets so the boss work does not collide with the rest of the asset table.</summary>
    public class BossAssets : ScriptableObject
    {
        static BossAssets _i;
        public static BossAssets I => _i ? _i : (_i = Resources.Load<BossAssets>("BossAssets"));

        [Header("Boss fight")]
        public AudioClip bossMusic;
        public Sprite wave;              // ground ring (shockwaves)
        public Sprite telegraph;         // impact marker
        public Sprite runes;             // rune circle (white, tinted)
        public Sprite lightColumn;       // vertical additive beam
        public Sprite fog;               // soft fog puff
        [Header("Boss HUD")]
        public Sprite barCap, barTrack, barFill, barCrest, objectivePanel, objectiveIcon;
    }
}
