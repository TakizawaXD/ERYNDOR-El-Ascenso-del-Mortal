using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Player side of the animation system: swaps the animation set when the equipped weapon or bow changes.
    /// The class controller (Soldier, KnightPaladin...) is replaced by the AnimatorOverrideController of the weapon's
    /// set (sword, greatsword, katana, rapier, daggers, spear, axe, heavy axe, hammer, staff, legendary) and the bow's
    /// SpecialAttack clips are laid over it, so every move of the Animator plays the animation of the weapon in hand.</summary>
    public class WeaponAnimationController : CharacterAnimationController
    {
        public string CurrentSet { get; private set; } = "";
        public string CurrentBow { get; private set; } = "";
        public int Swaps { get; private set; }
        /// <summary>True when a real set was found (false = the plain class controller is used).</summary>
        public bool HasSet { get; private set; }

        RuntimeAnimatorController _classController;
        string _character;
        readonly Dictionary<string, AnimatorOverrideController> _cache = new Dictionary<string, AnimatorOverrideController>();

        /// <summary>The class controller and its sprite name (called by PlayerController after the class is applied).</summary>
        public void SetClass(RuntimeAnimatorController ctrl, string character)
        {
            Bind();
            if (ctrl == _classController && character == _character) return;
            _classController = ctrl; _character = character;
            _cache.Clear(); CurrentSet = CurrentBow = "";
        }

        /// <summary>Applies the animation sets of these weapons (no-op when they did not change).</summary>
        public void Equip(ItemDef weapon, ItemDef bow, Vector2 facing)
        {
            Bind();
            if (!Animator) return;
            string set = WeaponTypes.SetFor(weapon);
            string bset = bow != null ? WeaponTypes.BowSet(bow.kind) : "Bow";
            if (set == CurrentSet && bset == CurrentBow) return;
            CurrentSet = set; CurrentBow = bset;
            Swaps++;
            var lib = WeaponAnimationSet.For(_character);
            string key = set + "|" + bset;
            if (!_cache.TryGetValue(key, out var ov))
            {
                var baseOv = lib != null ? lib.Controller(set) : null;
                HasSet = baseOv != null;
                RuntimeAnimatorController src = baseOv != null ? (RuntimeAnimatorController)baseOv : _classController;
                if (src == null) return;
                ov = new AnimatorOverrideController(src) { name = $"{_character}_{set}_{bset}" };
                var b = lib != null ? lib.BowClips(bset) : null;
                if (b != null)
                {
                    var pairs = new List<KeyValuePair<AnimationClip, AnimationClip>>(ov.overridesCount);
                    ov.GetOverrides(pairs);
                    for (int i = 0; i < pairs.Count; i++)
                    {
                        var orig = pairs[i].Key;
                        if (orig == null) continue;
                        for (int d = 0; d < 4; d++)
                            if (orig.name == $"{_character}_SpecialAttack_{WeaponAnimationSet.Dirs[d]}" && b.clips[d] != null)
                                pairs[i] = new KeyValuePair<AnimationClip, AnimationClip>(orig, b.clips[d]);
                    }
                    ov.ApplyOverrides(pairs);
                }
                _cache[key] = ov;
            }
            else HasSet = lib != null && lib.Controller(set) != null;
            Animator.runtimeAnimatorController = ov;
            // a new controller restarts the Animator: give it the facing back at once (no one-frame pose pop)
            Animator.SetFloat("MoveX", facing.x); Animator.SetFloat("MoveY", facing.y);
            Animator.Update(0f);
        }

        /// <summary>Timing + hitbox of a move of the current set (or of the bow for SpecialAttack).</summary>
        public AttackAnimationData Data(string move, WeaponStyle st)
        {
            string set = move == "SpecialAttack" ? CurrentBow : CurrentSet;
            var d = AttackLibrary.Find(set, move);
            if (d != null) return d;
            // fallback when the library is missing (old build): proportional to the weapon style
            float on = Mathf.Max(0.1f, st.windup), off = on + 0.1f, end = on + st.recover + 0.1f;
            return AttackAnimationData.Make(set, move, move == "SpecialAttack" ? -1f : on, off, end, st.reach, st.radius,
                                            set == "Spear" || set == "Rapier" ? HitShape.Thrust : HitShape.Arc, move == "SpecialAttack" ? on : -1f);
        }
    }
}
