using System.Collections;
using System.IO;
using System.Linq;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace WoodsGame.Tests
{
    /// <summary>Wind on the vegetation, rain showers coming and going, and screenshots of the new ground / rain / wind.</summary>
    public class WeatherTests
    {
        static readonly string Dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Documentation", "Screenshots"));
        VirtualInput _in;

        [UnitySetUp]
        public IEnumerator SetUp()
        {
            SaveSystem.Key = "woods_save_TEST"; SaveSystem.Delete();
            _in = new VirtualInput(); GameInput.Source = _in;
            GameManager.State = PlayerState.NewCharacter("knight"); SpawnDirector.Enabled = false;
            WeatherSystem.AutoCycle = false;
            Time.timeScale = 1;
            yield return null;
        }

        [UnityTearDown]
        public IEnumerator TearDown()
        {
            WeatherSystem.AutoCycle = true;
            SaveSystem.Delete(); SaveSystem.Key = "woods_save_v2"; SpawnDirector.Enabled = true;
            GameInput.Source = new KeyboardInput(); WorldUI.CloseAll(); Time.timeScale = 1;
            yield return null;
        }

        [UnityTest]
        public IEnumerator Wind_SwaysVegetation()
        {
            yield return WorldTests.LoadWorld();
            var ws = WeatherSystem.Current;
            Assert.IsNotNull(ws, "world has a WeatherSystem");
            var sh = Shader.Find("Woods/SpriteWind");
            Assert.IsNotNull(sh, "wind shader"); Assert.IsTrue(sh.isSupported, "wind shader supported");
            var swaying = Object.FindObjectsByType<SpriteRenderer>(FindObjectsSortMode.None)
                .Where(r => r.sharedMaterial != null && r.sharedMaterial.shader == sh).ToArray();
            Assert.Greater(swaying.Count(r => r.name.StartsWith("tree_")), 100, "trees sway");
            Assert.Greater(swaying.Count(r => r.name == "grass_tuft"), 500, "grass tufts sway");
            yield return new WaitForSeconds(0.3f);
            Assert.Greater(Shader.GetGlobalFloat("_WindStrength"), 0.3f, "wind is blowing");
            float a = Shader.GetGlobalFloat("_WindStrength");
            Assert.That(Mathf.Abs(Shader.GetGlobalFloat("_WindDir")), Is.EqualTo(1f));
            Assert.IsTrue(a > 0 && a < 3f);
        }

        [UnityTest]
        public IEnumerator Rain_ComesAndGoes_WithSplashesAndDarkerSky()
        {
            yield return WorldTests.LoadWorld();
            var ws = WeatherSystem.Current;
            Assert.IsNotNull(ws);
            Assert.AreEqual(0, ws.ActiveDrops, "starts dry");
            float wind0 = ws.Wind;
            ws.SetRain(true, 0.5f);
            yield return WorldTests.Until(() => ws.Intensity >= 1f, 3f, "rain fades in");
            yield return new WaitForSeconds(0.6f);
            Assert.Greater(ws.ActiveDrops, 200, "drops falling");
            Assert.Greater(ws.ActiveSplashes, 0, "splashes on the ground");
            Assert.Greater(ws.Wind, wind0 + 0.3f, "wind rises in the rain");
            var tint = ws.GetComponentsInChildren<SpriteRenderer>(true).Concat(Camera.main.GetComponentsInChildren<SpriteRenderer>(true))
                .FirstOrDefault(r => r.name == "RainTint");
            Assert.IsNotNull(tint); Assert.IsTrue(tint.enabled); Assert.Less(tint.color.b, 0.95f, "sky darker");
            var au = ws.GetComponent<AudioSource>();
            Assert.IsNotNull(au.clip, "rain loop assigned"); Assert.IsTrue(au.isPlaying, "rain is audible");

            ws.SetRain(false, 0.5f);
            yield return WorldTests.Until(() => ws.Intensity <= 0f, 3f, "rain fades out");
            yield return new WaitForSeconds(0.8f);
            Assert.AreEqual(0, ws.ActiveDrops, "no drops left");
            Assert.IsFalse(tint.enabled);

            // the automatic cycle starts a shower by itself
            WeatherSystem.AutoCycle = true;
            ws.clearTime = new Vector2(0.2f, 0.3f); ws.rainTime = new Vector2(0.2f, 0.3f); ws.fadeTime = 0.1f;
            ws.SetRain(false, 0f);
            yield return WorldTests.Until(() => ws.Raining, 3f, "automatic shower");
            yield return WorldTests.Until(() => !ws.Raining, 3f, "automatic clearing");
        }

        [UnityTest, Category("Screenshots")]
        public IEnumerator Capture_Weather()
        {
            Directory.CreateDirectory(Dir);
            yield return WorldTests.LoadWorld();
            var p = PlayerController.Current;
            var ws = WeatherSystem.Current;
            foreach (var e in Object.FindObjectsByType<EnemyController>(FindObjectsSortMode.None)) e.enabled = false;
            GameManager.State.clock = 10 * 60; DayNight.Advance(0.01f);
            ws.SetRain(false, 0f);
            // roads in the central valley: mossy flagstones, glowing flowers, swaying grass
            WorldTests.Teleport(p, new Vector2(127, 160 - 108));
            yield return new WaitForSeconds(1.5f);
            yield return WorldScreenshotsShot("21_ground_dark");
            WorldTests.Teleport(p, new Vector2(0.68f * 240, 160 - 0.24f * 160));
            yield return new WaitForSeconds(1.5f);
            yield return WorldScreenshotsShot("22_citadel_flagstones");
            // wind: two frames of the forest a moment apart
            WorldTests.Teleport(p, new Vector2(0.18f * 240, 160 - 0.36f * 160));
            yield return new WaitForSeconds(1.5f);
            yield return WorldScreenshotsShot("23_wind_forest");
            // rain by day and at night
            WorldTests.Teleport(p, new Vector2(127, 160 - 108));
            ws.SetRain(true, 0f);
            yield return new WaitForSeconds(1.2f);
            yield return WorldScreenshotsShot("24_rain_day");
            GameManager.State.clock = 22 * 60; DayNight.Advance(0.01f);
            yield return new WaitForSeconds(1.0f);
            yield return WorldScreenshotsShot("25_rain_night");
            ws.SetRain(false, 0f);
            yield return new WaitForSeconds(1.0f);
            yield return WorldScreenshotsShot("26_spores_night");
            GameManager.State.clock = 12 * 60; DayNight.Advance(0.01f);
        }

        static IEnumerator WorldScreenshotsShot(string name)
        {
            yield return new WaitForEndOfFrame();
            var cam = Camera.main;
            var rt = new RenderTexture(1280, 720, 24);
            cam.targetTexture = rt; cam.Render();
            var prev = RenderTexture.active; RenderTexture.active = rt;
            var tex = new Texture2D(1280, 720, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, 1280, 720), 0, 0); tex.Apply();
            RenderTexture.active = prev; cam.targetTexture = null;
            File.WriteAllBytes(Path.Combine(Dir, name + ".png"), tex.EncodeToPNG());
            Object.Destroy(rt); Object.Destroy(tex);
        }
    }
}
