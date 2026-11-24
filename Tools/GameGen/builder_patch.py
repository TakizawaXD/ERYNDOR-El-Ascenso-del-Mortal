p = 'G:/Juegos/Assets/Game/Editor/GameBuilder.cs'
s = open(p, encoding='utf8').read()
def rep(a, b):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b)
rep("    public static class GameBuilder\n", "    public static partial class GameBuilder\n")
rep("""                e.potionChance = 0; e.arrowChance = 0;
            });""", """                e.potionChance = 0; e.arrowChance = 0; e.bossFlag = "boss_B";
            });
            ActorPrefab("OrcChieftain", "Orc", true, 2, go =>
            {
                var e = go.AddComponent<EnemyController>();
                e.kind = EnemyKind.Orc; e.displayName = "JEFE ORCO"; e.isBoss = true; e.bossFlag = "boss_K"; e.maxHP = 40; e.damage = 3;
                e.walkSpeed = 1.5f; e.chaseSpeed = 2.3f; e.aggroRange = 6.5f; e.attackRange = 1.1f; e.attackCooldown = 1.0f; e.heavyChance = 0.5f;
                e.coins = 0; e.potionChance = 0; e.arrowChance = 0;
            });
            ActorPrefab("BloodMother", "BloodMonster", true, 2, go =>
            {
                var e = go.AddComponent<EnemyController>();
                e.kind = EnemyKind.BloodMonster; e.displayName = "MADRE DE SANGRE"; e.isBoss = true; e.bossFlag = "boss_Q"; e.maxHP = 45; e.damage = 2;
                e.walkSpeed = 1.3f; e.chaseSpeed = 2.0f; e.aggroRange = 7f; e.attackRange = 1.0f; e.attackCooldown = 1.2f; e.heavyChance = 0.35f;
                e.ranged = true; e.rangedMin = 2.2f; e.rangedMax = 7.5f; e.rangedCooldown = 2.0f; e.rangedDamage = 2;
                e.coins = 0; e.potionChance = 0; e.arrowChance = 0;
            });""")
rep("e.displayName = \"SEÑOR DEMONIO\"; e.isBoss = true; e.maxHP = 60;", "e.displayName = \"SEÑOR DEMONIO\"; e.isBoss = true; e.maxHP = 70;")
rep("""            BuildMenuScene();
            BuildLevelScene("Level1_Forest", requireClearForExit: true);
            BuildLevelScene("Level2_Ruins", requireClearForExit: false);
            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene($"{ScenesDir}/MainMenu.unity", true),
                new EditorBuildSettingsScene($"{ScenesDir}/Level1_Forest.unity", true),
                new EditorBuildSettingsScene($"{ScenesDir}/Level2_Ruins.unity", true),
            };""", """            BuildMenuScene();
            BuildWorldScene();
            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene($"{ScenesDir}/MainMenu.unity", true),
                new EditorBuildSettingsScene($"{ScenesDir}/World.unity", true),
            };""")
open(p, 'w', encoding='utf8').write(s)
print('ok')
