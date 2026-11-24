using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

namespace WoodsGame
{
    /// <summary>Open-world flow: new game / continue, death -> last campfire, bosses, victory, pause, enemy respawn.</summary>
    public partial class GameManager : MonoBehaviour
    {
        public static readonly string MenuScene = "MainMenu";
        public static readonly string WorldScene = "World";
        public static readonly string[] Levels = { WorldScene };
        public const float RespawnSeconds = 150f;

        public static PlayerState State = new PlayerState();
        public static int LevelIndex { get; private set; }
        public static bool Paused { get; private set; }
        public static bool InputBlocked => UIRoot.DialogOpen || WorldUI.PanelOpen || _transitioning || _ended;
        public static bool Ended => _ended;
        /// <summary>A fade (scene load, door, sleep) is running; player input is blocked meanwhile.</summary>
        public static bool Transitioning => _transitioning;
        public static bool Won { get; private set; }
        public static int EnemiesAlive => _enemies.Count;

        static readonly HashSet<EnemyController> _enemies = new HashSet<EnemyController>();
        static bool _transitioning, _ended;
        static GameManager _i;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Boot()
        {
            // top-down depth: sprites lower on screen draw in front (pivots are at the feet)
            GraphicsSettings.transparencySortMode = TransparencySortMode.CustomAxis;
            GraphicsSettings.transparencySortAxis = new Vector3(0, 1, 0);
            SceneManager.sceneLoaded += (s, m) => { _enemies.Clear(); _ended = false; Won = false; UIRoot.HideAll(); WorldUI.CloseAll(); SetPaused(false); OnMapLoaded(s); };
        }

        static GameManager I
        {
            get
            {
                if (_i) return _i;
                var go = new GameObject("GameManager");
                DontDestroyOnLoad(go);
                return _i = go.AddComponent<GameManager>();
            }
        }

        // ------------------------------------------------------------ autosave
        const float AutoSaveEvery = 60f;
        float _nextAutoSave;
        static Vector2? _resumeAt;

        /// <summary>Saves the whole game where you stand (progress, inventory, time, position). Rest points still decide
        /// where you come back after dying; Continue starts where you were.</summary>
        public static bool AutoSave(bool toast = false)
        {
            var p = PlayerController.Current;
            if (_ended || p == null || p.health.IsDead || LevelInfo.Current == null || State == null) return false;
            State.hp = p.health.hp;
            Vector2 at = p.transform.position;
            State.autoX = at.x; State.autoY = at.y;
            if (string.IsNullOrEmpty(State.saveMap)) State.saveMap = CurrentMap;
            State.Set("world_v3");
            SaveSystem.Save(State);
            if (toast) UIRoot.Toast("PARTIDA GUARDADA", 1.4f);
            return true;
        }

        void OnApplicationQuit() { AutoSave(); }
        void OnApplicationPause(bool paused) { if (paused) AutoSave(); }

        void Update()
        {
            if (LevelInfo.Current != null && !_ended && !_transitioning && Time.unscaledTime >= _nextAutoSave)
            {
                if (_nextAutoSave > 0f) AutoSave(true);
                _nextAutoSave = Time.unscaledTime + AutoSaveEvery;
            }
            bool inLevel = LevelInfo.Current != null;
            if (!inLevel || _ended || _transitioning || UIRoot.DialogOpen) return;
            if (WorldUI.PanelOpen)
            {
                if (GameInput.Pause) WorldUI.CloseAll();
                else if (GameInput.Map) WorldUI.ToggleMap();
                else if (GameInput.Journal) WorldUI.ToggleJournal();
                else if (GameInput.Character) WorldUI.ToggleCharacter();
                else if (GameInput.Inventory) WorldUI.ToggleInventory();
                return;
            }
            if (GameInput.Pause) SetPaused(!Paused);
            else if (!Paused && GameInput.Map) WorldUI.ToggleMap();
            else if (!Paused && GameInput.Journal) WorldUI.ToggleJournal();
            else if (!Paused && GameInput.Character) WorldUI.ToggleCharacter();
            else if (!Paused && GameInput.Inventory) WorldUI.ToggleInventory();
        }

        public static void Ensure() { var _ = I; }

        public static void SetLevelFromScene(string sceneName)
        {
            int i = System.Array.IndexOf(Levels, sceneName);
            if (i >= 0) LevelIndex = i;
        }

