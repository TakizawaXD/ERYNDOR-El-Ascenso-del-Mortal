// Tools > Game > Build Game
// One click: art pipeline (rule tiles, character animators) -> font -> prefabs -> GameAssets -> scenes -> build settings.
// Everything is generated from Assets/Art, Assets/Game/Levels/*.txt and Assets/Game/Audio, so it can be re-run safely.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.Tilemaps;
using WoodsArt.EditorTools;

namespace WoodsGame.EditorTools
{
    public static partial class GameBuilder
    {
        static AudioClip[] AudioIn(string folder) =>
            !AssetDatabase.IsValidFolder(folder) ? new AudioClip[0] :
            AssetDatabase.FindAssets("t:AudioClip", new[] { folder })
                .Select(g => AssetDatabase.LoadAssetAtPath<AudioClip>(AssetDatabase.GUIDToAssetPath(g)))
                .Where(c => c != null).OrderBy(c => c.name).ToArray();

        const string GameRoot = "Assets/Game";
        const string Prefabs = GameRoot + "/Prefabs";
        const string ScenesDir = GameRoot + "/Scenes";
        const string GenTiles = "Assets/Art/Tilesets/_Generated";
        const string Chars = "Assets/Art/Characters";
        const string Anims = "Assets/Art/Animations/Characters";
        static readonly string ProjectRoot = Path.GetFullPath(Path.Combine(Application.dataPath, ".."));

        [MenuItem("Tools/Game/Build Game", priority = 0)]
        public static void BuildGame()
        {
            try
            {
                Step("Copying original sprites", 0.02f); CopyOriginals();
                Step("Art pipeline: tiles & palette", 0.1f); ArtAssetBuilder.BuildAll();
                Step("Art pipeline: character animators", 0.25f); CharacterAnimationBuilder.BuildAll();
                Step("Pixel font", 0.4f); var font = BuildFont();
                Step("Prefabs", 0.5f); var assets = BuildAssetsAndPrefabs(font);
                SortPrefabsByFoot();
                Step("Scenes", 0.7f); BuildScenes();
                Step("Project settings", 0.95f); ConfigureProject();
                AssetDatabase.SaveAssets();
                Debug.Log("[GameBuilder] Game built. Open Assets/Game/Scenes/MainMenu.unity and press Play.");
            }
            finally { EditorUtility.ClearProgressBar(); }
        }

