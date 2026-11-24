// Bosses, their lairs and enemy auras (2026-11-20).
//   * Boss prefabs use the big 128 px sheets of Tools/CharAnim/bosses.py. The root keeps scale 2 (so all combat maths stay as
//     before) and the sprite child is scaled 0.5, so the art shows at its native pixel size.
//   * Every boss gets a BossBrain (phases + signature moves) and an arena: painted floor, rune circle, pillars with banners,
//     braziers, light beams, fog and debris in the boss's theme, and a rune wall (BossArena) that seals the fight.
//   * Regional enemies get an EnemyAura (glowing eyes, ground halo, motes) - their silhouettes come from features.py.
// Art: Tools/ArtGen2/arena.py (arena + boss HUD), Tools/GameGen/music_boss.py (boss theme + sfx).
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace WoodsGame.EditorTools
{
    public static partial class GameBuilder
    {
        const string ARENA = "Assets/Art/World/Arena/";

        class ArenaDef
        {
            public string prefab, title, subtitle, objective; public int theme;
            public Color tint, fog, glow;
        }

        static readonly ArenaDef[] ArenaDefs =
        {
            new ArenaDef { prefab = "Summoner", theme = 0, title = "EL INVOCADOR", subtitle = "SEÑOR DE LOS SIERVOS CAÍDOS", objective = "Derrota al Invocador",
                tint = new Color(0.62f, 0.52f, 0.9f), fog = new Color(0.5f, 0.25f, 0.85f, 0.32f), glow = new Color(0.7f, 0.35f, 1f) },
            new ArenaDef { prefab = "OrcChieftain", theme = 1, title = "GORGRAK EL CAUDILLO", subtitle = "SEÑOR DE LAS ARENAS ROJAS", objective = "Derrota a Gorgrak",
                tint = new Color(1f, 0.78f, 0.6f), fog = new Color(0.9f, 0.6f, 0.3f, 0.22f), glow = new Color(1f, 0.6f, 0.2f) },
            new ArenaDef { prefab = "BloodMother", theme = 2, title = "MADRE DE SANGRE", subtitle = "EL CORAZÓN DEL PANTANO CARMESÍ", objective = "Derrota a la Madre de Sangre",
                tint = new Color(0.85f, 0.6f, 0.68f), fog = new Color(0.7f, 0.15f, 0.3f, 0.3f), glow = new Color(1f, 0.25f, 0.35f) },
            new ArenaDef { prefab = "DemonLord", theme = 3, title = "SEÑOR DEMONIO", subtitle = "EL FUEGO BAJO EL MONTE CENIZA", objective = "Derrota al Señor Demonio",
                tint = new Color(0.95f, 0.62f, 0.5f), fog = new Color(0.45f, 0.12f, 0.08f, 0.32f), glow = new Color(1f, 0.45f, 0.1f) },
            new ArenaDef { prefab = "FrostColossus", theme = 4, title = "COLOSO DE ESCARCHA", subtitle = "EL CORAZÓN HELADO DE LOS PICOS", objective = "Derrota al Coloso de Escarcha",
                tint = new Color(0.75f, 0.86f, 1f), fog = new Color(0.85f, 0.93f, 1f, 0.3f), glow = new Color(0.4f, 0.85f, 1f) },
        };

        static readonly Vector2Int FrostTile = new Vector2Int(66, 17);     // World2.txt: Picos Nevados, open snowfield by the north road

        // ================================================================ prefabs
        /// <summary>Common boss setup inside an ActorPrefab configure callback (root scale 2 is applied afterwards).</summary>
        static void BossLook(GameObject go, string pattern, Color fx, string[] minions, float colRadius, float bodyHeight)
        {
            var spr = go.transform.Find("Sprite");
            if (spr) spr.localScale = new Vector3(0.5f, 0.5f, 1);
            var sh = go.transform.Find("Shadow");
            if (sh) sh.localScale = new Vector3(1.7f, 1.3f, 1);
            var col = go.GetComponent<CircleCollider2D>(); col.radius = colRadius; col.offset = new Vector2(0, 0.2f);
            var e = go.GetComponent<EnemyController>();
            e.bodyHeight = bodyHeight;
            var b = go.AddComponent<BossBrain>();
            b.pattern = pattern; b.fxColor = fx; b.minions = minions;
            var aura = go.AddComponent<EnemyAura>();
            aura.color = fx; aura.eyeHeight = bodyHeight + 0.35f; aura.groundRadius = 1.6f; aura.motes = 8; aura.falling = pattern == "colossus";
        }

        static GameObject FrostColossusPrefab()
        {
            return ActorPrefab("FrostColossus", "BossFrostColossus", true, 2, go =>
            {
                var e = go.AddComponent<EnemyController>();
                e.kind = EnemyKind.Orc; e.typeId = "FrostColossus"; e.ai = AIProfile.Brute; e.displayName = "COLOSO DE ESCARCHA";
                e.isBoss = true; e.bossFlag = "boss_F"; e.maxHP = 80; e.damage = 4; e.walkSpeed = 1.2f; e.chaseSpeed = 1.7f;
                e.aggroRange = 7f; e.attackRange = 1.25f; e.attackCooldown = 1.4f; e.heavyChance = 0.55f; e.knockbackResist = 0.9f; e.xpReward = 70;
                e.coins = 0; e.potionChance = 0; e.arrowChance = 0;
                BossLook(go, "colossus", new Color(0.45f, 0.85f, 1f), new[] { "OrcFrost" }, 0.42f, 1.1f);
            });
        }

        /// <summary>Glowing eyes + aura per regional enemy type (their silhouettes are drawn by Tools/CharAnim/features.py).</summary>
        static void DecorateEnemy(GameObject go, string type)
        {
            (Color c, int motes, float eye, bool fall)? cfg = type switch
            {
                "Orc" => (new Color(1f, 0.25f, 0.15f), 0, 0.85f, false),
                "OrcDesert" => (new Color(1f, 0.75f, 0.3f), 3, 0.85f, false),
                "OrcFrost" => (new Color(0.6f, 0.9f, 1f), 5, 0.9f, true),
                "OrcCorsair" => (new Color(0.4f, 1f, 0.85f), 2, 0.85f, false),
                "OrcBerserker" => (new Color(1f, 0.2f, 0.12f), 5, 0.85f, false),
                "Demon" => (new Color(0.8f, 0.4f, 1f), 3, 1.0f, false),
                "DemonAsh" => (new Color(1f, 0.55f, 0.15f), 6, 1.0f, false),
                "DemonWraith" => (new Color(0.6f, 0.85f, 1f), 6, 1.0f, false),
                "BloodMonster" => (new Color(1f, 0.3f, 0.4f), 2, 0.6f, false),
                "BloodToxic" => (new Color(0.7f, 1f, 0.3f), 4, 0.6f, false),
                "BloodMagma" => (new Color(1f, 0.5f, 0.1f), 6, 0.6f, false),
                "KnightFallen" => (new Color(0.45f, 1f, 0.95f), 4, 1.0f, false),
                _ => null,
            };
            if (cfg == null) return;
            var a = go.AddComponent<EnemyAura>();
            a.color = cfg.Value.c; a.motes = cfg.Value.motes; a.eyeHeight = cfg.Value.eye; a.falling = cfg.Value.fall; a.groundRadius = 0.8f;
        }

        /// <summary>Resources/BossAssets + the bosses that only exist here (called after BuildRpgAssets).</summary>
        static void BuildBossAssets()
        {
            string path = GameRoot + "/Resources/BossAssets.asset";
            var b = AssetDatabase.LoadAssetAtPath<BossAssets>(path);
            if (b == null) { b = ScriptableObject.CreateInstance<BossAssets>(); AssetDatabase.CreateAsset(b, path); }
            b.bossMusic = AssetDatabase.LoadAssetAtPath<AudioClip>(GameRoot + "/Audio/music_boss_loop.wav");
            b.wave = One(ARENA + "arena_wave.png");
            b.telegraph = One(ARENA + "arena_telegraph.png");
            b.runes = One(ARENA + "arena_runes.png");
            b.lightColumn = One(ARENA + "arena_lightcolumn.png");
            b.fog = One(ARENA + "arena_fog.png");
            b.barCap = One(UI + "Boss/ui_boss_cap.png");
            b.barTrack = One(UI + "Boss/ui_boss_track_9s3.png");
            b.barFill = One(UI + "Boss/ui_boss_fill.png");
            b.barCrest = One(UI + "Boss/ui_boss_crest.png");
            b.objectivePanel = One(UI + "Boss/ui_objective_9s4.png");
            b.objectiveIcon = One(UI + "Boss/ui_objective_icon.png");
            if (b.bossMusic == null || b.wave == null || b.barCap == null)
                Debug.LogError("[GameBuilder] boss art/audio missing (python Tools/ArtGen2/arena.py; python Tools/GameGen/music_boss.py)");
            EditorUtility.SetDirty(b);
            FrostColossusPrefab();
            BuildHeroPrefabs();                     // the roster's adventurers (GameBuilder.Roster.cs)
        }

        // ================================================================ arenas
        /// <summary>Called by BuildMapScene after nature and weather: places the Frost Colossus and builds a lair around every boss.</summary>
        static void BuildBossArenas(string id, LevelData d, Transform world)
        {
            PlaceAdventurers(id, d, world);         // heroes of the new roster in the towns (GameBuilder.Roster.cs)
            var actors = world.Find("Actors") ?? world;
            if (id == MapDB.World && !BossesIndoors)                // ERYNDOR: the Colossus waits in the Cripta de Escarcha
                Spawn("FrostColossus", actors, new Vector3(FrostTile.x + 0.5f, d.h - 1 - FrostTile.y, 0));
            var bosses = world.GetComponentsInChildren<EnemyController>(true).Where(e => e.isBoss).ToArray();
            foreach (var boss in bosses)
            {
                var src = PrefabUtility.GetCorrespondingObjectFromSource(boss.gameObject);
                var def = ArenaDefs.FirstOrDefault(a => src != null && a.prefab == src.name);
                if (def == null) { Debug.LogWarning("[GameBuilder] no arena for boss " + boss.name); continue; }
                BuildArena(def, d, world, boss);
            }
        }

        static float WalkableShare(LevelData d, Vector2 c, Vector2 size)
        {
            int n = 0, ok = 0;
            for (float y = -size.y; y <= size.y; y += 1f)
                for (float x = -size.x; x <= size.x; x += 1f)
                {
                    if (x * x / (size.x * size.x) + y * y / (size.y * size.y) > 1f) continue;
                    int tx = Mathf.FloorToInt(c.x + x), row = d.h - 1 - Mathf.FloorToInt(c.y + y);
                    n++;
                    if (WorldInfo.SolidTerrain.IndexOf(d.T(tx, row)) < 0) ok++;
                }
            return n == 0 ? 0 : ok / (float)n;
        }

        static void BuildArena(ArenaDef def, LevelData d, Transform world, EnemyController boss)
        {
            var size = new Vector2(9.5f, 5.8f);
            // the boss's mark may sit by a shore or a cliff: slide the lair to the nearest spot that is all open ground
            Vector2 mark = boss.transform.position;
            Vector2 center = mark; float best = WalkableShare(d, mark, size);
            for (int dy = -4; dy <= 4 && best < 0.99f; dy++)
                for (int dx = -4; dx <= 4; dx++)
                {
                    var c = mark + new Vector2(dx, dy);
                    float s = WalkableShare(d, c, size) - (Mathf.Abs(dx) + Mathf.Abs(dy)) * 0.002f;
                    if (s > best) { best = s; center = c; }
                }
            // El Invocador's clearing belongs to GameBuilder.Camps (another feature): the lair is built around it as it is -
            // he is not moved and his pillars, torches and ritual circle stay; only the floor, rim dressing and rune wall are added
            var clearing = boss.transform.parent;
            bool ownCircle = clearing != null && clearing.name == "SummonerClearing";
            if (ownCircle) center = (Vector2)boss.transform.position - new Vector2(0, 0.3f);
            else boss.transform.position = center + new Vector2(0, 1.6f);            // the boss waits at the back of his circle

            // a boss living in a fort or a courtyard: shrink the lair until no building sprite reaches into it
            var buildings = world.Find("Buildings");
            if (buildings)
            {
                var boxes = buildings.GetComponentsInChildren<SpriteRenderer>(true)
                    .Where(r => r.GetComponentInParent<Collider2D>() != null && r.bounds.size.y > 1.5f).Select(r => r.bounds).ToArray();   // solid structures only
                bool Blocked(Vector2 sz) => boxes.Any(bb =>
                {
                    Vector2 q = (Vector2)bb.ClosestPoint(new Vector3(center.x, center.y, bb.center.z)) - center;
                    return q.x * q.x / (sz.x * sz.x) + q.y * q.y / (sz.y * sz.y) < 1f;
                });
                var solid = buildings.GetComponentsInChildren<SpriteRenderer>(true)
                    .Where(r => r.GetComponentInParent<Collider2D>() != null && r.bounds.size.y > 1.5f).ToArray();
                var blocker = solid.FirstOrDefault(r =>
                {
                    Vector2 q = (Vector2)r.bounds.ClosestPoint(new Vector3(center.x, center.y, r.bounds.center.z)) - center;
                    return q.x * q.x / (size.x * size.x) + q.y * q.y / (size.y * size.y) < 1f;
                });
                if (blocker != null) Debug.Log($"[GameBuilder] arena {def.prefab}: {blocker.name} ({blocker.transform.parent?.name}) at {blocker.bounds.center} size {blocker.bounds.size} reaches in");
                while (Blocked(size) && size.x > 5f) size *= 0.9f;
                if (!ownCircle) boss.transform.position = center + new Vector2(0, size.y * 0.27f);
            }

            // nothing grows, stands or roams inside the lair
            bool Inside(Vector2 p, float grow) { var q = p - center; float rx = size.x + grow, ry = size.y + grow; return q.x * q.x / (rx * rx) + q.y * q.y / (ry * ry) < 1f; }
            var nature = world.Find("Nature");
            if (nature)
                foreach (Transform tr in nature.Cast<Transform>().ToArray())
                    if (Inside(tr.position, 0.8f)) Object.DestroyImmediate(tr.gameObject);
            foreach (var e in world.GetComponentsInChildren<EnemyController>(true))
                if (e != boss && !e.isBoss && Inside(e.transform.position, 1f)) Object.DestroyImmediate(e.gameObject);

            var root = new GameObject("BossArena_" + def.prefab).transform;
            root.SetParent(world, false);
            root.position = center;
            var arena = root.gameObject.AddComponent<BossArena>();
            arena.boss = boss; arena.size = size; arena.theme = def.theme;
            arena.bossTitle = def.title; arena.subtitle = def.subtitle; arena.objective = def.objective;
            arena.tint = def.tint; arena.fogColor = def.fog; arena.glowColor = def.glow;
            var ga = AssetDatabase.LoadAssetAtPath<GameAssets>(GameRoot + "/Resources/GameAssets.asset");
            var add = ga ? ga.matAdditive : null;
            int t = def.theme;

            // floor + rune circle under the boss
            Deco(root, "ArenaFloor", One(ARENA + $"arena_floor_{t}.png"), center, default, 0, -45);
            var runes = Deco(root, ownCircle ? "RuneHalo" : "RuneCircle", One(ARENA + "arena_runes.png"), (Vector2)boss.transform.position + new Vector2(0, -0.3f), default, 0, -40);
            if (ownCircle) runes.transform.localScale = new Vector3(1.6f, 1.6f, 1);
            var rsr = runes.GetComponent<SpriteRenderer>(); rsr.color = new Color(def.glow.r, def.glow.g, def.glow.b, 0.5f); if (add) rsr.sharedMaterial = add;
            var rp = runes.AddComponent<ArenaProp>(); rp.mode = ArenaProp.Mode.Pulse; rp.amount = 0.45f;
            LightGlow.Attach(runes.transform, Vector2.zero, 3.4f, def.glow, 0.35f, true);

            // rune wall (enabled by BossArena when the fight starts)
            var seal = new GameObject("Seal"); seal.transform.SetParent(root, false);
            var edge = seal.AddComponent<EdgeCollider2D>();
            var pts = new Vector2[49];
            for (int i = 0; i <= 48; i++) { float a = i / 48f * Mathf.PI * 2f; pts[i] = new Vector2(Mathf.Cos(a) * size.x, Mathf.Sin(a) * size.y); }
            edge.points = pts; edge.edgeRadius = 0.1f;
            var glyph = One(ARENA + "arena_sealrune.png");
            for (int i = 0; i < 44; i++)
            {
                float a = i / 44f * Mathf.PI * 2f;
                var g = Deco(seal.transform, "SealRune", glyph, center + new Vector2(Mathf.Cos(a) * size.x, Mathf.Sin(a) * size.y + 0.4f), default, 0, 2);
                var gs = g.GetComponent<SpriteRenderer>(); gs.color = new Color(def.glow.r, def.glow.g, def.glow.b, 0.85f); if (add) gs.sharedMaterial = add;
                var gp = g.AddComponent<ArenaProp>(); gp.mode = ArenaProp.Mode.Pulse; gp.speed = 2.5f; gp.amount = 0.6f;
            }

            Vector2 OnRing(float deg, float k) => center + new Vector2(Mathf.Cos(deg * Mathf.Deg2Rad) * size.x * k, Mathf.Sin(deg * Mathf.Deg2Rad) * size.y * k);
            var pillars = Sheet(ARENA + "arena_pillars_20x56.png");
            var banners = Sheet(ARENA + "arena_banners_14x30.png");
            var braziers = Sheet(ARENA + "arena_braziers_18x22.png");
            var flames = Sheet(ARENA + "arena_flames_16x16.png");
            var debris = Sheet(ARENA + "arena_debris_16x16.png");
            var chain = One(ARENA + "arena_chain.png");
            var beam = One(ARENA + "arena_lightcolumn.png");
            var fog = One(ARENA + "arena_fog.png");

            // pillars around the rim (the south side stays open: that is where you come in)
            float[] pillarAngles = { 20, 55, 90, 125, 160, 200, 340 };
            for (int i = 0; i < pillarAngles.Length; i++)
            {
                bool broken = i % 3 == 2;
                var at = OnRing(pillarAngles[i], 1.06f);
                var holder = new GameObject("Pillar"); holder.transform.SetParent(root, false); holder.transform.position = at;
                var bc = holder.AddComponent<BoxCollider2D>(); bc.size = new Vector2(1.0f, 0.5f); bc.offset = new Vector2(0, 0.2f);
                var spr = pillars.Length > t + 5 ? pillars[broken ? t + 5 : t] : null;
                Deco(holder.transform, "pillar", spr, at + new Vector2(0, 1.75f));
                if (!broken && banners.Length > t)
                    Deco(holder.transform, "banner", banners[t], at + new Vector2(0, 1.7f), default, 0, 1);
                if (!broken && chain != null && i % 2 == 1)
                    Deco(holder.transform, "chain", chain, at + new Vector2(0.55f, 1.9f), default, 0, 1);
            }
            // braziers between the pillars
            float[] brazierAngles = { 0, 38, 72, 108, 142, 180, 230, 310 };
            foreach (var deg in brazierAngles)
            {
                var at = OnRing(deg, 0.86f);
                var b = new GameObject("Brazier"); b.transform.SetParent(root, false); b.transform.position = at;
                var bc = b.AddComponent<BoxCollider2D>(); bc.size = new Vector2(0.7f, 0.35f); bc.offset = new Vector2(0, 0.15f);
                Deco(b.transform, "bowl", braziers.Length > t ? braziers[t] : null, at + new Vector2(0, 0.69f));
                if (flames.Length >= (t + 1) * 4)
                {
                    var fr = flames.Skip(t * 4).Take(4).ToArray();
                    var f = Deco(b.transform, "flame", fr[0], at + new Vector2(0, 1.55f), default, 0, 1);
                    Loop(f, fr, 10);
                }
                LightGlow.Attach(b.transform, new Vector2(0, 1.5f), 1.9f, def.glow, 0.5f, true);
            }
            // beams of light, fog banks, rubble
            foreach (var deg in new float[] { 45, 135, 225, 315 })
            {
                var at = OnRing(deg, 0.62f);
                var c = Deco(root, "LightBeam", beam, at + new Vector2(0, 2.4f), default, 0, DayNightLighting.OverlayOrder + 1);
                var sr = c.GetComponent<SpriteRenderer>(); sr.color = new Color(def.glow.r, def.glow.g, def.glow.b, 0.2f); if (add) sr.sharedMaterial = add;
                var ap = c.AddComponent<ArenaProp>(); ap.mode = ArenaProp.Mode.Flicker; ap.amount = 0.4f;
                var foot = Deco(root, "BeamFoot", One(ARENA + "arena_runes.png"), at, default, 0, -39);
                foot.transform.localScale = new Vector3(0.22f, 0.22f, 1);
                var fs = foot.GetComponent<SpriteRenderer>(); fs.color = new Color(def.glow.r, def.glow.g, def.glow.b, 0.6f); if (add) fs.sharedMaterial = add;
            }
            var rng = new System.Random(def.theme * 97 + 13);
            for (int i = 0; i < 5; i++)
            {
                var at = OnRing(rng.Next(0, 360), (float)(0.2 + rng.NextDouble() * 0.6));
                var fgo = Deco(root, "Fog", fog, at, default, 0, -20);
                var fsr = fgo.GetComponent<SpriteRenderer>(); fsr.color = new Color(def.fog.r, def.fog.g, def.fog.b, Mathf.Min(1f, def.fog.a * 1.3f));
                fgo.transform.localScale = new Vector3(1.4f, 1.2f, 1);
                var ap = fgo.AddComponent<ArenaProp>(); ap.mode = ArenaProp.Mode.Drift; ap.drift = new Vector2(1.2f, 0.2f); ap.amount = 0.4f;
            }
            if (debris.Length >= (t + 1) * 8)
                for (int i = 0; i < 18; i++)
                {
                    var at = OnRing(rng.Next(0, 360), (float)(0.55 + rng.NextDouble() * 0.38));
                    Deco(root, "debris", debris[t * 8 + rng.Next(0, 8)], at, default, 0, -38);
                }
            Debug.Log($"[GameBuilder] arena for {def.prefab} at {center} size {size} (open ground {best:P0})");
        }
    }
}
