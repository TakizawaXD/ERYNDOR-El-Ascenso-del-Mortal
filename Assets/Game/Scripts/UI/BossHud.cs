using UnityEngine;
using UnityEngine.UI;

namespace WoodsGame
{
    /// <summary>Boss fight HUD on its own 320x180 canvas: an ornate life bar with the boss's name at the top centre
    /// (gold diamond caps, crest, delayed "ghost" damage, phase pips) and the mission objective at the top right.</summary>
    public class BossHud : MonoBehaviour
    {
        static BossHud _i;
        RectTransform _root, _bar, _obj;
        RectTransform _fill, _ghost;
        Image _fillImg;
        Text _name, _phase, _objText;
        Image[] _pips = new Image[3];
        EnemyController _boss;
        float _ghostF = 1f, _objDoneAt = -1f;
        const float FillW = 150f;
        static readonly Color HpCol = new Color32(0xd8, 0x2a, 0x3c, 0xff), RageCol = new Color32(0xa0, 0x3c, 0xf0, 0xff);

        public static bool BarVisible => _i != null && _i._bar.gameObject.activeSelf;
        public static bool ObjectiveVisible => _i != null && _i._obj.gameObject.activeSelf;
        public static string ObjectiveText => _i != null ? _i._objText.text : "";
        public static string BossName => _i != null ? _i._name.text : "";
        public static EnemyController Boss => _i != null ? _i._boss : null;

        static BossHud I
        {
            get
            {
                if (_i) return _i;
                var go = new GameObject("BossHud");
                DontDestroyOnLoad(go);
                _i = go.AddComponent<BossHud>();
                _i.Build();
                return _i;
            }
        }

        void Build()
        {
            _root = UIRoot.CreateCanvas(transform, 101);
            var b = BossAssets.I;
            // ---------------------------------------------------- bar (top centre)
            _bar = UIRoot.Rect(_root, "BossBar", new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0, 66), new Vector2(180, 30));   // above the action bar (the top-left holds the player status)
            var crest = UIRoot.Img(_bar, b ? b.barCrest : null, false);
            crest.rectTransform.anchorMin = crest.rectTransform.anchorMax = new Vector2(0.5f, 1); crest.rectTransform.pivot = new Vector2(0.5f, 1);
            crest.rectTransform.sizeDelta = new Vector2(48, 10); crest.rectTransform.anchoredPosition = new Vector2(0, 2);
            _name = UIRoot.Label(_bar, "", new Vector2(0.5f, 1), new Vector2(0, -6), TextAnchor.UpperCenter, UIRoot.Cream);
            var track = UIRoot.Img(_bar, b ? b.barTrack : null, true);
            Place(track.rectTransform, new Vector2(0, -21), new Vector2(158, 10));
            if (!b) track.color = new Color(0.04f, 0.03f, 0.07f, 0.85f);
            var ghost = UIRoot.Img(_bar, b ? b.barFill : null, false); ghost.color = new Color(1f, 0.92f, 0.7f, 0.9f);
            _ghost = ghost.rectTransform; Left(_ghost, new Vector2(-FillW / 2, -21), new Vector2(FillW, 4));
            _fillImg = UIRoot.Img(_bar, b ? b.barFill : null, false); _fillImg.color = HpCol;
            _fill = _fillImg.rectTransform; Left(_fill, new Vector2(-FillW / 2, -21), new Vector2(FillW, 4));
            for (int s = -1; s <= 1; s += 2)
            {
                var cap = UIRoot.Img(_bar, b ? b.barCap : null, false);
                Place(cap.rectTransform, new Vector2(s * 84, -21), new Vector2(14, 18));
                if (s > 0) cap.rectTransform.localScale = new Vector3(-1, 1, 1);
            }
            for (int i = 0; i < 3; i++)
            {
                _pips[i] = UIRoot.Img(_bar, b ? b.objectiveIcon : null, false);
                Place(_pips[i].rectTransform, new Vector2(-10 + i * 10, -31), new Vector2(7, 7));
            }
            _phase = UIRoot.Label(_bar, "", new Vector2(0.5f, 1), new Vector2(0, -36), TextAnchor.UpperCenter, new Color(1, 1, 1, 0.75f));
            _bar.gameObject.SetActive(false);

