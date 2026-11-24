using System;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace WoodsGame
{
    /// <summary>ERYNDOR title screen: the illustration (with its own menu texts) shown full screen without distortion,
    /// and invisible buttons laid exactly over the five options printed in it. Hover / W-S highlight an option with a
    /// soft glow and a retro blip; click / Enter runs it. Nothing is drawn over the texts except that discreet glow.</summary>
    public class TitleScreen : MonoBehaviour
    {
        // option boxes measured on the 1672x941 image (pixels from the top-left), one per printed option
        public const float ImgW = 1672, ImgH = 941;
        static readonly float[] RowCenterY = { 527.5f, 580f, 627.5f, 675.5f, 722.5f };
        const float RowX0 = 672, RowX1 = 1000, RowH = 46;
        public static readonly string[] Names = { "Continuar", "Nueva Partida", "Opciones", "Créditos", "Salir" };

        Action[] _actions;
        bool[] _enabled;
        readonly Image[] _glow = new Image[5];
        readonly Image[] _shade = new Image[5];
        readonly Button[] _buttons = new Button[5];
        int _index = -1;
        float _t, _openedAt;
        // the selection cursor: a purple frame with a soft fill and a white arrow, sliding to the chosen option
        RectTransform _cursor, _arrow;
        Vector2 _curMin, _curMax;
        static readonly Color CursorFill = new Color(0.45f, 0.1f, 0.95f, 0.28f), CursorEdge = new Color(0.62f, 0.2f, 1f, 0.95f);

        /// <summary>Set while a dialog (options, credits, exit) is on top: the title ignores input.</summary>
        public Func<bool> blocked;

        public int Index => _index;
        public bool IsEnabled(int i) => _enabled[i];

        /// <summary>Builds the screen. actions: Continuar, Nueva Partida, Opciones, Créditos, Salir.</summary>
        public static TitleScreen Create(Transform parent, Sprite art, Action[] actions, bool canContinue)
        {
            var go = new GameObject("TitleScreen", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            go.transform.SetParent(parent, false);
            var canvas = go.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay; canvas.sortingOrder = 5;
            var sc = go.GetComponent<CanvasScaler>();
            sc.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            sc.referenceResolution = new Vector2(ImgW, ImgH);
            sc.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight; sc.matchWidthOrHeight = 0.5f;

            // black letterbox behind, then the picture kept at its own aspect ratio
            var back = new GameObject("Letterbox", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
            back.transform.SetParent(go.transform, false); UIRoot.Stretch(back.rectTransform); back.color = Color.black; back.raycastTarget = false;
            var frame = new GameObject("Picture", typeof(RectTransform), typeof(AspectRatioFitter)).GetComponent<RectTransform>();
            frame.SetParent(go.transform, false); UIRoot.Stretch(frame);
            var fit = frame.GetComponent<AspectRatioFitter>(); fit.aspectMode = AspectRatioFitter.AspectMode.FitInParent; fit.aspectRatio = ImgW / ImgH;
            var bg = new GameObject("Background", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
            bg.transform.SetParent(frame, false); UIRoot.Stretch(bg.rectTransform);
            bg.sprite = art; bg.preserveAspect = true; bg.raycastTarget = false; bg.color = Color.white;

            var t = go.AddComponent<TitleScreen>();
            t._actions = actions;
            t._enabled = new[] { canContinue, true, true, true, true };
            for (int i = 0; i < 5; i++) t.MakeHitbox(frame, i);
            t.MakeCursor(frame);
            t.Select(canContinue ? 0 : 1, false);
            t.Row(t._index, out t._curMin, out t._curMax);
            t._openedAt = Time.unscaledTime;
            return t;
        }

        /// <summary>Anchors of a printed option row (fractions of the picture).</summary>
        void Row(int i, out Vector2 min, out Vector2 max)
        {
            i = Mathf.Clamp(i, 0, 4);
            float cy = RowCenterY[i];
            min = new Vector2(RowX0 / ImgW, 1f - (cy + RowH / 2) / ImgH);
            max = new Vector2(RowX1 / ImgW, 1f - (cy - RowH / 2) / ImgH);
        }

        static Sprite _tri;
        static Sprite Triangle()
        {
            if (_tri) return _tri;
            const int W = 9, H = 13;
            var tex = new Texture2D(W, H, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point };
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    float half = (H - 1) / 2f, d = Mathf.Abs(y - half);
                    bool inside = x <= (W - 1) * (1f - d / half) + 0.01f;
                    bool edge = inside && (x == 0 || x > (W - 1) * (1f - (d + 1) / half));
                    tex.SetPixel(x, y, !inside ? Color.clear : edge ? new Color(0.85f, 0.8f, 0.95f) : Color.white);
                }
            tex.Apply();
            return _tri = Sprite.Create(tex, new Rect(0, 0, W, H), new Vector2(0.5f, 0.5f), 1);
        }

        void MakeCursor(RectTransform frame)
        {
            _cursor = new GameObject("Cursor", typeof(RectTransform)).GetComponent<RectTransform>();
            _cursor.SetParent(frame, false);
            _cursor.offsetMin = _cursor.offsetMax = Vector2.zero;
            var fill = new GameObject("Fill", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
            fill.transform.SetParent(_cursor, false); UIRoot.Stretch(fill.rectTransform); fill.color = CursorFill; fill.raycastTarget = false;
            void Edge(Vector2 aMin, Vector2 aMax, Vector2 size)
            {
                var e = new GameObject("Edge", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
                e.transform.SetParent(_cursor, false); e.color = CursorEdge; e.raycastTarget = false;
                var r = e.rectTransform; r.anchorMin = aMin; r.anchorMax = aMax; r.sizeDelta = size; r.anchoredPosition = Vector2.zero;
            }
            Edge(new Vector2(0, 1), new Vector2(1, 1), new Vector2(0, 4));     // top
            Edge(new Vector2(0, 0), new Vector2(1, 0), new Vector2(0, 4));     // bottom
            Edge(new Vector2(0, 0), new Vector2(0, 1), new Vector2(4, 0));     // left
            Edge(new Vector2(1, 0), new Vector2(1, 1), new Vector2(4, 0));     // right
            var arrow = new GameObject("Arrow", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
            arrow.transform.SetParent(_cursor, false); arrow.sprite = Triangle(); arrow.raycastTarget = false;
            _arrow = arrow.rectTransform; _arrow.anchorMin = _arrow.anchorMax = new Vector2(0, 0.5f);
            _arrow.sizeDelta = new Vector2(27, 39); _arrow.anchoredPosition = new Vector2(30, 0);
        }

        void MakeHitbox(RectTransform frame, int i)
        {
            var rt = new GameObject("Option_" + Names[i].Replace(" ", ""), typeof(RectTransform)).GetComponent<RectTransform>();
            rt.SetParent(frame, false);
            float cy = RowCenterY[i];
            rt.anchorMin = new Vector2(RowX0 / ImgW, 1f - (cy + RowH / 2) / ImgH);
            rt.anchorMax = new Vector2(RowX1 / ImgW, 1f - (cy - RowH / 2) / ImgH);
            rt.offsetMin = rt.offsetMax = Vector2.zero;
            // invisible hit area (alpha 0 but still catches the mouse)
            var hit = rt.gameObject.AddComponent<Image>(); hit.color = new Color(1, 1, 1, 0); hit.raycastTarget = true;
            var b = rt.gameObject.AddComponent<Button>(); b.transition = Selectable.Transition.None; b.targetGraphic = hit;
            int k = i;
            b.onClick.AddListener(() => { Select(k, false); Confirm(); });
            var trig = rt.gameObject.AddComponent<EventTrigger>();
            var enter = new EventTrigger.Entry { eventID = EventTriggerType.PointerEnter };
            enter.callback.AddListener(_ => { if (!Blocked()) Select(k, true); });
            trig.triggers.Add(enter);
            b.interactable = _enabled[i];
            _buttons[i] = b;
            // discreet selection: a soft light over the printed row (additive feel through low alpha)
            var glow = new GameObject("Glow", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
            glow.transform.SetParent(rt, false); UIRoot.Stretch(glow.rectTransform);
            glow.color = new Color(0.85f, 0.7f, 1f, 0f); glow.raycastTarget = false;
            _glow[i] = glow;
            // disabled option (no save to continue): dimmed
            var shade = new GameObject("Disabled", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
            shade.transform.SetParent(rt, false); UIRoot.Stretch(shade.rectTransform);
            shade.color = new Color(0.03f, 0.02f, 0.08f, _enabled[i] ? 0f : 0.62f); shade.raycastTarget = false;
            _shade[i] = shade;
        }

        float _freeAt;

        /// <summary>True while a dialog is open and for a moment after it closes, so the key that closed it
        /// does not also trigger the highlighted option.</summary>
        bool Blocked()
        {
            if (blocked != null && blocked()) { _freeAt = Time.unscaledTime + 0.2f; return true; }
            return Time.unscaledTime < _freeAt || Time.unscaledTime - _openedAt < 0.2f;
        }

        public void Select(int i, bool sound)
        {
            if (i < 0 || i >= 5 || !_enabled[i]) return;
            if (i != _index && sound) Sfx.Play("select", 0.55f);
            _index = i;
        }

        public void Confirm()
        {
            if (Blocked() || _index < 0 || !_enabled[_index]) return;
            Sfx.Play("confirm", 0.7f);
            _actions[_index]?.Invoke();
        }

        void Move(int dir)
        {
            int i = _index;
            for (int n = 0; n < 5; n++) { i = (i + dir + 5) % 5; if (_enabled[i]) break; }
            Select(i, true);
        }

        void Update()
        {
            _t += Time.unscaledDeltaTime;
            for (int i = 0; i < 5; i++) _glow[i].color = new Color(0.85f, 0.7f, 1f, 0f);
            if (_cursor != null && _index >= 0)
            {
                // the cursor glides to the chosen row; the arrow bobs a little
                Row(_index, out var tMin, out var tMax);
                float k = 1f - Mathf.Exp(-18f * Time.unscaledDeltaTime);
                _curMin = Vector2.Lerp(_curMin, tMin, k); _curMax = Vector2.Lerp(_curMax, tMax, k);
                _cursor.anchorMin = _curMin; _cursor.anchorMax = _curMax;
                _cursor.offsetMin = _cursor.offsetMax = Vector2.zero;
                _arrow.anchoredPosition = new Vector2(30 + 5f * Mathf.Sin(_t * 6f), 0);
            }
            if (Blocked()) return;
            if (GameInput.Up) Move(-1);
            else if (GameInput.Down) Move(1);
            else if (GameInput.Confirm) Confirm();
        }
    }
}
