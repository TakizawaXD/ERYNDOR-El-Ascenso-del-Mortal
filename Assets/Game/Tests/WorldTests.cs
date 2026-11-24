using System;
using System.Collections;
using System.Linq;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace WoodsGame.Tests
{
    /// <summary>Plays the real open-world scene with scripted input and checks the game rules.</summary>
    public class WorldTests
    {
        VirtualInput _in;

        [UnitySetUp]
        public IEnumerator SetUp()
        {
            SaveSystem.Key = "woods_save_TEST";
            SaveSystem.Delete();
            _in = new VirtualInput();
            GameInput.Source = _in;
            GameManager.State = Deterministic(PlayerState.NewCharacter("knight"));
            SpawnDirector.Enabled = false;          // no random spawns unless a test asks for them
            Time.timeScale = 1;
            yield return null;
        }

        [UnityTearDown]
        public IEnumerator TearDown()
        {
            SaveSystem.Delete();
            SaveSystem.Key = "woods_save_v2";
            SpawnDirector.Enabled = true;
            GameInput.Source = new KeyboardInput();
            WorldUI.CloseAll();
            Time.timeScale = 1;
            yield return null;
        }

        // ------------------------------------------------------------ helpers
        /// <summary>No crits, no dodges: exact damage numbers.</summary>
        internal static PlayerState Deterministic(PlayerState s) { s.dex = 0; s.agi = 0; return s; }

        internal static IEnumerator LoadWorld() => LoadMap("World");

        /// <summary>Loads one of the maps (World, City_Valle, City_Ciudadela, City_Puerto, Zone_MonteCeniza).</summary>
        internal static IEnumerator LoadMap(string map)
        {
            SceneManager.LoadScene(map);
            yield return null; yield return null;
            yield return new WaitForSeconds(0.2f);
        }

        internal static IEnumerator Until(Func<bool> cond, float timeout, string what)
        {
            float t = 0;
            while (!cond())
            {
                t += Time.unscaledDeltaTime;
                if (t > timeout) Assert.Fail("Timed out waiting for: " + what);
                yield return null;
            }
        }

        static PlayerController Player => PlayerController.Current;
        static T[] All<T>() where T : UnityEngine.Object => UnityEngine.Object.FindObjectsByType<T>(FindObjectsSortMode.None);

        internal static void Teleport(Component c, Vector2 p)
        {
            var rb = c.GetComponent<Rigidbody2D>();
            if (rb) { rb.position = p; rb.linearVelocity = Vector2.zero; }
            c.transform.position = p;
        }

        IEnumerator Press(string action) { _in.Press(action); yield return null; yield return null; }

        IEnumerator Face(Vector2 d) { _in.move = d; yield return null; yield return null; _in.move = Vector2.zero; yield return null; }

        static void Kill(Health h) => h.Damage(new DamageInfo { amount = 9999, source = h.team == Team.Player ? Team.Enemy : Team.Player });

        static EnemyController NearbyFrozen(EnemyKind kind, Vector2 offset)
        {
            var e = All<EnemyController>().First(x => x.kind == kind && !x.isBoss);
            e.enabled = false;
            WakeFrozen(e);
            Teleport(e, (Vector2)Player.transform.position + offset);
            return e;
        }

        /// <summary>A disabled enemy never runs its culling, so turn its physics/animation back on by hand.</summary>
        internal static void WakeFrozen(EnemyController e)
        {
            var rb = e.GetComponent<Rigidbody2D>(); if (rb) rb.simulated = true;
            var an = e.GetComponentInChildren<Animator>(); if (an) an.enabled = true;
        }

        // ------------------------------------------------------------ tests
        [UnityTest]
        public IEnumerator Menu_NewGame_LoadsWorld()
        {
            SceneManager.LoadScene("MainMenu");
            yield return new WaitForSeconds(0.5f);
            yield return Press("Confirm");          // first option without a save = NUEVA PARTIDA -> class select
            Assert.IsNotNull(ClassSelect.Current, "class select open");
            yield return new WaitForSecondsRealtime(0.3f);
            yield return Press("Right");            // PALADIN
            Assert.AreEqual(1, ClassSelect.Current.Index);
            yield return Press("Confirm");
            yield return Until(() => SceneManager.GetActiveScene().name == MapDB.StartMap && Player != null, 6f, "start village after choosing a class");
            Assert.AreEqual("paladin", GameManager.State.classId);
            Assert.AreEqual(KnightClass.Get("paladin").vit, GameManager.State.vit);
            StringAssert.Contains("KnightPaladin", Player.GetComponentInChildren<Animator>().runtimeAnimatorController.name, "paladin sprites");
        }

        [UnityTest]
        public IEnumerator World_HasOpenWorldContent()
        {
            yield return LoadWorld();
            Assert.IsNotNull(Player, "player");
            Assert.IsNotNull(WorldInfo.Current, "world info");
            Assert.AreEqual(2, All<EnemyController>().Count(e => e.isBoss), "the two guardians (the Demon Lord waits in Monte Ceniza)");
            Assert.Greater(All<EnemyController>().Count(e => !e.isBoss), 80, "enemies");
            Assert.GreaterOrEqual(All<Campfire>().Length, 7, "campfires");
            Assert.GreaterOrEqual(All<MapGate>().Length, 10, "gates to the towns and the volcano");
            Assert.GreaterOrEqual(All<Chest>().Length, 20, "chests");
            Assert.GreaterOrEqual(All<SealBarrier>().Length, 4, "seal pieces");
            Assert.IsTrue(All<Sign>().All(s => s.text.Length > 10), "sign texts");
            yield return new WaitForSeconds(0.5f);
            Assert.IsTrue(GameManager.State.flags.Any(f => f.StartsWith("region_")), "start region discovered");
        }

        [UnityTest]
        public IEnumerator Sword_DamagesEnemy_ByLevel()
        {
            yield return LoadWorld();
            yield return Face(Vector2.down);
            var orc = NearbyFrozen(EnemyKind.Orc, Vector2.down * 0.9f);
            yield return new WaitForFixedUpdate();
            int hp0 = orc.health.hp;
            yield return Press("Attack");
            yield return new WaitForSeconds(0.35f);
            Assert.AreEqual(hp0 - GameManager.State.SwordDamage, orc.health.hp);
        }

        [UnityTest]
        public IEnumerator Kill_GivesXp_DropsCoins_AndEnemyWaitsToRespawn()
        {
            yield return LoadWorld();
            var orc = NearbyFrozen(EnemyKind.Orc, Vector2.right * 3f);
            Kill(orc.health);
            yield return new WaitForSeconds(0.3f);
            Assert.AreEqual(1, GameManager.State.kills);
            Assert.AreEqual(Progression.XpFor(orc), GameManager.State.xp);
            Assert.IsTrue(All<Pickup>().Any(p => p.kind == PickupKind.Coin && Vector2.Distance(p.transform.position, orc.transform.position) < 3), "coins");
            yield return new WaitForSeconds(1.4f);
            Assert.IsTrue(orc != null && !orc.gameObject.activeSelf, "hidden, not destroyed (it will respawn)");
            orc.Respawn();
            Assert.IsTrue(orc.gameObject.activeSelf && orc.health.hp == orc.maxHP, "respawned");
        }

        [UnityTest]
        public IEnumerator Campfire_SavesGame_AndDeathReturnsThere()
        {
            yield return LoadWorld();
            foreach (var e in All<EnemyController>()) e.enabled = false;
            var fire = All<Campfire>().OrderBy(f => Vector2.Distance(f.transform.position, Player.transform.position)).First();
            Teleport(Player, (Vector2)fire.transform.position + Vector2.down * 0.9f);
            yield return Face(Vector2.up);
            yield return Press("Interact");
            Assert.IsTrue(SaveSystem.HasSave, "saved");
            Assert.IsTrue(WorldUI.TalkOpen, "the camp menu opens (craft, storage, sleep)");
            WorldUI.CloseAll();
            var saved = SaveSystem.Load();
            Assert.Less(Vector2.Distance(new Vector2(saved.saveX, saved.saveY), fire.transform.position), 2f, "save spot at the fire");
            Teleport(Player, Player.transform.position + Vector3.right * 20);
            Kill(Player.health);
            yield return Until(() => GameManager.Ended, 4f, "death screen");
            yield return new WaitForSecondsRealtime(0.4f);
            yield return Press("Confirm");          // VOLVER AL CAMPAMENTO
            yield return Until(() => !GameManager.Ended && Player != null && Player.health.hp == Player.health.maxHP, 6f, "respawn");
            Assert.Less(Vector2.Distance(Player.transform.position, new Vector2(saved.saveX, saved.saveY)), 1.5f, "respawned at the campfire");
        }

        [UnityTest]
        public IEnumerator Shop_SellsIngredients_NotPotions()
        {
            yield return LoadWorld();
            var s = GameManager.State;
            s.coins = 100;
            int cloth = s.InBag("tela");
            WorldUI.OpenShop();
            Assert.IsTrue(WorldUI.PanelOpen);
            Assert.AreEqual(0f, Time.timeScale, "time stops in the shop");
            yield return new WaitForSecondsRealtime(0.3f);
            yield return Press("Confirm");          // TELA DE LINO 4
            Assert.AreEqual(96, s.coins);
            Assert.AreEqual(cloth + 1, s.InBag("tela"));
            Assert.IsFalse(CraftDB.Mats.Any(m => m.name.ToLowerInvariant().Contains("poción")), "no ready-made potions anywhere");
            WorldUI.CloseAll();
            Assert.AreEqual(1f, Time.timeScale);
        }

        [UnityTest]
        public IEnumerator Seal_OpensAfterBothGuardians()
        {
            yield return LoadWorld();
            var seal = All<SealBarrier>().First();
            Assert.IsTrue(seal.GetComponent<Collider2D>().enabled, "closed at start");
            foreach (var b in All<EnemyController>().Where(e => e.isBoss && e.bossFlag != "boss_B")) Kill(b.health);
            yield return null; yield return null;
            Assert.IsTrue(GameManager.State.Has("boss_K") && GameManager.State.Has("boss_Q"));
            Assert.IsFalse(seal.GetComponent<Collider2D>().enabled, "seal broken");
            Assert.IsTrue(Quests.All.First(q => q.id == "m1").Rewarded(GameManager.State), "quest m1 done");
        }

        [UnityTest]
        public IEnumerator DemonLord_Defeat_IsVictory_AndYouCanKeepExploring()
        {
            yield return LoadMap("Zone_MonteCeniza");
            var lord = All<EnemyController>().Single(e => e.bossFlag == "boss_B");
            Assert.AreEqual(70, lord.health.maxHP);
            Kill(lord.health);
            yield return Until(() => GameManager.Won, 6f, "victory");
            GameManager.KeepExploring();
            Assert.IsFalse(GameManager.Ended, "back to the world");
        }

        [UnityTest]
        public IEnumerator Map_And_Journal_Toggle()
        {
            yield return LoadWorld();
            yield return Press("Map");
            Assert.IsTrue(WorldUI.PanelOpen, "map open");
            yield return Press("Map");
            Assert.IsFalse(WorldUI.PanelOpen, "map closed");
            yield return Press("Journal");
            Assert.IsTrue(WorldUI.PanelOpen, "journal open");
            yield return Press("Pause");
            Assert.IsFalse(WorldUI.PanelOpen, "esc closes it");
            Assert.IsFalse(GameManager.Paused);
        }

        [UnityTest]
        public IEnumerator FarEnemies_Sleep_NearOnes_Wake()
        {
            yield return LoadWorld();
            yield return new WaitForSeconds(1.0f);
            var enemies = All<EnemyController>().Where(e => !e.isBoss).ToArray();
            var far = enemies.First(e => Vector2.Distance(e.transform.position, Player.transform.position) > 30);
            Assert.IsFalse(far.GetComponent<Rigidbody2D>().simulated, "far enemy asleep");
            Teleport(Player, (Vector2)far.transform.position + Vector2.left * 6f);
            yield return new WaitForSeconds(1.0f);
            Assert.IsTrue(far.GetComponent<Rigidbody2D>().simulated, "woke up when the player came close");
        }

        [UnityTest]
        public IEnumerator RangedEnemy_Shoots()
        {
            yield return LoadWorld();
            var bm = All<EnemyController>().First(e => e.ai == AIProfile.Kiter && e.ranged && !e.isBoss);
            bm.rangedCooldown = 0.5f;
            Teleport(Player, (Vector2)bm.transform.position + Vector2.left * 4f);
            yield return Until(() => All<Projectile>().Any(p => p.team == Team.Enemy), 8f, "spit projectile");
        }

        // ------------------------------------------------------------ RPG: classes, attributes, levels
        [UnityTest]
        public IEnumerator Classes_HaveTheirOwnSpritesAndStats()
        {
            yield return LoadWorld();
            var a = GameAssets.I;
            Assert.AreEqual(10, KnightClass.All.Length);
            for (int i = 0; i < KnightClass.All.Length; i++)
            {
                Assert.IsNotNull(a.classControllers[i], "controller " + KnightClass.All[i].id);
                Assert.Greater(a.classIdle[i].frames.Length, 0, "idle frames " + KnightClass.All[i].id);
            }
            var dark = PlayerState.NewCharacter("dark"); var pal = PlayerState.NewCharacter("paladin");
            Assert.Greater(dark.SwordDamage, pal.SwordDamage, "dark knight hits harder");
            Assert.Greater(pal.maxHP, dark.maxHP, "paladin has more life");
            Assert.Greater(PlayerState.NewCharacter("ranger").arrows, dark.arrows, "ranger starts with more arrows");
        }

        [UnityTest]
        public IEnumerator LevelUp_GivesAttributePoints_AndSheetSpendsThem()
        {
            yield return LoadWorld();
            var s = GameManager.State;
            Progression.AddXP(s.XpToNext);
            Assert.AreEqual(2, s.level);
            Assert.AreEqual(s.Class.pointsPerLevel, s.attrPoints);
            int str = s.str, dmg = s.SwordDamage;
            yield return Press("Character");
            Assert.IsTrue(WorldUI.PanelOpen, "sheet open");
            yield return new WaitForSecondsRealtime(0.3f);
            yield return Press("Confirm");          // FUERZA +1
            yield return Press("Confirm");          // FUERZA +1
            Assert.AreEqual(str + 2, s.str);
            Assert.Greater(s.SwordDamage, dmg, "more strength = more sword damage");
            yield return Press("Down");             // VITALIDAD
            int max = s.maxHP;
            yield return Press("Confirm");
            Assert.AreEqual(max + 2, s.maxHP, "vitality raises max HP");
            Assert.AreEqual(s.maxHP, Player.health.maxHP);
            yield return Press("Character");
            Assert.IsFalse(WorldUI.PanelOpen, "sheet closed");
        }

        [UnityTest]
        public IEnumerator Defense_ReducesDamage()
        {
            yield return LoadWorld();
            var s = GameManager.State; s.def = 6;                // armor 2
            int hp0 = Player.health.hp;
            Player.health.Damage(new DamageInfo { amount = 3, source = Team.Enemy });
            Assert.AreEqual(hp0 - 1, Player.health.hp, "3 damage - 2 armor");
        }

        [UnityTest]
        public IEnumerator Movement_AcceleratesSmoothly()
        {
            yield return LoadWorld();
            foreach (var e in All<EnemyController>()) e.enabled = false;
            var rb = Player.GetComponent<Rigidbody2D>();
            _in.move = Vector2.right;
            yield return new WaitForFixedUpdate(); yield return null;
            float early = rb.linearVelocity.x;
            yield return new WaitForSeconds(0.4f);
            float full = rb.linearVelocity.x;
            _in.move = Vector2.zero;
            Assert.Less(early, full * 0.8f, "ramps up instead of jumping to full speed");
            Assert.AreEqual(Player.walkSpeed * GameManager.State.SpeedMultiplier, full, 0.15f, "reaches walking speed");
        }

        // ------------------------------------------------------------ day / night
        [UnityTest]
        public IEnumerator DayNight_ThirtyMinutesEach_AndNightFalls()
        {
            yield return LoadWorld();
            Assert.AreEqual(720f, DayNight.GameMinutesPerSecond * 30 * 60, 0.01f, "12 game hours in 30 real minutes");
            Assert.IsNotNull(Camera.main.GetComponent<DayNightLighting>(), "lighting on the camera");
            var s = GameManager.State;
            s.clock = 17 * 60 + 59;
            bool? phase = null;
            System.Action<bool> h = n => phase = n;
            DayNight.PhaseChanged += h;
            DayNight.Advance(2f);
            DayNight.PhaseChanged -= h;
            Assert.IsTrue(DayNight.IsNight); Assert.AreEqual(true, phase, "night event");
            Assert.Less(DayNight.Ambient(s.clock).b + 0.01f, 1f);
            int day = s.day;
            DayNight.SkipTo(DayNight.DawnHour);
            Assert.IsFalse(DayNight.IsNight); Assert.AreEqual(day + 1, s.day, "a new day");
            Assert.AreEqual(Color.white, DayNight.Ambient(12 * 60), "noon is untinted");
        }

        // ------------------------------------------------------------ living world
        [UnityTest]
        public IEnumerator Spawner_UsesRegionTables_DayAndNight()
        {
            yield return LoadWorld();
            var wi = WorldInfo.Current; var sd = SpawnDirector.Current;
            Assert.IsNotNull(sd, "spawn director in the world");
            foreach (var t in SpawnDirector.Table.Values)
                foreach (var id in t.day.Concat(t.night)) Assert.IsNotNull(GameAssets.I.EnemyPrefab(id), "prefab " + id);
            int made = 0;
            foreach (bool night in new[] { false, true })
            {
                for (int k = 0; k < 4; k++)
                {
                    var e = sd.TrySpawn(Player, wi, 1, night);
                    if (e == null) continue;
                    made++;
                    var t = SpawnDirector.Table[wi.RegionAt(e.transform.position)];
                    CollectionAssert.Contains(night ? t.night : t.day, e.typeId, "regional " + (night ? "night" : "day") + " type");
                    Assert.IsTrue(e.spawned);
                }
            }
            Assert.Greater(made, 0, "something spawned");
        }

        [UnityTest]
        public IEnumerator Threat_GrowsWithKills_SpawnsMoreAndStronger()
        {
            yield return LoadWorld();
            var s = GameManager.State;
            Assert.AreEqual(1, s.Threat);
            s.kills = 60;
            Assert.AreEqual(6, s.Threat);
            Assert.Greater(SpawnDirector.Cap(6, false), SpawnDirector.Cap(1, false), "more enemies at once");
            Assert.Less(SpawnDirector.Interval(6, false), SpawnDirector.Interval(1, false), "faster spawns");
            Assert.Greater(SpawnDirector.EliteChance(6), SpawnDirector.EliteChance(1), "more elites");
            EnemyController elite = null;
            for (int k = 0; k < 10 && elite == null; k++) elite = SpawnDirector.Current.TrySpawn(Player, WorldInfo.Current, s.Threat, false, EnemyRank.Elite);
            Assert.IsNotNull(elite, "elite spawned");
            var basePrefab = GameAssets.I.EnemyPrefab(elite.typeId).GetComponent<EnemyController>();
            Assert.Greater(elite.health.maxHP, basePrefab.maxHP * 2, "elite is much tougher");
            StringAssert.Contains("PODEROSO", elite.displayName);
            Assert.Greater(elite.xpReward, basePrefab.xpReward);
        }

        [UnityTest]
        public IEnumerator Sunrise_BurnsNightCreatures()
        {
            yield return LoadWorld();
            GameManager.State.clock = 23 * 60;
            DayNight.Advance(0.1f);
            EnemyController wraith = null;
            for (int k = 0; k < 30 && wraith == null; k++)
            {
                var e = SpawnDirector.Current.TrySpawn(Player, WorldInfo.Current, 1, true);
                if (e != null && SpawnDirector.NightOnly.Contains(e.typeId)) wraith = e;
            }
            Assert.IsNotNull(wraith, "a night creature");
            DayNight.SkipTo(DayNight.DawnHour);
            yield return null;
            Assert.IsTrue(wraith == null, "burned by the sun");
        }

        [UnityTest]
        public IEnumerator EnemyTypes_HaveTheirOwnAI()
        {
            yield return LoadWorld();
            AIProfile Ai(string id) => GameAssets.I.EnemyPrefab(id).GetComponent<EnemyController>().ai;
            Assert.AreEqual(AIProfile.Pack, Ai("Orc"));
            Assert.AreEqual(AIProfile.Charger, Ai("OrcBerserker"));
            Assert.AreEqual(AIProfile.Skirmisher, Ai("OrcDesert"));
            Assert.AreEqual(AIProfile.Brute, Ai("OrcFrost"));
            Assert.AreEqual(AIProfile.Kiter, Ai("BloodMonster"));
            Assert.AreEqual(AIProfile.Ambusher, Ai("BloodToxic"));
            Assert.AreEqual(AIProfile.Bomber, Ai("BloodMagma"));
            Assert.AreEqual(AIProfile.Caster, Ai("Demon"));
            Assert.AreEqual(AIProfile.Wraith, Ai("DemonWraith"));
            Assert.AreEqual(AIProfile.Duelist, Ai("KnightFallen"));
            // residents are regional: desert orcs in the red sands, frost orcs in the peaks
            var residents = All<EnemyController>().Where(e => !e.isBoss && !e.spawned).ToArray();
            Assert.IsTrue(residents.Any(e => e.typeId == "OrcDesert"), "desert orcs");
            Assert.IsTrue(residents.Any(e => e.typeId == "OrcFrost"), "frost orcs");
            Assert.IsTrue(residents.All(e => e.activeAt == ActiveTime.Day), "map residents are day creatures");
            // an ambusher starts hidden and a wraith drifts through walls
            var amb = residents.First(e => e.ai == AIProfile.Ambusher);
            Assert.IsTrue(amb.Hidden, "ambusher hidden");
            var w = UnityEngine.Object.Instantiate(GameAssets.I.EnemyPrefab("DemonWraith"), Player.transform.position + Vector3.right * 30, Quaternion.identity);
            Assert.IsTrue(w.GetComponent<Collider2D>().isTrigger, "wraith passes through walls");
            UnityEngine.Object.Destroy(w);
        }

        [UnityTest]
        public IEnumerator Charger_RamsThePlayer()
        {
            yield return LoadWorld();
            foreach (var e in All<EnemyController>()) e.enabled = false;
            var go = UnityEngine.Object.Instantiate(GameAssets.I.EnemyPrefab("OrcBerserker"), Player.transform.position + Vector3.right * 4f, Quaternion.identity);
            var c = go.GetComponent<EnemyController>(); c.spawned = true;
            int hp0 = Player.health.hp;
            yield return Until(() => Player.health.hp < hp0, 8f, "berserker charge hits");
            UnityEngine.Object.Destroy(go);
        }

        // ------------------------------------------------------------ houses
        [UnityTest]
        public IEnumerator House_EnterExplore_AndLeave()
        {
            yield return LoadMap("City_Valle");
            foreach (var e in All<EnemyController>()) e.enabled = false;
            Assert.GreaterOrEqual(All<Interior>().Length, 6, "every house of the village has an interior");
            Assert.IsTrue(All<Interior>().Any(i => i.template == "posada") && All<Interior>().Any(i => i.template == "herreria"), "special rooms");
            var door = All<HouseDoor>().OrderBy(d => Vector2.Distance(d.transform.position, Player.transform.position)).First();
            Teleport(Player, (Vector2)door.transform.position + Vector2.down * 0.75f);
            yield return Face(Vector2.up);
            yield return Press("Interact");
            yield return Until(() => Interior.Current == door.interior, 3f, "inside the house");
            yield return new WaitForSeconds(0.5f);
            Assert.IsTrue(door.interior.bounds.Contains(Player.transform.position), "player in the room");
            Assert.IsTrue(All<Bed>().Any(b => door.interior.bounds.Contains(b.transform.position)) ||
                          All<Chest>().Any(b => door.interior.bounds.Contains(b.transform.position)), "furnished");
            // walk out over the door mat
            _in.move = Vector2.down;
            yield return Until(() => Interior.Current == null, 4f, "back outside");
            _in.move = Vector2.zero;
            yield return new WaitForSeconds(0.4f);
            Assert.Less(Vector2.Distance(Player.transform.position, door.transform.position), 2f, "in front of the house");
        }

        [UnityTest]
        public IEnumerator Bed_SleepsUntilDawn_AndSaves()
        {
            yield return LoadMap("City_Valle");
            var s = GameManager.State;
            s.clock = 21 * 60; int day = s.day;
            Player.health.Damage(new DamageInfo { amount = 4, source = Team.Enemy });
            var bed = All<Bed>().First();
            GameManager.Sleep((Vector2)bed.transform.position + Vector2.down);
            yield return Until(() => !DayNight.IsNight && SaveSystem.HasSave && !GameManager.Transitioning, 5f, "morning");
            Assert.AreEqual(day + 1, s.day);
            Assert.AreEqual(DayNight.DawnHour, DayNight.Hour);
            Assert.AreEqual(Player.health.maxHP, Player.health.hp, "rested");
        }

        // ------------------------------------------------------------ equipment
        [UnityTest]
        public IEnumerator Equipment_Catalog_IsVariedAndHasArt()
        {
            yield return LoadWorld();
            var kinds = ItemDB.All.Where(i => i.slot == ItemSlot.Weapon).Select(i => i.kind).Distinct().ToArray();
            foreach (var k in new[] { WeaponKind.Sword, WeaponKind.Greatsword, WeaponKind.Katana, WeaponKind.Rapier, WeaponKind.Dagger, WeaponKind.Spear, WeaponKind.Axe, WeaponKind.Hammer })
                CollectionAssert.Contains(kinds, k, "melee kind " + k);
            Assert.GreaterOrEqual(ItemDB.All.Count(i => i.slot == ItemSlot.Bow), 5, "bows and crossbow");
            Assert.GreaterOrEqual(ItemDB.All.Count(i => i.slot == ItemSlot.Armor), 8, "armours");
            Assert.IsTrue(ItemDB.All.Any(i => i.rarity == Rarity.Legendary), "legendaries");
            foreach (var i in ItemDB.All) Assert.IsNotNull(GameAssets.I.ItemIcon(i.icon), "icon " + i.id);
            foreach (var n in GameAssets.I.weaponFxNames) Assert.Greater(GameAssets.I.WeaponFxFrames(n).Length, 2, "fx " + n);
        }

        [UnityTest]
        public IEnumerator Equip_ChangesStats()
        {
            yield return LoadWorld();
            var s = GameManager.State;
            int dmg = s.SwordDamage, armor = s.Armor, hp = s.maxHP;
            Assert.IsTrue(s.AddItem("greatsword"));
            Assert.IsFalse(s.AddItem("greatsword"), "one of each");
            Assert.IsTrue(s.Equip("greatsword"));
            Assert.AreEqual("greatsword", s.weapon);
            Assert.Contains("sword_long", s.inventory, "old weapon back in the bag");
            Assert.AreEqual(dmg + 3, s.SwordDamage, "greatsword +4 vs long sword +1");
            s.AddItem("armor_plate"); s.Equip("armor_plate");
            Assert.AreEqual(armor + 1, s.Armor, "plate 3 vs chain 2");
            Assert.AreEqual(hp + 2, s.maxHP, "plate +4 hp vs chain +2");
            Assert.Less(s.SpeedMultiplier, 1f, "plate is heavy");
        }

        [UnityTest]
        public IEnumerator Inventory_EquipsWithTheKeyboard()
        {
            yield return LoadWorld();
            var s = GameManager.State;
            s.AddItem("katana");
            yield return Press("Inventory");
            Assert.IsTrue(WorldUI.PanelOpen, "inventory open");
            yield return new WaitForSecondsRealtime(0.2f);
            for (int i = 0; i < 3; i++) yield return Press("Right");      // slots 0-2 = equipped, 3 = first bag item
            yield return Press("Confirm");
            Assert.AreEqual("katana", s.weapon, "katana equipped");
            yield return Press("Inventory");
            Assert.IsFalse(WorldUI.PanelOpen, "closed");
            // the katana swings faster than the long sword
            Assert.Less(ItemDB.Get("katana").Style.windup, ItemDB.Get("sword_long").Style.windup);
            Assert.Greater(ItemDB.Get("spear").Style.reach, ItemDB.Get("sword_long").Style.reach, "spears reach further");
        }

        [UnityTest]
        public IEnumerator Champion_DropsEquipment()
        {
            yield return LoadWorld();
            foreach (var e in All<EnemyController>()) e.enabled = false;
            var go = UnityEngine.Object.Instantiate(GameAssets.I.EnemyPrefab("Orc"), Player.transform.position + Vector3.right * 3f, Quaternion.identity);
            var c = go.GetComponent<EnemyController>(); c.spawned = true; c.Setup(EnemyRank.Champion, 3, true); c.enabled = false;
            yield return null;
            Kill(c.health);
            yield return new WaitForSeconds(0.2f);
            var drop = All<Pickup>().FirstOrDefault(p => p.kind == PickupKind.Item);
            Assert.IsNotNull(drop, "equipment dropped");
            Assert.GreaterOrEqual((int)ItemDB.Get(drop.itemId).rarity, (int)Rarity.Rare, "champion loot is at least rare");
            Teleport(Player, drop.transform.position);
            yield return Until(() => GameManager.State.Owns(drop.itemId), 3f, "picked up");
        }

        [UnityTest]
        public IEnumerator Blacksmith_SellsWeapons()
        {
            yield return LoadMap("City_Valle");
            Assert.IsTrue(All<ShopStall>().Any(s => s.smith), "anvils are blacksmiths");
            var s = GameManager.State; s.coins = 500;
            WorldUI.OpenSmith();
            Assert.IsTrue(WorldUI.PanelOpen);
            yield return new WaitForSecondsRealtime(0.3f);
            int owned = s.inventory.Count;
            yield return Press("Confirm");
            Assert.AreEqual(owned + 1, s.inventory.Count, "bought an item");
            Assert.Less(s.coins, 500);
            WorldUI.CloseAll();
        }

        // ------------------------------------------------------------ collisions
        [UnityTest, Timeout(150000)]
        public IEnumerator SolidObjects_CannotBeWalkedThrough()
        {
            yield return LoadWorld();
            foreach (var e in All<EnemyController>()) e.enabled = false;
            var p = Player;
            var rb = p.GetComponent<Rigidbody2D>();
            int tested = 0;
            foreach (var prefix in new[] { "castle_wall", "house_", "castle_tower", "watchtower", "mountain_big", "mountain_snow", "mesa", "ruin_wall", "rock_big", "well" })
            {
                var cands = All<SpriteRenderer>().Where(s => s.gameObject.name.StartsWith(prefix) && s.GetComponent<Collider2D>() != null).ToArray();
                Assert.Greater(cands.Length, 0, "found " + prefix);
                bool done = false;
                foreach (var sr in cands.Take(12))
                {
                    var foot = (Vector2)sr.transform.position;
                    float h = sr.bounds.size.y;
                    var north = foot + new Vector2(0, h + 0.7f);
                    var south = foot + new Vector2(0, -0.9f);
                    // need open ground on both sides to make a fair test
                    if (Physics2D.OverlapCircle(north + Vector2.up * 0.2f, 0.45f) || Physics2D.OverlapCircle(south + Vector2.up * 0.2f, 0.45f)) continue;
                    var wi = WorldInfo.Current;
                    if (!wi.Walkable(north) || !wi.Walkable(south)) continue;
                    // from the north, walking down: the feet must stay in the top margin of the sprite
                    Teleport(p, north);
                    _in.move = Vector2.down;
                    yield return new WaitForSeconds(1.6f);
                    _in.move = Vector2.zero;
                    Assert.Greater(p.transform.position.y, foot.y + h - 1.6f, $"{sr.name}: walked into it from the north");
                    // from the south, walking up: stopped at the base
                    Teleport(p, south);
                    _in.move = Vector2.up;
                    yield return new WaitForSeconds(1.2f);
                    _in.move = Vector2.zero;
                    Assert.Less(p.transform.position.y, foot.y + 0.3f, $"{sr.name}: walked into it from the south");
                    tested++; done = true;
                    break;
                }
                if (!done) Debug.Log("[Collision test] no open spot around " + prefix);
            }
            Assert.GreaterOrEqual(tested, 6, "tested enough obstacle types");
        }

        [UnityTest, Timeout(150000)]
        public IEnumerator Rolling_DoesNotTunnelThroughWalls()
        {
            yield return LoadWorld();
            foreach (var e in All<EnemyController>()) e.enabled = false;
            var p = Player;
            var wall = All<SpriteRenderer>().Where(s => s.gameObject.name.StartsWith("castle_wall") && s.GetComponent<Collider2D>() != null)
                .First(s => !Physics2D.OverlapCircle((Vector2)s.transform.position + new Vector2(0, -0.7f), 0.4f));
            Vector2 foot = wall.transform.position;
            for (int i = 0; i < 4; i++)
            {
                Teleport(p, foot + new Vector2(0, -0.9f));
                yield return Face(Vector2.up);
                _in.move = Vector2.up;
                _in.Press("Roll");
                yield return new WaitForSeconds(0.7f);
                _in.move = Vector2.zero;
                Assert.Less(p.transform.position.y, foot.y + 0.3f, "roll went through the wall");
            }
        }

        // ------------------------------------------------------------ animals
#if UNITY_EDITOR
        [UnityTest, Timeout(60000)]
        public IEnumerator Cats_TameOnesLetYouPet_ShyOnesRun()
        {
            yield return LoadWorld();
            foreach (var e in All<EnemyController>()) e.enabled = false;
            var p = Player;
            var tamePrefab = UnityEditor.AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Game/Prefabs/Animal_catgrey.prefab");
            var shyPrefab = UnityEditor.AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Game/Prefabs/Animal_cat_shy.prefab");
            Assert.IsNotNull(tamePrefab, "grey & white kitten prefab"); Assert.IsNotNull(shyPrefab, "shy kitten prefab");
            // tame: E strokes it (petting animation, the knight holds still), then it follows
            var tame = UnityEngine.Object.Instantiate(tamePrefab, (Vector2)p.transform.position + Vector2.right * 0.9f, Quaternion.identity).GetComponent<Animal>();
            yield return new WaitForSeconds(0.2f);
            Teleport(p, (Vector2)tame.transform.position + Vector2.left * 0.8f);
            yield return Face(Vector2.right);
            yield return Press("Interact");
            Assert.IsTrue(tame.Petting, "being stroked");
            Assert.IsNotNull(tame.pet, "has petting frames"); Assert.AreEqual(2, tame.pet.Length);
            yield return Until(() => tame.Following, 4f, "follows after the cuddle");
            Teleport(p, (Vector2)p.transform.position + Vector2.left * 4f);
            yield return new WaitForSeconds(2.5f);
            Assert.Less(Vector2.Distance(tame.transform.position, p.transform.position), 2.5f, "trots after the knight");
            // shy: cannot be stroked and runs away
            var shy = UnityEngine.Object.Instantiate(shyPrefab, (Vector2)p.transform.position + Vector2.down * 3.5f, Quaternion.identity).GetComponent<Animal>();
            Assert.IsFalse(shy.GetComponent<PetAnimal>().CanInteract, "shy cats can't be petted");
            Teleport(shy, (Vector2)p.transform.position + Vector2.down * 1.6f);
            float d0 = Vector2.Distance(shy.transform.position, p.transform.position);
            yield return new WaitForSeconds(1.0f);
            Assert.Greater(Vector2.Distance(shy.transform.position, p.transform.position), d0 + 0.8f, "ran away from the knight");
            // nobody can hurt a kitten
            int hp = shy.GetComponent<Health>().hp;
            shy.GetComponent<Health>().Damage(new DamageInfo { amount = 5, source = Team.Player });
            Assert.AreEqual(hp, shy.GetComponent<Health>().hp);
        }
#endif
    }
}
