using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace WoodsGame
{
    /// <summary>Vertical text menu: W/S or arrows + Enter, or mouse hover/click. Works while time is paused.</summary>
    public class MenuList : MonoBehaviour
    {
        readonly List<Text> _items = new List<Text>();
        readonly List<string> _labels = new List<string>();
        Action[] _actions;
        Color _normal, _selected;
        int _index;
        float _enabledAt;

        /// <summary>When this object is active, every MenuList ignores input.</summary>
        public static GameObject Overlay;

        public int Index => _index;
        public int Count => _items.Count;

        /// <summary>Changes the texts in place (keeps the selection and accepts the next key press right away).</summary>
        public void SetLabels(string[] labels)
        {
            for (int i = 0; i < _items.Count && i < labels.Length; i++) _labels[i] = UIRoot.Pretty(labels[i]);
            Select(_index);
        }

        public static MenuList Create(Transform parent, string[] labels, Action[] actions, Vector2 pos, Color normal, Color selected, float spacing = 12f)
        {
            var rt = UIRoot.Rect(parent, "Menu", new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), pos, new Vector2(140, labels.Length * spacing));
            var m = rt.gameObject.AddComponent<MenuList>();
            m._actions = actions; m._normal = normal; m._selected = selected;
            for (int i = 0; i < labels.Length; i++)
            {
                var t = UIRoot.Label(rt, labels[i], new Vector2(0.5f, 1), new Vector2(0, -i * spacing), TextAnchor.UpperCenter, normal);
                t.rectTransform.sizeDelta = new Vector2(140, spacing);
                t.raycastTarget = true;
                int k = i;
                var trig = t.gameObject.AddComponent<EventTrigger>();
                AddEvent(trig, EventTriggerType.PointerEnter, () => m.Select(k));
                AddEvent(trig, EventTriggerType.PointerClick, () => { m.Select(k); m.Confirm(); });
                m._items.Add(t); m._labels.Add(UIRoot.Pretty(labels[i]));
            }
            m.Select(0);
            return m;
        }

        static void AddEvent(EventTrigger t, EventTriggerType type, Action a)
        {
            var e = new EventTrigger.Entry { eventID = type };
            e.callback.AddListener(_ => a());
            t.triggers.Add(e);
        }

        void OnEnable() { _enabledAt = Time.unscaledTime; }

        public void Select(int i)
        {
            if (_items.Count == 0) return;
            if (i != _index && isActiveAndEnabled) Sfx.Play("select", 0.6f);
            _index = (i + _items.Count) % _items.Count;
            for (int k = 0; k < _items.Count; k++)
            {
                bool s = k == _index;
                _items[k].text = s ? "· " + _labels[k] + " ·" : _labels[k];
                _items[k].color = s ? _selected : _normal;
            }
        }

        public void Confirm()
        {
            if (Time.unscaledTime - _enabledAt < 0.2f) return;   // ignore the key press that opened the menu
            Sfx.Play("confirm", 0.7f);
            _actions?[_index]?.Invoke();
        }

        void Update()
        {
            // another sheet is on top (e.g. controls): only the menus inside that sheet keep listening
            if (Overlay != null && Overlay.activeInHierarchy && !transform.IsChildOf(Overlay.transform)) return;
            if (GameInput.Up) Select(_index - 1);
            else if (GameInput.Down) Select(_index + 1);
            else if (GameInput.Confirm) Confirm();
        }
    }
}
