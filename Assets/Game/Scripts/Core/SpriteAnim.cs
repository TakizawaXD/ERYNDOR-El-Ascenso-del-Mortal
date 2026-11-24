using UnityEngine;

namespace WoodsGame
{
    /// <summary>Plays a sprite sequence once (or looping) on a SpriteRenderer.</summary>
    public class SpriteAnim : MonoBehaviour
    {
        public Sprite[] frames;
        public float fps = 12f;
        public bool loop;
        public bool destroyAtEnd = true;
        SpriteRenderer _sr;
        float _t;

        void Awake() { _sr = GetComponent<SpriteRenderer>(); }

        void Update()
        {
            if (frames == null || frames.Length == 0) return;
            _t += Time.deltaTime;
            int i = Mathf.FloorToInt(_t * fps);
            if (i >= frames.Length)
            {
                if (loop) { i %= frames.Length; }
                else if (destroyAtEnd) { Destroy(gameObject); return; }
                else i = frames.Length - 1;
            }
            _sr.sprite = frames[i];
        }
    }
}
