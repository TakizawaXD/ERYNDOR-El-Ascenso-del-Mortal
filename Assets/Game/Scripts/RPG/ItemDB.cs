using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    public enum ItemSlot { Weapon, Bow, Armor }
    // HeavyAxe and Staff were added after None so the numbers of the older kinds never change
    public enum WeaponKind { Sword, Greatsword, Katana, Rapier, Dagger, Spear, Axe, Hammer, Bow, Longbow, Crossbow, None, HeavyAxe, Staff }
    public enum Rarity { Common, Rare, Epic, Legendary }
    public enum Element { None, Fire, Frost, Venom, Holy }

    /// <summary>One weapon or armour. Icons are cells of Assets/Art/UI/Icons/ui_items_16x16.png (Tools/ArtGen2/items.py).</summary>
    public class ItemDef
    {
        public string id, name, desc;
        public ItemSlot slot;
        public WeaponKind kind = WeaponKind.None;
        public Rarity rarity;
        public Element element;
        public int icon, damage, defense, hp, price, pierce, multishot = 1, lifesteal;
        public float crit, speedMod;

        public WeaponStyle Style => WeaponStyle.Of(kind);
        public Color RarityColor => ItemDB.RarityColors[(int)rarity];
        public string RarityName => ItemDB.RarityNames[(int)rarity];
    }

    /// <summary>How each kind of weapon swings: reach, hit radius, timings, effect and heavy-attack multiplier.</summary>
    public struct WeaponStyle
    {
        public float reach, radius, windup, recover, knockback, heavyMul;
        public string fx;         // Assets/Art/Effects/Weapons/fx_<fx>_anim_32x32.png
        public string label;

        public static WeaponStyle Of(WeaponKind k)
        {
            switch (k)
            {
                case WeaponKind.Greatsword: return new WeaponStyle { reach = 0.95f, radius = 1.0f, windup = 0.34f, recover = 0.4f, knockback = 8f, heavyMul = 1.8f, fx = "greatsword", label = "Espadón" };
                case WeaponKind.Katana: return new WeaponStyle { reach = 0.85f, radius = 0.8f, windup = 0.13f, recover = 0.22f, knockback = 4f, heavyMul = 1.5f, fx = "katana", label = "Katana" };
                case WeaponKind.Rapier: return new WeaponStyle { reach = 1.05f, radius = 0.45f, windup = 0.11f, recover = 0.2f, knockback = 3f, heavyMul = 1.4f, fx = "thrust", label = "Estoque" };
                case WeaponKind.Dagger: return new WeaponStyle { reach = 0.55f, radius = 0.55f, windup = 0.08f, recover = 0.17f, knockback = 2.5f, heavyMul = 1.4f, fx = "dagger", label = "Daga" };
                case WeaponKind.Spear: return new WeaponStyle { reach = 1.35f, radius = 0.5f, windup = 0.2f, recover = 0.3f, knockback = 6f, heavyMul = 1.6f, fx = "thrust", label = "Lanza" };
                case WeaponKind.Axe: return new WeaponStyle { reach = 0.8f, radius = 0.9f, windup = 0.28f, recover = 0.34f, knockback = 7f, heavyMul = 1.7f, fx = "axe", label = "Hacha" };
                case WeaponKind.Hammer: return new WeaponStyle { reach = 0.8f, radius = 1.1f, windup = 0.38f, recover = 0.42f, knockback = 11f, heavyMul = 2f, fx = "impact", label = "Martillo" };
                case WeaponKind.HeavyAxe: return new WeaponStyle { reach = 0.95f, radius = 1.15f, windup = 0.42f, recover = 0.45f, knockback = 10f, heavyMul = 2.1f, fx = "axe", label = "Hacha pesada" };
                case WeaponKind.Staff: return new WeaponStyle { reach = 0.85f, radius = 0.7f, windup = 0.22f, recover = 0.3f, knockback = 4f, heavyMul = 1.6f, fx = "magic", label = "Bastón" };
                case WeaponKind.Longbow: return new WeaponStyle { windup = 0.6f, recover = 0.2f, knockback = 5f, label = "Arco largo" };
                case WeaponKind.Crossbow: return new WeaponStyle { windup = 0.7f, recover = 0.25f, knockback = 6f, label = "Ballesta" };
                case WeaponKind.Bow: return new WeaponStyle { windup = 0.42f, recover = 0.2f, knockback = 4f, label = "Arco" };
                default: return new WeaponStyle { reach = 0.75f, radius = 0.75f, windup = 0.2f, recover = 0.3f, knockback = 5f, heavyMul = 1.6f, fx = "sword", label = "Espada" };
            }
        }

        public float ArrowSpeed => label == "Ballesta" ? 16f : label == "Arco largo" ? 14f : 11f;
    }

    public static class ItemDB
    {
        public static readonly string[] RarityNames = { "Común", "Raro", "Épico", "Legendario" };
        public static readonly Color[] RarityColors =
        {
            new Color32(0xd8, 0xd2, 0xc8, 0xff), new Color32(0x5c, 0xb8, 0xff, 0xff), new Color32(0xc3, 0x7a, 0xff, 0xff), new Color32(0xff, 0xb8, 0x3a, 0xff)
        };
        public static readonly string[] ElementNames = { "", "Fuego", "Escarcha", "Veneno", "Sagrado" };

        static ItemDef W(string id, string name, WeaponKind k, Rarity r, int icon, int dmg, int price, float crit = 0, Element e = Element.None, string desc = "") =>
            new ItemDef { id = id, name = name, slot = k >= WeaponKind.Bow && k <= WeaponKind.Crossbow ? ItemSlot.Bow : ItemSlot.Weapon, kind = k, rarity = r, icon = icon, damage = dmg, price = price, crit = crit, element = e, desc = desc };

        static ItemDef A(string id, string name, Rarity r, int icon, int def, int hp, float speed, int price, float crit = 0, string desc = "") =>
            new ItemDef { id = id, name = name, slot = ItemSlot.Armor, rarity = r, icon = icon, defense = def, hp = hp, speedMod = speed, price = price, crit = crit, desc = desc };

        public static readonly ItemDef[] All =
        {
            W("sword_short", "Espada corta", WeaponKind.Sword, Rarity.Common, 0, 0, 15, desc: "Ligera y fiable."),
            W("sword_long", "Espada larga", WeaponKind.Sword, Rarity.Common, 1, 1, 40, desc: "La espada del soldado."),
            W("sword_knight", "Espada del caballero", WeaponKind.Sword, Rarity.Rare, 2, 2, 90, 0.05f, desc: "Forjada en la Ciudadela."),
            W("greatsword", "Espadón", WeaponKind.Greatsword, Rarity.Rare, 3, 4, 120, desc: "Lento, amplio y demoledor."),
            W("katana", "Katana", WeaponKind.Katana, Rarity.Rare, 4, 2, 130, 0.10f, desc: "Cortes rapidísimos."),
            W("katana_moon", "Katana lunar", WeaponKind.Katana, Rarity.Epic, 5, 4, 280, 0.15f, Element.Frost, "Su filo hiela y ralentiza."),
            W("rapier", "Estoque", WeaponKind.Rapier, Rarity.Rare, 6, 1, 110, 0.22f, desc: "Estocadas largas, muchos críticos."),
            W("dagger", "Daga", WeaponKind.Dagger, Rarity.Common, 7, 0, 25, 0.12f, desc: "Corta distancia, gran velocidad."),
            W("dagger_venom", "Daga venenosa", WeaponKind.Dagger, Rarity.Epic, 8, 2, 240, 0.15f, Element.Venom, "Envenena a cada corte."),
            W("spear", "Lanza", WeaponKind.Spear, Rarity.Common, 9, 1, 45, desc: "Mantén a raya a tus enemigos."),
            W("halberd", "Alabarda", WeaponKind.Spear, Rarity.Rare, 10, 3, 130, desc: "Alcance enorme y golpe pesado."),
            W("trident", "Tridente del mar", WeaponKind.Spear, Rarity.Epic, 11, 4, 260, 0.05f, Element.Frost, "Reliquia de la Costa del Puerto."),
            W("axe", "Hacha de guerra", WeaponKind.Axe, Rarity.Common, 12, 2, 50, desc: "Tajos anchos y contundentes."),
            W("axe_frost", "Hacha de escarcha", WeaponKind.Axe, Rarity.Epic, 13, 5, 300, desc: "Hielo de los Picos Nevados.", e: Element.Frost),
            W("hammer", "Martillo de guerra", WeaponKind.Hammer, Rarity.Rare, 14, 4, 140, desc: "Aturde y derriba."),
            W("mace_holy", "Maza sagrada", WeaponKind.Hammer, Rarity.Epic, 15, 4, 290, desc: "Daño x1,5 contra demonios.", e: Element.Holy),
            W("blade_ash", "Hoja de ceniza", WeaponKind.Sword, Rarity.Legendary, 16, 6, 600, 0.10f, Element.Fire, "Arde con el fuego del Monte Ceniza."),
            W("sword_rune", "Espada rúnica", WeaponKind.Katana, Rarity.Legendary, 17, 7, 700, 0.15f, desc: "Cada golpe te devuelve vida."),
            W("heavyaxe", "Hacha de verdugo", WeaponKind.HeavyAxe, Rarity.Rare, 33, 5, 160, desc: "A dos manos: tajos lentos que derriban."),
            W("staff_oak", "Bastón de roble", WeaponKind.Staff, Rarity.Common, 34, 1, 50, desc: "Golpea y lanza saetas mágicas (3.er golpe y K)."),
            W("staff_frost", "Bastón de escarcha", WeaponKind.Staff, Rarity.Epic, 35, 3, 300, 0.05f, Element.Frost, "Sus saetas hielan y ralentizan."),
            W("bow_short", "Arco corto", WeaponKind.Bow, Rarity.Common, 18, 0, 15, desc: "Disparo rápido."),
            W("bow_long", "Arco largo", WeaponKind.Longbow, Rarity.Common, 19, 1, 45, desc: "Flechas más rápidas y potentes."),
            W("crossbow", "Ballesta", WeaponKind.Crossbow, Rarity.Rare, 20, 3, 130, desc: "Los virotes atraviesan a un enemigo."),
            W("bow_elf", "Arco élfico", WeaponKind.Bow, Rarity.Epic, 21, 2, 280, 0.08f, desc: "Dispara tres flechas en abanico."),
            W("bow_bone", "Arco de hueso", WeaponKind.Longbow, Rarity.Rare, 22, 2, 120, 0.15f, desc: "Hecho con huesos de dragón joven."),
            W("bow_dragon", "Arco del dragón", WeaponKind.Longbow, Rarity.Legendary, 23, 4, 650, 0.10f, Element.Fire, "Dos flechas ígneas por disparo."),
            A("armor_cloth", "Ropa de viaje", Rarity.Common, 24, 0, 0, 0.05f, 10, desc: "Cómoda, no protege mucho."),
            A("armor_leather", "Armadura de cuero", Rarity.Common, 25, 1, 0, 0.02f, 40, desc: "Ligera y flexible."),
            A("armor_chain", "Cota de malla", Rarity.Rare, 26, 2, 2, -0.03f, 100, desc: "Buena defensa sin pesar demasiado."),
            A("armor_plate", "Armadura de placas", Rarity.Rare, 27, 3, 4, -0.08f, 170, desc: "Muy resistente, algo lenta."),
            A("armor_paladin", "Armadura sagrada", Rarity.Epic, 28, 4, 6, -0.05f, 320, desc: "Bendecida en la Capilla."),
            A("armor_shadow", "Armadura sombría", Rarity.Epic, 29, 2, 2, 0.06f, 300, 0.10f, "Para quien ataca desde las sombras."),
            A("armor_ranger", "Capa de montaraz", Rarity.Rare, 30, 1, 2, 0.08f, 120, 0.05f, "Ligera: más velocidad y críticos."),
            A("armor_dragon", "Armadura dracónica", Rarity.Legendary, 31, 5, 8, -0.02f, 750, 0.05f, "Escamas de dragón: casi impenetrable."),
            A("armor_frost", "Coraza de escarcha", Rarity.Epic, 32, 4, 4, -0.04f, 280, desc: "Hielo eterno de los Picos."),
        };

        static Dictionary<string, ItemDef> _byId;

        static ItemDB()
        {
            Get("bow_elf").multishot = 3; Get("bow_dragon").multishot = 2;
            Get("crossbow").pierce = 1; Get("sword_rune").lifesteal = 1;
        }

        public static ItemDef Get(string id)
        {
            if (_byId == null) { _byId = new Dictionary<string, ItemDef>(); foreach (var i in All) _byId[i.id] = i; }
            return id != null && _byId.TryGetValue(id, out var d) ? d : null;
        }

        /// <summary>Random loot of the given rarity range (used by chests, elites, champions and bosses).</summary>
        public static ItemDef Roll(Rarity min, Rarity max)
        {
            var pool = new List<ItemDef>();
            foreach (var i in All) if (i.rarity >= min && i.rarity <= max) pool.Add(i);
            return pool.Count == 0 ? null : pool[Random.Range(0, pool.Count)];
        }

        /// <summary>Weighted rarity: higher threat makes better loot more likely.</summary>
        public static Rarity RollRarity(int threat, Rarity floor = Rarity.Common)
        {
            float r = Random.value;
            float leg = 0.01f + threat * 0.006f, epic = 0.07f + threat * 0.015f, rare = 0.3f + threat * 0.02f;
            var res = r < leg ? Rarity.Legendary : r < leg + epic ? Rarity.Epic : r < leg + epic + rare ? Rarity.Rare : Rarity.Common;
            return res < floor ? floor : res;
        }

        public static readonly string[] SmithStock =
            { "sword_long", "sword_knight", "greatsword", "katana", "rapier", "spear", "halberd", "axe", "heavyaxe", "hammer", "staff_oak", "bow_long", "crossbow", "bow_bone", "armor_leather", "armor_chain", "armor_plate", "armor_ranger" };
    }
}
