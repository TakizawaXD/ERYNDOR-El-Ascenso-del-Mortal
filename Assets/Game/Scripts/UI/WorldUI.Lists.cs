using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;

namespace WoodsGame
{
    /// <summary>List-based panels: crafting at camps, camp storage, and trading (shops + the smith's buy / sell / upgrade / repair).
    /// All share one layout: tabs on top, a scrolling list of rows on the left and the details of the selected row on the right.</summary>
    public partial class WorldUI
    {
        public enum TradeMode { Buy, Sell, Upgrade, Repair }

        // ================================================================ shared row list + details view
        public class Row
        {
            public Sprite icon; public string name, right; public Color color = Color.white, rightColor = new Color32(0xff, 0xc8, 0x5a, 0xff);
            public Sprite bigIcon; public string title, sub, body, desc; public Color titleColor = Color.white;
            public Action act; public string hint;
        }

        class ListView
        {
            public readonly List<Image> bg = new List<Image>(), icon = new List<Image>();
            public readonly List<Text> name = new List<Text>(), right = new List<Text>();
            public int rows, scroll;
            public RectTransform root;

            public ListView(Transform parent, Vector2 pos, int rows, float width)
            {
                this.rows = rows;
                root = UIRoot.Rect(parent, "List", new Vector2(0, 1), new Vector2(0, 1), pos, new Vector2(width, rows * 15));
                for (int r = 0; r < rows; r++)
                {
                    var row = UIRoot.Rect(root, "Row", new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, -r * 15), new Vector2(width, 14));
                    var b = row.gameObject.AddComponent<Image>(); b.color = Color.clear; bg.Add(b);
                    var ic = UIRoot.Img(row, null, false);
                    var irt = ic.rectTransform; irt.anchorMin = irt.anchorMax = new Vector2(0, 0.5f); irt.pivot = new Vector2(0, 0.5f);
                    irt.anchoredPosition = new Vector2(1, 0); irt.sizeDelta = new Vector2(16, 16); icon.Add(ic);
                    name.Add(UIRoot.Label(row, "", new Vector2(0, 1), new Vector2(20, -1), TextAnchor.UpperLeft, UIRoot.Cream));
                    right.Add(UIRoot.Label(row, "", new Vector2(1, 1), new Vector2(-3, -1), TextAnchor.UpperRight, new Color32(0xff, 0xc8, 0x5a, 0xff)));
                }
            }

            public void Show(List<Row> list, int sel, bool focused)
            {
                if (sel < scroll) scroll = sel;
                if (sel >= scroll + rows) scroll = sel - rows + 1;
                scroll = Mathf.Clamp(scroll, 0, Mathf.Max(0, list.Count - rows));
                for (int r = 0; r < rows; r++)
                {
                    int i = scroll + r;
                    var it = i < list.Count ? list[i] : null;
                    bool s = i == sel && it != null;
                    bg[r].color = s ? new Color(1f, 0.78f, 0.35f, focused ? 0.2f : 0.08f) : Color.clear;
                    icon[r].sprite = it?.icon; icon[r].color = it?.icon != null ? Color.white : Color.clear;
                    name[r].text = it != null ? it.name : ""; name[r].color = it == null ? Color.clear : s && focused ? Color.white : it.color;
                    right[r].text = it != null ? it.right ?? "" : ""; right[r].color = it != null ? it.rightColor : Color.clear;
                }
            }
        }

