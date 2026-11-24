// RPG layer of the builder: knight classes, regional enemy prefabs, lighting assets, house interiors and night lights.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace WoodsGame.EditorTools
{
    public static partial class GameBuilder
    {
        const string INT = "Assets/Art/World/Interiors/";

        // ================================================================ assets: classes, enemies, lighting
        static void BuildRpgAssets(GameAssets a)
        {
            // knight classes -> controllers + preview frames
            a.classControllers = KnightClass.All.Select(k => AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>($"{Anims}/{k.sprite}/{k.sprite}.controller")).ToArray();
            a.classIdle = KnightClass.All.Select(k => new GameAssets.FrameSet { frames = Sheet($"{Chars}/{k.sprite}/Idle/{k.sprite}_Idle_Down.png") }).ToArray();
            a.classWalk = KnightClass.All.Select(k => new GameAssets.FrameSet { frames = Sheet($"{Chars}/{k.sprite}/Walk/{k.sprite}_Walk_Down.png") }).ToArray();
            for (int i = 0; i < KnightClass.All.Length; i++)
                if (a.classControllers[i] == null) Debug.LogError("[GameBuilder] missing class controller for " + KnightClass.All[i].sprite);

            // lighting
            a.lightSprite = One(FX + "light_radial.png");
            a.matMultiply = MaterialAsset("M_NightMultiply", "Woods/SpriteMultiply");
            a.matAdditive = MaterialAsset("M_LightAdditive", "Woods/SpriteAdditive");
            a.rpgIcons = Sheet(UI + "Icons/ui_icons_rpg_16x16.png");
            a.windowFrames = Sheet(INT + "Furniture/window_22x20.png");

            // equipment + minimal flat UI (replaces the wooden frames everywhere)
            a.itemIcons = Sheet(UI + "Icons/ui_items_16x16.png");
            a.itemIconsLarge = Sheet(UI + "Icons/ui_items_32x32.png");
            BuildCombatData(a);                        // weapon effects, attack data, weapon sets (GameBuilder.Combat.cs)
            a.flatPanel = One(UI + "Flat/ui_flat_panel_9s3.png");
            var flatSlots = Sheet(UI + "Flat/ui_flat_slot_12x12_9s3.png");
            a.flatSlot = flatSlots.Length > 0 ? flatSlots[0] : null; a.flatSlotSelected = flatSlots.Length > 1 ? flatSlots[1] : a.flatSlot;
            if (a.flatPanel) { a.panel = a.flatPanel; a.dialog = a.flatPanel; }
            if (a.flatSlot) { a.slot = a.flatSlot; a.slotSelected = a.flatSlotSelected; }
            if (a.itemIcons.Length < ItemDB.All.Length) Debug.LogError("[GameBuilder] item icons missing");

            // regional enemies (the three base types were made in BuildAssetsAndPrefabs; here their AI + all the variants)
            var list = new List<GameObject>();
            void Enemy(string name, string sprite, EnemyKind kind, AIProfile ai, Action<EnemyController> cfg, int scale = 1)
            {
                list.Add(ActorPrefab(name, sprite, true, scale, go =>
                {
                    var e = go.AddComponent<EnemyController>();
                    e.kind = kind; e.typeId = name; e.ai = ai;
                    cfg(e);
                    DecorateEnemy(go, name);          // glowing eyes + aura per type (GameBuilder.Bosses.cs)
                }));
            }
            Enemy("Orc", "Orc", EnemyKind.Orc, AIProfile.Pack, e =>
            {
                e.displayName = "ORCO"; e.maxHP = 6; e.damage = 2; e.walkSpeed = 1.6f; e.chaseSpeed = 2.4f; e.aggroRange = 4.5f; e.attackRange = 1.0f;
                e.attackCooldown = 1.3f; e.heavyChance = 0.3f; e.coins = 2; e.xpReward = 3;
            });
            Enemy("OrcBerserker", "OrcBerserker", EnemyKind.Orc, AIProfile.Charger, e =>
            {
                e.displayName = "ORCO BERSERKER"; e.maxHP = 11; e.damage = 3; e.walkSpeed = 1.7f; e.chaseSpeed = 2.6f; e.aggroRange = 6f; e.attackRange = 1.05f;
                e.attackCooldown = 1.1f; e.heavyChance = 0.5f; e.knockbackResist = 0.5f; e.coins = 4; e.xpReward = 7;
            });
            Enemy("OrcDesert", "OrcDesert", EnemyKind.Orc, AIProfile.Skirmisher, e =>
            {
                e.displayName = "ORCO DEL DESIERTO"; e.maxHP = 7; e.damage = 2; e.walkSpeed = 1.9f; e.chaseSpeed = 2.9f; e.aggroRange = 5.5f; e.attackRange = 1.0f;
                e.attackCooldown = 1.0f; e.heavyChance = 0.2f; e.coins = 3; e.xpReward = 4;
            });
            Enemy("OrcFrost", "OrcFrost", EnemyKind.Orc, AIProfile.Brute, e =>
            {
                e.displayName = "ORCO DE HIELO"; e.maxHP = 13; e.damage = 3; e.walkSpeed = 1.3f; e.chaseSpeed = 2.0f; e.aggroRange = 5f; e.attackRange = 1.1f;
                e.attackCooldown = 1.5f; e.heavyChance = 0.55f; e.knockbackResist = 0.6f; e.coins = 4; e.xpReward = 6;
            });
            Enemy("OrcCorsair", "OrcCorsair", EnemyKind.Orc, AIProfile.Pack, e =>
            {
                e.displayName = "ORCO CORSARIO"; e.maxHP = 8; e.damage = 2; e.walkSpeed = 1.7f; e.chaseSpeed = 2.6f; e.aggroRange = 5.5f; e.attackRange = 1.0f;
                e.attackCooldown = 1.1f; e.heavyChance = 0.35f; e.coins = 5; e.xpReward = 5; e.arrowChance = 0.4f;
            });
            Enemy("BloodMonster", "BloodMonster", EnemyKind.BloodMonster, AIProfile.Kiter, e =>
            {
                e.displayName = "MONSTRUO DE SANGRE"; e.maxHP = 5; e.damage = 1; e.walkSpeed = 1.4f; e.chaseSpeed = 2.0f; e.aggroRange = 5.5f; e.attackRange = 0.9f;
                e.attackCooldown = 1.4f; e.heavyChance = 0.25f; e.ranged = true; e.rangedMin = 2.2f; e.rangedMax = 5.5f; e.rangedCooldown = 2.8f; e.rangedDamage = 1;
                e.coins = 2; e.xpReward = 3;
            });
            Enemy("BloodToxic", "BloodToxic", EnemyKind.BloodMonster, AIProfile.Ambusher, e =>
            {
                e.displayName = "LIMO TÓXICO"; e.maxHP = 6; e.damage = 2; e.walkSpeed = 1.3f; e.chaseSpeed = 2.4f; e.aggroRange = 4.5f; e.attackRange = 0.9f;
                e.attackCooldown = 1.2f; e.heavyChance = 0.3f; e.coins = 3; e.xpReward = 4; e.potionChance = 0.2f;
            });
            Enemy("BloodMagma", "BloodMagma", EnemyKind.BloodMonster, AIProfile.Bomber, e =>
            {
                e.displayName = "ENGENDRO DE MAGMA"; e.maxHP = 8; e.damage = 2; e.walkSpeed = 1.4f; e.chaseSpeed = 2.1f; e.aggroRange = 6f; e.attackRange = 0.9f;
                e.attackCooldown = 1.4f; e.ranged = true; e.rangedMin = 2.4f; e.rangedMax = 6f; e.rangedCooldown = 2.4f; e.rangedDamage = 2; e.coins = 4; e.xpReward = 6;
            });
            Enemy("Demon", "Demon", EnemyKind.Demon, AIProfile.Caster, e =>
            {
                e.displayName = "DEMONIO"; e.maxHP = 9; e.damage = 2; e.walkSpeed = 1.7f; e.chaseSpeed = 2.6f; e.aggroRange = 5.5f; e.attackRange = 1.1f;
                e.attackCooldown = 1.2f; e.heavyChance = 0.35f; e.ranged = true; e.rangedMin = 2.5f; e.rangedMax = 6.5f; e.rangedCooldown = 3.2f; e.rangedDamage = 2;
                e.coins = 4; e.potionChance = 0.25f; e.xpReward = 6;
            });
            Enemy("DemonAsh", "DemonAsh", EnemyKind.Demon, AIProfile.Brute, e =>
            {
                e.displayName = "DEMONIO DE CENIZA"; e.maxHP = 15; e.damage = 3; e.walkSpeed = 1.5f; e.chaseSpeed = 2.3f; e.aggroRange = 6f; e.attackRange = 1.15f;
                e.attackCooldown = 1.3f; e.heavyChance = 0.5f; e.knockbackResist = 0.5f; e.ranged = true; e.rangedMin = 2.5f; e.rangedMax = 7f; e.rangedCooldown = 3.5f;
                e.rangedDamage = 2; e.coins = 6; e.potionChance = 0.3f; e.xpReward = 9;
            });
            Enemy("DemonWraith", "DemonWraith", EnemyKind.Demon, AIProfile.Wraith, e =>
            {
                e.displayName = "ESPECTRO"; e.maxHP = 7; e.damage = 2; e.walkSpeed = 2.0f; e.chaseSpeed = 3.0f; e.aggroRange = 7.5f; e.attackRange = 1.0f;
                e.attackCooldown = 1.3f; e.heavyChance = 0.2f; e.coins = 3; e.xpReward = 6; e.activeAt = ActiveTime.Night; e.arrowChance = 0.1f;
            });
            Enemy("KnightFallen", "KnightFallen", EnemyKind.Demon, AIProfile.Duelist, e =>
            {
                e.displayName = "CABALLERO CAÍDO"; e.maxHP = 13; e.damage = 3; e.walkSpeed = 1.8f; e.chaseSpeed = 2.7f; e.aggroRange = 6.5f; e.attackRange = 1.0f;
                e.attackCooldown = 1.0f; e.heavyChance = 0.35f; e.coins = 6; e.potionChance = 0.35f; e.xpReward = 9; e.activeAt = ActiveTime.Night;
            });
            list.Add(SummonerPrefab());                                   // El Invocador (GameBuilder.Camps.cs)
            list.AddRange(RosterEnemyPrefabs());                          // new roster monsters (GameBuilder.Roster.cs)
            a.enemyPrefabs = list.ToArray();
            // crafting, camps, summoning
            a.matIcons = Sheet(UI + "Icons/ui_materials_16x16.png");
            a.gatherFrames = WSheet("Props/gather_anim_16x16.png");
            a.summonFx = Sheet(FX + "fx_demon_summon_circle_anim_32x32.png");
            if (a.matIcons.Length < CraftDB.Mats.Length) Debug.LogError("[GameBuilder] material icons missing (python Tools/ArtGen2/camp.py)");
        }

        static Material MaterialAsset(string name, string shader)
        {
            string path = $"{GameRoot}/Resources/{name}.mat";
            var sh = Shader.Find(shader);
            if (sh == null) { Debug.LogError("[GameBuilder] shader not found: " + shader); return null; }
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(sh); AssetDatabase.CreateAsset(m, path); }
            m.shader = sh;
            EditorUtility.SetDirty(m);
            return m;
        }

        /// <summary>Map residents ('o','b','d') become the regional variant of their kind.</summary>
        static string RegionalType(char c, char region)
        {
            switch (c)
            {
                case 'o': return region == 'e' ? "OrcFrost" : region == 'f' ? "OrcDesert" : region == 'j' ? "OrcCorsair" : region == 'h' ? "OrcBerserker" : "Orc";
                case 'b': return region == 'c' || region == 'a' ? "BloodToxic" : region == 'g' ? "BloodMagma" : "BloodMonster";
                default: return region == 'g' || region == 'f' ? "DemonAsh" : "Demon";
            }
        }

        // ================================================================ interiors
        class RoomTemplate { public string name; public int w, h; public string[] rows; public List<(string item, float x, float y, bool wall)> items = new List<(string, float, float, bool)>(); }

        static Dictionary<string, RoomTemplate> LoadRooms()
        {
            var rooms = new Dictionary<string, RoomTemplate>();
            var lines = File.ReadAllLines(Path.Combine(ProjectRoot, GameRoot, "Levels", "Interiors.txt"));
            RoomTemplate cur = null; var rows = new List<string>();
            foreach (var l in lines)
            {
                if (l.StartsWith("#") || l.Length == 0) continue;
                if (l.StartsWith("INTERIOR "))
                {
                    var p = l.Split(' ');
                    cur = new RoomTemplate { name = p[1], w = int.Parse(p[2]), h = int.Parse(p[3]) }; rows.Clear();
                }
                else if (l.StartsWith("ITEM ") && cur != null)
                {
                    var p = l.Split(' ');
                    cur.items.Add((p[1], float.Parse(p[2], System.Globalization.CultureInfo.InvariantCulture),
                                   float.Parse(p[3], System.Globalization.CultureInfo.InvariantCulture), p.Length > 4 && p[4] == "wall"));
                }
                else if (l == "END" && cur != null) { cur.rows = rows.ToArray(); rooms[cur.name] = cur; cur = null; }
                else if (cur != null) rows.Add(l);
            }
            return rooms;
        }

        static readonly Dictionary<Vector2Int, string> HouseTemplates = new Dictionary<Vector2Int, string>
        {
            { new Vector2Int(50, 99), "posada" }, { new Vector2Int(130, 102), "herreria" },
            { new Vector2Int(154, 25), "cuartel" }, { new Vector2Int(172, 25), "biblioteca" }, { new Vector2Int(167, 30), "capilla" },
            { new Vector2Int(172, 31), "herreria" }, { new Vector2Int(159, 30), "casa" },
        };

        static readonly Dictionary<string, string> RoomTitles = new Dictionary<string, string>
        {
            { "casa", "CASA" }, { "cabana", "CABAÑA" }, { "posada", "POSADA DEL JABALÍ" }, { "herreria", "HERRERÍA" },
            { "cuartel", "CUARTEL DEL REY" }, { "capilla", "CAPILLA" }, { "biblioteca", "BIBLIOTECA DEL SABIO" },
        };

        static readonly string[] Lore =
        {
            "CRÓNICA DEL REINO: EL SEÑOR DEMONIO DESPERTÓ BAJO EL MONTE CENIZA Y SU CORRUPCIÓN SE EXTIENDE CADA NOCHE.",
            "DICEN QUE LOS ESPECTROS SON LAS ALMAS DE LOS QUE CAYERON EN LA NIEBLA. HUYEN DEL PRIMER RAYO DE SOL.",
            "MANUAL DEL CABALLERO: EL ORCO DE HIELO GOLPEA FUERTE PERO LENTO. RUEDA Y CONTRAATACA.",
            "EL LIMO TÓXICO SE ESCONDE EN LA HIERBA DEL LAGO. SI VES UN BRILLO VERDE, NO TE ACERQUES SIN TU ESPADA.",
            "CUANTOS MÁS MONSTRUOS CAEN, MÁS VIENEN. LA OSCURIDAD RESPONDE A LA MATANZA CON CRIATURAS MÁS PODEROSAS.",
            "EL SELLO DEL MONTE CENIZA SOLO CAERÁ CUANDO EL JEFE ORCO Y LA MADRE DE SANGRE HAYAN SIDO DERROTADOS.",
            "LOS CABALLEROS CAÍDOS AÚN RECUERDAN SU ENTRENAMIENTO: BLOQUEAN Y ESQUIVAN. GOLPÉALOS POR LA ESPALDA.",
            "LOS ENGENDROS DE MAGMA EXPLOTAN AL MORIR. ALÉJATE EN CUANTO CAIGAN.",
        };

        static readonly (string room, string cls, float x, float y, string text)[] Npcs =
        {
            ("posada", "Soldier", 4.5f, 2.5f, "POSADERO: ¡BIENVENIDO AL JABALÍ! LAS CAMAS DE ARRIBA SON GRATIS PARA LOS HÉROES. DORMIR RESTAURA Y GUARDA."),
            ("cuartel", "KnightPaladin", 9f, 6f, "PALADÍN: DE NOCHE LOS CABALLEROS CAÍDOS PATRULLAN LA CIUDADELA. NO VAYAS SIN POCIONES."),
            ("cuartel", "KnightRanger", 14f, 8f, "MONTARAZ: SUBE TUS ATRIBUTOS CON C AL SUBIR DE NIVEL. LA DESTREZA HACE QUE TUS FLECHAS SEAN CRÍTICAS."),
            ("capilla", "KnightPaladin", 9.6f, 4.3f, "SACERDOTE: REZA EN EL ALTAR Y TU VIDA Y TUS POCIONES SERÁN RESTAURADAS."),
            ("biblioteca", "KnightDark", 13.5f, 6.5f, "SABIO: CADA REGIÓN TIENE SUS PROPIAS CRIATURAS, Y LA NOCHE TRAE OTRAS. LEE MIS LIBROS, APRENDERÁS."),
            ("herreria", "KnightDark", 7.5f, 5.2f, "HERRERO: USA EL YUNQUE Y TE VENDERÉ MEJORAS PARA TU ESPADA Y TU ARMADURA."),
        };

        /// <summary>One room per house, built out past the east edge of the map (x &gt;= baseX). Returns the rooms
        /// keyed by the house's foot cell (x, row) so other builders can place people in them.</summary>
        static Dictionary<Vector2Int, Interior> BuildInteriors(List<(GameObject house, char c, int x, int row, Vector3 foot)> houses, Transform world,
            Dictionary<Vector2Int, string> templates = null, float baseX = 300)
        {
            var rooms = LoadRooms();
            var root = new GameObject("Interiors").transform; root.SetParent(world);
            var chest = WSheet("Props/chest_anim_16x16.png");
            var black = One("Assets/Art/Game/shadow_blob.png");
            int i = 0;
            var built = new Dictionary<Vector2Int, Interior>();
            foreach (var h in houses)
            {
                string key = (templates ?? HouseTemplates).TryGetValue(new Vector2Int(h.x, h.row), out var k) ? k : h.c == '8' ? "cabana" : "casa";
                if (!rooms.TryGetValue(key, out var t)) { Debug.LogWarning("[GameBuilder] no interior template " + key); continue; }
                float X0 = baseX + (i % 4) * 34, Y0 = 20 + (i / 4) * 26;
                i++;
                var room = new GameObject($"Interior_{key}_{h.x}_{h.row}").transform; room.SetParent(root);
                var info = room.gameObject.AddComponent<Interior>();
                info.template = key; info.title = RoomTitles.TryGetValue(key, out var title) ? title : "CASA";
                info.bounds = new Rect(X0, Y0, t.w, t.h);
                built[new Vector2Int(h.x, h.row)] = info;

                // backdrop + painted shell
                var bd = Deco(room, "Backdrop", DayNightLighting_White(), new Vector3(X0 + t.w / 2f, Y0 + t.h / 2f, 0), default, 0, -150);
                bd.transform.localScale = new Vector3(t.w + 26, t.h + 26, 1); bd.GetComponent<SpriteRenderer>().color = new Color32(0x0c, 0x0a, 0x14, 0xff);
                Deco(room, "Room", One(INT + $"room_{key}.png"), new Vector3(X0 + t.w / 2f, Y0 + t.h / 2f, 0), default, 0, -100);

                // walls: merged horizontal runs of solid tiles
                for (int gy = 0; gy < t.h; gy++)
                {
                    int gx = 0;
                    while (gx < t.w)
                    {
                        if ("WB".IndexOf(t.rows[gy][gx]) < 0) { gx++; continue; }
                        int start = gx; while (gx < t.w && "WB".IndexOf(t.rows[gy][gx]) >= 0) gx++;
                        var wall = new GameObject("Wall"); wall.transform.SetParent(room, false);
                        wall.transform.position = new Vector3(X0 + (start + gx) / 2f, Y0 + t.h - gy - 0.5f, 0);
                        wall.AddComponent<BoxCollider2D>().size = new Vector2(gx - start, 1);
                    }
                }
                // exit mat
                for (int gy = 0; gy < t.h; gy++)
                    for (int gx = 0; gx < t.w; gx++)
                        if (t.rows[gy][gx] == 'D')
                        {
                            var ex = new GameObject("Exit"); ex.transform.SetParent(room, false);
                            ex.transform.position = new Vector3(X0 + gx + 0.5f, Y0 + t.h - gy - 0.3f, 0);
                            var bc = ex.AddComponent<BoxCollider2D>(); bc.isTrigger = true; bc.size = new Vector2(1f, 0.6f);
                            ex.AddComponent<InteriorExit>().interior = info;
                            ex.GetComponent<InteriorExit>().promptHeight = 1.0f;
                            info.entry = new Vector2(X0 + gx + 0.5f, Y0 + t.h - gy + 0.9f);
                        }
                info.outside = (Vector2)h.foot + new Vector2(0, -0.7f);

                // furniture
                int lore = (h.x * 7 + h.row) % Lore.Length;
                foreach (var it in t.items) PlaceFurniture(room, it, X0, Y0, t.h, chest, ref lore, h.x, h.row);
                // the people who live and work in the houses are NpcDB townsfolk with routines (GameBuilder.Camps.cs: PlaceVillagers)

                // the house's front door in the world
                var door = new GameObject("Door"); door.transform.SetParent(h.house.transform, false);
                door.transform.position = h.foot + new Vector3(0, 0.35f, 0);
                var hd = door.AddComponent<HouseDoor>(); hd.interior = info; hd.promptHeight = 1.6f;
                // warm windows at night
                LightGlow.Attach(h.house.transform, new Vector2(-1.3f, 1.5f), 1.6f, new Color(1f, 0.75f, 0.35f), 0.6f);
                LightGlow.Attach(h.house.transform, new Vector2(1.3f, 1.5f), 1.6f, new Color(1f, 0.75f, 0.35f), 0.6f);
            }
            return built;
        }

        static Sprite DayNightLighting_White()
        {
            // a 4x4 white sprite asset for backdrops (runtime-created sprites can't be saved in scenes)
            string p = GameRoot + "/Tiles/white_4x4.png";
            string full = Path.Combine(ProjectRoot, p);
            if (!File.Exists(full))
            {
                var t = new Texture2D(4, 4, TextureFormat.RGBA32, false);
                var px = Enumerable.Repeat(new Color32(255, 255, 255, 255), 16).ToArray(); t.SetPixels32(px); t.Apply();
                File.WriteAllBytes(full, t.EncodeToPNG());
                AssetDatabase.ImportAsset(p);
                var ti = (TextureImporter)AssetImporter.GetAtPath(p);
                ti.textureType = TextureImporterType.Sprite; ti.spritePixelsPerUnit = 4; ti.filterMode = FilterMode.Point; ti.SaveAndReimport();
            }
            return One(p);
        }

        static void PlaceFurniture(Transform room, (string item, float x, float y, bool wall) it, float X0, float Y0, int H, Sprite[] chest, ref int lore, int hx, int hrow)
        {
            string n = it.item;
            float wx = X0 + it.x;
            // foot = bottom of tile row y;  wall items: centred on row y
            float footY = Y0 + H - 1 - it.y;
            Sprite[] frames = null; Sprite s = null;
            switch (n)
            {
                case "fireplace": frames = Sheet(INT + "Furniture/fireplace_anim_40x46.png"); break;
                case "forge": frames = Sheet(INT + "Furniture/forge_anim_42x44.png"); break;
                case "candle": frames = Sheet(INT + "Furniture/candle_anim_10x24.png"); break;
                case "cauldron": frames = Sheet(INT + "Furniture/cauldron_anim_22x22.png"); break;
                case "window": frames = Sheet(INT + "Furniture/window_22x20.png"); break;
                case "chest": frames = chest; break;
                default: s = One(INT + $"Furniture/{n}.png"); break;
            }
            if (s == null && (frames == null || frames.Length == 0)) { Debug.LogWarning("[GameBuilder] missing furniture " + n); return; }
            var sprite = s ?? frames[0];
            float hU = sprite.rect.height / 16f, wU = sprite.rect.width / 16f;
            Vector3 pos = it.wall ? new Vector3(wx, Y0 + H - it.y - hU / 2f, 0) : new Vector3(wx, footY, 0);
            bool solid = !it.wall && n != "chair" && n != "stool" && n != "candle" && n != "plant";
            Vector2 col = solid ? new Vector2(wU * 0.85f, Mathf.Min(hU * 0.45f, n.StartsWith("bed") || n == "bunk" ? 1.7f : 0.9f)) : default;
            var go = Deco(room, n, sprite, pos, col, col.y / 2f, it.wall ? -90 : 0);
            if (n == "fireplace" || n == "forge" || n == "candle" || n == "cauldron") Loop(go, frames, n == "candle" ? 8 : 10);
            if (n == "window") { var dn = go.AddComponent<DayNightSprite>(); dn.day = frames[0]; dn.night = frames.Length > 1 ? frames[1] : frames[0]; }
            if (n == "fireplace") LightGlow.Attach(go.transform, new Vector2(0, 1.0f), 4.5f, new Color(1f, 0.6f, 0.25f), 0.55f, true);
            if (n == "forge") LightGlow.Attach(go.transform, new Vector2(0, 1.4f), 4.5f, new Color(1f, 0.5f, 0.2f), 0.6f, true);
            if (n == "candle") LightGlow.Attach(go.transform, new Vector2(0, 1.4f), 2.2f, new Color(1f, 0.8f, 0.4f), 0.45f, true);
            switch (n)
            {
                case "bed_double": case "bed_single": case "bunk":
                    go.AddComponent<Bed>().promptHeight = hU + 0.2f; break;
                case "chest":
                {
                    var ch = go.AddComponent<Chest>(); ch.frames = chest; ch.promptHeight = 1.3f;
                    ch.coins = 4 + (hx + hrow) % 7; ch.potions = (hx + hrow) % 2; ch.arrows = (hx * 3 + hrow) % 3 == 0 ? 8 : 0;
                    break;
                }
                case "bookshelf": case "lectern": case "globe":
                    go.AddComponent<Sign>().text = Lore[lore++ % Lore.Length]; go.GetComponent<Sign>().promptHeight = hU + 0.2f; break;
                case "anvil": { var sh = go.AddComponent<ShopStall>(); sh.promptHeight = hU + 0.4f; sh.smith = true; break; }
                case "counter":
                    go.AddComponent<ShopStall>().promptHeight = hU + 0.4f; break;
                case "altar":
                    go.AddComponent<Altar>().promptHeight = hU + 0.2f; break;
                case "dummy":
                    go.AddComponent<Sign>().text = "MUÑECO DE PRÁCTICAS: J ESPADA, PULSA DOS VECES PARA EL COMBO. K GOLPE FUERTE. ESPACIO PARA RODAR."; break;
            }
        }

        static void PlaceNpc(Transform room, string cls, Vector3 pos, string text)
        {
            var go = new GameObject("NPC_" + cls); go.transform.SetParent(room, false); go.transform.position = pos;
            var spr = new GameObject("Sprite"); spr.transform.SetParent(go.transform, false);
            var sr = spr.AddComponent<SpriteRenderer>(); sr.sprite = Cell($"{Chars}/{cls}/Idle/{cls}_Idle_Down.png", 0);
            spr.AddComponent<AnimationEventHandler>();
            var an = spr.AddComponent<Animator>(); an.runtimeAnimatorController = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>($"{Anims}/{cls}/{cls}.controller");
            var sh = new GameObject("Shadow"); sh.transform.SetParent(go.transform, false);
            var ssr = sh.AddComponent<SpriteRenderer>(); ssr.sprite = One("Assets/Art/Game/shadow_blob.png"); ssr.sortingOrder = -1; sh.transform.localPosition = new Vector3(0, 0.05f, 0);
            var col = go.AddComponent<CircleCollider2D>(); col.radius = 0.3f; col.offset = new Vector2(0, 0.2f);
            go.AddComponent<Sign>().text = text; go.GetComponent<Sign>().promptHeight = 1.5f;
            go.AddComponent<NpcIdle>();
        }

        /// <summary>Campfires, torches and lava get a glow that shows at night.</summary>
        static void AddWorldLights(Transform world)
        {
            foreach (var cf in world.GetComponentsInChildren<Campfire>(true))
                LightGlow.Attach(cf.transform, new Vector2(0, 0.4f), 4.5f, new Color(1f, 0.62f, 0.28f), 0.75f);
            foreach (var sr in world.GetComponentsInChildren<SpriteRenderer>(true))
                if (sr.sprite != null && sr.sprite.name.StartsWith("torch_anim") && sr.GetComponent<LightGlow>() == null
                    && sr.transform.parent != null && sr.transform.parent.name != "Underground")
                    LightGlow.Attach(sr.transform, new Vector2(0, 1.8f), 3f, new Color(1f, 0.7f, 0.3f), 0.7f);
        }
    }
}
