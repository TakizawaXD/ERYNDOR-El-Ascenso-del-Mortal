using UnityEngine;

namespace WoodsGame
{
    /// <summary>Enemy side of the animation system: the attack data of this enemy type (filled by the GameBuilder from
    /// its clips: the PrepareAttack -> Attack -> AttackRecovery chain, the heavy and the special/ranged attack) and the
    /// telegraph tint. EnemyController.Melee / Ranged run the attacks through <see cref="CharacterAnimationController.RunAttack"/>.</summary>
    public class EnemyAnimationController : CharacterAnimationController
    {
        public AttackAnimationData attack, heavy, special;

        /// <summary>Data for the move, with a code fallback for prefabs built before the combat data existed.</summary>
        public AttackAnimationData Data(string move, float reach, float radius)
        {
            var d = move == "HeavyAttack" ? heavy : move == "SpecialAttack" ? special : attack;
            if (d != null) return d;
            switch (move)
            {
                case "HeavyAttack": return heavy = AttackAnimationData.Make("Enemy", "HeavyAttack", 0.42f, 0.55f, 0.85f, reach, radius * 1.25f);
                case "SpecialAttack": return special = AttackAnimationData.Make("Enemy", "SpecialAttack", -1f, -1f, 0.7f, reach, radius, HitShape.Arc, 0.45f);
            }
            return attack = AttackAnimationData.Make("Enemy", "Attack", 0.3f, 0.42f, 0.7f, reach, radius);
        }

        public bool HasPhaseClips
        {
            get
            {
                if (!Animator || !Animator.isActiveAndEnabled || Animator.runtimeAnimatorController == null) return false;
                return Animator.HasState(0, Animator.StringToHash("PrepareAttack"));
            }
        }
    }
}
