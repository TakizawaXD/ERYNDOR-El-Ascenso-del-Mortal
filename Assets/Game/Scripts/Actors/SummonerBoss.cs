using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>El Invocador (end of the first part). Fights with magic (teleport + violet fire, from EnemyController's Caster AI) and
    /// raises the dead to fight for him. While any of his minions stands he is immune; when they all fall he is defenceless for a
    /// few seconds, then he raises the fallen again (each wave bigger). Defeating him curses the player with his power.</summary>
    [RequireComponent(typeof(EnemyController))]
    public class SummonerBoss : MonoBehaviour
    {
        public string[] minionTypes = { "KnightFallen", "Orc", "DemonWraith", "Demon", "OrcBerserker" };
        public int firstWave = 3, maxWave = 5;
        public float exposedSeconds = 9f;
        public float exposedDamage = 0.22f;      // part of his life you can take in one opening

        EnemyController _e;
        readonly List<EnemyController> _minions = new List<EnemyController>();
        readonly List<(string type, Vector2 at)> _fallen = new List<(string, Vector2)>();
        bool _started, _exposed, _raising;
        float _exposedUntil; int _hpAtExpose, _wave;
        LightGlow _shield;

        public bool Exposed => _exposed;
        public int MinionsAlive { get { _minions.RemoveAll(m => m == null || m.health.IsDead); return _minions.Count; } }
        public IReadOnlyList<EnemyController> Minions => _minions;

        void Awake() { _e = GetComponent<EnemyController>(); }

        void Update()
        {
            if (_e.health.IsDead || GameManager.Paused) return;
            var p = PlayerController.Current;
            if (!_started)
            {
                if (_e.Engaged && p != null) Begin();
                return;
            }
            if (_e.Asleep || p == null || p.health.IsDead) { ResetFight(); return; }
            if (_raising) return;
            int alive = MinionsAlive;
            if (alive > 0) { SetShield(true); return; }
            if (!_exposed)
            {
                _exposed = true; _exposedUntil = Time.time + exposedSeconds; _hpAtExpose = _e.health.hp;
                SetShield(false);
                _e.Stun(1.6f);
                UIRoot.Toast("¡EL INVOCADOR ESTÁ INDEFENSO! ¡ATACA!", 2f);
                return;
            }
            bool tookEnough = _hpAtExpose - _e.health.hp >= Mathf.CeilToInt(_e.health.maxHP * exposedDamage);
            if (Time.time > _exposedUntil || tookEnough) StartCoroutine(RaiseWave());
        }

        void Begin()
        {
            _started = true; _wave = 0;
            UIRoot.TitleCard("EL INVOCADOR", "DERROTA A SUS SIERVOS PARA PODER HERIRLE");
            StartCoroutine(RaiseWave());
        }

        void ResetFight()
        {
            foreach (var m in _minions) if (m != null) Destroy(m.gameObject);
            _minions.Clear(); _fallen.Clear();
            _started = false; _exposed = false; _raising = false;
            SetShield(true);
            _e.health.Init(_e.health.maxHP);
        }

        IEnumerator RaiseWave()
        {
            _raising = true; _exposed = false;
            SetShield(true);
            _e.EndStun();                                      // a stun never stops him from casting
            int n = Mathf.Min(maxWave, firstWave + _wave);
            _wave++;
            UIRoot.Toast(_wave == 1 ? "«LEVANTAOS, SIERVOS MÍOS»" : "«LA MUERTE NO OS LIBRA DE MÍ»", 2.2f);
            Sfx.Play("boss_roar");
            var anim = GetComponentInChildren<Animator>(); if (anim) anim.SetTrigger("CastSpell");
            var spots = new List<(string, Vector2)>();
            // the fallen come back first, then new ones around him
            foreach (var f in _fallen) if (spots.Count < n) spots.Add(f);
            _fallen.Clear();
            for (int i = spots.Count; i < n; i++)
            {
                float ang = (i / (float)n) * 360f + _wave * 25f;
                Vector2 at = (Vector2)transform.position + (Vector2)(Quaternion.Euler(0, 0, ang) * Vector2.right) * Random.Range(2.6f, 3.6f);
                spots.Add((minionTypes[(i + _wave) % minionTypes.Length], at));
            }
            foreach (var (_, at) in spots) Fx.Spawn(FxKind.Summon, at, -1, 10f);
            yield return new WaitForSeconds(0.9f);
            int threat = Mathf.Max(3, GameManager.State.Threat);
            foreach (var (type, at) in spots)
            {
                var prefab = GameAssets.I ? GameAssets.I.EnemyPrefab(type) : null;
                if (prefab == null) continue;
                var m = Instantiate(prefab, at, Quaternion.identity).GetComponent<EnemyController>();
                m.spawned = true; m.summoner = _e;
                m.activeAt = ActiveTime.Always;
                m.Setup(EnemyRank.Normal, threat, false);
                m.aggroRange = 12f;
                _minions.Add(m);
                Fx.Spawn(FxKind.Poof, at);
            }
            yield return new WaitForSeconds(0.3f);
            _raising = false;
        }

        public void MinionDied(EnemyController m)
        {
            _fallen.Add((m.typeId, m.transform.position));
            if (MinionsAlive == 0) UIRoot.Popup(_e.Body + Vector2.up * 1.6f, "¡SIN SIERVOS!", UIRoot.Gold);
        }

        void SetShield(bool on)
        {
            if (_e.shielded == on && (_shield != null || !on)) return;
            _e.shielded = on;
            if (on && _shield == null) _shield = LightGlow.Attach(transform, new Vector2(0, 0.6f), 3.2f, new Color(0.65f, 0.3f, 1f), 0.9f, true);
            if (_shield != null) _shield.gameObject.SetActive(on);
        }

        void OnDestroy() { foreach (var m in _minions) if (m != null && !m.health.IsDead) Destroy(m.gameObject); }

        /// <summary>When he dies his minions crumble.</summary>
        public void Crumble()
        {
            foreach (var m in _minions) if (m != null && !m.health.IsDead) { Fx.Spawn(FxKind.Poof, m.Body); Destroy(m.gameObject); }
            _minions.Clear();
        }
    }
}
