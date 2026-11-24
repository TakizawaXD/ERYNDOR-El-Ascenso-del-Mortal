using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Night darkening + warm lights in the built-in 2D renderer: a camera-sized quad with a multiply shader tints
    /// the world by the ambient colour, then additive radial glows (campfires, torches, windows, the player's lantern) are drawn on top.</summary>
    [RequireComponent(typeof(Camera))]
    public class DayNightLighting : MonoBehaviour
    {
        public const int OverlayOrder = 1000;
        SpriteRenderer _overlay;
        Camera _cam;
        LightGlow _lantern;
        static Sprite _white;

        void Start()
        {
            _cam = GetComponent<Camera>();
            var a = GameAssets.I;
            var go = new GameObject("NightOverlay");
            go.transform.SetParent(transform, false);
            go.transform.localPosition = new Vector3(0, 0, 9f);
            _overlay = go.AddComponent<SpriteRenderer>();
            _overlay.sprite = White;
            _overlay.sortingOrder = OverlayOrder;
            if (a && a.matMultiply) _overlay.sharedMaterial = a.matMultiply;
            if (GetComponent<ZoneAtmosphere>() == null) gameObject.AddComponent<ZoneAtmosphere>();   // region light, fog and particles
            // the player's lantern: small, so the night stays dark but you always see yourself
            var p = PlayerController.Current;
            if (p != null) _lantern = LightGlow.Attach(p.transform, new Vector2(0, 0.6f), 3.2f, new Color(1f, 0.85f, 0.6f), 0.55f);
        }

        public static Sprite White
        {
            get
            {
                if (_white) return _white;
                var t = new Texture2D(4, 4, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point };
                var px = new Color32[16]; for (int i = 0; i < 16; i++) px[i] = new Color32(255, 255, 255, 255);
                t.SetPixels32(px); t.Apply();
                return _white = Sprite.Create(t, new Rect(0, 0, 4, 4), new Vector2(0.5f, 0.5f), 4);
            }
        }

        void LateUpdate()
        {
            if (_cam == null || _overlay == null) return;
            float h = _cam.orthographicSize * 2f + 2f;
            _overlay.transform.localScale = new Vector3(h * _cam.aspect + 2f, h, 1);
            bool inside = Interior.Current != null;
            bool cave = !inside && WorldInfo.PlayerUnderground;          // underground: always deep dark, torches and your lantern
            Color amb = inside ? new Color(1f, 0.93f, 0.84f) : cave ? new Color(0.36f, 0.34f, 0.44f) * ZoneAtmosphere.Tint
                      : DayNight.Ambient(DayNight.Clock) * ZoneAtmosphere.Tint;
            amb.a = 1f;
            _overlay.color = amb;
            _overlay.enabled = amb != Color.white;
            float dark = inside ? 0.35f : cave ? 0.95f : Mathf.Max(DayNight.Darkness(DayNight.Clock), ZoneAtmosphere.Gloom);
            LightGlow.SetIntensity(dark);
            if (_lantern) _lantern.extra = inside ? 0f : 1f;
        }
    }
}
