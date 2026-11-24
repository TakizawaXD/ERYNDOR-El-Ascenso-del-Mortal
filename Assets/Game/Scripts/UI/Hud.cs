using UnityEngine;
using UnityEngine.UI;

namespace WoodsGame
{
    /// <summary>Minimal RPG HUD on the 320x180 canvas. No frames: thin bars and shadowed text that float over the world.
    ///  top-left   class · level, life bar, stamina bar, experience bar (+ unspent points), coins / arrows / raised allies
    ///  top-right  minimap (WorldUI) and below it the clock (sun/moon, day, hour) and threat level
    ///  bottom     four small action slots: weapon (with its oil), heavy, bow (special arrows) and the quick item (Q, R to change)</summary>
    public class Hud : MonoBehaviour
    {
        RectTransform _status, _clock, _bar;
        Image _hpFill, _hpGhost, _xpFill, _phaseIcon, _weaponIcon, _heavyIcon, _bowIcon, _stFill, _quickIcon, _potIcon;
        Text _name, _hp, _points, _coins, _arrows, _potions, _time, _threat, _bowCount, _potCount, _help;
        float _blink, _ghost = 1f, _shownAt = -1f;
        static readonly Color StCol = new Color32(0x7c, 0xd0, 0x5a, 0xff), StLow = new Color32(0xd8, 0xa8, 0x3a, 0xff);

        static readonly Color HpCol = new Color32(0xe0, 0x3a, 0x4a, 0xff), XpCol = new Color32(0xff, 0xc8, 0x5a, 0xff);
        static readonly Color Track = new Color(0.04f, 0.03f, 0.07f, 0.65f), Dim = new Color(1f, 1f, 1f, 0.6f);
        static readonly Color NightCol = new Color32(0xa9, 0xc8, 0xff, 0xff);
        const float BarW = 70;

        public static Hud Create(RectTransform parent)
        {
            var go = new GameObject("RpgHud", typeof(RectTransform));
            go.transform.SetParent(parent, false);
            UIRoot.Stretch((RectTransform)go.transform);
            var h = go.AddComponent<Hud>();
            h.Build((RectTransform)go.transform);
            return h;
        }

        void Build(RectTransform root)
        {
            var a = GameAssets.I;
            // ---------------------------------------------------------- status (top-left)
            _status = UIRoot.Rect(root, "Status", new Vector2(0, 1), new Vector2(0, 1), new Vector2(6, -5), new Vector2(110, 40));
            _name = UIRoot.Label(_status, "", new Vector2(0, 1), new Vector2(0, 0), TextAnchor.UpperLeft, UIRoot.Cream);
            _hpGhost = Bar(_status, new Vector2(0, -12), 4, new Color(1f, 0.85f, 0.85f, 0.8f), out var hpTrack);
            _hpFill = Fill(hpTrack, HpCol);
            _hp = UIRoot.Label(_status, "", new Vector2(0, 1), new Vector2(BarW + 4, -9), TextAnchor.UpperLeft, UIRoot.Cream);
            _stFill = Bar(_status, new Vector2(0, -18), 3, StCol, out _);
            _xpFill = Bar(_status, new Vector2(0, -23), 1, XpCol, out _);
            _points = UIRoot.Label(_status, "", new Vector2(0, 1), new Vector2(BarW + 4, -17), TextAnchor.UpperLeft, XpCol);
            var row = UIRoot.Rect(_status, "Counters", new Vector2(0, 1), new Vector2(0, 1), new Vector2(-3, -25), new Vector2(120, 14));
            _coins = Counter(row, a ? a.iconCoin : null, 0);
            _arrows = Counter(row, a ? a.iconArrow : null, 38);
            _potions = Counter(row, a ? a.iconSkull : null, 72);
            _potIcon = row.GetChild(row.childCount - 2).GetComponent<Image>();

            // ---------------------------------------------------------- clock (top-right, under the minimap)
            _clock = UIRoot.Rect(root, "Clock", new Vector2(1, 1), new Vector2(1, 1), new Vector2(-6, -50), new Vector2(70, 22));
            // a soft dark plate behind the clock: readable over snow, trees and sand alike
            var plate = UIRoot.Img(_clock, null, false); plate.color = new Color(0.04f, 0.03f, 0.06f, 0.55f);
            var pr = plate.rectTransform; pr.anchorMin = Vector2.zero; pr.anchorMax = Vector2.one; pr.offsetMin = new Vector2(-3, -1); pr.offsetMax = new Vector2(2, 1);
            plate.raycastTarget = false;
            _phaseIcon = UIRoot.Img(_clock, null, false); _phaseIcon.color = Color.white;
            var ir = _phaseIcon.rectTransform; ir.anchorMin = ir.anchorMax = new Vector2(1, 1); ir.pivot = new Vector2(1, 1);
            ir.sizeDelta = new Vector2(16, 16); ir.anchoredPosition = new Vector2(2, 2);
            _time = UIRoot.Label(_clock, "", new Vector2(1, 1), new Vector2(-16, 0), TextAnchor.UpperRight, UIRoot.Cream);
            _threat = UIRoot.Label(_clock, "", new Vector2(1, 1), new Vector2(-16, -9), TextAnchor.UpperRight, Dim);

            // ---------------------------------------------------------- action bar (bottom centre)
            // quick panel (bottom-left corner): one row per action - key, icon, count beside it (never on top of the icon)
            _bar = UIRoot.Rect(root, "QuickPanel", new Vector2(0, 0), new Vector2(0, 0), new Vector2(5, 5), new Vector2(50, 40));
            var qplate = UIRoot.Img(_bar, null, false); qplate.color = new Color(0.04f, 0.03f, 0.06f, 0.5f); qplate.raycastTarget = false;
            var qr = qplate.rectTransform; qr.anchorMin = Vector2.zero; qr.anchorMax = Vector2.one; qr.offsetMin = new Vector2(-2, -2); qr.offsetMax = new Vector2(2, 2);
            _weaponIcon = QuickRow(0, "J/K", out _);
            _heavyIcon = UIRoot.Img(_bar, null, false); _heavyIcon.gameObject.SetActive(false);    // the weapon row covers both blows
            _bowIcon = QuickRow(1, "L", out _bowCount);
            _quickIcon = QuickRow(2, "Q/R", out _potCount);
            _help = UIRoot.Label(root, "Ctrl bloquear · F parry · Q usar · R cambiar · I bolsa · C ficha · M mapa · Esc menú", new Vector2(0.5f, 0), new Vector2(0, 25), TextAnchor.LowerCenter, Dim);
        }