        class DetailView
        {
            public Image icon; public Text title, sub, body, desc;
            public DetailView(Transform parent, Vector2 pos, float w)
            {
                var det = UIRoot.Rect(parent, "Details", new Vector2(0, 1), new Vector2(0, 1), pos, new Vector2(w, 140));
                var frame = UIRoot.Rect(det, "IconFrame", new Vector2(0, 1), new Vector2(0, 1), Vector2.zero, new Vector2(38, 38));
                var fi = frame.gameObject.AddComponent<Image>(); fi.sprite = GameAssets.I ? GameAssets.I.flatSlot : null; fi.type = Image.Type.Sliced;
                if (fi.sprite == null) fi.color = new Color(1, 1, 1, 0.12f);
                icon = UIRoot.Img(frame, null, false); icon.rectTransform.sizeDelta = new Vector2(32, 32);
                title = UIRoot.Label(det, "", new Vector2(0, 1), new Vector2(42, -4), TextAnchor.UpperLeft, UIRoot.Cream);
                sub = UIRoot.Label(det, "", new Vector2(0, 1), new Vector2(42, -15), TextAnchor.UpperLeft, Soft);
                body = UIRoot.Label(det, "", new Vector2(0, 1), new Vector2(0, -44), TextAnchor.UpperLeft, UIRoot.Cream);
                body.rectTransform.sizeDelta = new Vector2(w, 60); body.horizontalOverflow = HorizontalWrapMode.Wrap;
                desc = UIRoot.Label(det, "", new Vector2(0, 1), new Vector2(0, -104), TextAnchor.UpperLeft, Soft);
                desc.rectTransform.sizeDelta = new Vector2(w, 30); desc.horizontalOverflow = HorizontalWrapMode.Wrap;
            }

            public void Show(Row r)
            {
                if (r == null) { icon.color = Color.clear; title.text = sub.text = body.text = desc.text = ""; return; }
                icon.sprite = r.bigIcon ?? r.icon; icon.color = icon.sprite ? Color.white : Color.clear;
                title.text = r.title ?? r.name; title.color = r.titleColor;
                sub.text = r.sub ?? ""; body.text = r.body ?? ""; desc.text = r.desc ?? "";
            }
        }

        /// <summary>A "book" panel: title, tabs, list, details, coins and hint.</summary>
        class Book
        {
            public RectTransform panel; public Text title, tabs, coins, hint;
            public ListView list; public ListView list2; public DetailView details;
            public int sel, sel2, tab, column;
            public List<Row> rows = new List<Row>(), rows2 = new List<Row>();
            public float opened;
        }

        Book MakeBook(string name, bool twoLists)
        {
            var b = new Book { panel = Panel(name, new Vector2(300, 168)) };
            var box = b.panel.Find("Box");
            b.title = Label(box, "", new Vector2(0, 1), new Vector2(10, -7), TextAnchor.UpperLeft, UIRoot.Cream);
            b.tabs = Label(box, "", new Vector2(0.5f, 1), new Vector2(20, -7), TextAnchor.UpperCenter, Soft);
            b.coins = Label(box, "", new Vector2(1, 1), new Vector2(-10, -7), TextAnchor.UpperRight, new Color32(0xff, 0xc8, 0x5a, 0xff));
            b.list = new ListView(box, new Vector2(8, -22), 9, twoLists ? 138 : 146);
            if (twoLists) b.list2 = new ListView(box, new Vector2(154, -22), 9, 138);
            else b.details = new DetailView(box, new Vector2(160, -22), 132);
            b.hint = Label(box, "", new Vector2(0.5f, 0), new Vector2(0, 5), TextAnchor.LowerCenter, Soft);
            return b;
        }

        static string Tabs(string[] names, int cur) => string.Join("   ", names.Select((n, i) => i == cur ? "[" + n + "]" : n));

        /// <summary>Up/Down select, Left/Right tab (or column), Enter act. Returns true if something changed.</summary>
        static bool BookInput(Book b, int tabCount, Action refresh)
        {
            if (Time.unscaledTime - b.opened < 0.2f) return false;
            int n = b.column == 0 ? b.rows.Count : b.rows2.Count;
            ref int sel = ref (b.column == 0 ? ref b.sel : ref b.sel2);
            if (GameInput.Up && n > 0) { sel = (sel - 1 + n) % n; Sfx.Play("select", 0.5f); refresh(); return true; }
            if (GameInput.Down && n > 0) { sel = (sel + 1) % n; Sfx.Play("select", 0.5f); refresh(); return true; }
            if ((GameInput.Left || GameInput.Right) && tabCount > 1)
            {
                b.tab = (b.tab + (GameInput.Right ? 1 : tabCount - 1)) % tabCount; b.sel = 0; b.list.scroll = 0;
                Sfx.Play("select", 0.6f); refresh(); return true;
            }
            if (GameInput.Confirm && n > 0)
            {
                var r = b.column == 0 ? b.rows[Mathf.Clamp(b.sel, 0, n - 1)] : b.rows2[Mathf.Clamp(b.sel2, 0, n - 1)];
                r.act?.Invoke(); refresh(); return true;
            }
            return false;
        }

