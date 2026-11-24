using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;

namespace WoodsGame
{
    /// <summary>Conversation box (portrait, name, trade, text and answers), camp menu and the orders for raised allies.</summary>
    public partial class WorldUI
    {
        RectTransform _talk, _talkBox;
        Image _talkPortrait, _talkFrame;
        Text _talkName, _talkJob, _talkText;
        MenuList _talkMenu;
        Sprite[] _talkFrames;
        float _talkAnim;

        public static bool TalkOpen => _i != null && _i._talk != null && _i._talk.gameObject.activeSelf;
        public static string TalkText => _i != null && _i._talkText != null ? _i._talkText.text : "";
        public static int TalkOptions => _i != null && _i._talkMenu != null ? _i._talkMenu.Count : 0;
        public static MenuList TalkMenu => _i != null ? _i._talkMenu : null;

        void BuildTalk()
        {
            _talk = UIRoot.Rect(_root, "Talk", Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            _talk.gameObject.AddComponent<Image>().color = new Color(0.03f, 0.02f, 0.06f, 0.35f);
            _panels.Add(_talk);
            _talkBox = UIRoot.Rect(_talk, "Box", new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0, 6), new Vector2(304, 110));
            UIRoot.Img(_talkBox, GameAssets.I ? GameAssets.I.panel : null, true).rectTransform.sizeDelta = new Vector2(304, 110);
            var frame = UIRoot.Rect(_talkBox, "Portrait", new Vector2(0, 1), new Vector2(0, 1), new Vector2(8, -8), new Vector2(40, 40));
            _talkFrame = frame.gameObject.AddComponent<Image>(); _talkFrame.color = new Color32(0x3e, 0x89, 0x48, 0xff);
            _talkPortrait = UIRoot.Img(frame, null, false); _talkPortrait.rectTransform.sizeDelta = new Vector2(64, 64);
            _talkPortrait.rectTransform.anchoredPosition = new Vector2(0, 6);
            frame.gameObject.AddComponent<RectMask2D>();
            _talkName = Label(_talkBox, "", new Vector2(0, 1), new Vector2(54, -7), TextAnchor.UpperLeft, UIRoot.Cream);
            _talkJob = Label(_talkBox, "", new Vector2(0, 1), new Vector2(54, -17), TextAnchor.UpperLeft, GoldC);
            _talkText = Label(_talkBox, "", new Vector2(0, 1), new Vector2(54, -29), TextAnchor.UpperLeft, Soft);
            _talkText.rectTransform.sizeDelta = new Vector2(242, 30); _talkText.horizontalOverflow = HorizontalWrapMode.Wrap;
            _talk.gameObject.SetActive(false);
        }

        /// <summary>Shows a line of a conversation with its answers (W/S + Enter, or mouse).</summary>
        public static void Talk(Sprite[] portrait, string name, string job, string text, string[] options, Action[] actions)
        {
            var ui = I;
            if (!ui._talk.gameObject.activeSelf) Open(ui._talk);
            ui._talkFrames = portrait;
            ui._talkFrame.gameObject.SetActive(portrait != null && portrait.Length > 0);
            ui._talkName.text = name; ui._talkJob.text = job ?? "";
            ui._talkText.text = text;
            // text height depends on its length; answers go under it
            int lines = Mathf.Clamp(Mathf.CeilToInt(text.Length / 52f), 1, 6);
            ui._talkText.rectTransform.sizeDelta = new Vector2(242, lines * 10 + 4);
            float textBottom = 29 + lines * 10 + 4;
            float h = Mathf.Max(56, textBottom) + options.Length * 10 + 10;
            ui._talkBox.sizeDelta = new Vector2(304, h);
            ui._talkBox.GetChild(0).GetComponent<RectTransform>().sizeDelta = new Vector2(304, h);
            if (ui._talkMenu != null) Destroy(ui._talkMenu.gameObject);
            ui._talkMenu = MenuList.Create(ui._talkBox, options, actions, Vector2.zero, Soft, GoldC, 10);
            var mr = (RectTransform)ui._talkMenu.transform;
            mr.anchorMin = mr.anchorMax = new Vector2(0, 1); mr.pivot = new Vector2(0, 1);
            mr.anchoredPosition = new Vector2(84, -Mathf.Max(52, textBottom));
            mr.sizeDelta = new Vector2(200, options.Length * 10);
            foreach (var t in ui._talkMenu.GetComponentsInChildren<Text>())
            {
                var rt = t.rectTransform; float y = rt.anchoredPosition.y;
                t.alignment = TextAnchor.UpperLeft;
                rt.anchorMin = rt.anchorMax = new Vector2(0, 1); rt.pivot = new Vector2(0, 1);
                rt.anchoredPosition = new Vector2(0, y); rt.sizeDelta = new Vector2(214, 10);
            }
            Sfx.Play("talk", 0.4f);
        }

