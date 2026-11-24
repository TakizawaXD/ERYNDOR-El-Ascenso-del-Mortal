using System.Collections;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>A hero of the new roster living in a town: idles and strolls around its post (with idle / walk animations),
    /// talks with E and does its job:
    ///   Guard   attacks any enemy that comes close to its post     Healer  heals you fully (once a day)
    ///   Sage    gives a boss tip each time you talk                  Ranger  gives 8 arrows (once a day)
    ///   Patrol  walks a much wider round</summary>
    public class Adventurer : Interactable
    {
        public string heroId;
        public float wander = 2.5f;
        public float guardRange = 5f;
        public int damage = 4;

        RosterDB.Hero _hero;
        Animator _anim;
        Vector2 _home, _target;
        float _nextMove, _nextSwing;
        int _line;
        bool _busy;

        public RosterDB.Job Job => _hero != null ? _hero.job : RosterDB.Job.Guard;
        public EnemyController Target { get; private set; }

        void Start()
        {
            _hero = RosterDB.Get(heroId);
            _anim = GetComponentInChildren<Animator>();
            _home = _target = transform.position;
            if (Job == RosterDB.Job.Patrol) wander = 9f;
            promptHeight = 1.6f;
            Face(Vector2.down);
        }

        public override void Interact(PlayerController p)
        {
            if (_hero == null) return;
            Face(p.transform.position - transform.position);
            string text = _hero.lines[_line % _hero.lines.Length];
            _line++;
            var s = GameManager.State;
            string dayKey = $"hero_{heroId}_{(int)(s.TotalMinutes / (24 * 60f))}";
            switch (Job)
            {
                case RosterDB.Job.Healer:
                    if (s.Has(dayKey)) text = "Ya te he bendecido hoy. Descansa un poco.";
                    else { s.Set(dayKey); p.health.Heal(p.health.maxHP); Fx.Spawn(FxKind.Heal, p.transform.position); Sfx.Play("levelup", 0.6f); }
                    break;
                case RosterDB.Job.Ranger:
                    if (s.Has(dayKey)) text = "Por hoy no me quedan flechas de sobra.";
                    else { s.Set(dayKey); s.arrows += 8; UIRoot.Popup((Vector2)p.transform.position + Vector2.up, "+8 FLECHAS", UIRoot.Gold); }
                    break;
            }
            UIRoot.ShowDialog(_hero.name.ToUpper() + ": " + text);
        }

        protected override void Update()
        {
            base.Update();
            if (GameManager.Paused || _busy) return;
            if (Job == RosterDB.Job.Guard || Job == RosterDB.Job.Patrol) { Guard(); if (_busy) return; }
            Stroll();
        }

        void Guard()
        {
            if (Target != null && (Target.health.IsDead || Vector2.Distance(Target.transform.position, _home) > guardRange * 1.6f)) Target = null;
            if (Target == null && Time.frameCount % 15 == 0)
                foreach (var e in EnemyController.Active)
                    if (e != null && !e.health.IsDead && !e.ally && Vector2.Distance(e.transform.position, transform.position) < guardRange) { Target = e; break; }
            if (Target == null) return;
            Vector2 to = Target.Body - (Vector2)transform.position;
            Face(to);
            if (to.magnitude > 1.1f) { Move(to.normalized, 2.6f); return; }
            if (Time.time >= _nextSwing) StartCoroutine(Swing());
            else Move(Vector2.zero, 0);
        }

        IEnumerator Swing()
        {
            _busy = true; _nextSwing = Time.time + 1.1f;
            Move(Vector2.zero, 0);
            if (_anim) _anim.SetTrigger("Attack");
            yield return new WaitForSeconds(0.25f);
            if (Target != null)
                Combat.Hit(Target.Body, 0.7f, new DamageInfo { amount = damage, knockback = 5f, source = Team.Player }, transform);
            yield return new WaitForSeconds(0.25f);
            _busy = false;
        }

        void Stroll()
        {
            var p = PlayerController.Current;
            if (p != null && Vector2.Distance(p.transform.position, transform.position) < 2f)
            {
                Move(Vector2.zero, 0); Face(p.transform.position - transform.position); return;
            }
            if (Time.time >= _nextMove)
            {
                _nextMove = Time.time + Random.Range(2.5f, 6f);
                _target = Random.value < 0.4f ? (Vector2)transform.position : _home + Random.insideUnitCircle * wander;
                var wi = WorldInfo.Current;
                if (wi != null && !wi.Walkable(_target)) _target = transform.position;
            }
            Vector2 d = _target - (Vector2)transform.position;
            if (d.magnitude < 0.1f) { Move(Vector2.zero, 0); return; }
            Face(d); Move(d.normalized, Job == RosterDB.Job.Patrol ? 1.8f : 1.1f);
        }

        void Move(Vector2 dir, float speed)
        {
            transform.position += (Vector3)(dir * speed * Time.deltaTime);
            if (_anim) { _anim.SetBool("IsMoving", speed > 0.01f); _anim.SetFloat("Speed", speed > 0.01f ? 0.3f : 0f); }
        }

        void Face(Vector2 d)
        {
            if (d.sqrMagnitude < 0.0001f || _anim == null) return;
            var f = Combat.Snap4(d);
            _anim.SetFloat("MoveX", f.x); _anim.SetFloat("MoveY", f.y);
        }
    }
}