        static void ShowBook(Book b)
        {
            b.sel = Mathf.Clamp(b.sel, 0, Mathf.Max(0, b.rows.Count - 1));
            b.list.Show(b.rows, b.sel, b.column == 0);
            if (b.list2 != null) { b.sel2 = Mathf.Clamp(b.sel2, 0, Mathf.Max(0, b.rows2.Count - 1)); b.list2.Show(b.rows2, b.sel2, b.column == 1); }
            if (b.details != null) b.details.Show(b.sel < b.rows.Count ? b.rows[b.sel] : null);
            var cur = b.column == 0 ? (b.sel < b.rows.Count ? b.rows[b.sel] : null) : (b.sel2 < b.rows2.Count ? b.rows2[b.sel2] : null);
            if (cur != null && !string.IsNullOrEmpty(cur.hint)) b.hint.text = cur.hint;
            b.coins.text = $"Monedas  {GameManager.State.coins}";
        }

        static Sprite Mi(MatDef m) => m != null && GameAssets.I ? GameAssets.I.MatIcon(m.icon) : null;
        static Sprite Ii(ItemDef it) => it != null && GameAssets.I ? GameAssets.I.ItemIcon(it.icon) : null;
        static Sprite IiL(ItemDef it) => it != null && GameAssets.I ? GameAssets.I.ItemIconLarge(it.icon) : null;
        static readonly Color GoldC = new Color32(0xff, 0xc8, 0x5a, 0xff);

        static string Needs((string id, int n)[] needs, Func<string, int> have)
        {
            var lines = new List<string>();
            foreach (var (id, n) in needs)
            {
                var m = CraftDB.Get(id);
                int h = have(id);
                lines.Add($"{(h >= n ? "+" : "-")} {m?.name ?? id}  {h}/{n}");
            }
            return string.Join("\n", lines);
        }

        // ================================================================ crafting (camp workbench)
        Book _craft;
        static readonly string[] CraftTabs = { "Curación", "Ataque" };

        public static bool CraftOpen => _i != null && _i._craft != null && _i._craft.panel.gameObject.activeSelf;

        /// <summary>Crafting needs a camp: there you can also use what is in the storage.</summary>
        public static void OpenCraft(bool unused)
        {
            var ui = I;
            Open(ui._craft.panel);
            ui._craft.opened = Time.unscaledTime;
            ui.RefreshCraft();
        }

        static bool AtCamp
        {
            get
            {
                var p = PlayerController.Current;
                return p != null && (Campfire.Current != null || Campfire.Near(p.transform.position) != null);
            }
        }

        void RefreshCraft()
        {
            var b = _craft; var s = GameManager.State; bool camp = AtCamp;
            b.title.text = "Fabricar"; b.tabs.text = Tabs(CraftTabs, b.tab);
            var cat = b.tab == 0 ? RecipeCat.Healing : RecipeCat.Attack;
            int Have(string id) => camp ? s.Total(id) : s.InBag(id);
            b.rows = CraftDB.Recipes.Where(r => r.cat == cat).Select(r =>
            {
                var m = CraftDB.Get(r.result);
                bool can = r.needs.All(n => Have(n.id) >= n.n);
                return new Row
                {
                    icon = Mi(m), name = r.name + (r.count > 1 ? $" x{r.count}" : ""), color = can ? UIRoot.Cream : new Color(0.7f, 0.66f, 0.75f),
                    right = s.InBag(r.result) > 0 ? "x" + s.InBag(r.result) : "", rightColor = Soft,
                    title = m.name, sub = $"Llevas {s.InBag(r.result)} · almacén {s.InStash(r.result)}",
                    body = Needs(r.needs, Have), desc = m.desc,
                    hint = can ? "Enter fabricar · flechas: elegir · ←→ categoría · Esc salir" : "Te faltan ingredientes · ←→ categoría · Esc salir",
                    act = () => Craft(r),
                };
            }).ToList();
            ShowBook(b);
            if (!camp) b.hint.text = "Solo se fabrica en un campamento";
        }

