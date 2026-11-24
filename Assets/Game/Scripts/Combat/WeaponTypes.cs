using UnityEngine;

namespace WoodsGame
{
    /// <summary>The "WeaponType" layer of the combat animation system: which animation set, sounds and effects every
    /// weapon uses. The weapon kinds themselves are <see cref="WeaponKind"/> (ItemDB); a set is the group of animations
    /// drawn for a family of weapons (Tools/CharAnim/weaponsets.py), e.g. both katanas share "Katana" and every
    /// legendary melee weapon uses the "Legendary" set.</summary>
    public static class WeaponTypes
    {
        public static readonly string[] MeleeSets =
            { "Sword", "Greatsword", "Katana", "Rapier", "Dagger", "Spear", "Axe", "HeavyAxe", "Hammer", "Staff", "Legendary" };
        public static readonly string[] BowSets = { "Bow", "Longbow", "Crossbow" };

        /// <summary>Animation set of a melee weapon (null / unknown -> Sword).</summary>
        public static string SetFor(ItemDef w)
        {
            if (w == null) return "Sword";
            if (w.slot == ItemSlot.Bow) return BowSet(w.kind);
            if (w.rarity == Rarity.Legendary && w.kind != WeaponKind.Staff) return "Legendary";
            return SetFor(w.kind);
        }

        public static string SetFor(WeaponKind k)
        {
            switch (k)
            {
                case WeaponKind.Greatsword: return "Greatsword";
                case WeaponKind.Katana: return "Katana";
                case WeaponKind.Rapier: return "Rapier";
                case WeaponKind.Dagger: return "Dagger";
                case WeaponKind.Spear: return "Spear";
                case WeaponKind.Axe: return "Axe";
                case WeaponKind.HeavyAxe: return "HeavyAxe";
                case WeaponKind.Hammer: return "Hammer";
                case WeaponKind.Staff: return "Staff";
                case WeaponKind.Bow: case WeaponKind.Longbow: case WeaponKind.Crossbow: return BowSet(k);
            }
            return "Sword";
        }

        public static string BowSet(WeaponKind k) => k == WeaponKind.Longbow ? "Longbow" : k == WeaponKind.Crossbow ? "Crossbow" : "Bow";

        public static bool IsMagic(string set) => set == "Staff";
        public static bool TwoHanded(string set) => set == "Greatsword" || set == "HeavyAxe" || set == "Hammer" || set == "Spear";

        /// <summary>The swing sound of a set (sfx_wpn_* of Tools/GameGen/sfx_weapons.py; falls back to the older swings).</summary>
        public static string SwingSfx(string set, bool heavy)
        {
            switch (set)
            {
                case "Dagger": case "Katana": case "Rapier": return heavy ? "wpn_swing_blade" : "wpn_swing_light";
                case "Spear": return "wpn_thrust";
                case "Greatsword": case "HeavyAxe": case "Hammer": return "wpn_swing_heavy";
                case "Axe": return heavy ? "wpn_swing_heavy" : "wpn_swing_blade";
                case "Staff": return heavy ? "magic_charge" : "wpn_swing_staff";
                case "Legendary": return "wpn_swing_legend";
                case "Bow": case "Longbow": return "bow_draw";
                case "Crossbow": return "crossbow_load";
            }
            return heavy ? "wpn_swing_heavy" : "wpn_swing_blade";
        }

        /// <summary>Impact sound of a weapon on flesh (the element / critical sounds of Sfx.HitFor still win).</summary>
        public static string HitSfx(string set)
        {
            switch (set)
            {
                case "Hammer": case "Staff": return "hit_blunt";
                case "Spear": case "Rapier": case "Dagger": return "hit_pierce";
            }
            return "hit_blade";
        }

        /// <summary>Weapon trail sheet (Assets/Art/Effects/Weapons/fx_&lt;name&gt;_anim_32x32.png).</summary>
        public static string TrailFx(string set, string move)
        {
            bool heavy = move == "HeavyAttack" || move == "ComboAttack" || move == "ChargedAttack_Release";
            switch (set)
            {
                case "Spear": case "Rapier": return heavy && set == "Spear" ? "spear_sweep" : "thrust";
                case "Dagger": return "dagger";
                case "Katana": return "katana";
                case "Greatsword": return "greatsword";
                case "Axe": case "HeavyAxe": return "axe";
                case "Hammer": return "impact";
                case "Staff": return "magic";
                case "Legendary": return "legend";
            }
            return heavy ? "greatsword" : "sword";
        }

        /// <summary>Ground effect on a heavy blow (dust ring / shockwave).</summary>
        public static bool Shockwave(string set, string move) =>
            (set == "Hammer" || set == "HeavyAxe" || set == "Greatsword") && (move == "HeavyAttack" || move == "ComboAttack" || move == "ChargedAttack_Release" || move == "Attack");

        public static Color MagicColor(ItemDef w)
        {
            if (w != null && w.element == Element.Frost) return new Color(0.6f, 0.9f, 1f);
            if (w != null && w.element == Element.Fire) return new Color(1f, 0.6f, 0.3f);
            return new Color(0.55f, 0.85f, 1f);
        }
    }
}
