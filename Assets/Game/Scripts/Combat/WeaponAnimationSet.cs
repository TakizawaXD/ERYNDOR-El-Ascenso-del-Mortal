using System;
using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>All weapon animation sets of one character class (Resources/Combat/WeaponSets_&lt;Character&gt;.asset):
    /// an AnimatorOverrideController per melee set and the four SpecialAttack clips of every bow set.
    /// Filled by GameBuilder.Combat.cs from Assets/Art/Animations/Characters/WeaponSets.</summary>
    public class WeaponAnimationSet : ScriptableObject
    {
        [Serializable] public class Melee { public string set; public AnimatorOverrideController controller; }
        [Serializable] public class Bow { public string set; public AnimationClip[] clips = new AnimationClip[4]; }   // Down, Up, Left, Right

        public string character = "Soldier";
        public List<Melee> melee = new List<Melee>();
        public List<Bow> bows = new List<Bow>();

        public static readonly string[] Dirs = { "Down", "Up", "Left", "Right" };

        public AnimatorOverrideController Controller(string set)
        {
            foreach (var m in melee) if (m.set == set) return m.controller;
            return null;
        }

        public Bow BowClips(string set)
        {
            foreach (var b in bows) if (b.set == set) return b;
            return null;
        }

        static readonly Dictionary<string, WeaponAnimationSet> Cache = new Dictionary<string, WeaponAnimationSet>();

        public static WeaponAnimationSet For(string character)
        {
            if (string.IsNullOrEmpty(character)) return null;
            if (!Cache.TryGetValue(character, out var s) || s == null)
                Cache[character] = s = Resources.Load<WeaponAnimationSet>("Combat/WeaponSets_" + character);
            return s;
        }
    }
}