        static void Craft(Recipe r)
        {
            var s = GameManager.State; bool camp = AtCamp;
            if (!camp) { Sfx.Play("error"); return; }
            if (!r.needs.All(n => s.Total(n.id) >= n.n)) { Sfx.Play("error"); I._craft.hint.text = "Te faltan ingredientes"; return; }
            foreach (var (id, n) in r.needs) s.Consume(id, n, true);
            int stored = s.Give(r.result, r.count);
            Sfx.Play("craft");
            I._craft.hint.text = $"Fabricado: {r.name}" + (r.count > 1 ? $" x{r.count}" : "") + (stored > 0 ? " (al almacén)" : "");
        }

        // ================================================================ storage (camp chest)
        Book _stash;
        public static void OpenStash()
        {
            var ui = I;
            Open(ui._stash.panel);
            ui._stash.opened = Time.unscaledTime;
            ui.RefreshStash();
        }

        void RefreshStash()
        {
            var b = _stash; var s = GameManager.State;
            b.title.text = "Almacén"; b.tabs.text = b.column == 0 ? "[Bolsa] → almacén" : "bolsa ← [Almacén]";
            Row R(ItemStack st, bool inBag)
            {
                var m = CraftDB.Get(st.id);
                return new Row
                {
                    icon = Mi(m), name = m?.name ?? st.id, right = "x" + st.n, rightColor = UIRoot.Cream,
                    hint = inBag ? "Enter guardar · ←→ bolsa/almacén · Esc salir" : "Enter coger (máx. " + (m?.BagCap ?? 0) + ") · ←→ bolsa/almacén · Esc salir",
                    act = () => MoveStack(st.id, inBag),
                };
            }
            b.rows = s.bag.Where(x => CraftDB.Get(x.id) != null).OrderBy(x => CraftDB.Get(x.id).icon).Select(x => R(x, true)).ToList();
            b.rows2 = s.stash.Where(x => CraftDB.Get(x.id) != null).OrderBy(x => CraftDB.Get(x.id).icon).Select(x => R(x, false)).ToList();
            ShowBook(b);
            if (b.rows.Count + b.rows2.Count == 0) b.hint.text = "No llevas nada · Esc salir";
        }

        static void MoveStack(string id, bool toStash)
        {
            var s = GameManager.State; var m = CraftDB.Get(id);
            if (toStash) { int n = s.InBag(id); PlayerState.TakeFrom(s.bag, id, n); PlayerState.AddTo(s.stash, id, n); }
            else
            {
                int room = Mathf.Max(0, m.BagCap - s.InBag(id));
                int n = PlayerState.TakeFrom(s.stash, id, room);
                if (n == 0) { Sfx.Play("error"); I._stash.hint.text = "No te cabe más en la bolsa"; return; }
                PlayerState.AddTo(s.bag, id, n);
            }
            Sfx.Play("chest", 0.5f);
        }

        void StashInput()
        {
            var b = _stash;
            if (Time.unscaledTime - b.opened < 0.2f) return;
            if (GameInput.Left || GameInput.Right) { b.column = 1 - b.column; Sfx.Play("select", 0.5f); RefreshStash(); return; }
            BookInput(b, 1, RefreshStash);
        }

        // ================================================================ trade: shops and the smith
        Book _trade;
        TradeMode[] _tradeModes = { TradeMode.Buy, TradeMode.Sell };
        string _vendor = "", _stock = "general";

        public static bool TradeOpen => _i != null && _i._trade != null && _i._trade.panel.gameObject.activeSelf;

        static readonly Dictionary<string, (string id, int price)[]> Stocks = new Dictionary<string, (string, int)[]>
        {
            { "general", new[] { ("tela", 4), ("aceite", 5), ("frasco", 3), ("madera", 2), ("hierba", 4), ("carne", 5) } },
            { "herbs", new[] { ("hierba", 3), ("raiz", 6), ("frasco", 3), ("seta_azul", 8), ("flor_luna", 15), ("seta_roja", 4) } },
            { "exotic", new[] { ("aceite", 4), ("frasco", 3), ("tela", 4), ("cristal", 18), ("plata", 22), ("ceniza", 12), ("madera", 2) } },
        };

