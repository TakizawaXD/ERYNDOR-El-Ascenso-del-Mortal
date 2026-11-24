using System.Collections;
using System.Linq;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace WoodsGame.Tests
{
    /// <summary>Bosses with their own big sprites, lairs that seal, phases with new moves, the boss HUD, enemy auras and
    /// the per-region atmosphere. The last test saves a screenshot of every boss in its arena.</summary>
    public class BossTests
    {
        VirtualInput _in;
        // El Invocador ("Summoner") has its own hand-drawn sheet and logic from another feature (summoner_art.py, SummonerBoss);
        // these four use the 128 px sheets of Tools/CharAnim/bosses.py and BossBrain
        static readonly string[] BossPrefabs = { "OrcChieftain", "BloodMother", "DemonLord", "FrostColossus" };

        [UnitySetUp]
        public IEnumerator SetUp()
        {
            SaveSystem.Key = "woods_save_TEST"; SaveSystem.Delete();
            _in = new VirtualInput(); GameInput.Source = _in;
            GameManager.State = PlayerState.NewCharacter("knight"); SpawnDirector.Enabled = false;
            Time.timeScale = 1;
            yield return null;
        }

        [UnityTearDown]
        public IEnumerator TearDown()
        {
            SaveSystem.Delete(); SaveSystem.Key = "woods_save_v2"; SpawnDirector.Enabled = true;
            GameInput.Source = new KeyboardInput(); WorldUI.CloseAll(); Time.timeScale = 1;
            Sfx.BossMusic(false); BossHud.Hide();
            yield return null;
        }

        static T[] All<T>() where T : Object => Object.FindObjectsByType<T>(FindObjectsSortMode.None);
        static PlayerController Player => PlayerController.Current;

        static IEnumerator Load(string map)
        {
            SceneManager.LoadScene(map);
            yield return WorldTests.Until(() => SceneManager.GetActiveScene().name == map && Player != null, 10f, "load " + map);
            yield return new WaitForSeconds(0.4f);
        }

        static BossArena ArenaOf(string prefab) =>
            All<BossArena>().FirstOrDefault(a => a.name == "BossArena_" + prefab);

        static IEnumerator EnterArena(BossArena a)
        {
            Player.health.Init(999);
            WorldTests.Teleport(Player, (Vector2)a.transform.position + new Vector2(0, -a.size.y * 0.35f));
            yield return WorldTests.Until(() => a.Sealed, 8f, "arena " + a.name + " seals when the boss engages");
        }

        // ------------------------------------------------------------------ art
#if UNITY_EDITOR
        [Test]
        public void Bosses_HaveTheirOwnBigSprites_WithEveryAnimation()
        {
            var textures = new System.Collections.Generic.HashSet<Texture2D>();
            foreach (var name in BossPrefabs)
            {
                var prefab = UnityEditor.AssetDatabase.LoadAssetAtPath<GameObject>($"Assets/Game/Prefabs/{name}.prefab");
                Assert.IsNotNull(prefab, name + " prefab");
                var sr = prefab.GetComponentInChildren<SpriteRenderer>();
                Assert.IsNotNull(sr.sprite, name + " sprite");
                Assert.AreEqual(128f, sr.sprite.rect.height, name + " uses the 128 px boss cells");
                Assert.IsTrue(sr.sprite.texture.name.StartsWith("Boss"), name + " is drawn by bosses.py, not a recolour: " + sr.sprite.texture.name);
                Assert.IsTrue(textures.Add(sr.sprite.texture), name + " shares its art with another boss");
                Assert.IsNotNull(prefab.GetComponent<BossBrain>(), name + " has phases");
                var ctrl = prefab.GetComponentInChildren<Animator>().runtimeAnimatorController as UnityEditor.Animations.AnimatorController;
                Assert.IsNotNull(ctrl, name + " animator");
                var states = ctrl.layers[0].stateMachine.states.Select(s => s.state.name).ToArray();
                foreach (var st in new[] { "Idle", "Walk", "Attack", "HeavyAttack", "SpecialAttack", "CastSpell", "Hurt", "Death" })
                    Assert.Contains(st, states, name + " animation " + st);
            }
        }
#endif

        [Test]
        public void RegionalEnemies_HaveAnAura()
        {
            foreach (var t in new[] { "OrcFrost", "OrcBerserker", "DemonAsh", "DemonWraith", "BloodToxic", "BloodMagma", "KnightFallen" })
            {
                var p = GameAssets.I.EnemyPrefab(t);
                Assert.IsNotNull(p, t);
                Assert.IsNotNull(p.GetComponent<EnemyAura>(), t + " aura");
            }
        }

        // ------------------------------------------------------------------ arenas
        [UnityTest, Timeout(150000)]
        public IEnumerator World_HasALairForEveryBoss_WithItsDressing()
        {
            yield return Load("World");
            foreach (var name in new[] { "Summoner", "OrcChieftain", "BloodMother", "FrostColossus" })
            {
                var a = ArenaOf(name);
                Assert.IsNotNull(a, "arena for " + name);
                Assert.IsNotNull(a.boss, name + " arena knows its boss");
                Assert.IsTrue(a.Contains(a.boss.transform.position), name + " stands in his arena");
                Assert.IsNotNull(a.transform.Find("ArenaFloor"), name + " floor");
                Assert.GreaterOrEqual(a.GetComponentsInChildren<LightGlow>(true).Length, 8, name + " braziers and runes glow");
                Assert.GreaterOrEqual(a.GetComponentsInChildren<ArenaProp>(true).Length, 8, name + " animated runes, beams and fog");
                Assert.IsNotNull(a.GetComponentInChildren<EdgeCollider2D>(true), name + " rune wall");
                Assert.IsFalse(a.Sealed, name + " starts open");
            }
            yield return Load("Zone_MonteCeniza");
            Assert.IsNotNull(ArenaOf("DemonLord"), "Señor Demonio's lair in Monte Ceniza");
        }

        [UnityTest, Timeout(150000)]
        public IEnumerator Fight_SealsTheArena_ShowsTheBossHud_ChangesPhase_AndOpensOnVictory()
        {
            yield return Load("World");
            var a = ArenaOf("OrcChieftain");
            var boss = a.boss;
            var brain = boss.GetComponent<BossBrain>();
            yield return EnterArena(a);
            Assert.IsTrue(a.GetComponentInChildren<EdgeCollider2D>(true).enabled, "rune wall closes");
            Assert.IsTrue(BossHud.BarVisible, "ornate boss bar");
            StringAssert.Contains("GORGRAK", BossHud.BossName.ToUpper());
            Assert.IsTrue(BossHud.ObjectiveVisible, "objective on screen");
            StringAssert.Contains("Gorgrak", BossHud.ObjectiveText, "objective names the boss");
            Assert.IsTrue(Sfx.BossMusicPlaying || BossAssets.I.bossMusic == null, "boss theme");
            Assert.AreEqual(BossArena.Inside, a, "the arena's own atmosphere");

            // phase 2
            boss.health.Damage(new DamageInfo { amount = Mathf.CeilToInt(boss.health.maxHP * 0.4f), source = Team.Player });
            yield return WorldTests.Until(() => brain.Phase == 2, 5f, "phase 2");
            int done = brain.MovesDone;
            yield return WorldTests.Until(() => !brain.Busy, 6f, "phase shift ends");
            brain.ForceMove();
            yield return WorldTests.Until(() => brain.MovesDone > done, 6f, "a phase-2 move");
            // phase 3, then the kill
            yield return new WaitForSeconds(0.3f);
            boss.health.Damage(new DamageInfo { amount = Mathf.CeilToInt(boss.health.maxHP * 0.35f), source = Team.Player });
            yield return WorldTests.Until(() => brain.Phase == 3, 5f, "phase 3");
            yield return new WaitForSeconds(0.3f);
            for (int guard = 0; !boss.health.IsDead; guard++)
            {
                if (guard > 200) Assert.Fail("the boss never died (invulnerable?) hp " + boss.health.hp);
                Time.timeScale = 1;
                boss.health.Damage(new DamageInfo { amount = 50, source = Team.Player });
                yield return new WaitForSecondsRealtime(0.2f);
            }
            yield return WorldTests.Until(() => !a.Sealed, 4f, "arena opens after the victory");
            Assert.IsTrue(a.Cleared);
            Assert.IsFalse(a.GetComponentInChildren<EdgeCollider2D>(true).enabled, "rune wall gone");
            Assert.IsTrue(GameManager.State.Has("boss_K"), "victory saved");
            StringAssert.Contains("Completado", BossHud.ObjectiveText);
        }

        [UnityTest, Timeout(150000)]
        public IEnumerator EveryBoss_UsesItsSignatureMoves()
        {
            yield return Load("World");
            foreach (var name in new[] { "BloodMother", "FrostColossus" })
            {
                var a = ArenaOf(name);
                var brain = a.boss.GetComponent<BossBrain>();
                yield return EnterArena(a);
                int done = brain.MovesDone;
                brain.ForceMove();
                yield return WorldTests.Until(() => brain.MovesDone > done, 8f, name + " special move");
                Assert.IsNotEmpty(brain.LastMove);
                // walk out of the arena: dying/fleeing is simulated by moving the player far away -> the lair opens again
                WorldTests.Teleport(Player, (Vector2)a.transform.position + new Vector2(0, -30f));
                yield return WorldTests.Until(() => !a.Sealed, 4f, name + " arena reopens");
            }
        }

        // ------------------------------------------------------------------ atmosphere
        [UnityTest, Timeout(150000)]
        public IEnumerator EveryRegion_HasItsOwnLightFogAndParticles()
        {
            yield return Load("World");
            var wi = WorldInfo.Current;
            var seen = new System.Collections.Generic.Dictionary<char, Color>();
            foreach (var (r, at) in new[] { ('h', new Vector2(20, 120)), ('e', new Vector2(80, 148)), ('d', new Vector2(200, 50)), ('f', new Vector2(200, 130)), ('b', new Vector2(20, 105)) })
            {
                Vector2 p = at;
                // find a walkable tile of that region near the hint
                for (int k = 0; k < 400 && (wi.RegionAt(p) != r || !wi.Walkable(p)); k++) p = at + Random.insideUnitCircle * 12f;
                Assert.AreEqual(r, wi.RegionAt(p), "found region " + r);
                WorldTests.Teleport(Player, p);
                yield return WorldTests.Until(() => ZoneAtmosphere.Current != null && ZoneAtmosphere.Current.ActiveId == r.ToString(), 4f, "atmosphere of " + r);
                yield return new WaitForSeconds(2.8f);
                Assert.Greater(ZoneAtmosphere.Current.LiveMotes, 0, "particles in " + r);
                seen[r] = ZoneAtmosphere.Tint;
            }
            Assert.AreEqual(seen.Count, seen.Values.Distinct().Count(), "each region tints the light differently");
        }

        // ------------------------------------------------------------------ screenshots
        [UnityTest, Category("Screenshots"), Timeout(240000)]
        public IEnumerator Capture_EveryBossInItsArena()
        {
            foreach (var (map, prefab, file) in new[] { ("World", "Summoner", "boss_01_invocador"), ("World", "OrcChieftain", "boss_02_gorgrak"),
                         ("World", "BloodMother", "boss_03_madre_de_sangre"), ("World", "FrostColossus", "boss_04_coloso_de_escarcha"),
                         ("Zone_MonteCeniza", "DemonLord", "boss_05_senor_demonio") })
            {
                yield return Load(map);
                var a = ArenaOf(prefab);
                Assert.IsNotNull(a, prefab);
                yield return EnterArena(a);
                yield return new WaitForSeconds(2.2f);
                var brain = a.boss.GetComponent<BossBrain>();       // El Invocador fights with SummonerBoss instead
                if (brain != null) brain.ForceMove();
                yield return new WaitForSeconds(0.9f);
                yield return WorldScreenshots.Shot(file);
            }
        }

        [UnityTest, Category("Screenshots"), Timeout(240000)]
        public IEnumerator Capture_RegionAtmospheres()
        {
            yield return Load("World");
            var wi = WorldInfo.Current;
            foreach (var (r, at, file) in new[] { ('h', new Vector2(20, 118), "zona_bosque_corrupto"), ('e', new Vector2(80, 148), "zona_picos_nevados"),
                         ('d', new Vector2(200, 50), "zona_pantano_carmesi"), ('f', new Vector2(210, 130), "zona_arenas_rojas") })
            {
                Vector2 p = at;
                for (int k = 0; k < 400 && (wi.RegionAt(p) != r || !wi.Walkable(p)); k++) p = at + Random.insideUnitCircle * 10f;
                WorldTests.Teleport(Player, p);
                yield return new WaitForSeconds(3.5f);
                yield return WorldScreenshots.Shot(file);
            }
            yield return Load("Zone_MonteCeniza");
            yield return new WaitForSeconds(3.5f);
            yield return WorldScreenshots.Shot("zona_monte_ceniza");
        }
    }
}
