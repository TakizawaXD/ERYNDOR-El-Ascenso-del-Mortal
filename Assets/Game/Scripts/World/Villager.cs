using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>A living townsperson (NpcDB): walks a daily routine — work, chat in the square, home to sleep (inside their house) —
    /// plays work animations (the smith hammers, merchants serve, the herbalist picks plants), looks at you, says short lines
    /// when you pass by and talks with E (Dialogue). Guards are on duty at night.</summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public class Villager : Interactable
    {
        public static readonly List<Villager> All = new List<Villager>();

        public string npcId;
        public Vector2[] work = new Vector2[0], social = new Vector2[0];
        public Vector2[] workFace = new Vector2[0], socialFace = new Vector2[0];
        public Vector2 sleepSpot, sleepFace = Vector2.down;
        public Sprite[] portrait;
        public float speed = 1.5f;

        public NpcDef Def => NpcDB.Get(npcId);
        public bool Sleeping => _activity == Act.Sleep && _arrived && !Def.nightOwl;
        public bool Talking { get; set; }
        public string Activity => _activity.ToString();
        public Vector2 Target => _target;

        enum Act { Work, Social, Sleep }
        Act _activity;
        Vector2 _target, _face = Vector2.down, _lastPos, _slide;
        bool _arrived;
        int _spot;
        float _nextSpot, _nextWork, _stuck, _slideUntil, _nextBark, _nextLook;
        Rigidbody2D _rb;
        Animator _anim;
        SpriteRenderer _sr;
        Vector2 _vel;

        static readonly int P_X = Animator.StringToHash("MoveX"), P_Y = Animator.StringToHash("MoveY"), P_Moving = Animator.StringToHash("IsMoving"),
                            P_Speed = Animator.StringToHash("Speed"), P_Sleep = Animator.StringToHash("IsSleeping"), P_Sit = Animator.StringToHash("IsSitting");

        protected override void OnEnable() { base.OnEnable(); All.Add(this); }
        protected override void OnDisable() { base.OnDisable(); All.Remove(this); }

        void Awake()
        {
            _rb = GetComponent<Rigidbody2D>();
            _rb.gravityScale = 0; _rb.freezeRotation = true; _rb.mass = 6f;
            _rb.interpolation = RigidbodyInterpolation2D.Interpolate;
            _anim = GetComponentInChildren<Animator>();
            _sr = GetComponentInChildren<SpriteRenderer>();
            _nextBark = Time.time + Random.Range(2f, 8f);
            _spot = Random.Range(0, 100);
        }

        void Start()
        {
            // appear where the routine says they are right now (no long walks after loading)
            Plan(true);
            Teleport(_target);
        }

        // ------------------------------------------------------------ schedule
        Act Scheduled()
        {
            int h = DayNight.Hour;
            var d = Def;
            if (d != null && d.nightOwl) return h >= 21 || h < 6 ? Act.Sleep : (h >= 12 && h < 13) || (h >= 19 && h < 21) ? Act.Social : Act.Work;
            if (h >= 22 || h < 6) return Act.Sleep;
            if ((h >= 6 && h < 8) || (h >= 12 && h < 13) || (h >= 19 && h < 22)) return Act.Social;
            return Act.Work;
        }

        /// <summary>Picks the activity of the hour and the spot for it.</summary>
        void Plan(bool force)
        {
            var act = Scheduled();
            if (!force && act == _activity && Time.time < _nextSpot) return;
            bool changed = act != _activity;
            _activity = act;
            if (act == Act.Sleep) { _target = sleepSpot; _face = sleepFace; }
            else
            {
                var list = act == Act.Work ? work : social; var faces = act == Act.Work ? workFace : socialFace;
                if (list == null || list.Length == 0) { list = work; faces = workFace; }
                if (list == null || list.Length == 0) { _target = sleepSpot; _face = Vector2.down; }
                else
                {
                    _spot = changed || force ? Random.Range(0, list.Length) : (_spot + 1) % list.Length;
                    _target = list[_spot];
                    _face = faces != null && _spot < faces.Length ? faces[_spot] : Vector2.zero;
                }
            }
            _arrived = false;
            _nextSpot = Time.time + Random.Range(act == Act.Work ? 25f : 18f, act == Act.Work ? 50f : 35f);
        }

        protected override void Update()
        {
            base.Update();
            if (GameManager.Paused) return;
            if (Talking) { _vel = Vector2.zero; Anim(false); LookAtPlayer(true); return; }
            Plan(false);
            if (!_arrived) Walk();
            else Stay();
            Bark();
        }

        void FixedUpdate()
        {
            if (_rb.bodyType == RigidbodyType2D.Dynamic) _rb.linearVelocity = _vel;
        }

        // ------------------------------------------------------------ walking (also through house doors)
        void Walk()
        {
            if (_anim) { _anim.SetBool(P_Sleep, false); _anim.SetBool(P_Sit, false); }
            Vector2 pos = _rb.position;
            var curRoom = Interior.At(pos); var tgtRoom = Interior.At(_target);
            Vector2 way = _target;
            if (curRoom != tgtRoom)
            {
                if (curRoom != null)
                {
                    way = curRoom.entry + Vector2.down * 0.6f;                 // the exit mat
                    if (Vector2.Distance(pos, way) < 0.45f) { Teleport(curRoom.outside); return; }
                }
                else
                {
                    way = tgtRoom.outside;                                      // the front door
                    if (Vector2.Distance(pos, way) < 0.6f) { Teleport(tgtRoom.entry); return; }
                }
            }
            Vector2 to = way - pos;
            float dist = to.magnitude;
            if (dist < 0.12f && way == _target) { _arrived = true; _vel = Vector2.zero; _nextWork = Time.time + Random.Range(0.5f, 2f); return; }
            Vector2 dir = to / Mathf.Max(0.001f, dist);
            // a player in the way: wait politely
            var p = PlayerController.Current;
            if (p != null && Vector2.Distance(p.transform.position, pos + dir * 0.6f) < 0.45f) { _vel = Vector2.zero; Anim(false); LookAtPlayer(true); return; }
            // stuck on a tree / fence: slide sideways, then give up and skip ahead when nobody is looking
            if ((pos - _lastPos).sqrMagnitude < 0.0002f) _stuck += Time.deltaTime; else _stuck = Mathf.Max(0, _stuck - Time.deltaTime * 0.5f);
            _lastPos = pos;
            if (_stuck > 0.5f && Time.time > _slideUntil) { _slide = Vector2.Perpendicular(dir) * (Random.value < 0.5f ? 1 : -1); _slideUntil = Time.time + 0.5f; }
            if (_stuck > 3f && !OnScreen()) { Teleport(way); _stuck = 0; return; }
            Vector2 move = Time.time < _slideUntil ? (dir * 0.3f + _slide).normalized : dir;
            _vel = move * speed;
            Face(move);
            Anim(true);
        }

        void Stay()
        {
            _vel = Vector2.zero;
            Anim(false);
            if (_activity == Act.Sleep && !Def.nightOwl)
            {
                if (_anim) _anim.SetBool(P_Sleep, true);
                return;
            }
            if (LookAtPlayer(false)) return;
            if (_face != Vector2.zero) Face(_face);
            // work animations
            if (_activity == Act.Work && Time.time > _nextWork && !string.IsNullOrEmpty(Def.workAnim))
            {
                _nextWork = Time.time + (Def.workAnim == "Attack" ? Random.Range(0.9f, 1.4f) : Random.Range(2.5f, 5f));
                if (_anim) _anim.SetTrigger(Def.workAnim);
                if (Def.workAnim == "Attack") Hammer();
            }
        }

        /// <summary>The smith strikes the anvil: sparks and a ring you hear when you are close.</summary>
        void Hammer()
        {
            var p = PlayerController.Current;
            Vector2 at = (Vector2)transform.position + _face * 0.75f + Vector2.up * 0.45f;
            if (OnScreen()) Fx.Spawn(FxKind.Hit, at, 60, 20f);
            if (p != null && Vector2.Distance(p.transform.position, transform.position) < 7f && Interior.At(p.transform.position) == Interior.At(transform.position))
                Sfx.PlayAt("anvil", transform.position, 0.6f);
        }

        bool LookAtPlayer(bool always)
        {
            var p = PlayerController.Current;
            if (p == null) return false;
            Vector2 to = (Vector2)p.transform.position - (Vector2)transform.position;
            if (!always && (to.sqrMagnitude > 4.5f || Time.time < _nextLook)) return false;
            Face(to);
            return true;
        }

        void Bark()
        {
            var p = PlayerController.Current;
            var d = Def;
            if (p == null || d == null || d.barks == null || d.barks.Length == 0 || Time.time < _nextBark || Sleeping) return;
            float dist = Vector2.Distance(p.transform.position, transform.position);
            if (dist > 3.5f) return;
            _nextBark = Time.time + Random.Range(25f, 45f);
            var mem = GameManager.State.Memory(d.id);
            string line = mem.talks > 0 && mem.affinity >= 3 ? "¡" + (GameManager.State.Class.shortName.ToLowerInvariant()) + "!" : d.barks[Random.Range(0, d.barks.Length)];
            UIRoot.Say(this.transform, line, 2.4f);
        }

        // ------------------------------------------------------------ helpers
        void Teleport(Vector2 at)
        {
            _rb.position = at; transform.position = at; _lastPos = at; _vel = Vector2.zero;
        }

        bool OnScreen()
        {
            var cam = Camera.main;
            if (cam == null) return false;
            var v = cam.WorldToViewportPoint(transform.position);
            return v.x > -0.1f && v.x < 1.1f && v.y > -0.1f && v.y < 1.1f;
        }

        void Face(Vector2 d)
        {
            if (d.sqrMagnitude < 0.0001f || _anim == null) return;
            var f = Combat.Snap4(d);
            _anim.SetFloat(P_X, f.x); _anim.SetFloat(P_Y, f.y);
        }

        void Anim(bool moving)
        {
            if (_anim == null) return;
            _anim.SetBool(P_Moving, moving);
            _anim.SetFloat(P_Speed, moving ? 0.5f : 0f);
        }

        public override bool CanInteract => Def != null;

        public override void Interact(PlayerController p)
        {
            if (Sleeping) { UIRoot.ShowDialog($"{Def.name} duerme profundamente... Zzz. Vuelve por la mañana."); return; }
            _nextLook = 0;
            Dialogue.Start(this);
        }

        /// <summary>Tests / debug: put the villager at its spot for the current hour at once.</summary>
        public void SnapToRoutine() { Plan(true); Teleport(_target); _arrived = true; }
    }
}
