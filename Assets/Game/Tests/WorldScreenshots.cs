using System.Collections;
using System.IO;
using System.Linq;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace WoodsGame.Tests
{
    /// <summary>Real in-game frames (world + UI) -> Documentation/Screenshots, for visual review.</summary>
    [Category("Screenshots")]
    public class WorldScreenshots
    {
        static readonly string Dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Documentation", "Screenshots"));
        VirtualInput _in;

        [UnitySetUp]
        public IEnumerator SetUp()
        {
            SaveSystem.Key = "woods_save_TEST"; SaveSystem.Delete();
            _in = new VirtualInput(); GameInput.Source = _in;
            GameManager.State = PlayerState.NewCharacter("knight"); SpawnDirector.Enabled = false;
            Time.timeScale = 1;
            Directory.CreateDirectory(Dir);
            yield return null;
        }

        [UnityTearDown]
        public IEnumerator TearDown()
        {
            SaveSystem.Delete(); SaveSystem.Key = "woods_save_v2"; SpawnDirector.Enabled = true;
            GameInput.Source = new KeyboardInput(); WorldUI.CloseAll(); Time.timeScale = 1;
            yield return null;
        }

        internal static IEnumerator Shot(string name)
        {
            var cam = Camera.main;
            var rt = new RenderTexture(1280, 720, 24);
            var canvases = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None).Where(c => c.isRootCanvas).ToArray();
            var modes = canvases.Select(c => c.renderMode).ToArray();
            var orders = canvases.Select(c => c.sortingOrder).ToArray();
            // UI must stay above the night overlay (sorting order 1000+) when canvases are rendered by the camera
            foreach (var c in canvases) { c.renderMode = RenderMode.ScreenSpaceCamera; c.worldCamera = cam; c.planeDistance = 1f; c.sortingOrder += 3000; }
            cam.targetTexture = rt;
            yield return null;
            Canvas.ForceUpdateCanvases();
            cam.Render();
            var prev = RenderTexture.active; RenderTexture.active = rt;
            var tex = new Texture2D(1280, 720, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, 1280, 720), 0, 0); tex.Apply();
            RenderTexture.active = prev;
            File.WriteAllBytes(Path.Combine(Dir, name + ".png"), tex.EncodeToPNG());
            cam.targetTexture = null;
            for (int i = 0; i < canvases.Length; i++) if (canvases[i]) { canvases[i].renderMode = modes[i]; canvases[i].sortingOrder = orders[i]; }
            Object.Destroy(rt); Object.Destroy(tex);
        }

        static void Teleport(Component c, Vector2 p) => WorldTests.Teleport(c, p);

        [UnityTest]
        public IEnumerator Capture_World()
        {
            SceneManager.LoadScene("MainMenu");
            yield return new WaitForSeconds(0.7f);
            yield return Shot("01_menu");
            _in.Press("Confirm"); yield return null; yield return null;
            yield return new WaitForSecondsRealtime(0.3f);
            _in.Press("Right"); yield return null; yield return null;
            yield return new WaitForSecondsRealtime(0.4f);
            yield return Shot("01b_class_select");

            SceneManager.LoadScene(MapDB.StartMap);
            yield return new WaitForSeconds(1.0f);
            yield return Shot("02_start_village");
            SceneManager.LoadScene("World");
            yield return new WaitForSeconds(1.0f);
            var p = PlayerController.Current;

            _in.move = new Vector2(1, 0.3f).normalized; _in.run = true;
            yield return new WaitForSeconds(1.5f);
            _in.move = Vector2.zero; _in.run = false;
            yield return new WaitForSeconds(0.8f);
            yield return Shot("03_walking");

            var orc = Object.FindObjectsByType<EnemyController>(FindObjectsSortMode.None).First(e => e.kind == EnemyKind.Orc && !e.isBoss);
            orc.enabled = false; WorldTests.WakeFrozen(orc);
            Teleport(orc, (Vector2)p.transform.position + Vector2.right * 1.1f);
            _in.move = Vector2.right; yield return null; yield return null; _in.move = Vector2.zero;
            _in.Press("Attack");
            yield return new WaitForSeconds(0.25f);
            yield return Shot("04_combat");

            _in.Press("Map"); yield return null; yield return null;
            yield return Shot("05_map");
            WorldUI.CloseAll();
            GameManager.State.coins = 120;
            WorldUI.OpenShop(); yield return null;
            yield return Shot("06_shop");
            WorldUI.CloseAll();
            GameManager.State.Set("region_c"); GameManager.State.Set("region_a");
            WorldUI.ToggleJournal(); yield return null;
            yield return Shot("07_journal");
            WorldUI.CloseAll();

            foreach (var (name, fx, fy) in new[] { ("08_lake", 0.50f, 0.52f), ("09_citadel", 0.68f, 0.24f), ("10_peaks", 0.30f, 0.16f),
                                                   ("11_swamp", 0.84f, 0.76f), ("12_desert_fort", 0.88f, 0.34f), ("13_port", 0.20f, 0.66f) })
            {
                Teleport(p, new Vector2(fx * 240, 160 - fy * 160));
                yield return new WaitForSeconds(1.6f);
                yield return Shot(name);
            }
            // character sheet with points to spend
            GameManager.State.attrPoints = 4; GameManager.State.level = 3;
            WorldUI.ToggleCharacter(); yield return new WaitForSecondsRealtime(0.3f);
            yield return Shot("16_character_sheet");
            WorldUI.CloseAll();
            foreach (var id in new[] { "katana_moon", "halberd", "axe_frost", "bow_elf", "crossbow", "armor_dragon", "dagger_venom", "mace_holy" })
                GameManager.State.AddItem(id);
            WorldUI.ToggleInventory(); yield return new WaitForSecondsRealtime(0.3f);
            yield return Shot("19_inventory");
            WorldUI.CloseAll();
            WorldUI.OpenSmith(); yield return new WaitForSecondsRealtime(0.3f);
            yield return Shot("20_blacksmith");
            WorldUI.CloseAll();

            // night in the village, with an elite and a wraith
            SceneManager.LoadScene(MapDB.StartMap);
            yield return new WaitForSeconds(1.0f);
            p = PlayerController.Current;
            var village = Object.FindObjectsByType<Campfire>(FindObjectsSortMode.None).First();
            Teleport(p, (Vector2)village.transform.position + Vector2.down * 1.5f);
            GameManager.State.clock = 22 * 60; DayNight.Advance(0.01f);
            foreach (var e in Object.FindObjectsByType<EnemyController>(FindObjectsSortMode.None)) e.enabled = false;
            var elite = Object.Instantiate(GameAssets.I.EnemyPrefab("OrcBerserker"), p.transform.position + new Vector3(-3f, 0.5f), Quaternion.identity).GetComponent<EnemyController>();
            elite.spawned = true; elite.Setup(EnemyRank.Elite, 4, true); elite.enabled = false;
            var ghost = Object.Instantiate(GameAssets.I.EnemyPrefab("DemonWraith"), p.transform.position + new Vector3(3f, 1f), Quaternion.identity).GetComponent<EnemyController>();
            ghost.spawned = true; ghost.Setup(EnemyRank.Normal, 4, true); ghost.enabled = false;
            yield return new WaitForSeconds(1.2f);
            yield return Shot("17_night_village");
            Object.Destroy(elite.gameObject); Object.Destroy(ghost.gameObject);
            GameManager.State.clock = 12 * 60; DayNight.Advance(0.01f);

            // interiors: inn, house, smithy (village) and chapel, library, barracks (citadel)
            foreach (var tpl in new[] { "posada", "casa", "herreria", "@City_Ciudadela", "capilla", "biblioteca", "cuartel" })
            {
                if (tpl.StartsWith("@")) { SceneManager.LoadScene(tpl.Substring(1)); yield return new WaitForSeconds(1.0f); p = PlayerController.Current; continue; }
                var room = Object.FindObjectsByType<Interior>(FindObjectsSortMode.None).FirstOrDefault(r => r.template == tpl);
                if (room == null) continue;
                GameManager.EnterInterior(room);
                yield return new WaitForSeconds(1.0f);
                yield return Shot("18_interior_" + tpl);
                GameManager.ExitInterior();
                yield return new WaitForSeconds(0.8f);
            }

            p.health.Damage(new DamageInfo { amount = 999, source = Team.Enemy });
            yield return new WaitForSeconds(2.4f);
            yield return Shot("15_death");
        }
    }
}
