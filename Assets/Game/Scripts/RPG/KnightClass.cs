using System.Collections.Generic;

namespace WoodsGame
{
    /// <summary>The ten playable classes (2026-11-21): the Soldier, the Samurai (a lacquered recolour with all the weapon
    /// sets) and eight hand-drawn heroes (Assets/Art/Characters/&lt;sprite&gt;), each
    /// with its own base attributes, starting kit and one passive perk.</summary>
    public class KnightClass
    {
        public string id, name, shortName, sprite, perk, description;
        public int str, vit, agi, dex, def;
        public int startArrows = 10, startPotions = 1, pointsPerLevel = 3;
        public string startWeapon = "sword_long", startBow = "bow_short", startArmor = "armor_chain";

        public const string Default = "knight";

        public static readonly KnightClass[] All =
        {
            K("knight", "CABALLERO", "CABALLERO", "Soldier", false, 3, 4, 3, 3, 3, "sword_long", "armor_chain",
              "VERSÁTIL: +4 PUNTOS POR NIVEL", "SOLDADO DEL REY. EQUILIBRADO EN TODO.", ppl: 4),
            K("royal", "CABALLERO REAL", "C. REAL", "HeroKnight", false, 4, 4, 2, 2, 5, "sword_knight", "armor_plate",
              "BALUARTE: RECIBE 1 DAÑO MENOS", "ESPADA Y ESCUDO DE LA GUARDIA REAL."),
            K("crusader", "CRUZADO", "CRUZADO", "HeroCrusader", false, 3, 5, 2, 3, 4, "spear", "armor_paladin",
              "SAGRADO: SUS GOLPES CASTIGAN A LOS DEMONIOS", "LANZA BENDITA Y FE INQUEBRANTABLE."),
            K("dark", "GUERRERO DEL HACHA", "HACHERO", "HeroAxeKnight", false, 6, 4, 2, 2, 3, "axe", "armor_leather",
              "SED DE SANGRE: CADA ENEMIGO TE CURA", "GOLPES BRUTALES. VIVE AL LÍMITE."),
            K("merc", "MERCENARIO", "MERCENARIO", "HeroSoldier", false, 4, 3, 4, 3, 2, "sword_short", "armor_leather",
              "CODICIA: +50% DE MONEDAS", "LUCHA POR ORO Y NUNCA PIERDE UNA MONEDA."),
            K("mage", "MAGO", "MAGO", "HeroWizard", false, 2, 3, 3, 6, 2, "staff_oak", "armor_cloth",
              "ARCANO: SAETAS MÁGICAS +1 DAÑO", "BASTÓN Y SAETAS DE ENERGÍA ARCANA."),
            K("blade", "ESPADACHINA", "ESPADACHINA", "HeroSwordswoman", true, 3, 3, 6, 4, 2, "rapier", "armor_leather",
              "FILO CERTERO: +10% DE CRÍTICO", "VELOZ Y PRECISA CON EL ESTOQUE."),
            K("paladin", "SACERDOTISA", "SACERDOTISA", "HeroPriestess", true, 2, 6, 3, 3, 4, "mace_holy", "armor_paladin",
              "FE: POCIONES +50% Y REGENERA VIDA", "SANADORA DE AURELITH. RESISTE LO QUE SEA.", potions: 3),
            K("ranger", "ARQUERA", "ARQUERA", "HeroRanger", true, 2, 3, 5, 6, 2, "dagger", "armor_ranger",
              "OJO DE HALCÓN: FLECHAS PERFORANTES", "RÁPIDA Y CERTERA CON EL ARCO.", arrows: 30, bow: "bow_long"),
            K("samurai", "SAMURÁI", "SAMURÁI", "KnightSamurai", false, 5, 3, 5, 3, 2, "katana", "armor_leather",
              "BUSHIDO: +2 DAÑO CON KATANA", "GUERRERO DE ORIENTE. LA KATANA ES SU ALMA."),
        };

        /// <summary>The look of the character is drawn by hand (Hero* art) with its own weapon in the sprite: no extra
        /// held-weapon sprite is drawn over it.</summary>
        public bool OwnWeaponArt => sprite.StartsWith("Hero");
        public bool female;

        // ---- weapon rules (2026-11-21): magic belongs to the Mago, bows to the Arquera
        /// <summary>The Arquera is the only class that shoots (L).</summary>
        public bool UsesBow => id == "ranger";
        /// <summary>The Mago casts a magic bolt with L instead of shooting.</summary>
        public bool UsesMagic => id == "mage";

        /// <summary>Can this class equip the item? Mago: only staffs. Arquera: bows and daggers (her knife).
        /// Everyone else: any melee weapon but staffs, and no bows. Armour fits everybody.</summary>
        public bool CanUse(ItemDef it)
        {
            if (it == null) return false;
            if (it.slot == ItemSlot.Bow) return UsesBow;
            if (it.slot != ItemSlot.Weapon) return true;
            if (UsesMagic) return it.kind == WeaponKind.Staff;
            if (UsesBow) return it.kind == WeaponKind.Dagger;
            return it.kind != WeaponKind.Staff;
        }

        /// <summary>Why an item cannot be equipped (shown in the bag).</summary>
        public string WhyNot(ItemDef it)
        {
            if (it.slot == ItemSlot.Bow) return "SOLO LA ARQUERA USA ARCOS";
            if (it.kind == WeaponKind.Staff) return "SOLO EL MAGO USA BASTONES DE MAGIA";
            if (UsesMagic) return "EL MAGO SOLO USA BASTONES DE MAGIA";
            if (UsesBow) return "LA ARQUERA SOLO LLEVA DAGAS Y ARCOS";
            return "TU CLASE NO PUEDE USARLO";
        }
        public string GenderName => female ? "MUJER" : "HOMBRE";

        static KnightClass K(string id, string name, string shortName, string sprite, bool female, int str, int vit, int agi, int dex, int def,
                             string weapon, string armor, string perk, string desc, int ppl = 3, int potions = 1, int arrows = 10, string bow = "bow_short")
            => new KnightClass { id = id, name = name, shortName = shortName, sprite = sprite, female = female, str = str, vit = vit, agi = agi,
                                 dex = dex, def = def, startWeapon = weapon, startArmor = armor, perk = perk, description = desc,
                                 pointsPerLevel = ppl, startPotions = potions, startArrows = arrows, startBow = bow };

        static Dictionary<string, KnightClass> _byId;

        public static KnightClass Get(string id)
        {
            if (_byId == null) { _byId = new Dictionary<string, KnightClass>(); foreach (var k in All) _byId[k.id] = k; }
            return id != null && _byId.TryGetValue(id, out var c) ? c : All[0];
        }

        public static int IndexOf(string id)
        {
            for (int i = 0; i < All.Length; i++) if (All[i].id == id) return i;
            return 0;
        }

        public static readonly string[] AttrNames = { "FUERZA", "VITALIDAD", "AGILIDAD", "DESTREZA", "DEFENSA" };
        public static readonly string[] AttrShort = { "FUE", "VIT", "AGI", "DES", "DEF" };
        public static readonly string[] AttrHelp =
        {
            "DAÑO DE LA ESPADA", "VIDA MÁXIMA Y POCIONES", "VELOCIDAD Y ESQUIVA", "DAÑO DEL ARCO Y CRÍTICOS", "REDUCE EL DAÑO RECIBIDO"
        };
    }
}
