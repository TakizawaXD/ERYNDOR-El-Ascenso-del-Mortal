using UnityEngine;

namespace WoodsArt.Animation
{
    /// <summary>
    /// Sets an Animator bool to true while this state (or state machine) is playing and back to false on exit.
    /// Used for the read-only flags IsAttacking / IsHurt / IsDodging so gameplay code can query
    /// animator.GetBool("IsAttacking") without tracking clip lengths itself.
    /// </summary>
    public class AnimatorStateFlag : StateMachineBehaviour
    {
        public string parameter = "IsAttacking";

        public override void OnStateEnter(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
        {
            animator.SetBool(parameter, true);
        }

        // a zero-length transition between two flagged states (Attack -> Attack2) enters the new state before it exits
        // the old one, which clears the flag: keep re-asserting it while the state plays
        public override void OnStateUpdate(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
        {
            if (!animator.IsInTransition(layerIndex) && !animator.GetBool(parameter)) animator.SetBool(parameter, true);
        }

        public override void OnStateExit(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
        {
            animator.SetBool(parameter, false);
        }
    }
}
