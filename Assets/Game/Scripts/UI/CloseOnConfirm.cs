using UnityEngine;

namespace WoodsGame
{
    /// <summary>Closes its GameObject on Enter / Esc (used by the controls sheet).</summary>
    public class CloseOnConfirm : MonoBehaviour
    {
        float _opened;
        void OnEnable() { _opened = Time.unscaledTime; }
        void Update()
        {
            if (Time.unscaledTime - _opened > 0.15f && (GameInput.Confirm || GameInput.Pause || GameInput.Interact))
                gameObject.SetActive(false);
        }
    }
}
