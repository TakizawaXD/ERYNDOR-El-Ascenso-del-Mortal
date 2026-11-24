using UnityEngine;

namespace WoodsArt.Animation
{
    /// <summary>
    /// OPTIONAL helper that feeds the generated Animator Controllers from a movement vector.
    /// It does not move anything itself: call SetMovement() from your own movement code
    /// (or leave this component off and set the parameters directly).
    ///   MoveX / MoveY : last facing direction (kept when stopping, so idles face the right way)
    ///   Speed         : 0 = idle, (0, runThreshold) = walk, >= runThreshold = run
    /// </summary>
    [RequireComponent(typeof(Animator))]
    public class CharacterAnimatorDriver : MonoBehaviour
    {
        [Tooltip("Normalised speed at which Walk switches to Run (must match the controller, default 0.6)")]
        public float runThreshold = 0.6f;

        Animator _anim;
        Vector2 _facing = Vector2.down;

        static readonly int MoveX = Animator.StringToHash("MoveX");
        static readonly int MoveY = Animator.StringToHash("MoveY");
        static readonly int Speed = Animator.StringToHash("Speed");
        static readonly int IsMoving = Animator.StringToHash("IsMoving");

        void Awake() { _anim = GetComponent<Animator>(); }

        /// <param name="direction">raw input / velocity direction</param>
        /// <param name="normalisedSpeed">0..1 (1 = full run speed)</param>
        public void SetMovement(Vector2 direction, float normalisedSpeed)
        {
            bool moving = normalisedSpeed > 0.01f && direction.sqrMagnitude > 0.0001f;
            if (moving)
            {
                // snap to the 4 directions the sprites exist for
                _facing = Mathf.Abs(direction.x) >= Mathf.Abs(direction.y)
                    ? new Vector2(Mathf.Sign(direction.x), 0f)
                    : new Vector2(0f, Mathf.Sign(direction.y));
            }
            _anim.SetFloat(MoveX, _facing.x);
            _anim.SetFloat(MoveY, _facing.y);
            _anim.SetFloat(Speed, moving ? normalisedSpeed : 0f);
            _anim.SetBool(IsMoving, moving);
        }

        public void Trigger(string name) { _anim.SetTrigger(name); }
        public void SetFlag(string name, bool value) { _anim.SetBool(name, value); }
    }
}
