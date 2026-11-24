using System;
using UnityEngine;

namespace WoodsGame
{
    public enum Team { Player, Enemy, Neutral }

    public struct DamageInfo
    {
        public int amount;
        public Vector2 direction;   // push direction (from attacker to victim)
        public float knockback;     // units/second of initial push
        public Team source;
        public bool heavy;
        public bool crit;
        public Element element;
        public Transform attacker;  // who swung (melee hits can be parried; null for traps / damage over time)
        public bool ranged;         // arrows, fireballs, spit: can be blocked but not parried
    }

    /// <summary>Hit points, invulnerability window and damage/heal events.</summary>
    public class Health : MonoBehaviour
    {
        public Team team = Team.Enemy;
        public int maxHP = 6;
        public int hp = 6;
        public float invulnerableAfterHit = 0.25f;

        public bool IsDead => hp <= 0;
        public bool Invulnerable => _forcedInvuln || Time.time < _invulnUntil;

        public event Action<DamageInfo> Damaged;
        public event Action Died;
        public event Action Changed;
        /// <summary>Optional last word on incoming damage (defense, dodge, block). Return amount 0 to cancel the hit.</summary>
        public Func<DamageInfo, DamageInfo> filter;
        /// <summary>Raised when a hit was cancelled by the filter (blocked / dodged).</summary>
        public event Action<DamageInfo> Avoided;

        float _invulnUntil;
        bool _forcedInvuln;

        public void SetInvulnerable(bool on) { _forcedInvuln = on; }

        public void Init(int max, int current = -1)
        {
            maxHP = Mathf.Max(1, max);
            hp = current < 0 ? maxHP : Mathf.Clamp(current, 0, maxHP);
            Changed?.Invoke();
        }

        public bool Damage(DamageInfo info)
        {
            if (IsDead || Invulnerable || info.source == team || info.amount <= 0) return false;
            if (filter != null)
            {
                info = filter(info);
                if (info.amount <= 0) { _invulnUntil = Time.time + 0.15f; Avoided?.Invoke(info); return false; }
            }
            hp = Mathf.Max(0, hp - info.amount);
            _invulnUntil = Time.time + invulnerableAfterHit;
            Damaged?.Invoke(info);
            Changed?.Invoke();
            if (hp == 0) Died?.Invoke();
            return true;
        }

        public int Heal(int amount)
        {
            if (IsDead) return 0;
            int before = hp;
            hp = Mathf.Min(maxHP, hp + amount);
            Changed?.Invoke();
            return hp - before;
        }
    }
}
