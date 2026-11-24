using UnityEngine;

namespace WoodsGame
{
    /// <summary>Experience, levels, attribute points, class perks on kill and kill bookkeeping.</summary>
    public static class Progression
    {
        public static int XpFor(EnemyController e) => Mathf.Max(1, e.xpReward);

        public static void OnEnemyKilled(EnemyController e)
        {
            var s = GameManager.State;
            s.kills++;
            switch (e.kind)
            {
                case EnemyKind.Orc: s.orcKills++; break;
                case EnemyKind.BloodMonster: s.bloodKills++; break;
                case EnemyKind.Demon: s.demonKills++; break;
            }
            if (e.rank == EnemyRank.Elite) s.eliteKills++;
            if (e.rank == EnemyRank.Champion) s.champions++;
            if (!string.IsNullOrEmpty(e.bossFlag)) s.Set(e.bossFlag);
            int threatBefore = s.Threat;
            UIRoot.Popup(e.Body + Vector2.up * 0.9f, $"+{XpFor(e)} XP", new Color32(0xff, 0xc8, 0x5a, 0xff));
            AddXP(XpFor(e));
            // class perk: the Dark Knight drinks from every kill
            var p = PlayerController.Current;
            if (s.classId == "dark" && p != null && !p.health.IsDead) p.health.Heal(e.rank == EnemyRank.Normal ? 1 : 3);
            if (s.Threat > threatBefore)
                UIRoot.Toast($"AMENAZA {s.Threat}: EL MUNDO RESPONDE A TU MATANZA", 2.6f);
            Quests.Refresh();
        }

        public static void AddXP(int amount)
        {
            var s = GameManager.State;
            if (s.level >= PlayerState.MaxLevel) return;
            s.xp += amount;
            while (s.level < PlayerState.MaxLevel && s.xp >= s.XpToNext)
            {
                s.xp -= s.XpToNext;
                s.level++;
                int pts = s.Class.pointsPerLevel;
                s.attrPoints += pts;
                s.RecalcHP(true);
                var p = PlayerController.Current;
                if (p) { p.health.Init(s.maxHP, s.hp); Fx.Spawn(FxKind.Heal, p.Body); }
                Sfx.Jingle("levelup");
                UIRoot.TitleCard($"¡Nivel {s.level}!", $"+{pts} puntos de atributo · pulsa C para repartirlos");
            }
        }
    }
}
