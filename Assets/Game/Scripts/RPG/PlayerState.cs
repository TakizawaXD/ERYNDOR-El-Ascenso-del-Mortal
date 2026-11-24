using System;
using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Everything that persists: class, attributes, inventory, progression, world flags, clock and the save position.</summary>
    [Serializable]
    public class PlayerState
    {
        // ---------------------------------------------------------------- class + attributes
        public string classId = KnightClass.Default;
        public string heroName = "";                          // the name the player gave the character ("" = the class name)
        public string DisplayName => string.IsNullOrEmpty(heroName) ? Class.shortName : heroName;
        public int str = 3, vit = 4, agi = 3, dex = 3, def = 3;   // FUERZA, VITALIDAD, AGILIDAD, DESTREZA, DEFENSA
        public int attrPoints;

        // ---------------------------------------------------------------- stats + inventory
        public int maxHP = 12, hp = 12, coins, arrows = 10, potions, kills;   // potions: legacy (old saves), see Migrate
        public int level = 1, xp;
        public int swordBonus, heartsBought;
        public int orcKills, bloodKills, demonKills, chestsOpened, eliteKills, champions;
        public List<string> flags = new List<string>();      // boss_K, boss_Q, boss_B, chest_x_y, region_a, buy_sword_n...
        public float saveX = -1, saveY = -1;                  // last campfire / bed (respawn + continue point)
        public float autoX = -1, autoY = -1;                  // autosave: where you were (Continue starts here; dying uses the rest point)
        public string saveMap = "";                           // scene of that rest point ("" in old saves = World)
        public string map = "";                               // scene (map) you are in right now
        public List<string> defeated = new List<string>();    // "map|x|y|until": map residents killed, back after 'until' (game minutes)
        public float TotalMinutes => day * 1440f + clock;     // game time that never wraps (respawn timers across maps)

        // ---------------------------------------------------------------- equipment
        public List<string> inventory = new List<string>();
        public string weapon = "sword_long", bow = "bow_short", armor = "armor_chain";

        public ItemDef Weapon => ItemDB.Get(weapon) ?? ItemDB.Get("sword_short");
        public ItemDef Bow => ItemDB.Get(bow) ?? ItemDB.Get("bow_short");
        public ItemDef ArmorItem => ItemDB.Get(armor) ?? ItemDB.Get("armor_cloth");

        public bool Owns(string id) => inventory.Contains(id) || weapon == id || bow == id || armor == id;

        // ---------------------------------------------------------------- materials, consumables, storage (CraftDB)
        public List<ItemStack> bag = new List<ItemStack>();        // carried (capped per stack, see MatDef.BagCap)
        public List<ItemStack> stash = new List<ItemStack>();      // camp storage (shared by every camp)
        public List<ItemStack> upgrades = new List<ItemStack>();   // equipment id -> forge level (+1..+5)
        public List<ItemStack> wear = new List<ItemStack>();       // equipment id -> durability lost
        public string quick = "venda";                             // selected quick item (Q uses it, R cycles)
        public string ammo = "";                                   // special arrows loaded in the bow
        public string oil = ""; public int oilHits;                // weapon oil and the hits it has left
        public List<NpcMemory> npcs = new List<NpcMemory>();       // what every townsperson remembers about you
        public List<string> summons = new List<string>();          // enemy types bound by the Summoner's curse (max 4)
        public bool migrated;                                      // old saves: potions turned into medicine once

        static int Find(List<ItemStack> l, string id) { for (int i = 0; i < l.Count; i++) if (l[i].id == id) return i; return -1; }
        public static int CountIn(List<ItemStack> l, string id) { int i = Find(l, id); return i < 0 ? 0 : l[i].n; }
        public int InBag(string id) => CountIn(bag, id);
        public int InStash(string id) => CountIn(stash, id);
        /// <summary>Bag + camp storage (crafting at a camp can use both).</summary>
        public int Total(string id) => InBag(id) + InStash(id);

        public static void AddTo(List<ItemStack> l, string id, int n)
        {
            if (n <= 0) return;
            int i = Find(l, id);
            if (i < 0) l.Add(new ItemStack(id, n)); else l[i].n += n;
        }

        public static int TakeFrom(List<ItemStack> l, string id, int n)
        {
            int i = Find(l, id); if (i < 0 || n <= 0) return 0;
            int k = Mathf.Min(n, l[i].n);
            l[i].n -= k; if (l[i].n <= 0) l.RemoveAt(i);
            return k;
        }

        /// <summary>Adds to the bag up to the carry cap; the rest is sent to the camp storage. Returns how many went to storage.</summary>
        public int Give(string id, int n = 1)
        {
            var m = CraftDB.Get(id); if (m == null || n <= 0) return 0;
            int room = Mathf.Max(0, m.BagCap - InBag(id));
            int toBag = Mathf.Min(room, n);
            AddTo(bag, id, toBag);
            AddTo(stash, id, n - toBag);
            if (m.Consumable && (string.IsNullOrEmpty(quick) || InBag(quick) == 0)) quick = id;
            return n - toBag;
        }

        /// <summary>Uses materials from the bag first, then (when allowed, at a camp) from storage.</summary>
        public bool Consume(string id, int n, bool useStash)
        {
            if ((useStash ? Total(id) : InBag(id)) < n) return false;
            int k = TakeFrom(bag, id, n);
            if (k < n) TakeFrom(stash, id, n - k);
            return true;
        }

        public int Level(string itemId) => CountIn(upgrades, itemId);
        public int Wear(string itemId) => CountIn(wear, itemId);
        public int Durability(string itemId) => Mathf.Max(0, CraftDB.MaxDurability(ItemDB.Get(itemId)) - Wear(itemId));
        public bool Broken(string itemId) => !string.IsNullOrEmpty(itemId) && ItemDB.Get(itemId) != null && Durability(itemId) <= 0;
        public void AddWear(string itemId, int n) { if (!string.IsNullOrEmpty(itemId) && Durability(itemId) > 0) AddTo(wear, itemId, Mathf.Min(n, Durability(itemId))); }
        public void Repair(string itemId, int amount = 99999) { TakeFrom(wear, itemId, amount); }
        public void Upgrade(string itemId) { AddTo(upgrades, itemId, 1); RecalcHP(false); }

        /// <summary>Consumables in the bag, in a stable order (the quick slot cycles through these).</summary>
        public List<string> QuickItems()
        {
            var l = new List<string>();
            foreach (var m in CraftDB.Mats) if (m.Consumable && InBag(m.id) > 0) l.Add(m.id);
            return l;
        }

        public string CycleQuick()
        {
            var l = QuickItems();
            if (l.Count == 0) { quick = ""; return quick; }
            int i = l.IndexOf(quick);
            quick = l[(i + 1) % l.Count];
            return quick;
        }

        public NpcMemory Memory(string npc)
        {
            foreach (var m in npcs) if (m.id == npc) return m;
            var n = new NpcMemory { id = npc };
            npcs.Add(n);
            return n;
        }

        /// <summary>Old saves: the potion count becomes medicine in the bag.</summary>
        public void Migrate()
        {
            if (migrated) return;
            migrated = true;
            if (potions > 0) { Give("medicina", potions); potions = 0; }
            if (bag.Count == 0 && stash.Count == 0) { Give("venda", 2); Give("tela", 2); Give("hierba", 2); }
        }

        /// <summary>Adds to the bag (one of each item). Returns false if it was already owned.</summary>
        public bool AddItem(string id)
        {
            if (ItemDB.Get(id) == null || Owns(id)) return false;
            inventory.Add(id);
            return true;
        }

        /// <summary>Equips an owned item in its slot; the previous one goes back to the bag.</summary>
        public bool Equip(string id)
        {
            var it = ItemDB.Get(id);
            if (it == null || !Owns(id) || !Class.CanUse(it)) return false;     // class weapon rules (KnightClass.CanUse)
            inventory.Remove(id);
            string old = it.slot == ItemSlot.Weapon ? weapon : it.slot == ItemSlot.Bow ? bow : armor;
            if (it.slot == ItemSlot.Weapon) weapon = id; else if (it.slot == ItemSlot.Bow) bow = id; else armor = id;
            if (!string.IsNullOrEmpty(old) && old != id && !inventory.Contains(old)) inventory.Add(old);
            RecalcHP(false);
            return true;
        }

        // ---------------------------------------------------------------- world clock (minutes of the day, 0..1440)
        public float clock = 8 * 60;
        public int day = 1;

        public const int MaxLevel = 30;
        public int XpToNext => 8 + (level - 1) * 6;

        // ---------------------------------------------------------------- derived stats
        public KnightClass Class => KnightClass.Get(classId);
        public int MaxHPFromStats => 4 + vit * 2 + heartsBought * 2 + ArmorItem.hp + CraftDB.UpgradeHP(Level(armor));
        public int SwordDamage
        {
            get
            {
                int d = 1 + str / 2 + swordBonus + Weapon.damage + CraftDB.UpgradeDamage(Level(weapon))
                        + (classId == "samurai" && Weapon.kind == WeaponKind.Katana ? 2 : 0);      // Samurai: bushido
                return Broken(weapon) ? Mathf.Max(1, d / 2) : d;      // a broken blade hits at half strength
            }
        }
        public int ArrowDamage => 1 + dex / 2 + (classId == "ranger" ? 1 : 0) + Bow.damage + CraftDB.UpgradeDamage(Level(bow)) + (ammo == "flecha_plata" ? 2 : 0);
        public float CritChance => Mathf.Min(0.6f, 0.03f * dex + Weapon.crit + ArmorItem.crit + (classId == "blade" ? 0.1f : 0f));
        public float BowCritChance => Mathf.Min(0.6f, 0.03f * dex + Bow.crit + ArmorItem.crit);
        public int Armor => def / 3 + (classId == "royal" ? 1 : 0) + (Broken(armor) ? 0 : ArmorItem.defense + CraftDB.UpgradeDefense(Level(armor)));                     // flat damage reduction (never below 1 dmg)
        public float DodgeChance => Mathf.Min(0.25f, 0.012f * agi);          // chance to avoid a hit completely
        public float SpeedMultiplier => Mathf.Max(0.6f, 1f + (agi - 3) * 0.04f + ArmorItem.speedMod);
        public float RollCooldown => Mathf.Max(0.3f, 0.6f - agi * 0.025f);
        /// <summary>Healing items heal more with Vitality (and +50% for the Paladin).</summary>
        public int HealPower(int baseHeal) => (baseHeal + vit / 3) * (classId == "paladin" ? 3 : 2) / 2;
        public int PotionHeal => HealPower(6);
        // ---------------------------------------------------------------- stamina (runtime, never saved)
        public float MaxStamina => 60 + vit * 3 + agi * 4;
        public float StaminaRegen => 32 + agi * 2.5f;
        /// <summary>Danger grows with what you kill: more spawns, tougher enemies, more elites (1..10).</summary>
        public int Threat => Mathf.Clamp(1 + kills / 12, 1, 10);

        public bool Has(string flag) => flags.Contains(flag);
        public bool Set(string flag)
        {
            if (flags.Contains(flag)) return false;
            flags.Add(flag);
            return true;
        }

        /// <summary>New character of the given class: base attributes, starting kit, full health.</summary>
        public static PlayerState NewCharacter(string classId, string name = "")
        {
            var k = KnightClass.Get(classId);
            var s = new PlayerState { classId = k.id, str = k.str, vit = k.vit, agi = k.agi, dex = k.dex, def = k.def };
            s.arrows = k.startArrows; s.potions = 0; s.migrated = true;
            s.Give("venda", k.startPotions + 1); s.Give("tela", 2); s.Give("hierba", 2); s.quick = "venda";
            s.weapon = k.startWeapon; s.bow = k.startBow; s.armor = k.startArmor;
            s.heroName = (name ?? "").Trim();
            s.RecalcHP(true);
            return s;
        }

        public void RecalcHP(bool fill)
        {
            int before = maxHP;
            maxHP = Mathf.Max(2, MaxHPFromStats);
            hp = fill ? maxHP : Mathf.Clamp(hp + Mathf.Max(0, maxHP - before), 0, maxHP);
        }

        public int Get(int attr) => attr switch { 0 => str, 1 => vit, 2 => agi, 3 => dex, _ => def };

        public bool Spend(int attr)
        {
            if (attrPoints <= 0) return false;
            attrPoints--;
            switch (attr)
            {
                case 0: str++; break;
                case 1: vit++; RecalcHP(false); break;
                case 2: agi++; break;
                case 3: dex++; break;
                default: def++; break;
            }
            return true;
        }

        public PlayerState Clone() => JsonUtility.FromJson<PlayerState>(JsonUtility.ToJson(this));
    }

    /// <summary>What one townsperson remembers about you (saved).</summary>
    [Serializable]
    public class NpcMemory
    {
        public string id;
        public int talks;              // conversations held
        public int lastDay = -1;       // day of the last conversation
        public int affinity;           // how much they like you (gifts, quests, kind answers)
        public int quest;              // 0 not offered, 1 accepted, 2 completed
        public int questBase;          // counter value when the quest was accepted (kill quests)
        public List<string> notes = new List<string>();    // things you told them / did for them
        public bool Knows(string note) => notes.Contains(note);
        public void Note(string note) { if (!notes.Contains(note)) notes.Add(note); }
    }

    /// <summary>Single save slot in PlayerPrefs (JSON).</summary>
    public static class SaveSystem
    {
        public static string Key = "woods_save_v2";   // tests switch this to their own slot
        public static bool HasSave => PlayerPrefs.HasKey(Key);

        public static void Save(PlayerState s)
        {
            PlayerPrefs.SetString(Key, JsonUtility.ToJson(s));
            PlayerPrefs.Save();
        }

        public static PlayerState Load()
        {
            if (!HasSave) return null;
            try { var s = JsonUtility.FromJson<PlayerState>(PlayerPrefs.GetString(Key)); s?.Migrate(); return s; }
            catch { return null; }
        }

        public static void Delete() { PlayerPrefs.DeleteKey(Key); PlayerPrefs.Save(); }
    }
}