            // ---------------------------------------------------- objective (top right, under the clock)
            _obj = UIRoot.Rect(_root, "Objective", new Vector2(1, 1), new Vector2(1, 1), new Vector2(-4, -76), new Vector2(112, 16));
            var pan = UIRoot.Img(_obj, b ? b.objectivePanel : null, true);
            UIRoot.Stretch(pan.rectTransform);
            if (!b) pan.color = new Color(0.05f, 0.03f, 0.08f, 0.8f);
            var icon = UIRoot.Img(_obj, b ? b.objectiveIcon : null, false);
            icon.rectTransform.anchorMin = icon.rectTransform.anchorMax = new Vector2(0, 0.5f); icon.rectTransform.pivot = new Vector2(0, 0.5f);
            icon.rectTransform.sizeDelta = new Vector2(9, 9); icon.rectTransform.anchoredPosition = new Vector2(4, 0);
            _objText = UIRoot.Label(_obj, "", new Vector2(0, 0.5f), new Vector2(16, 5), TextAnchor.MiddleLeft, UIRoot.Cream);
            _obj.gameObject.SetActive(false);
        }

        static void Place(RectTransform r, Vector2 pos, Vector2 size)
        {
            r.anchorMin = r.anchorMax = new Vector2(0.5f, 1); r.pivot = new Vector2(0.5f, 0.5f);
            r.anchoredPosition = pos; r.sizeDelta = size;
        }

        static void Left(RectTransform r, Vector2 pos, Vector2 size)
        {
            r.anchorMin = r.anchorMax = new Vector2(0.5f, 1); r.pivot = new Vector2(0, 0.5f);
            r.anchoredPosition = pos; r.sizeDelta = size;
        }

        // ---------------------------------------------------------------- api
        public static void Show(EnemyController boss, string objective)
        {
            var h = I;
            if (h._boss != boss) h._ghostF = 1f;
            h._boss = boss;
            h._name.text = UIRoot.Pretty(boss.displayName);
            h._bar.gameObject.SetActive(true);
            if (!string.IsNullOrEmpty(objective))
            {
                h._objText.text = UIRoot.Pretty(objective);
                h._objText.color = UIRoot.Cream;
                h._obj.sizeDelta = new Vector2(Mathf.Max(80, objective.Length * 5 + 24), 16);
                h._obj.gameObject.SetActive(true);
                h._objDoneAt = -1f;
            }
            Phase(boss.GetComponent<BossBrain>() is BossBrain br ? br.Phase : 1);
        }

        public static void HideBar() { if (_i) { _i._bar.gameObject.SetActive(false); _i._boss = null; } }

        public static void Hide()
        {
            if (!_i) return;
            HideBar();
            if (_i._objDoneAt < 0) _i._obj.gameObject.SetActive(false);
        }

        public static void Completed(string objective)
        {
            var h = I;
            HideBar();
            h._objText.text = UIRoot.Pretty("Completado: " + (string.IsNullOrEmpty(objective) ? "jefe derrotado" : objective));
            h._objText.color = UIRoot.Gold;
            h._obj.gameObject.SetActive(true);
            h._objDoneAt = Time.unscaledTime;
        }

        public static void Phase(int phase)
        {
            if (!_i) return;
            for (int i = 0; i < 3; i++) _i._pips[i].color = i < phase ? Color.white : new Color(1, 1, 1, 0.2f);
            _i._phase.text = phase > 1 ? UIRoot.Pretty("FASE " + phase) : "";
        }

        void Update()
        {
            if (_objDoneAt > 0 && Time.unscaledTime - _objDoneAt > 6f) { _obj.gameObject.SetActive(false); _objDoneAt = -1f; }
            if (!_bar.gameObject.activeSelf) return;
            if (_boss == null || !_boss.isActiveAndEnabled) { HideBar(); return; }
            float f = Mathf.Clamp01(_boss.health.hp / (float)_boss.health.maxHP);
            _fill.sizeDelta = new Vector2(Mathf.Round(FillW * f), 4);
            _ghostF = Mathf.Max(f, Mathf.MoveTowards(_ghostF, f, Time.unscaledDeltaTime * 0.35f));
            _ghost.sizeDelta = new Vector2(Mathf.Round(FillW * _ghostF), 4);
            _fillImg.color = _boss.Enraged ? Color.Lerp(RageCol, HpCol, 0.5f + 0.5f * Mathf.Sin(Time.unscaledTime * 6f)) : HpCol;
            _name.color = _boss.Enraged ? new Color(1f, 0.55f, 0.55f) : UIRoot.Cream;
            bool panel = WorldUI.PanelOpen;
            _bar.localScale = _obj.localScale = panel ? Vector3.zero : Vector3.one;
        }
    }
}
