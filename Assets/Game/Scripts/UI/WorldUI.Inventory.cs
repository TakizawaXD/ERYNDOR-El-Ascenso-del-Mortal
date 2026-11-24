using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;

namespace WoodsGame
{
    /// <summary>Inventory (I): equipped weapon / bow / armour, a grid of everything you own, details with a comparison
    /// against what you wear, Enter to equip. Also the blacksmith's shop (anvils) that sells weapons and armour.</summary>
    public partial class WorldUI
    {
        RectTransform _inv;
        readonly List<Image> _invSlots = new List<Image>(), _invIcons = new List<Image>();
        readonly List<Text> _invMarks = new List<Text>();
        Image[] _eqIcons = new Image[3];
        Text[] _eqNames = new Text[3];
        Image _detIcon;
        Text _detName, _detInfo, _detStats, _detDesc, _invHint;
        int _invIndex, _invPage;          // page 0 equipment, 1 bag (materials and consumables)
        List<string> _invItems = new List<string>();
        Text _invTitle;
        readonly List<Text> _invCounts = new List<Text>();
        const int Cols = 6, Rows = 4;

        static readonly Color Good = new Color32(0x8e, 0xe0, 0x7a, 0xff), Bad = new Color32(0xff, 0x7a, 0x7a, 0xff);
        static readonly Color Soft = new Color32(0xa9, 0xa3, 0xb8, 0xff);

        void BuildInventory()
        {
            var a = GameAssets.I;
            _inv = Panel("Inventory", new Vector2(300, 168));
            var box = _inv.Find("Box");
            _invTitle = Label(box, "Inventario", new Vector2(0, 1), new Vector2(10, -7), TextAnchor.UpperLeft, UIRoot.Cream);
            string[] slotNames = { "Arma", "Arco", "Armadura" };
            for (int i = 0; i < 3; i++)
            {
                var s = SlotImg(box, new Vector2(10 + i * 46, -22), false);
                _eqIcons[i] = Icon(s);
                Label(box, slotNames[i], new Vector2(0, 1), new Vector2(31 + i * 46, -27), TextAnchor.UpperLeft, Soft);
                _eqNames[i] = Label(box, "", new Vector2(0, 1), new Vector2(31 + i * 46, -31), TextAnchor.UpperLeft, UIRoot.Cream);
            }
            for (int r = 0; r < Rows; r++)
                for (int c = 0; c < Cols; c++)
                {
                    var s = SlotImg(box, new Vector2(10 + c * 23, -52 - r * 23), false);
                    _invSlots.Add(s);
                    _invIcons.Add(Icon(s));
                    var m = UIRoot.Label(s.transform, "", new Vector2(1, 1), new Vector2(0, 1), TextAnchor.UpperRight, new Color32(0xff, 0xc8, 0x5a, 0xff));
                    _invMarks.Add(m);
                    _invCounts.Add(UIRoot.Label(s.transform, "", new Vector2(1, 0), new Vector2(1, -1), TextAnchor.LowerRight, UIRoot.Cream));
                }
            // details
            var det = UIRoot.Rect(box, "Details", new Vector2(0, 1), new Vector2(0, 1), new Vector2(156, -50), new Vector2(136, 110));
            _detIcon = UIRoot.Img(det, null, false);
            var dr = _detIcon.rectTransform; dr.anchorMin = dr.anchorMax = new Vector2(0, 1); dr.pivot = new Vector2(0, 1);
            dr.sizeDelta = new Vector2(32, 32); dr.anchoredPosition = new Vector2(0, 0);
            _detName = Label(det, "", new Vector2(0, 1), new Vector2(36, -2), TextAnchor.UpperLeft, UIRoot.Cream);
            _detInfo = Label(det, "", new Vector2(0, 1), new Vector2(36, -12), TextAnchor.UpperLeft, Soft);
            _detStats = Label(det, "", new Vector2(0, 1), new Vector2(0, -36), TextAnchor.UpperLeft, UIRoot.Cream);
            _detStats.rectTransform.sizeDelta = new Vector2(136, 60);
            _detDesc = Label(det, "", new Vector2(0, 1), new Vector2(0, -88), TextAnchor.UpperLeft, Soft);
            _detDesc.rectTransform.sizeDelta = new Vector2(136, 24); _detDesc.horizontalOverflow = HorizontalWrapMode.Wrap;
            _invHint = Label(box, "", new Vector2(0.5f, 0), new Vector2(0, 5), TextAnchor.LowerCenter, Soft);
        }

