using UnityEngine;

namespace WoodsGame
{
    /// <summary>Demonic seal blocking the volcano road. Breaks once both guardians (boss_K, boss_Q) are dead.</summary>
    public class SealBarrier : MonoBehaviour
    {
        public string[] requiredFlags = { "boss_K", "boss_Q" };
        bool _open;
        float _nextToast;

        /// <summary>boss flag -> the dungeon that guardian lives in (ERYNDOR: no main boss stands outdoors)</summary>
        static string DungeonOf(string flag) => flag == "boss_K" ? "Dungeon_Orco" : flag == "boss_Q" ? "Dungeon_Sangre" : null;

        /// <summary>A guardian counts once beaten, or while his dungeon does not exist yet (so the story never dead-ends).</summary>
        System.Collections.Generic.HashSet<string> _present;

        bool Counts(string f)
        {
            if (GameManager.State.Has(f)) return true;
            // the guardian lives in a cave of the one map: he counts only if he is not there at all (never a dead end)
            if (_present == null)
            {
                _present = new System.Collections.Generic.HashSet<string>();
                foreach (var e in Object.FindObjectsByType<EnemyController>(FindObjectsInactive.Include, FindObjectsSortMode.None))
                    if (e.isBoss && !string.IsNullOrEmpty(e.bossFlag)) _present.Add(e.bossFlag);
            }
            return !_present.Contains(f) && DungeonOf(f) != null;
        }

        bool Ready()
        {
            foreach (var f in requiredFlags) if (!Counts(f)) return false;
            return true;
        }

        void Start() { if (Ready()) Open(false); }

        void Update()
        {
            if (!_open && Ready()) Open(true);
        }

        void Open(bool fx)
        {
            _open = true;
            foreach (var c in GetComponentsInChildren<Collider2D>()) c.enabled = false;
            foreach (var r in GetComponentsInChildren<SpriteRenderer>()) r.enabled = false;
            if (fx)
            {
                Fx.Spawn(FxKind.Explosion, transform.position);
                CameraFollow.Shake(0.4f, 0.15f);
                Sfx.Play("boss_roar");
            }
        }

        void OnCollisionEnter2D(Collision2D c)
        {
            if (_open || Time.time < _nextToast || c.collider.GetComponentInParent<PlayerController>() == null) return;
            _nextToast = Time.time + 3f;
            int n = 0; foreach (var f in requiredFlags) if (Counts(f)) n++;
            UIRoot.Toast($"EL SELLO RESISTE. GUARDIANES DERROTADOS: {n}/{requiredFlags.Length}", 2.5f);
        }
    }
}
