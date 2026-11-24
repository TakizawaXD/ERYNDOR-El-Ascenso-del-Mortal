using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Phases and signature attacks on top of EnemyController (which keeps doing melee, chasing and its own ranged shot).
    /// Phase 2 at 2/3 of the life, phase 3 at 1/3: each phase adds moves and shortens the pause between them.
    ///   warlord   Gorgrak: ground slams (shockwaves), calls desert raiders, throws axes in a fan
    ///   mother    Madre de Sangre: spit rings, spawns toxic slimes, spiral of spit
    ///   demon     Señor Demonio: fireball fans, meteors on your position, fire spiral, ash imps
    ///   colossus  Coloso de Escarcha: frost shockwaves, falling icicles, ice shard bursts
    ///   summoner  El Invocador: violet orb fans, soul rings and a spiral (his minions come from SummonerBoss)</summary>
    [RequireComponent(typeof(EnemyController))]
    public class BossBrain : MonoBehaviour
    {
        public string pattern = "warlord";
        public Color fxColor = Color.white;
        public string[] minions = { };
        public int maxMinions = 4;
        public float cooldown = 4.2f;

        public int Phase { get; private set; } = 1;
        public int MovesDone { get; private set; }
        public string LastMove { get; private set; } = "";
        public bool Busy => _busy;
        public IReadOnlyList<EnemyController> Spawned => _spawned;

        EnemyController _e;
        float _next;
        bool _busy;
        int _turn;
        readonly List<EnemyController> _spawned = new List<EnemyController>();

        void Awake() { _e = GetComponent<EnemyController>(); }

        void Update()
        {
            if (_e.health.IsDead) { Crumble(); return; }
            if (GameManager.Paused || _e.Asleep || !_e.Engaged || _busy || _e.ally) return;
            var p = PlayerController.Current;
            if (p == null || p.health.IsDead) return;
            float hp = _e.health.hp / (float)_e.health.maxHP;
            int want = hp <= 0.34f ? 3 : hp <= 0.67f ? 2 : 1;
            if (want > Phase) { StartCoroutine(Run(PhaseShift(want))); return; }
            if (_next == 0) _next = Time.time + 2f;
            if (Time.time < _next) return;
            if (Vector2.Distance(p.transform.position, transform.position) > _e.aggroRange * 2.2f) return;
            StartCoroutine(Run(NextMove(p)));
        }

        /// <summary>Forces the next special move now (tests and debugging).</summary>
        public void ForceMove() { _next = Time.time; }

        IEnumerator Run(IEnumerator r)
        {
            _busy = true;
            yield return r;
            _busy = false;
            _next = Time.time + cooldown * (Phase == 3 ? 0.55f : Phase == 2 ? 0.75f : 1f) * Random.Range(0.85f, 1.15f);
        }

        IEnumerator PhaseShift(int to)
        {
            Phase = to;
            _e.Hold(1.6f);
            _e.PlayAnim("CastSpell");
            Sfx.Play("boss_phase");
            CameraFollow.Shake(0.5f, 0.2f);
            Fx.Spawn(FxKind.Summon, transform.position, -1, 10f);
            UIRoot.Toast(to == 2 ? "«¡AÚN NO HE EMPEZADO!»" : "«¡ARDERÁS CONMIGO!»", 2.2f);
            BossHud.Phase(to);
            var arena = GetComponentInParent<BossArena>() ?? BossArena.For(_e);
            if (arena) arena.Flare(to);
            yield return new WaitForSeconds(0.8f);
            yield return Wave(1);                     // every phase change knocks you back
        }

        // ------------------------------------------------------------ move tables
        IEnumerator NextMove(PlayerController p)
        {
            _turn++;
            var moves = new List<System.Func<IEnumerator>>();
            switch (pattern)
            {
                case "warlord":
                    moves.Add(() => Wave(Phase == 3 ? 2 : 1));
                    if (Phase >= 2) { moves.Add(() => Summon(2)); moves.Add(() => Fan(p, GameAssets.I.arrowPrefab, Phase == 3 ? 7 : 5, 50f, 8f)); }
                    if (Phase >= 3) moves.Add(() => Meteors(p, 4));
                    break;
                case "mother":
                    moves.Add(() => Burst(GameAssets.I.spitPrefab, Phase == 1 ? 8 : 12, 6.5f));
                    if (Phase >= 2) { moves.Add(() => Summon(3)); moves.Add(() => Wave(1)); }
                    if (Phase >= 3) moves.Add(() => Spiral(GameAssets.I.spitPrefab, 3, 2.4f));
                    break;
                case "demon":
                    moves.Add(() => Fan(p, GameAssets.I.fireballPrefab, Phase == 1 ? 5 : 7, 60f, 7f));
                    moves.Add(() => Meteors(p, Phase == 1 ? 3 : 5));
                    if (Phase >= 2) moves.Add(() => Spiral(GameAssets.I.fireballPrefab, 4, 2.6f));
                    if (Phase >= 3) { moves.Add(() => Summon(2)); moves.Add(() => Wave(2)); }
                    break;
                case "colossus":
                    moves.Add(() => Wave(Phase == 1 ? 1 : 2));
                    if (Phase >= 2) moves.Add(() => Meteors(p, 5));
                    if (Phase >= 3) { moves.Add(() => Burst(GameAssets.I.arrowPrefab, 14, 7.5f)); moves.Add(() => Summon(2)); }
                    break;
                default:   // summoner
                    moves.Add(() => Fan(p, GameAssets.I.fireballPrefab, 3, 36f, 6.5f));
                    if (Phase >= 2) { moves.Add(() => Burst(GameAssets.I.fireballPrefab, 10, 5.5f)); moves.Add(() => Wave(1)); }
                    if (Phase >= 3) moves.Add(() => Spiral(GameAssets.I.fireballPrefab, 3, 2.2f));
                    break;
            }
            // cycle through the table so every move is seen, with a little randomness
            var m = moves[(_turn + (Random.value < 0.3f ? 1 : 0)) % moves.Count];
            MovesDone++;
            yield return m();
        }

        int Dmg(int baseDmg) => baseDmg + (Phase - 1);

        // ------------------------------------------------------------ moves
        IEnumerator Wave(int count)
        {
            LastMove = "wave";
            _e.Hold(0.8f + count * 0.5f);
            for (int i = 0; i < count; i++)
            {
                _e.PlayAnim("HeavyAttack");
                yield return new WaitForSeconds(0.45f);
                Sfx.Play("quake"); Sfx.Play("wave", 0.7f);
                CameraFollow.Shake(0.35f, 0.15f);
                Fx.Spawn(FxKind.Dust, transform.position);
                BossWave.Spawn(transform.position, fxColor, 5.5f + Phase * 0.5f, 9f, Dmg(2), transform);
                yield return new WaitForSeconds(0.5f);
            }
        }

        IEnumerator Burst(GameObject prefab, int n, float speed)
        {
            LastMove = "burst";
            _e.Hold(1.0f);
            _e.PlayAnim("SpecialAttack");
            yield return new WaitForSeconds(0.45f);
            float off = Random.value * 360f;
            for (int i = 0; i < n; i++) Shoot(prefab, Quaternion.Euler(0, 0, off + i * 360f / n) * Vector2.right, speed);
            Sfx.Play(pattern == "colossus" ? "ice" : "fireball");
            yield return new WaitForSeconds(0.3f);
        }

        IEnumerator Fan(PlayerController p, GameObject prefab, int n, float spread, float speed)
        {
            LastMove = "fan";
            _e.Hold(0.9f);
            _e.Face(p.Body - _e.Body);
            _e.PlayAnim("SpecialAttack");
            yield return new WaitForSeconds(0.45f);
            if (p == null) yield break;
            Vector2 aim = (p.Body - _e.Body).normalized;
            for (int i = 0; i < n; i++)
            {
                float a = n == 1 ? 0 : -spread / 2 + spread * i / (n - 1);
                Shoot(prefab, Quaternion.Euler(0, 0, a) * aim, speed);
            }
            Sfx.Play(pattern == "warlord" ? "heavy_swing" : "fireball");
            yield return new WaitForSeconds(0.25f);
        }

        IEnumerator Spiral(GameObject prefab, int arms, float seconds)
        {
            LastMove = "spiral";
            _e.Hold(seconds + 0.4f);
            _e.PlayAnim("CastSpell");
            yield return new WaitForSeconds(0.35f);
            float t = 0, ang = Random.value * 360f;
            while (t < seconds && !_e.health.IsDead)
            {
                for (int k = 0; k < arms; k++) Shoot(prefab, Quaternion.Euler(0, 0, ang + k * 360f / arms) * Vector2.right, 5f);
                ang += 17f;
                if (Mathf.FloorToInt(t * 10) % 3 == 0) Sfx.Play("fireball", 0.35f);
                yield return new WaitForSeconds(0.16f);
                t += 0.16f;
            }
        }

        IEnumerator Meteors(PlayerController p, int n)
        {
            LastMove = "meteors";
            _e.Hold(0.9f);
            _e.PlayAnim("CastSpell");
            yield return new WaitForSeconds(0.4f);
            if (p == null) yield break;
            Vector2 at = p.transform.position;
            BossMarker.Spawn(at, fxColor, 1.2f, 1.1f, Dmg(2), transform, pattern == "colossus" ? FxKind.Splash : FxKind.Explosion);
            for (int i = 1; i < n; i++)
            {
                Vector2 o = Random.insideUnitCircle * 3.2f;
                BossMarker.Spawn(at + o, fxColor, 1.1f, 1.1f + i * 0.18f, Dmg(2), transform, pattern == "colossus" ? FxKind.Splash : FxKind.Explosion);
            }
            Sfx.Play(pattern == "colossus" ? "ice" : "fireball");
        }

        IEnumerator Summon(int n)
        {
            LastMove = "summon";
            _spawned.RemoveAll(m => m == null || m.health.IsDead);
            if (minions.Length == 0 || _spawned.Count >= maxMinions) { yield return Wave(1); yield break; }
            _e.Hold(1.2f);
            _e.PlayAnim("CastSpell");
            Sfx.Play("summon");
            var spots = new List<Vector2>();
            for (int i = 0; i < n && _spawned.Count + spots.Count < maxMinions; i++)
            {
                float a = (i / (float)n) * 360f + Random.value * 40f;
                Vector2 at = (Vector2)transform.position + (Vector2)(Quaternion.Euler(0, 0, a) * Vector2.right) * Random.Range(2.4f, 3.4f);
                var wi = WorldInfo.Current;
                if (wi != null && !wi.Walkable(at)) at = (Vector2)transform.position + Random.insideUnitCircle * 1.5f;
                spots.Add(at);
                Fx.Spawn(FxKind.Summon, at, -1, 10f);
            }
            yield return new WaitForSeconds(0.8f);
            int threat = Mathf.Max(2, GameManager.State.Threat);
            for (int i = 0; i < spots.Count; i++)
            {
                var prefab = GameAssets.I ? GameAssets.I.EnemyPrefab(minions[(i + _turn) % minions.Length]) : null;
                if (prefab == null) continue;
                var m = Instantiate(prefab, spots[i], Quaternion.identity).GetComponent<EnemyController>();
                m.spawned = true; m.summoner = _e; m.activeAt = ActiveTime.Always;
                m.Setup(EnemyRank.Normal, threat, false);
                m.aggroRange = 12f;
                _spawned.Add(m);
                Fx.Spawn(FxKind.Poof, spots[i]);
            }
        }

        void Shoot(GameObject prefab, Vector2 dir, float speed)
        {
            if (prefab == null) return;
            var pr = Projectile.Fire(prefab, _e.Body + dir * 0.9f, dir, speed, Dmg(_e.rangedDamage > 0 ? _e.rangedDamage : 2), _e.health.team, transform);
            if (pr == null) return;
            pr.life = 3.2f;
            var sr = pr.GetComponentInChildren<SpriteRenderer>();
            if (sr) sr.color = Color.Lerp(Color.white, fxColor, 0.65f);
        }

        bool _crumbled;
        void Crumble()
        {
            if (_crumbled) return;
            _crumbled = true;
            foreach (var m in _spawned) if (m != null && !m.health.IsDead) { Fx.Spawn(FxKind.Poof, m.Body); Destroy(m.gameObject); }
            _spawned.Clear();
        }

        void OnDestroy() { foreach (var m in _spawned) if (m != null) Destroy(m.gameObject); }
    }
}