        Image SlotImg(Transform parent, Vector2 pos, bool sel)
        {
            var a = GameAssets.I;
            var rt = UIRoot.Rect(parent, "Slot", new Vector2(0, 1), new Vector2(0, 1), pos, new Vector2(20, 20));
            var im = rt.gameObject.AddComponent<Image>();
            im.sprite = a ? (sel ? a.flatSlotSelected : a.flatSlot) : null; im.type = Image.Type.Sliced;
            if (im.sprite == null) im.color = new Color(1, 1, 1, 0.15f);
            return im;
        }

        static Image Icon(Image slot)
        {
            var ic = UIRoot.Img(slot.transform, null, false);
            ic.rectTransform.sizeDelta = new Vector2(16, 16);
            return ic;
        }

        public static void ToggleInventory()
        {
            if (I._inv.gameObject.activeSelf) { CloseAll(); return; }
            Open(I._inv);
            I.RefreshInventory();
        }

        void RefreshInventory()
        {
            if (_invPage == 1) { RefreshBag(); return; }
            _invTitle.text = "Inventario   [Equipo]  Bolsa (R)";
            foreach (var c in _invCounts) c.text = "";
            var s = GameManager.State; var a = GameAssets.I;
            _invItems = new List<string> { s.weapon, s.bow, s.armor };
            _invItems.AddRange(s.inventory.Where(id => ItemDB.Get(id) != null)
                .OrderBy(id => (int)ItemDB.Get(id).slot).ThenByDescending(id => (int)ItemDB.Get(id).rarity));
            _invIndex = Mathf.Clamp(_invIndex, 0, Mathf.Max(0, Mathf.Min(_invItems.Count, Cols * Rows) - 1));
            var eq = new[] { s.Weapon, s.Bow, s.ArmorItem };
            for (int i = 0; i < 3; i++)
            {
                _eqIcons[i].sprite = a ? a.ItemIcon(eq[i].icon) : null; _eqIcons[i].color = Color.white;
                _eqNames[i].text = ""; _eqIcons[i].transform.parent.GetComponent<Image>().color = eq[i].rarity == Rarity.Common ? Color.white : eq[i].RarityColor;
            }
            for (int k = 0; k < _invSlots.Count; k++)
            {
                var it = k < _invItems.Count ? ItemDB.Get(_invItems[k]) : null;
                _invIcons[k].sprite = it != null && a ? a.ItemIcon(it.icon) : null;
                _invIcons[k].color = it != null ? Color.white : Color.clear;
                _invSlots[k].sprite = a ? (k == _invIndex ? a.flatSlotSelected : a.flatSlot) : null;
                _invSlots[k].color = it != null ? Color.Lerp(Color.white, it.RarityColor, it.rarity == Rarity.Common ? 0f : 0.55f) : new Color(1, 1, 1, 0.5f);
                _invMarks[k].text = k < 3 ? "E" : "";
            }
            ShowDetails(_invIndex < _invItems.Count ? ItemDB.Get(_invItems[_invIndex]) : null, _invIndex < 3);
        }

        static string Short(string n) => n.Length > 9 ? n.Substring(0, 8) + "." : n;

        void ShowDetails(ItemDef it, bool equipped)
        {
            var a = GameAssets.I;
            if (it == null) { _detName.text = _detInfo.text = _detStats.text = _detDesc.text = ""; _detIcon.color = Color.clear; _invHint.text = "I cerrar"; return; }
            _detIcon.sprite = a ? a.ItemIconLarge(it.icon) : null; _detIcon.color = Color.white;
            _detName.text = it.name; _detName.color = it.RarityColor;
            string type = it.slot == ItemSlot.Armor ? "Armadura" : it.Style.label;
            _detInfo.text = $"{it.RarityName} · {type}" + (it.element != Element.None ? " · " + ItemDB.ElementNames[(int)it.element] : "");
            _detStats.text = StatsText(it, Current(it.slot));
            _detDesc.text = it.desc;
            var st = GameManager.State;
            int lvl = st.Level(it.id), dur = st.Durability(it.id), max = CraftDB.MaxDurability(it);
            if (lvl > 0) _detName.text = $"{it.name} +{lvl}";
            _detDesc.text = $"Estado {dur}/{max}" + (st.Broken(it.id) ? " · ROTA" : "") + "\n" + it.desc;
            _invHint.text = equipped ? "Equipado · flechas: elegir · R bolsa · I cerrar" : "Enter equipar · flechas: elegir · R bolsa · I cerrar";
        }

