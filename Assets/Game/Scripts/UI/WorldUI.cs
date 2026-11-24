using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;

namespace WoodsGame
{
    /// <summary>Open-world UI: minimap, full map with fog (M), journal (Tab), shop. Time stops while a panel is open.</summary>
    public partial class WorldUI : MonoBehaviour
    {
        static WorldUI _i;
        RectTransform _root, _miniBox, _map, _journal, _sheet;
        readonly List<RectTransform> _panels = new List<RectTransform>();
        Image _sheetPortrait;
        Text _sheetLeft, _sheetRight, _sheetPoints, _sheetHelp;
        MenuList _attrMenu;
        float _sheetAnim;
        RawImage _mini, _mapImg;
        Image _miniDot;
        RectTransform _markers;
        Text _journalText;
        Texture2D _fogTex;
        float _blink;

        public static bool PanelOpen
        {
            get
            {
                if (_i == null) return false;
                foreach (var p in _i._panels) if (p != null && p.gameObject.activeSelf) return true;
                return false;
            }
        }

        static WorldUI I
        {
            get
            {
                if (_i) return _i;
                var go = new GameObject("WorldUI");
                DontDestroyOnLoad(go);
                _i = go.AddComponent<WorldUI>();
                _i.Build();
                return _i;
            }
        }

        static readonly Color Ink = new Color32(0xf4, 0xed, 0xea, 0xff);
        static readonly Color Ink2 = new Color32(0xa9, 0xa3, 0xb8, 0xff);

