using System.Collections;
using System.Collections.Generic;
using System.Linq;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace WoodsGame.Tests
{
    /// <summary>Soundtrack and sound: the piece follows the region, town, interior, camp, combat and boss; the night layer
    /// fades in at night and stays in sync; menus duck the music; music and effects volumes are respected and saved.</summary>
    public class AudioTests
    {
        VirtualInput _in;
        float _music, _sfx;

        [UnitySetUp]
        public IEnumerator SetUp()
        {
            SaveSystem.Key = "woods_save_TEST"; SaveSystem.Delete();
            _in = new VirtualInput(); GameInput.Source = _in;
            GameManager.State = WorldTests.Deterministic(PlayerState.NewCharacter("knight"));
            SpawnDirector.Enabled = false;
            Time.timeScale = 1;
            _music = Sfx.MusicVolume; _sfx = Sfx.SfxVolume;
            Sfx.MusicVolume = 0.6f; Sfx.SfxVolume = 0.8f;
            MusicDirector.Force = null;
            yield return null;
        }

        [UnityTearDown]
        public IEnumerator TearDown()
        {
            Sfx.MusicVolume = _music; Sfx.SfxVolume = _sfx;
            MusicDirector.Force = null;
            if (GameManager.Paused) GameManager.SetPaused(false);
            SaveSystem.Delete(); SaveSystem.Key = "woods_save_v2"; SpawnDirector.Enabled = true;
            GameInput.Source = new KeyboardInput(); WorldUI.CloseAll(); Time.timeScale = 1;
            yield return null;
        }

        static PlayerController Player => PlayerController.Current;

        static IEnumerator Load(string map)
        {
            yield return WorldTests.LoadMap(map);
            yield return WorldTests.Until(() => Player != null && WorldInfo.Current != null, 10f, "load " + map);
            Player.health.Init(999);
            DayNight.SkipTo(10);
        }

        /// <summary>No enemy around: they would start the battle music.</summary>
        static void Calm()
        {
            foreach (var e in Object.FindObjectsByType<EnemyController>(FindObjectsSortMode.None)) e.enabled = false;
        }

        /// <summary>A walkable tile in the middle of a region of the current map.</summary>
        static Vector2 TileIn(char region)
        {
            var wi = WorldInfo.Current;
            var tiles = new List<Vector2>();
            for (int row = 0; row < wi.regionRows.Length; row += 2)
                for (int x = 0; x < wi.regionRows[row].Length; x += 2)
                {
                    if (wi.regionRows[row][x] != region) continue;
                    var p = new Vector2(x + 0.5f, wi.height - 1 - row + 0.5f);
                    if (wi.Walkable(p) && wi.Walkable(p + Vector2.right) && wi.Walkable(p + Vector2.up)) tiles.Add(p);
                }
            Assert.IsNotEmpty(tiles, "walkable tiles in region " + region);
            var c = tiles.Aggregate(Vector2.zero, (a, b) => a + b) / tiles.Count;
            return tiles.OrderBy(t => (t - c).sqrMagnitude).First();
        }

        // ------------------------------------------------------------------ assets
        [Test]
        public void Soundtrack_HasAPieceForEveryPartOfTheGame()
        {
            var a = GameAssets.I;
            Assert.IsNotNull(a);
            string[] loops = { "menu", "classselect", "camp", "combat", "combat_elite", "city_valle", "city_ciudadela", "city_puerto",
                "int_casa", "int_posada", "int_capilla", "int_herreria", "boss_I", "boss_K", "boss_Q", "boss_B", "boss_F" };
            foreach (var id in loops) Assert.IsNotNull(a.MusicClip("music_" + id + "_loop"), id);
            foreach (var r in "abcdefghij")
            {
                var day = a.MusicClip("music_region_" + r + "_loop");
                var night = a.MusicClip("music_region_" + r + "_night");
                Assert.IsNotNull(day, "region " + r); Assert.IsNotNull(night, "night layer of region " + r);
                Assert.AreEqual(day.samples, night.samples, "night layer of region " + r + " has the same length");
            }
            foreach (var b in new[] { "menu", "boss_I", "boss_K", "boss_Q", "boss_B", "boss_F" }) Assert.IsNotNull(a.MusicClip("music_" + b + "_intro"), b + " intro");
            foreach (var j in new[] { "victory", "defeat", "levelup", "discover" }) Assert.IsNotNull(a.MusicClip("jingle_" + j), j);
            foreach (var amb in new[] { "wind", "wind_strong", "desert", "birds", "crickets", "waves", "lake", "lava", "swamp", "fire", "corrupt", "town" })
                Assert.IsNotNull(a.AmbienceClip("amb_" + amb), amb);
            // effects come in variants
            foreach (var s in new[] { "step_grass", "step_snow", "step_wood", "step_sand", "swing", "hit_blade", "hit_blunt", "vox_orc_hurt", "vox_demon_die", "cow", "pig", "chicken", "sheep", "cat_meow" })
                Assert.GreaterOrEqual(a.sfx.Count(c => c != null && c.name.StartsWith("sfx_" + s + "_") && char.IsDigit(c.name[c.name.Length - 1])), 2, s + " variants");
            foreach (var s in new[] { "cat_purr", "door_open", "door_close", "gate", "buy", "sell", "menu_open", "menu_close", "equip", "error", "spell", "heal" })
                Assert.IsNotNull(Sfx.Clip(s), s);
        }

        // ------------------------------------------------------------------ music follows the place
        [UnityTest, Timeout(120000)]
        public IEnumerator Music_ChangesWithTheRegion_AndTheNightLayerFadesIn()
        {
            yield return Load("World");
            Calm();
            WorldTests.Teleport(Player, TileIn('b'));
            yield return WorldTests.Until(() => Sfx.CurrentTrack == "region_b", 8f, "Bosque del Oeste theme");
            WorldTests.Teleport(Player, TileIn('e'));
            yield return WorldTests.Until(() => Sfx.CurrentTrack == "region_e", 8f, "Picos Nevados theme");
            Assert.Less(Sfx.Director.NightLayer, 0.2f, "daytime: the day piece");
            Assert.AreEqual("snow", Sfx.Surface(Player.transform.position), "snowy steps on the peaks");
            DayNight.SkipTo(23);
            yield return WorldTests.Until(() => Sfx.Director.NightLayer > 0.95f, 12f, "night layer fades in");
            Assert.IsTrue(Sfx.Director.NightLayerInSync, "night layer locked to the day piece");
            Assert.Greater(Sfx.Director.CurrentVolume, 0.05f, "audible");
            DayNight.SkipTo(10);
        }

        [UnityTest, Timeout(120000)]
        public IEnumerator Music_TownsInteriorsAndCamp_HaveTheirOwnPieces()
        {
            yield return Load("City_Valle");
            Calm();
            yield return WorldTests.Until(() => Sfx.CurrentTrack == "city_valle", 6f, "village theme");
            var inn = Interior.All.FirstOrDefault(i => i.template == "posada") ?? Interior.All.FirstOrDefault();
            Assert.IsNotNull(inn, "the village has houses to enter");
            string piece = MusicDirector.InteriorPiece(inn.template);
            GameManager.EnterInterior(inn);
            yield return WorldTests.Until(() => Sfx.CurrentTrack == piece, 6f, "interior music " + piece);
            Assert.Greater(Sfx.Ambience.Level("fire") + 0.001f, 0f);
            GameManager.ExitInterior();
            yield return WorldTests.Until(() => Sfx.CurrentTrack == "city_valle", 6f, "back to the village theme");
            var fire = Campfire.All.FirstOrDefault(f => f != null && f.gameObject.scene == Player.gameObject.scene);
            if (fire != null)
            {
                WorldTests.Teleport(Player, (Vector2)fire.transform.position + new Vector2(0, -1.4f));
                yield return WorldTests.Until(() => Sfx.CurrentTrack == "camp", 6f, "camp music by the fire");
            }
            yield return Load("City_Puerto");
            Calm();
            yield return WorldTests.Until(() => Sfx.CurrentTrack == "city_puerto", 6f, "port theme");
            yield return WorldTests.Until(() => Sfx.Ambience.Level("waves") > 0.2f, 8f, "waves in the port");
        }

        [UnityTest, Timeout(150000)]
        public IEnumerator Music_GoesToBattle_WhenEnemiesChase_AndBack()
        {
            yield return Load("World");
            Calm();
            WorldTests.Teleport(Player, TileIn('a'));
            yield return WorldTests.Until(() => Sfx.CurrentTrack == "region_a", 8f, "valley theme");
            var e = Object.FindObjectsByType<EnemyController>(FindObjectsSortMode.None).First(x => !x.isBoss && x.kind == EnemyKind.Orc);
            WorldTests.WakeFrozen(e);
            WorldTests.Teleport(e, (Vector2)Player.transform.position + new Vector2(2.5f, 0));
            e.enabled = true;
            yield return WorldTests.Until(() => Sfx.CurrentTrack == "combat", 6f, "battle music when an orc chases you");
            Assert.IsTrue(Sfx.Director.InCombat);
            e.rank = EnemyRank.Elite;
            e.health.Damage(new DamageInfo { amount = 9999, source = Team.Player });
            yield return WorldTests.Until(() => Sfx.CurrentTrack == "region_a", 10f, "the zone theme returns after the fight");

            var champ = Object.FindObjectsByType<EnemyController>(FindObjectsSortMode.None).First(x => !x.isBoss && x != e && !x.health.IsDead);
            WorldTests.WakeFrozen(champ);
            champ.rank = EnemyRank.Champion;
            WorldTests.Teleport(champ, (Vector2)Player.transform.position + new Vector2(-2.5f, 0));
            champ.enabled = true;
            yield return WorldTests.Until(() => Sfx.CurrentTrack == "combat_elite", 6f, "the harder battle theme for a champion");
            champ.health.Damage(new DamageInfo { amount = 99999, source = Team.Player });
        }

        [UnityTest, Timeout(150000)]
        public IEnumerator Music_EachBossHasItsOwnTheme()
        {
            yield return Load("World");
            var a = Object.FindObjectsByType<BossArena>(FindObjectsSortMode.None).FirstOrDefault(x => x.name == "BossArena_OrcChieftain");
            Assert.IsNotNull(a, "Gorgrak's arena");
            WorldTests.Teleport(Player, (Vector2)a.transform.position + new Vector2(0, -2.5f));
            yield return WorldTests.Until(() => a.Sealed, 10f, "arena seals");
            yield return WorldTests.Until(() => Sfx.CurrentTrack == "boss_K", 4f, "Gorgrak's war drums");
            Assert.IsTrue(Sfx.BossMusicPlaying);
            a.boss.health.Damage(new DamageInfo { amount = 99999, source = Team.Player });
            yield return WorldTests.Until(() => !a.Sealed, 6f, "arena opens");
            yield return WorldTests.Until(() => Sfx.CurrentTrack != null && !Sfx.CurrentTrack.StartsWith("boss"), 10f, "boss theme ends");
        }

        // ------------------------------------------------------------------ volumes
        [UnityTest, Timeout(120000)]
        public IEnumerator Volumes_MusicAndEffects_AreSeparate_AndMenusDuckTheMusic()
        {
            yield return Load("World");
            Calm();
            yield return WorldTests.Until(() => Sfx.CurrentTrack != null && Sfx.Director.CurrentVolume > 0.3f, 10f, "music fades in");
            Sfx.MusicVolume = 0.25f;
            yield return null; yield return null;
            Assert.LessOrEqual(Sfx.Director.CurrentVolume, 0.251f, "music volume caps the music");
            Assert.Greater(Sfx.Director.CurrentVolume, 0.05f);
            Sfx.MusicVolume = 0f;
            yield return null;
            Assert.AreEqual(0f, Sfx.Director.CurrentVolume, 1e-4f, "music muted");
            Sfx.MusicVolume = 0.6f;

            Sfx.SfxVolume = 0.4f;
            Sfx.Play("coin");
            var playing = Object.FindObjectsByType<AudioSource>(FindObjectsSortMode.None).Where(s => s.isPlaying && s.clip != null && s.clip.name.StartsWith("sfx_coin")).ToArray();
            Assert.IsNotEmpty(playing, "the coin sound plays");
            Assert.IsTrue(playing.All(s => s.volume <= 0.4001f), "effects volume caps the effects");
            Sfx.SfxVolume = 0f;
            Sfx.Play("coin");
            Assert.IsTrue(Object.FindObjectsByType<AudioSource>(FindObjectsSortMode.None).Where(s => s.isPlaying && s.clip != null && s.clip.name.StartsWith("sfx_") && s.time < 0.05f)
                .All(s => s.volume <= 0.0001f), "effects muted");
            Assert.AreEqual(0f, PlayerPrefs.GetFloat("vol_sfx", -1f), 1e-4f, "saved");
            Sfx.SfxVolume = 0.8f;

            // the pause menu: two volume rows, ← → change them
            GameManager.SetPaused(true);
            yield return null;
            var opts = Object.FindAnyObjectByType<VolumeOptions>();
            Assert.IsNotNull(opts, "pause menu has the volume options");
            float before = Sfx.MusicVolume;
            opts.Change(VolumeOptions.MusicRow, -1, false);
            Assert.AreEqual(before - 0.1f, Sfx.MusicVolume, 0.011f, "← lowers the music");
            yield return WorldTests.Until(() => Sfx.Director.Duck < 0.5f, 3f, "pause ducks the music");
            GameManager.SetPaused(false);
            yield return WorldTests.Until(() => Sfx.Director.Duck > 0.95f, 4f, "music comes back after the pause");
            WorldUI.ToggleInventory();
            yield return WorldTests.Until(() => Sfx.Director.Duck < 0.5f, 3f, "the bag ducks the music");
            WorldUI.CloseAll();
        }

        [UnityTest, Timeout(60000)]
        public IEnumerator Jingle_DucksTheMusicUnderIt()
        {
            yield return Load("World");
            Calm();
            yield return WorldTests.Until(() => Sfx.CurrentTrack != null, 6f, "music");
            Sfx.Jingle("levelup");
            yield return WorldTests.Until(() => Sfx.Director.Duck < 0.3f, 2f, "music ducks under the fanfare");
            yield return WorldTests.Until(() => Sfx.Director.Duck > 0.95f, 8f, "and comes back");
        }
    }
}