        // ---------------------------------------------------------------- bag page (materials and consumables)
        List<ItemStack> _bagItems = new List<ItemStack>();

        void RefreshBag()
        {
            var s = GameManager.State; var a = GameAssets.I;
            _invTitle.text = "Inventario   Equipo  [Bolsa] (R)";
            _bagItems = s.bag.Where(x => CraftDB.Get(x.id) != null).OrderBy(x => CraftDB.Get(x.id).icon).ToList();
            var eq = new[] { s.Weapon, s.Bow, s.ArmorItem };
            for (int i = 0; i < 3; i++) { _eqIcons[i].sprite = a ? a.ItemIcon(eq[i].icon) : null; _eqIcons[i].color = new Color(1, 1, 1, 0.35f); }
            _invIndex = Mathf.Clamp(_invIndex, 0, Mathf.Max(0, Mathf.Min(_bagItems.Count, Cols * Rows) - 1));
            for (int k = 0; k < _invSlots.Count; k++)
            {
                var st = k < _bagItems.Count ? _bagItems[k] : null;
                var m = st != null ? CraftDB.Get(st.id) : null;
                _invIcons[k].sprite = m != null && a ? a.MatIcon(m.icon) : null;
                _invIcons[k].color = m != null ? Color.white : Color.clear;
                _invSlots[k].sprite = a ? (k == _invIndex ? a.flatSlotSelected : a.flatSlot) : null;
                _invSlots[k].color = m != null ? (m.Consumable ? new Color(0.85f, 1f, 0.85f) : Color.white) : new Color(1, 1, 1, 0.5f);
                _invMarks[k].text = st != null && st.id == s.quick ? "Q" : "";
                _invCounts[k].text = st != null ? st.n.ToString() : "";
            }
            var cur = _invIndex < _bagItems.Count ? _bagItems[_invIndex] : null;
            var md = cur != null ? CraftDB.Get(cur.id) : null;
            if (md == null) { _detName.text = "Bolsa vacía"; _detInfo.text = _detStats.text = _detDesc.text = ""; _detIcon.color = Color.clear; _invHint.text = "R equipo · I cerrar"; return; }
            _detIcon.sprite = a ? a.MatIcon(md.icon) : null; _detIcon.color = Color.white;
            _detName.text = md.name; _detName.color = UIRoot.Cream;
            _detInfo.text = (md.Consumable ? "Consumible" : "Material") + $" · llevas {cur.n}/{md.BagCap}";
            _detStats.text = $"En el almacén: {s.InStash(md.id)}";
            _detDesc.text = CraftDB.Describe(md);
            _invHint.text = md.Consumable ? "Enter usar · Q rápido · R equipo · I cerrar" : "Material de fabricación · R equipo · I cerrar";
        }

        void BagInput()
        {
            int n = Mathf.Min(_bagItems.Count, Cols * Rows);
            if (n == 0) return;
            int i = _invIndex;
            if (GameInput.Left) i--; else if (GameInput.Right) i++;
            else if (GameInput.Up) i -= Cols; else if (GameInput.Down) i += Cols;
            else if (GameInput.Confirm && i < _bagItems.Count)
            {
                var m = CraftDB.Get(_bagItems[i].id);
                if (m != null && m.Consumable)
                {
                    var s = GameManager.State;
                    s.quick = m.id;                                   // becomes the quick item (Q)
                    var p = PlayerController.Current;
                    CloseAll();
                    if (p) p.UseItem(m.id);
                }
                return;
            }
            else if (GameInput.Potion && i < _bagItems.Count)
            {
                var m = CraftDB.Get(_bagItems[i].id);
                if (m != null && m.Consumable) { GameManager.State.quick = m.id; Sfx.Play("confirm"); RefreshBag(); }
                return;
            }
            else return;
            i = Mathf.Clamp(i, 0, n - 1);
            if (i != _invIndex) { _invIndex = i; Sfx.Play("select", 0.5f); RefreshBag(); }
        }