        void Build()
        {
            _root = UIRoot.CreateCanvas(transform, 90);
            var a = GameAssets.I;
            // minimap (top-right)
            _miniBox = UIRoot.Rect(_root, "Minimap", new Vector2(1, 1), new Vector2(1, 1), new Vector2(-5, -5), new Vector2(62, 40));
            var mframe = UIRoot.Img(_miniBox, a ? a.flatSlot : null, true); mframe.rectTransform.sizeDelta = new Vector2(62, 40); mframe.color = new Color(1, 1, 1, 0.9f);
            _mini = new GameObject("Map", typeof(RectTransform), typeof(RawImage)).GetComponent<RawImage>();
            _mini.transform.SetParent(_miniBox, false);
            _mini.rectTransform.sizeDelta = new Vector2(60, 38);
            _miniDot = UIRoot.Img(_miniBox, null, false); _miniDot.color = UIRoot.Red; _miniDot.rectTransform.sizeDelta = new Vector2(2, 2);
            _miniBox.gameObject.SetActive(false);

            // full map
            _map = Panel("FullMap", new Vector2(256, 176));
            _mapImg = new GameObject("Map", typeof(RectTransform), typeof(RawImage)).GetComponent<RawImage>();
            _mapImg.transform.SetParent(_map.Find("Box"), false);
            _mapImg.rectTransform.sizeDelta = new Vector2(240, 160);
            _mapImg.rectTransform.anchoredPosition = new Vector2(0, -3);
            _markers = UIRoot.Rect(_mapImg.transform, "Markers", Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            BuildMapTexts();

            // journal
            _journal = Panel("Journal", new Vector2(250, 170));
            _journalText = Label(_journal.Find("Box"), "", new Vector2(0, 1), new Vector2(12, -10), TextAnchor.UpperLeft, Ink2);
            _journalText.rectTransform.sizeDelta = new Vector2(230, 150);

            BuildSheet();
            BuildInventory();
            BuildLists();
            BuildTalk();
            CloseAll();
        }

        RectTransform Panel(string name, Vector2 size)
        {
            var dim = UIRoot.Rect(_root, name, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            dim.gameObject.AddComponent<Image>().color = new Color(0.03f, 0.02f, 0.06f, 0.55f);
            var box = UIRoot.Rect(dim, "Box", new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, size);
            UIRoot.Img(box, GameAssets.I ? GameAssets.I.panel : null, true).rectTransform.sizeDelta = size;
            _panels.Add(dim);
            return dim;
        }

        static Text Label(Transform p, string t, Vector2 anchor, Vector2 pos, TextAnchor al, Color c) => UIRoot.Label(p, t, anchor, pos, al, c);

        // ================================================================ map texture with fog
        /// <summary>Minimap picture: the fogged world map in the overworld, the town/zone plan elsewhere.</summary>
        Texture2D MapTexture(bool fog) => InWorldMap ? WorldMapTexture(fog) : LocalMapTexture();

        void Update()
        {
            var wi = WorldInfo.Current;
            var p = PlayerController.Current;
            bool inWorld = wi != null && p != null && LevelInfo.Current != null && !GameManager.Ended;
            _miniBox.gameObject.SetActive(inWorld && !PanelOpen && Interior.Current == null && !wi.Underground(p.transform.position));
            if (inWorld && _sheet.gameObject.activeSelf) AnimateSheet();
            if (inWorld && _inv.gameObject.activeSelf) InventoryInput();
            if (inWorld) ListsInput();
            if (inWorld && _talk.gameObject.activeSelf) AnimateTalk();
            if (!inWorld) return;
            _blink += Time.unscaledDeltaTime;
            if (_mini.texture == null || Time.frameCount % 120 == 0) _mini.texture = MapTexture(true);
            // minimap window: 60x38 tiles around the player
            float sw = wi.IsWorld ? wi.surfaceWidth : wi.width;          // the map picture covers the surface only
            float u = p.transform.position.x / sw, v = p.transform.position.y / wi.height;
            float ww = 60f / sw, hh = 38f / wi.height;
            _mini.uvRect = new Rect(Mathf.Clamp(u - ww / 2, 0, 1 - ww), Mathf.Clamp(v - hh / 2, 0, 1 - hh), ww, hh);
            var r = _mini.uvRect;
            _miniDot.rectTransform.anchoredPosition = new Vector2((u - r.x) / r.width * 60 - 30, (v - r.y) / r.height * 38 - 19);
            _miniDot.enabled = (_blink % 0.6f) < 0.4f;
            if (_map.gameObject.activeSelf) { MapInput(); UpdateMapView(wi, p); }
        }

        // ================================================================ API
        public static void CloseAll() => CloseAll(true);

        static void CloseAll(bool endTalk)
        {
            if (_i == null) return;
            bool any = false;
            foreach (var p in _i._panels) if (p != null) { any |= p.gameObject.activeSelf; p.gameObject.SetActive(false); }
            if (any && !_quiet) Sfx.Play("menu_close", 0.5f);
            if (endTalk) Dialogue.End();
            if (!GameManager.Paused) Time.timeScale = 1f;
        }

        static bool _quiet;

        static void Open(RectTransform panel)
        {
            bool was = panel.gameObject.activeSelf;
            _quiet = true; CloseAll(panel != I._talk); _quiet = false;           // the conversation box replaces itself without ending the talk
            panel.gameObject.SetActive(true);
            Time.timeScale = 0f;
            if (!was && panel != I._talk) Sfx.Play("menu_open", 0.6f);
        }

        public static void ToggleMap()
        {
            if (I._map.gameObject.activeSelf) { CloseAll(); return; }
            Open(I._map);
            I.ShowMap(false);          // a town opens its own map first; Left/Right switch to the world
        }

        public static void ToggleJournal()
        {
            if (I._journal.gameObject.activeSelf) { CloseAll(); return; }
            var s = GameManager.State;
            var lines = new List<string>
            {
                $"DIARIO      NIVEL {s.level}   XP {s.xp}/{s.XpToNext}   ESPADA {s.SwordDamage}",
                ""
            };
            foreach (var q in Quests.Visible(s))
            {
                string mark = q.Rewarded(s) ? "[X]" : "[ ]";
                string prog = q.goal > 1 ? $" {Mathf.Min(q.progress(s), q.goal)}/{q.goal}" : "";
                lines.Add($"{mark} {(q.main ? "* " : "")}{q.title}{prog}");
            }
            var npcJobs = Dialogue.JournalLines().ToList();
            if (npcJobs.Count > 0) { lines.Add(""); lines.Add("ENCARGOS"); lines.AddRange(npcJobs); }
            var next = Quests.Visible(s).FirstOrDefault(q => q.main && !q.Rewarded(s));
            lines.Add("");
            lines.Add(next != null ? next.description : "HAS COMPLETADO LA HISTORIA. EL MUNDO SIGUE ABIERTO.");
            lines.Add("");
            lines.Add($"ENEMIGOS {s.kills}   COFRES {s.chestsOpened}   REGIONES {s.flags.Count(f => f.StartsWith("region_"))}/10   AMENAZA {s.Threat}");
            I._journalText.text = UIRoot.Pretty(string.Join("\n", lines));
            I._journalText.horizontalOverflow = HorizontalWrapMode.Wrap;
            Open(I._journal);
        }

        // ---------------------------------------------------------------- character sheet (C)
        void BuildSheet()
        {
            _sheet = Panel("CharacterSheet", new Vector2(296, 168));
            var box = _sheet.Find("Box");
            Label(box, "FICHA DEL HÉROE", new Vector2(0.5f, 1), new Vector2(0, -6), TextAnchor.UpperCenter, Ink);
            var frame = UIRoot.Rect(box, "Portrait", new Vector2(0, 1), new Vector2(0, 1), new Vector2(10, -18), new Vector2(66, 66));
            frame.gameObject.AddComponent<Image>().color = new Color32(0xff, 0xff, 0xff, 0x30);
            var inner = UIRoot.Rect(frame, "In", new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(64, 64));
            inner.gameObject.AddComponent<Image>().color = new Color32(0x3e, 0x89, 0x48, 0xff);
            _sheetPortrait = UIRoot.Img(inner, null, false); _sheetPortrait.rectTransform.sizeDelta = new Vector2(64, 64);
            _sheetLeft = Label(box, "", new Vector2(0, 1), new Vector2(10, -88), TextAnchor.UpperLeft, Ink2);
            _sheetLeft.rectTransform.sizeDelta = new Vector2(84, 74); _sheetLeft.horizontalOverflow = HorizontalWrapMode.Wrap;
            _sheetPoints = Label(box, "", new Vector2(0, 1), new Vector2(86, -18), TextAnchor.UpperLeft, Ink);
            _sheetRight = Label(box, "", new Vector2(0, 1), new Vector2(196, -18), TextAnchor.UpperLeft, Ink2);
            _sheetRight.rectTransform.sizeDelta = new Vector2(96, 140);
            _sheetHelp = Label(box, "", new Vector2(0.5f, 0), new Vector2(0, 6), TextAnchor.LowerCenter, Ink2);
        }

        public static void ToggleCharacter()
        {
            if (I._sheet.gameObject.activeSelf) { CloseAll(); return; }
            Open(I._sheet);
            I.RefreshSheet(0);
        }

        const string NL = "\n";

        void RefreshSheet(int index)
        {
            var s = GameManager.State;
            var k = s.Class;
            var p = PlayerController.Current;
            int hp = p ? p.health.hp : s.hp;
            _sheetLeft.text = UIRoot.Pretty(string.Join(NL, k.name, k.perk)) + NL + NL + s.Weapon.name + NL + s.Bow.name + NL + s.ArmorItem.name;
            _sheetPoints.text = $"Nivel {s.level}   XP {s.xp}/{s.XpToNext}" + NL + (s.attrPoints > 0 ? $"Puntos para repartir: {s.attrPoints}" : "Atributos");
            _sheetRight.text = UIRoot.Pretty(string.Join(NL,
                $"VIDA      {hp}/{s.maxHP}", $"ESPADA    {s.SwordDamage}", $"ARCO      {s.ArrowDamage}",
                $"CRÍTICO   {Mathf.RoundToInt(s.CritChance * 100)}%", $"ARMADURA  {s.Armor}", $"ESQUIVA   {Mathf.RoundToInt(s.DodgeChance * 100)}%",
                $"VELOCIDAD {Mathf.RoundToInt(s.SpeedMultiplier * 100)}%", $"AGUANTE   {Mathf.RoundToInt(s.MaxStamina)}", $"VENDA     +{s.HealPower(4)}",
                $"ENEMIGOS  {s.kills}", $"PODEROSOS {s.eliteKills + s.champions}", $"AMENAZA   {s.Threat}/10",
                $"DÍA {s.day}  {DayNight.TimeText}"));
            var labels = new string[5]; var acts = new Action[5];
            for (int i = 0; i < 5; i++)
            {
                int a = i;
                labels[i] = $"{KnightClass.AttrNames[i],-10}{s.Get(i),3}" + (s.attrPoints > 0 ? " +" : "  ");
                acts[i] = () => SpendPoint(a);
            }
            if (_attrMenu == null)
                _attrMenu = MenuList.Create(_sheet.Find("Box"), labels, acts, new Vector2(-6, 8), Ink2, new Color32(0xff, 0xc8, 0x5a, 0xff), 13);
            else _attrMenu.SetLabels(labels);           // in place: quick repeated Enter presses all count
            _attrMenu.Select(index);
            _sheetHelp.text = UIRoot.Pretty(KnightClass.AttrHelp[index]) + (s.attrPoints > 0 ? " · Enter subir" : " · C cerrar");
        }

        void SpendPoint(int attr)
        {
            var s = GameManager.State;
            if (!s.Spend(attr)) { Sfx.Play("error"); return; }
            var p = PlayerController.Current;
            if (p) p.health.Init(s.maxHP, s.hp);
            Sfx.Play("levelup", 0.5f);
            RefreshSheet(attr);
        }

        void AnimateSheet()
        {
            _sheetAnim += Time.unscaledDeltaTime;
            var f = GameAssets.I ? GameAssets.I.ClassIdle(GameManager.State.classId) : null;
            if (f != null && f.Length > 0) { _sheetPortrait.sprite = f[(int)(_sheetAnim * 6) % f.Length]; _sheetPortrait.color = Color.white; }
            if (_attrMenu != null && _sheetHelp != null)
            {
                var s = GameManager.State;
                _sheetHelp.text = UIRoot.Pretty(KnightClass.AttrHelp[_attrMenu.Index]) + (s.attrPoints > 0 ? " · Enter subir" : " · C cerrar");
            }
        }
    }
}