        // ------------------------------------------------------------ flow
        public static void NewGame() => NewGame(KnightClass.Default);

        /// <summary>Fresh character of the chosen knight class.</summary>
        public static void NewGame(string classId) => NewGame(classId, "");

        public static void NewGame(string classId, string heroName)
        {
            State = PlayerState.NewCharacter(classId, heroName);
            State.Set("world_v3"); _resumeAt = null;
            LoadMap(MapDB.StartMap, null);              // the adventure starts in the village
        }

        public static bool CanContinue => SaveSystem.HasSave;

        public static void Continue()
        {
            var s = SaveSystem.Load();
            State = s ?? new PlayerState();
            State.hp = State.maxHP;
            bool v3 = State.Has("world_v3");
            string map = ResumeMap(State);              // the map of the last rest point
            _resumeAt = v3 && State.autoX >= 0 ? new Vector2(State.autoX, State.autoY) : (Vector2?)null;   // ...or where you autosaved
            LoadMap(map, null);
        }

        /// <summary>The overworld map (no gate: the player keeps its builder / rest-point position).</summary>
        public static void LoadWorld() { LoadMap(WorldScene, null); }

        // kept for compatibility with older callers/tests
        public static void LoadLevel(int index) { LoadWorld(); }

        IEnumerator LoadRoutine(string scene)
        {
            _transitioning = true;
            SetPaused(false);
            yield return UIRoot.Fade(1f, 0.35f);
            SceneManager.LoadScene(scene);
            yield return null;
            yield return UIRoot.Fade(0f, 0.35f);
            _transitioning = false;
        }

        /// <summary>Back to the last campfire with the last saved state (a quarter of the coins is lost).</summary>
        public static void Respawn()
        {
            int coins = State.coins;
            var saved = SaveSystem.Load();
            _resumeAt = null;                           // dying always sends you to the rest point
            State = saved ?? new PlayerState();
            State.coins = Mathf.Max(0, Mathf.Min(State.coins, coins) - coins / 4);
            State.hp = State.maxHP;
            LoadMap(ResumeMap(State), null);
        }

        public static void Retry() { Respawn(); }

        public static void ToMenu()
        {
            AutoSave();
            SetPaused(false);
            I.StartCoroutine(I.MenuRoutine());
        }

        IEnumerator MenuRoutine()
        {
            _transitioning = true;
            yield return UIRoot.Fade(1f, 0.3f);
            UIRoot.HideAll(); WorldUI.CloseAll();
            SceneManager.LoadScene(MenuScene);
            yield return null;
            yield return UIRoot.Fade(0f, 0.3f);
            _transitioning = false;
        }

        public static void PlayerDied()
        {
            if (_ended) return;
            _ended = true;
            WorldUI.CloseAll();                   // a camp / shop / conversation never stays open over the death screen
            Sfx.Music(false);
            Sfx.Jingle("defeat");
            UIRoot.ShowGameOver();
        }

        public static void Victory()
        {
            if (_ended) return;
            _ended = true; Won = true;
            State.Set("victory");
            SaveSystem.Save(State);
            Sfx.Music(false);
            Sfx.Jingle("victory");
            UIRoot.ShowVictory();
        }

        /// <summary>Close the victory screen and keep exploring the world.</summary>
        public static void KeepExploring()
        {
            _ended = false;
            UIRoot.HideVictory();
            Sfx.Music(true);
        }

        public static void CompleteLevel() { }   // the open world has no level exits

        // ------------------------------------------------------------ houses
        public static void EnterInterior(Interior room) { if (room != null && !_transitioning) I.StartCoroutine(I.Door(room, true)); }
        public static void ExitInterior() { if (Interior.Current != null && !_transitioning) I.StartCoroutine(I.Door(Interior.Current, false)); }

        IEnumerator Door(Interior room, bool enter)
        {
            _transitioning = true;
            Sfx.Play(enter ? "door_open" : "door_close", 0.8f);
            yield return UIRoot.Fade(1f, 0.22f);
            var p = PlayerController.Current;
            if (p != null)
            {
                Vector2 to = enter ? room.entry : room.outside;
                var rb = p.GetComponent<Rigidbody2D>();
                rb.position = to; rb.linearVelocity = Vector2.zero; p.transform.position = to;
                p.Face(enter ? Vector2.up : Vector2.down);
            }
            Interior.Current = enter ? room : null;
            Interior.EnteredAt = Time.time;
            CameraFollow.SnapTo(p != null ? (Vector2)p.transform.position + Vector2.up * 0.5f : Vector2.zero);
            yield return null;
            yield return UIRoot.Fade(0f, 0.22f);
            _transitioning = false;
            if (enter) UIRoot.TitleCard(room.title, "");
        }

