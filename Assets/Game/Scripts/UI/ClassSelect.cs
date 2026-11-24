using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace WoodsGame
{
    /// <summary>"ELIGE TU HÉROE" (2026-11-21): a carousel of the ten classes (five cards in view around the chosen one,
    /// A/D or arrows or the mouse), each with its own drawn character, gender and attributes; Enter goes to the second
    /// step, the hero's name (type it, Backspace to erase, Enter to start, Esc back to the classes).</summary>
    public class ClassSelect : MonoBehaviour
    {
        public static ClassSelect Current { get; private set; }
        public int Index { get; private set; }
        /// <summary>Called with (class id, hero name).</summary>
        public Action<string, string> onChosenNamed;
        public Action<string> onChosen;
        public Action onBack;

        const float CardW = 58, CardH = 112, Step = 62;
        readonly List<RectTransform> _cardRoots = new List<RectTransform>();
        readonly List<Image> _cards = new List<Image>();
        readonly List<Image> _previews = new List<Image>();
        Text _desc, _perk, _hint, _title;
        RectTransform _nameBox;
        Text _nameText, _nameClass;
        string _name = "";
        bool _naming;
        float _t, _openedAt, _scroll;

        public bool Naming => _naming;
        public string TypedName => _name;
        const int MaxName = 14;

        static readonly Color Ink = new Color32(0xf4, 0xed, 0xea, 0xff), Ink2 = new Color32(0xa9, 0xa3, 0xb8, 0xff);
        static readonly Color Pip = new Color32(0xff, 0xc8, 0x5a, 0xff), PipOff = new Color32(0x3a, 0x34, 0x4a, 0xff);
        static readonly Color Stage = new Color32(0x1d, 0x2a, 0x2c, 0xff), StageLit = new Color32(0x2a, 0x3e, 0x3a, 0xff);
        static readonly Color Female = new Color32(0xf2, 0x9b, 0xc8, 0xff), Male = new Color32(0x8c, 0xc4, 0xff, 0xff);

        public static ClassSelect Create(RectTransform root)
        {
            var dim = UIRoot.Rect(root, "ClassSelect", Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            dim.gameObject.AddComponent<Image>().color = new Color(0.05f, 0.04f, 0.1f, 0.9f);
            var cs = dim.gameObject.AddComponent<ClassSelect>();
            cs.Build(dim);
            dim.gameObject.SetActive(false);
            return cs;
        }

        void Build(RectTransform dim)
        {
            var a = GameAssets.I;
            _title = UIRoot.Label(dim, "ELIGE TU HÉROE", new Vector2(0.5f, 1), new Vector2(0, -6), TextAnchor.UpperCenter, UIRoot.Gold);
            var strip = UIRoot.Rect(dim, "Carousel", new Vector2(0.5f, 1), new Vector2(0.5f, 1), new Vector2(0, -20), new Vector2(Step * 5, CardH + 6));
            strip.gameObject.AddComponent<RectMask2D>();
            for (int i = 0; i < KnightClass.All.Length; i++)
            {
                var k = KnightClass.All[i];
                var card = UIRoot.Rect(strip, "Card" + i, new Vector2(0.5f, 1), new Vector2(0.5f, 1), Vector2.zero, new Vector2(CardW, CardH));
                _cardRoots.Add(card);
                var bg = UIRoot.Img(card, a ? a.panel : null, true); bg.rectTransform.sizeDelta = new Vector2(CardW, CardH);
                if (!a || !a.panel) bg.color = new Color(0.08f, 0.07f, 0.12f, 0.9f);
                _cards.Add(bg);
                var stage = UIRoot.Rect(card, "Stage", new Vector2(0.5f, 1), new Vector2(0.5f, 1), new Vector2(0, -5), new Vector2(CardW - 10, 42));
                stage.gameObject.AddComponent<RectMask2D>();
                stage.gameObject.AddComponent<Image>().color = Stage;
                var pv = UIRoot.Img(stage, null, false);
                pv.rectTransform.anchorMin = pv.rectTransform.anchorMax = new Vector2(0.5f, 0); pv.rectTransform.pivot = new Vector2(0.5f, 0);
                pv.rectTransform.sizeDelta = new Vector2(64, 64); pv.rectTransform.anchoredPosition = new Vector2(0, -12);
                _previews.Add(pv);
                var name = UIRoot.Label(card, k.shortName, new Vector2(0.5f, 1), new Vector2(0, -49), TextAnchor.UpperCenter, Ink);
                name.rectTransform.sizeDelta = new Vector2(CardW, 12);
                var g = UIRoot.Label(card, k.GenderName, new Vector2(0.5f, 1), new Vector2(0, -58), TextAnchor.UpperCenter, k.female ? Female : Male);
                g.rectTransform.sizeDelta = new Vector2(CardW, 10);
                int[] vals = { k.str, k.vit, k.agi, k.dex, k.def };
                for (int s = 0; s < 5; s++)
                {
                    UIRoot.Label(card, KnightClass.AttrShort[s], new Vector2(0, 1), new Vector2(4, -68 - s * 8.5f), TextAnchor.UpperLeft, Ink2);
                    for (int d = 0; d < 6; d++)
                    {
                        var pip = UIRoot.Rect(card, "pip", new Vector2(0, 1), new Vector2(0, 1), new Vector2(22 + d * 5.5f, -70 - s * 8.5f), new Vector2(4, 4));
                        pip.gameObject.AddComponent<Image>().color = d < vals[s] ? Pip : PipOff;
                    }
                }
                int idx = i;
                var trig = card.gameObject.AddComponent<EventTrigger>();
                bg.raycastTarget = true;
                var enter = new EventTrigger.Entry { eventID = EventTriggerType.PointerEnter }; enter.callback.AddListener(_ => { if (!_naming) Select(idx); }); trig.triggers.Add(enter);
                var click = new EventTrigger.Entry { eventID = EventTriggerType.PointerClick };
                click.callback.AddListener(_ => { if (_naming) return; if (idx == Index) Choose(); else Select(idx); }); trig.triggers.Add(click);
            }
            var info = UIRoot.Rect(dim, "Info", new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0, 4), new Vector2(300, 40));
            var ib = UIRoot.Img(info, a ? a.dialog : null, true); ib.rectTransform.sizeDelta = new Vector2(300, 40);
            _desc = UIRoot.Label(info, "", new Vector2(0.5f, 1), new Vector2(0, -5), TextAnchor.UpperCenter, UIRoot.Cream);
            _perk = UIRoot.Label(info, "", new Vector2(0.5f, 1), new Vector2(0, -16), TextAnchor.UpperCenter, UIRoot.Gold);
            _hint = UIRoot.Label(info, "", new Vector2(0.5f, 1), new Vector2(0, -27), TextAnchor.UpperCenter, new Color(1, 1, 1, 0.6f));

            // step 2: the name
            _nameBox = UIRoot.Rect(dim, "NameBox", new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(0, 6), new Vector2(170, 56));
            var nb = UIRoot.Img(_nameBox, a ? a.dialog : null, true); nb.rectTransform.sizeDelta = new Vector2(170, 56);
            if (!a || !a.dialog) nb.color = new Color(0.08f, 0.07f, 0.12f, 0.95f);
            _nameClass = UIRoot.Label(_nameBox, "", new Vector2(0.5f, 1), new Vector2(0, -5), TextAnchor.UpperCenter, Ink2);
            UIRoot.Label(_nameBox, "NOMBRE DE TU HÉROE", new Vector2(0.5f, 1), new Vector2(0, -15), TextAnchor.UpperCenter, UIRoot.Gold);
            var field = UIRoot.Rect(_nameBox, "Field", new Vector2(0.5f, 1), new Vector2(0.5f, 1), new Vector2(0, -28), new Vector2(130, 14));
            field.gameObject.AddComponent<Image>().color = new Color(0.02f, 0.02f, 0.05f, 0.85f);
            _nameText = UIRoot.Label(field, "", new Vector2(0.5f, 0.5f), new Vector2(0, -2), TextAnchor.MiddleCenter, Ink);
            _nameText.rectTransform.sizeDelta = new Vector2(126, 12);
            _nameBox.gameObject.SetActive(false);
            Select(0);
            Layout(true);
        }

        void OnEnable() { Current = this; _openedAt = Time.unscaledTime; _naming = false; if (_nameBox) _nameBox.gameObject.SetActive(false); Refresh(); }
        void OnDisable() { if (Current == this) Current = null; }

        public void Select(int i)
        {
            int n = KnightClass.All.Length;
            i = (i % n + n) % n;
            if (i != Index && isActiveAndEnabled) Sfx.Play("select", 0.6f);
            Index = i;
            Refresh();
        }

        void Refresh()
        {
            if (_cards.Count == 0) return;
            for (int c = 0; c < _cards.Count; c++)
            {
                _cards[c].color = c == Index ? Color.white : new Color(1f, 1f, 1f, 0.5f);
                var st = _cardRoots[c].Find("Stage");
                if (st) st.GetComponent<Image>().color = c == Index ? StageLit : Stage;
            }
            var k = KnightClass.All[Index];
            if (_desc) { _desc.text = k.name + ": " + k.description; _perk.text = k.perk; }
            if (_hint) _hint.text = _naming ? "ESCRIBE · RETROCESO BORRAR · ENTER EMPEZAR · ESC VOLVER"
                                            : $"A/D ELEGIR ({Index + 1}/{KnightClass.All.Length}) · ENTER CONTINUAR · ESC VOLVER";
        }

        /// <summary>Cards slide so the chosen one is in the middle (wrapping around the ten classes).</summary>
        void Layout(bool snap)
        {
            int n = KnightClass.All.Length;
            float k = snap ? 1f : 1f - Mathf.Exp(-14f * Time.unscaledDeltaTime);
            _scroll = Mathf.Lerp(_scroll, Index, k);
            if (Mathf.Abs(_scroll - Index) > n / 2f) _scroll = Index;      // wrapped: jump instead of sliding across
            for (int c = 0; c < _cardRoots.Count; c++)
            {
                float off = c - _scroll;
                if (off > n / 2f) off -= n; else if (off < -n / 2f) off += n;
                var rt = _cardRoots[c];
                rt.gameObject.SetActive(Mathf.Abs(off) < 2.8f);
                rt.anchoredPosition = new Vector2(off * Step, c == Index ? -2 : -6);
            }
        }

        public void Choose()
        {
            if (Time.unscaledTime - _openedAt < 0.2f) return;
            Sfx.Play("confirm", 0.7f);
            _naming = true; _name = ""; _openedAt = Time.unscaledTime;
            var k = KnightClass.All[Index];
            _nameClass.text = k.name + " · " + k.GenderName;
            _nameBox.gameObject.SetActive(true);
            Refresh();
        }

        void Start_()
        {
            Sfx.Play("confirm", 0.7f);
            string id = KnightClass.All[Index].id;
            if (onChosenNamed != null) onChosenNamed(id, _name.Trim());
            else onChosen?.Invoke(id);
        }

        void Update()
        {
            _t += Time.unscaledDeltaTime;
            Layout(false);
            var a = GameAssets.I;
            for (int c = 0; c < _previews.Count; c++)
            {
                if (!_cardRoots[c].gameObject.activeSelf) continue;
                Sprite[] f = null;
                if (a != null && a.classWalk != null && c < a.classWalk.Length && c == Index) f = a.classWalk[c]?.frames;
                if ((f == null || f.Length == 0) && a != null) f = a.ClassIdle(KnightClass.All[c].id);
                if (f != null && f.Length > 0) { _previews[c].sprite = f[(int)(_t * 8) % f.Length]; _previews[c].color = Color.white; }
            }
            if (_naming) { NameInput(); return; }
            if (GameInput.Left) Select(Index - 1);
            else if (GameInput.Right) Select(Index + 1);
            else if (GameInput.Confirm) Choose();
            else if (GameInput.Pause && Time.unscaledTime - _openedAt > 0.2f) onBack?.Invoke();
        }

        void NameInput()
        {
            bool blink = (_t % 0.8f) < 0.45f;
            if (Time.unscaledTime - _openedAt > 0.15f)
            {
                foreach (char ch in Input.inputString)
                {
                    if (ch == '\b') { if (_name.Length > 0) { _name = _name.Substring(0, _name.Length - 1); Sfx.Play("select", 0.4f); } }
                    else if (ch == '\n' || ch == '\r') { Start_(); return; }
                    else if (_name.Length < MaxName && (char.IsLetterOrDigit(ch) || ch == ' ' || ch == '-' || ch == '\''))
                    { _name += char.ToUpperInvariant(ch); Sfx.Play("select", 0.35f); }
                }
                if (Input.GetKeyDown(KeyCode.Escape)) { _naming = false; _nameBox.gameObject.SetActive(false); _openedAt = Time.unscaledTime; Refresh(); return; }
            }
            string shown = _name.Length > 0 ? UIRoot.Pretty(_name) : "";
            _nameText.text = shown + (blink ? "_" : " ");
            if (_name.Length == 0 && !blink) _nameText.text = UIRoot.Pretty(KnightClass.All[Index].shortName.ToLowerInvariant());
        }
    }
}
