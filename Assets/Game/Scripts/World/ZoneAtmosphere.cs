using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Each region has its own air: a light tint (multiplied into DayNightLighting's ambient), low fog banks and
    /// a particle kind (falling leaves, snow, ash and embers, blowing sand, violet wisps, swamp spores...). A boss arena the
    /// player stands in overrides it. Lives on the camera; everything follows the view, so the cost is constant.</summary>
    [RequireComponent(typeof(Camera))]
    public class ZoneAtmosphere : MonoBehaviour
    {
        public enum Motes { None, Leaves, Snow, Ash, Embers, Sand, Wisps, Spores, Motes, Spray, Fireflies }

        public struct Profile
        {
            public string id;
            public Color tint;          // multiply (white = none)
            public Color fog;           // rgb + alpha of the fog banks
            public Motes motes;
            public Color moteColor;
            public int moteCount;
            public float gloom;         // minimum darkness for the light glows (braziers/torches show by day)
        }

        /// <summary>Current tint multiplied into the ambient light.</summary>
        public static Color Tint { get; private set; } = Color.white;
        public static float Gloom { get; private set; }
        public static ZoneAtmosphere Current { get; private set; }
        public Profile Active => _target;
        public string ActiveId => _target.id;
        public int LiveMotes { get { int n = 0; foreach (var m in _motes) if (m.sr.enabled) n++; return n; } }

        Camera _cam;
        Profile _target, _from;
        float _blend = 1f;
        Color _tint = Color.white, _fog = Color.clear;
        float _gloom;
        readonly List<SpriteRenderer> _fogs = new List<SpriteRenderer>();
        struct Mote { public SpriteRenderer sr; public Vector2 pos, vel; public float life, age, size; }
        readonly List<Mote> _motes = new List<Mote>();
        const int MaxMotes = 60;
        float _nextCheck;

        static Color C(float r, float g, float b, float a = 1f) => new Color(r, g, b, a);

        public static Profile ForRegion(char region, string mapId)
        {
            var p = new Profile { id = region.ToString(), tint = Color.white, fog = Color.clear, motes = Motes.None, moteColor = Color.white, moteCount = 0 };
            switch (region)
            {
                case 'a': p.tint = C(1f, 0.98f, 0.93f); p.motes = Motes.Fireflies; p.moteColor = C(0.95f, 1f, 0.55f); p.moteCount = 14; break;
                case 'b': p.tint = C(0.86f, 0.97f, 0.86f); p.fog = C(0.75f, 0.95f, 0.8f, 0.12f); p.motes = Motes.Leaves; p.moteColor = C(0.85f, 0.6f, 0.25f); p.moteCount = 22; break;
                case 'c': p.tint = C(0.88f, 0.95f, 1f); p.fog = C(0.85f, 0.95f, 1f, 0.2f); p.motes = Motes.Motes; p.moteColor = C(0.7f, 0.9f, 1f); p.moteCount = 18; break;
                case 'd': p.tint = C(0.9f, 0.74f, 0.8f); p.fog = C(0.75f, 0.3f, 0.45f, 0.28f); p.motes = Motes.Spores; p.moteColor = C(1f, 0.4f, 0.55f); p.moteCount = 30; p.gloom = 0.2f; break;
                case 'e': p.tint = C(0.86f, 0.92f, 1f); p.fog = C(0.95f, 0.97f, 1f, 0.26f); p.motes = Motes.Snow; p.moteColor = Color.white; p.moteCount = 55; break;
                case 'f': p.tint = C(1f, 0.88f, 0.74f); p.fog = C(1f, 0.8f, 0.55f, 0.16f); p.motes = Motes.Sand; p.moteColor = C(0.95f, 0.75f, 0.5f); p.moteCount = 45; break;
                case 'g': p.tint = C(0.95f, 0.7f, 0.6f); p.fog = C(0.5f, 0.2f, 0.15f, 0.3f); p.motes = Motes.Embers; p.moteColor = C(1f, 0.55f, 0.15f); p.moteCount = 45; p.gloom = 0.3f; break;
                case 'h': p.tint = C(0.7f, 0.6f, 0.9f); p.fog = C(0.45f, 0.25f, 0.7f, 0.3f); p.motes = Motes.Wisps; p.moteColor = C(0.75f, 0.45f, 1f); p.moteCount = 34; p.gloom = 0.35f; break;
                case 'i': p.tint = C(0.97f, 0.96f, 1f); p.motes = Motes.Motes; p.moteColor = C(1f, 0.95f, 0.8f); p.moteCount = 12; break;
                case 'j': p.tint = C(0.94f, 0.98f, 1f); p.fog = C(0.9f, 0.97f, 1f, 0.12f); p.motes = Motes.Spray; p.moteColor = Color.white; p.moteCount = 20; break;
                // the underground (one map: the caves lie right of the overworld): dust in the torchlight, each cave its colour
                case 'k': case 'm': case 's': case 'x': case 'z': p.tint = C(0.92f, 0.9f, 1f); p.fog = C(0.3f, 0.3f, 0.4f, 0.22f); p.motes = Motes.Motes; p.moteColor = C(0.85f, 0.85f, 0.75f); p.moteCount = 20; p.gloom = 0.5f; break;
                case 'l': case 'q': case 'u': case 'v': case 'B': p.tint = C(1f, 0.9f, 0.78f); p.fog = C(0.45f, 0.32f, 0.2f, 0.22f); p.motes = Motes.Motes; p.moteColor = C(0.9f, 0.75f, 0.5f); p.moteCount = 22; p.gloom = 0.5f; break;
                case 'n': case 'o': case 'w': p.tint = C(0.86f, 0.9f, 1f); p.fog = C(0.25f, 0.3f, 0.45f, 0.25f); p.motes = Motes.Wisps; p.moteColor = C(0.6f, 0.75f, 1f); p.moteCount = 16; p.gloom = 0.5f; break;
                case 'p': case 't': case 'A': p.tint = C(1f, 0.78f, 0.8f); p.fog = C(0.5f, 0.12f, 0.18f, 0.26f); p.motes = Motes.Embers; p.moteColor = C(1f, 0.35f, 0.3f); p.moteCount = 22; p.gloom = 0.5f; break;
                case 'r': case 'y': p.tint = C(0.8f, 0.9f, 1.05f); p.fog = C(0.7f, 0.85f, 1f, 0.25f); p.motes = Motes.Snow; p.moteColor = C(0.85f, 0.95f, 1f); p.moteCount = 26; p.gloom = 0.5f; break;
            }
            return p;
        }

        public static Profile ForArena(BossArena a)
        {
            var p = ForRegion('\0', "");
            p.id = "arena:" + a.name; p.tint = a.tint; p.fog = a.fogColor; p.gloom = 0.25f;
            p.moteColor = a.glowColor; p.moteCount = 34;
            p.motes = a.theme == 4 ? Motes.Snow : a.theme == 3 ? Motes.Embers : a.theme == 2 ? Motes.Spores : a.theme == 1 ? Motes.Sand : Motes.Wisps;
            return p;
        }

        void Awake()
        {
            Current = this;
            _cam = GetComponent<Camera>();
            _target = _from = ForRegion('\0', "");
        }

        void OnDestroy() { if (Current == this) { Current = null; Tint = Color.white; Gloom = 0; } }

        void Start()
        {
            var b = BossAssets.I; var a = GameAssets.I;
            for (int i = 0; i < 4; i++)
            {
                var go = new GameObject("Fog" + i);
                go.transform.SetParent(transform, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = b ? b.fog : null;
                sr.sortingOrder = DayNightLighting.OverlayOrder - 6;
                sr.enabled = false;
                _fogs.Add(sr);
            }
            for (int i = 0; i < MaxMotes; i++)
            {
                var go = new GameObject("Mote");
                go.transform.SetParent(transform, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = DayNightLighting.White;
                sr.enabled = false;
                _motes.Add(new Mote { sr = sr });
            }
            _additive = a ? a.matAdditive : null;
            _default = _motes.Count > 0 ? _motes[0].sr.sharedMaterial : null;
            Pick(true);
        }

        Material _additive, _default;

        void Pick(bool snap)
        {
            Profile want;
            var wi = WorldInfo.Current;
            var p = PlayerController.Current;
            if (Interior.Current != null) want = ForRegion('\0', "");
            else if (BossArena.Inside != null) want = ForArena(BossArena.Inside);
            else
            {
                char r = wi != null && p != null ? wi.RegionAt(p.transform.position) : '\0';
                if (r == '\0' && wi != null && wi.regionNames != null && wi.regionNames.Length > 0 && !wi.IsWorld) r = wi.regionNames[0][0];
                want = ForRegion(r, wi != null ? wi.mapId : "");
            }
            if (want.id == _target.id && !snap) return;
            _from = Current == this && !snap ? new Profile { tint = _tint, fog = _fog, gloom = _gloom } : want;
            _target = want; _blend = snap ? 1f : 0f;
        }

        void LateUpdate()
        {
            if (_cam == null) return;
            if (Time.time >= _nextCheck) { _nextCheck = Time.time + 0.5f; Pick(false); }
            _blend = Mathf.MoveTowards(_blend, 1f, Time.deltaTime / 2.5f);
            _tint = Color.Lerp(_from.tint, _target.tint, _blend);
            _fog = Color.Lerp(_from.fog, _target.fog, _blend);
            _gloom = Mathf.Lerp(_from.gloom, _target.gloom, _blend);
            Tint = _tint; Gloom = _gloom;
            float h = _cam.orthographicSize, w = h * _cam.aspect;
            UpdateFog(w, h);
            UpdateMotes(w, h);
        }

        void UpdateFog(float w, float h)
        {
            bool on = _fog.a > 0.01f && Interior.Current == null;
            for (int i = 0; i < _fogs.Count; i++)
            {
                var sr = _fogs[i];
                sr.enabled = on && sr.sprite != null;
                if (!sr.enabled) continue;
                float t = Time.time * 0.04f + i * 0.37f;
                float x = Mathf.Repeat(t + i * 0.5f, 2f) - 1f;
                Vector3 local = new Vector3(x * (w + 6f), -h + 1.5f + i * (h * 0.55f), 10f);
                sr.transform.localPosition = local;
                sr.transform.localScale = new Vector3(3.2f, 2.2f, 1);
                sr.color = new Color(_fog.r, _fog.g, _fog.b, _fog.a * (0.7f + 0.3f * Mathf.Sin(Time.time * 0.3f + i)));
            }
        }

        void UpdateMotes(float w, float h)
        {
            int want = Interior.Current != null ? 0 : Mathf.Min(MaxMotes, Mathf.RoundToInt(_target.moteCount * _blend));
            var kind = _target.motes;
            bool glow = kind == Motes.Embers || kind == Motes.Wisps || kind == Motes.Spores || kind == Motes.Fireflies || kind == Motes.Motes;
            Vector2 cam = transform.position;
            float dt = Time.deltaTime;
            for (int i = 0; i < _motes.Count; i++)
            {
                var m = _motes[i];
                if (i >= want || kind == Motes.None) { if (m.sr.enabled) m.sr.enabled = false; _motes[i] = m; continue; }
                if (!m.sr.enabled || m.age >= m.life || Mathf.Abs(m.pos.x - cam.x) > w + 2 || Mathf.Abs(m.pos.y - cam.y) > h + 2)
                    m = Spawn(m, kind, cam, w, h, glow);
                m.age += dt;
                float t = Time.time + i;
                Vector2 v = m.vel;
                if (kind == Motes.Leaves || kind == Motes.Snow || kind == Motes.Ash) v.x += Mathf.Sin(t * 1.7f) * 0.5f;
                if (kind == Motes.Wisps || kind == Motes.Fireflies || kind == Motes.Motes) v += new Vector2(Mathf.Sin(t * 1.1f), Mathf.Cos(t * 0.9f)) * 0.3f;
                m.pos += v * dt;
                float k = m.age / m.life;
                float a = Mathf.Sin(Mathf.Clamp01(k) * Mathf.PI);
                if (kind == Motes.Fireflies) a *= 0.5f + 0.5f * Mathf.Sin(t * 4f);
                var c = _target.moteColor;
                m.sr.color = new Color(c.r, c.g, c.b, a * (glow ? 0.9f : 0.8f));
                m.sr.transform.position = new Vector3(Mathf.Round(m.pos.x * 16f) / 16f, Mathf.Round(m.pos.y * 16f) / 16f, 0);
                _motes[i] = m;
            }
        }

        Mote Spawn(Mote m, Motes kind, Vector2 cam, float w, float h, bool glow)
        {
            m.sr.enabled = true;
            m.sr.sharedMaterial = glow && _additive ? _additive : _default;
            m.sr.sortingOrder = glow ? DayNightLighting.OverlayOrder + 3 : DayNightLighting.OverlayOrder - 5;
            m.age = 0; m.life = Random.Range(3f, 7f);
            m.pos = cam + new Vector2(Random.Range(-w - 1, w + 1), Random.Range(-h - 1, h + 1));
            float px = 1f / 16f;
            m.size = px;
            switch (kind)
            {
                case Motes.Snow: m.vel = new Vector2(Random.Range(-0.3f, 0.3f), -Random.Range(0.8f, 1.6f)); m.size = px * Random.Range(1, 3); m.pos.y = cam.y + h + 0.5f - Random.value * 2 * h; break;
                case Motes.Ash: m.vel = new Vector2(0.2f, -0.5f); break;
                case Motes.Leaves: m.vel = new Vector2(Random.Range(0.4f, 1.1f), -Random.Range(0.5f, 1.0f)); m.size = px * 2; break;
                case Motes.Embers: m.vel = new Vector2(Random.Range(-0.3f, 0.3f), Random.Range(0.6f, 1.5f)); m.size = px * Random.Range(1, 3); break;
                case Motes.Sand: m.vel = new Vector2(Random.Range(3f, 5.5f), Random.Range(-0.3f, 0.2f)); m.life = Random.Range(1.5f, 3f); break;
                case Motes.Wisps: m.vel = new Vector2(0, Random.Range(0.3f, 0.8f)); m.size = px * 2; break;
                case Motes.Spores: m.vel = new Vector2(Random.Range(-0.2f, 0.2f), Random.Range(0.15f, 0.45f)); m.size = px * Random.Range(1, 3); break;
                case Motes.Spray: m.vel = new Vector2(Random.Range(0.6f, 1.4f), Random.Range(-0.1f, 0.3f)); break;
                default: m.vel = Vector2.zero; break;
            }
            m.sr.transform.localScale = new Vector3(m.size * (kind == Motes.Leaves || kind == Motes.Sand ? 2f : 1f), m.size, 1);
            return m;
        }
    }
}