        /// <summary>Bed: sleep until dawn (at night) or until dusk (by day), full health, save at the bed.</summary>
        public static void Sleep(Vector2 spot) { if (!_transitioning) I.StartCoroutine(I.SleepRoutine(spot)); }

        IEnumerator SleepRoutine(Vector2 spot)
        {
            _transitioning = true;
            bool night = DayNight.IsNight;
            yield return UIRoot.Fade(1f, 0.6f);
            DayNight.SkipTo(night ? DayNight.DawnHour : DayNight.DuskHour);
            State.hp = State.maxHP;
            var p = PlayerController.Current;
            if (p != null) p.health.Init(State.maxHP, State.hp);
            SetRestPoint(spot, CurrentMap);
            SaveSystem.Save(State);
            yield return new WaitForSecondsRealtime(0.5f);
            yield return UIRoot.Fade(0f, 0.6f);
            _transitioning = false;
            UIRoot.Toast(night ? "DESCANSAS HASTA EL AMANECER · PARTIDA GUARDADA" : "DESCANSAS HASTA EL ANOCHECER · PARTIDA GUARDADA", 2.6f);
        }

        public static void SetPaused(bool p)
        {
            if (Paused != p) Sfx.Play(p ? "menu_open" : "menu_close", 0.6f);
            Paused = p;
            Time.timeScale = p ? 0f : 1f;
            UIRoot.ShowPause(p);
        }

        // ------------------------------------------------------------ enemies
        public static void RegisterEnemy(EnemyController e) { _enemies.Add(e); }

        public static void EnemyKilled(EnemyController e)
        {
            _enemies.Remove(e);
            Progression.OnEnemyKilled(e);
            if (e.isBoss) I.StartCoroutine(I.BossDown(e.bossFlag));
        }

        IEnumerator BossDown(string flag)
        {
            UIRoot.HideBoss();
            foreach (var sb in FindObjectsByType<SummonerBoss>(FindObjectsSortMode.None)) sb.Crumble();
            yield return new WaitForSeconds(2.5f);
            if (flag == "boss_B") { Victory(); yield break; }
            if (flag == "boss_F") { UIRoot.TitleCard("EL CORAZÓN HELADO SE APAGA", "LOS PICOS NEVADOS VUELVEN A RESPIRAR"); yield break; }
            if (flag == "boss_I")
            {
                // the Summoner's last breath: his curse passes to the knight
                State.Set(Summoning.CurseFlag);
                var p = PlayerController.Current;
                if (p) { Fx.Spawn(FxKind.Summon, p.transform.position, -1, 8f); CameraFollow.Shake(0.6f, 0.12f); }
                Sfx.Play("boss_roar");
                UIRoot.TitleCard("LA MALDICIÓN DEL INVOCADOR", "FIN DE LA PRIMERA PARTE");
                yield return new WaitForSeconds(3f);
                UIRoot.ShowDialog("«NO MUERO... ME QUEDO EN TI.»  AHORA PUEDES ALZAR A LOS ENEMIGOS QUE DERROTES: PULSA V JUNTO A UN CUERPO RECIENTE (MÁXIMO 4) Y V DE NUEVO PARA DARLES ÓRDENES. SI UNA INVOCACIÓN MUERE, LA PIERDES PARA SIEMPRE.");
                SaveSystem.Save(State);
                yield break;
            }
            bool both = State.Has("boss_K") && State.Has("boss_Q");
            UIRoot.TitleCard(both ? "¡EL SELLO HA CAÍDO!" : "UN GUARDIÁN HA CAÍDO",
                             both ? "EL CAMINO AL MONTE CENIZA ESTÁ ABIERTO" : "EL SELLO DEL MONTE CENIZA SE DEBILITA");
        }

        /// <summary>A map resident died: it comes back after RespawnSeconds (the timer survives leaving the map, see GameManager.Maps).</summary>
        public static void ScheduleRespawn(EnemyController e) { RecordDefeat(e); I.StartCoroutine(I.RespawnRoutine(e, RespawnSeconds)); }
    }
}