        /// <summary>The general store (market stalls, the inn counter): ingredients, arrows, a heart — no ready-made potions.</summary>
        public static void OpenShop() => OpenShop("general", "");

        public static void OpenShop(string stock, string vendor)
        {
            var ui = I;
            ui._stock = stock; ui._vendor = vendor;
            ui._tradeModes = new[] { TradeMode.Buy, TradeMode.Sell };
            ui._trade.tab = 0; ui._trade.sel = 0;
            Open(ui._trade.panel);
            ui._trade.opened = Time.unscaledTime;
            ui.RefreshTrade();
        }

        /// <summary>The blacksmith: buy weapons and armour, sell, upgrade (+1..+5) and repair.</summary>
        public static void OpenSmith() => OpenTrade(TradeMode.Buy, "");

        public static void OpenTrade(TradeMode mode, string vendor)
        {
            var ui = I;
            ui._stock = "smith"; ui._vendor = vendor;
            ui._tradeModes = new[] { TradeMode.Buy, TradeMode.Sell, TradeMode.Upgrade, TradeMode.Repair };
            ui._trade.tab = Array.IndexOf(ui._tradeModes, mode); ui._trade.sel = 0;
            Open(ui._trade.panel);
            ui._trade.opened = Time.unscaledTime;
            ui.RefreshTrade();
        }

        static string ModeName(TradeMode m) => m == TradeMode.Buy ? "Comprar" : m == TradeMode.Sell ? "Vender" : m == TradeMode.Upgrade ? "Mejorar" : "Reparar";
        float PriceMul => _vendor == "bruna" && GameManager.State.Has("discount_bruna") ? 0.8f : 1f;

        void RefreshTrade()
        {
            var b = _trade; var s = GameManager.State;
            var mode = _tradeModes[Mathf.Clamp(b.tab, 0, _tradeModes.Length - 1)];
            var vend = NpcDB.Get(_vendor);
            b.title.text = vend != null ? vend.name : _stock == "smith" ? "Herrería" : "Tienda";
            b.tabs.text = Tabs(_tradeModes.Select(ModeName).ToArray(), b.tab);
            b.rows = mode == TradeMode.Buy ? BuyRows() : mode == TradeMode.Sell ? SellRows() : mode == TradeMode.Upgrade ? UpgradeRows() : RepairRows();
            ShowBook(b);
            if (b.rows.Count == 0) b.hint.text = mode == TradeMode.Repair ? "Todo tu equipo está en buen estado · Esc salir" : "Nada por aquí · Esc salir";
        }

