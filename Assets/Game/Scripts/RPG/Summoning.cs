using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>The Summoner's curse (after defeating El Invocador): press V next to an enemy you just killed to raise it as an ally
    /// (up to 4). Press V elsewhere to give your allies a task. An ally that dies is lost for good. Allies are saved and come back with you.</summary>
    public static class Summoning
    {
        public const string Follow = "seguir", Attack = "atacar", Guard = "guardar";
        public const int Max = 4;
        public const float CorpseSeconds = 8f;
        public const string CurseFlag = "curse_summoner";

        public static bool Cursed => GameManager.State.Has(CurseFlag);

        public static IEnumerable<EnemyController> Allies => EnemyController.Active.Where(e => e != null && e.ally && !e.health.IsDead);
        public static int Count => GameManager.State.summons.Count;

        public static string TaskName(string t) => t == Attack ? "atacar" : t == Guard ? "guardar" : "seguirte";

        /// <summary>V: raise a fresh corpse if there is one at hand, otherwise open the command menu.</summary>
        public static void OnKey(PlayerController p)
        {
            if (!Cursed) return;
            var corpse = FreshCorpse(p);
            if (corpse != null)
            {
                if (Count >= Max) { UIRoot.Toast($"YA TIENES {Max} INVOCACIONES · LIBERA ALGUNA (V)", 2f); return; }
                Raise(corpse, p);
                return;
            }
            WorldUI.OpenSummons();
        }

        public static EnemyController FreshCorpse(PlayerController p)
        {
            EnemyController best = null; float bd = 2.4f;
            foreach (var e in Object.FindObjectsByType<EnemyController>(FindObjectsSortMode.None))
            {
                if (!e.health.IsDead || e.ally || e.isBoss || e.summoner != null || e.DiedAt < 0 || Time.time - e.DiedAt > CorpseSeconds) continue;
                float d = Vector2.Distance(e.transform.position, p.transform.position);
                if (d < bd) { bd = d; best = e; }
            }
            return best;
        }

        public static EnemyController Raise(EnemyController corpse, PlayerController p)
        {
            var prefab = GameAssets.I ? GameAssets.I.EnemyPrefab(corpse.typeId) : null;
            if (prefab == null) { UIRoot.Toast("ESTE CUERPO NO RESPONDE A LA MALDICIÓN"); return null; }
            Vector2 at = corpse.transform.position;
            corpse.ConsumeCorpse();
            var ally = Spawn(corpse.typeId, at, Follow);
            if (ally == null) return null;
            GameManager.State.summons.Add(corpse.typeId);
            Sfx.Play("spell"); Sfx.Play("boss_roar", 0.3f);
            UIRoot.Toast($"{ally.displayName} TE OBEDECE ({Count}/{Max}) · V PARA DARLE ÓRDENES", 2.6f);
            return ally;
        }

        static EnemyController Spawn(string type, Vector2 at, string task)
        {
            var prefab = GameAssets.I ? GameAssets.I.EnemyPrefab(type) : null;
            if (prefab == null) return null;
            var e = Object.Instantiate(prefab, at, Quaternion.identity).GetComponent<EnemyController>();
            e.MakeAlly(task);
            e.guardPoint = at;
            Fx.Spawn(FxKind.Summon, at, -1, 12f);
            return e;
        }

        /// <summary>After loading the world (continue / respawn), the saved allies appear around you.</summary>
        public static void Restore(PlayerController p)
        {
            var s = GameManager.State;
            int i = 0;
            foreach (var t in s.summons.ToArray())
            {
                Vector2 at = (Vector2)p.transform.position + (Vector2)(Quaternion.Euler(0, 0, 90 * i++) * Vector2.right) * 1.2f;
                if (Spawn(t, at, Follow) == null) s.summons.Remove(t);
            }
        }

        public static void OnAllyDied(EnemyController e)
        {
            GameManager.State.summons.Remove(e.typeId);
            UIRoot.Toast($"{e.displayName} HA CAÍDO PARA SIEMPRE", 2.4f);
        }

        public static void SetTask(EnemyController e, string task)
        {
            if (e == null) return;
            e.allyTask = task;
            var p = PlayerController.Current;
            if (task == Guard) e.guardPoint = p ? (Vector2)p.transform.position + Random.insideUnitCircle * 0.8f : (Vector2)e.transform.position;
        }

        public static void Release(EnemyController e)
        {
            if (e == null) return;
            GameManager.State.summons.Remove(e.typeId);
            Fx.Spawn(FxKind.Poof, e.Body);
            Object.Destroy(e.gameObject);
        }
    }
}
