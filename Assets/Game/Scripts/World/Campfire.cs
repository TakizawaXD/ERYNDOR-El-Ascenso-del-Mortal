using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Bonfire (dark-fantasy rest point, replaces the camps). The first time you reach one you kindle it (ignition
    /// flash); from then on: rest = full life and stamina, respawn point and saved game, and normal enemies of this map
    /// come back. Its menu keeps the camp's services: crafting, storage and sleeping until dawn/dusk.</summary>
    public class Campfire : Interactable
    {
        public static readonly List<Campfire> All = new List<Campfire>();
        /// <summary>The bonfire the player is using right now (crafting here may use the storage).</summary>
        public static Campfire Current { get; private set; }

        public string campName = "HOGUERA";
        [Tooltip("frame 0 = cold ash with the planted sword, 1.. = fire loop")]
        public Sprite[] frames;

        SpriteRenderer _sr; SpriteAnim _anim; LightGlow _glow;

        protected override void OnEnable() { base.OnEnable(); All.Add(this); }
        protected override void OnDisable() { base.OnDisable(); All.Remove(this); if (Current == this) Current = null; }

        /// <summary>Seen at least once (it shows on the map).</summary>
        public bool Discovered => GameManager.State.Has(Id);
        /// <summary>Kindled by the player: a rest point.</summary>
        public bool Lit => GameManager.State.Has("lit_" + Id);
        string Id => MapDB.Key("fire", transform.position, gameObject.scene.name);
        public Vector2 Spot => (Vector2)transform.position + Vector2.down * 1.1f;

        /// <summary>The player is close to some bonfire (crafting and storage need one).</summary>
        public static Campfire Near(Vector2 at, float radius = 4.5f)
        {
            foreach (var c in All) if (Vector2.Distance(c.transform.position, at) < radius) return c;
            return null;
        }

        void Start()
        {
            _sr = GetComponent<SpriteRenderer>(); _anim = GetComponent<SpriteAnim>(); _glow = GetComponentInChildren<LightGlow>(true);
            ShowLit(Lit);
        }

        void ShowLit(bool lit)
        {
            if (frames != null && frames.Length > 1 && _anim != null)
            {
                _anim.enabled = lit;
                if (lit) { var f = new Sprite[frames.Length - 1]; System.Array.Copy(frames, 1, f, 0, f.Length); _anim.frames = f; }
                else if (_sr) _sr.sprite = frames[0];
            }
            if (_glow) _glow.gameObject.SetActive(lit);
        }

        protected override void Update()
        {
            base.Update();
            var p = PlayerController.Current;
            if (p == null) return;
            float d = Vector2.Distance(p.transform.position, transform.position);
            if (!Discovered && d < 6f) GameManager.State.Set(Id);            // shows up on the map once seen
            if (Current == this && d > 6f) Current = null;
        }

        public override void Interact(PlayerController p)
        {
            if (!Lit) { StartCoroutine(Kindle(p)); return; }
            Rest(p);
            OpenMenu();
        }

        IEnumerator Kindle(PlayerController p)
        {
            GameManager.State.Set("lit_" + Id);
            Sfx.Play("fire_ignite", 1f);
            Fx.Spawn(FxKind.Explosion, (Vector2)transform.position + Vector2.up * 0.6f);
            CameraFollow.Shake(0.12f, 0.06f);
            ShowLit(true);
            UIRoot.TitleCard("HOGUERA ENCENDIDA", campName);
            yield return new WaitForSeconds(0.6f);
            Rest(p);
            OpenMenu();
        }

        /// <summary>Sit by the fire: full life and stamina, the bonfire becomes the respawn point, the game is saved and the
        /// ordinary enemies of this map return (bosses and their arenas never do).</summary>
        public void Rest(PlayerController p)
        {
            Current = this;
            var s = GameManager.State;
            s.Set(Id); s.Set("lit_" + Id);
            s.hp = s.maxHP;
            p.health.Init(s.maxHP, s.hp);
            p.RestoreStamina();
            GameManager.SetRestPoint(Spot, gameObject.scene.name);
            ResetEnemies();
            SaveSystem.Save(s);
            Fx.Spawn(FxKind.Heal, p.Body);
            Sfx.Play("heal"); Sfx.Play("fire_ignite", 0.5f);
        }

        /// <summary>Resting at a bonfire resets the world's enemies: every ordinary creature lives again at its home with full
        /// life, the roaming ones vanish. Bosses never come back; creatures asleep for the night stay asleep.</summary>
        public static void ResetEnemies()
        {
            string map = GameManager.CurrentMap;
            GameManager.State.defeated.RemoveAll(k => k.StartsWith(map + "|"));
            foreach (var e in Resources.FindObjectsOfTypeAll<EnemyController>())
            {
                if (e == null || e.isBoss || !e.gameObject.scene.IsValid()) continue;
                if (e.spawned) { if (e.gameObject.activeSelf) Object.Destroy(e.gameObject); continue; }
                if (!e.gameObject.activeSelf && !e.health.IsDead) continue;      // asleep for the night: wakes at dawn as usual
                e.Respawn();
            }
            UIRoot.Toast("LOS ENEMIGOS HAN REGRESADO", 2f);
        }

        static void RespawnResidents(Vector2 player)
        {
            string map = GameManager.CurrentMap;
            GameManager.State.defeated.RemoveAll(k => k.StartsWith(map + "|"));
            foreach (var e in Resources.FindObjectsOfTypeAll<EnemyController>())
            {
                if (e == null || e.isBoss || e.spawned || !e.gameObject.scene.IsValid() || e.gameObject.activeSelf) continue;
                if (Vector2.Distance(e.Home, player) < 12f) continue;              // never pop up in front of you
                e.Respawn();
            }
        }

        public void OpenMenu()
        {
            Current = this;
            bool night = DayNight.IsNight;
            WorldUI.Choice(campName, "Descansas junto al fuego. Vida y aguante restaurados · partida guardada · los enemigos regresan.",
                new[] { "FABRICAR", "ALMACÉN", night ? "DORMIR HASTA EL AMANECER" : "DORMIR HASTA EL ANOCHECER", "SEGUIR EL CAMINO" },
                new System.Action[] { () => WorldUI.OpenCraft(false), WorldUI.OpenStash, () => { WorldUI.CloseAll(); GameManager.Sleep(Spot); }, WorldUI.CloseAll },
                GameAssets.I ? GameAssets.I.MatIcon(24) : null);
        }
    }
}
