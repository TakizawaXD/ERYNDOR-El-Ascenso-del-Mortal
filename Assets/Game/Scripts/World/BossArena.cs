using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>A boss's lair: when the fight starts with the player inside, a rune wall seals the circle, the boss theme plays
    /// and the objective appears. Beating the boss opens it again; dying or leaving it reset. While the player stands in it,
    /// the arena's own light and fog replace the region's (ZoneAtmosphere).</summary>
    public class BossArena : MonoBehaviour
    {
        static readonly List<BossArena> All = new List<BossArena>();

        public EnemyController boss;
        public Vector2 size = new Vector2(9.5f, 5.8f);            // ellipse half-axes (matches the painted floor)
        public string bossTitle = "", subtitle = "", objective = "";
        public Color tint = new Color(0.75f, 0.7f, 0.95f);       // multiply colour of the arena light
        public Color fogColor = new Color(0.6f, 0.4f, 0.9f, 0.25f);
        public Color glowColor = new Color(0.7f, 0.35f, 1f);
        public int theme;

        public bool Sealed { get; private set; }
        public bool Cleared { get; private set; }
        public static BossArena Inside { get; private set; }
        public static BossArena Fighting { get; private set; }

        EdgeCollider2D _wall;
        GameObject _wallFx;
        float _flare = 1f;

        public static BossArena For(EnemyController e)
        {
            foreach (var a in All) if (a != null && a.boss == e) return a;
            return null;
        }

        void OnEnable() { All.Add(this); }
        void OnDisable()
        {
            All.Remove(this);
            if (Inside == this) Inside = null;
            if (Fighting == this) { Fighting = null; Sfx.BossMusic(false); BossHud.Hide(); }
        }

        void Awake()
        {
            var seal = transform.Find("Seal");
            if (seal != null)
            {
                _wall = seal.GetComponent<EdgeCollider2D>();
                _wallFx = seal.gameObject;
                if (_wall) _wall.enabled = false;
                foreach (var r in seal.GetComponentsInChildren<SpriteRenderer>(true)) r.enabled = false;
            }
        }

        void Update()
        {
            var p = PlayerController.Current;
            bool inside = p != null && Contains(p.transform.position);
            if (inside) Inside = this; else if (Inside == this) Inside = null;

            if (!Cleared && (boss == null || !boss.gameObject.activeInHierarchy) && !Sealed) { Cleared = true; SetFlare(0.6f); }
            if (Cleared && !Sealed) return;

            if (!Sealed)
            {
                bool deep = p != null && Contains(p.transform.position, 1.2f);
                if (deep && boss != null && boss.Engaged && !boss.health.IsDead && !p.health.IsDead) Seal();
                return;
            }
            if (boss == null || boss.health.IsDead) { Victory(); return; }
            if (p == null || p.health.IsDead || !inside) Open();
        }

        void Seal()
        {
            Sealed = true; Fighting = this;
            if (_wall) _wall.enabled = true;
            if (_wallFx) foreach (var r in _wallFx.GetComponentsInChildren<SpriteRenderer>(true)) r.enabled = true;
            Sfx.Play("boss_roar");
            Sfx.BossMusic(true);
            CameraFollow.Shake(0.3f, 0.12f);
            if (boss.GetComponent<SummonerBoss>() == null) UIRoot.TitleCard(bossTitle, subtitle);
            BossHud.Show(boss, objective);
            SetFlare(1.25f);
        }

        void Open()
        {
            Sealed = false;
            if (Fighting == this) Fighting = null;
            if (_wall) _wall.enabled = false;
            if (_wallFx) foreach (var r in _wallFx.GetComponentsInChildren<SpriteRenderer>(true)) r.enabled = false;
            Sfx.BossMusic(false);
            BossHud.Hide();
            SetFlare(1f);
        }

        void Victory()
        {
            Open();
            Cleared = true;
            Sfx.Play("boss_win");
            UIRoot.TitleCard("¡VICTORIA!", (bossTitle.Length > 0 ? bossTitle : "EL JEFE") + " HA CAÍDO");
            BossHud.Completed(objective);
            SetFlare(0.6f);
        }

        /// <summary>Phase change: braziers and runes blaze brighter.</summary>
        public void Flare(int phase) { SetFlare(1.25f + 0.15f * (phase - 1)); }

        void SetFlare(float k)
        {
            _flare = k;
            foreach (var g in GetComponentsInChildren<LightGlow>(true)) g.extra = k;
            foreach (var a in GetComponentsInChildren<ArenaProp>(true)) a.boost = Mathf.Min(1.6f, k);
        }

        public float FlareLevel => _flare;

        /// <summary>Is a point inside the ellipse (shrunk by margin units)?</summary>
        public bool Contains(Vector2 world, float margin = 0f)
        {
            Vector2 d = world - (Vector2)transform.position;
            float rx = Mathf.Max(0.5f, size.x - margin), ry = Mathf.Max(0.5f, size.y - margin);
            return (d.x * d.x) / (rx * rx) + (d.y * d.y) / (ry * ry) < 1f;
        }
    }
}
