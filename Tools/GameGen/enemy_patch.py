p = 'G:/Juegos/Assets/Game/Scripts/Actors/EnemyController.cs'
s = open(p, encoding='utf8').read()
def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b)
rep("""        public bool Enraged => _enraged;
""", """        public bool Enraged => _enraged;
        public Vector2 Home => _home;
        public const float ActiveRange = 16f;      // beyond this the enemy sleeps (open-world performance)
        bool _bossBarShown;
        float _nextCull;
        bool _asleep;
""")
rep("""        void Start()
        {
            GameManager.RegisterEnemy(this);
            if (isBoss) UIRoot.ShowBoss(this);
        }

        void Update()
        {
            if (health.IsDead || GameManager.Paused) { moveVel = Vector2.zero; return; }
            var p = PlayerController.Current;
            if (Locked) { moveVel = Vector2.zero; SetLocomotion(0); return; }
""", """        void Start()
        {
            // bosses already beaten in this save stay beaten
            if (isBoss && !string.IsNullOrEmpty(bossFlag) && GameManager.State.Has(bossFlag)) { gameObject.SetActive(false); return; }
            GameManager.RegisterEnemy(this);
        }

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
                    if (far) { moveVel = Vector2.zero; transform.position = _home; _wasChasing = false; }
                }
            }
            if (_asleep) return;
            if (isBoss && p != null)
            {
                bool near = Vector2.Distance(p.transform.position, transform.position) < aggroRange * 1.6f;
                if (near != _bossBarShown) { _bossBarShown = near; if (near) UIRoot.ShowBoss(this); else UIRoot.HideBoss(); }
            }
            if (Locked) { moveVel = Vector2.zero; SetLocomotion(0); return; }
""")
rep("""        IEnumerator Fade()
        {
            yield return new WaitForSeconds(isBoss ? 2.5f : 1.1f);
            Fx.Spawn(FxKind.Poof, Body);
            if (isBoss) { Fx.Spawn(FxKind.Explosion, Body); CameraFollow.Shake(0.5f, 0.2f); }
            Destroy(gameObject, 0.1f);
        }""", """        IEnumerator Fade()
        {
            yield return new WaitForSeconds(isBoss ? 2.5f : 1.1f);
            Fx.Spawn(FxKind.Poof, Body);
            if (isBoss) { Fx.Spawn(FxKind.Explosion, Body); CameraFollow.Shake(0.5f, 0.2f); Destroy(gameObject, 0.1f); yield break; }
            gameObject.SetActive(false);
            GameManager.ScheduleRespawn(this);
        }

        /// <summary>Back to life at home (called by GameManager after the respawn delay).</summary>
        public void Respawn()
        {
            transform.position = _home;
            gameObject.SetActive(true);
            foreach (var c in GetComponentsInChildren<Collider2D>()) c.enabled = true;
            rb.simulated = true;
            health.Init(maxHP);
            if (anim) { anim.enabled = true; anim.SetBool("IsDead", false); anim.Rebind(); }
            _enraged = false; _wasChasing = false; _asleep = false;
            Face(Vector2.down);
            GameManager.RegisterEnemy(this);
        }""")
open(p, 'w', encoding='utf8').write(s)
print('ok')
