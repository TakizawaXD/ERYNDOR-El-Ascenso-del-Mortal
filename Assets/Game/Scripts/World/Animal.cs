using System.Collections;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Farm and meadow animal (Cute Fantasy pack sheets: row 0 idle, row 1 walk, 2 frames each, facing left).
    /// Grazes and wanders around its home, turns to where it walks, startles and runs away when you sprint close or hit it,
    /// and can be hunted for crafting materials. Animals respawn when the map is loaded again.</summary>
    [RequireComponent(typeof(Rigidbody2D), typeof(Health))]
    public class Animal : MonoBehaviour
    {
        public string species = "cow";
        public Sprite[] idle, walk;
        public float walkSpeed = 0.9f, fleeSpeed = 3.2f, roam = 3f;
        public int maxHP = 4;
        public string[] drops = { "carne" };
        public int dropCount = 1;
        public string sound = "step";
        [UnityEngine.Tooltip("pets (the kitten): cannot be hurt, can be stroked with E and then follow you around")]
        public bool friendly;
        [UnityEngine.Tooltip("shy cats never let you near: they hiss and run when you come close")]
        public bool shy;
        public Sprite[] pet;                 // being stroked (sits, eyes shut)
        public Sprite heart;                 // little hearts while purring
        public bool Petting => _petting;
        bool _petting;
        float _nextHiss;
        public bool Following => Time.time < _followUntil;
        float _followUntil;

        Rigidbody2D _rb; SpriteRenderer _sr; Health _hp;
        Vector2 _home, _target, _vel;
        float _nextThink, _fleeUntil, _anim;
        bool _moving;

        void Awake()
        {
            _rb = GetComponent<Rigidbody2D>(); _rb.gravityScale = 0; _rb.freezeRotation = true;
            _rb.interpolation = RigidbodyInterpolation2D.Interpolate;
            _sr = GetComponentInChildren<SpriteRenderer>();
            _hp = GetComponent<Health>(); _hp.team = Team.Neutral; _hp.invulnerableAfterHit = 0.3f; _hp.Init(maxHP);
            _hp.Damaged += OnHit; _hp.Died += OnDied;
            if (friendly) _hp.filter = d => { d.amount = 0; return d; };      // nobody hurts the kitten
            _home = _target = transform.position;
            _anim = Random.value * 2f;
            _nextThink = Time.time + Random.Range(0.5f, 3f);
        }

        float _nextCall;

        void Update()
        {
            if (_hp.IsDead || GameManager.Paused) return;
            var p = PlayerController.Current;
            float dPlayer = p ? Vector2.Distance(p.transform.position, transform.position) : 99f;
            if (dPlayer > 18f) { _vel = Vector2.zero; return; }                       // far away: stand still, cheap
            if (dPlayer < 9f && Time.time > _nextCall)                                 // moo, oink, baa, cluck, meow now and then
            {
                if (_nextCall > 0 && !_petting) Sfx.PlayAt(Sfx.AnimalSound(species), transform.position, 0.45f);
                _nextCall = Time.time + Random.Range(species == "chicken" ? 5f : 9f, species == "chicken" ? 12f : 22f);
            }
            // a running knight (or a chicken's nerves) makes it bolt
            if (!friendly && p && dPlayer < (species == "chicken" ? 2.2f : 1.6f) && GameInput.Run && GameInput.Move.sqrMagnitude > 0.1f) Startle(p.transform.position);
            if (_petting) { _vel = Vector2.zero; return; }
            // shy cats keep their distance whatever you do
            if (shy && p && dPlayer < 2.6f && !Following)
            {
                if (Time.time >= _fleeUntil && Time.time > _nextHiss)
                {
                    _nextHiss = Time.time + 4f;
                    UIRoot.Popup((Vector2)transform.position + Vector2.up * 0.9f, "¡Fsss!", new Color(1f, 0.6f, 0.6f));
                }
                _fleeUntil = Time.time + 1.4f;
            }
            if (Following && p)
            {
                // trots after you and sits down at your feet
                Vector2 to = (Vector2)p.transform.position + new Vector2(_sideOffset, -0.4f) - (Vector2)transform.position;
                _vel = to.magnitude > 0.9f ? to.normalized * Mathf.Min(fleeSpeed, 1.2f + to.magnitude) : Vector2.zero;
                if (to.magnitude > 14f) { transform.position = (Vector2)p.transform.position + Vector2.left; _rb.position = transform.position; }
                _home = transform.position;
                Animate();
                return;
            }
            if (Time.time < _fleeUntil && p)
            {
                Vector2 away = ((Vector2)transform.position - (Vector2)p.transform.position).normalized;
                _vel = away * fleeSpeed;
            }
            else if (Time.time >= _nextThink)
            {
                _nextThink = Time.time + Random.Range(2f, 5f);
                _target = Random.value < 0.45f ? (Vector2)transform.position : _home + Random.insideUnitCircle * roam;   // graze or stroll
            }
            if (Time.time >= _fleeUntil)
            {
                Vector2 to = _target - (Vector2)transform.position;
                _vel = to.magnitude > 0.15f ? to.normalized * walkSpeed : Vector2.zero;
            }
            Animate();
        }

        float _sideOffset = 0.7f;

        void Animate()
        {
            _moving = _vel.sqrMagnitude > 0.01f;
            if (Mathf.Abs(_vel.x) > 0.05f) _sr.flipX = _vel.x > 0;                    // sheets face left
            // animation: grazing idle is slow, walking quick
            _anim += Time.deltaTime * (_moving ? (Time.time < _fleeUntil ? 10f : 5f) : 1.6f);
            var frames = _moving && walk != null && walk.Length > 0 ? walk : idle;
            if (frames != null && frames.Length > 0) _sr.sprite = frames[(int)_anim % frames.Length];
        }

        void FixedUpdate() { if (!_hp.IsDead) _rb.linearVelocity = _vel; }

        /// <summary>Stroking the kitten: you kneel, it sits and purrs with its eyes shut while hearts float up,
        /// then it follows you for a while.</summary>
        public void Pet(PlayerController p)
        {
            if (_petting || shy) return;
            StartCoroutine(PetRoutine(p));
        }

        public const float PetSeconds = 1.6f;

        IEnumerator PetRoutine(PlayerController p)
        {
            _petting = true; _vel = Vector2.zero;
            Vector2 toCat = (Vector2)transform.position - (Vector2)p.transform.position;
            p.Face(toCat);
            p.HoldStill(PetSeconds);
            _sr.flipX = p.transform.position.x > transform.position.x;           // look at the knight
            Sfx.PlayAt("cat_purr", transform.position, 0.8f);
            UIRoot.Popup((Vector2)transform.position + Vector2.up * 0.9f, "Rrr...", new Color32(0xff, 0xc8, 0x5a, 0xff));
            float t = 0, nextHeart = 0;
            while (t < PetSeconds)
            {
                var frames = pet != null && pet.Length > 0 ? pet : idle;
                _sr.sprite = frames[(int)(t * 4f) % frames.Length];
                if (t >= nextHeart) { nextHeart = t + 0.45f; Heart(); }
                t += Time.deltaTime;
                yield return null;
            }
            Sfx.PlayAt("cat_meow", transform.position, 0.7f);
            UIRoot.Popup((Vector2)transform.position + Vector2.up * 0.9f, "¡Miau!", new Color32(0xff, 0xc8, 0x5a, 0xff));
            _petting = false;
            _followUntil = Time.time + 120f;
            _sideOffset = Random.value < 0.5f ? -0.7f : 0.7f;
        }

        void Heart()
        {
            if (heart == null) { Fx.Spawn(FxKind.Sparkle, (Vector2)transform.position + Vector2.up * 0.7f); return; }
            var go = new GameObject("heart");
            go.transform.position = (Vector2)transform.position + new Vector2(Random.Range(-0.25f, 0.25f), 0.8f);
            var sr = go.AddComponent<SpriteRenderer>(); sr.sprite = heart; sr.sortingOrder = 130;
            go.AddComponent<FloatAway>();
        }

        void Startle(Vector2 from)
        {
            if (Time.time < _fleeUntil) return;
            _fleeUntil = Time.time + 1.6f;
            Sfx.PlayAt(Sfx.AnimalSound(species), transform.position, 0.6f);
        }

        void OnHit(DamageInfo d)
        {
            var p = PlayerController.Current;
            Startle(p ? (Vector2)p.transform.position : (Vector2)transform.position);
            _fleeUntil = Time.time + 2.5f;
            StartCoroutine(Flash());
        }

        IEnumerator Flash()
        {
            _sr.color = new Color(1f, 0.6f, 0.6f);
            yield return new WaitForSeconds(0.12f);
            if (_sr) _sr.color = Color.white;
        }

        void OnDied()
        {
            _vel = Vector2.zero; _rb.linearVelocity = Vector2.zero; _rb.simulated = false;
            foreach (var c in GetComponentsInChildren<Collider2D>()) c.enabled = false;
            for (int i = 0; i < dropCount; i++)
                foreach (var id in drops) Pickup.DropMat(id, transform.position);
            Fx.Spawn(FxKind.Poof, (Vector2)transform.position + Vector2.up * 0.4f);
            Destroy(gameObject, 0.05f);
        }
    }
}
