// Tools > Art > Build Character Animations
// Reads Assets/Art/Characters/<Char>/<Char>_animations.json (written by Tools/CharAnim/build.py) and creates:
//   * one AnimationClip per animation & direction  -> Assets/Art/Animations/Characters/<Char>/
//   * one Animator Controller per character        -> Assets/Art/Animations/Characters/<Char>/<Char>.controller
// Clips use each sheet's unique frames plus the frame sequence (holds/repeats) stored in the manifest.
// Existing clips/controllers are updated in place, so GUID references in prefabs keep working.
// Combat (2026-11-21):
//   * manifest "events" -> Animation Events calling AnimEvent(string) (HitOn, HitOff, Projectile, Telegraph, ComboWindow,
//     End...) received by WoodsGame.AnimationEventHandler on the Animator's GameObject
//   * PrepareAttack + Attack + AttackRecovery clips -> the "Attack" trigger plays the three phases as a chain
//   * Attack2 / Attack3 states: combo chain Attack -> Attack2 -> Attack3 -> ComboAttack
//   * Assets/Art/Characters/WeaponSets/<Class>/<Kind>/ -> one AnimatorOverrideController per weapon type over the class
//     controller (Assets/Art/Animations/Characters/WeaponSets/<Class>/<Kind>/<Class>_<Kind>.overrideController); the class
//     controller gets placeholder clips for every state/direction a set overrides, so each override is complete.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;
using WoodsArt.Animation;

namespace WoodsArt.EditorTools
{
    public static class CharacterAnimationBuilder
    {
        const string CharRoot = "Assets/Art/Characters";
        const string AnimRoot = "Assets/Art/Animations/Characters";
        public const float RunThreshold = 0.6f;

#pragma warning disable 0649 // filled by JsonUtility
        [Serializable] class Ev { public int frame; public string fn, arg; }
        [Serializable] class Clip { public string name, dir, file; public int frames; public int[] seq; public float fps; public bool loop; public Ev[] events; }
        [Serializable] class Manifest { public string character, @base, weapon; public int cell; public float[] pivot; public int ppu; public Clip[] clips; }
        public const string SetsFolder = "WeaponSets";
        static readonly string[] Dirs = { "Down", "Up", "Left", "Right" };
#pragma warning restore 0649

        // ---------------------------------------------------------------- params
        static readonly string[] Floats = { "MoveX", "MoveY", "Speed" };
        static readonly string[] Bools =
        {
            "IsMoving", "IsDead", "IsGrounded", "IsBlocking", "IsCharging", "IsClimbing", "IsSwimming", "IsSitting",
            "IsSleeping", "IsPushing", "IsPulling", "IsChargingEnergy",
            // read-only flags maintained by AnimatorStateFlag behaviours:
            "IsAttacking", "IsHurt", "IsDodging"
        };
        static readonly string[] Triggers =
        {
            "Attack", "HeavyAttack", "SpecialAttack", "ComboAttack", "CriticalAttack", "Hurt", "Knockback", "BlockHit",
            "Dodge", "Roll", "Jump", "Victory", "Defeat", "Interact", "PickUp", "CastSpell", "Attack2", "Attack3"
        };
        // one-shot states fired by a trigger of the same name, with the read-only flag they raise
        static readonly (string state, string flag, bool guardAttacking)[] OneShots =
        {
            ("Attack", "IsAttacking", true), ("HeavyAttack", "IsAttacking", true), ("SpecialAttack", "IsAttacking", true),
            ("ComboAttack", "IsAttacking", true), ("CriticalAttack", "IsAttacking", true),
            ("Attack2", "IsAttacking", true), ("Attack3", "IsAttacking", true),
            ("Hurt", "IsHurt", false), ("Knockback", "IsHurt", false), ("Dodge", "IsDodging", false), ("Roll", "IsDodging", false),
            ("Interact", null, true), ("PickUp", null, true), ("CastSpell", "IsAttacking", true),
        };
        // looping / holding states driven by a bool
        static readonly (string state, string param)[] Holds =
        {
            ("Block", "IsBlocking"), ("Climb", "IsClimbing"), ("Swim", "IsSwimming"), ("Sit", "IsSitting"),
            ("Sleep", "IsSleeping"), ("Push", "IsPushing"), ("Pull", "IsPulling"), ("ChargeEnergy", "IsChargingEnergy"),
        };