        /// <summary>Every sprite of every prefab (player, enemies, animals, pickups, projectiles...) sorts by its pivot (the
        /// feet) instead of the image centre: a 64 px character cell has its centre far above the feet, which put
        /// characters behind chairs, fences and torches they were standing in front of.</summary>
        static void SortPrefabsByFoot()
        {
            int n = 0;
            foreach (var guid in AssetDatabase.FindAssets("t:Prefab", new[] { Prefabs }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                var root = PrefabUtility.LoadPrefabContents(path);
                bool dirty = false;
                foreach (var sr in root.GetComponentsInChildren<SpriteRenderer>(true))
                    if (sr.spriteSortPoint != SpriteSortPoint.Pivot) { sr.spriteSortPoint = SpriteSortPoint.Pivot; dirty = true; n++; }
                if (dirty) PrefabUtility.SaveAsPrefabAsset(root, path);
                PrefabUtility.UnloadPrefabContents(root);
            }
            Debug.Log($"[GameBuilder] {n} prefab sprites now sort by their feet");
        }

        static void Step(string what, float p)
        {
            Debug.Log("[GameBuilder] " + what);
            if (!Application.isBatchMode) EditorUtility.DisplayProgressBar("Build Game", what, p);
        }

        // ================================================================ originals
        static void CopyOriginals()
        {
            Ensure("Assets/Art/Original");
            string src = Path.Combine(ProjectRoot, "pixel_16_woods v2 free", "free_pixel_16_woods.png");
            string dst = Path.Combine(ProjectRoot, GameArtPostprocessor.WoodsPath);
            if (File.Exists(src) && !File.Exists(dst))
            {
                File.Copy(src, dst);
                AssetDatabase.ImportAsset(GameArtPostprocessor.WoodsPath, ImportAssetOptions.ForceUpdate);
            }
        }

        // ================================================================ font
        [Serializable] class Glyph { public int c, x, y, w, adv; }
        [Serializable] class FontMeta { public int cellW, cellH, ascent, size, scale = 1; public Glyph[] glyphs; }

        static Font BuildFont()
        {
            string json = Path.Combine(ProjectRoot, "Assets/Game/Fonts/pixelfont.json");
            var meta = JsonUtility.FromJson<FontMeta>(File.ReadAllText(json));
            AssetDatabase.ImportAsset(GameArtPostprocessor.FontPng, ImportAssetOptions.ForceUpdate);
            var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(GameArtPostprocessor.FontPng);
            string path = "Assets/Game/Fonts/PixelFont.fontsettings";
            var font = AssetDatabase.LoadAssetAtPath<Font>(path);
            bool create = font == null;
            if (create) font = new Font("PixelFont");
            float W = tex.width, H = tex.height;
            float sc = Mathf.Max(1, meta.scale);
            var infos = new List<CharacterInfo>();
            foreach (var g in meta.glyphs)
            {
                var ci = new CharacterInfo
                {
                    index = g.c,
                    advance = g.adv,
                    minX = 0, maxX = g.w,
                    minY = -1, maxY = meta.cellH - 1,          // one descender row under the baseline
                    // atlas may be drawn at N texels per canvas pixel (font_hd.py: scale 2) for smoother letters
                    uvBottomLeft = new Vector2(g.x / W, 1f - (g.y + meta.cellH * sc) / H),
                    uvBottomRight = new Vector2((g.x + g.w * sc) / W, 1f - (g.y + meta.cellH * sc) / H),
                    uvTopLeft = new Vector2(g.x / W, 1f - g.y / H),
                    uvTopRight = new Vector2((g.x + g.w * sc) / W, 1f - g.y / H),
                };
                infos.Add(ci);
            }
            font.characterInfo = infos.ToArray();
            Material mat = create ? null : AssetDatabase.LoadAllAssetsAtPath(path).OfType<Material>().FirstOrDefault();
            if (mat == null) { mat = new Material(Shader.Find("UI/Default")) { name = "PixelFont Material" }; }
            mat.mainTexture = tex;
            if (create) { AssetDatabase.CreateAsset(font, path); AssetDatabase.AddObjectToAsset(mat, font); }
            font.material = mat;
            var so = new SerializedObject(font);
            SetFloat(so, "m_FontSize", meta.cellH);
            SetFloat(so, "m_LineSpacing", meta.cellH + 1);
            SetFloat(so, "m_Ascent", meta.cellH - 1);
            so.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(font);
            return font;
        }

        static void SetFloat(SerializedObject so, string prop, float v)
        {
            var p = so.FindProperty(prop);
            if (p == null) return;
            if (p.propertyType == SerializedPropertyType.Integer) p.intValue = (int)v; else p.floatValue = v;
        }

        // ================================================================ sprites helpers
        static Sprite[] Sheet(string path) => ArtAssetBuilder.SlicedSprites(path);
        static Sprite One(string path) => AssetDatabase.LoadAllAssetsAtPath(path).OfType<Sprite>().FirstOrDefault();
        static Sprite Cell(string path, int i) { var s = Sheet(path); return s.Length > i ? s[i] : null; }
        static Sprite Woods(string name) => AssetDatabase.LoadAllAssetsAtPath(GameArtPostprocessor.WoodsPath).OfType<Sprite>().FirstOrDefault(s => s.name == name);

        const string FX = "Assets/Art/Effects/";
        const string UI = "Assets/Art/UI/";
        const string PROPS = "Assets/Art/Props/";
        const string VEG = "Assets/Art/Environments/Vegetation/";
        const string DECO = "Assets/Art/Environments/Decorations/";

        // ================================================================ assets + prefabs
        static GameAssets BuildAssetsAndPrefabs(Font font)
        {
            Ensure(GameRoot + "/Resources"); Ensure(Prefabs); Ensure(GameRoot + "/Tiles");
            string ap = GameRoot + "/Resources/GameAssets.asset";
            var a = AssetDatabase.LoadAssetAtPath<GameAssets>(ap);
            if (a == null) { a = ScriptableObject.CreateInstance<GameAssets>(); AssetDatabase.CreateAsset(a, ap); }

            a.fxHit = Sheet(FX + "fx_hit_spark_anim_32x32.png");
            a.fxBlood = Sheet(FX + "fx_blood_burst_anim_32x32.png");
            a.fxDust = Sheet(FX + "fx_dust_walk_anim_16x16.png");
            a.fxPoof = Sheet(FX + "fx_smoke_poof_anim_32x32.png");
            a.fxSplash = Sheet(FX + "fx_water_splash_anim_32x32.png");
            a.fxSparkle = Sheet(FX + "fx_pickup_sparkle_anim_16x16.png");
            a.fxHeal = Sheet(FX + "fx_heal_anim_32x32.png");
            a.fxExplosion = Sheet(FX + "fx_explosion_anim_48x48.png");
            a.fxSummon = Sheet(FX + "fx_demon_summon_circle_anim_32x32.png");
            a.arrowFrames = new[] { One("Assets/Art/Game/proj_arrow.png") };
            a.fireballFrames = Sheet(FX + "fx_demon_fireball_anim_16x16.png");
            a.spitFrames = Sheet("Assets/Art/Game/proj_spit_anim_8x8.png");

            string icons = UI + "Icons/ui_icons_items_16x16.png";
            a.coin = Cell(icons, 7); a.potion = Cell(icons, 5); a.arrows = Cell(icons, 3);
            a.heart = Cell(UI + "ui_hearts_16x16.png", 0);
            a.font = font;
            a.heartFull = Cell(UI + "ui_hearts_16x16.png", 0);
            a.heartHalf = Cell(UI + "ui_hearts_16x16.png", 1);
            a.heartEmpty = Cell(UI + "ui_hearts_16x16.png", 2);
            a.panel = One(UI + "ui_panel_wood_9s8.png");
            a.dialog = One(UI + "ui_dialog_box_9s6.png");
            a.slot = Cell(UI + "ui_inventory_slot_20x20_9s4.png", 0);
            a.slotSelected = Cell(UI + "ui_inventory_slot_20x20_9s4.png", 1);
            a.barFrame = One(UI + "ui_bar_frame_9s3.png");
            a.barFillHP = Cell(UI + "ui_bar_fills_8x6.png", 0);
            a.barFillBoss = Cell(UI + "ui_bar_fills_8x6.png", 0);
            a.iconCoin = Cell(icons, 7); a.iconArrow = Cell(icons, 3); a.iconPotion = Cell(icons, 5);
            a.iconSkull = Cell(icons, 12); a.iconSword = Cell(icons, 0);
            a.promptE0 = Cell(UI + "ui_prompts_16x16.png", 0); a.promptE1 = Cell(UI + "ui_prompts_16x16.png", 1);
            a.menuBackground = One("Assets/Art/Environments/Backgrounds/bg_menu_world_320x180.png") ?? One("Assets/Art/Environments/Backgrounds/bg_menu_forest_320x180.png");
            a.titleScreen = One("Assets/Art/UI/Title/eryndor_title.png");
            a.button = Cell(UI + "ui_button_states_48x16_9s4.png", 0);
            a.buttonHover = Cell(UI + "ui_button_states_48x16_9s4.png", 1);
            a.sfx = AssetDatabase.FindAssets("t:AudioClip", new[] { GameRoot + "/Audio" })
                .Select(g => AssetDatabase.LoadAssetAtPath<AudioClip>(AssetDatabase.GUIDToAssetPath(g)))
                .Where(c => c != null && c.name.StartsWith("sfx_")).ToArray();
            a.music = AssetDatabase.LoadAssetAtPath<AudioClip>(GameRoot + "/Audio/music_forest_loop.wav");
            a.musicClips = AudioIn(GameRoot + "/Audio/Music");        // Tools/GameGen/music.py: every piece, night layer, intro, jingle
            a.ambienceClips = AudioIn(GameRoot + "/Audio/Ambience");  // Tools/GameGen/ambience.py
            if (a.musicClips.Length < 40 || a.ambienceClips.Length < 10)
                Debug.LogError("[GameBuilder] music / ambience missing (python Tools/GameGen/music.py; python Tools/GameGen/ambience.py)");

            // projectiles
            a.arrowPrefab = ProjectilePrefab("Arrow", a.arrowFrames, 0.12f, FxKind.Hit);
            a.fireballPrefab = ProjectilePrefab("Fireball", a.fireballFrames, 0.2f, FxKind.Explosion);
            a.spitPrefab = ProjectilePrefab("Spit", a.spitFrames, 0.18f, FxKind.Splash);
            // pickups
            a.coinPrefab = PickupPrefab("Coin", a.coin, PickupKind.Coin, 1);
            a.potionPrefab = PickupPrefab("Potion", a.potion, PickupKind.Potion, 1);
            a.arrowsPickupPrefab = PickupPrefab("ArrowBundle", a.arrows, PickupKind.Arrows, 5);
            // actors
            ActorPrefab("Player", "Soldier", false, 1, go =>
            {
                var p = go.AddComponent<PlayerController>();
                p.walkSpeed = 3.2f; p.runSpeed = 5f;
            });
            ActorPrefab("DemonLord", "BossDemonLord", true, 2, go =>
            {
                var e = go.AddComponent<EnemyController>();
                e.kind = EnemyKind.Demon; e.typeId = "DemonLord"; e.ai = AIProfile.Caster; e.xpReward = 60; e.displayName = "SEÑOR DEMONIO"; e.isBoss = true; e.maxHP = 70; e.damage = 3; e.walkSpeed = 1.6f;
                e.chaseSpeed = 2.2f; e.aggroRange = 7f; e.attackRange = 1.1f; e.attackCooldown = 1.1f; e.heavyChance = 0.45f;
                e.ranged = true; e.rangedMin = 2.5f; e.rangedMax = 8f; e.rangedCooldown = 2.4f; e.rangedDamage = 2; e.coins = 0;
                e.potionChance = 0; e.arrowChance = 0; e.bossFlag = "boss_B";
                BossLook(go, "demon", new Color(1f, 0.5f, 0.15f), new[] { "DemonAsh" }, 0.4f, 1.15f);
            });
            ActorPrefab("OrcChieftain", "BossOrcWarlord", true, 2, go =>
            {
                var e = go.AddComponent<EnemyController>();
                e.kind = EnemyKind.Orc; e.typeId = "OrcChieftain"; e.ai = AIProfile.Charger; e.xpReward = 40; e.knockbackResist = 0.6f; e.displayName = "GORGRAK EL CAUDILLO"; e.isBoss = true; e.bossFlag = "boss_K"; e.maxHP = 55; e.damage = 3;
                e.walkSpeed = 1.5f; e.chaseSpeed = 2.3f; e.aggroRange = 6.5f; e.attackRange = 1.1f; e.attackCooldown = 1.0f; e.heavyChance = 0.5f;
                e.coins = 0; e.potionChance = 0; e.arrowChance = 0;
                BossLook(go, "warlord", new Color(1f, 0.65f, 0.25f), new[] { "OrcDesert", "OrcBerserker" }, 0.4f, 1.05f);
            });
            ActorPrefab("BloodMother", "BossBloodMother", true, 2, go =>
            {
                var e = go.AddComponent<EnemyController>();
                e.kind = EnemyKind.BloodMonster; e.typeId = "BloodMother"; e.ai = AIProfile.Kiter; e.xpReward = 40; e.displayName = "MADRE DE SANGRE"; e.isBoss = true; e.bossFlag = "boss_Q"; e.maxHP = 55; e.damage = 2;
                e.walkSpeed = 1.3f; e.chaseSpeed = 2.0f; e.aggroRange = 7f; e.attackRange = 1.0f; e.attackCooldown = 1.2f; e.heavyChance = 0.35f;
                e.ranged = true; e.rangedMin = 2.2f; e.rangedMax = 7.5f; e.rangedCooldown = 2.0f; e.rangedDamage = 2;
                e.coins = 0; e.potionChance = 0; e.arrowChance = 0;
                BossLook(go, "mother", new Color(1f, 0.3f, 0.4f), new[] { "BloodToxic" }, 0.48f, 0.85f);
            });
            BuildAnimalPrefabs();
            BuildRpgAssets(a);
            BuildBossAssets();                      // Resources/BossAssets + Frost Colossus (GameBuilder.Bosses.cs)
            EditorUtility.SetDirty(a);
            AssetDatabase.SaveAssets();
            return a;
        }

        static GameObject SavePrefab(GameObject go, string name)
        {
            string path = $"{Prefabs}/{name}.prefab";
            var p = PrefabUtility.SaveAsPrefabAsset(go, path);
            UnityEngine.Object.DestroyImmediate(go);
            return p;
        }

        static GameObject ProjectilePrefab(string name, Sprite[] frames, float radius, FxKind impact)
        {
            var go = new GameObject(name);
            var sr = go.AddComponent<SpriteRenderer>(); sr.sprite = frames.FirstOrDefault(); sr.sortingOrder = 50;
            if (frames.Length > 1) { var an = go.AddComponent<SpriteAnim>(); an.frames = frames; an.fps = 12; an.loop = true; an.destroyAtEnd = false; }
            var rb = go.AddComponent<Rigidbody2D>(); rb.gravityScale = 0; rb.collisionDetectionMode = CollisionDetectionMode2D.Continuous; rb.freezeRotation = true;
            var col = go.AddComponent<CircleCollider2D>(); col.isTrigger = true; col.radius = radius;
            var p = go.AddComponent<Projectile>(); p.impactFx = impact;
            return SavePrefab(go, name);
        }

        static GameObject PickupPrefab(string name, Sprite s, PickupKind kind, int amount)
        {
            var go = new GameObject(name);
            var p = go.AddComponent<Pickup>(); p.kind = kind; p.amount = amount;
            var gfx = new GameObject("gfx"); gfx.transform.SetParent(go.transform, false);
            var sr = gfx.AddComponent<SpriteRenderer>(); sr.sprite = s; sr.sortingOrder = 1;
            var sh = new GameObject("shadow"); sh.transform.SetParent(go.transform, false); sh.transform.localPosition = new Vector3(0, -0.3f, 0);
            var ssr = sh.AddComponent<SpriteRenderer>(); ssr.sprite = One("Assets/Art/Game/shadow_blob.png"); ssr.sortingOrder = -2;
            sh.transform.localScale = new Vector3(0.6f, 0.6f, 1);
            return SavePrefab(go, name);
        }

        static GameObject ActorPrefab(string name, string character, bool shadow, int scale, Action<GameObject> configure)
        {
            var go = new GameObject(name);
            var rb = go.AddComponent<Rigidbody2D>();
            rb.gravityScale = 0; rb.freezeRotation = true; rb.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            rb.interpolation = RigidbodyInterpolation2D.Interpolate;
            var col = go.AddComponent<CircleCollider2D>(); col.radius = 0.28f; col.offset = new Vector2(0, 0.2f);
            go.AddComponent<Health>();
            var spr = new GameObject("Sprite"); spr.transform.SetParent(go.transform, false);
            var sr = spr.AddComponent<SpriteRenderer>();
            sr.sprite = Cell($"{Chars}/{character}/Idle/{character}_Idle_Down.png", 0);
            var anim = spr.AddComponent<Animator>();
            anim.runtimeAnimatorController = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>($"{Anims}/{character}/{character}.controller");
            if (shadow)
            {
                var sh = new GameObject("Shadow"); sh.transform.SetParent(go.transform, false);
                var ssr = sh.AddComponent<SpriteRenderer>(); ssr.sprite = One("Assets/Art/Game/shadow_blob.png"); ssr.sortingOrder = -1;
                sh.transform.localPosition = new Vector3(0, 0.05f, 0);
            }
            configure(go);
            WireCombat(go, character);                 // animation events, attack data, hitbox (GameBuilder.Combat.cs)
            go.transform.localScale = new Vector3(scale, scale, 1);
            return SavePrefab(go, name);
        }

        // ================================================================ levels
        class LevelData
        {
            public string title, subtitle; public int w, h;
            public string[] terrain, entities;
            public Dictionary<Vector2Int, string> signs = new Dictionary<Vector2Int, string>();
            public char T(int x, int row) => x < 0 || row < 0 || x >= w || row >= h ? 'c' : terrain[row][x];
            public char E(int x, int row) => x < 0 || row < 0 || x >= w || row >= h ? ' ' : entities[row][x];
        }

        static LevelData Parse(string file)
        {
            var lines = File.ReadAllLines(Path.Combine(ProjectRoot, file));
            var d = new LevelData();
            int t0 = Array.IndexOf(lines, "TERRAIN"), e0 = Array.IndexOf(lines, "ENTITIES");
            foreach (var l in lines.Take(t0))
            {
                if (l.StartsWith("TITLE ")) d.title = l.Substring(6);
                else if (l.StartsWith("SUBTITLE ")) d.subtitle = l.Substring(9);
                else if (l.StartsWith("SIZE ")) { var p = l.Split(' '); d.w = int.Parse(p[1]); d.h = int.Parse(p[2]); }
                else if (l.StartsWith("SIGN ")) { var p = l.Split(new[] { ' ' }, 4); d.signs[new Vector2Int(int.Parse(p[1]), int.Parse(p[2]))] = p[3]; }
            }
            d.terrain = lines.Skip(t0 + 1).Take(e0 - t0 - 1).ToArray();
            d.entities = lines.Skip(e0 + 1).Take(d.h).ToArray();
            return d;
        }

        static void BuildScenes()
        {
            Ensure(ScenesDir);
            BuildMenuScene();
            // several loaded maps: the overworld, each town and Monte Ceniza (GameBuilder.Maps.cs)
            LoadMapCatalog();
            var ga = AssetDatabase.LoadAssetAtPath<GameAssets>(GameRoot + "/Resources/GameAssets.asset");
            if (ga != null) { ga.worldMap = One(WA + "world_map.png"); EditorUtility.SetDirty(ga); }
            foreach (var m in MapDB.Maps) BuildMapScene(m.id);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene($"{ScenesDir}/MainMenu.unity", true) }
                .Concat(MapDB.Maps.Select(m => new EditorBuildSettingsScene($"{ScenesDir}/{m.id}.unity", true))).ToArray();
        }

