using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace WoodsGame
{
    /// <summary>All in-game UI on one 320x180 pixel canvas, created on demand and kept across scenes.</summary>
    public class UIRoot : MonoBehaviour
    {
        static UIRoot _i;
        public static readonly Color Gold = new Color32(0xff, 0xfc, 0x40, 0xff);
        public static readonly Color Cream = new Color32(0xf4, 0xed, 0xea, 0xff);
        public static readonly Color Red = new Color32(0xed, 0x0d, 0x0d, 0xff);

        RectTransform _root, _hud, _popups, _bossBar, _bossFill, _dialog, _pause, _over, _victory, _controls;
        Text _toast, _title, _subtitle, _dialogText, _bossName, _victoryStats;
        Image _fade;
        float _toastUntil, _titleUntil;
        Hud _hudView;
        readonly List<(Text t, Vector2 world, float born)> _live = new List<(Text, Vector2, float)>();
        readonly Stack<Text> _pool = new Stack<Text>();
        EnemyController _boss;
        MenuList _pauseMenu, _overMenu, _victoryMenu;
        VolumeOptions _pauseVol;

        public static bool ControlsOpen => _i != null && _i._controls != null && _i._controls.gameObject.activeSelf;
        public static bool DialogOpen => _i != null && _i._dialog != null && _i._dialog.gameObject.activeSelf;

        static UIRoot I
        {
            get
            {
                if (_i) return _i;
                var go = new GameObject("UIRoot");
                DontDestroyOnLoad(go);
                _i = go.AddComponent<UIRoot>();
                _i.Build();
                return _i;
            }
        }

        // ================================================================ build
        void Build()
        {
            _root = CreateCanvas(transform, 100);
            if (FindAnyObjectByType<EventSystem>() == null)
            {
                var es = new GameObject("EventSystem", typeof(EventSystem), typeof(StandaloneInputModule));
                DontDestroyOnLoad(es);
            }
            var a = GameAssets.I;

            // HUD -------------------------------------------------------
            _hud = Rect(_root, "HUD", Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            _hudView = Hud.Create(_hud);
            _popups = Rect(_root, "Popups", Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);

            _bossBar = Rect(_hud, "BossBar", new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0, 30), new Vector2(162, 10));
            var frame = Img(_bossBar, null, false); frame.color = new Color(0.04f, 0.03f, 0.07f, 0.75f); frame.rectTransform.sizeDelta = new Vector2(162, 6);
            var bossFillImg = Img(_bossBar, null, false); bossFillImg.color = new Color32(0xe0, 0x3a, 0x4a, 0xff); _bossFill = bossFillImg.rectTransform;
            _bossFill.anchorMin = new Vector2(0, 0.5f); _bossFill.anchorMax = new Vector2(0, 0.5f); _bossFill.pivot = new Vector2(0, 0.5f);
            _bossFill.anchoredPosition = new Vector2(2, 0); _bossFill.sizeDelta = new Vector2(158, 2);
            _bossName = Label(_bossBar, "", new Vector2(0.5f, 1), new Vector2(0, 11), TextAnchor.LowerCenter, Cream);
            _bossBar.gameObject.SetActive(false);

            _toast = Label(_root, "", new Vector2(0.5f, 1), new Vector2(0, -44), TextAnchor.UpperCenter, Gold);
            _title = Label(_root, "", new Vector2(0.5f, 0.5f), new Vector2(0, 24), TextAnchor.MiddleCenter, Cream);
            _subtitle = Label(_root, "", new Vector2(0.5f, 0.5f), new Vector2(0, 10), TextAnchor.MiddleCenter, Gold);

            // dialog ----------------------------------------------------
            _dialog = Rect(_root, "Dialog", new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0, 30), new Vector2(300, 52));
            Img(_dialog, a ? a.dialog : null, true).rectTransform.sizeDelta = new Vector2(300, 52);
            _dialogText = Label(_dialog, "", new Vector2(0, 1), new Vector2(10, -8), TextAnchor.UpperLeft, Cream);
            _dialogText.rectTransform.sizeDelta = new Vector2(280, 36);
            _dialogText.horizontalOverflow = HorizontalWrapMode.Wrap;
            Label(_dialog, "E / ENTER", new Vector2(1, 0), new Vector2(-8, 5), TextAnchor.LowerRight, Gold);
            _dialog.gameObject.SetActive(false);

            // pause / game over / victory ------------------------------------
            _pause = Panel("Pause", "PAUSA", out _pauseMenu, VolumeOptions.PauseLabels(),
                new Action[] { () => GameManager.SetPaused(false), () => _pauseVol.Change(1, +1, true), () => _pauseVol.Change(2, +1, true), () => ShowControls(true), GameManager.ToMenu });
            _pauseVol = _pause.gameObject.AddComponent<VolumeOptions>(); _pauseVol.menu = _pauseMenu;
            _pause.Find("Box").GetComponent<RectTransform>().sizeDelta = new Vector2(170, 104);
            foreach (Transform c in _pause.Find("Box")) c.GetComponent<RectTransform>().sizeDelta = new Vector2(170, 104);
            _over = Panel("GameOver", "HAS CAÍDO", out _overMenu, new[] { "VOLVER AL CAMPAMENTO", "MENÚ PRINCIPAL" },
                new Action[] { () => { _over.gameObject.SetActive(false); GameManager.Respawn(); }, GameManager.ToMenu });
            _victory = Panel("Victory", "¡VICTORIA!", out _victoryMenu, new[] { "SEGUIR EXPLORANDO", "MENÚ PRINCIPAL" }, new Action[] { GameManager.KeepExploring, GameManager.ToMenu });
            _victoryStats = Label(_victory, "", new Vector2(0.5f, 0.5f), new Vector2(0, 14), TextAnchor.MiddleCenter, Cream);
            _controls = ControlsPanel(_root);

            // fade (top-most) -------------------------------------------
            _fade = new GameObject("Fade", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
            _fade.transform.SetParent(_root, false);
            Stretch(_fade.rectTransform);
            _fade.color = new Color(0, 0, 0, 0);
            _fade.raycastTarget = false;

            HideAll();
        }

        RectTransform Panel(string name, string title, out MenuList menu, string[] options, Action[] actions)
        {
            var dim = Rect(_root, name, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            var bg = dim.gameObject.AddComponent<Image>(); bg.color = new Color(0.05f, 0.04f, 0.1f, 0.65f);
            var box = Rect(dim, "Box", new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(150, 96));
            Img(box, GameAssets.I ? GameAssets.I.panel : null, true).rectTransform.sizeDelta = new Vector2(150, 96);
            var t = Label(dim, title, new Vector2(0.5f, 0.5f), new Vector2(0, 34), TextAnchor.MiddleCenter, new Color32(0xf4, 0xed, 0xea, 0xff));
            t.name = "Title";
            menu = MenuList.Create(dim, options, actions, new Vector2(0, -6), new Color32(0xa9, 0xa3, 0xb8, 0xff), new Color32(0xff, 0xc8, 0x5a, 0xff));
            dim.gameObject.SetActive(false);
            return dim;
        }

        RectTransform ControlsPanel(RectTransform parent)
        {
            var dim = Rect(parent, "Controls", Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            dim.gameObject.AddComponent<Image>().color = new Color(0.05f, 0.04f, 0.1f, 0.85f);
            var box = Rect(dim, "Box", new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(240, 156));
            Img(box, GameAssets.I ? GameAssets.I.panel : null, true).rectTransform.sizeDelta = new Vector2(240, 156);
            var lines = new[]
            {
                "CONTROLES", "WASD / FLECHAS   MOVER · SHIFT CORRER", "J / CLIC        ESPADA (X2 COMBO)", "K / CLIC DER.   GOLPE FUERTE",
                "CTRL / U        BLOQUEAR CON EL ESCUDO", "F               PARRY (JUSTO A TIEMPO)", "ESPACIO         RODAR / SALTO ATRÁS",
                "L               ARCO", "Q / R           USAR OBJETO / CAMBIARLO", "E               USAR / HABLAR / RECOGER",
                "V               INVOCAR (TRAS LA MALDICIÓN)", "I · C · M · TAB  BOLSA · FICHA · MAPA · DIARIO", "ENTER PARA VOLVER"
            };
            for (int i = 0; i < lines.Length; i++)
                Label(box, lines[i], new Vector2(0.5f, 1), new Vector2(0, -8 - i * 11), TextAnchor.UpperCenter,
                    i == 0 ? (Color)new Color32(0xf4, 0xed, 0xea, 0xff) : (Color)new Color32(0xa9, 0xa3, 0xb8, 0xff));
            dim.gameObject.AddComponent<CloseOnConfirm>();
            dim.gameObject.SetActive(false);
            return dim;
        }

        // ================================================================ update
        void Update()
        {
            var s = GameManager.State;
            if (_hud.gameObject.activeSelf)
            {
                _hudView.Refresh();
                // safety net: never leave the bar of a boss that is gone, frozen or far away
                var pl = PlayerController.Current;
                if (_bossBar.gameObject.activeSelf && (_boss == null || !_boss.isActiveAndEnabled ||
                    (pl != null && Vector2.Distance(pl.transform.position, _boss.transform.position) > _boss.aggroRange * 3.5f)))
                    _bossBar.gameObject.SetActive(false);
                if (_boss != null && _bossBar.gameObject.activeSelf)
                {
                    float f = Mathf.Clamp01(_boss.health.hp / (float)_boss.health.maxHP);
                    _bossFill.sizeDelta = new Vector2(Mathf.Round(158 * f), 2);
                    _bossName.color = _boss.Enraged ? Red : Cream;
                }
            }
            UpdatePopups();
            UpdateSays();
            if (_toast.text.Length > 0 && Time.unscaledTime > _toastUntil) _toast.text = "";
            if (_title.text.Length > 0 && Time.unscaledTime > _titleUntil) { _title.text = ""; _subtitle.text = ""; }
            bool panel = WorldUI.PanelOpen;
            _title.enabled = _subtitle.enabled = !panel;
            if (_popups.gameObject.activeSelf == panel) _popups.gameObject.SetActive(!panel);
            if (_bossBar.gameObject.activeSelf) _bossBar.localScale = panel ? Vector3.zero : Vector3.one;
            if (DialogOpen && (GameInput.Confirm || GameInput.Interact) && Time.unscaledTime > _dialogOpenedAt + 0.15f)
                _dialog.gameObject.SetActive(false);
        }

        float _dialogOpenedAt;

        // ================================================================ floating numbers
        /// <summary>Damage numbers / BLOQUEO / ESQUIVA rising from a world position for 0.7 s.</summary>
        public static void Popup(Vector2 world, string text, Color color)
        {
            if (_i == null || !_i._hud.gameObject.activeSelf) return;
            var ui = _i;
            var t = ui._pool.Count > 0 ? ui._pool.Pop() : Label(ui._popups, "", Vector2.zero, Vector2.zero, TextAnchor.MiddleCenter, color);
            t.gameObject.SetActive(true);
            t.text = text; t.color = color;
            t.rectTransform.sizeDelta = new Vector2(60, 12);
            ui._live.Add((t, world + new Vector2(UnityEngine.Random.Range(-0.15f, 0.15f), 0), Time.time));
            ui.PlacePopup(t, world, 0);
        }

        void UpdatePopups()
        {
            for (int i = _live.Count - 1; i >= 0; i--)
            {
                var (t, w, born) = _live[i];
                float age = Time.time - born;
                if (age > 0.7f || t == null) { if (t) { t.gameObject.SetActive(false); _pool.Push(t); } _live.RemoveAt(i); continue; }
                PlacePopup(t, w, age);
                var c = t.color; c.a = age < 0.45f ? 1f : 1f - (age - 0.45f) / 0.25f; t.color = c;
            }
        }

        void PlacePopup(Text t, Vector2 world, float age)
        {
            var cam = Camera.main;
            if (cam == null) return;
            Vector3 vp = cam.WorldToViewportPoint(world + Vector2.up * (age * 1.2f));
            var size = _root.rect.size;
            t.rectTransform.anchoredPosition = new Vector2(Mathf.Round(vp.x * size.x), Mathf.Round(vp.y * size.y));
        }

        // ================================================================ API
        public static void ShowHUD(bool on) { I._hud.gameObject.SetActive(on); }

        public static void Toast(string msg, float seconds = 1.8f)
        {
            I._toast.text = Pretty(msg); I._toast.color = Gold;
            I._toastUntil = Time.unscaledTime + seconds;
        }

        public static void TitleCard(string title, string subtitle)
        {
            I._title.text = Pretty(title ?? "");
            I._subtitle.text = Pretty(subtitle ?? "");
            I._titleUntil = Time.unscaledTime + 2.6f;
        }

        public static void ShowDialog(string text)
        {
            I._dialogText.text = Pretty(text);
            I._dialog.gameObject.SetActive(true);
            I._dialogOpenedAt = Time.unscaledTime;
        }

        public static void ShowBoss(EnemyController boss)
        {
            if (boss.isBoss) { BossHud.Show(boss, null); return; }     // real bosses get the ornate bar at the top (BossHud)
            I._boss = boss;
            I._bossName.text = Pretty(boss.displayName);
            I._bossBar.gameObject.SetActive(true);
        }

        /// <summary>"New item" notice with the rarity colour.</summary>
        public static void ItemToast(ItemDef it)
        {
            I._toast.text = $"Nuevo: {it.name}  ({it.RarityName})  · I inventario";
            I._toast.color = it.RarityColor;
            I._toastUntil = Time.unscaledTime + 3f;
        }

        /// <summary>"+2 Hierba curativa" (and where it went when the bag is full).</summary>
        public static void MatToast(MatDef m, int n, int stored)
        {
            if (m == null) return;
            I._toast.text = stored >= n ? $"+{n} {m.name} → almacén (bolsa llena)" : stored > 0 ? $"+{n} {m.name} ({stored} al almacén)" : $"+{n} {m.name}";
            I._toast.color = new Color32(0xc8, 0xf0, 0xa0, 0xff);
            I._toastUntil = Time.unscaledTime + 1.8f;
        }

        readonly List<(Text t, Transform who, float until)> _says = new List<(Text, Transform, float)>();

        /// <summary>A short line said by a townsperson, floating over their head for a few seconds.</summary>
        public static void Say(Transform who, string text, float seconds = 2.4f)
        {
            if (_i == null || who == null || !_i._hud.gameObject.activeSelf) return;
            var ui = _i;
            for (int i = ui._says.Count - 1; i >= 0; i--) if (ui._says[i].who == who) { if (ui._says[i].t) Destroy(ui._says[i].t.gameObject); ui._says.RemoveAt(i); }
            var t = Label(ui._popups, text, Vector2.zero, Vector2.zero, TextAnchor.LowerCenter, Cream);
            t.rectTransform.sizeDelta = new Vector2(160, 12);
            ui._says.Add((t, who, Time.time + seconds));
        }

        void UpdateSays()
        {
            var cam = Camera.main;
            for (int i = _says.Count - 1; i >= 0; i--)
            {
                var (t, who, until) = _says[i];
                if (t == null || who == null || Time.time > until || cam == null) { if (t) Destroy(t.gameObject); _says.RemoveAt(i); continue; }
                Vector3 vp = cam.WorldToViewportPoint((Vector2)who.position + Vector2.up * 1.55f);
                var size = _root.rect.size;
                t.rectTransform.anchoredPosition = new Vector2(Mathf.Round(vp.x * size.x), Mathf.Round(vp.y * size.y));
                var c = t.color; c.a = Mathf.Clamp01((until - Time.time) * 3f); t.color = c;
            }
        }

        // ================================================================ text style
        static readonly HashSet<string> KeepCaps = new HashSet<string> { "XP", "ESC", "TAB", "HP", "II", "III", "IV", "PS" };
        static readonly string[] Proper =
        {
            "Valle Central", "Bosque del Oeste", "Lago Espejo", "Pantano Carmesí", "Picos Nevados", "Arenas Rojas", "Monte Ceniza",
            "Bosque Corrupto", "Ciudadela del Rey", "Costa del Puerto", "Señor Demonio", "Jefe Orco", "Gorgrak", "Coloso de Escarcha", "Madre de Sangre", "Posada del Jabalí",
            "Biblioteca del Sabio", "Cuartel del Rey", "La Espada del Bosque", "Capilla", "Sello",
            "Valtherion", "Eldoria", "Aurelith", "Noxheim", "Valgrimm", "Drakmor", "Torre Prohibida", "Desierto de los Antiguos",
            "Ruinas Eternas", "Rey Olvidado", "Rey Sepultado", "Invocador", "Madre de Sangre", "Coloso de Escarcha", "Eryndor", "Primordiales"
        };

        /// <summary>The game's texts are written in capitals; the minimal UI shows them in sentence case
        /// (keeps key names like J, ESC and XP, and proper names like Monte Ceniza). Mixed-case text is left as is.</summary>
        public static string Pretty(string s)
        {
            if (string.IsNullOrEmpty(s)) return s;
            bool hasLetters = false;
            foreach (char ch in s) { if (char.IsLower(ch)) return s; if (char.IsLetter(ch)) hasLetters = true; }
            if (!hasLetters) return s;
            var sb = new System.Text.StringBuilder(s.Length);
            bool cap = true;
            int i = 0;
            while (i < s.Length)
            {
                char ch = s[i];
                if (char.IsLetter(ch))
                {
                    int j = i; while (j < s.Length && char.IsLetter(s[j])) j++;
                    string w = s.Substring(i, j - i);
                    bool isolated = w.Length == 1 && (i == 0 || !char.IsLetter(s[i - 1])) && (j >= s.Length || s[j] == ' ' || s[j] == ':' || s[j] == '/') && w != "Y" && w != "A" && w != "O" && w != "E";
                    if (KeepCaps.Contains(w) || isolated) sb.Append(w);
                    else if (cap) sb.Append(w[0]).Append(w.Substring(1).ToLowerInvariant());
                    else sb.Append(w.ToLowerInvariant());
                    cap = false; i = j; continue;
                }
                sb.Append(ch);
                if (ch == '.' || ch == '!' || ch == '?' || ch == '\n' || ch == '¡' || ch == '¿') cap = true;
                i++;
            }
            string r = sb.ToString();
            foreach (var p in Proper)
            {
                int k = r.IndexOf(p, StringComparison.OrdinalIgnoreCase);
                while (k >= 0) { r = r.Substring(0, k) + p + r.Substring(k + p.Length); k = r.IndexOf(p, k + p.Length, StringComparison.OrdinalIgnoreCase); }
            }
            return r;
        }

        public static void HideBoss() { if (_i) _i._bossBar.gameObject.SetActive(false); if (BossArena.Fighting == null) BossHud.HideBar(); }

        public static void ShowPause(bool on)
        {
            if (_i == null && !on) return;
            I._pause.gameObject.SetActive(on);
            if (on) I._pauseMenu.Select(0);
            else I._controls.gameObject.SetActive(false);
        }

        public static void ShowControls(bool on) { MenuList.Overlay = I._controls.gameObject; I._controls.gameObject.SetActive(on); }

        public static void ShowGameOver()
        {
            I._over.gameObject.SetActive(true);
            I._overMenu.Select(0);
        }

        public static void ShowVictory()
        {
            var s = GameManager.State;
            I._victoryStats.text = $"EL BOSQUE ESTÁ A SALVO.  NIVEL {s.level}  ENEMIGOS {s.kills}";
            I._victory.gameObject.SetActive(true);
            I._victoryMenu.Select(0);
        }

        public static void HideVictory() { if (_i) _i._victory.gameObject.SetActive(false); }

        public static void HideAll()
        {
            if (_i == null) return;
            _i._hud.gameObject.SetActive(false);
            _i._bossBar.gameObject.SetActive(false);
            _i._dialog.gameObject.SetActive(false);
            _i._pause.gameObject.SetActive(false);
            _i._over.gameObject.SetActive(false);
            _i._victory.gameObject.SetActive(false);
            _i._controls.gameObject.SetActive(false);
            _i._toast.text = ""; _i._title.text = ""; _i._subtitle.text = "";
            foreach (var (t, _, _) in _i._live) if (t) { t.gameObject.SetActive(false); _i._pool.Push(t); }
            _i._live.Clear();
            _i._boss = null;
        }

        public static IEnumerator Fade(float to, float seconds)
        {
            var img = I._fade;
            float from = img.color.a, t = 0;
            while (t < seconds)
            {
                t += Time.unscaledDeltaTime;
                img.color = new Color(0, 0, 0, Mathf.Lerp(from, to, t / seconds));
                yield return null;
            }
            img.color = new Color(0, 0, 0, to);
        }

        // ================================================================ helpers (also used by the main menu)
        public static RectTransform CreateCanvas(Transform parent, int order)
        {
            var go = new GameObject("Canvas", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            go.transform.SetParent(parent, false);
            var c = go.GetComponent<Canvas>();
            c.renderMode = RenderMode.ScreenSpaceOverlay;
            c.sortingOrder = order;
            c.pixelPerfect = true;
            var sc = go.GetComponent<CanvasScaler>();
            sc.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            sc.referenceResolution = new Vector2(320, 180);
            sc.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            sc.matchWidthOrHeight = 1f;
            sc.referencePixelsPerUnit = 16;
            return (RectTransform)go.transform;
        }

        public static RectTransform Rect(Transform parent, string name, Vector2 aMin, Vector2 aMax, Vector2 pos, Vector2 size)
        {
            var rt = new GameObject(name, typeof(RectTransform)).GetComponent<RectTransform>();
            rt.SetParent(parent, false);
            rt.anchorMin = aMin; rt.anchorMax = aMax;
            rt.pivot = new Vector2(aMin == aMax ? aMin.x : 0.5f, aMin == aMax ? aMin.y : 0.5f);
            rt.anchoredPosition = pos; rt.sizeDelta = size;
            return rt;
        }

        public static void Stretch(RectTransform rt)
        {
            rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = rt.offsetMax = Vector2.zero;
        }

        public static Image Img(Transform parent, Sprite s, bool sliced)
        {
            var im = new GameObject("Image", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
            im.transform.SetParent(parent, false);
            im.sprite = s;
            im.type = sliced && s != null && s.border != Vector4.zero ? Image.Type.Sliced : Image.Type.Simple;
            im.raycastTarget = false;
            if (s == null) im.color = new Color(0, 0, 0, 0);
            return im;
        }

        public static Text Label(Transform parent, string text, Vector2 anchor, Vector2 pos, TextAnchor align, Color color)
        {
            var t = new GameObject("Text", typeof(RectTransform), typeof(Text)).GetComponent<Text>();
            t.transform.SetParent(parent, false);
            var rt = t.rectTransform;
            rt.anchorMin = rt.anchorMax = anchor;
            rt.pivot = new Vector2(align == TextAnchor.UpperLeft || align == TextAnchor.LowerLeft || align == TextAnchor.MiddleLeft ? 0 :
                                   align == TextAnchor.UpperRight || align == TextAnchor.LowerRight || align == TextAnchor.MiddleRight ? 1 : 0.5f, anchor.y);
            rt.anchoredPosition = pos;
            rt.sizeDelta = new Vector2(300, 12);
            var a = GameAssets.I;
            if (a && a.font) { t.font = a.font; t.fontSize = a.font.fontSize; }
            else t.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            t.text = Pretty(text ?? "");
            if (color.r + color.g + color.b > 1.6f) { var sh = t.gameObject.AddComponent<Shadow>(); sh.effectColor = new Color(0, 0, 0, 0.75f); sh.effectDistance = new Vector2(1, -1); }
            t.alignment = align;
            t.color = color;
            t.horizontalOverflow = HorizontalWrapMode.Overflow;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            t.raycastTarget = false;
            t.supportRichText = false;
            return t;
        }
    }
}