        [MenuItem("Tools/Art/Build Character Animations")]
        public static void BuildAll()
        {
            int n = 0;
            var sets = WeaponSetManifests();
            // states every weapon set of a class overrides -> the class controller must have them in all directions
            var needs = new Dictionary<string, HashSet<string>>();
            foreach (var (_, sm) in sets)
            {
                if (!needs.TryGetValue(sm.@base, out var hs)) needs[sm.@base] = hs = new HashSet<string>();
                foreach (var c in sm.clips) hs.Add(c.name);
            }
            foreach (var dir in AssetDatabase.GetSubFolders(CharRoot))
            {
                string name = Path.GetFileName(dir);
                string man = $"{dir}/{name}_animations.json";
                if (!File.Exists(man)) continue;
                needs.TryGetValue(name, out var need);
                Build(JsonUtility.FromJson<Manifest>(File.ReadAllText(man)), $"{CharRoot}/{name}", need);
                n++;
            }
            int k = 0;
            foreach (var (dir, sm) in sets) { BuildWeaponSet(sm, dir); k++; }
            AssetDatabase.SaveAssets();
            Debug.Log($"[CharacterAnimationBuilder] Built {n} characters and {k} weapon sets.");
        }

        static List<(string dir, Manifest m)> WeaponSetManifests()
        {
            var list = new List<(string, Manifest)>();
            string root = $"{CharRoot}/{SetsFolder}";
            if (!AssetDatabase.IsValidFolder(root)) return list;
            foreach (var cls in AssetDatabase.GetSubFolders(root))
                foreach (var kind in AssetDatabase.GetSubFolders(cls))
                {
                    string man = $"{kind}/{Path.GetFileName(cls)}_{Path.GetFileName(kind)}_animations.json";
                    if (File.Exists(man)) list.Add((kind, JsonUtility.FromJson<Manifest>(File.ReadAllText(man))));
                }
            return list;
        }

        static void Build(Manifest m, string srcDir, HashSet<string> need)
        {
            string outDir = $"{AnimRoot}/{m.character}";
            var clips = BuildClips(m, srcDir, outDir);
            if (need != null) AddPlaceholders(m.character, outDir, clips, need);
            BuildController(m.character, outDir, clips);
        }

        /// <summary>An override replaces clips, not states: a class controller that weapon sets override needs its own clip
        /// for every overridden state in all four directions. Missing ones are copies of a sibling clip.</summary>
        static void AddPlaceholders(string character, string outDir, Dictionary<string, Dictionary<string, AnimationClip>> clips, HashSet<string> need)
        {
            foreach (var name in need)
            {
                if (!clips.TryGetValue(name, out var byDir))
                {
                    string from = name == "Attack2" || name == "Attack3" ? "Attack" : null;
                    if (from == null || !clips.TryGetValue(from, out var src)) continue;
                    clips[name] = byDir = new Dictionary<string, AnimationClip>();
                    foreach (var kv in src) byDir[kv.Key] = Placeholder(kv.Value, $"{character}_{name}_{kv.Key}", outDir);
                }
                foreach (var d in Dirs)
                {
                    if (byDir.ContainsKey(d)) continue;
                    AnimationClip src = byDir.TryGetValue(d == "Left" ? "Left" : "Right", out var a) ? a
                                      : byDir.TryGetValue("Right", out var r) ? r : byDir.Values.First();
                    byDir[d] = Placeholder(src, $"{character}_{name}_{d}", outDir);
                }
            }
        }

        static AnimationClip Placeholder(AnimationClip src, string name, string outDir)
        {
            var c = UnityEngine.Object.Instantiate(src);
            c.name = name;
            return Save(c, $"{outDir}/{name}.anim");
        }

