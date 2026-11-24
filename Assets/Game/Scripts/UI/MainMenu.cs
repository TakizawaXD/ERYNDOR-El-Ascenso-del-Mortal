using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;

namespace WoodsGame
{
    /// <summary>Main menu scene: the ERYNDOR title illustration with its five printed options made interactive
    /// (TitleScreen), plus the dialogs they open: class select (new game), options, credits and the exit confirmation.</summary>
    public class MainMenu : MonoBehaviour
    {
        GameObject _controls, _options, _credits, _exit;
        ClassSelect _classes;
        TitleScreen _title;
        MenuList _optMenu;
        int _resIndex;
        Resolution[] _resolutions;

        static readonly Color Soft = new Color32(0xa9, 0xa3, 0xb8, 0xff), Accent = new Color32(0xd9, 0xa8, 0xff, 0xff);

        void Start()
        {
            GameManager.Ensure();
            UIRoot.HideAll();
            Sfx.Music(true);
            var a = GameAssets.I;
            bool cont = GameManager.CanContinue;
            _title = TitleScreen.Create(transform, a ? a.titleScreen : null,
                new Action[] { GameManager.Continue, Play, ShowOptions, ShowCredits, AskQuit }, cont);
            _title.blocked = () => (MenuList.Overlay != null && MenuList.Overlay.activeInHierarchy);

            var root = UIRoot.CreateCanvas(transform, 20);            // dialogs on the game's 320x180 pixel canvas
            _controls = BuildControls(root);
            _options = BuildOptions(root);
            _credits = BuildCredits(root);
            _exit = BuildExit(root);
            _classes = ClassSelect.Create(root);
            _classes.onChosenNamed = (id, name) => { _classes.enabled = false; GameManager.NewGame(id, name); };
            _classes.onBack = () => Close(_classes.gameObject);
        }

        void Open(GameObject panel) { MenuList.Overlay = panel; panel.SetActive(true); }
        void Close(GameObject panel) { panel.SetActive(false); if (MenuList.Overlay == panel) MenuList.Overlay = null; }

        // ---------------------------------------------------------------- actions
        void Play() { Open(_classes.gameObject); _classes.Select(0); }      // new game: choose your knight, then the first map loads

        void ShowOptions() { Open(_options); _optMenu.Select(0); }

        void ShowCredits() => Open(_credits);

        void AskQuit() => Open(_exit);

        void Quit()
        {
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }

