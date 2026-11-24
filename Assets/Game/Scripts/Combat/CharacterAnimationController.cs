using System;
using System.Collections;
using UnityEngine;

namespace WoodsGame
{
    public enum AttackPhase { None, Anticipation, Active, Recovery }

    /// <summary>Character side of the animation system: owns the Animator of the "Sprite" child, receives its Animation
    /// Events through the AnimationEventHandler and turns them into attack phases (anticipation -> active window ->
    /// recovery). It also runs an attack with a watchdog: every phase callback is guaranteed to happen exactly once,
    /// on the animation frame when the events arrive, or at the time written in the AttackAnimationData if they do not
    /// (Animator culled, a different controller, the clip interrupted) - so nobody freezes waiting for an event.</summary>
    public class CharacterAnimationController : MonoBehaviour
    {
        public Animator Animator { get; private set; }
        public AnimationEventHandler Events { get; private set; }
        public AttackPhase Phase { get; private set; }
        public event Action<string> OnEvent;
        /// <summary>The data of the attack being played (null when idle).</summary>
        public AttackAnimationData Current { get; private set; }
        public int AttacksStarted { get; private set; }
        public int WatchdogFired { get; private set; }

        bool _evHitOn, _evHitOff, _evProj, _evEnd, _evTele, _evCombo;

        protected virtual void Awake() { Bind(); }

        public void Bind()
        {
            if (Animator != null && Events != null) return;
            Animator = GetComponentInChildren<Animator>(true);
            if (Animator == null) return;
            Events = AnimationEventHandler.On(Animator.gameObject);
            Events.Fired -= Handle;
            Events.Fired += Handle;
        }

        void OnDestroy() { if (Events != null) Events.Fired -= Handle; }

        protected virtual void Handle(string e)
        {
            switch (e)
            {
                case "Telegraph": case "Anticipation": _evTele = true; if (Phase == AttackPhase.None) Phase = AttackPhase.Anticipation; break;
                case "HitOn": _evHitOn = true; Phase = AttackPhase.Active; break;
                case "HitOff": _evHitOff = true; Phase = AttackPhase.Recovery; break;
                case "Projectile": _evProj = true; break;
                case "ComboWindow": _evCombo = true; break;
                case "End": _evEnd = true; break;
            }
            OnEvent?.Invoke(e);
        }

        public void Play(string trigger) { if (Animator && !string.IsNullOrEmpty(trigger)) Animator.SetTrigger(trigger); }
        public void SetSpeed(float s) { if (Animator) Animator.speed = s; }
        public float Speed => Animator ? Animator.speed : 1f;

        /// <summary>Name of the clip playing with the most weight (tests and debugging).</summary>
        public string CurrentClip
        {
            get
            {
                if (!Animator || !Animator.isActiveAndEnabled || Animator.runtimeAnimatorController == null) return "";
                var info = Animator.GetCurrentAnimatorClipInfo(0);
                string best = ""; float w = -1;
                foreach (var c in info) if (c.weight > w && c.clip) { w = c.weight; best = c.clip.name; }
                return best;
            }
        }

        public struct Callbacks
        {
            public Action telegraph, hitOn, hitOff, projectile, comboWindow, end;
        }

        /// <summary>Plays an attack and calls the phase callbacks in order, each exactly once. `speed` scales the clip.
        /// While it runs, <see cref="Phase"/> reports where the attack is. Yields until the end of the clip.</summary>
        /// <summary>True when the last RunAttack left early to chain into the next combo step.</summary>
        public bool LastChained { get; private set; }

        public IEnumerator RunAttack(AttackAnimationData d, float speed, Callbacks cb, bool trigger = true, Func<bool> chainNow = null)
        {
            LastChained = false;
            Bind();
            Current = d; AttacksStarted++;
            _evHitOn = _evHitOff = _evProj = _evEnd = _evTele = _evCombo = false;
            Phase = AttackPhase.Anticipation;
            SetSpeed(speed);
            if (trigger) Play(d.trigger);
            float t0 = Time.time;
            float k = 1f / Mathf.Max(0.05f, speed);
            const float slack = 0.12f;                  // how late an event may be before the watchdog steps in
            bool tele = false, on = false, off = false, proj = false, combo = false;
            while (true)
            {
                float t = Time.time - t0;
                if (!tele && (_evTele || t >= Mathf.Max(0, d.anticipation) * k + slack)) { tele = true; cb.telegraph?.Invoke(); }
                if (d.HasHit && !on && (_evHitOn || t >= d.hitOn * k + slack))
                {
                    if (!_evHitOn) WatchdogFired++;
                    on = true; Phase = AttackPhase.Active; cb.hitOn?.Invoke();
                }
                if (d.HasProjectile && !proj && (_evProj || t >= d.projectile * k + slack))
                {
                    if (!_evProj) WatchdogFired++;
                    proj = true; cb.projectile?.Invoke();
                }
                if (d.HasHit && on && !off && (_evHitOff || t >= Mathf.Max(d.hitOff, d.hitOn + 0.02f) * k + slack))
                {
                    off = true; Phase = AttackPhase.Recovery; cb.hitOff?.Invoke();
                }
                if (!combo && (_evCombo || t >= Mathf.Max(d.comboWindow, d.hitOff) * k + slack) && (!d.HasHit || off))
                {
                    combo = true; cb.comboWindow?.Invoke();
                }
                bool allDone = (!d.HasHit || off) && (!d.HasProjectile || proj);
                if (combo && allDone && chainNow != null && chainNow()) { LastChained = true; break; }
                if (allDone && (_evEnd || t >= d.end * k + slack)) break;
                if (t > d.end * k + 1.5f) break;         // absolute safety: never wait forever
                yield return null;
            }
            if (LastChained) { Phase = AttackPhase.None; Current = null; yield break; }   // the next step sets its own speed
            if (!combo) cb.comboWindow?.Invoke();
            cb.end?.Invoke();
            Phase = AttackPhase.None;
            Current = null;
            SetSpeed(1f);
        }

        /// <summary>Stops tracking the attack (hurt, death, dodge cancel). The coroutine owner stops the coroutine.</summary>
        public void Interrupt()
        {
            Phase = AttackPhase.None; Current = null; SetSpeed(1f);
        }
    }
}