        /// <summary>One weapon set: its clips plus an AnimatorOverrideController over the class controller.</summary>
        static void BuildWeaponSet(Manifest m, string srcDir)
        {
            string cls = m.@base, kind = m.weapon;
            string outDir = $"{AnimRoot}/{SetsFolder}/{cls}/{kind}";
            var clips = BuildClips(m, srcDir, outDir);
            var baseCtrl = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>($"{AnimRoot}/{cls}/{cls}.controller");
            if (baseCtrl == null) { Debug.LogError($"[CharacterAnimationBuilder] weapon set {cls}/{kind}: no base controller"); return; }
            string path = $"{outDir}/{cls}_{kind}.overrideController";
            var ov = AssetDatabase.LoadAssetAtPath<AnimatorOverrideController>(path);
            if (ov == null) { ov = new AnimatorOverrideController(baseCtrl); AssetDatabase.CreateAsset(ov, path); }
            else ov.runtimeAnimatorController = baseCtrl;
            var pairs = new List<KeyValuePair<AnimationClip, AnimationClip>>(ov.overridesCount);
            ov.GetOverrides(pairs);
            int hit = 0;
            string prefix = cls + "_";
            for (int i = 0; i < pairs.Count; i++)
            {
                var orig = pairs[i].Key;
                AnimationClip repl = null;
                if (orig != null && orig.name.StartsWith(prefix))
                {
                    string rest = orig.name.Substring(prefix.Length);
                    int u = rest.LastIndexOf('_');
                    if (u > 0 && clips.TryGetValue(rest.Substring(0, u), out var byDir) && byDir.TryGetValue(rest.Substring(u + 1), out var c)) { repl = c; hit++; }
                }
                pairs[i] = new KeyValuePair<AnimationClip, AnimationClip>(orig, repl);
            }
            ov.ApplyOverrides(pairs);
            EditorUtility.SetDirty(ov);
            if (hit == 0) Debug.LogWarning($"[CharacterAnimationBuilder] weapon set {cls}/{kind} overrides nothing");
        }

        static Dictionary<string, Dictionary<string, AnimationClip>> BuildClips(Manifest m, string srcDir, string outDir)
        {
            EnsureFolder(outDir);
            var clips = new Dictionary<string, Dictionary<string, AnimationClip>>();
            foreach (var c in m.clips)
            {
                string tex = $"{srcDir}/{c.file}";
                var sprites = ArtAssetBuilder.SlicedSprites(tex);
                if (sprites.Length < c.frames)
                {
                    Debug.LogError($"[CharacterAnimationBuilder] {tex}: expected {c.frames} sprites, found {sprites.Length}. Run Tools > Art > Reapply Import Rules.");
                    continue;
                }
                var clip = MakeClip(sprites, c);
                clip.name = $"{m.character}_{c.name}_{c.dir}";
                clip = Save(clip, $"{outDir}/{clip.name}.anim");
                if (!clips.TryGetValue(c.name, out var byDir)) clips[c.name] = byDir = new Dictionary<string, AnimationClip>();
                byDir[c.dir] = clip;
            }
            return clips;
        }

        static AnimationClip MakeClip(Sprite[] sprites, Clip c)
        {
            var clip = new AnimationClip { frameRate = c.fps };
            var binding = EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite");
            var seq = c.seq != null && c.seq.Length > 0 ? c.seq : Enumerable.Range(0, c.frames).ToArray();
            var keys = new List<ObjectReferenceKeyframe>();
            for (int i = 0; i < seq.Length; i++)
                keys.Add(new ObjectReferenceKeyframe { time = i / c.fps, value = sprites[seq[i]] });
            // closing key: loops wrap to frame 0, one-shots give the last frame its full duration and hold it
            keys.Add(new ObjectReferenceKeyframe { time = seq.Length / c.fps, value = sprites[c.loop ? seq[0] : seq[seq.Length - 1]] });
            AnimationUtility.SetObjectReferenceCurve(clip, binding, keys.ToArray());
            if (c.events != null && c.events.Length > 0)
            {
                // frame = index in the played sequence; the event fires when that frame appears
                var evs = c.events.Select(e => new AnimationEvent
                {
                    time = Mathf.Min(e.frame, seq.Length - 1) / c.fps,
                    functionName = string.IsNullOrEmpty(e.fn) ? "AnimEvent" : e.fn,
                    stringParameter = e.arg,
                    messageOptions = SendMessageOptions.DontRequireReceiver,
                }).OrderBy(e => e.time).ToArray();
                AnimationUtility.SetAnimationEvents(clip, evs);
            }
            var s = AnimationUtility.GetAnimationClipSettings(clip);
            s.loopTime = c.loop;
            AnimationUtility.SetAnimationClipSettings(clip, s);
            return clip;
        }

