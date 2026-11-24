using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace WoodsGame
{
    public enum MatKind { Herb, Animal, Monster, Mineral, Supply, Healing, Attack, Tool }
    public enum RecipeCat { Healing, Attack, Forge }

    /// <summary>A stack of a material or consumable (saved in the bag / camp storage).</summary>
    [Serializable]
    public class ItemStack
    {
        public string id;
        public int n;
        public ItemStack() { }
        public ItemStack(string id, int n) { this.id = id; this.n = n; }
    }

    /// <summary>Materials and consumables. Icons are cells of Assets/Art/UI/Icons/ui_materials_16x16.png (Tools/ArtGen2/camp.py).</summary>
    public class MatDef
    {
        public string id, name, desc, source;
        public MatKind kind;
        public int icon, price;
        public bool Consumable => kind == MatKind.Healing || kind == MatKind.Attack || kind == MatKind.Tool;
        /// <summary>How many you can carry; the rest goes to the camp storage.</summary>
        public int BagCap => Consumable ? (kind == MatKind.Attack && id.StartsWith("flecha") ? 30 : 6) : 30;
    }

    public class Recipe
    {
        public string id, result, name;
        public int count = 1;
        public RecipeCat cat;
        public (string id, int n)[] needs;
        public string text;
    }

    /// <summary>Everything about crafting: materials, consumables, recipes, forge upgrades (+1..+5) and wear.</summary>
    public static class CraftDB
    {
        static MatDef M(string id, string name, MatKind k, int icon, int price, string desc, string source = "") =>
            new MatDef { id = id, name = name, kind = k, icon = icon, price = price, desc = desc, source = source };

        public static readonly MatDef[] Mats =
        {
            M("hierba", "Hierba curativa", MatKind.Herb, 0, 2, "Hoja fresca que cierra heridas.", "Prados del Valle, Bosque del Oeste y Lago Espejo"),
            M("flor_luna", "Flor de luna", MatKind.Herb, 1, 8, "Solo se abre de noche. Medicina fuerte.", "Bosques y lago, de noche"),
            M("raiz", "Raíz amarga", MatKind.Herb, 2, 4, "Amarga como el pantano. Base de medicinas.", "Pantano Carmesí y Valle"),
            M("seta_roja", "Seta roja", MatKind.Herb, 3, 3, "Venenosa. Útil para bombas.", "Bosque del Oeste y Bosque Corrupto"),
            M("seta_azul", "Seta azul", MatKind.Herb, 4, 5, "Brilla en la oscuridad. Devuelve el aliento.", "Lago Espejo y Pantano"),
            M("carne", "Carne cruda", MatKind.Animal, 5, 3, "Para un buen guiso.", "Orcos"),
            M("cuero", "Cuero", MatKind.Animal, 6, 5, "Curtido a medias. Sirve para la forja.", "Orcos"),
            M("colmillo", "Colmillo de orco", MatKind.Monster, 7, 6, "Duro como el acero.", "Orcos"),
            M("limo", "Limo tóxico", MatKind.Monster, 8, 5, "Pegajoso y venenoso.", "Limos tóxicos y monstruos de sangre"),
            M("sangre", "Sangre carmesí", MatKind.Monster, 9, 6, "Aún late.", "Monstruos de sangre"),
            M("ceniza", "Ceniza demoníaca", MatKind.Monster, 10, 7, "Arde sin llama.", "Demonios y espectros"),
            M("hierro", "Mineral de hierro", MatKind.Mineral, 11, 6, "La base de toda forja.", "Rocas de Picos, Arenas y colinas"),
            M("plata", "Mineral de plata", MatKind.Mineral, 12, 14, "Castiga a los no muertos.", "Picos Nevados y caballeros caídos"),
            M("obsidiana", "Obsidiana", MatKind.Mineral, 13, 25, "Vidrio de volcán, filo perfecto.", "Monte Ceniza"),
            M("nucleo", "Núcleo ígneo", MatKind.Monster, 14, 30, "El corazón de un engendro de magma.", "Engendros de magma"),
            M("tela", "Tela de lino", MatKind.Supply, 15, 4, "Para vendas y mechas.", "Tiendas"),
            M("aceite", "Aceite", MatKind.Supply, 16, 5, "Base de ungüentos y aceites de arma.", "Tiendas"),
            M("frasco", "Frasco vacío", MatKind.Supply, 17, 3, "Para medicinas y tónicos.", "Tiendas"),
            M("cristal", "Cristal de escarcha", MatKind.Mineral, 18, 12, "Frío eterno.", "Picos Nevados y orcos de hielo"),
            M("madera", "Madera seca", MatKind.Supply, 19, 2, "Para flechas y mangos.", "Tiendas y cajas rotas"),

            M("venda", "Venda", MatKind.Healing, 20, 10, "Cura 5 de vida."),
            M("unguento", "Ungüento", MatKind.Healing, 21, 18, "Cura 8 y 4 más poco a poco."),
            M("medicina", "Medicina", MatKind.Healing, 22, 35, "Cura 16 de vida."),
            M("tonico", "Tónico de aguante", MatKind.Healing, 23, 20, "Aguante lleno y recuperación x2 durante 60 s."),
            M("guiso", "Guiso del cazador", MatKind.Healing, 24, 15, "Cura 6 y +25 de aguante máximo durante 3 min."),
            M("bomba", "Bomba", MatKind.Attack, 25, 20, "Explota: 8 de daño en área."),
            M("bomba_veneno", "Bomba de veneno", MatKind.Attack, 26, 22, "Nube venenosa: daño y veneno en área."),
            M("aceite_fuego", "Aceite ígneo", MatKind.Attack, 27, 25, "Tu arma quema durante 30 golpes."),
            M("aceite_hielo", "Aceite gélido", MatKind.Attack, 28, 25, "Tu arma hiela durante 30 golpes."),
            M("aceite_sagrado", "Aceite bendito", MatKind.Attack, 29, 30, "Tu arma castiga demonios durante 30 golpes."),
            M("flecha_fuego", "Flechas ígneas", MatKind.Attack, 30, 4, "Queman al impactar. Úsalas para cargarlas."),
            M("flecha_veneno", "Flechas venenosas", MatKind.Attack, 31, 4, "Envenenan. Úsalas para cargarlas."),
            M("flecha_plata", "Flechas de plata", MatKind.Attack, 32, 6, "+2 daño y perforan. Úsalas para cargarlas."),
            M("elixir", "Elixir del sabio", MatKind.Healing, 33, 80, "Vida y aguante completos."),
            M("kit_reparar", "Kit de reparación", MatKind.Tool, 34, 30, "Repara el arma equipada a la mitad."),
        };

        static R Rc(string result, int count, RecipeCat cat, params (string, int)[] needs) => new R(result, count, cat, needs);
        public class R { public string result; public int count; public RecipeCat cat; public (string, int)[] needs; public R(string r, int c, RecipeCat k, (string, int)[] n) { result = r; count = c; cat = k; needs = n; } }

        public static readonly Recipe[] Recipes = new[]
        {
            Rc("venda", 1, RecipeCat.Healing, ("tela", 1), ("hierba", 1)),
            Rc("unguento", 1, RecipeCat.Healing, ("hierba", 2), ("aceite", 1)),
            Rc("medicina", 1, RecipeCat.Healing, ("flor_luna", 1), ("raiz", 1), ("frasco", 1)),
            Rc("tonico", 1, RecipeCat.Healing, ("seta_azul", 2), ("frasco", 1)),
            Rc("guiso", 1, RecipeCat.Healing, ("carne", 1), ("hierba", 1), ("seta_azul", 1)),
            Rc("elixir", 1, RecipeCat.Healing, ("flor_luna", 2), ("sangre", 1), ("cristal", 1), ("frasco", 1)),
            Rc("bomba", 1, RecipeCat.Attack, ("ceniza", 1), ("aceite", 1), ("tela", 1)),
            Rc("bomba_veneno", 1, RecipeCat.Attack, ("limo", 2), ("seta_roja", 1), ("frasco", 1)),
            Rc("aceite_fuego", 1, RecipeCat.Attack, ("aceite", 1), ("ceniza", 1)),
            Rc("aceite_hielo", 1, RecipeCat.Attack, ("aceite", 1), ("cristal", 1)),
            Rc("aceite_sagrado", 1, RecipeCat.Attack, ("aceite", 1), ("plata", 1), ("flor_luna", 1)),
            Rc("flecha_fuego", 5, RecipeCat.Attack, ("madera", 1), ("ceniza", 1), ("aceite", 1)),
            Rc("flecha_veneno", 5, RecipeCat.Attack, ("madera", 1), ("limo", 1)),
            Rc("flecha_plata", 5, RecipeCat.Attack, ("madera", 1), ("plata", 1)),
            Rc("kit_reparar", 1, RecipeCat.Attack, ("hierro", 2), ("cuero", 1), ("madera", 1)),
        }.Select(r => new Recipe
        {
            id = "r_" + r.result, result = r.result, count = r.count, cat = r.cat, needs = r.needs,
            name = Get(r.result)?.name ?? r.result,
        }).ToArray();

        static Dictionary<string, MatDef> _byId;

        public static MatDef Get(string id)
        {
            if (_byId == null) { _byId = new Dictionary<string, MatDef>(); foreach (var m in Mats) _byId[m.id] = m; }
            return id != null && _byId.TryGetValue(id, out var d) ? d : null;
        }

        public static Recipe RecipeFor(string result) => Recipes.FirstOrDefault(r => r.result == result);

        // ================================================================ forge: upgrade levels +1..+5
        public const int MaxUpgrade = 5;

        /// <summary>Materials and coins to raise an item from level <paramref name="from"/> to from+1.</summary>
        public static (string id, int n)[] UpgradeCost(int from, out int coins)
        {
            switch (from)
            {
                case 0: coins = 20; return new[] { ("hierro", 2), ("cuero", 1) };
                case 1: coins = 40; return new[] { ("hierro", 3), ("colmillo", 2) };
                case 2: coins = 80; return new[] { ("plata", 2), ("hierro", 2) };
                case 3: coins = 140; return new[] { ("plata", 3), ("cristal", 2) };
                default: coins = 220; return new[] { ("obsidiana", 2), ("nucleo", 1), ("plata", 2) };
            }
        }

        /// <summary>Weapons and bows: +1 damage per level. Armour: +1 defense at +1/+3/+5 and +2 life per level.</summary>
        public static int UpgradeDamage(int lvl) => lvl;
        public static int UpgradeDefense(int lvl) => (lvl + 1) / 2;
        public static int UpgradeHP(int lvl) => lvl * 2;

        // ================================================================ wear (durability)
        public static int MaxDurability(ItemDef it) => it == null ? 100 : 80 + (int)it.rarity * 35;

        public static int RepairCost(ItemDef it, int wear) => wear <= 0 ? 0 : Mathf.CeilToInt(wear * (it.price + 40) / 300f) + 2;

        /// <summary>What sells for how much (equipment: a third of the price; materials: their value).</summary>
        public static int SellPrice(ItemDef it) => Mathf.Max(1, it.price / 3);
        public static int SellPrice(MatDef m) => Mathf.Max(1, m.price / 2);

        /// <summary>Material drops by enemy type (id, chance).</summary>
        public static (string id, float chance)[] Drops(string typeId, EnemyKind kind)
        {
            switch (typeId)
            {
                case "OrcFrost": return new[] { ("cristal", 0.4f), ("carne", 0.4f), ("cuero", 0.3f) };
                case "OrcDesert": return new[] { ("cuero", 0.45f), ("hierro", 0.3f), ("colmillo", 0.3f) };
                case "OrcCorsair": return new[] { ("carne", 0.4f), ("tela", 0.4f), ("aceite", 0.3f) };
                case "OrcBerserker": return new[] { ("colmillo", 0.55f), ("cuero", 0.4f), ("carne", 0.4f) };
                case "BloodToxic": return new[] { ("limo", 0.7f), ("seta_azul", 0.2f) };
                case "BloodMagma": return new[] { ("nucleo", 0.35f), ("ceniza", 0.4f), ("obsidiana", 0.15f) };
                case "DemonAsh": return new[] { ("ceniza", 0.6f), ("obsidiana", 0.25f) };
                case "DemonWraith": return new[] { ("ceniza", 0.5f), ("flor_luna", 0.2f) };
                case "KnightFallen": return new[] { ("plata", 0.5f), ("hierro", 0.5f), ("tela", 0.3f) };
            }
            switch (kind)
            {
                case EnemyKind.Orc: return new[] { ("carne", 0.5f), ("cuero", 0.4f), ("colmillo", 0.25f) };
                case EnemyKind.BloodMonster: return new[] { ("sangre", 0.55f), ("limo", 0.3f) };
                default: return new[] { ("ceniza", 0.55f), ("sangre", 0.15f) };
            }
        }

        /// <summary>Gathering spots placed by the builder (same order as Tools/ArtGen2/camp.py GATHER).</summary>
        public static readonly string[] GatherKinds = { "hierba", "flor_luna", "raiz", "seta_roja", "seta_azul", "hierro", "plata", "obsidiana", "cristal" };

        public static string Describe(MatDef m)
        {
            if (m == null) return "";
            var r = RecipeFor(m.id);
            return m.desc + (string.IsNullOrEmpty(m.source) ? "" : "\nSe encuentra en: " + m.source);
        }
    }
}