        static Camera MakeCamera(Color bg)
        {
            var cam = new GameObject("Main Camera", typeof(Camera), typeof(AudioListener)).GetComponent<Camera>();
            cam.tag = "MainCamera";
            cam.orthographic = true; cam.orthographicSize = 5.625f;
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = bg;
            cam.transform.position = new Vector3(0, 0, -10);
            return cam;
        }

        static void BuildMenuScene()
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            MakeCamera(new Color32(0x14, 0x10, 0x13, 0xff));
            new GameObject("MainMenu").AddComponent<MainMenu>();
            EditorSceneManager.SaveScene(scene, $"{ScenesDir}/MainMenu.unity");
        }

        static void BuildLevelScene(string name, bool requireClearForExit)
        {
            var d = Parse($"{GameRoot}/Levels/{name}.txt");
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var cam = MakeCamera(new Color32(0x24, 0x52, 0x3b, 0xff));
            cam.gameObject.AddComponent<CameraFollow>();

            var info = new GameObject("Level").AddComponent<LevelInfo>();
            info.title = d.title; info.subtitle = d.subtitle; info.bounds = new Rect(0, 0, d.w, d.h);

            PaintTerrain(d);
            var world = new GameObject("World").transform;
            PlaceEntities(d, world, requireClearForExit);

            var start = d.entities.SelectMany((r, row) => r.Select((c, x) => (c, x, row))).FirstOrDefault(t => t.c == 'P');
            cam.transform.position = new Vector3(start.x + 0.5f, d.h - 1 - start.row + 0.5f, -10);
            EditorSceneManager.SaveScene(scene, $"{ScenesDir}/{name}.unity");
        }