        // -------------------------------------------------------------- controller
        static void BuildController(string character, string outDir, Dictionary<string, Dictionary<string, AnimationClip>> clips)
        {
            string path = $"{outDir}/{character}.controller";
            if (AssetDatabase.LoadAssetAtPath<AnimatorController>(path) != null) AssetDatabase.DeleteAsset(path);
            var ctrl = AnimatorController.CreateAnimatorControllerAtPath(path);
            foreach (var f in Floats) ctrl.AddParameter(f, AnimatorControllerParameterType.Float);
            foreach (var b in Bools) ctrl.AddParameter(b, AnimatorControllerParameterType.Bool);
            foreach (var t in Triggers) ctrl.AddParameter(t, AnimatorControllerParameterType.Trigger);
            var ps = ctrl.parameters;
            foreach (var p in ps)
            {
                if (p.name == "IsGrounded") p.defaultBool = true;
                if (p.name == "MoveY") p.defaultFloat = -1f;   // face the camera by default
            }
            ctrl.parameters = ps;

            var sm = ctrl.layers[0].stateMachine;
            var states = new Dictionary<string, AnimatorState>();
            AnimatorState Make(string name, Vector2 pos)
            {
                if (!clips.TryGetValue(name, out var byDir)) return null;
                var st = sm.AddState(name, pos);
                st.motion = MotionFor(ctrl, name, byDir);
                st.writeDefaultValues = false;
                states[name] = st;
                return st;
            }

            // locomotion
            var idle = Make("Idle", new Vector2(300, 0));
            var walk = Make("Walk", new Vector2(300, 100));
            var run = Make("Run", new Vector2(300, 200));
            sm.defaultState = idle;
            Link(idle, walk, ("IsMoving", true));
            Link(walk, idle, ("IsMoving", false));
            if (run != null)
            {
                Link(walk, run, ("Speed", RunThreshold, true));
                Link(run, walk, ("Speed", RunThreshold, false), ("IsMoving", true));
                Link(run, idle, ("IsMoving", false));
                Link(idle, run, ("IsMoving", true), ("Speed", RunThreshold, true));
            }

            // one-shots from Any State, back to Idle when finished
            int y = 0;
            // three-phase attack (anticipation -> strike -> recovery) when the character has the phase clips
            AnimatorState prep = null, recov = null;
            if (clips.ContainsKey("PrepareAttack") && clips.ContainsKey("AttackRecovery") && clips.ContainsKey("Attack"))
            {
                prep = Make("PrepareAttack", new Vector2(500, -200));
                recov = Make("AttackRecovery", new Vector2(800, -200));
                prep.AddStateMachineBehaviour<AnimatorStateFlag>().parameter = "IsAttacking";
                recov.AddStateMachineBehaviour<AnimatorStateFlag>().parameter = "IsAttacking";
                var tp = FromAny(sm, prep);
                tp.AddCondition(AnimatorConditionMode.If, 0, "Attack");
                tp.AddCondition(AnimatorConditionMode.IfNot, 0, "IsDead");
                tp.AddCondition(AnimatorConditionMode.IfNot, 0, "IsAttacking");
                Finish(recov, idle);
            }
            foreach (var (name, flag, guard) in OneShots)
            {
                var st = Make(name, new Vector2(650, y)); y += 60;
                if (st == null) continue;
                if (name == "Attack" && prep != null)
                {
                    st.AddStateMachineBehaviour<AnimatorStateFlag>().parameter = flag;
                    Finish(prep, st);
                    Finish(st, recov);
                    continue;
                }
                var t = FromAny(sm, st);
                t.AddCondition(AnimatorConditionMode.If, 0, name);
                t.AddCondition(AnimatorConditionMode.IfNot, 0, "IsDead");
                if (guard) t.AddCondition(AnimatorConditionMode.IfNot, 0, "IsAttacking");   // attacks never restart themselves
                if (name == "Hurt" || name == "Knockback") t.AddCondition(AnimatorConditionMode.IfNot, 0, "IsDodging"); // i-frames
                if (flag != null) st.AddStateMachineBehaviour<AnimatorStateFlag>().parameter = flag;
                Finish(st, idle);
            }
            // combo can chain out of a running basic attack (second half of the swing)
            if (states.TryGetValue("Attack", out var atk) && states.TryGetValue("ComboAttack", out var combo))
            {
                var t = atk.AddTransition(combo);
                t.hasExitTime = true; t.exitTime = 0.5f; t.duration = 0; t.hasFixedDuration = true;
                t.AddCondition(AnimatorConditionMode.If, 0, "ComboAttack");
            }
            // combo chain: each step can be triggered from the running previous step (the code waits for its ComboWindow)
            foreach (var (from, to) in new[] { ("Attack", "Attack2"), ("Attack2", "Attack3"), ("Attack3", "ComboAttack") })
            {
                if (!states.TryGetValue(from, out var a) || !states.TryGetValue(to, out var b)) continue;
                var tc = a.AddTransition(b);
                tc.hasExitTime = false; tc.duration = 0; tc.hasFixedDuration = true;
                tc.AddCondition(AnimatorConditionMode.If, 0, to);
            }
            // block: hold while IsBlocking, BlockHit plays on impact and returns to the guard
            var block = Make("Block", new Vector2(950, 0));
            var blockHit = Make("BlockHit", new Vector2(950, 60));
            if (block != null)
            {
                var t = FromAny(sm, block);
                t.AddCondition(AnimatorConditionMode.If, 0, "IsBlocking");
                t.AddCondition(AnimatorConditionMode.IfNot, 0, "IsDead");
                t.AddCondition(AnimatorConditionMode.IfNot, 0, "IsAttacking");
                Link(block, idle, ("IsBlocking", false));
                if (blockHit != null)
                {
                    var h = block.AddTransition(blockHit); h.hasExitTime = false; h.duration = 0;
                    h.AddCondition(AnimatorConditionMode.If, 0, "BlockHit");
                    Finish(blockHit, block);
                }
            }
            // other bool-driven holds
            y = 120;
            foreach (var (name, param) in Holds)
            {
                if (name == "Block") continue;
                var st = Make(name, new Vector2(950, y)); y += 60;
                if (st == null) continue;
                var t = FromAny(sm, st);
                t.AddCondition(AnimatorConditionMode.If, 0, param);
                t.AddCondition(AnimatorConditionMode.IfNot, 0, "IsDead");
                Link(st, idle, (param, false));
            }
            // charged attack: charge while IsCharging, release when it is cleared
            var charge = Make("ChargedAttack_Charge", new Vector2(650, -120));
            var release = Make("ChargedAttack_Release", new Vector2(650, -60));
            if (charge != null && release != null)
            {
                var t = FromAny(sm, charge);
                t.AddCondition(AnimatorConditionMode.If, 0, "IsCharging");
                t.AddCondition(AnimatorConditionMode.IfNot, 0, "IsDead");
                t.AddCondition(AnimatorConditionMode.IfNot, 0, "IsAttacking");
                Link(charge, release, ("IsCharging", false));
                release.AddStateMachineBehaviour<AnimatorStateFlag>().parameter = "IsAttacking";
                Finish(release, idle);
            }
            // jump -> fall -> land
            var jump = Make("Jump", new Vector2(0, 300));
            var fall = Make("Fall", new Vector2(0, 360));
            var land = Make("Land", new Vector2(0, 420));
            if (jump != null)
            {
                var t = FromAny(sm, jump);
                t.AddCondition(AnimatorConditionMode.If, 0, "Jump");
                t.AddCondition(AnimatorConditionMode.IfNot, 0, "IsDead");
                Finish(jump, fall ?? idle);
                if (fall != null) Link(fall, land ?? idle, ("IsGrounded", true));
                if (land != null) Finish(land, idle);
            }
            // victory / defeat hold their last frame until the character moves again
            foreach (var name in new[] { "Victory", "Defeat" })
            {
                var st = Make(name, new Vector2(0, name == "Victory" ? 500 : 560));
                if (st == null) continue;
                var t = FromAny(sm, st);
                t.AddCondition(AnimatorConditionMode.If, 0, name);
                t.AddCondition(AnimatorConditionMode.IfNot, 0, "IsDead");
                Link(st, idle, ("IsMoving", true));
            }
            // death
            var death = Make("Death", new Vector2(0, 650));
            if (death != null)
            {
                var t = FromAny(sm, death);
                t.AddCondition(AnimatorConditionMode.If, 0, "IsDead");
                Link(death, idle, ("IsDead", false));
            }
            EditorUtility.SetDirty(ctrl);
        }