        List<Row> BuyRows()
        {
            var s = GameManager.State; var rows = new List<Row>();
            if (_stock == "smith")
            {
                var stock = ItemDB.SmithStock.AsEnumerable();
                if (_vendor == "tordo") stock = stock.Concat(new[] { "katana_moon", "armor_paladin", "bow_elf", "mace_holy" });
                foreach (var id in stock.Where(x => !s.Owns(x)))
                {
                    var it = ItemDB.Get(id); int price = Mathf.RoundToInt(it.price * PriceMul);
                    rows.Add(new Row
                    {
                        icon = Ii(it), bigIcon = IiL(it), name = it.name, color = it.RarityColor, right = price.ToString(),
                        rightColor = s.coins >= price ? GoldC : new Color(1f, 0.45f, 0.45f),
                        title = it.name, titleColor = it.RarityColor, sub = $"{it.RarityName} · {(it.slot == ItemSlot.Armor ? "Armadura" : it.Style.label)}",
                        body = StatsText(it, Current(it.slot)), desc = it.desc,
                        hint = s.coins >= price ? "Enter comprar · ←→ pestaña · Esc salir" : "Te faltan monedas · ←→ pestaña · Esc salir",
                        act = () =>
                        {
                            if (s.coins < price || s.Owns(id)) { Sfx.Play("error"); return; }
                            s.coins -= price; s.AddItem(id); Sfx.Play("buy"); UIRoot.ItemToast(it);
                        },
                    });
                }
                return rows;
            }
            foreach (var (id, price) in Stocks.TryGetValue(_stock, out var st) ? st : Stocks["general"])
            {
                var m = CraftDB.Get(id); if (m == null) continue;
                rows.Add(new Row
                {
                    icon = Mi(m), name = m.name, right = price.ToString(), rightColor = s.coins >= price ? GoldC : new Color(1f, 0.45f, 0.45f),
                    title = m.name, sub = $"Llevas {s.InBag(id)} · almacén {s.InStash(id)}", body = "", desc = m.desc,
                    hint = "Enter comprar uno · ←→ pestaña · Esc salir",
                    act = () => { if (s.coins < price) { Sfx.Play("error"); return; } s.coins -= price; s.Give(id, 1); Sfx.Play("buy"); },
                });
            }
            rows.Add(new Row
            {
                icon = GameAssets.I ? GameAssets.I.iconArrow : null, name = "10 flechas", right = "10", rightColor = s.coins >= 10 ? GoldC : new Color(1f, 0.45f, 0.45f),
                title = "10 flechas", sub = $"Llevas {s.arrows}", desc = "Flechas normales para el arco.", hint = "Enter comprar · Esc salir",
                act = () => { if (s.coins < 10) { Sfx.Play("error"); return; } s.coins -= 10; s.arrows += 10; Sfx.Play("buy"); },
            });
            if (_stock == "general" && s.heartsBought < 3)
                rows.Add(new Row
                {
                    icon = GameAssets.I ? GameAssets.I.heart : null, name = "Corazón extra", right = "60", rightColor = s.coins >= 60 ? GoldC : new Color(1f, 0.45f, 0.45f),
                    title = "Corazón extra", sub = $"{s.heartsBought}/3 comprados", desc = "+2 de vida máxima, para siempre.", hint = "Enter comprar · Esc salir",
                    act = () =>
                    {
                        if (s.coins < 60 || s.heartsBought >= 3) { Sfx.Play("error"); return; }
                        s.coins -= 60; s.heartsBought++; s.RecalcHP(true);
                        var p = PlayerController.Current; if (p) p.health.Init(s.maxHP, s.hp);
                        Sfx.Play("buy");
                    },
                });
            return rows;
        }

        List<Row> SellRows()
        {
            var s = GameManager.State; var rows = new List<Row>();
            foreach (var id in s.inventory.ToArray())
            {
                var it = ItemDB.Get(id); if (it == null) continue;
                int price = CraftDB.SellPrice(it);
                rows.Add(new Row
                {
                    icon = Ii(it), bigIcon = IiL(it), name = it.name + (s.Level(id) > 0 ? $" +{s.Level(id)}" : ""), color = it.RarityColor, right = "+" + price,
                    title = it.name, titleColor = it.RarityColor, sub = $"{it.RarityName} · {(it.slot == ItemSlot.Armor ? "Armadura" : it.Style.label)}",
                    body = StatsText(it, Current(it.slot)), desc = "Se vende por un tercio de su precio.", hint = "Enter vender · ←→ pestaña · Esc salir",
                    act = () => { if (!s.inventory.Remove(id)) return; s.coins += price; Sfx.Play("sell"); },
                });
            }
            foreach (var st in s.bag.ToArray())
            {
                var m = CraftDB.Get(st.id); if (m == null) continue;
                int price = CraftDB.SellPrice(m);
                rows.Add(new Row
                {
                    icon = Mi(m), name = m.name + $" x{st.n}", right = "+" + price, title = m.name, sub = $"Llevas {st.n}", desc = m.desc,
                    hint = "Enter vender uno · ←→ pestaña · Esc salir",
                    act = () => { if (!s.Consume(st.id, 1, false)) return; s.coins += price; Sfx.Play("sell"); },
                });
            }
            return rows;
        }

        static IEnumerable<string> Gear(PlayerState s) => new[] { s.weapon, s.bow, s.armor }.Concat(s.inventory).Where(x => ItemDB.Get(x) != null).Distinct();

