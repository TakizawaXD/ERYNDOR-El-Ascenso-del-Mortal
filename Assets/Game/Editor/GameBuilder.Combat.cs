// Combat animation system (2026-11-21): data assets and prefab wiring.
//   * Assets/Game/Data/Combat/Player/<Set>_<Move>.asset   AttackAnimationData of every move of every weapon set, timings read
//                                                          from the Animation Events of the built clips (speed 1)
//   * Resources/Combat/AttackLibrary.asset                 all of the above (WeaponAnimationController.Data)
//   * Resources/Combat/WeaponSets_<Class>.asset            override controller per melee set + bow SpecialAttack clips
//   * Assets/Game/Data/Combat/Enemies/<Char>_<Move>.asset  attack / heavy / special of every enemy look
//   * every actor prefab: AnimationEventHandler on the Animator, the right animation controller and a WeaponHitboxController
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace WoodsGame.EditorTools
{
    public static partial class GameBuilder
    {
        const string CombatData = GameRoot + "/Data/Combat";
        static readonly string[] PlayerMoves =
            { "Attack", "Attack2", "Attack3", "ComboAttack", "HeavyAttack", "ChargedAttack_Release", "CriticalAttack", "SpecialAttack" };
        static readonly string[] ClassSprites = { "Soldier", "KnightPaladin", "KnightRanger", "KnightDark", "KnightSamurai" };

#pragma warning disable 0649
        [System.Serializable] class SetMeta { public string character, @base, weapon, set_type; public float reach_px; public int body_px; }
#pragma warning restore 0649

        // hit width of each set (world units at scale 1); reach comes from the drawn weapon
        static readonly Dictionary<string, float> SetRadius = new Dictionary<string, float>
        {
            { "Sword", 0.7f }, { "Greatsword", 1.0f }, { "Katana", 0.75f }, { "Rapier", 0.45f }, { "Dagger", 0.5f }, { "Spear", 0.5f },
            { "Axe", 0.85f }, { "HeavyAxe", 1.1f }, { "Hammer", 1.1f }, { "Staff", 0.65f }, { "Legendary", 0.85f },
        };

        /// <summary>Called from BuildAssetsAndPrefabs before the actor prefabs.</summary>
        static void BuildCombatData(GameAssets a)
        {
            Ensure(CombatData + "/Player"); Ensure(CombatData + "/Enemies"); Ensure(GameRoot + "/Resources/Combat");
            // ---- attack library (timings are the same for every class: they are recolours)
            var lib = LoadOrCreate<AttackLibrary>(GameRoot + "/Resources/Combat/AttackLibrary.asset");
            lib.attacks.Clear();
            foreach (var set in WeaponTypes.MeleeSets.Concat(WeaponTypes.BowSets))
            {
                var meta = ReadSetMeta("Soldier", set);
                foreach (var move in PlayerMoves)
                {
                    var clip = AssetDatabase.LoadAssetAtPath<AnimationClip>($"{Anims}/WeaponSets/Soldier/{set}/Soldier_{set}_{move}_Right.anim");
                    if (clip == null) continue;
                    var d = LoadOrCreate<AttackAnimationData>($"{CombatData}/Player/{set}_{move}.asset");
                    FillFromClips(d, set, move, null, clip, null);
                    TuneForSet(d, set, move, meta);
                    EditorUtility.SetDirty(d);
                    lib.attacks.Add(d);
                }
            }
            EditorUtility.SetDirty(lib);
            // ---- per class: override controllers + bow clips
            foreach (var cls in ClassSprites)
            {
                var ws = LoadOrCreate<WeaponAnimationSet>($"{GameRoot}/Resources/Combat/WeaponSets_{cls}.asset");
                ws.character = cls;
                ws.melee.Clear(); ws.bows.Clear();
                foreach (var set in WeaponTypes.MeleeSets)
                {
                    var ov = AssetDatabase.LoadAssetAtPath<AnimatorOverrideController>($"{Anims}/WeaponSets/{cls}/{set}/{cls}_{set}.overrideController");
                    if (ov == null) { Debug.LogError($"[GameBuilder] missing weapon set {cls}/{set} (python Tools/CharAnim/weaponsets.py)"); continue; }
                    ws.melee.Add(new WeaponAnimationSet.Melee { set = set, controller = ov });
                }
                foreach (var set in WeaponTypes.BowSets)
                {
                    var b = new WeaponAnimationSet.Bow { set = set };
                    for (int i = 0; i < 4; i++)
                        b.clips[i] = AssetDatabase.LoadAssetAtPath<AnimationClip>($"{Anims}/WeaponSets/{cls}/{set}/{cls}_{set}_SpecialAttack_{WeaponAnimationSet.Dirs[i]}.anim");
                    if (b.clips.Any(c => c == null)) Debug.LogError($"[GameBuilder] bow set {cls}/{set} incomplete");
                    ws.bows.Add(b);
                }
                EditorUtility.SetDirty(ws);
            }
            // ---- effects + the staff's magic bolt
            string wfx = FX + "Weapons";
            var names = Directory.GetFiles(Path.Combine(ProjectRoot, wfx), "fx_*_anim_32x32.png")
                                 .Select(p => Path.GetFileNameWithoutExtension(p)).Select(n => n.Substring(3, n.Length - 3 - "_anim_32x32".Length)).OrderBy(n => n).ToArray();
            a.weaponFxNames = names;
            a.weaponFx = names.Select(n => new GameAssets.FrameSet { frames = Sheet($"{wfx}/fx_{n}_anim_32x32.png") }).ToArray();
            var bolt = Sheet(FX + "fx_magic_bolt_anim_16x16.png");
            if (bolt.Length > 0) a.magicBoltPrefab = ProjectilePrefab("MagicBolt", bolt, 0.16f, FxKind.Sparkle);
            EditorUtility.SetDirty(a);
            AssetDatabase.SaveAssets();
            Debug.Log($"[GameBuilder] combat data: {lib.attacks.Count} player moves, {ClassSprites.Length} classes, {names.Length} weapon effects");
        }

        static T LoadOrCreate<T>(string path) where T : ScriptableObject
        {
            var x = AssetDatabase.LoadAssetAtPath<T>(path);
            if (x != null) return x;
            x = ScriptableObject.CreateInstance<T>();
            Ensure(System.IO.Path.GetDirectoryName(path).Replace((char)92, '/'));   // enemy prefabs ask for their data before BuildCombatData runs
            AssetDatabase.CreateAsset(x, path);
            return x;
        }

        static SetMeta ReadSetMeta(string cls, string set)
        {
            string p = Path.Combine(ProjectRoot, $"{Chars}/WeaponSets/{cls}/{set}/{cls}_{set}_animations.json");
            return File.Exists(p) ? JsonUtility.FromJson<SetMeta>(File.ReadAllText(p)) : null;
        }

        /// <summary>Phase times (speed 1) from the Animation Events. prep/recov: the chained PrepareAttack and
        /// AttackRecovery clips of the enemies (their lengths shift the times of the strike clip).</summary>
        static void FillFromClips(AttackAnimationData d, string set, string move, AnimationClip prep, AnimationClip clip, AnimationClip recov)
        {
            d.set = set; d.move = move;
            d.trigger = move == "ChargedAttack_Release" ? "" : move;
            float off0 = prep ? prep.length : 0f;
            d.anticipation = d.hitOn = d.hitOff = d.comboWindow = d.projectile = -1f;
            void Read(AnimationClip c, float offset)
            {
                if (c == null) return;
                foreach (var e in AnimationUtility.GetAnimationEvents(c))
                {
                    float t = offset + e.time;
                    switch (e.stringParameter)
                    {
                        case "Telegraph": case "Anticipation": if (d.anticipation < 0) d.anticipation = t; break;
                        case "HitOn": if (d.hitOn < 0) d.hitOn = t; break;
                        case "HitOff": d.hitOff = t; break;
                        case "ComboWindow": if (d.comboWindow < 0) d.comboWindow = t; break;
                        case "Projectile": if (d.projectile < 0) d.projectile = t; break;
                    }
                }
            }
            Read(prep, 0f); Read(clip, off0); Read(recov, off0 + (clip ? clip.length : 0f));
            d.length = off0 + (clip ? clip.length : 0f) + (recov ? recov.length : 0f);
            d.end = d.length;
            if (d.anticipation < 0) d.anticipation = 0f;
            if (d.hitOn >= 0 && d.hitOff < d.hitOn) d.hitOff = Mathf.Min(d.end, d.hitOn + 0.1f);
            if (d.comboWindow < 0) d.comboWindow = d.hitOff >= 0 ? d.hitOff : d.end * 0.8f;
            // a clip without any event (should not happen): a sensible middle
            if (d.hitOn < 0 && d.projectile < 0 && move != "SpecialAttack" && move != "CastSpell") { d.hitOn = d.length * 0.45f; d.hitOff = d.length * 0.6f; }
            if ((move == "SpecialAttack" || move == "CastSpell") && d.projectile < 0 && d.hitOn < 0) d.projectile = d.length * 0.5f;
        }

        static void TuneForSet(AttackAnimationData d, string set, string move, SetMeta meta)
        {
            bool big = move == "HeavyAttack" || move == "ComboAttack" || move == "ChargedAttack_Release";
            float px = meta != null ? meta.reach_px : 12f;
            d.reach = (px + 4f) / 16f * (big ? 1.15f : 1f);
            d.radius = (SetRadius.TryGetValue(set, out var r) ? r : 0.7f) * (big ? 1.25f : 1f);
            d.shape = (set == "Spear" && move != "Attack2") || set == "Rapier" && move != "Attack3" || move == "CriticalAttack" ? HitShape.Thrust : HitShape.Arc;
            d.arc = set == "Dagger" ? 100f : set == "Katana" ? 130f : big ? 170f : 140f;
            bool spin = (move == "Attack3" && (set == "Greatsword" || set == "HeavyAxe" || set == "Hammer")) || (move == "ComboAttack" && set == "Dagger");
            if (spin) { d.shape = HitShape.Circle; d.radius = Mathf.Max(d.radius, d.reach * 0.9f); d.arc = 360f; }
            d.damageMul = move == "ComboAttack" ? 1.6f : big ? 1.5f : move == "Attack3" ? 1.2f : 1f;
            d.projectileKind = set == "Staff" && d.projectile >= 0 ? ProjectileKind.Magic : WeaponTypes.BowSets.Contains(set) ? ProjectileKind.Arrow : ProjectileKind.None;
            d.fx = WeaponTypes.TrailFx(set, move);
            d.sfxSwing = WeaponTypes.SwingSfx(set, big);
            d.sfxHit = WeaponTypes.HitSfx(set);
            d.shake = set == "Hammer" || set == "HeavyAxe" ? (big ? 0.22f : 0.12f) : big ? 0.12f : 0f;
        }

        /// <summary>Attack data of one enemy look, read from its clips (PrepareAttack -> Attack -> AttackRecovery chain).</summary>
        static void EnemyCombatData(EnemyAnimationController ea, string character)
        {
            string dir = $"{Anims}/{character}";
            AnimationClip C(string n) => AssetDatabase.LoadAssetAtPath<AnimationClip>($"{dir}/{character}_{n}_Right.anim");
            var meta = JsonUtility.FromJson<SetMeta>(File.Exists(Path.Combine(ProjectRoot, $"{Chars}/{character}/{character}_animations.json"))
                ? File.ReadAllText(Path.Combine(ProjectRoot, $"{Chars}/{character}/{character}_animations.json")) : "{}");
            float reach = meta != null && meta.reach_px > 0 ? meta.reach_px / 16f : 0f;
            float size = meta != null && meta.body_px > 26 ? 1.3f : 1f;
            AttackAnimationData Make(string move, AnimationClip prep, AnimationClip clip, AnimationClip recov, float radius)
            {
                if (clip == null) return null;
                var d = LoadOrCreate<AttackAnimationData>($"{CombatData}/Enemies/{character}_{move}.asset");
                FillFromClips(d, "Enemy", move, prep, clip, recov);
                d.trigger = move;
                d.reach = reach * (move == "HeavyAttack" ? 1.1f : 1f);
                d.radius = radius * size;
                d.shape = HitShape.Arc; d.arc = move == "HeavyAttack" ? 170f : 140f;
                d.projectileKind = move == "SpecialAttack" ? ProjectileKind.Enemy : ProjectileKind.None;
                d.shake = move == "HeavyAttack" && size > 1f ? 0.12f : 0f;
                d.fx = ""; d.sfxSwing = move == "HeavyAttack" ? "heavy_swing" : "swing"; d.sfxHit = "hit";
                EditorUtility.SetDirty(d);
                return d;
            }
            var prepC = C("PrepareAttack"); var recC = C("AttackRecovery");
            ea.attack = Make("Attack", prepC, C("Attack"), prepC != null ? recC : null, 0.7f);
            ea.heavy = Make("HeavyAttack", null, C("HeavyAttack"), null, 0.9f);
            ea.special = Make("SpecialAttack", null, C("SpecialAttack"), null, 0.7f);
        }

        /// <summary>Animation side of every actor prefab (called by ActorPrefab after configure).</summary>
        static void WireCombat(GameObject go, string character)
        {
            foreach (var an in go.GetComponentsInChildren<Animator>(true))
                if (an.GetComponent<AnimationEventHandler>() == null) an.gameObject.AddComponent<AnimationEventHandler>();
            if (go.GetComponent<Actor>() == null) return;
            if (go.GetComponent<WeaponHitboxController>() == null) go.AddComponent<WeaponHitboxController>();
            if (go.GetComponent<PlayerController>() != null)
            {
                if (go.GetComponent<WeaponAnimationController>() == null) go.AddComponent<WeaponAnimationController>();
            }
            else if (go.GetComponent<EnemyController>() != null)
            {
                var ea = go.GetComponent<EnemyAnimationController>() ?? go.AddComponent<EnemyAnimationController>();
                EnemyCombatData(ea, character);
            }
            else if (go.GetComponent<CharacterAnimationController>() == null) go.AddComponent<CharacterAnimationController>();
        }
    }
}
