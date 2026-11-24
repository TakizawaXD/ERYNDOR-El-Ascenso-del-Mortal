using UnityEngine;

namespace WoodsGame
{
    /// <summary>Floats up with a little sway and fades out (hearts over a purring cat).</summary>
    public class FloatAway : MonoBehaviour
    {
        public float life = 1.1f, rise = 0.9f;
        SpriteRenderer _sr; float _t; Vector3 _start; float _seed;
        void Awake() { _sr = GetComponent<SpriteRenderer>(); _start = transform.position; _seed = Random.value * 6f; }
        void Update()
        {
            _t += Time.deltaTime;
            float k = _t / life;
            transform.position = _start + new Vector3(Mathf.Sin(_t * 6f + _seed) * 0.08f, rise * k, 0);
            if (_sr) _sr.color = new Color(1, 1, 1, 1f - k * k);
            if (_t >= life) Destroy(gameObject);
        }
    }
}
