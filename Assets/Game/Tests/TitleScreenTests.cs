using System.Collections;
using System.IO;
using System.Linq;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using UnityEngine.UI;

namespace WoodsGame.Tests
{
    /// <summary>The ERYNDOR title screen: the picture is the menu, the options are invisible buttons on top of it.</summary>
    public class TitleScreenTests
    {
        VirtualInput _in;

        [UnitySetUp]
        public IEnumerator SetUp()
        {
            SaveSystem.Key = "woods_save_TEST"; SaveSystem.Delete();
            _in = new VirtualInput(); GameInput.Source = _in;
            Time.timeScale = 1;
            SceneManager.LoadScene("MainMenu");
            yield return new WaitForSecondsRealtime(0.6f);
        }

        [UnityTearDown]
        public IEnumerator TearDown()
        {
            SaveSystem.Delete(); SaveSystem.Key = "woods_save_v2";
            GameInput.Source = new KeyboardInput(); MenuList.Overlay = null;
            yield return null;
        }

        IEnumerator Press(string a) { _in.Press(a); yield return null; yield return null; }
        static T Find<T>() where T : Object => Object.FindAnyObjectByType<T>(FindObjectsInactive.Include);

        [UnityTest, Timeout(60000)]
        public IEnumerator Title_ShowsTheIllustration_WithFiveHitboxes()
        {
            var t = Find<TitleScreen>();
            Assert.IsNotNull(t, "title screen");
            var bg = t.GetComponentsInChildren<Image>().First(i => i.name == "Background");
            Assert.IsNotNull(bg.sprite, "illustration assigned");
            Assert.IsTrue(bg.preserveAspect, "keeps its proportions");
            Assert.AreEqual(1672f / 941f, bg.sprite.rect.width / bg.sprite.rect.height, 0.01f, "original size");
            var buttons = t.GetComponentsInChildren<Button>();
            Assert.AreEqual(5, buttons.Length, "one hitbox per printed option");
            Assert.IsTrue(buttons.All(b => b.GetComponent<Image>().color.a == 0f), "hitboxes are invisible");
            // hitboxes are stacked top to bottom over the menu box in the middle of the picture
            var ys = buttons.Select(b => ((RectTransform)b.transform).anchorMin.y).ToArray();
            for (int i = 1; i < ys.Length; i++) Assert.Less(ys[i], ys[i - 1]);
            Assert.IsFalse(t.IsEnabled(0), "no save: Continuar disabled");
            Assert.AreEqual(1, t.Index, "starts on Nueva Partida");
            yield return Shot("00_title_screen");
        }

        [UnityTest, Timeout(60000)]
        public IEnumerator Title_OptionsCreditsExit_OpenAndClose()
        {
            var t = Find<TitleScreen>();
            yield return new WaitForSecondsRealtime(0.3f);
            yield return Press("Down");                          // Opciones
            Assert.AreEqual(2, t.Index);
            yield return Press("Confirm");
            var opt = GameObject.Find("Options");
            Assert.IsTrue(opt != null && opt.activeInHierarchy, "options open");
            float v = Sfx.MusicVolume;
            yield return Press("Down");                          // Música
            yield return Press("Left");
            Assert.Less(Sfx.MusicVolume, v + 0.001f, "music volume changes");
            Sfx.MusicVolume = v;
            yield return Shot("00b_title_options");
            yield return new WaitForSecondsRealtime(0.3f);
            yield return Press("Pause");
            Assert.IsFalse(opt.activeInHierarchy, "Esc closes options");
            yield return new WaitForSecondsRealtime(0.3f);
            yield return Press("Down");                          // Créditos
            yield return Press("Confirm");
            var cred = GameObject.Find("Credits");
            Assert.IsTrue(cred != null && cred.activeInHierarchy, "credits open");
            Assert.IsTrue(cred.GetComponentsInChildren<Text>().Any(x => x.text.Contains("AndresTaki")), "creator credited");
            yield return Shot("00c_title_credits");
            yield return new WaitForSecondsRealtime(0.3f);
            yield return Press("Pause");
            yield return new WaitForSecondsRealtime(0.3f);
            yield return Press("Down");                          // Salir -> confirmation, then No
            yield return Press("Confirm");
            var exit = GameObject.Find("ExitConfirm");
            Assert.IsTrue(exit != null && exit.activeInHierarchy, "exit asks first");
            yield return new WaitForSecondsRealtime(0.3f);
            yield return Press("Down");
            yield return Press("Confirm");                       // No
            Assert.IsFalse(exit.activeInHierarchy, "stayed in the game");
        }

        static IEnumerator Shot(string name)
        {
            string dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Documentation", "Screenshots"));
            Directory.CreateDirectory(dir);
            var cam = Camera.main;
            var rt = new RenderTexture(1280, 720, 24);
            var canvases = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None).Where(c => c.isRootCanvas).ToArray();
            var modes = canvases.Select(c => c.renderMode).ToArray();
            var orders = canvases.Select(c => c.sortingOrder).ToArray();
            foreach (var c in canvases) { c.renderMode = RenderMode.ScreenSpaceCamera; c.worldCamera = cam; c.planeDistance = 1f; c.sortingOrder += 3000; }
            cam.targetTexture = rt;
            yield return null;
            Canvas.ForceUpdateCanvases();
            cam.Render();
            var prev = RenderTexture.active; RenderTexture.active = rt;
            var tex = new Texture2D(1280, 720, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, 1280, 720), 0, 0); tex.Apply();
            RenderTexture.active = prev;
            File.WriteAllBytes(Path.Combine(dir, name + ".png"), tex.EncodeToPNG());
            cam.targetTexture = null;
            for (int i = 0; i < canvases.Length; i++) if (canvases[i]) { canvases[i].renderMode = modes[i]; canvases[i].sortingOrder = orders[i]; }
            Object.Destroy(rt); Object.Destroy(tex);
        }
    }
}