        // ---------------------------------------------------------------- dialogs
        RectTransform Dialog(RectTransform root, string name, Vector2 size, string title)
        {
            var dim = UIRoot.Rect(root, name, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            dim.gameObject.AddComponent<Image>().color = new Color(0.04f, 0.02f, 0.09f, 0.78f);
            var box = UIRoot.Rect(dim, "Box", new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, size);
            var bg = UIRoot.Img(box, GameAssets.I ? GameAssets.I.panel : null, true); bg.rectTransform.sizeDelta = size;
            if (!GameAssets.I || !GameAssets.I.panel) bg.color = new Color(0.08f, 0.05f, 0.14f, 0.95f);
            UIRoot.Label(box, title, new Vector2(0.5f, 1), new Vector2(0, -7), TextAnchor.UpperCenter, Accent);
            dim.gameObject.SetActive(false);
            return dim;
        }

        GameObject BuildCredits(RectTransform root)
        {
            var dim = Dialog(root, "Credits", new Vector2(230, 140), "Créditos");
            var box = dim.Find("Box");
            string[] lines =
            {
                "ERYNDOR - El Ascenso del Mortal",
                "",
                "Creado por AndresTaki",
                "",
                "Personajes base: Tiny RPG Character Asset Packs",
                "Bosque: pixel_16 woods · Granja: Cute Fantasy (Free)",
                "Música, efectos y resto del arte: hechos para el juego",
                "",
                "Enter o Esc para volver",
            };
            for (int i = 0; i < lines.Length; i++)
                UIRoot.Label(box, lines[i], new Vector2(0.5f, 1), new Vector2(0, -22 - i * 11), TextAnchor.UpperCenter,
                    i == 2 ? (Color)new Color32(0xff, 0xc8, 0x5a, 0xff) : i == 0 ? UIRoot.Cream : Soft);
            var closer = dim.gameObject.AddComponent<CloseOnConfirm>();
            return dim.gameObject;
        }

        GameObject BuildExit(RectTransform root)
        {
            var dim = Dialog(root, "ExitConfirm", new Vector2(150, 70), "¿Salir del juego?");
            var menu = MenuList.Create(dim.Find("Box"), new[] { "Sí, salir", "No" }, new Action[] { Quit, () => Close(dim.gameObject) },
                new Vector2(0, -8), Soft, new Color32(0xff, 0xc8, 0x5a, 0xff));
            menu.gameObject.AddComponent<MenuListOwner>().owner = dim.gameObject;
            dim.gameObject.AddComponent<EscCloses>().onClose = () => Close(dim.gameObject);
            return dim.gameObject;
        }

        // ---------------------------------------------------------------- options: volumes, resolution, full screen
        GameObject BuildOptions(RectTransform root)
        {
            var dim = Dialog(root, "Options", new Vector2(230, 120), "Opciones");
            _resolutions = Screen.resolutions.GroupBy(r => (r.width, r.height)).Select(g => g.Last()).Where(r => r.width >= 640).ToArray();
            if (_resolutions.Length == 0) _resolutions = new[] { new Resolution { width = 1280, height = 720 } };
            _resIndex = Array.FindIndex(_resolutions, r => r.width == Screen.width && r.height == Screen.height);
            if (_resIndex < 0) _resIndex = _resolutions.Length - 1;
            RefreshOptions(dim);
            dim.gameObject.AddComponent<EscCloses>().onClose = () => Close(dim.gameObject);
            var keys = dim.gameObject.AddComponent<OptionKeys>();
            keys.onChange = d => { Change(d); RefreshOptions(dim); };
            return dim.gameObject;
        }

        string[] OptionLabels()
        {
            var r = _resolutions[Mathf.Clamp(_resIndex, 0, _resolutions.Length - 1)];
            return new[]
            {
                $"Efectos   < {Mathf.RoundToInt(Sfx.SfxVolume * 100)}% >",
                $"Música    < {Mathf.RoundToInt(Sfx.MusicVolume * 100)}% >",
                $"Resolución  < {r.width}x{r.height} >",
                $"Pantalla completa  < {(Screen.fullScreen ? "Sí" : "No")} >",
                "Controles",
                "Volver",
            };
        }

        void RefreshOptions(RectTransform dim)
        {
            int keep = _optMenu != null ? _optMenu.Index : 0;
            var labels = OptionLabels();
            if (_optMenu == null)
            {
                _optMenu = MenuList.Create(dim.Find("Box"), labels, new Action[]
                {
                    () => { Change(1); RefreshOptions(dim); }, () => { Change(1); RefreshOptions(dim); },
                    () => { Change(1); RefreshOptions(dim); }, () => { Change(1); RefreshOptions(dim); },
                    () => { MenuList.Overlay = _controls; _controls.SetActive(true); },
                    () => Close(dim.gameObject),
                }, new Vector2(0, -8), Soft, new Color32(0xff, 0xc8, 0x5a, 0xff), 13);
                _optMenu.gameObject.AddComponent<MenuListOwner>().owner = dim.gameObject;
            }
            else _optMenu.SetLabels(labels);
            _optMenu.Select(keep);
        }

        /// <summary>Left/right (or Enter) on the highlighted option.</summary>
        void Change(int d)
        {
            if (_optMenu == null) return;
            switch (_optMenu.Index)
            {
                case 0: Sfx.SfxVolume = Mathf.Clamp01(Mathf.Round(Sfx.SfxVolume * 10 + d) / 10f); Sfx.Play("select", 0.8f); break;
                case 1: Sfx.MusicVolume = Mathf.Clamp01(Mathf.Round(Sfx.MusicVolume * 10 + d) / 10f); break;
                case 2:
                    _resIndex = (_resIndex + d + _resolutions.Length) % _resolutions.Length;
                    var r = _resolutions[_resIndex];
                    Screen.SetResolution(r.width, r.height, Screen.fullScreenMode);
                    break;
                case 3:
                    Screen.fullScreenMode = Screen.fullScreen ? FullScreenMode.Windowed : FullScreenMode.FullScreenWindow;
                    break;
            }
        }

        GameObject BuildControls(RectTransform root)
        {
            var dim = UIRoot.Rect(root, "Controls", Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            dim.gameObject.AddComponent<Image>().color = new Color(0.04f, 0.02f, 0.09f, 0.9f);
            var box = UIRoot.Rect(dim, "Box", new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(240, 156));
            UIRoot.Img(box, GameAssets.I ? GameAssets.I.panel : null, true).rectTransform.sizeDelta = new Vector2(240, 156);
            string[] lines =
            {
                "CONTROLES", "", "WASD / FLECHAS   MOVER", "SHIFT           CORRER", "J / CLIC        ESPADA (X2 COMBO)",
                "K / CLIC DER.   GOLPE FUERTE", "L               ARCO", "ESPACIO         RODAR", "E               USAR / HABLAR",
                "Q               BEBER POCIÓN", "M / TAB         MAPA / DIARIO", "C               FICHA DEL HÉROE", "ENTER PARA VOLVER"
            };
            for (int i = 0; i < lines.Length; i++)
                UIRoot.Label(box, lines[i], new Vector2(0.5f, 1), new Vector2(0, -10 - i * 10), TextAnchor.UpperCenter,
                    i == 0 ? (Color)new Color32(0xf4, 0xed, 0xea, 0xff) : Soft);
            var c = dim.gameObject.AddComponent<CloseOnConfirm>();
            dim.gameObject.SetActive(false);
            return dim.gameObject;
        }

        void Update()
        {
            // a sub-dialog (controls) closing hands the input back to the options panel
            if (_options != null && _options.activeSelf && (MenuList.Overlay == null || !MenuList.Overlay.activeInHierarchy) && !_controls.activeSelf)
                MenuList.Overlay = _options;
        }
    }

    /// <summary>A MenuList inside a dialog keeps working while its own dialog is the overlay.</summary>
    public class MenuListOwner : MonoBehaviour { public GameObject owner; }

    /// <summary>Esc closes the dialog it sits on.</summary>
    public class EscCloses : MonoBehaviour
    {
        public Action onClose;
        float _opened;
        void OnEnable() { _opened = Time.unscaledTime; }
        void Update()
        {
            if (Time.unscaledTime - _opened < 0.2f || MenuList.Overlay != gameObject) return;
            if (GameInput.Pause) { Sfx.Play("select", 0.5f); onClose?.Invoke(); }
        }
    }

    /// <summary>Left / right on the options panel.</summary>
    public class OptionKeys : MonoBehaviour
    {
        public Action<int> onChange;
        void Update()
        {
            if (MenuList.Overlay != gameObject) return;
            if (GameInput.Left) onChange?.Invoke(-1);
            else if (GameInput.Right) onChange?.Invoke(1);
        }
    }
}
