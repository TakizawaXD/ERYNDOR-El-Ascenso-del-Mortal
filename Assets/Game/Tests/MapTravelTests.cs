using System.Collections;
using System.Linq;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace WoodsGame.Tests
{
    /// <summary>Several loaded maps: towns and Monte Ceniza are their own scenes, gates travel between them keeping the
    /// whole PlayerState, the save remembers the map, defeated residents stay defeated, and M shows local + world maps.</summary>
    public class MapTravelTests
    {
        VirtualInput _in;
        static readonly string[] Towns = { "City_Valle", "City_Ciudadela", "City_Puerto" };

        [UnitySetUp]
        public IEnumerator SetUp()
        {
            SaveSystem.Key = "woods_save_TEST";
            SaveSystem.Delete();
            _in = new VirtualInput();
            GameInput.Source = _in;
            GameManager.State = WorldTests.Deterministic(PlayerState.NewCharacter("knight"));
            SpawnDirector.Enabled = false;
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

        static PlayerController Player => PlayerController.Current;
        static T[] All<T>() where T : Object => Object.FindObjectsByType<T>(FindObjectsSortMode.None);
        static string Scene => SceneManager.GetActiveScene().name;

        internal static IEnumerator Load(string map)
        {
            SceneManager.LoadScene(map);
            yield return null; yield return null;
            yield return new WaitForSeconds(0.3f);
        }

        static IEnumerator Arrive(string map)
        {
            yield return WorldTests.Until(() => Scene == map && Player != null && !GameManager.Transitioning, 8f, "arrive in " + map);
            yield return new WaitForSeconds(0.2f);
        }

        IEnumerator WalkInto(MapGate g, float timeout = 6f)
        {
            var target = (Vector2)g.transform.position;
            string from = Scene;
            float t = 0;
            while (Scene == from && t < timeout)
            {
                if (Player != null) _in.move = (target - (Vector2)Player.transform.position).normalized;
                t += Time.deltaTime;
                yield return null;
            }
            _in.move = Vector2.zero;
            Assert.AreNotEqual(from, Scene, $"walking into gate {g.id} of {from} loads another map");
        }

        // ------------------------------------------------------------------ tests
        [Test]
        public void Catalog_HasWorldTownsAndZone_AndEveryGateHasItsPair()
        {
            Assert.IsNotNull(MapDB.Get("World"));
            foreach (var t in Towns) Assert.AreEqual("city", MapDB.Get(t)?.kind, t);
            Assert.AreEqual("zone", MapDB.Get("Zone_MonteCeniza")?.kind);
            Assert.GreaterOrEqual(MapDB.Gates.Count, 20);
            foreach (var g in MapDB.Gates)
            {
                var back = MapDB.Gate(g.toMap, g.toGate);
                Assert.IsNotNull(back, $"{g.map}:{g.id} -> {g.toMap}:{g.toGate} exists");
                Assert.AreEqual(g.map, back.toMap, $"{g.toMap}:{g.toGate} leads back to {g.map}");
                Assert.AreEqual(g.id, back.toGate, $"{g.toMap}:{g.toGate} leads back to gate {g.id}");
            }
            foreach (var m in MapDB.Maps)
                Assert.GreaterOrEqual(SceneUtility.GetBuildIndexByScenePath($"Assets/Game/Scenes/{m.id}.unity"), 0, m.id + " in Build Settings");
        }

        [UnityTest]
        public IEnumerator NewGame_StartsInTheVillage_WithItsOwnMap()
        {
            GameManager.NewGame("knight");
            yield return Arrive("City_Valle");
            var wi = WorldInfo.Current;
            Assert.AreEqual("City_Valle", wi.mapId);
            Assert.AreEqual("city", wi.kind);
            Assert.IsNotNull(wi.mapSprite, "local map picture");
            Assert.AreEqual("City_Valle", GameManager.State.map);
            Assert.GreaterOrEqual(All<Interior>().Length, 6, "the village houses have interiors");
            Assert.AreEqual(4, All<MapGate>().Length, "village gates");
            Assert.GreaterOrEqual(All<ShopStall>().Length, 2, "market");
            Assert.GreaterOrEqual(All<Campfire>().Length, 1, "camp");
            Assert.IsNull(Object.FindAnyObjectByType<SpawnDirector>(), "no random monsters inside the village");
        }

        [UnityTest]
        public IEnumerator Every_Town_IsBigger_HasGates_Houses_AndInteriors()
        {
            foreach (var t in Towns)
            {
                yield return Load(t);
                var def = MapDB.Get(t);
                Assert.AreEqual(t, WorldInfo.Current.mapId);
                Assert.GreaterOrEqual(def.w * def.h, 3500, t + " is a big map");
                var gates = All<MapGate>();
                Assert.AreEqual(MapDB.Gates.Count(g => g.map == t), gates.Length, t + " gates");
                Assert.IsTrue(gates.All(g => g.toMap == "World" && g.GetComponent<BoxCollider2D>().isTrigger), t + " gates lead to the world");
                Assert.GreaterOrEqual(All<HouseDoor>().Length, 5, t + " houses with a door");
                Assert.AreEqual(All<HouseDoor>().Length, All<Interior>().Length, t + " one interior per house");
                Assert.GreaterOrEqual(All<Sign>().Count(s => s.GetComponent<NpcIdle>() != null), 3, t + " townsfolk");
                Assert.IsNotNull(Player, t + " player");
                foreach (var g in gates)
                {
                    var hits = Physics2D.OverlapCircleAll(g.arrival + Vector2.up * 0.2f, 0.25f).Where(c => !c.isTrigger).ToArray();
                    Assert.AreEqual(0, hits.Length, $"{t} gate {g.id}: arrival point is free ({string.Join(",", hits.Select(h => h.name))})");
                }
            }
            yield return Load("World");
            Assert.AreEqual(0, All<Interior>().Length, "houses are entered in their towns, not in the world");
            Assert.AreEqual(0, All<HouseDoor>().Length);
            foreach (var g in All<MapGate>())
            {
                var hits = Physics2D.OverlapCircleAll(g.arrival + Vector2.up * 0.2f, 0.25f).Where(c => !c.isTrigger).ToArray();
                Assert.AreEqual(0, hits.Length, $"world gate {g.id}: arrival point is free ({string.Join(",", hits.Select(h => h.name))})");
                Assert.IsTrue(WorldInfo.Current.Walkable(g.arrival), $"world gate {g.id}: arrival on open ground");
            }
        }

        [UnityTest]
        public IEnumerator Walking_ThroughTheTownGate_LoadsTheWorld_AndBack()
        {
            yield return Load("City_Valle");
            var s = GameManager.State;
            s.coins = 321; s.Set("test_flag"); s.AddItem("katana_moon"); s.clock = 10 * 60;
            Player.health.Damage(new DamageInfo { amount = 3, source = Team.Enemy });
            int hp = Player.health.hp;
            var gate = All<MapGate>().First(g => g.id == "N0");
            WorldTests.Teleport(Player, gate.arrival);
            yield return new WaitForSeconds(0.7f);
            yield return WalkInto(gate);
            yield return Arrive("World");
            var back = MapGate.Find("City_Valle:N0");
            Assert.IsNotNull(back);
            Assert.Less(Vector2.Distance(Player.transform.position, back.arrival), 1.2f, "appears outside the village's north gate");
            Assert.AreEqual(321, GameManager.State.coins, "coins travel");
            Assert.IsTrue(GameManager.State.Has("test_flag"), "flags travel");
            Assert.IsTrue(GameManager.State.Owns("katana_moon"), "inventory travels");
            Assert.AreEqual(hp, Player.health.hp, "health travels");
            Assert.GreaterOrEqual(DayNight.Clock, 10 * 60, "the clock keeps going");
            Assert.AreEqual("World", GameManager.State.map);
            // and back in through the same gate
            yield return new WaitForSeconds(0.7f);
            yield return WalkInto(back);
            yield return Arrive("City_Valle");
            Assert.Less(Vector2.Distance(Player.transform.position, gate.arrival), 1.2f, "back at the village's north gate");
        }

        [UnityTest]
        public IEnumerator Travel_ReachesEveryTown_FromItsWorldGates()
        {
            yield return Load("World");
            foreach (var g in MapDB.Gates.Where(g => g.map == "World"))
            {
                GameManager.Travel(g.toMap, g.toGate);
                yield return Arrive(g.toMap);
                var arrival = MapDB.Gate(g.toMap, g.toGate).arrival;
                Assert.Less(Vector2.Distance(Player.transform.position, arrival), 1f, $"{g.id} -> {g.toMap}:{g.toGate}");
                GameManager.Travel("World", g.id);
                yield return Arrive("World");
                Assert.Less(Vector2.Distance(Player.transform.position, g.arrival), 1f, $"back to {g.id}");
            }
        }

        [UnityTest]
        public IEnumerator Save_RemembersTheMap_AndContinueReturnsThere()
        {
            yield return Load("City_Puerto");
            var fire = All<Campfire>().First();
            fire.Rest(Player);
            WorldUI.CloseAll();
            Vector2 spot = fire.Spot;
            var saved = SaveSystem.Load();
            Assert.AreEqual("City_Puerto", saved.saveMap, "the save remembers the map");
            GameManager.Travel("World", "City_Puerto:W0");
            yield return Arrive("World");
            GameManager.Continue();
            yield return WorldTests.Until(() => Scene == "City_Puerto" && Player != null && !GameManager.Transitioning, 8f, "continue in the port");
            yield return new WaitForSeconds(0.2f);
            Assert.Less(Vector2.Distance(Player.transform.position, spot), 1.2f, "at the port's camp");
            // dying in the world sends you back to the last camp, in its map
            GameManager.Travel("World", "City_Puerto:E0");
            yield return Arrive("World");
            GameManager.Respawn();
            yield return WorldTests.Until(() => Scene == "City_Puerto" && Player != null && !GameManager.Transitioning, 8f, "respawn in the port");
        }

        [UnityTest]
        public IEnumerator OldSave_InsideATown_ContinuesInTheVillage()
        {
            var s = GameManager.State;
            s.saveX = 124; s.saveY = 50; s.saveMap = "";          // an old single-map save next to the old village camp
            Assert.AreEqual("City_Valle", GameManager.ResumeMap(s));
            s.saveX = 80; s.saveY = 80; s.saveMap = "";
            Assert.AreEqual("World", GameManager.ResumeMap(s));
            yield return null;
        }

        [UnityTest]
        public IEnumerator DefeatedResidents_StayDefeated_WhenYouComeBack()
        {
            yield return Load("World");
            var orc = All<EnemyController>().First(e => !e.isBoss && !e.spawned && e.kind == EnemyKind.Orc);
            Vector2 home = orc.Home;
            orc.health.Damage(new DamageInfo { amount = 9999, source = Team.Player });
            yield return new WaitForSeconds(1.5f);
            Assert.Greater(GameManager.DefeatedFor("World", home), 100f, "respawn timer recorded");
            GameManager.Travel("City_Valle", "N0");
            yield return Arrive("City_Valle");
            GameManager.Travel("World", "City_Valle:N0");
            yield return Arrive("World");
            yield return null;
            var again = Object.FindObjectsByType<EnemyController>(FindObjectsInactive.Include, FindObjectsSortMode.None)
                .First(e => Vector2.Distance(e.Home, home) < 0.05f);
            Assert.IsFalse(again.gameObject.activeSelf, "still dead after leaving and coming back");
            // an hour of game time later it is back
            DayNight.Advance(70);
            Assert.AreEqual(0f, GameManager.DefeatedFor("World", home));
            GameManager.Travel("City_Valle", "N0");
            yield return Arrive("City_Valle");
            GameManager.Travel("World", "City_Valle:N0");
            yield return Arrive("World");
            yield return null;
            again = Object.FindObjectsByType<EnemyController>(FindObjectsInactive.Include, FindObjectsSortMode.None)
                .First(e => Vector2.Distance(e.Home, home) < 0.05f);
            Assert.IsTrue(again.gameObject.activeSelf, "respawned once its time was up");
        }

        [UnityTest]
        public IEnumerator MonteCeniza_IsItsOwnMap_BehindTheSeal()
        {
            yield return Load("World");
            Assert.IsFalse(All<EnemyController>().Any(e => e.bossFlag == "boss_B"), "the Demon Lord is not in the world map");
            var gate = MapGate.Find("Zone_MonteCeniza:S0");
            Assert.IsNotNull(gate, "corridor behind the seal");
            var seal = All<SealBarrier>().OrderBy(b => Vector2.Distance(b.transform.position, gate.transform.position)).First();
            Assert.Less(Vector2.Distance(seal.transform.position, gate.transform.position), 4f, "the gate is right behind the seal");
            GameManager.Travel("Zone_MonteCeniza", "S0");
            yield return Arrive("Zone_MonteCeniza");
            Assert.AreEqual("zone", WorldInfo.Current.kind);
            Assert.AreEqual(1, All<EnemyController>().Count(e => e.bossFlag == "boss_B"), "Demon Lord");
            Assert.Greater(All<EnemyController>().Count(e => !e.isBoss), 10, "volcano monsters");
            Assert.GreaterOrEqual(All<Campfire>().Length, 1, "a camp at the entrance");
            Assert.IsNotNull(Object.FindAnyObjectByType<SpawnDirector>(), "the volcano spawns its own monsters");
        }

        [UnityTest]
        public IEnumerator MapKey_ShowsTheTownMap_AndTheWorldMap()
        {
            yield return Load("City_Ciudadela");
            _in.Press("Map"); yield return null; yield return null;
            Assert.IsTrue(WorldUI.MapOpen, "map open");
            Assert.IsFalse(WorldUI.MapShowsWorld, "a town opens its own map");
            _in.Press("Right"); yield return null; yield return null;
            Assert.IsTrue(WorldUI.MapShowsWorld, "right: the world map");
            _in.Press("Left"); yield return null; yield return null;
            Assert.IsFalse(WorldUI.MapShowsWorld, "left: back to the town");
            _in.Press("Map"); yield return null; yield return null;
            Assert.IsFalse(WorldUI.MapOpen, "closed");
            yield return Load("World");
            _in.Press("Map"); yield return null; yield return null;
            Assert.IsTrue(WorldUI.MapOpen && WorldUI.MapShowsWorld, "the overworld shows the world map");
            WorldUI.CloseAll();
        }

        [UnityTest]
        public IEnumerator Houses_InATown_StillWork()
        {
            yield return Load("City_Ciudadela");
            var door = All<HouseDoor>().First(d => d.interior.template == "capilla");
            WorldTests.Teleport(Player, (Vector2)door.transform.position + Vector2.down * 0.75f);
            _in.move = Vector2.up; yield return null; yield return null; _in.move = Vector2.zero; yield return null;
            _in.Press("Interact"); yield return null; yield return null;
            yield return WorldTests.Until(() => Interior.Current == door.interior, 3f, "inside the chapel");
            Assert.IsTrue(door.interior.bounds.Contains(Player.transform.position));
            Assert.Greater(door.interior.bounds.xMin, MapDB.Get("City_Ciudadela").w, "rooms are built outside the town map");
        }
    }

    /// <summary>Frames of the new maps -> Documentation/Screenshots (30_..).</summary>
    [Category("Screenshots")]
    public class MapScreenshots
    {
        VirtualInput _in;

        [UnitySetUp]
        public IEnumerator SetUp()
        {
            SaveSystem.Key = "woods_save_TEST"; SaveSystem.Delete();
            _in = new VirtualInput(); GameInput.Source = _in;
            GameManager.State = PlayerState.NewCharacter("knight"); SpawnDirector.Enabled = false;
            GameManager.State.clock = 11 * 60;
            Time.timeScale = 1;
            System.IO.Directory.CreateDirectory(System.IO.Path.GetFullPath(System.IO.Path.Combine(Application.dataPath, "..", "Documentation", "Screenshots")));
            yield return null;
        }

        [UnityTearDown]
        public IEnumerator TearDown()
        {
            SaveSystem.Delete(); SaveSystem.Key = "woods_save_v2"; SpawnDirector.Enabled = true;
            GameInput.Source = new KeyboardInput(); WorldUI.CloseAll(); Time.timeScale = 1;
            yield return null;
        }

        static IEnumerator At(Vector2 pos, float wait = 1.2f)
        {
            WorldTests.Teleport(PlayerController.Current, pos);
            yield return new WaitForSeconds(wait);
        }

        [UnityTest]
        public IEnumerator Capture_Maps()
        {
            var s = GameManager.State;
            foreach (var r in "abcdefghij") s.Set("region_" + r);
            // the village: square, houses, gate
            yield return MapTravelTests.Load("City_Valle");
            var fire = Object.FindObjectsByType<Campfire>(FindObjectsSortMode.None).First();
            yield return At(fire.Spot + new Vector2(0, -1.5f));
            yield return WorldScreenshots.Shot("30_aldea_plaza");
            var n0 = MapGate.Find("N0");
            yield return At(n0.arrival + Vector2.down * 1.5f);
            yield return WorldScreenshots.Shot("31_aldea_puerta_norte");
            _in.Press("Map"); yield return null; yield return null;
            yield return new WaitForSecondsRealtime(0.2f);
            yield return WorldScreenshots.Shot("32_mapa_local_aldea");
            _in.Press("Right"); yield return null; yield return null;
            yield return new WaitForSecondsRealtime(0.2f);
            yield return WorldScreenshots.Shot("33_mapa_del_mundo");
            WorldUI.CloseAll();
            // through the gate into the world: the village seen from outside
            GameManager.Travel("World", "City_Valle:N0");
            yield return WorldTests.Until(() => SceneManager.GetActiveScene().name == "World" && PlayerController.Current != null && !GameManager.Transitioning, 8f, "world");
            yield return new WaitForSeconds(1.2f);
            yield return WorldScreenshots.Shot("34_mundo_puerta_aldea");
            var cit = MapGate.Find("City_Ciudadela:S0");
            yield return At(cit.arrival + Vector2.down * 2f);
            yield return WorldScreenshots.Shot("35_mundo_ciudadela_por_fuera");
            // the citadel and the port
            yield return MapTravelTests.Load("City_Ciudadela");
            fire = Object.FindObjectsByType<Campfire>(FindObjectsSortMode.None).First();
            yield return At(fire.Spot + new Vector2(0, -2f));
            yield return WorldScreenshots.Shot("36_ciudadela_plaza");
            yield return At(MapGate.Find("S0").arrival + Vector2.up * 3f);
            yield return WorldScreenshots.Shot("37_ciudadela_puerta_sur");
            _in.Press("Map"); yield return null; yield return null;
            yield return new WaitForSecondsRealtime(0.2f);
            yield return WorldScreenshots.Shot("38_mapa_local_ciudadela");
            WorldUI.CloseAll();
            yield return MapTravelTests.Load("City_Puerto");
            fire = Object.FindObjectsByType<Campfire>(FindObjectsSortMode.None).First();
            yield return At(fire.Spot + new Vector2(-6f, -9f));
            yield return WorldScreenshots.Shot("39_puerto_muelles");
            yield return At(fire.Spot + new Vector2(0, -1.5f));
            yield return WorldScreenshots.Shot("40_puerto_mercado");
            // Monte Ceniza
            yield return MapTravelTests.Load("Zone_MonteCeniza");
            yield return WorldScreenshots.Shot("41_monte_ceniza_entrada");
            var lord = Object.FindObjectsByType<EnemyController>(FindObjectsSortMode.None).First(e => e.bossFlag == "boss_B");
            foreach (var e in Object.FindObjectsByType<EnemyController>(FindObjectsSortMode.None)) e.enabled = false;
            yield return At((Vector2)lord.transform.position + Vector2.down * 4f, 1.8f);
            yield return WorldScreenshots.Shot("42_monte_ceniza_senor_demonio");
        }
    }
}
