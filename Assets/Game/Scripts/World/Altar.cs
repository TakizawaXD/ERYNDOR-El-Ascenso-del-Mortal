using UnityEngine;

namespace WoodsGame
{
    /// <summary>Chapel altar: a blessing that restores all health and stamina, and saves.</summary>
    public class Altar : Interactable
    {
        public override void Interact(PlayerController p)
        {
            var s = GameManager.State;
            s.hp = s.maxHP; p.health.Init(s.maxHP, s.hp);
            Vector2 spot = (Vector2)transform.position + Vector2.down * 1.3f;
            GameManager.SetRestPoint(spot, gameObject.scene.name);
            SaveSystem.Save(s);
            Fx.Spawn(FxKind.Heal, p.Body); Fx.Spawn(FxKind.Sparkle, p.Body);
            Sfx.Play("levelup");
            UIRoot.Toast("BENDICIÓN: VIDA RESTAURADA · PARTIDA GUARDADA", 2.6f);
        }
    }
}