        /// <summary>Thin bar: dark track + coloured fill. Returns the fill.</summary>
        Image Bar(RectTransform parent, Vector2 pos, float h, Color fill, out RectTransform track)
        {
            track = UIRoot.Rect(parent, "Track", new Vector2(0, 1), new Vector2(0, 1), pos, new Vector2(BarW, h));
            track.gameObject.AddComponent<Image>().color = Track;
            return Fill(track, fill);
        }

        static Image Fill(RectTransform track, Color c)
        {
            var f = new GameObject("Fill", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
            f.transform.SetParent(track, false);
            var r = f.rectTransform; r.anchorMin = new Vector2(0, 0); r.anchorMax = new Vector2(0, 1); r.pivot = new Vector2(0, 0.5f);
            r.sizeDelta = new Vector2(BarW, 0); r.anchoredPosition = Vector2.zero;
            f.color = c;
            return f;
        }

        Text Counter(RectTransform row, Sprite icon, float x)
        {
            var im = UIRoot.Img(row, icon, false);
            var rt = im.rectTransform;
            rt.anchorMin = rt.anchorMax = new Vector2(0, 1); rt.pivot = new Vector2(0, 1);
            rt.anchoredPosition = new Vector2(x, 0); rt.sizeDelta = new Vector2(16, 16);
            if (icon) im.color = Color.white;
            return UIRoot.Label(row, "0", new Vector2(0, 1), new Vector2(x + 15, -4), TextAnchor.UpperLeft, UIRoot.Cream);
        }

        Image Slot(RectTransform bar, int i, string key)
        {
            var a = GameAssets.I;
            var s = UIRoot.Rect(bar, "Slot" + key, new Vector2(0, 0), new Vector2(0, 0), new Vector2(i * 22, 0), new Vector2(18, 18));
            var bg = UIRoot.Img(s, a ? a.flatSlot : null, true); bg.rectTransform.sizeDelta = new Vector2(18, 18);
            if (!a || !a.flatSlot) bg.color = Track; else bg.color = new Color(1, 1, 1, 0.85f);
            var ic = UIRoot.Img(s, null, false); ic.rectTransform.sizeDelta = new Vector2(16, 16);
            UIRoot.Label(s, key, new Vector2(0, 1), new Vector2(1, 6), TextAnchor.UpperLeft, Dim);
            return ic;
        }

        Text SlotCount(int i) => UIRoot.Label(_bar.GetChild(i), "", new Vector2(1, 0), new Vector2(1, -1), TextAnchor.LowerRight, UIRoot.Cream);

        /// <summary>A row of the quick panel: dim key name, 12 px icon, count text to its right. Row 0 is the top one.</summary>
        Image QuickRow(int i, string key, out Text count)
        {
            var row = UIRoot.Rect(_bar, "Row" + key, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, -i * 13), new Vector2(50, 13));
            UIRoot.Label(row, key, new Vector2(0, 1), new Vector2(0, -2), TextAnchor.UpperLeft, Dim);
            var ic = UIRoot.Img(row, null, false);
            var rt = ic.rectTransform; rt.anchorMin = rt.anchorMax = new Vector2(0, 1); rt.pivot = new Vector2(0, 1);
            rt.sizeDelta = new Vector2(12, 12); rt.anchoredPosition = new Vector2(19, 0);
            count = UIRoot.Label(row, "", new Vector2(0, 1), new Vector2(33, -2), TextAnchor.UpperLeft, UIRoot.Cream);
            return ic;
        }