        List<Row> UpgradeRows()
        {
            var s = GameManager.State; var rows = new List<Row>();
            foreach (var id in Gear(s))
            {
                var it = ItemDB.Get(id); int lvl = s.Level(id);
                bool max = lvl >= CraftDB.MaxUpgrade;
                var cost = CraftDB.UpgradeCost(lvl, out int coins);
                coins = Mathf.RoundToInt(coins * PriceMul);
                bool can = !max && s.coins >= coins && cost.All(c => s.InBag(c.id) >= c.n);
                string gain = it.slot == ItemSlot.Armor ? $"Defensa +{CraftDB.UpgradeDefense(lvl + 1) - CraftDB.UpgradeDefense(lvl)} · Vida +2" : "Daño +1";
                bool eq = id == s.weapon || id == s.bow || id == s.armor;
                rows.Add(new Row
                {
                    icon = Ii(it), bigIcon = IiL(it), name = it.name + (lvl > 0 ? $" +{lvl}" : "") + (eq ? " (E)" : ""), color = it.RarityColor,
                    right = max ? "MÁX" : coins.ToString(), rightColor = max ? Soft : s.coins >= coins ? GoldC : new Color(1f, 0.45f, 0.45f),
                    title = $"{it.name} +{lvl}" + (max ? "" : $" → +{lvl + 1}"), titleColor = it.RarityColor,
                    sub = max ? "Mejorado al máximo" : gain,
                    body = max ? "" : Needs(cost, x => s.InBag(x)) + $"\n{(s.coins >= coins ? "+" : "-")} {coins} monedas",
                    desc = "Materiales de la bolsa. +1/+2 hierro; +3/+4 plata; +5 obsidiana y núcleo ígneo.",
                    hint = can ? "Enter mejorar · ←→ pestaña · Esc salir" : max ? "Ya no admite más mejoras" : "Te faltan materiales o monedas",
                    act = () =>
                    {
                        if (!can) { Sfx.Play("error"); return; }
                        foreach (var (mid, n) in cost) s.Consume(mid, n, false);
                        s.coins -= coins; s.Upgrade(id);
                        var p = PlayerController.Current; if (p) p.health.Init(s.maxHP, Mathf.Min(s.hp, s.maxHP));
                        Sfx.Play("anvil"); Sfx.Play("levelup", 0.4f);
                        UIRoot.Toast($"{it.name.ToUpperInvariant()} +{s.Level(id)}", 2f);
                    },
                });
            }
            return rows;
        }

        List<Row> RepairRows()
        {
            var s = GameManager.State; var rows = new List<Row>();
            foreach (var id in Gear(s))
            {
                int wear = s.Wear(id); if (wear <= 0) continue;
                var it = ItemDB.Get(id); int max = CraftDB.MaxDurability(it);
                int price = Mathf.RoundToInt(CraftDB.RepairCost(it, wear) * PriceMul);
                rows.Add(new Row
                {
                    icon = Ii(it), bigIcon = IiL(it), name = it.name, color = s.Broken(id) ? new Color(1f, 0.5f, 0.5f) : it.RarityColor, right = price.ToString(),
                    rightColor = s.coins >= price ? GoldC : new Color(1f, 0.45f, 0.45f),
                    title = it.name, titleColor = it.RarityColor, sub = $"Estado {s.Durability(id)}/{max}" + (s.Broken(id) ? " · ROTA" : ""),
                    body = s.Broken(id) ? (it.slot == ItemSlot.Armor ? "Rota: no protege." : "Rota: golpea a la mitad.") : "Desgastada.", desc = "El herrero la deja como nueva.",
                    hint = "Enter reparar · ←→ pestaña · Esc salir",
                    act = () => { if (s.coins < price) { Sfx.Play("error"); return; } s.coins -= price; s.Repair(id); Sfx.Play("anvil"); },
                });
            }
            return rows;
        }

        void BuildLists()
        {
            _craft = MakeBook("Craft", false);
            _stash = MakeBook("Stash", true);
            _trade = MakeBook("Trade", false);
        }

        void ListsInput()
        {
            if (_craft.panel.gameObject.activeSelf) BookInput(_craft, CraftTabs.Length, RefreshCraft);
            else if (_stash.panel.gameObject.activeSelf) StashInput();
            else if (_trade.panel.gameObject.activeSelf) BookInput(_trade, _tradeModes.Length, RefreshTrade);
        }

        /// <summary>For tests: act on the selected row of the open list panel.</summary>
        public static int ListRows => _i == null ? 0 : CraftOpen ? _i._craft.rows.Count : TradeOpen ? _i._trade.rows.Count : _i._stash.rows.Count + _i._stash.rows2.Count;
    }
}
