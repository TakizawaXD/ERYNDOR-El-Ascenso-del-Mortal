using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    public enum EnemyKind { Orc, Demon, BloodMonster }
    public enum EnemyRank { Normal, Elite, Champion }
    public enum ActiveTime { Always, Day, Night }

    /// <summary>How an enemy fights. Every regional enemy type uses one of these.</summary>
    public enum AIProfile
    {
        Brute,       // walks straight in, heavy swings, hard to push (frost orcs)
        Pack,        // calls nearby allies and flanks from the sides (orcs, corsairs)
        Skirmisher,  // hit and run, circles while its attack recharges, flees when hurt (desert orcs)
        Kiter,       // keeps its distance and spits from range (blood monsters)
        Caster,      // teleports around the player and throws fire volleys (demons)
        Ambusher,    // hides almost invisible and lunges when you pass by (toxic slimes)
        Charger,     // winds up and rams in a straight line (berserkers)
        Wraith,      // night ghost: floats through walls, fades out after striking, burns at dawn
        Duelist,     // fallen knight: blocks, sidesteps your swings and counter-attacks
        Bomber,      // magma spawn: keeps distance, explodes when it dies
    }

    /// <summary>Regional enemy with its own AI profile, rank scaling and day/night activity. Bosses get a rage phase below 50% HP.</summary>
    public class EnemyController : Actor
    {
        public static readonly List<EnemyController> Active = new List<EnemyController>();

        public EnemyKind kind = EnemyKind.Orc;
        public string typeId = "Orc";
        public string displayName = "ORCO";
        public AIProfile ai = AIProfile.Brute;
        public ActiveTime activeAt = ActiveTime.Always;
        public int maxHP = 6;
        public int damage = 2;
        public float chaseSpeed = 2.2f;
        public float aggroRange = 5f;
        public float attackRange = 0.9f;
        public float attackCooldown = 1.2f;
        [Range(0, 1)] public float heavyChance = 0.3f;
        [Range(0, 1)] public float knockbackResist;
        public int xpReward = 3;
        [Header("Ranged (Demon fireball / Blood spit)")]
        public bool ranged;
        public float rangedMin = 2.5f, rangedMax = 6f, rangedCooldown = 3f;
        public int rangedDamage = 2;
        [Header("Loot")]
        public int coins = 2;
        [Range(0, 1)] public float potionChance = 0.15f;
        [Range(0, 1)] public float arrowChance = 0.25f;
        [Header("Boss")]
        public bool isBoss;
        [Tooltip("world flag set when this boss dies (boss_K, boss_Q, boss_B)")]
        public string bossFlag = "";

        [HideInInspector] public EnemyRank rank = EnemyRank.Normal;
        [HideInInspector] public bool spawned;          // created by the SpawnDirector (not a map resident)
        [Header("Allies (the Summoner's curse) and summoned minions")]
        [HideInInspector] public bool ally;             // raised by the player: fights for them
        [HideInInspector] public string allyTask = Summoning.Follow;
        [HideInInspector] public Vector2 guardPoint;
        [HideInInspector] public EnemyController summoner;   // minion raised by a boss (no loot)
        [HideInInspector] public bool shielded;         // immune (the Summoner while his minions live)
        float _stunUntil;
        Coroutine _stunFx;

        public bool Stunned => Time.time < _stunUntil && !health.IsDead;
        public bool Asleep => _asleep;
        public float DiedAt { get; private set; } = -1f;

        Vector2 _home, _wanderTarget;
        float _nextAttack, _nextRanged, _nextWander, _stuckTimer, _nextSpecial, _retreatUntil, _fleeUntil, _hideAt;
        bool _enraged, _fled, _hidden, _alerted;
        Vector2 _lastPos;
        Collider2D _col;
        float _speedMul = 1f;

        public bool Enraged => _enraged;
        public bool Hidden => _hidden;
        public Vector2 Home => _home;
        public bool ShowsBar => isBoss || rank == EnemyRank.Champion;
        public bool Engaged => _wasChasing;
        public const float ActiveRange = 16f;      // beyond this the enemy sleeps (open-world performance)
        bool _bossBarShown;
        float _nextCull;
        bool _asleep;

        protected override void Awake()
        {
            base.Awake();
            _col = GetComponent<Collider2D>();
            health.team = Team.Enemy;
            health.invulnerableAfterHit = isBoss ? 0.15f : 0.25f;
            health.Init(maxHP);
            health.filter = Filter;
            health.Avoided += OnAvoided;
            _home = transform.position;
            _sideSign = Random.value < 0.5f ? 1f : -1f;
            _wanderTarget = _home;
            _nextRanged = Time.time + Random.Range(1f, rangedCooldown);
            _nextSpecial = Time.time + Random.Range(1.5f, 4f);
            if (ai == AIProfile.Wraith && _col) _col.isTrigger = true;     // drifts through walls and trees
            if (ai == AIProfile.Ambusher) Hide(true);
            Face(Vector2.down);
        }

        void OnEnable() { if (!Active.Contains(this)) Active.Add(this); }
        void OnDisable() { Active.Remove(this); }

        void Start()
        {
            // bosses already beaten in this save stay beaten
            if (isBoss && !string.IsNullOrEmpty(bossFlag) && GameManager.State.Has(bossFlag)) { gameObject.SetActive(false); return; }
            GameManager.RegisterEnemy(this);
            ApplyLook();
        }

        // ------------------------------------------------------------ rank + scaling
        /// <summary>Called by the SpawnDirector: threat level (1..10) makes everything tougher; elites and champions far more.</summary>
        public void Setup(EnemyRank r, int threat, bool night)
        {
            rank = r;
            float hpMul = 1f + 0.12f * (threat - 1);
            int dmgAdd = (threat - 1) / 3;
            _speedMul = night ? 1.1f : 1f;
            switch (r)
            {
                case EnemyRank.Elite:
                    hpMul *= 2.5f; dmgAdd += 1 + damage / 2; xpReward *= 3; coins = coins * 3 + 3; potionChance = Mathf.Max(potionChance, 0.5f);
                    displayName = displayName + " PODEROSO"; transform.localScale *= 1.25f; knockbackResist = Mathf.Max(knockbackResist, 0.5f);
                    break;
                case EnemyRank.Champion:
                    hpMul *= 5f; dmgAdd += 2 + damage / 2; xpReward *= 8; coins = coins * 6 + 10; potionChance = 1f;
                    displayName = "CAMPEÓN: " + displayName; transform.localScale *= 1.5f; knockbackResist = 0.8f;
                    aggroRange *= 1.3f; attackCooldown *= 0.8f;
                    break;
            }
            maxHP = Mathf.RoundToInt(maxHP * hpMul);
            damage += dmgAdd; rangedDamage += dmgAdd;
            xpReward = Mathf.RoundToInt(xpReward * (1f + 0.1f * (threat - 1)));
            health.Init(maxHP);
            ApplyLook();
        }

        void ApplyLook()
        {
            if (!sr) return;
            var c = Color.white;
            if (rank == EnemyRank.Elite) c = new Color(1f, 0.82f, 0.7f);
            if (rank == EnemyRank.Champion) c = new Color(1f, 0.7f, 0.55f);
            if (ally) c = new Color(0.78f, 0.62f, 1f);
            if (ai == AIProfile.Wraith) c.a = 0.72f;
            if (_hidden) c.a = 0.18f;
            sr.color = c;
            if (ally && GetComponentInChildren<LightGlow>() == null)
                LightGlow.Attach(transform, new Vector2(0, 0.4f), 1.6f, new Color(0.7f, 0.4f, 1f), 0.7f, true);
            if (rank != EnemyRank.Normal && GetComponentInChildren<LightGlow>() == null)
                LightGlow.Attach(transform, new Vector2(0, 0.5f), rank == EnemyRank.Champion ? 2.2f : 1.4f,
                                 rank == EnemyRank.Champion ? new Color(1f, 0.3f, 0.2f) : new Color(1f, 0.75f, 0.3f), 0.7f, true);
        }

        // ------------------------------------------------------------ main loop
        void Update()
        {
            if (health.IsDead || GameManager.Paused) { moveVel = Vector2.zero; return; }
            var p = PlayerController.Current;
            // sleep when far from the player: no AI, no animation, no physics work
            if (Time.time >= _nextCull)
            {
                _nextCull = Time.time + 0.4f + Random.value * 0.2f;
                bool far = p == null || Vector2.Distance(p.transform.position, transform.position) > ActiveRange * Scale;
                if (far != _asleep)
                {
                    _asleep = far;
                    if (anim) anim.enabled = !far;
                    rb.simulated = !far;
                    if (far) { moveVel = Vector2.zero; if (!spawned) transform.position = _home; _wasChasing = false; _alerted = false; if (_bossBarShown) { _bossBarShown = false; UIRoot.HideBoss(); } }
                }
            }
            if (_asleep) return;
            if (ShowsBar && p != null)
            {
                bool near = Vector2.Distance(p.transform.position, transform.position) < aggroRange * 1.6f;
                if (near != _bossBarShown) { _bossBarShown = near; if (near) UIRoot.ShowBoss(this); else UIRoot.HideBoss(); }
            }
            if (Locked) { if (action == null) moveVel = Vector2.zero; SetLocomotion(0); return; }
            if (ally) { AllyThink(p); return; }

            Actor tgt = ChooseTarget(p);
            bool playerAlive = tgt != null;
            float dist = playerAlive ? Vector2.Distance(Body, tgt.Body) : 999f;
            float leash = aggroRange * (ShowsBar ? 3f : 1.8f);

            if (_hidden)
            {
                if (playerAlive && dist < 2.8f) { Run(Lunge(tgt)); return; }
                moveVel = Vector2.zero; SetLocomotion(0); return;
            }

            if (playerAlive && (dist < aggroRange || (dist < leash && _wasChasing)))
            {
                if (!_wasChasing && !ally && !isBoss) Sfx.Voice(this, "alert", 0.55f);
                _wasChasing = true;
                Vector2 to = tgt.Body - Body;
                Face(to);
                if (Decide(tgt, dist)) return;
                Chase(tgt, dist, to);
            }
            else
            {
                _wasChasing = false; _alerted = false;
                Wander();
                if (ai == AIProfile.Ambusher && !_hidden && Vector2.Distance(transform.position, _home) < 0.6f)
                {
                    if (_hideAt == 0) _hideAt = Time.time + 3f;
                    else if (Time.time > _hideAt) Hide(true);
                }
            }
        }

        /// <summary>Starts an attack or special move if one is ready. Returns true when it did.</summary>
        bool Decide(Actor p, float dist)
        {
            if (Time.time < _fleeUntil) return false;
            bool keepsAway = ai == AIProfile.Kiter || ai == AIProfile.Bomber;
            if (ranged && dist >= rangedMin && dist <= rangedMax && Time.time >= _nextRanged) { Run(Ranged(p)); return true; }
            if (ai == AIProfile.Caster && Time.time >= _nextSpecial && dist > 1.4f && dist < aggroRange * 1.5f) { Run(Blink(p)); return true; }
            if (ai == AIProfile.Charger && Time.time >= _nextSpecial && dist > 2.2f && dist < 6.5f) { Run(Charge(p)); return true; }
            if (ai == AIProfile.Duelist && p is PlayerController && Time.time >= _nextSpecial && dist < 2.2f && Time.time - PlayerController.LastSwing < 0.2f && Random.value < 0.5f)
            { Run(Sidestep(p)); return true; }
            if (dist <= attackRange * Scale && Time.time >= _nextAttack && (!keepsAway || _stuckTimer > 0.3f || dist < 0.8f))
            { Run(Melee()); return true; }
            return false;
        }

        void Chase(Actor p, float dist, Vector2 to)
        {
            Vector2 dir = to.normalized;
            float sp = (_enraged ? 1.35f : 1f) * chaseSpeed * _speedMul * (Time.time < _slowUntil ? 0.5f : 1f);
            if (Time.time < _fleeUntil) { Move(-dir, sp * 1.1f); return; }
            switch (ai)
            {
                case AIProfile.Pack:
                    if (!_alerted) AlertPack();
                    if (dist > 2.3f)
                    {
                        Vector2 flank = p.Body + (Vector2)(Quaternion.Euler(0, 0, _sideSign * 55f) * -dir) * 1.7f;
                        Move((flank - Body).normalized, sp);
                    }
                    else Move(dir, sp);
                    break;
                case AIProfile.Skirmisher:
                    if (Time.time < _retreatUntil) Move(-dir, sp * 1.05f);
                    else if (Time.time < _nextAttack && dist < 3f) Move(Strafe(dir, 0.35f), sp * 0.7f);
                    else Move(dir, sp * 1.15f);
                    break;
                case AIProfile.Kiter:
                case AIProfile.Bomber:
                case AIProfile.Caster:
                    if (dist < rangedMin * 0.85f && _stuckTimer < 0.3f) Move(-dir, sp);
                    else if (dist <= rangedMax) Move(Strafe(dir, 0f), walkSpeed * 0.6f);
                    else Move(dir, sp);
                    break;
                case AIProfile.Wraith:
                    Move((dir + Vector2.Perpendicular(dir) * Mathf.Sin(Time.time * 3f + _sideSign) * 0.6f).normalized, sp);
                    break;
                case AIProfile.Duelist:
                    if (dist < 1.6f && Time.time < _nextAttack) Move(Strafe(dir, -0.2f), sp * 0.6f);
                    else Move(dir, sp);
                    break;
                default:
                    Move(dir, sp);
                    break;
            }
        }

        void Move(Vector2 dir, float speed)
        {
            moveVel = (ai == AIProfile.Wraith ? dir : Steer(dir)) * speed;
            SetLocomotion(speed > walkSpeed ? 1f : 0.5f);
        }

        /// <summary>Sideways around the player (bias &gt; 0 closes in, &lt; 0 backs off).</summary>
        Vector2 Strafe(Vector2 dir, float bias)
        {
            if (Random.value < 0.01f) _sideSign = -_sideSign;
            return (Vector2.Perpendicular(dir) * _sideSign + dir * bias).normalized;
        }

        bool _wasChasing;
        float _sideSign = 1f;

        Vector2 Steer(Vector2 dir)
        {
            // tiny anti-stuck: if we barely moved while trying to, slide sideways for a moment
            if (((Vector2)transform.position - _lastPos).sqrMagnitude < 0.0004f) _stuckTimer += Time.deltaTime;
            else _stuckTimer = 0;
            _lastPos = transform.position;
            if (_stuckTimer > 0.35f) return (dir + Vector2.Perpendicular(dir) * _sideSign).normalized;
            return dir;
        }

        void Wander()
        {
            if (Time.time > _nextWander)
            {
                _nextWander = Time.time + Random.Range(1.5f, 3.5f);
                _wanderTarget = Random.value < 0.35f ? (Vector2)transform.position : _home + Random.insideUnitCircle * 2.5f;
            }
            Vector2 to = _wanderTarget - (Vector2)transform.position;
            if (to.magnitude > 0.2f)
            {
                moveVel = (ai == AIProfile.Wraith ? to.normalized : Steer(to.normalized)) * walkSpeed * 0.5f;
                Face(to);
                SetLocomotion(0.5f);
            }
            else { moveVel = Vector2.zero; SetLocomotion(0); }
        }

        void AlertPack()
        {
            _alerted = true;
            foreach (var e in Active)
                if (e != this && !e._wasChasing && e.ai == AIProfile.Pack && Vector2.Distance(e.transform.position, transform.position) < 8f)
                { e._wasChasing = true; e._alerted = true; }
            Sfx.Voice(this, "alert", 0.7f);
        }

        // ------------------------------------------------------------ attacks
        protected override CharacterAnimationController CreateAnimController() => gameObject.AddComponent<EnemyAnimationController>();

        EnemyAnimationController EAnim => AnimCtrl as EnemyAnimationController;
        /// <summary>Last attack played (tests): Attack / HeavyAttack / SpecialAttack.</summary>
        public string LastMove { get; private set; } = "";

        /// <summary>Melee blow: the "Attack" trigger plays PrepareAttack (telegraph) -> Attack -> AttackRecovery; the
        /// weapon hitbox is open only between the HitOn and HitOff events of the strike frames.</summary>
        IEnumerator Melee()
        {
            bool heavy = Random.value < (_enraged ? heavyChance + 0.3f : heavyChance);
            moveVel = Vector2.zero;
            SetLocomotion(0);
            float windup = (heavy ? 0.42f : 0.3f) * (_enraged ? 0.8f : 1f);
            _nextAttack = Time.time + attackCooldown * (_enraged ? 0.7f : 1f);
            string move = heavy ? "HeavyAttack" : "Attack";
            LastMove = move;
            float defReach = attackRange * 0.7f, defRadius = heavy ? 0.9f : 0.7f;
            var d = EAnim ? EAnim.Data(move, defReach, defRadius) : AttackAnimationData.Make("Enemy", move, windup, windup + 0.1f, windup + 0.45f, defReach, defRadius);
            float speed = d.SpeedFor(windup);
            Lock(d.end / speed + 0.1f);
            Sfx.PlayAt(heavy ? "heavy_swing" : "swing", transform.position, 0.7f); if (Random.value < 0.5f) Sfx.Voice(this, "attack", 0.6f);
            int hits = 0;
            var cb = new CharacterAnimationController.Callbacks
            {
                // tell: parry now (the PrepareAttack frames raise the weapon while the body glows)
                telegraph = () => { if (sr && !ally) sr.color = heavy ? new Color(1f, 0.55f, 0.45f) : new Color(1f, 0.95f, 0.75f); },
                hitOn = () =>
                {
                    ApplyLook();
                    float reach = Mathf.Max(d.reach, defReach * 0.8f), radius = Mathf.Max(d.radius, defRadius * 0.8f);
                    Hitbox.Open(d, new DamageInfo { amount = heavy ? damage + 1 : damage, knockback = heavy ? 8f : 5f, source = health.team, heavy = heavy },
                                reach, radius, null, false);
                },
                hitOff = () =>
                {
                    hits = Hitbox.Close();
                    if (hits == 0) Sfx.PlayAt("wpn_whiff", transform.position, 0.35f);
                    if (heavy && d.shake > 0 && hits > 0) CameraFollow.Shake(d.shake, 0.08f);
                },
            };
            yield return AnimCtrl.RunAttack(d, speed, cb);
            ApplyLook();
            if (ai == AIProfile.Skirmisher) _retreatUntil = Time.time + 0.9f;
            if (ai == AIProfile.Wraith && hits > 0) StartCoroutine(Fade(1.2f));
            action = null;
        }

        IEnumerator Ranged(Actor p)
        {
            moveVel = Vector2.zero;
            SetLocomotion(0);
            _nextRanged = Time.time + rangedCooldown * (_enraged ? 0.6f : 1f);
            LastMove = "SpecialAttack";
            var d = EAnim ? EAnim.Data("SpecialAttack", attackRange * 0.7f, 0.7f) : AttackAnimationData.Make("Enemy", "SpecialAttack", -1f, -1f, 0.75f, 0.5f, 0.5f, HitShape.Arc, 0.45f);
            float speed = d.SpeedFor(0.45f);
            Lock(d.end / speed + 0.05f);
            bool fired = false;
            // the bolt / fireball / spit leaves on the Projectile frame of the animation
            var cb = new CharacterAnimationController.Callbacks { projectile = () => { fired = true; FireRanged(p); } };
            yield return AnimCtrl.RunAttack(d, speed, cb);
            if (!fired) FireRanged(p);
            action = null;
        }

        void FireRanged(Actor p)
        {
            if (p == null || health.IsDead) return;
            Vector2 dir = (p.Body - Body).normalized;
            bool bolt = typeId == "ImpCrossbow";                     // crossbow imps shoot bolts, not fire
            var prefab = bolt ? GameAssets.I.arrowPrefab : kind == EnemyKind.Demon ? GameAssets.I.fireballPrefab : GameAssets.I.spitPrefab;
            Sfx.PlayAt(bolt ? "crossbow_shot" : kind == EnemyKind.Demon ? "fireball" : "spit", transform.position);
            int shots = _enraged || rank == EnemyRank.Champion ? 3 : (typeId == "DemonAsh" ? 2 : 1);
            for (int i = 0; i < shots; i++)
            {
                float ang = (i - (shots - 1) / 2f) * 18f;
                Vector2 d = Quaternion.Euler(0, 0, ang) * dir;
                var pr = Projectile.Fire(prefab, Body + d * 0.5f * Scale, d, kind == EnemyKind.Demon ? 6f : 7f, rangedDamage, health.team, transform);
                if (pr && (ally || typeId == "Summoner")) pr.GetComponentInChildren<SpriteRenderer>().color = new Color(0.8f, 0.5f, 1f);
            }
        }

        IEnumerator Blink(Actor p)
        {
            _nextSpecial = Time.time + Random.Range(4.5f, 7f);
            Lock(0.6f); moveVel = Vector2.zero;
            Trigger("CastSpell");
            Fx.Spawn(FxKind.Poof, Body);
            Sfx.PlayAt("blink", transform.position, 0.8f);
            yield return new WaitForSeconds(0.2f);
            for (int i = 0; i < 8 && p != null; i++)
            {
                Vector2 t = p.Body + Random.insideUnitCircle.normalized * Random.Range(2.4f, 3.6f);
                if (Physics2D.OverlapCircle(t, 0.35f, ~0) is Collider2D c && !c.isTrigger) continue;
                rb.position = t - Vector2.up * bodyHeight * Scale; transform.position = rb.position;
                break;
            }
            Fx.Spawn(FxKind.Summon, transform.position);
            _nextRanged = Mathf.Min(_nextRanged, Time.time + 0.35f);
            yield return new WaitForSeconds(0.2f);
            action = null;
        }

        IEnumerator Charge(Actor p)
        {
            _nextSpecial = Time.time + Random.Range(4f, 6f);
            moveVel = Vector2.zero; SetLocomotion(0);
            Vector2 dir = ((Vector2)p.Body - Body).normalized;
            Face(dir);
            Lock(1.4f);
            Trigger("HeavyAttack");
            Sfx.Voice(this, "alert", 0.9f);
            for (float t = 0; t < 0.5f; t += Time.deltaTime)                      // wind-up tremble
            {
                if (sr) sr.transform.localPosition = new Vector3(Mathf.Sin(t * 80f) * 0.04f, 0, 0);
                yield return null;
            }
            if (sr) sr.transform.localPosition = Vector3.zero;
            bool hit = false; float stuck = 0; Vector2 last = rb.position;
            for (float t = 0; t < 0.45f; t += Time.deltaTime)
            {
                moveVel = dir * 11f;
                SetLocomotion(1f);
                if (!hit && p != null && Vector2.Distance(p.Body, Body) < 0.8f * Scale)
                {
                    hit = p.health.Damage(new DamageInfo { amount = damage + 2, knockback = 11f, direction = dir, source = health.team, heavy = true, attacker = transform });
                    if (hit) CameraFollow.Shake(0.2f, 0.12f);
                }
                if ((rb.position - last).sqrMagnitude < 0.0009f) stuck += Time.deltaTime; else stuck = 0;
                last = rb.position;
                if (stuck > 0.08f) { Fx.Spawn(FxKind.Dust, transform.position, 6); CameraFollow.Shake(0.15f, 0.08f); Lock(0.9f); break; }   // hit a wall: dazed
                yield return null;
            }
            moveVel = Vector2.zero; SetLocomotion(0);
            _nextAttack = Time.time + attackCooldown;
            action = null;
        }

        IEnumerator Lunge(Actor p)
        {
            Hide(false);
            Trigger("Attack");
            Sfx.PlayAt("spit", transform.position);
            Fx.Spawn(FxKind.Splash, transform.position);
            Vector2 dir = ((Vector2)p.Body - Body).normalized;
            Face(dir);
            Lock(0.8f);
            _wasChasing = true;
            bool hit = false;
            for (float t = 0; t < 0.28f; t += Time.deltaTime)
            {
                moveVel = dir * 8.5f;
                if (!hit && p != null && Vector2.Distance(p.Body, Body) < 0.8f)
                    hit = p.health.Damage(new DamageInfo { amount = damage + 1, knockback = 6f, direction = dir, source = health.team, attacker = transform });
                yield return null;
            }
            moveVel = Vector2.zero;
            _nextAttack = Time.time + attackCooldown;
            action = null;
        }

        IEnumerator Sidestep(Actor p)
        {
            _nextSpecial = Time.time + Random.Range(2.2f, 3.5f);
            Vector2 away = ((Vector2)Body - p.Body).normalized;
            Vector2 dir = (Vector2.Perpendicular(away) * _sideSign + away * 0.6f).normalized;
            Lock(0.5f);
            Trigger("Roll");
            health.SetInvulnerable(true);
            for (float t = 0; t < 0.3f; t += Time.deltaTime) { moveVel = dir * 6.5f; yield return null; }
            health.SetInvulnerable(false);
            moveVel = Vector2.zero;
            _nextAttack = Time.time;                    // counter-attack right away
            action = null;
        }

        IEnumerator Fade(float seconds)
        {
            health.SetInvulnerable(true);
            if (_col) _col.enabled = false;
            for (float t = 0; t < seconds; t += Time.deltaTime)
            {
                if (sr) { var c = sr.color; c.a = Mathf.Lerp(0.72f, 0.08f, Mathf.PingPong(t * 2f / seconds, 1f) * 2f); sr.color = c; }
                yield return null;
            }
            if (_col) _col.enabled = true;
            health.SetInvulnerable(false);
            ApplyLook();
        }

        void Hide(bool on)
        {
            _hidden = on; _hideAt = 0;
            ApplyLook();
        }

        // ------------------------------------------------------------ damage
        DamageInfo Filter(DamageInfo d)
        {
            if (shielded) { _immuneHit = true; d.amount = 0; return d; }
            _immuneHit = false;
            // the fallen knight raises its shield against frontal hits it sees coming
            if (ai == AIProfile.Duelist && !Locked && Vector2.Dot(d.direction, facing) < -0.3f && Random.value < (rank == EnemyRank.Normal ? 0.3f : 0.45f))
                d.amount = 0;
            if (knockbackResist > 0) d.knockback *= 1f - knockbackResist;
            if (d.element == Element.Holy && kind == EnemyKind.Demon) d.amount = Mathf.CeilToInt(d.amount * 1.5f);
            return d;
        }

        bool _immuneHit;

        void OnAvoided(DamageInfo d)
        {
            if (_immuneHit) { Sfx.Play("block", 0.6f); UIRoot.Popup(Body + Vector2.up * 0.7f * Scale, "INMUNE", new Color(0.8f, 0.55f, 1f)); return; }
            Trigger("BlockHit");
            Sfx.PlayAt("block", transform.position);
            UIRoot.Popup(Body + Vector2.up * 0.5f, "BLOQUEO", UIRoot.Cream);
            _nextAttack = Time.time + 0.15f;
        }

        protected override void OnDamaged(DamageInfo d)
        {
            base.OnDamaged(d);
            UIRoot.Popup(Body + Vector2.up * 0.45f * Scale, d.crit ? d.amount + "!" : d.amount.ToString(), d.crit ? UIRoot.Gold : Color.white);
            if (_hidden) Hide(false);
            if (health.IsDead) return;
            if (d.element != Element.None) ApplyElement(d.element);
            _wasChasing = true;   // getting shot from afar wakes them up
            if (Random.value < 0.6f) Sfx.Voice(this, "hurt", 0.7f);
            bool stagger = (!isBoss && rank != EnemyRank.Champion) || d.heavy;
            if (stagger && knockbackResist < 0.7f) { CancelAction(); health.SetInvulnerable(false); Lock(isBoss ? 0.15f : 0.3f); }
            if (!_fled && !ShowsBar && (ai == AIProfile.Skirmisher || ai == AIProfile.Kiter) && health.hp <= health.maxHP / 4)
            { _fled = true; _fleeUntil = Time.time + 2.5f; }
            if (ShowsBar && !_enraged && health.hp <= health.maxHP / 2)
            {
                _enraged = true;
                Sfx.Play("boss_roar");
                Fx.Spawn(FxKind.Summon, transform.position, -1, 10f);
                CameraFollow.Shake(0.4f, 0.15f);
                UIRoot.Toast("¡" + displayName + " SE ENFURECE!");
            }
        }

        protected override void OnDied()
        {
            DiedAt = Time.time;
            _stunUntil = 0;
            Sfx.PlayAt("enemy_die", transform.position); Sfx.Voice(this, "die", 0.9f);
            foreach (var c in GetComponentsInChildren<Collider2D>()) c.enabled = false;
            rb.linearVelocity = Vector2.zero;
            rb.simulated = false;
            if (ally) { Summoning.OnAllyDied(this); StartCoroutine(FadeOut()); return; }
            if (summoner == null) DropLoot();
            GameManager.EnemyKilled(this);
            if (summoner != null) summoner.GetComponent<SummonerBoss>()?.MinionDied(this);
            if (ai == AIProfile.Bomber) StartCoroutine(Explode());
            StartCoroutine(FadeOut());
        }

        // ------------------------------------------------------------ elements (weapon effects)
        Coroutine _dot;
        float _slowUntil;

        void ApplyElement(Element e)
        {
            switch (e)
            {
                case Element.Fire: if (_dot != null) StopCoroutine(_dot); _dot = StartCoroutine(Dot(3, new Color(1f, 0.55f, 0.3f), FxKind.Explosion)); break;
                case Element.Venom: if (_dot != null) StopCoroutine(_dot); _dot = StartCoroutine(Dot(4, new Color(0.6f, 1f, 0.4f), FxKind.Splash)); break;
                case Element.Frost: _slowUntil = Time.time + 2f; StartCoroutine(Tint(new Color(0.6f, 0.85f, 1f), 2f)); break;
            }
        }

        IEnumerator Dot(int ticks, Color c, FxKind fx)
        {
            for (int i = 0; i < ticks && !health.IsDead; i++)
            {
                yield return new WaitForSeconds(1f);
                if (health.IsDead) break;
                if (sr) sr.color = c;
                health.hp = Mathf.Max(1, health.hp - 1);           // damage over time never steals the kill
                UIRoot.Popup(Body + Vector2.up * 0.45f, "1", c);
                yield return new WaitForSeconds(0.12f);
                ApplyLook();
            }
            _dot = null;
        }

        IEnumerator Tint(Color c, float seconds)
        {
            if (sr) sr.color = c;
            yield return new WaitForSeconds(seconds);
            ApplyLook();
        }

        IEnumerator Explode()
        {
            yield return new WaitForSeconds(0.45f);
            Fx.Spawn(FxKind.Explosion, Body);
            Sfx.Play("fireball");
            CameraFollow.Shake(0.2f, 0.1f);
            Combat.Hit(Body, 1.5f * Scale, new DamageInfo { amount = Mathf.Max(2, damage + 1), knockback = 9f, source = health.team, heavy = true }, transform);
        }

        void DropLoot()
        {
            var a = GameAssets.I;
            for (int i = 0; i < coins; i++) Pickup.Drop(a.coinPrefab, transform.position);
            if (Random.value < potionChance) Pickup.DropMat(Random.value < 0.25f ? "venda" : "hierba", transform.position);
            foreach (var (id, chance) in CraftDB.Drops(typeId, kind))
                if (Random.value < chance * (rank == EnemyRank.Normal ? 1f : 1.6f)) Pickup.DropMat(id, transform.position, rank == EnemyRank.Champion ? 2 : 1);
            float ac = arrowChance + (GameManager.State.classId == "ranger" ? 0.3f : 0f);
            if (Random.value < ac) Pickup.Drop(a.arrowsPickupPrefab, transform.position);
            // equipment: rare from normal enemies, likely from elites, always from champions and bosses
            var s = GameManager.State;
            float itemChance = isBoss ? 1f : rank == EnemyRank.Champion ? 1f : rank == EnemyRank.Elite ? 0.35f : 0.04f;
            if (Random.value < itemChance)
            {
                var floor = isBoss ? Rarity.Epic : rank == EnemyRank.Champion ? Rarity.Rare : Rarity.Common;
                var item = ItemDB.Roll(ItemDB.RollRarity(s.Threat, floor), isBoss ? Rarity.Legendary : rank == EnemyRank.Normal ? Rarity.Epic : Rarity.Legendary);
                if (item != null) Pickup.DropItem(item, transform.position);
            }
        }

        IEnumerator FadeOut()
        {
            // with the Summoner's curse the body lingers a few seconds so it can be raised (V)
            yield return new WaitForSeconds(ShowsBar ? 2.5f : !ally && summoner == null && Summoning.Cursed ? Summoning.CorpseSeconds : 1.1f);
            if (this == null) yield break;
            Fx.Spawn(FxKind.Poof, Body);
            if (ShowsBar) UIRoot.HideBoss();
            if (isBoss || spawned || ally)
            {
                if (ShowsBar) { Fx.Spawn(FxKind.Explosion, Body); CameraFollow.Shake(0.5f, 0.2f); }
                Destroy(gameObject, 0.1f); yield break;
            }
            gameObject.SetActive(false);
            GameManager.ScheduleRespawn(this);
        }

        /// <summary>A night creature caught by the sunrise: burns away without loot.</summary>
        public void Burn()
        {
            if (health.IsDead) return;
            Fx.Spawn(FxKind.Poof, Body);
            Fx.Spawn(FxKind.Sparkle, Body);
            if (_bossBarShown) UIRoot.HideBoss();
            Destroy(gameObject);
        }

        /// <summary>Back to life at home (called by GameManager after the respawn delay).</summary>
        public void Respawn()
        {
            transform.position = _home;
            gameObject.SetActive(true);
            foreach (var r in GetComponentsInChildren<SpriteRenderer>(true)) r.enabled = true;
            foreach (var c in GetComponentsInChildren<Collider2D>()) c.enabled = true;
            if (ai == AIProfile.Wraith && _col) _col.isTrigger = true;
            rb.simulated = true;
            health.Init(maxHP);
            if (anim) { anim.enabled = true; anim.SetBool("IsDead", false); anim.Rebind(); }
            _enraged = false; _wasChasing = false; _asleep = false; _fled = false; DiedAt = -1f; _stunUntil = 0;
            if (ai == AIProfile.Ambusher) Hide(true); else ApplyLook();
            Face(Vector2.down);
            GameManager.RegisterEnemy(this);
        }

        // ------------------------------------------------------------ parry stun
        /// <summary>The player parried this enemy's blow: it reels, open to a critical riposte.</summary>
        public void Parried(PlayerController by)
        {
            if (health.IsDead) return;
            float secs = isBoss ? 1.3f : rank == EnemyRank.Champion ? 1.7f : 2.4f;
            Stun(secs);
            knockVel = ((Vector2)transform.position - (Vector2)by.transform.position).normalized * 3f;
        }

        public void Stun(float seconds)
        {
            CancelAction();
            health.SetInvulnerable(false);
            moveVel = Vector2.zero;
            _stunUntil = Time.time + seconds;
            Lock(seconds);
            Trigger("Knockback");
            UIRoot.Popup(Body + Vector2.up * 0.6f * Scale, "ATURDIDO", UIRoot.Gold);
            if (_stunFx != null) StopCoroutine(_stunFx);
            _stunFx = StartCoroutine(StunFx());
        }

        public void EndStun()
        {
            _stunUntil = 0;
            lockUntil = Time.time + 0.35f;
        }

        IEnumerator StunFx()
        {
            float next = 0;
            while (Stunned)
            {
                if (sr) sr.color = Color.Lerp(Color.white, new Color(1f, 0.9f, 0.4f), 0.5f + 0.5f * Mathf.Sin(Time.time * 18f));
                if (Time.time > next) { next = Time.time + 0.35f; Fx.Spawn(FxKind.Sparkle, Body + Vector2.up * (0.55f * Scale) + Random.insideUnitCircle * 0.2f, 110); }
                yield return null;
            }
            ApplyLook();
            _stunFx = null;
        }

        // ------------------------------------------------------------ targets: the player, or the player's raised allies
        Actor ChooseTarget(PlayerController p)
        {
            Actor best = null; float bd = 999f;
            if (p != null && !p.health.IsDead && Interior.Current == null) { best = p; bd = Vector2.Distance(Body, p.Body); }
            foreach (var e in Active)
            {
                if (e == null || !e.ally || e.health.IsDead) continue;
                float d = Vector2.Distance(Body, e.Body) * 1.25f;          // prefers the player at equal distance
                if (d < bd && d < aggroRange * 1.5f) { bd = d; best = e; }
            }
            return best;
        }

        // ------------------------------------------------------------ ally brain (the Summoner's curse)
        void AllyThink(PlayerController p)
        {
            if (p == null || p.health.IsDead) { moveVel = Vector2.zero; SetLocomotion(0); return; }
            Vector2 anchor = allyTask == Summoning.Guard ? guardPoint : (Vector2)p.transform.position;
            float radius = allyTask == Summoning.Attack ? 9f : allyTask == Summoning.Guard ? 5f : 6f;
            EnemyController foe = null; float bd = radius;
            foreach (var e in Active)
            {
                if (e == null || e == this || e.ally || e.health.IsDead || e._asleep || e.Hidden || !e.isActiveAndEnabled) continue;
                float d = Vector2.Distance(e.Body, anchor);
                if (d < bd) { bd = d; foe = e; }
            }
            if (foe != null && (allyTask != Summoning.Guard || Vector2.Distance(foe.Body, guardPoint) < radius))
            {
                Vector2 to = foe.Body - Body;
                float dist = to.magnitude;
                Face(to);
                if (ranged && dist >= rangedMin && dist <= rangedMax && Time.time >= _nextRanged) { Run(Ranged(foe)); return; }
                if (dist <= attackRange * Scale && Time.time >= _nextAttack) { Run(Melee()); return; }
                Move(to.normalized, chaseSpeed);
                return;
            }
            Vector2 back = anchor - (Vector2)transform.position;
            float far = back.magnitude;
            if (far > 15f && allyTask != Summoning.Guard) { rb.position = anchor + Random.insideUnitCircle.normalized * 1.2f; Fx.Spawn(FxKind.Summon, rb.position); return; }
            if (far > (allyTask == Summoning.Guard ? 0.4f : 1.8f)) { Face(back); Move(back.normalized, far > 4f ? chaseSpeed * 1.2f : walkSpeed); }
            else { moveVel = Vector2.zero; SetLocomotion(0); if (allyTask != Summoning.Guard) Face(p.Body - Body); }
        }

        /// <summary>The body was raised by the player: hide it (the resident still respawns later as usual).</summary>
        public void ConsumeCorpse()
        {
            DiedAt = -1f;
            foreach (var r in GetComponentsInChildren<SpriteRenderer>()) r.enabled = false;
            Fx.Spawn(FxKind.Summon, transform.position, -1, 12f);
        }

        /// <summary>Turns this (freshly spawned) enemy into one of the player's raised allies.</summary>
        public void MakeAlly(string task)
        {
            ally = true; spawned = true; allyTask = task;
            health.team = Team.Player;
            displayName = "ALIADO: " + displayName;
            coins = 0; potionChance = 0; arrowChance = 0; xpReward = 0;
            if (ai == AIProfile.Ambusher) Hide(false);
            if (ai == AIProfile.Wraith && _col) _col.isTrigger = false;
            ApplyLook();
        }

        // ------------------------------------------------------------ boss patterns (BossBrain)
        /// <summary>Stops the normal AI for a while so a scripted boss move can play.</summary>
        public void Hold(float seconds) { CancelAction(); moveVel = Vector2.zero; SetLocomotion(0); Lock(seconds); }
        public void PlayAnim(string trigger) => Trigger(trigger);

        void OnDrawGizmosSelected()
        {
            Gizmos.color = Color.yellow; Gizmos.DrawWireSphere(transform.position, aggroRange);
            Gizmos.color = Color.red; Gizmos.DrawWireSphere(transform.position, attackRange);
        }
    }
}