        static Motion MotionFor(AnimatorController ctrl, string name, Dictionary<string, AnimationClip> byDir)
        {
            if (byDir.Count == 1) return byDir.Values.First();
            var tree = new BlendTree { name = name, hideFlags = HideFlags.HideInHierarchy, useAutomaticThresholds = false };
            AssetDatabase.AddObjectToAsset(tree, ctrl);
            if (byDir.ContainsKey("Down") || byDir.ContainsKey("Up"))
            {
                tree.blendType = BlendTreeType.SimpleDirectional2D;
                tree.blendParameter = "MoveX"; tree.blendParameterY = "MoveY";
                var pos = new Dictionary<string, Vector2> { { "Down", Vector2.down }, { "Up", Vector2.up }, { "Left", Vector2.left }, { "Right", Vector2.right } };
                foreach (var kv in byDir) tree.AddChild(kv.Value, pos[kv.Key]);
            }
            else
            {
                // side-only animation: MoveX < 0 -> Left, otherwise (incl. facing up/down) -> Right
                tree.blendType = BlendTreeType.Simple1D;
                tree.blendParameter = "MoveX";
                if (byDir.TryGetValue("Left", out var l)) tree.AddChild(l, -1f);
                if (byDir.TryGetValue("Right", out var r)) tree.AddChild(r, -0.0001f);
            }
            return tree;
        }

