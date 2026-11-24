using UnityEngine;

namespace WoodsGame
{
    /// <summary>Smooth follow clamped to the level bounds (or the room you are in). Snapped to whole screen pixels,
    /// not to the 16 px art grid, so the scrolling glides instead of stepping.</summary>
    [RequireComponent(typeof(Camera))]
    public class CameraFollow : MonoBehaviour
    {
        public const int PPU = 16;
        public const int RefHeight = 180;   // 320x180 virtual screen
        public float smooth = 8f;

        static CameraFollow _i;
        static float _shakeUntil, _shakeAmp;
        Camera _cam;
        Vector3 _pos;

        void Awake()
        {
            _i = this;
            _cam = GetComponent<Camera>();
            _cam.orthographic = true;
            _cam.orthographicSize = RefHeight / 2f / PPU;   // 5.625 -> 11.25 tiles tall
            _pos = transform.position;
        }

        public static void Shake(float seconds, float amplitude)
        {
            _shakeUntil = Time.time + seconds;
            _shakeAmp = amplitude;
        }

        void LateUpdate()
        {
            var p = PlayerController.Current;
            if (p != null)
            {
                Vector3 target = (Vector2)p.transform.position + Vector2.up * 0.5f;
                _pos = Vector3.Lerp(_pos, target, 1f - Mathf.Exp(-smooth * Time.unscaledDeltaTime));
            }
            var lv = LevelInfo.Current;
            Vector3 c = _pos;
            if (lv != null || Interior.Current != null)
            {
                float h = _cam.orthographicSize, w = h * _cam.aspect;
                var wiv = WorldInfo.Current;
                var b = Interior.Current != null ? Interior.Current.bounds
                      : wiv != null && lv != null ? wiv.ViewBounds(_pos) : lv.bounds;
                c.x = b.width > 2 * w ? Mathf.Clamp(c.x, b.xMin + w, b.xMax - w) : b.center.x;
                c.y = b.height > 2 * h ? Mathf.Clamp(c.y, b.yMin + h, b.yMax - h) : b.center.y;
            }
            if (Time.time < _shakeUntil) c += (Vector3)(Random.insideUnitCircle * _shakeAmp);
            float upp = 2f * _cam.orthographicSize / Mathf.Max(1, Screen.height);   // world units per screen pixel
            c.x = Mathf.Round(c.x / upp) * upp;
            c.y = Mathf.Round(c.y / upp) * upp;
            c.z = -10;
            transform.position = c;
        }

        public static void SnapTo(Vector2 p)
        {
            if (_i) { _i._pos = p; _i.LateUpdate(); }
        }
    }
}
