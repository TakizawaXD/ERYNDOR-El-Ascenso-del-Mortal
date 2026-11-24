using System.Collections;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Shared movement / facing / animator plumbing for the player and the enemies.</summary>
    [RequireComponent(typeof(Rigidbody2D), typeof(Health))]
    public abstract class Actor : MonoBehaviour
    {
        public float walkSpeed = 3f;
        public float runSpeed = 4.8f;
        [Tooltip("height of the body centre above the feet (world units) - attacks are aimed from here")]
        public float bodyHeight = 0.6f;

        [HideInInspector] public Vector2 facing = Vector2.down;
        public Health health { get; private set; }
        protected Rigidbody2D rb;
        protected Animator anim;
        protected SpriteRenderer sr;
        protected Vector2 moveVel;
        protected Vector2 knockVel;
        protected float lockUntil;
        protected Coroutine action;
        /// <summary>Animation side of combat: phases, Animation Events, attack watchdog (Combat/CharacterAnimationController).</summary>
        public CharacterAnimationController AnimCtrl { get; private set; }
        /// <summary>The weapon hitbox, open only between the HitOn and HitOff events of an attack.</summary>
        public WeaponHitboxController Hitbox { get; private set; }

        public bool Locked => Time.time < lockUntil;
        public float Scale => transform.localScale.y;

        static readonly int P_MoveX = Animator.StringToHash("MoveX");
        static readonly int P_MoveY = Animator.StringToHash("MoveY");
        static readonly int P_Speed = Animator.StringToHash("Speed");
        static readonly int P_Moving = Animator.StringToHash("IsMoving");
        static readonly int P_Dead = Animator.StringToHash("IsDead");

        protected virtual void Awake()
        {
            rb = GetComponent<Rigidbody2D>();
            rb.gravityScale = 0;
            rb.freezeRotation = true;
            rb.interpolation = RigidbodyInterpolation2D.Interpolate;
            anim = GetComponentInChildren<Animator>();
            sr = GetComponentInChildren<SpriteRenderer>();
            health = GetComponent<Health>();
            AnimCtrl = GetComponent<CharacterAnimationController>();
            if (AnimCtrl == null) AnimCtrl = CreateAnimController();
            AnimCtrl.Bind();
            Hitbox = GetComponent<WeaponHitboxController>();
            if (Hitbox == null) Hitbox = gameObject.AddComponent<WeaponHitboxController>();
            health.Damaged += OnDamaged;
            health.Died += OnDiedInternal;
        }

        /// <summary>Which animation controller this actor gets when its prefab has none (player and enemies override).</summary>
        protected virtual CharacterAnimationController CreateAnimController() => gameObject.AddComponent<CharacterAnimationController>();

        /// <summary>Stops an attack in progress: hitbox closed, phase cleared, Animator back to normal speed.</summary>
        protected virtual void InterruptAttack()
        {
            if (Hitbox) Hitbox.Close();
            if (AnimCtrl) AnimCtrl.Interrupt();
        }

        protected void Lock(float seconds) { lockUntil = Mathf.Max(lockUntil, Time.time + seconds); }

        /// <summary>Keeps the actor still for a moment (e.g. kneeling to stroke a cat).</summary>
        public void HoldStill(float seconds) { moveVel = Vector2.zero; Lock(seconds); }

        public void Face(Vector2 dir)
        {
            if (dir.sqrMagnitude > 0.01f) facing = Combat.Snap4(dir);
            if (anim) { anim.SetFloat(P_MoveX, facing.x); anim.SetFloat(P_MoveY, facing.y); }
        }

        protected void SetLocomotion(float speed01)
        {
            if (!anim) return;
            bool moving = speed01 > 0.01f;
            anim.SetBool(P_Moving, moving);
            anim.SetFloat(P_Speed, moving ? speed01 : 0f);
        }

        protected void Trigger(string name) { if (anim) anim.SetTrigger(name); }

        public Vector2 Body => (Vector2)transform.position + Vector2.up * bodyHeight * Scale;
        public Vector2 AttackPoint(float reach) => Body + facing * reach * Scale;

        protected virtual void FixedUpdate()
        {
            if (!rb.simulated) return;
            rb.linearVelocity = moveVel + knockVel;
            knockVel = Vector2.MoveTowards(knockVel, Vector2.zero, 35f * Time.fixedDeltaTime);
        }

        protected virtual void OnDamaged(DamageInfo d)
        {
            knockVel = d.direction * d.knockback;
            if (health.IsDead) return;
            Trigger("Hurt");
        }

        void OnDiedInternal()
        {
            if (action != null) StopCoroutine(action);
            action = null;
            InterruptAttack();
            moveVel = Vector2.zero;
            if (anim) anim.SetBool(P_Dead, true);
            OnDied();
        }

        protected abstract void OnDied();

        protected void Run(IEnumerator routine)
        {
            if (action != null) { StopCoroutine(action); InterruptAttack(); }
            action = StartCoroutine(routine);
        }

        protected void CancelAction()
        {
            if (action != null) StopCoroutine(action);
            action = null;
            InterruptAttack();
        }

        protected IEnumerator Blink(float seconds)
        {
            float end = Time.time + seconds;
            while (Time.time < end && sr)
            {
                sr.enabled = !sr.enabled;
                yield return new WaitForSeconds(0.06f);
            }
            if (sr) sr.enabled = true;
        }
    }
}
