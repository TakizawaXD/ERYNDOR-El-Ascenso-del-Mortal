using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Walking into it finishes the level.</summary>
    public class LevelExit : MonoBehaviour
    {
        public string lockedMessage = "";
        public bool requireAllEnemies;
        bool _used;

        void OnTriggerEnter2D(Collider2D other)
        {
            if (_used || other.GetComponentInParent<PlayerController>() == null) return;
            if (requireAllEnemies && GameManager.EnemiesAlive > 0)
            {
                UIRoot.Toast(string.IsNullOrEmpty(lockedMessage) ? "QUEDAN ENEMIGOS: " + GameManager.EnemiesAlive : lockedMessage);
                return;
            }
            _used = true;
            GameManager.CompleteLevel();
        }
    }
}