        public void Refresh()
        {
            var s = GameManager.State;
            var a = GameAssets.I;
            bool clear = !WorldUI.PanelOpen;
            _status.gameObject.SetActive(clear); _clock.gameObject.SetActive(clear); _bar.gameObject.SetActive(clear);
            if (_shownAt < 0) _shownAt = Time.unscaledTime;
            float helpA = Mathf.Clamp01(1f - (Time.unscaledTime - _shownAt - 20f) / 3f);
            _help.gameObject.SetActive(clear && helpA > 0);
            _help.color = new Color(1, 1, 1, 0.6f * helpA);
            if (!clear) return;
            _blink += Time.unscaledDeltaTime;

            var p = PlayerController.Current;
            int hp = p ? p.health.hp : s.hp, max = p ? p.health.maxHP : s.maxHP;
            float f = max > 0 ? hp / (float)max : 0;
            _ghost = Mathf.MoveTowards(_ghost, f, Time.unscaledDeltaTime * 0.6f);
            if (_ghost < f) _ghost = f;
            _name.text = string.IsNullOrEmpty(s.heroName) ? $"{s.Class.shortName}  ·  Nv {s.level}" : $"{s.heroName}  ·  {s.Class.shortName}  ·  Nv {s.level}";
            _hp.text = $"{hp}/{max}";
            SetFill(_hpFill, f); SetFill(_hpGhost, _ghost);
            _hpFill.color = f <= 0.25f && (_blink % 0.6f) < 0.3f ? new Color32(0xff, 0x80, 0x80, 0xff) : HpCol;
            SetFill(_xpFill, s.level >= PlayerState.MaxLevel ? 1 : s.xp / (float)s.XpToNext);
            _points.text = s.attrPoints > 0 ? $"+{s.attrPoints} puntos (C)" : "";
            _points.color = new Color(XpCol.r, XpCol.g, XpCol.b, (_blink % 1.2f) < 0.8f ? 1f : 0.5f);

            _coins.text = s.coins.ToString(); _arrows.text = s.arrows.ToString();
            bool cursed = Summoning.Cursed;
            _potions.text = cursed ? $"{Summoning.Count}/{Summoning.Max}" : ""; _potIcon.enabled = cursed;
            // stamina: thin green bar (amber when out of breath)
            float sf = p ? p.Stamina / Mathf.Max(1f, p.MaxStamina) : 1f;
            SetFill(_stFill, sf);
            _stFill.color = p != null && p.Exhausted ? ((_blink % 0.5f) < 0.25f ? StLow : new Color(StLow.r, StLow.g, StLow.b, 0.6f)) : StCol;
            if (a)
            {
                var w = s.Weapon; var b = s.Bow;
                _weaponIcon.sprite = a.ItemIcon(w.icon); _heavyIcon.sprite = a.ItemIcon(w.icon); _bowIcon.sprite = a.ItemIcon(b.icon);
                var oil = s.oilHits > 0 ? (s.oil == "aceite_fuego" ? new Color(1f, 0.6f, 0.35f) : s.oil == "aceite_hielo" ? new Color(0.6f, 0.85f, 1f) : new Color(1f, 0.95f, 0.55f)) : Color.white;
                _weaponIcon.color = s.Broken(s.weapon) ? new Color(1f, 0.45f, 0.45f) : oil;
                _heavyIcon.color = new Color(1f, 0.85f, 0.6f);
                bool special = !string.IsNullOrEmpty(s.ammo) && s.InBag(s.ammo) > 0;
                _bowIcon.color = special ? (s.ammo == "flecha_fuego" ? new Color(1f, 0.7f, 0.4f) : s.ammo == "flecha_veneno" ? new Color(0.6f, 1f, 0.45f) : new Color(0.85f, 0.95f, 1f))
                               : s.arrows > 0 ? Color.white : new Color(1, 1, 1, 0.35f);
                var q = CraftDB.Get(s.quick);
                bool has = q != null && s.InBag(s.quick) > 0;
                _quickIcon.sprite = q != null ? a.MatIcon(q.icon) : null;
                _quickIcon.color = q == null ? Color.clear : has ? Color.white : new Color(1, 1, 1, 0.3f);
                _bowCount.text = special ? s.InBag(s.ammo).ToString() : s.arrows.ToString();
                if (s.Class.UsesMagic) { _bowIcon.sprite = a.ItemIcon(w.icon); _bowIcon.color = new Color(0.75f, 0.85f, 1f); _bowCount.text = "MAGIA"; }
                else if (!s.Class.UsesBow) { _bowIcon.color = new Color(1, 1, 1, 0.15f); _bowCount.text = ""; }
                _potCount.text = has ? s.InBag(s.quick).ToString() : "";
            }

            bool night = DayNight.IsNight;
            _phaseIcon.sprite = a ? a.Icon(night ? 1 : 0) : null;
            _time.text = $"Día {s.day}  {DayNight.TimeText}";
            _time.color = night ? NightCol : UIRoot.Cream;
            _threat.text = Interior.Current != null ? UIRoot.Pretty(Interior.Current.title) : $"Amenaza {s.Threat}";
        }

        static void SetFill(Image fill, float f)
        {
            fill.rectTransform.sizeDelta = new Vector2(Mathf.Round(BarW * Mathf.Clamp01(f)), 0);
        }
    }
}