        static Tilemap Layer(Transform grid, string name, int order, bool render = true)
        {
            var go = new GameObject(name, typeof(Tilemap), typeof(TilemapRenderer));
            go.transform.SetParent(grid, false);
            var r = go.GetComponent<TilemapRenderer>();
            r.sortingOrder = order; r.mode = TilemapRenderer.Mode.Chunk; r.enabled = render;
            return go.GetComponent<Tilemap>();
        }

        static T LoadTile<T>(string path) where T : TileBase
        {
            var t = AssetDatabase.LoadAssetAtPath<T>(path);
            if (t == null) Debug.LogError("[GameBuilder] missing tile " + path + " (did the art pipeline run?)");
            return t;
        }

        static void PaintTerrain(LevelData d)
        {
            var grid = new GameObject("Grid", typeof(Grid)).transform;
            var ground = Layer(grid, "Ground", -60);
            var grass = Layer(grid, "Grass", -59);
            var tall = Layer(grid, "TallGrass", -58);
            var path = Layer(grid, "Path", -57);
            var water = Layer(grid, "Water", -56);
            var bridge = Layer(grid, "Bridge", -55);
            var cliff = Layer(grid, "Cliff", -54);
            var block = Layer(grid, "Collision", 0, render: false);

            var tDirt = LoadTile<TileBase>($"{GenTiles}/RT_DirtFill_Random.asset");
            var tGrass = LoadTile<TileBase>($"{GenTiles}/RT_Grass.asset");
            var tTall = LoadTile<TileBase>($"{GenTiles}/RT_TallGrass.asset");
            var tPath = LoadTile<TileBase>($"{GenTiles}/RT_StonePath.asset");
            var tWater = LoadTile<TileBase>($"{GenTiles}/RT_Water.asset");
            var tCliff = LoadTile<TileBase>($"{GenTiles}/RT_Cliff.asset");
            var bridgeH = new[] { 0, 1, 2 }.Select(i => LoadTile<TileBase>($"{GenTiles}/deco_bridge_16x16_{i}.asset")).ToArray();
            var bridgeV = new[] { 3, 4, 5 }.Select(i => LoadTile<TileBase>($"{GenTiles}/deco_bridge_16x16_{i}.asset")).ToArray();
            var tBlock = BlockTile();

            const int M = 8;   // margin painted around the map so rule tiles never end at the camera edge
            for (int row = -M; row < d.h + M; row++)
                for (int x = -M; x < d.w + M; x++)
                {
                    var c = new Vector3Int(x, d.h - 1 - row, 0);
                    char t = d.T(x, row);
                    ground.SetTile(c, tDirt);
                    if (".\"pwc=H".IndexOf(t) >= 0) grass.SetTile(c, tGrass);
                    if (t == '"') tall.SetTile(c, tTall);
                    if (t == 'p') path.SetTile(c, tPath);
                    if ("w=H".IndexOf(t) >= 0) water.SetTile(c, tWater);
                    if (t == 'c') cliff.SetTile(c, tCliff);
                    if (t == '=')
                        bridge.SetTile(c, bridgeH[d.T(x - 1, row) != '=' ? 0 : d.T(x + 1, row) != '=' ? 2 : 1]);
                    if (t == 'H')
                        bridge.SetTile(c, bridgeV[d.T(x, row - 1) != 'H' ? 0 : d.T(x, row + 1) != 'H' ? 2 : 1]);
                    if (t == 'w' || t == 'c') block.SetTile(c, tBlock);
                }
            // solid walls: one merged collider for water, cliffs and the map frame
            var body = block.gameObject.AddComponent<Rigidbody2D>(); body.bodyType = RigidbodyType2D.Static;
            var tc = block.gameObject.AddComponent<TilemapCollider2D>();
            tc.compositeOperation = Collider2D.CompositeOperation.Merge;
            var comp = block.gameObject.AddComponent<CompositeCollider2D>(); comp.geometryType = CompositeCollider2D.GeometryType.Polygons;
        }