        static AnimatorStateTransition FromAny(AnimatorStateMachine sm, AnimatorState st)
        {
            var t = sm.AddAnyStateTransition(st);
            t.canTransitionToSelf = false;
            t.hasExitTime = false;
            t.duration = 0;
            t.hasFixedDuration = true;
            return t;
        }

        static void Finish(AnimatorState from, AnimatorState to)
        {
            if (from == null || to == null) return;
            var t = from.AddTransition(to);
            t.hasExitTime = true; t.exitTime = 1f; t.duration = 0; t.hasFixedDuration = true;
        }

        static void Link(AnimatorState from, AnimatorState to, params object[] conds)
        {
            if (from == null || to == null) return;
            var t = from.AddTransition(to);
            t.hasExitTime = false; t.duration = 0; t.hasFixedDuration = true;
            foreach (var c in conds)
            {
                switch (c)
                {
                    case ValueTuple<string, bool> b:
                        t.AddCondition(b.Item2 ? AnimatorConditionMode.If : AnimatorConditionMode.IfNot, 0, b.Item1); break;
                    case ValueTuple<string, float, bool> f:
                        t.AddCondition(f.Item3 ? AnimatorConditionMode.Greater : AnimatorConditionMode.Less, f.Item2, f.Item1); break;
                }
            }
        }

        static AnimationClip Save(AnimationClip clip, string path)
        {
            var existing = AssetDatabase.LoadAssetAtPath<AnimationClip>(path);
            if (existing == null) { AssetDatabase.CreateAsset(clip, path); return clip; }
            EditorUtility.CopySerialized(clip, existing);
            EditorUtility.SetDirty(existing);
            return existing;
        }

        static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;
            var parent = Path.GetDirectoryName(path).Replace('\\', '/');
            EnsureFolder(parent);
            AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
        }
    }
}
