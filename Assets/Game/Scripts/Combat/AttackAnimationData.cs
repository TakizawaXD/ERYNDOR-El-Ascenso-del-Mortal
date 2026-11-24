using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    public enum HitShape { Arc, Thrust, Circle }
    public enum ProjectileKind { None, Arrow, Magic, Enemy }

    /// <summary>Timing and hitbox of one attack animation (a move of a weapon set, or an enemy's attack).
    /// The times are read from the Animation Events of the clip at speed 1 by the GameBuilder (GameBuilder.Combat.cs):
    /// anticipation -> hitOn (the hitbox opens) -> hitOff (it closes) -> comboWindow (next input accepted) -> end.
    /// At run time the Animator speed is scaled so hitOn lands at the weapon's wind-up time (WeaponStyle).</summary>
    [CreateAssetMenu(menuName = "Woods/Attack Animation Data")]
    public class AttackAnimationData : ScriptableObject
    {
        [Header("Which animation")]
        public string set = "Sword";
        public string move = "Attack";
        [Tooltip("Animator trigger that starts it (empty: started by a bool, e.g. the charged release)")]
        public string trigger = "Attack";
        [Header("Phases (seconds at Animator speed 1, -1 = not in this clip)")]
        public float length = 0.5f;
        public float anticipation = 0.08f;
        public float hitOn = 0.2f;
        public float hitOff = 0.3f;
        public float comboWindow = 0.3f;
        public float projectile = -1f;
        public float end = 0.5f;
        [Header("Hitbox (world units at scale 1, measured on the drawn weapon)")]
        public HitShape shape = HitShape.Arc;
        public float reach = 0.8f;
        public float radius = 0.7f;
        [Range(30, 360)] public float arc = 140f;
        [Header("Effect on the target")]
        public float damageMul = 1f;
        public float knockbackMul = 1f;
        public float staminaMul = 1f;
        public ProjectileKind projectileKind;
        [Header("Look and sound")]
        public string fx = "sword";
        public string sfxSwing = "wpn_swing_blade";
        public string sfxHit = "hit_blade";
        public float shake;

        public bool HasHit => hitOn >= 0f;
        public bool HasProjectile => projectile >= 0f;
        public float FirstAction => HasHit ? hitOn : HasProjectile ? projectile : end * 0.5f;

        /// <summary>Animator speed that makes the first action of the clip happen after `seconds`.</summary>
        public float SpeedFor(float seconds) => Mathf.Clamp(FirstAction / Mathf.Max(0.04f, seconds), 0.5f, 2.2f);

        /// <summary>A data object built in code (fallback when no asset exists: tests, unknown sets).</summary>
        public static AttackAnimationData Make(string set, string move, float hitOn, float hitOff, float end, float reach, float radius,
                                               HitShape shape = HitShape.Arc, float projectile = -1f)
        {
            var d = CreateInstance<AttackAnimationData>();
            d.name = $"{set}_{move}"; d.set = set; d.move = move; d.trigger = move;
            d.hitOn = hitOn; d.hitOff = hitOff; d.end = d.length = end; d.comboWindow = hitOff; d.anticipation = hitOn * 0.5f;
            d.reach = reach; d.radius = radius; d.shape = shape; d.projectile = projectile;
            return d;
        }
    }
}