        static TileBase BlockTile()
        {
            string p = GameRoot + "/Tiles/T_Block.asset";
            var t = AssetDatabase.LoadAssetAtPath<Tile>(p);
            if (t == null) { t = ScriptableObject.CreateInstance<Tile>(); AssetDatabase.CreateAsset(t, p); }
            t.sprite = Cell("Assets/Art/Environments/Terrain/terrain_dirt_fill_16x16.png", 0);
            t.colliderType = Tile.ColliderType.Grid;
            EditorUtility.SetDirty(t);
            return t;
        }

        // ---------------------------------------------------------------- entities
        static GameObject Deco(Transform parent, string name, Sprite s, Vector3 pos, Vector2 col = default, float colY = 0.15f, int order = 0)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.position = pos;
            var sr = go.AddComponent<SpriteRenderer>(); sr.sprite = s; sr.sortingOrder = order;
            sr.spriteSortPoint = SpriteSortPoint.Pivot;      // depth by the foot, not the image centre (a tall sprite never hides one in front of it)
            if (col != default)
            {
                var bc = go.AddComponent<BoxCollider2D>(); bc.size = col; bc.offset = new Vector2(0, colY);
            }
            return go;
        }

        static void Loop(GameObject go, Sprite[] frames, float fps)
        {
            var an = go.AddComponent<SpriteAnim>(); an.frames = frames; an.fps = fps; an.loop = true; an.destroyAtEnd = false;
        }

        static GameObject Spawn(string prefab, Transform parent, Vector3 pos)
        {
            var p = AssetDatabase.LoadAssetAtPath<GameObject>($"{Prefabs}/{prefab}.prefab");
            var go = (GameObject)PrefabUtility.InstantiatePrefab(p, parent);
            go.transform.position = pos;
            return go;
        }

        static void PlaceEntities(LevelData d, Transform world, bool requireClear)
        {
            var props = Sheet(PROPS + "props_static_16x16.png");               // barrel crate pot pot_broken sign rocks grave
            var chest = Sheet(PROPS + "prop_chest_open_anim_16x16.png");
            var torch = Sheet(PROPS + "prop_torch_anim_16x32.png");
            var fire = Sheet(PROPS + "prop_campfire_anim_16x16.png");
            var obelisk = Sheet(DECO + "deco_demon_obelisk_anim_16x32.png");
            var fence = Sheet(DECO + "deco_fence_16x16.png");
            var tuft = Sheet(VEG + "veg_tallgrass_sway_anim_16x16.png");
            var flowers = Sheet(VEG + "veg_flowers_16x16.png");
            var bushes = Sheet(VEG + "veg_bushes_small_16x16.png");
            var sparkle = Sheet(FX + "fx_pickup_sparkle_anim_16x16.png");
            var rng = new System.Random(d.w * 31 + d.h);

            var actors = new GameObject("Actors").transform; actors.SetParent(world);
            var decor = new GameObject("Decor").transform; decor.SetParent(world);
            var items = new GameObject("Items").transform; items.SetParent(world);

            for (int row = 0; row < d.h; row++)
                for (int x = 0; x < d.w; x++)
                {
                    char c = d.E(x, row);
                    var foot = new Vector3(x + 0.5f, d.h - 1 - row, 0);           // bottom-centre of the cell
                    var mid = foot + new Vector3(0, 0.3f, 0);
                    switch (c)
                    {
                        case 'P': Spawn("Player", actors, mid); break;
                        case 'o': Spawn("Orc", actors, mid); break;
                        case 'd': Spawn("Demon", actors, mid); break;
                        case 'm': Spawn("BloodMonster", actors, mid); break;
                        case 'B': Spawn("DemonLord", actors, mid); break;
                        case 'T': Deco(decor, "Tree", Woods("woods_tree_big"), foot, new Vector2(1.2f, 0.5f), 0.35f); break;
                        case 't': Deco(decor, "TreeSmall", Woods("woods_tree_small"), foot, new Vector2(0.6f, 0.35f), 0.25f); break;
                        case 'i': Deco(decor, "Pine", Woods("woods_pine"), foot, new Vector2(0.5f, 0.35f), 0.25f); break;
                        case 'r': Deco(decor, "Rock", Woods("woods_rock"), foot, new Vector2(0.8f, 0.4f), 0.2f); break;
                        case 'g': Deco(decor, "Bush", rng.Next(2) == 0 ? Woods("woods_bush") : bushes[rng.Next(bushes.Length)], foot); break;
                        case 'M': Deco(decor, "Mushrooms", Woods("woods_mushrooms"), foot, default, 0, -1); break;
                        case 'Z': Deco(decor, "Stump", Woods("woods_stump"), foot, new Vector2(0.7f, 0.35f), 0.2f); break;
                        case 'D': Deco(decor, "DeadTree", One(VEG + "veg_tree_dead_32x40.png"), foot, new Vector2(0.8f, 0.4f), 0.25f); break;
                        case 'b': Deco(decor, "BigBush", One(VEG + "veg_bush_large_32x24.png"), foot, new Vector2(1.6f, 0.45f), 0.25f); break;
                        case 'n': Deco(decor, "Log", One(VEG + "veg_log_fallen_32x16.png"), foot, new Vector2(1.7f, 0.45f), 0.25f); break;
                        case 'y': Deco(decor, "Flowers", flowers[rng.Next(flowers.Length)], foot, default, 0, -1); break;
                        case 'v':
                        {
                            int v = rng.Next(3);
                            var go = Deco(decor, "Tuft", tuft[v * 4], foot, default, 0, -1);
                            Loop(go, tuft.Skip(v * 4).Take(4).ToArray(), 4 + (float)rng.NextDouble() * 2);
                            break;
                        }
                        case 'x': Breakable(Deco(decor, "Crate", props[1], foot, new Vector2(0.8f, 0.55f), 0.3f), null, 0.5f); break;
                        case 'k': Breakable(Deco(decor, "Barrel", props[0], foot, new Vector2(0.75f, 0.55f), 0.3f), null, 0.5f); break;
                        case 'u': Breakable(Deco(decor, "Pot", props[2], foot, new Vector2(0.5f, 0.4f), 0.25f), props[3], 0.6f); break;
                        case 'G': Deco(decor, "Grave", props[6], foot, new Vector2(0.7f, 0.4f), 0.25f); break;
                        case 'S':
                        {
                            var go = Deco(decor, "Sign", props[4], foot, new Vector2(0.7f, 0.35f), 0.2f);
                            var s = go.AddComponent<Sign>();
                            s.text = d.signs.TryGetValue(new Vector2Int(x, row), out var txt) ? txt : "...";
                            break;
                        }
                        case 'C':
                        {
                            var go = Deco(decor, "Chest", chest[0], foot, new Vector2(0.85f, 0.55f), 0.3f);
                            var ch = go.AddComponent<Chest>();
                            ch.frames = chest; ch.coins = 4 + rng.Next(4); ch.potions = rng.Next(3) == 0 ? 1 : 0; ch.arrows = rng.Next(2) == 0 ? 6 : 0;
                            if (ch.potions == 0 && ch.arrows == 0) ch.potions = 1;
                            break;
                        }
                        case 'L': Loop(Deco(decor, "Torch", torch[0], foot, new Vector2(0.35f, 0.25f), 0.15f), torch, 8); break;
                        case 'F': Loop(Deco(decor, "Campfire", fire[0], foot, new Vector2(0.75f, 0.4f), 0.2f), fire, 8); break;
                        case 'l': Deco(decor, "Lantern", One(PROPS + "prop_lantern_post_16x32.png"), foot, new Vector2(0.35f, 0.25f), 0.15f); break;
                        case 'R': Deco(decor, "RuinWall", One(DECO + "deco_ruin_wall_32x32.png"), foot, new Vector2(1.8f, 0.6f), 0.35f); break;
                        case 'I': Deco(decor, "Pillar", One(DECO + "deco_ruin_pillar_16x32.png"), foot, new Vector2(0.75f, 0.45f), 0.25f); break;
                        case 'O': Loop(Deco(decor, "Obelisk", obelisk[0], foot, new Vector2(0.75f, 0.45f), 0.25f), obelisk, 6); break;
                        case 'f': Deco(decor, "Fence", fence[1], foot + new Vector3(0, 0.5f, 0), new Vector2(1f, 0.3f), -0.15f); break;
                        case 'h': Spawn("Potion", items, mid); break;
                        case 'a': { var p = Spawn("ArrowBundle", items, mid); p.GetComponent<Pickup>().amount = 6; break; }
                        case '$': Spawn("Coin", items, mid); break;
                        case 'E':
                        {
                            if (d.E(x - 1, row) == 'E') break;          // merged with the cell on its left
                            int w = 1; while (d.E(x + w, row) == 'E') w++;
                            var go = new GameObject("Exit");
                            go.transform.SetParent(world, false);
                            go.transform.position = new Vector3(x + w / 2f, d.h - 1 - row + 0.5f, 0);
                            var bc = go.AddComponent<BoxCollider2D>(); bc.isTrigger = true; bc.size = new Vector2(w, 1);
                            var ex = go.AddComponent<LevelExit>(); ex.requireAllEnemies = requireClear;
                            ex.lockedMessage = "";
                            var fx = new GameObject("glow"); fx.transform.SetParent(go.transform, false);
                            var sr = fx.AddComponent<SpriteRenderer>(); sr.sprite = sparkle[0]; sr.sortingOrder = 5;
                            Loop(fx, sparkle, 8);
                            break;
                        }
                    }
                }
        }

        static void Breakable(GameObject go, Sprite broken, float coin)
        {
            var b = go.AddComponent<Breakable>(); b.broken = broken; b.coinChance = coin;
        }

        // ================================================================ project
        static void ConfigureProject()
        {
            PlayerSettings.productName = "La Espada del Bosque";
            PlayerSettings.companyName = "WoodsGame";
            PlayerSettings.defaultScreenWidth = 1280;
            PlayerSettings.defaultScreenHeight = 720;
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.resizableWindow = true;
            PlayerSettings.runInBackground = true;
            // legacy Input Manager (the game reads UnityEngine.Input)
            var ps = AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/ProjectSettings.asset").FirstOrDefault();
            if (ps != null)
            {
                var so = new SerializedObject(ps);
                var p = so.FindProperty("activeInputHandler");
                if (p != null && p.intValue == 1) { p.intValue = 2; so.ApplyModifiedPropertiesWithoutUndo(); }
            }
            QualitySettings.antiAliasing = 0;
        }

        static void Ensure(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;
            var parent = Path.GetDirectoryName(path).Replace('\\', '/');
            Ensure(parent);
            AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
        }
    }
}