        /// <summary>A simple menu box (camps, signs with options).</summary>
        public static void Choice(string title, string text, string[] options, Action[] actions, Sprite icon = null)
        {
            Talk(icon != null ? new[] { icon } : null, title, "", text, options, actions);
            if (icon != null) { I._talkPortrait.rectTransform.sizeDelta = new Vector2(32, 32); I._talkPortrait.rectTransform.anchoredPosition = Vector2.zero; }
        }

        void AnimateTalk()
        {
            _talkAnim += Time.unscaledDeltaTime;
            if (_talkFrames != null && _talkFrames.Length > 0)
            {
                _talkPortrait.sprite = _talkFrames[(int)(_talkAnim * 5) % _talkFrames.Length];
                _talkPortrait.color = Color.white;
                bool big = _talkFrames[0] != null && _talkFrames[0].rect.width >= 48;
                if (big) { _talkPortrait.rectTransform.sizeDelta = new Vector2(64, 64); _talkPortrait.rectTransform.anchoredPosition = new Vector2(0, -2); }
            }
        }

        // ================================================================ orders for the raised allies (V)
        int _summonSel;   // -1 = all

        public static void OpenSummons()
        {
            var ui = I;
            var allies = Summoning.Allies.ToList();
            if (allies.Count == 0)
            {
                Choice("Maldición del Invocador", $"No tienes invocaciones. Derrota a un enemigo y pulsa V junto a su cuerpo para alzarlo (máximo {Summoning.Max}).",
                    new[] { "Cerrar" }, new Action[] { CloseAll }, GameAssets.I && GameAssets.I.summonFx != null && GameAssets.I.summonFx.Length > 0 ? GameAssets.I.summonFx[0] : null);
                return;
            }
            ui._summonSel = Mathf.Clamp(ui._summonSel, -1, allies.Count - 1);
            string who = ui._summonSel < 0 ? "Todas" : allies[ui._summonSel].displayName;
            var lines = allies.Select((a, i) => $"{(i == ui._summonSel ? ">" : " ")} {a.displayName.Replace("ALIADO: ", "")} {a.health.hp}/{a.health.maxHP} · {Summoning.TaskName(a.allyTask)}");
            string text = string.Join("\n", lines);
            var opts = new List<string> { "Elegir: " + (ui._summonSel < 0 ? "todas" : who.Replace("ALIADO: ", "").ToLowerInvariant()), "Seguirme", "Atacar a los enemigos", "Guardar este lugar", "Liberar", "Cerrar" };
            var acts = new List<Action>
            {
                () => { ui._summonSel = ui._summonSel + 1 >= allies.Count ? -1 : ui._summonSel + 1; OpenSummons(); },
                () => Order(allies, Summoning.Follow), () => Order(allies, Summoning.Attack), () => Order(allies, Summoning.Guard),
                () => { foreach (var a in Targets(allies)) Summoning.Release(a); ui._summonSel = -1; CloseAll(); UIRoot.Toast("INVOCACIÓN LIBERADA"); },
                CloseAll,
            };
            Talk(null, $"Invocaciones {allies.Count}/{Summoning.Max}", "", text, opts.ToArray(), acts.ToArray());
        }

        static IEnumerable<EnemyController> Targets(List<EnemyController> allies) => I._summonSel < 0 ? allies : new[] { allies[I._summonSel] };

        static void Order(List<EnemyController> allies, string task)
        {
            foreach (var a in Targets(allies)) Summoning.SetTask(a, task);
            Sfx.Play("confirm");
            CloseAll();
            UIRoot.Toast("ÓRDEN: " + Summoning.TaskName(task).ToUpperInvariant(), 1.4f);
        }
    }
}
