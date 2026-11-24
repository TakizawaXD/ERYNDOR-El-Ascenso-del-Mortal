using System.Collections;
using System.Linq;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace WoodsGame.Tests
{
    /// <summary>The new roster (Tools/CharAnim/roster.py): every figure is animated (idle breathing, walk, attack, hurt,
    /// death), the monsters spawn in their regions and the town heroes do their jobs.</summary>
    public class RosterTests
    {
        VirtualInput _in;

        [UnitySetUp]
        public IEnumerator SetUp()
        {
            SaveSystem.Key = "woods_save_TEST"; SaveSystem.Delete();
            _in = new VirtualInput(); GameInput.Source = _in;
            GameManager.State = PlayerState.NewCharacter("knight"); SpawnDirector.Enabled = false; Time.timeScale = 1;
            yield return null;
        }

        [UnityTearDown]
        public IEnumerator TearDown()
        {
            SaveSystem.Delete(); SaveSystem.Key = "woods_save_v2"; SpawnDirector.Enabled = true;
            GameInput.Source = new KeyboardInput(); WorldUI.CloseAll(); Time.timeScale = 1;
            yield return null;
        }

#if UNITY_EDITOR
        [Test]
        public void EveryRosterFigure_HasIdleWalkAttackHurtAndDeath()
        {
            var ids = RosterDB.Heroes.Select(h => h.id).Concat(RosterDB.Spawns.Values.SelectMany(v => v.day.Concat(v.night))).Distinct().ToArray();
            Assert.GreaterOrEqual(ids.Length, 40);
            foreach (var id in ids)
            {
                var prefab = UnityEditor.AssetDatabase.LoadAssetAtPath<GameObject>($"Assets/Game/Prefabs/{id}.prefab");
                Assert.IsNotNull(prefab, id + " prefab");
                var ctrl = prefab.GetComponentInChildren<Animator>().runtimeAnimatorController as UnityEditor.Animations.AnimatorController;
                Assert.IsNotNull(ctrl, id + " animator");
                var states = ctrl.layers[0].stateMachine.states.Select(s => s.state.name).ToArray();
                foreach (var st in new[] { "Idle", "Walk", "Attack", "HeavyAttack", "Hurt", "Death" })
                    Assert.Contains(st, states, id + " " + st);
                var idle = UnityEditor.AssetDatabase.LoadAllAssetsAtPath($"Assets/Art/Characters/{id}/Idle/{id}_Idle_Down.png").OfType<Sprite>().Count();
                Assert.GreaterOrEqual(idle, 2, id + " idle actually moves");
            }
        }
#endif

        [Test]
        public void Monsters_SpawnInTheirRegions()
        {
            Assert.Contains("Werewolf", SpawnDirector.Table['b'].night);
            Assert.Contains("LavaGolem", SpawnDirector.Table['g'].day);
            Assert.Contains("Reaper", SpawnDirector.Table['h'].night);
            foreach (var t in SpawnDirector.Table.Values.SelectMany(v => v.day.Concat(v.night)).Distinct())
                Assert.IsNotNull(GameAssets.I.EnemyPrefab(t), "prefab for spawn type " + t);
        }

        [UnityTest, Timeout(120000)]
        public IEnumerator TownHeroes_DoTheirJobs()
        {
            SceneManager.LoadScene("City_Valle");
            yield return WorldTests.Until(() => SceneManager.GetActiveScene().name == "City_Valle" && PlayerController.Current != null, 10f, "load the village");
            yield return new WaitForSeconds(0.5f);
            var heroes = Object.FindObjectsByType<Adventurer>(FindObjectsSortMode.None);
            Assert.GreaterOrEqual(heroes.Length, 3, "adventurers in the village");
            var p = PlayerController.Current;
            var healer = heroes.First(h => h.Job == RosterDB.Job.Healer);
            p.health.Init(p.health.maxHP, 1);
            healer.Interact(p);
            Assert.AreEqual(p.health.maxHP, p.health.hp, "the priestess heals");
            WorldUI.CloseAll();
            var ranger = heroes.First(h => h.Job == RosterDB.Job.Ranger);
            int arrows = GameManager.State.arrows;
            ranger.Interact(p);
            Assert.AreEqual(arrows + 8, GameManager.State.arrows, "the ranger gives arrows");
            // a guard attacks an enemy that comes to its post
            var guard = heroes.First(h => h.Job == RosterDB.Job.Guard);
            var e = Object.Instantiate(GameAssets.I.EnemyPrefab("GoblinAxe"), guard.transform.position + Vector3.right * 2f, Quaternion.identity).GetComponent<EnemyController>();
            e.aggroRange = 0.1f;
            int hp = e.health.hp;
            yield return WorldTests.Until(() => e == null || e.health.hp < hp, 8f, "the guard strikes the goblin");
        }
    }
}