        static ItemDef Current(ItemSlot slot)
        {
            var s = GameManager.State;
            return slot == ItemSlot.Weapon ? s.Weapon : slot == ItemSlot.Bow ? s.Bow : s.ArmorItem;
        }

        /// <summary>Stat lines with the difference to the equipped item of the same slot.</summary>
        public static string StatsText(ItemDef it, ItemDef cur)
        {
            var lines = new List<string>();
            string Cmp(int v, int c) => cur == null || cur == it || v == c ? "" : v > c ? $"  (+{v - c})" : $"  ({v - c})";
            string CmpF(float v, float c) => cur == null || cur == it || Mathf.Approximately(v, c) ? "" : v > c ? $"  (+{Mathf.RoundToInt((v - c) * 100)}%)" : $"  ({Mathf.RoundToInt((v - c) * 100)}%)";
            if (it.slot != ItemSlot.Armor)
            {
                lines.Add($"Daño +{it.damage}{Cmp(it.damage, cur?.damage ?? 0)}");
                var st = it.Style;
                if (it.slot == ItemSlot.Weapon) lines.Add($"Alcance {Mathf.RoundToInt(st.reach * 10)}  ·  Velocidad {Mathf.RoundToInt(0.5f / (st.windup + st.recover) * 100)}%");
                else lines.Add($"Tensado {st.windup:0.0}s" + (it.multishot > 1 ? $"  ·  {it.multishot} flechas" : "") + (it.pierce > 0 ? "  ·  perfora" : ""));
            }
            else
            {
                lines.Add($"Defensa +{it.defense}{Cmp(it.defense, cur?.defense ?? 0)}");
                if (it.hp != 0 || (cur != null && cur.hp != 0)) lines.Add($"Vida +{it.hp}{Cmp(it.hp, cur?.hp ?? 0)}");
                lines.Add($"Velocidad {(it.speedMod >= 0 ? "+" : "")}{Mathf.RoundToInt(it.speedMod * 100)}%{CmpF(it.speedMod, cur?.speedMod ?? 0)}");
            }
            if (it.crit > 0 || (cur != null && cur.crit > 0)) lines.Add($"Crítico +{Mathf.RoundToInt(it.crit * 100)}%{CmpF(it.crit, cur?.crit ?? 0)}");
            if (it.lifesteal > 0) lines.Add("Roba vida al golpear");
            if (it.element == Element.Fire) lines.Add("Quema: daño durante 3 s");
            if (it.element == Element.Frost) lines.Add("Hiela: enemigos más lentos");
            if (it.element == Element.Venom) lines.Add("Veneno: daño durante 4 s");
            if (it.element == Element.Holy) lines.Add("x1,5 contra demonios");
            return string.Join("\n", lines);
        }

        void InventoryInput()
        {
            if (GameInput.Cycle) { _invPage = 1 - _invPage; _invIndex = 0; Sfx.Play("select", 0.6f); RefreshInventory(); return; }
            if (_invPage == 1) { BagInput(); return; }
            int n = Mathf.Min(_invItems.Count, Cols * Rows);
            if (n == 0) return;
            int i = _invIndex;
            if (GameInput.Left) i--; else if (GameInput.Right) i++;
            else if (GameInput.Up) i -= Cols; else if (GameInput.Down) i += Cols;
            else if (GameInput.Confirm && i >= 3 && i < _invItems.Count)
            {
                var id = _invItems[i];
                var cls = GameManager.State.Class; var item = ItemDB.Get(id);
                if (item != null && !cls.CanUse(item)) { UIRoot.Toast(cls.WhyNot(item), 2.2f); Sfx.Play("error", 0.7f); return; }
                if (GameManager.State.Equip(id))
                {
                    var p = PlayerController.Current; var s = GameManager.State;
                    if (p) p.health.Init(s.maxHP, Mathf.Min(s.hp, s.maxHP));
                    Sfx.Play("equip", 0.8f);
                    _invIndex = (int)ItemDB.Get(id).slot;              // the new item now sits in its equipped slot
                    RefreshInventory();
                }
                return;
            }
            else return;
            i = Mathf.Clamp(i, 0, n - 1);
            if (i != _invIndex) { _invIndex = i; Sfx.Play("select", 0.5f); RefreshInventory(); }
        }
    }
}
