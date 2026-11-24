using UnityEngine;

namespace WoodsGame
{
    /// <summary>Townsfolk knights inside houses: stand idle and turn to look at the player when close.</summary>
    public class NpcIdle : MonoBehaviour
    {
        Animator _anim;
        void Start() { _anim = GetComponentInChildren<Animator>(); Look(Vector2.down); }

        void Update()
        {
            var p = PlayerController.Current;
            if (p == null || _anim == null || Time.frameCount % 10 != 0) return;
            Vector2 to = p.transform.position - transform.position;
            Look(to.sqrMagnitude < 9f ? Combat.Snap4(to) : Vector2.down);
        }

        void Look(Vector2 d) { if (_anim) { _anim.SetFloat("MoveX", d.x); _anim.SetFloat("MoveY", d.y); } }
    }
}
