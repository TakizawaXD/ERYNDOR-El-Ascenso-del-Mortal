using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Every AttackAnimationData of the player's weapon sets (Resources/Combat/AttackLibrary.asset).</summary>
    public class AttackLibrary : ScriptableObject
    {
        public List<AttackAnimationData> attacks = new List<AttackAnimationData>();

        static AttackLibrary _i;
        static Dictionary<string, AttackAnimationData> _map;

        public static AttackLibrary I
        {
            get
            {
                if (_i == null) _i = Resources.Load<AttackLibrary>("Combat/AttackLibrary");
                return _i;
            }
        }

        public static AttackAnimationData Find(string set, string move)
        {
            if (_map == null)
            {
                _map = new Dictionary<string, AttackAnimationData>();
                if (I != null) foreach (var a in I.attacks) if (a != null) _map[a.set + "/" + a.move] = a;
            }
            return _map.TryGetValue(set + "/" + move, out var d) ? d : null;
        }
    }
}
