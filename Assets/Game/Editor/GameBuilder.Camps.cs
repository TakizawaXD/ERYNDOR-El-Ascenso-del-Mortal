// RPG content of the maps (2026-11-20): campsites (replace the bonfires 'F'), gathering spots, the living townsfolk
// (NpcDB + Villager routines) and El Invocador's clearing in the Bosque Corrupto. Art: Tools/ArtGen2/camp.py,
// townsfolk palettes: Tools/CharAnim/variants.py (Npc*, Invocador).
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace WoodsGame.EditorTools
{
    public static partial class GameBuilder
    {
        const string PROPS2 = "Props/";
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

        // ================================================================ clearings: nature never grows inside a camp or the arena
        static readonly Dictionary<LevelData, HashSet<Vector2Int>> _clearings = new Dictionary<LevelData, HashSet<Vector2Int>>();
        const string ClearableNature = "TUtAVuiIkYgGqyzMeZnrRW/*;obd";
        static readonly Vector2Int SummonerTile = new Vector2Int(28, 34);   // World2.txt: south of the dark tower, Bosque Corrupto

        static bool IsClearing(LevelData d, int x, int row, char c)
        {
            if (ClearableNature.IndexOf(c) < 0) return false;
            if (!_clearings.TryGetValue(d, out var set))
            {
                set = new HashSet<Vector2Int>();
                for (int r = 0; r < d.h; r++)
                    for (int cx = 0; cx < d.w; cx++)
                        if (d.E(cx, r) == 'F')
                            for (int dy = -2; dy <= 2; dy++)
                                for (int dx = -4; dx <= 4; dx++) set.Add(new Vector2Int(cx + dx, r + dy));
                if (d.w == 240 && d.h == 160)                               // the overworld: the Summoner's clearing
                    for (int dy = -7; dy <= 6; dy++)
                        for (int dx = -8; dx <= 8; dx++)
                            if (dx * dx / 64f + dy * dy / 49f <= 1.05f) set.Add(SummonerTile + new Vector2Int(dx, dy));
                _clearings[d] = set;
            }
            return set.Contains(new Vector2Int(x, row));
        }

        // ================================================================ campsites
        /// <summary>A camp around the 'F' tile: fire pit, tent, bedroll, workbench, storage chest, log bench and drying rack.</summary>
        static void BuildCamp(Transform parent, Vector3 foot) => BuildBonfire(parent, foot);   // ERYNDOR: bonfires replace the camps

        static void BuildCampLegacy(Transform parent, Vector3 foot)
        {
            var root = new GameObject("Camp").transform; root.SetParent(parent, false); root.position = foot;
            var fire = WSheet(PROPS2 + "camp_firepit_anim_24x24.png");
            if (fire.Length == 0) fire = WSheet(PROPS2 + "campfire_anim_20x20.png");
            var fgo = Deco(root, "Campfire", fire[0], foot, new Vector2(1.1f, 0.5f), 0.25f);
            Loop(fgo, fire, 10);
            var camp = fgo.AddComponent<Campfire>(); camp.promptHeight = 1.3f;

            GameObject Part(string name, string file, Vector2 off, Vector2 col, float colY, CampPart.Role? role, float prompt, int order = 0)
            {
                var s = WOne(PROPS2 + file);
                if (s == null) { Debug.LogWarning("[GameBuilder] missing camp art " + file); return null; }
                var go = Deco(root, name, s, foot + (Vector3)off, col, colY, order);
                if (role.HasValue) { var cp = go.AddComponent<CampPart>(); cp.role = role.Value; cp.camp = camp; cp.promptHeight = prompt; }
                return go;
            }
            Part("Tent", "camp_tent.png", new Vector2(-2.7f, 0.6f), new Vector2(2.4f, 0.7f), 0.35f, CampPart.Role.Tent, 2.6f);
            Part("Bedroll", "camp_bedroll.png", new Vector2(1.8f, -0.5f), default, 0, CampPart.Role.Tent, 0.9f, -3);
            Part("Workbench", "camp_workbench.png", new Vector2(2.5f, 0.9f), new Vector2(2.0f, 0.5f), 0.3f, CampPart.Role.Workbench, 1.9f);
            Part("Stash", "camp_stash.png", new Vector2(0.1f, 1.7f), new Vector2(1.2f, 0.5f), 0.3f, CampPart.Role.Stash, 1.4f);
            Part("Log", "camp_log.png", new Vector2(-1.4f, -1.0f), default, 0, null, 0, -2);
            Part("Rack", "camp_rack.png", new Vector2(4.0f, -0.4f), new Vector2(1.4f, 0.35f), 0.2f, null, 0);
        }

        // ================================================================ gathering spots
        static readonly Dictionary<char, (string kind, int n)[]> GatherTable = new Dictionary<char, (string, int)[]>
        {
            { 'a', new[] { ("hierba", 16), ("raiz", 5), ("hierro", 4) } },
            { 'b', new[] { ("hierba", 10), ("seta_roja", 8), ("flor_luna", 6) } },
            { 'c', new[] { ("seta_azul", 9), ("flor_luna", 7), ("hierba", 6) } },
            { 'd', new[] { ("raiz", 9), ("seta_azul", 7), ("seta_roja", 3) } },
            { 'e', new[] { ("hierro", 8), ("plata", 7), ("cristal", 7) } },
            { 'f', new[] { ("hierro", 9), ("raiz", 2) } },
            { 'g', new[] { ("obsidiana", 7), ("hierro", 3) } },
            { 'h', new[] { ("seta_roja", 9), ("flor_luna", 5), ("hierba", 3) } },
            { 'i', new[] { ("plata", 3), ("hierba", 3) } },
            { 'j', new[] { ("hierba", 5), ("seta_azul", 3) } },
        };

        static void PlaceGatherNodes(string id, LevelData d, Transform world, string[] regionRows, Func<int, int, char, bool> skip)
        {
            var frames = WSheet(PROPS2 + "gather_anim_16x16.png");
            if (frames.Length < CraftDB.GatherKinds.Length * 2) { Debug.LogWarning("[GameBuilder] gather art missing"); return; }
            var root = new GameObject("Gathering").transform; root.SetParent(world);
            var rnd = new System.Random(id.GetHashCode() & 0x7fffffff);
            var taken = new HashSet<Vector2Int>();
            bool zone = id.StartsWith("Zone_");
            IEnumerable<(char region, (string kind, int n)[] table)> plan = zone
                ? new[] { ('*', new[] { ("obsidiana", 8), ("cristal", 2) }) }
                : GatherTable.Select(kv => (kv.Key, kv.Value));
            int placed = 0;
            foreach (var (region, table) in plan)
                foreach (var (kind, n) in table)
                {
                    int k = Array.IndexOf(CraftDB.GatherKinds, kind);
                    for (int i = 0, tries = 0; i < n && tries < 4000; tries++)
                    {
                        int x = rnd.Next(2, d.w - 2), row = rnd.Next(2, d.h - 2);
                        if (!zone && (regionRows == null || row >= regionRows.Length || x >= regionRows[row].Length || regionRows[row][x] != region)) continue;
                        if (!Walkable(d, x, row) || d.E(x, row) != ' ' || (skip != null && skip(x, row, 'o')) || IsClearing(d, x, row, 'T')) continue;
                        if (NearBuilding(d, x, row) || MapDB.Places.Any(pl => pl.kind == "town" && pl.Contains(x, row))) continue;   // never against a wall or inside a town
                        var cell = new Vector2Int(x, row);
                        if (taken.Contains(cell) || taken.Any(t => (t - cell).sqrMagnitude < 9)) continue;
                        taken.Add(cell);
                        var foot = new Vector3(x + 0.5f, d.h - 1 - row, 0);
                        var go = Deco(root, "gather_" + kind, frames[k * 2], foot, default, 0, 0);
                        var g = go.AddComponent<Gatherable>();
                        g.kind = k; g.ready = frames[k * 2]; g.picked = frames[k * 2 + 1]; g.promptHeight = 1.0f;
                        g.amount = k >= 5 ? 1 : 1;
                        i++; placed++;
                    }
                }
            Debug.Log($"[GameBuilder] {id}: {placed} gathering spots");
        }

        /// <summary>A castle wall, tower, house or other big building within two cells (gathering spots and props stay clear).</summary>
        static bool NearBuilding(LevelData d, int x, int row)
        {
            for (int dy = -2; dy <= 3; dy++)
                for (int dx = -2; dx <= 2; dx++)
                    if ("#90678Jjx@$5".IndexOf(d.E(x + dx, row + dy)) >= 0) return true;
            return false;
        }

        static bool Walkable(LevelData d, int x, int row)
        {
            if (x < 0 || row < 0 || x >= d.w || row >= d.h) return false;
            if ("wOcCLsk~".IndexOf(d.T(x, row)) >= 0) return false;
            char e = d.E(x, row);
            return e == ' ' || "yzMel;".IndexOf(e) >= 0;
        }

        // ================================================================ townsfolk with routines (NpcDB)
        static void PlaceVillagers(string id, string[] lines, LevelData d, Transform world, RectInt? area = null)
        {
            var defs = NpcDB.All.Where(n => n.town == id).ToArray();
            if (defs.Length == 0) return;
            var root = new GameObject("Villagers_" + id).transform; root.SetParent(world);
            bool In(int cx, int crow) => !area.HasValue || (cx >= area.Value.xMin && cx <= area.Value.xMax && crow >= area.Value.yMin && crow <= area.Value.yMax);
            // landmarks in reading order (row-major), like the map file
            var anchors = new Dictionary<string, List<Vector2>>();
            void Add(string k, Vector2 v) { if (!anchors.TryGetValue(k, out var l)) anchors[k] = l = new List<Vector2>(); l.Add(v); }
            for (int row = 0; row < d.h; row++)
                for (int x = 0; x < d.w; x++)
                {
                    char c = d.E(x, row);
                    if (!In(x, row)) continue;
                    var at = new Vector2(x + 0.5f, d.h - 1 - row);
                    switch (c) { case 'F': Add("fire", at); break; case '@': Add("well", at); break; case '$': Add("shop", at); break;
                                 case 'S': Add("sign", at); break; case 'J': Add("mill", at); break; case 'P': Add("start", at); break; }
                }
            var rooms = world.GetComponentsInChildren<Interior>(true)
                .Where(r => In(Mathf.FloorToInt(r.outside.x), d.h - 1 - Mathf.FloorToInt(r.outside.y)))
                .OrderByDescending(r => r.outside.y).ThenBy(r => r.outside.x).ToList();
            Interior Room(string spec)
            {
                var p = spec.Split('#'); int n = p.Length > 1 ? int.Parse(p[1]) : 1;
                return rooms.Where(r => r.template == p[0]).Skip(n - 1).FirstOrDefault();
            }
            Vector2 Dir(string s) => s == "^" ? Vector2.up : s == "v" ? Vector2.down : s == "<" ? Vector2.left : s == ">" ? Vector2.right : Vector2.zero;
            bool Resolve(string spot, out Vector2 at, out Vector2 face)
            {
                at = Vector2.zero; face = Vector2.zero;
                var p = spot.Split(':');
                try
                {
                    if (p[0] == "i")
                    {
                        var room = Room(p[1]);
                        if (room == null) { Debug.LogWarning($"[GameBuilder] {id}: no house '{p[1]}' for {spot}"); return false; }
                        var xy = p[2].Split(',');
                        float lx = float.Parse(xy[0], Inv), ly = float.Parse(xy[1], Inv);
                        at = new Vector2(room.bounds.xMin + lx, room.bounds.yMax - 1 - ly + 0.3f);
                        if (p.Length > 3) face = Dir(p[3]);
                        return true;
                    }
                    Vector2 baseAt;
                    string[] off;
                    if (p[0] == "m") { var xy = p[1].Split(','); baseAt = new Vector2(int.Parse(xy[0]) + 0.5f, d.h - 1 - int.Parse(xy[1]) + 0.3f); off = new[] { "0", "0" }; if (p.Length > 2) face = Dir(p[2]); }
                    else
                    {
                        string key = p[1]; int dirIdx = 3;
                        if (key == "house") { var room = Room(p[2]); if (room == null) { Debug.LogWarning($"[GameBuilder] {id}: no house '{p[2]}'"); return false; } baseAt = room.outside; off = p[3].Split(','); dirIdx = 4; }
                        else
                        {
                            var kp = key.Split('#'); int n = kp.Length > 1 ? int.Parse(kp[1]) : 1;
                            if (!anchors.TryGetValue(kp[0], out var l) || l.Count < n) { Debug.LogWarning($"[GameBuilder] {id}: no landmark '{key}' for {spot}"); return false; }
                            baseAt = l[n - 1]; off = p[2].Split(',');
                        }
                        if (p.Length > dirIdx) face = Dir(p[dirIdx]);
                    }
                    var target = baseAt + new Vector2(float.Parse(off[0], Inv), -float.Parse(off[1], Inv));     // +dy = further south, like map rows
                    at = SnapWalkable(d, target);
                    return true;
                }
                catch (Exception e) { Debug.LogWarning($"[GameBuilder] bad NPC spot '{spot}': {e.Message}"); return false; }
            }

            foreach (var def in defs)
            {
                string cls = def.sprite;
                var ctrl = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>($"{Anims}/{cls}/{cls}.controller");
                if (ctrl == null) { Debug.LogError($"[GameBuilder] NPC {def.id}: no animator for {cls} (run variants.py)"); continue; }
                var work = new List<Vector2>(); var workF = new List<Vector2>(); var soc = new List<Vector2>(); var socF = new List<Vector2>();
                foreach (var s in def.work) if (Resolve(s, out var at, out var f)) { work.Add(at); workF.Add(f); }
                foreach (var s in def.social) if (Resolve(s, out var at, out var f)) { soc.Add(at); socF.Add(f); }
                if (!Resolve(def.sleep, out var sleep, out var sleepF)) sleep = work.Count > 0 ? work[0] : SnapWalkable(d, new Vector2(d.w / 2f, d.h / 2f));
                var start = work.Count > 0 ? work[0] : sleep;

                var go = new GameObject("NPC_" + def.id); go.transform.SetParent(root, false); go.transform.position = start;
                var spr = new GameObject("Sprite"); spr.transform.SetParent(go.transform, false);
                var sr = spr.AddComponent<SpriteRenderer>(); sr.sprite = Cell($"{Chars}/{cls}/Idle/{cls}_Idle_Down.png", 0);
                spr.AddComponent<Animator>().runtimeAnimatorController = ctrl;
                spr.AddComponent<AnimationEventHandler>();
                var sh = new GameObject("Shadow"); sh.transform.SetParent(go.transform, false);
                var ssr = sh.AddComponent<SpriteRenderer>(); ssr.sprite = One("Assets/Art/Game/shadow_blob.png"); ssr.sortingOrder = -1; sh.transform.localPosition = new Vector3(0, 0.05f, 0);
                var rb = go.AddComponent<Rigidbody2D>(); rb.gravityScale = 0; rb.freezeRotation = true; rb.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
                var col = go.AddComponent<CircleCollider2D>(); col.radius = 0.26f; col.offset = new Vector2(0, 0.2f);
                var v = go.AddComponent<Villager>();
                v.npcId = def.id; v.promptHeight = 1.5f;
                v.work = work.ToArray(); v.workFace = workF.ToArray(); v.social = soc.ToArray(); v.socialFace = socF.ToArray();
                v.sleepSpot = sleep; v.sleepFace = sleepF == Vector2.zero ? Vector2.down : sleepF;
                v.portrait = Sheet($"{Chars}/{cls}/Idle/{cls}_Idle_Down.png");
            }
            Debug.Log($"[GameBuilder] {id}: {defs.Length} townsfolk with routines");
        }

        static Vector2 SnapWalkable(LevelData d, Vector2 world)
        {
            int x0 = Mathf.FloorToInt(world.x), row0 = d.h - 1 - Mathf.FloorToInt(world.y);
            for (int r = 0; r < 8; r++)
                for (int dy = -r; dy <= r; dy++)
                    for (int dx = -r; dx <= r; dx++)
                    {
                        if (Mathf.Max(Mathf.Abs(dx), Mathf.Abs(dy)) != r) continue;
                        int x = x0 + dx, row = row0 + dy;
                        if (Walkable(d, x, row) && Walkable(d, x, row - 1)) return new Vector2(x + 0.5f, d.h - 1 - row + 0.3f);
                    }
            return world;
        }

        // ================================================================ El Invocador
        static GameObject SummonerPrefab()
        {
            // his own hand-built sheet (Tools/ArtGen2/summoner_art.py): twice the Soldier's height inside the same 64 px cells
            return ActorPrefab("Summoner", "Invocador", false, 1, go =>
            {
                var e = go.AddComponent<EnemyController>();
                e.kind = EnemyKind.Demon; e.typeId = "Summoner"; e.ai = AIProfile.Caster; e.displayName = "EL INVOCADOR";
                e.isBoss = true; e.bossFlag = "boss_I"; e.maxHP = 60; e.damage = 3; e.walkSpeed = 1.4f; e.chaseSpeed = 1.9f;
                e.aggroRange = 7.5f; e.attackRange = 1.1f; e.attackCooldown = 1.3f; e.heavyChance = 0.35f; e.xpReward = 50;
                e.ranged = true; e.rangedMin = 2.2f; e.rangedMax = 8f; e.rangedCooldown = 2.2f; e.rangedDamage = 2;
                e.coins = 0; e.potionChance = 0; e.arrowChance = 0;
                go.AddComponent<SummonerBoss>();
                var col = go.GetComponent<CircleCollider2D>(); col.radius = 0.55f; col.offset = new Vector2(0, 0.6f);
                go.GetComponent<EnemyController>().bodyHeight = 1.3f;
                LightGlow.Attach(go.transform, new Vector2(0, 0.6f), 2.6f, new Color(0.65f, 0.3f, 1f), 0.8f, true);
            });
        }

        static void PlaceSummoner(LevelData d, Transform world, Vector2Int? tile = null)
        {
            var root = new GameObject("SummonerClearing").transform; root.SetParent(world);
            var spot = tile ?? SummonerTile;
            var center = new Vector3(spot.x + 0.5f, d.h - 1 - spot.y, 0);
            var circle = WSheet("Effects/rune_circle_anim_96x56.png");
            if (circle.Length > 0)
            {
                var c = Deco(root, "RuneCircle", circle[0], center + new Vector3(0, 0.6f, 0), default, 0, -60);
                Loop(c, circle, 6);
                LightGlow.Attach(c.transform, Vector2.zero, 4.5f, new Color(0.6f, 0.25f, 1f), 0.6f, true);
            }
            var pillar = WOne("Structures/ruin_pillar.png");
            var torch = WSheet("Props/torch_anim_16x34.png");
            for (int k = 0; k < 6; k++)
            {
                float a = k / 6f * Mathf.PI * 2f + 0.3f;
                var at = center + new Vector3(Mathf.Cos(a) * 6.2f, Mathf.Sin(a) * 4.6f, 0);
                if (k % 2 == 0 && pillar != null) Deco(root, "ruin_pillar", pillar, at, new Vector2(0.8f, 0.5f), 0.25f);
                else if (torch.Length > 0)
                {
                    var t = Deco(root, "torch_anim_16x34", torch[0], at, new Vector2(0.35f, 0.25f), 0.15f);
                    Loop(t, torch, 9);
                    t.GetComponent<SpriteRenderer>().color = new Color(0.8f, 0.6f, 1f);
                }
            }
            var boss = Spawn("Summoner", root, center + new Vector3(0, 0.3f, 0));
            boss.name = "ElInvocador";
        }

        /// <summary>Called by BuildMapScene for every map after the houses and town NPCs.</summary>
        static void BuildRpgExtras(string id, LevelData d, Transform world, string[] lines, string[] regionRows, Func<int, int, char, bool> skip)
        {
            if (id == MapDB.World || id.StartsWith("Zone_")) PlaceGatherNodes(id, d, world, regionRows, skip);
            if (id == MapDB.World && !BossesIndoors) PlaceSummoner(d, world);     // ERYNDOR: El Invocador waits in his dungeon
            if (id.StartsWith("City_")) PlaceVillagers(id, lines, d, world);
        }
    }
}
