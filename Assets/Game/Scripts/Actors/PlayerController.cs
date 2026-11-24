using System.Collections;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>The knight (class chosen at the start). Souls-like combat on a stamina bar:
    ///  J sword (x2 combo) · K heavy · L bow · Space roll (moving) / backstep (standing) · Shift run
    ///  hold Ctrl/U block with the shield · F parry (precise window: stuns the enemy, then J = critical riposte)
    ///  Q use the quick item (bandage, medicine, bomb, oil, special arrows) · R next quick item · E interact.
    /// Damage, speed, defense, crits and healing come from the attributes, the forge level and the wear of the gear.</summary>
    public class PlayerController : Actor
    {
        public static PlayerController Current { get; private set; }
        /// <summary>Time of the last sword swing (the Fallen Knight reads it to dodge).</summary>
        public static float LastSwing = -10f;

        [Header("Movement feel")]
        public float acceleration = 30f;
        public float deceleration = 40f;

        [Header("Combat")]
        public float heavyCooldown = 1.0f;
        public float rollSpeed = 7.5f;
        public const float ParryWindow = 0.22f;

        [Header("Stamina costs")]
        public float rollCost = 18f, backstepCost = 12f, heavyMul = 1.8f, parryCost = 8f, bowCost = 8f, runCostPerSecond = 13f;

        bool _attacking, _comboQueued, _blocking, _exhausted;
        float _attackStarted, _nextHeavy, _nextRoll, _nextStep, _lastHurt = -99f, _nextRegen, _nextParry, _parryUntil, _staminaDelayUntil, _nextTiredMsg;
        float _tonicUntil, _stewUntil;
        Vector2 _rollVel;

        public float Stamina { get; private set; }
        public float MaxStamina => S.MaxStamina + (Time.time < _stewUntil ? 25f : 0f);
        public bool Blocking => _blocking;
        public bool ParryActive => Time.time <= _parryUntil;
        public bool Exhausted => _exhausted;

        PlayerState S => GameManager.State;
        static readonly int P_Block = Animator.StringToHash("IsBlocking");

        protected override void Awake()
        {
            base.Awake();
            Current = this;
            var ctrl = GameAssets.I ? GameAssets.I.ClassController(S.classId) : null;
            if (ctrl && anim) anim.runtimeAnimatorController = ctrl;
            health.team = Team.Player;
            health.filter = Defend;
            health.Avoided += OnAvoided;
            health.invulnerableAfterHit = 0.9f;
            S.Migrate();
            health.Init(S.maxHP, S.hp);
            health.Changed += () => S.hp = health.hp;
            Stamina = MaxStamina;
            Face(Vector2.down);
            // no WeaponHold overlay: the item icon beside the body looked like a floating weapon. Every class draws its weapon
            // in its own frames (weapon sets for the Caballero / Samurái, the drawing itself for the heroes).
            // one animation set per weapon type: the class controller is swapped for the set of the weapon in hand
            Weapons = AnimCtrl as WeaponAnimationController;
            if (Weapons && anim)
            {
                var kc = KnightClass.Get(S.classId);
                Weapons.SetClass(anim.runtimeAnimatorController, kc != null ? kc.sprite : "Soldier");
                RefreshWeaponSet();
            }
            // arriving through a map gate, or continue / respawn: appear at that gate or at the last camp of this map
            if (GameManager.ArrivalPoint(gameObject.scene.name, out var at, out var face))
            {
                transform.position = new Vector3(at.x, at.y, 0);
                if (rb) rb.position = transform.position;
                Face(face);
            }
        }

        void Start() { Summoning.Restore(this); }

        protected override CharacterAnimationController CreateAnimController() => gameObject.AddComponent<WeaponAnimationController>();

        /// <summary>Animation sets of the equipped weapon and bow (WeaponAnimationController).</summary>
        public WeaponAnimationController Weapons { get; private set; }
        /// <summary>Last attack move played (Attack, Attack2, Attack3, ComboAttack, HeavyAttack, ChargedAttack_Release...).</summary>
        public string LastMove { get; private set; } = "";
        public int ComboStep { get; private set; }
        public bool Attacking => _attacking;
        public bool Charging => _charging;

        /// <summary>Follows equipment changes (inventory, shops, tests): the set swaps on the next frame.</summary>
        public void RefreshWeaponSet()
        {
            if (Weapons == null || _attacking || _charging) return;
            Weapons.Equip(S.Weapon, S.Bow, facing);
        }

        void OnDestroy() { if (Current == this) Current = null; }

        void Update()
        {
            if (health.IsDead) return;
            if (GameManager.Paused || GameManager.InputBlocked)
            {
                moveVel = Vector2.zero; SetLocomotion(0); SetBlock(false);
                return;
            }
            Regenerate();
            RegenStamina();
            Vector2 input = GameInput.Move;
            RefreshWeaponSet();

            // input buffer: a press during a swing chains the next combo step at its ComboWindow event
            if (_attacking && GameInput.Attack && Time.time - _attackStarted > 0.08f) _comboQueued = true;

            // cancel: in the recovery of a swing (after HitOff) a roll / backstep interrupts the rest of the animation
            if (Locked && _attacking && AnimCtrl && AnimCtrl.Phase == AttackPhase.Recovery && GameInput.Roll && Time.time >= _nextRoll)
            {
                bool mv = input.sqrMagnitude > 0.01f;
                if (Spend(mv ? rollCost : backstepCost)) { lockUntil = 0; Run(mv ? Roll(input) : Backstep()); }
            }

            if (!Locked)
            {
                bool wantBlock = GameInput.Block && Stamina > 0 && !_attacking;
                SetBlock(wantBlock);
                if (GameInput.Attack) { if (!_attacking && !TryRiposte() && Spend(AttackCost)) Run(AttackChain()); }
                else if (GameInput.Heavy && Time.time >= _nextHeavy) { if (Spend(AttackCost * heavyMul)) Run(HeavyOrCharged()); }
                else if (GameInput.Parry && Time.time >= _nextParry) { if (Spend(parryCost)) Run(Parry()); }
                else if (GameInput.Special) TryBow();
                else if (GameInput.Roll && Time.time >= _nextRoll)
                {
                    bool moving = input.sqrMagnitude > 0.01f;
                    if (Spend(moving ? rollCost : backstepCost)) Run(moving ? Roll(input) : Backstep());
                }
                else if (GameInput.Interact) TryInteract();
                else if (GameInput.Potion) UseQuick();
                else if (GameInput.Cycle) CycleQuick();
                else if (GameInput.Summon) Summoning.OnKey(this);
            }
            else SetBlock(false);

            if (!Locked)
            {
                bool moving = input.sqrMagnitude > 0.01f;
                bool running = moving && GameInput.Run && !_blocking && !_exhausted && Stamina > 0;
                if (running) { Stamina = Mathf.Max(0, Stamina - runCostPerSecond * Time.deltaTime); _staminaDelayUntil = Time.time + 0.4f; if (Stamina <= 0) Tired(); }
                float speed = _blocking ? walkSpeed * 0.4f : running ? runSpeed : walkSpeed;
                Vector2 target = input * speed * S.SpeedMultiplier;
                // smooth acceleration / braking instead of instant velocity changes
                float rate = target.sqrMagnitude >= moveVel.sqrMagnitude ? acceleration : deceleration;
                moveVel = Vector2.MoveTowards(moveVel, target, rate * Time.deltaTime);
                if (moving && !_blocking) Face(input);
                else if (moving && _blocking && (facing - Combat.Snap4(input)).sqrMagnitude > 3.5f) { }   // keep the shield up while backing off
                SetLocomotion(moving ? (running ? 1f : 0.5f) : 0f);
                if (moving && Time.time > _nextStep) { Sfx.Step(transform.position, running ? 0.6f : 0.45f); _nextStep = Time.time + (running ? 0.22f : 0.32f); }
            }
            else
            {
                moveVel = _rollVel;
                SetLocomotion(0);
            }
        }

        // ------------------------------------------------------------ stamina
        /// <summary>Heavier weapons cost more stamina per swing.</summary>
        public float AttackCost => 9f + S.Weapon.Style.windup * 22f;

        /// <summary>Souls rule: any action is allowed while there is some stamina left; at zero you are out of breath.</summary>
        public bool Spend(float cost)
        {
            if (Stamina <= 0.5f) { Tired(); return false; }
            Stamina = Mathf.Max(0, Stamina - cost);
            _staminaDelayUntil = Time.time + 0.75f;
            if (Stamina <= 0) _exhausted = true;
            return true;
        }

        void Tired()
        {
            _exhausted = true;
            if (Time.time < _nextTiredMsg) return;
            _nextTiredMsg = Time.time + 1.2f;
            Sfx.Play("tired", 0.7f);
            UIRoot.Popup(Body + Vector2.up * 0.6f, "Sin aliento", new Color(0.6f, 0.9f, 0.5f));
        }

        void RegenStamina()
        {
            float max = MaxStamina;
            if (Stamina > max) Stamina = max;
            if (Time.time < _staminaDelayUntil || Stamina >= max) { if (Stamina >= max) _exhausted = false; return; }
            float rate = S.StaminaRegen * (_blocking ? 0.35f : 1f) * (Time.time < _tonicUntil ? 2f : 1f) * (_exhausted ? 0.8f : 1f);
            Stamina = Mathf.Min(max, Stamina + rate * Time.deltaTime);
            if (_exhausted && Stamina >= max * 0.3f) _exhausted = false;
        }

        public void RestoreStamina() { Stamina = MaxStamina; _exhausted = false; }

        void SetBlock(bool on)
        {
            if (_blocking == on) return;
            _blocking = on;
            if (anim) anim.SetBool(P_Block, on);
        }

        // ------------------------------------------------------------ actions
        // Every weapon set has its own animations (WeaponAnimationController). The damage happens only inside the
        // hit window of the animation: HitOn opens the weapon hitbox, HitOff closes it (Animation Events, with a
        // watchdog in CharacterAnimationController). WeaponStyle sets the pace: the Animator speed is scaled so the
        // blade lands at the weapon's wind-up time. Light combo: Attack -> Attack2 -> Attack3 -> ComboAttack.
        static readonly string[] Chain = { "Attack", "Attack2", "Attack3", "ComboAttack" };
        bool _charging;

        IEnumerator AttackChain()
        {
            var w = S.Weapon; var st = w.Style;
            _attacking = true; _comboQueued = false; _attackStarted = Time.time;
            for (int step = 0; step < Chain.Length; step++)
            {
                ComboStep = step;
                _comboQueued = false;
                var d = Weapons ? Weapons.Data(Chain[step], st) : AttackAnimationData.Make("Sword", Chain[step], st.windup, st.windup + 0.1f, st.windup + st.recover, st.reach, st.radius);
                float mul = step == 3 ? 1.6f : 1f + 0.12f * step;
                int bonus = Mathf.RoundToInt(S.SwordDamage * (mul - 1f));
                bool last = step == Chain.Length - 1;
                yield return Move(Chain[step], d, st.windup * (last ? 1.25f : 1f), bonus, st.knockback * (last ? 1.6f : 1f), last, step > 0,
                                  () => !last && _comboQueued && Stamina > 0.5f);
                if (!(AnimCtrl && AnimCtrl.LastChained) || !Spend(AttackCost * 0.8f)) break;
            }
            EndAttack();
        }

        void EndAttack()
        {
            AnimSpeed(1f);
            _attacking = false; _charging = false;
            if (anim) anim.SetBool(P_Charging, false);
            action = null;
        }

        protected override void InterruptAttack()
        {
            base.InterruptAttack();
            _attacking = false;
            if (_charging && anim) anim.SetBool(P_Charging, false);
            _charging = false;
        }

        /// <summary>K: a heavy blow; held for a moment it becomes a charged attack released when K is let go.</summary>
        IEnumerator HeavyOrCharged()
        {
            var w = S.Weapon; var st = w.Style;
            _attacking = true; _attackStarted = Time.time;
            _nextHeavy = Time.time + heavyCooldown * Mathf.Clamp(st.windup / 0.2f, 0.6f, 1.6f);
            moveVel = Vector2.zero;
            Lock(0.3f);
            float t0 = Time.time;
            while (GameInput.HeavyHeld && Time.time - t0 < 0.25f) yield return null;
            int bonus = Mathf.RoundToInt(S.SwordDamage * (st.heavyMul - 1f));
            if (!GameInput.HeavyHeld)
            {
                var d = Weapons ? Weapons.Data("HeavyAttack", st) : AttackAnimationData.Make("Sword", "HeavyAttack", st.windup * 1.6f, st.windup * 1.6f + 0.1f, st.windup * 1.6f + st.recover, st.reach * 1.15f, st.radius * 1.3f);
                yield return Move("HeavyAttack", d, st.windup * 1.6f, bonus, st.knockback * 1.8f, true, false, null);
                EndAttack();
                yield break;
            }
            // charging: the Charge loop plays while K is held (max 1.6 s), stamina drains a little
            _charging = true;
            if (anim) anim.SetBool(P_Charging, true);
            Sfx.Play(WeaponTypes.SwingSfx(Weapons ? Weapons.CurrentSet : "Sword", true), 0.6f);
            float charge = 0f;
            while (GameInput.HeavyHeld && charge < 1.6f && Stamina > 0)
            {
                moveVel = Vector2.zero;
                Lock(0.2f);
                charge += Time.deltaTime;
                Stamina = Mathf.Max(0, Stamina - 6f * Time.deltaTime); _staminaDelayUntil = Time.time + 0.5f;
                yield return null;
            }
            float k = Mathf.Clamp01(charge / 1.2f);
            if (k >= 0.99f) UIRoot.Popup(Body + Vector2.up * 0.7f, "¡CARGA MÁXIMA!", UIRoot.Gold);
            _charging = false;
            if (anim) anim.SetBool(P_Charging, false);           // Charge -> ChargedAttack_Release
            var rd = Weapons ? Weapons.Data("ChargedAttack_Release", st) : AttackAnimationData.Make("Sword", "ChargedAttack_Release", 0.15f, 0.3f, 0.6f, st.reach * 1.2f, st.radius * 1.4f);
            LastMove = "ChargedAttack_Release";
            yield return Move("ChargedAttack_Release", rd, 0.12f, bonus + Mathf.RoundToInt(S.SwordDamage * (0.5f + k)), st.knockback * (2f + k), true, false, null, trigger: false);
            EndAttack();
        }

        static readonly int P_Charging = Animator.StringToHash("IsCharging");

        /// <summary>One attack move: animation, hit window, magic bolts on the Projectile frame, costs and feedback.</summary>
        IEnumerator Move(string move, AttackAnimationData d, float impactAt, int bonus, float knockback, bool heavy, bool chained,
                         System.Func<bool> chainNow, bool trigger = true)
        {
            var w = S.Weapon;
            string set = Weapons ? Weapons.CurrentSet : WeaponTypes.SetFor(w);
            float speed = d.SpeedFor(impactAt);
            LastMove = move; LastSwing = Time.time;
            moveVel = Vector2.zero;
            Lock(d.end / speed + 0.02f);
            int hits = 0;
            var cb = new CharacterAnimationController.Callbacks
            {
                telegraph = () => Sfx.Play(string.IsNullOrEmpty(d.sfxSwing) ? WeaponTypes.SwingSfx(set, heavy) : d.sfxSwing, heavy ? 0.85f : 0.75f),
                hitOn = () =>
                {
                    var info = Sword(bonus, knockback, heavy);
                    info.element = WeaponElement(w);
                    float reach = Mathf.Max(0.55f, d.reach), radius = Mathf.Max(0.3f, d.radius);
                    WeaponFx.Swing(string.IsNullOrEmpty(d.fx) ? w.Style.fx : d.fx, AttackPoint(reach * 0.55f), facing, radius, w);
                    if (WeaponTypes.Shockwave(set, move)) WeaponFx.Shockwave(AttackPoint(reach * 0.7f), radius, w);
                    Hitbox.Open(d, info, reach, radius, OnWeaponHit, true);
                },
                hitOff = () =>
                {
                    hits = Hitbox.Close();
                    if (hits > 0)
                    {
                        UseOil(); Wear(S.weapon, 1);
                        if (heavy || d.shake > 0) CameraFollow.Shake(Mathf.Max(d.shake, 0.1f), heavy ? 0.12f : 0.07f);
                    }
                    else Sfx.Play("wpn_whiff", 0.45f);
                },
                projectile = () => FireMagic(move, bonus, heavy),
            };
            yield return AnimCtrl.RunAttack(d, speed, cb, trigger, chainNow);
        }

        void OnWeaponHit(Health h, DamageInfo d)
        {
            var w = S.Weapon;
            if (w.lifesteal > 0) health.Heal(w.lifesteal);
        }

        /// <summary>Staff: a magic bolt leaves the crystal on the Projectile frame of the animation.</summary>
        void FireMagic(string move, int bonus, bool heavy)
        {
            var w = S.Weapon;
            var a = GameAssets.I;
            var prefab = a ? (a.magicBoltPrefab ? a.magicBoltPrefab : a.fireballPrefab) : null;
            int shots = heavy ? 3 : 1;
            for (int i = 0; i < shots; i++)
            {
                Vector2 d = Quaternion.Euler(0, 0, (i - (shots - 1) / 2f) * 14f) * facing;
                bool crit = Random.value < S.CritChance;
                int dmg = Mathf.Max(1, S.SwordDamage + bonus / 2 + (heavy ? 1 : 0) + (S.classId == "mage" ? 1 : 0));   // Mago: arcano
                var p = Projectile.Fire(prefab, Body + d * 0.5f, d, heavy ? 9f : 10f, crit ? dmg * 2 : dmg, Team.Player, transform);
                if (p)
                {
                    p.crit = crit; p.element = WeaponElement(w);
                    var psr = p.GetComponentInChildren<SpriteRenderer>();
                    if (psr && !(a && a.magicBoltPrefab)) psr.color = WeaponTypes.MagicColor(w);
                }
            }
            Sfx.Play(heavy ? "magic_burst" : "magic_bolt", 0.8f);
            UseOil();
        }

        Element WeaponElement(ItemDef w)
        {
            if (S.oilHits > 0 && !string.IsNullOrEmpty(S.oil))
                return S.oil == "aceite_fuego" ? Element.Fire : S.oil == "aceite_hielo" ? Element.Frost : S.oil == "aceite_sagrado" ? Element.Holy : w.element;
            if (S.classId == "crusader" && w.element == Element.None) return Element.Holy;       // Cruzado: golpes sagrados
            return w.element;
        }

        void UseOil()
        {
            if (S.oilHits <= 0) return;
            if (--S.oilHits <= 0) { S.oil = ""; UIRoot.Toast("EL ACEITE DEL ARMA SE HA GASTADO"); }
        }

        void Wear(string itemId, int n)
        {
            if (string.IsNullOrEmpty(itemId)) return;
            bool was = S.Broken(itemId);
            int before = S.Durability(itemId);
            S.AddWear(itemId, n);
            int max = CraftDB.MaxDurability(ItemDB.Get(itemId));
            if (!was && S.Broken(itemId)) { UIRoot.Toast(ItemDB.Get(itemId).name.ToUpperInvariant() + " SE HA ROTO · REPÁRALO EN LA HERRERÍA", 3f); Sfx.Play("guard_break", 0.6f); }
            else if (before > max / 4 && S.Durability(itemId) <= max / 4) UIRoot.Toast(ItemDB.Get(itemId).name.ToUpperInvariant() + " ESTÁ MUY DESGASTADA", 2.2f);
        }

        void AnimSpeed(float k) { if (anim) anim.speed = Mathf.Clamp(k, 0.6f, 1.8f); }

        // ------------------------------------------------------------ parry + riposte
        IEnumerator Parry()
        {
            _nextParry = Time.time + 0.55f;
            _parryUntil = Time.time + ParryWindow;
            Lock(0.42f);
            moveVel = Vector2.zero;
            SetBlock(true);
            Sfx.Play("swing", 0.5f);
            yield return new WaitForSeconds(0.38f);
            SetBlock(false);
            action = null;
        }

        /// <summary>J next to an enemy stunned by a parry: a critical riposte (x3 damage, always critical).</summary>
        bool TryRiposte()
        {
            EnemyController best = null; float bd = 1.5f * Scale;
            foreach (var e in EnemyController.Active)
            {
                if (e == null || !e.Stunned || e.health.IsDead) continue;
                float d = Vector2.Distance(e.Body, Body);
                if (d < bd) { bd = d; best = e; }
            }
            if (best == null) return false;
            Run(Riposte(best));
            return true;
        }

        IEnumerator Riposte(EnemyController e)
        {
            Face(e.Body - Body);
            LastSwing = Time.time; LastMove = "CriticalAttack";
            var st = S.Weapon.Style;
            var d = Weapons ? Weapons.Data("CriticalAttack", st) : AttackAnimationData.Make("Sword", "CriticalAttack", 0.28f, 0.4f, 0.6f, 1f, 1f);
            float speed = d.SpeedFor(0.28f);
            Lock(d.end / speed + 0.05f);
            Sfx.Play("heavy_swing");
            health.SetInvulnerable(true);
            _attacking = true;
            // the riposte lands on the HitOn frame of the CriticalAttack animation of the weapon in hand
            var cb = new CharacterAnimationController.Callbacks
            {
                hitOn = () =>
                {
                    if (e == null || e.health.IsDead) return;
                    int dmg = S.SwordDamage * 3 + 2;
                    e.EndStun();
                    e.health.Damage(new DamageInfo { amount = dmg, direction = facing, knockback = 9f, source = Team.Player, heavy = true, crit = true, element = WeaponElement(S.Weapon), attacker = transform });
                    Sfx.Play("riposte");
                    CameraFollow.Shake(0.25f, 0.16f);
                    Fx.Spawn(FxKind.Hit, e.Body, 120);
                    WeaponFx.Spark(e.Body, new Color(1f, 0.9f, 0.4f));
                    UIRoot.Popup(e.Body + Vector2.up * 0.9f, "¡CRÍTICO!", UIRoot.Gold);
                    StartCoroutine(HitStop(0.12f));
                    UseOil(); Wear(S.weapon, 1);
                },
            };
            yield return AnimCtrl.RunAttack(d, speed, cb);
            health.SetInvulnerable(false);
            EndAttack();
        }

        static IEnumerator HitStop(float seconds)
        {
            if (Time.timeScale < 0.99f) yield break;
            Time.timeScale = 0.05f;
            yield return new WaitForSecondsRealtime(seconds);
            if (!GameManager.Paused && !WorldUI.PanelOpen) Time.timeScale = 1f;
        }

        // ------------------------------------------------------------ bow
        void TryBow()
        {
            var kc = KnightClass.Get(S.classId);
            if (kc.UsesMagic) { if (Spend(bowCost)) Run(MagicCast()); return; }        // Mago: L casts a magic bolt
            if (!kc.UsesBow) { UIRoot.Toast("SOLO LA ARQUERA USA ARCO", 1.6f); return; }
            bool special = !string.IsNullOrEmpty(S.ammo) && S.InBag(S.ammo) > 0;
            if (!special && S.arrows <= 0) { UIRoot.Toast("SIN FLECHAS"); return; }
            if (!Spend(bowCost)) return;
            Run(Bow());
        }

        /// <summary>Mago: a quick spell (L) - a magic bolt from the staff, no arrows needed.</summary>
        IEnumerator MagicCast()
        {
            _attacking = true; LastMove = "CastSpell";
            moveVel = Vector2.zero;
            Lock(0.42f);
            Trigger("CastSpell");
            Sfx.Play("magic_charge", 0.6f);
            yield return new WaitForSeconds(0.22f);
            if (!health.IsDead) FireMagic("CastSpell", 1, false);
            yield return new WaitForSeconds(0.2f);
            _attacking = false;
        }

        IEnumerator Bow()
        {
            var b = S.Bow; var st = b.Style;
            var d = Weapons ? Weapons.Data("SpecialAttack", st) : AttackAnimationData.Make("Bow", "SpecialAttack", -1f, -1f, st.windup + st.recover, 0, 0, HitShape.Arc, st.windup);
            float speed = d.SpeedFor(st.windup);
            Lock(d.end / speed + 0.02f);
            LastMove = "SpecialAttack"; _attacking = true;
            bool shot = false;
            var cb = new CharacterAnimationController.Callbacks
            {
                telegraph = () => Sfx.Play(WeaponTypes.SwingSfx(WeaponTypes.BowSet(b.kind), false), 0.6f),
                projectile = () => { shot = true; ShootArrows(b, st); },
            };
            // the arrow leaves on the Projectile frame of the bow's SpecialAttack animation
            yield return AnimCtrl.RunAttack(d, speed, cb);
            if (!shot) ShootArrows(b, st);
            EndAttack();
        }

        void ShootArrows(ItemDef b, WeaponStyle st)
        {
            string ammo = !string.IsNullOrEmpty(S.ammo) && S.InBag(S.ammo) > 0 ? S.ammo : "";
            if (ammo != "") { S.Consume(ammo, 1, false); if (S.InBag(ammo) == 0) { S.ammo = ""; UIRoot.Toast("SE ACABARON LAS FLECHAS ESPECIALES"); } }
            else S.arrows--;
            var element = ammo == "flecha_fuego" ? Element.Fire : ammo == "flecha_veneno" ? Element.Venom : b.element;
            int shots = Mathf.Max(1, b.multishot);
            for (int i = 0; i < shots; i++)
            {
                float ang = (i - (shots - 1) / 2f) * 12f;
                Vector2 d = Quaternion.Euler(0, 0, ang) * facing;
                bool crit = Random.value < S.BowCritChance;
                int dmg = S.ArrowDamage;
                var arrow = Projectile.Fire(GameAssets.I.arrowPrefab, Body + d * 0.4f, d, st.ArrowSpeed, crit ? dmg * 2 : dmg, Team.Player, transform);
                if (arrow)
                {
                    arrow.crit = crit; arrow.element = element;
                    arrow.pierce = (S.classId == "ranger" ? 2 : 0) + b.pierce + (ammo == "flecha_plata" ? 1 : 0);
                    var asr = arrow.GetComponentInChildren<SpriteRenderer>();
                    if (element == Element.Fire) asr.color = new Color(1f, 0.7f, 0.4f);
                    else if (element == Element.Venom) asr.color = new Color(0.6f, 1f, 0.45f);
                    else if (ammo == "flecha_plata") asr.color = new Color(0.85f, 0.95f, 1f);
                }
            }
            Wear(S.bow, 1);
            Sfx.Play(b.kind == WeaponKind.Crossbow ? "crossbow_shot" : "bow_release");
        }

        // ------------------------------------------------------------ dodge
        IEnumerator Roll(Vector2 input)
        {
            Vector2 dir = input.sqrMagnitude > 0.01f ? Combat.Snap4(input) : facing;
            Face(dir);
            _nextRoll = Time.time + S.RollCooldown;
            Lock(0.42f);
            Trigger("Roll");
            Sfx.Play("roll");
            health.SetInvulnerable(true);
            _rollVel = input.normalized * rollSpeed;
            Fx.Spawn(FxKind.Dust, transform.position, 5);
            yield return new WaitForSeconds(0.32f);
            _rollVel = Vector2.zero;
            health.SetInvulnerable(false);
            yield return new WaitForSeconds(0.1f);
            action = null;
        }

        /// <summary>Space without a direction: a quick hop backwards, shorter invulnerability than the roll.</summary>
        IEnumerator Backstep()
        {
            _nextRoll = Time.time + S.RollCooldown * 0.8f;
            Lock(0.3f);
            Trigger("Dodge");
            Sfx.Play("roll", 0.6f);
            health.SetInvulnerable(true);
            _rollVel = -facing * 6f;
            yield return new WaitForSeconds(0.18f);
            _rollVel = Vector2.zero;
            health.SetInvulnerable(false);
            yield return new WaitForSeconds(0.1f);
            action = null;
        }

        void TryInteract()
        {
            var it = Interactable.Nearest(AttackPoint(0.4f), 1.1f);
            if (it != null)
            {
                Face((Vector2)it.transform.position - (Vector2)transform.position);
                Trigger("Interact");
                it.Interact(this);
            }
        }

        // ------------------------------------------------------------ quick items
        void CycleQuick()
        {
            string id = S.CycleQuick();
            var m = CraftDB.Get(id);
            Sfx.Play("select", 0.6f);
            UIRoot.Toast(m != null ? $"{m.name} ({S.InBag(id)})" : "BOLSA SIN OBJETOS DE USO", 1.2f);
        }

        void UseQuick()
        {
            if (string.IsNullOrEmpty(S.quick) || S.InBag(S.quick) <= 0)
            {
                S.CycleQuick();
                if (string.IsNullOrEmpty(S.quick)) { UIRoot.Toast("NO LLEVAS MEDICINAS · FABRÍCALAS EN UN CAMPAMENTO", 2.2f); return; }
            }
            UseItem(S.quick);
        }

        /// <summary>Uses a consumable from the bag. Healing takes a moment (you can be interrupted); throwing and coating are quick.</summary>
        public bool UseItem(string id)
        {
            var m = CraftDB.Get(id);
            if (m == null || S.InBag(id) <= 0) return false;
            switch (id)
            {
                case "venda": case "unguento": case "medicina": case "guiso": case "elixir":
                    if (health.hp >= health.maxHP && id != "guiso" && id != "elixir") { UIRoot.Toast("VIDA COMPLETA"); return false; }
                    Run(Heal(id)); return true;
                case "tonico":
                    S.Consume(id, 1, false); RestoreStamina(); _tonicUntil = Time.time + 60f;
                    Fx.Spawn(FxKind.Sparkle, Body); Sfx.Play("potion"); UIRoot.Toast("TÓNICO: ALIENTO RENOVADO", 1.6f); return true;
                case "bomba": case "bomba_veneno":
                    if (!Spend(10f)) return false;
                    S.Consume(id, 1, false); Run(Throw(id)); return true;
                case "aceite_fuego": case "aceite_hielo": case "aceite_sagrado":
                    S.Consume(id, 1, false); S.oil = id; S.oilHits = 30;
                    Lock(0.4f); Trigger("Interact"); Sfx.Play("craft", 0.7f);
                    UIRoot.Toast($"{m.name.ToUpperInvariant()} APLICADO: 30 GOLPES", 2f); return true;
                case "flecha_fuego": case "flecha_veneno": case "flecha_plata":
                    S.ammo = id; Sfx.Play("select"); UIRoot.Toast($"CARGADAS: {m.name.ToUpperInvariant()} ({S.InBag(id)})", 1.8f); return true;
                case "kit_reparar":
                {
                    var w = S.Weapon;
                    if (S.Wear(S.weapon) <= 0) { UIRoot.Toast("TU ARMA NO NECESITA REPARACIÓN"); return false; }
                    S.Consume(id, 1, false); S.Repair(S.weapon, CraftDB.MaxDurability(w) / 2);
                    Lock(0.8f); Trigger("Interact"); Sfx.Play("anvil");
                    UIRoot.Toast($"{w.name.ToUpperInvariant()} REPARADA ({S.Durability(S.weapon)}/{CraftDB.MaxDurability(w)})", 2f); return true;
                }
            }
            return false;
        }

        IEnumerator Heal(string id)
        {
            moveVel = Vector2.zero;
            Lock(0.7f);
            Trigger("PickUp");
            Sfx.Play(id == "guiso" ? "eat" : "potion", 0.6f);
            float t0 = Time.time;
            while (Time.time - t0 < 0.55f) { moveVel = Vector2.zero; yield return null; }    // interrupted if hit: OnDamaged cancels this
            S.Consume(id, 1, false);
            switch (id)
            {
                case "venda": health.Heal(S.HealPower(4)); break;
                case "unguento": health.Heal(S.HealPower(6)); StartCoroutine(HealOverTime(4, 1f)); break;
                case "medicina": health.Heal(S.HealPower(13)); break;
                case "guiso": health.Heal(S.HealPower(4)); _stewUntil = Time.time + 180f; UIRoot.Toast("GUISO: +25 DE AGUANTE MÁXIMO DURANTE 3 MIN", 2f); break;
                case "elixir": health.Heal(999); RestoreStamina(); break;
            }
            Fx.Spawn(FxKind.Heal, Body);
            action = null;
        }

        IEnumerator HealOverTime(int ticks, float every)
        {
            for (int i = 0; i < ticks && !health.IsDead; i++) { yield return new WaitForSeconds(every); health.Heal(1); }
        }

        IEnumerator Throw(string id)
        {
            Lock(0.35f);
            Trigger("SpecialAttack");
            yield return new WaitForSeconds(0.15f);
            ThrownBomb.Throw(id, Body + facing * 0.3f, facing, this);
            Sfx.Play("swing", 0.6f);
            yield return new WaitForSeconds(0.2f);
            action = null;
        }

        // ------------------------------------------------------------ damage
        protected override void OnDamaged(DamageInfo d)
        {
            base.OnDamaged(d);
            _lastHurt = Time.time;
            UIRoot.Popup(Body + Vector2.up * 0.5f, "-" + d.amount, UIRoot.Red);
            _attacking = false; _rollVel = Vector2.zero;
            CancelAction();
            SetBlock(false);
            AnimSpeed(1f);
            Wear(S.armor, 1);
            if (health.IsDead) return;
            Lock(0.25f);
            Sfx.Play("player_hurt");
            CameraFollow.Shake(0.15f, 0.1f);
            StartCoroutine(Blink(health.invulnerableAfterHit));
        }

        void OnAvoided(DamageInfo d)
        {
            if (_avoidKind == 1) return;    // parry: handled in Defend
            if (_avoidKind == 2) { Trigger("BlockHit"); Sfx.Play("block"); UIRoot.Popup(Body + Vector2.up * 0.5f, "BLOQUEO", UIRoot.Cream); knockVel = d.direction * 2.5f; return; }
            UIRoot.Popup(Body + Vector2.up * 0.5f, "ESQUIVA", UIRoot.Cream);
        }

        protected override void OnDied()
        {
            Sfx.Play("player_die");
            Lock(99f);
            SetBlock(false);
            StartCoroutine(DeathSequence());
        }

        IEnumerator DeathSequence()
        {
            yield return new WaitForSeconds(1.6f);
            GameManager.PlayerDied();
        }

        DamageInfo Sword(int bonus, float knockback, bool heavy)
        {
            bool crit = Random.value < S.CritChance;
            int dmg = S.SwordDamage + bonus;
            return new DamageInfo { amount = crit ? dmg * 2 : dmg, knockback = knockback * (crit ? 1.3f : 1f), source = Team.Player, heavy = heavy || crit, crit = crit, attacker = transform };
        }

        int _avoidKind;   // what the last cancelled hit was: 0 dodge, 1 parry, 2 shield block

        bool Frontal(DamageInfo d, float tolerance)
        {
            Vector2 from = d.attacker != null ? ((Vector2)d.attacker.position - (Vector2)transform.position).normalized : -d.direction;
            return Vector2.Dot(from, facing) > tolerance;
        }

        /// <summary>Parry, shield block, then Agility (dodge chance) and armour.</summary>
        DamageInfo Defend(DamageInfo d)
        {
            _avoidKind = 0;
            // parry: a melee blow inside the window is turned aside and the attacker is stunned
            if (ParryActive && Frontal(d, -0.2f))
            {
                _avoidKind = 1;
                var e = d.attacker != null ? d.attacker.GetComponentInParent<EnemyController>() : null;
                if (!d.ranged && e != null) e.Parried(this);
                Sfx.Play("parry");
                Fx.Spawn(FxKind.Hit, Body + facing * 0.4f, 120);
                UIRoot.Popup(Body + Vector2.up * 0.7f, d.ranged ? "DESVÍO" : "¡PARRY!", UIRoot.Gold);
                Stamina = Mathf.Min(MaxStamina, Stamina + parryCost);
                StartCoroutine(HitStop(0.08f));
                d.amount = 0; return d;
            }
            // shield: frontal hits cost stamina instead of life; a hit you can't afford breaks the guard
            if (_blocking && Frontal(d, 0.1f))
            {
                float cost = 6f + d.amount * 5f * (d.heavy ? 1.4f : 1f);
                if (Stamina >= cost)
                {
                    _avoidKind = 2;
                    Stamina -= cost; _staminaDelayUntil = Time.time + 0.6f;
                    d.amount = 0; return d;
                }
                Stamina = 0; _exhausted = true;
                SetBlock(false);
                Sfx.Play("guard_break");
                UIRoot.Popup(Body + Vector2.up * 0.7f, "GUARDIA ROTA", UIRoot.Red);
                d.amount = Mathf.Max(1, d.amount / 2);
                d.amount = Mathf.Max(1, d.amount - S.Armor);
                StartCoroutine(GuardBroken());
                return d;
            }
            if (Random.value < S.DodgeChance) { d.amount = 0; return d; }
            d.amount = Mathf.Max(1, d.amount - S.Armor);
            return d;
        }

        IEnumerator GuardBroken()
        {
            yield return null;               // after OnDamaged has set its own short lock
            Lock(0.8f);
            Trigger("Knockback");
        }

        /// <summary>Paladin perk: out of combat, one half-heart every 6 seconds.</summary>
        void Regenerate()
        {
            if (S.classId != "paladin" || health.hp >= health.maxHP || Time.time - _lastHurt < 5f || Time.time < _nextRegen) return;
            _nextRegen = Time.time + 6f;
            health.Heal(1);
        }

        public void Heal(int amount)
        {
            if (health.Heal(amount) > 0) { Fx.Spawn(FxKind.Heal, Body); Sfx.Play("potion"); }
        }
    }
}
