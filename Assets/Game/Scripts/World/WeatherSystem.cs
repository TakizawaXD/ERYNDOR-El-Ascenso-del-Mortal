using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Weather for the open world: wind (drives the Woods/SpriteWind vegetation shader through global properties),
    /// rain showers that come and go on their own (streaks, splashes on the ground, a darker sky, a rain loop) and glowing green
    /// spores drifting over the grass. Lives on the world's Level object; built by GameBuilder.BuildWeather.
    /// Everything follows the camera, so cost is constant however big the map is. Hidden inside houses.</summary>
    public class WeatherSystem : MonoBehaviour
    {
        public static WeatherSystem Current { get; private set; }
        /// <summary>Tests switch the automatic rain cycle off to drive it by hand.</summary>
        public static bool AutoCycle = true;

        [Header("Art (set by the builder)")]
        public Sprite drop;
        public Sprite[] splash;
        public AudioClip rainLoop;

        [Header("Cycle (real seconds)")]
        public Vector2 clearTime = new Vector2(150, 330);
        public Vector2 rainTime = new Vector2(70, 160);
        public float fadeTime = 7f;

        [Header("Look")]
        public int maxDrops = 320;
        public int maxSpores = 34;
        public Color rainTint = new Color(0.72f, 0.77f, 0.88f);
        public float baseWind = 1f;

        public const int RainOrder = DayNightLighting.OverlayOrder - 2;       // under the night tint -> rain darkens at night
        public const int SporeOrder = DayNightLighting.OverlayOrder + 2;      // additive glow above the night tint

        static readonly int IdStrength = Shader.PropertyToID("_WindStrength"), IdGust = Shader.PropertyToID("_WindGust"),
            IdDir = Shader.PropertyToID("_WindDir");

        /// <summary>0 = clear, 1 = full shower.</summary>
        public float Intensity { get; private set; }
        public bool Raining => _target > 0f;
        public float Wind { get; private set; }
        public float Gust { get; private set; }
        public int ActiveDrops { get; private set; }
        public int ActiveSplashes { get; private set; }
        public int VisibleSpores { get; private set; }

        float _target, _timer, _fadeSpeed = 1f / 7f, _flash, _nextFlash;
        float _windDir = 1f;
        Camera _cam;
        Transform _root;
        SpriteRenderer _tint, _flashSr;
        AudioSource _audio;

        /// <summary>What falls in a shower depends on the biome: rain on the plains and forests, snow in Valgrimm,
        /// a sandstorm in the desert, ash and embers over Drakmor and the Forbidden Tower lands.</summary>
        public enum Precip { Rain, Snow, Sand, Ash }
        public Precip Kind { get; private set; }
        public static Precip KindFor(char region) =>
            region == 'e' ? Precip.Snow : region == 'f' ? Precip.Sand : region == 'g' || region == 'h' ? Precip.Ash : Precip.Rain;

        struct Drop { public Transform t; public SpriteRenderer sr; public Vector2 pos; public float groundY, speed, phase; public bool live; public Precip kind; }
        struct Splash { public SpriteRenderer sr; public float age; }
        struct Spore { public Transform t; public SpriteRenderer sr; public Vector2 pos, vel; public float phase, size; }
        Drop[] _drops;
        readonly List<Splash> _splashes = new List<Splash>();
        readonly Queue<SpriteRenderer> _splashPool = new Queue<SpriteRenderer>();
        Spore[] _spores;

        void Awake()
        {
            Current = this;
            _timer = Random.Range(clearTime.x, clearTime.y) * 0.5f;    // first shower comes a bit sooner
            _windDir = Random.value < 0.5f ? -1f : 1f;
        }

        void OnDestroy()
        {
            if (Current == this) Current = null;
            Shader.SetGlobalFloat(IdStrength, 0f); Shader.SetGlobalFloat(IdGust, 0f);
        }

        void Start()
        {
            _cam = Camera.main;
            _root = new GameObject("WeatherFx").transform;
            _root.SetParent(transform, false);
            var a = GameAssets.I;

            _drops = new Drop[maxDrops];
            for (int i = 0; i < maxDrops; i++)
            {
                var go = new GameObject("drop");
                go.transform.SetParent(_root, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = drop; sr.sortingOrder = RainOrder; sr.enabled = false;
                _drops[i] = new Drop { t = go.transform, sr = sr };
            }
            for (int i = 0; i < 90; i++) _splashPool.Enqueue(NewSplash());

            if (_cam)
            {
                // the rain darkens the world (multiply), the lightning brightens it (additive)
                _tint = Overlay("RainTint", a ? a.matMultiply : null, RainOrder + 1);
                _flashSr = Overlay("Lightning", a ? a.matAdditive : null, DayNightLighting.OverlayOrder + 1);
            }

            _spores = new Spore[maxSpores];
            for (int i = 0; i < maxSpores; i++)
            {
                var go = new GameObject("spore");
                go.transform.SetParent(_root, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = a ? a.lightSprite : null; sr.sortingOrder = SporeOrder; sr.enabled = false;
                if (a && a.matAdditive) sr.sharedMaterial = a.matAdditive;
                _spores[i] = new Spore { t = go.transform, sr = sr, phase = Random.value * 50f, size = Random.Range(0.16f, 0.3f) };
                RespawnSpore(ref _spores[i], true);
            }

            _audio = gameObject.AddComponent<AudioSource>();
            _audio.clip = rainLoop; _audio.loop = true; _audio.playOnAwake = false; _audio.volume = 0f; _audio.spatialBlend = 0f;
        }

        SpriteRenderer Overlay(string name, Material m, int order)
        {
            var go = new GameObject(name);
            go.transform.SetParent(_cam.transform, false);
            go.transform.localPosition = new Vector3(0, 0, 9f);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = DayNightLighting.White; sr.sortingOrder = order; sr.enabled = false;
            if (m) sr.sharedMaterial = m;
            return sr;
        }

        SpriteRenderer NewSplash()
        {
            var go = new GameObject("splash");
            go.transform.SetParent(_root, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sortingOrder = RainOrder; sr.enabled = false;
            return sr;
        }

        // ------------------------------------------------------------ control
        /// <summary>Starts or stops a shower (fades over `fade` seconds; 0 = instantly).</summary>
        public void SetRain(bool on, float fade = -1f)
        {
            if (fade < 0) fade = fadeTime;
            _target = on ? 1f : 0f;
            _fadeSpeed = fade <= 0.01f ? 1000f : 1f / fade;
            _timer = on ? Random.Range(rainTime.x, rainTime.y) : Random.Range(clearTime.x, clearTime.y);
            if (on) _nextFlash = Random.Range(12f, 30f);
        }

        // ------------------------------------------------------------ update
        void Update()
        {
            float dt = GameManager.Paused ? 0f : Time.deltaTime;
            float t = Time.time;

            if (AutoCycle && dt > 0f)
            {
                _timer -= dt;
                if (_timer <= 0f) SetRain(!Raining);
            }
            Intensity = Mathf.MoveTowards(Intensity, _target, _fadeSpeed * Mathf.Max(dt, 0f));

            // wind: a steady breeze, slow gusts (stronger in the rain); direction flips now and then between showers
            float g = Mathf.PerlinNoise(t * 0.11f, 3.7f);
            Gust = Mathf.Clamp01((g - 0.45f) * 2.4f) * (0.8f + Intensity * 0.9f);
            Wind = baseWind * (0.75f + 0.25f * Mathf.PerlinNoise(t * 0.05f, 9.1f)) + Intensity * 0.8f;
            if (!Raining && Gust < 0.02f && Random.value < dt * 0.01f) _windDir = -_windDir;
            Shader.SetGlobalFloat(IdStrength, Wind);
            Shader.SetGlobalFloat(IdGust, Gust);
            Shader.SetGlobalFloat(IdDir, _windDir);

            bool inside = Interior.Current != null || WorldInfo.PlayerUnderground;      // caves: no sky
            if (_cam == null) _cam = Camera.main;
            var wiK = WorldInfo.Current;
            if (_cam != null && wiK != null) Kind = KindFor(wiK.RegionAt(_cam.transform.position));
            if (_cam == null) return;
            float h = _cam.orthographicSize, w = h * _cam.aspect;
            Vector2 c = _cam.transform.position;
            var view = new Rect(c.x - w - 1f, c.y - h - 1f, 2 * w + 2f, 2 * h + 3f);

            UpdateRain(dt, inside ? 0f : Intensity, view);
            UpdateSpores(dt, inside, view, t);
            UpdateOverlays(dt, inside, h, w);

            if (_audio && _audio.clip)
            {
                float vol = (inside ? 0.25f : 0.6f) * Intensity * Sfx.sfxVolume * (Kind == Precip.Rain ? 1f : 0f);
                _audio.volume = vol;
                if (vol > 0.001f && !_audio.isPlaying) _audio.Play();
                else if (vol <= 0.001f && _audio.isPlaying) _audio.Stop();
            }
        }

        void UpdateRain(float dt, float k, Rect view)
        {
            int want = Mathf.RoundToInt(maxDrops * k);
            float slant = 0.18f * _windDir * (1f + Gust);
            int live = 0;
            for (int i = 0; i < _drops.Length; i++)
            {
                ref var d = ref _drops[i];
                if (!d.live)
                {
                    if (i >= want) continue;
                    SpawnDrop(ref d, view, true);
                }
                switch (d.kind)
                {
                    case Precip.Rain: d.pos += new Vector2(slant, -1f) * d.speed * dt; break;
                    case Precip.Sand: d.pos += new Vector2(_windDir, -0.14f) * d.speed * dt; break;
                    default:        // snow and ash flutter down, carried by the gusts
                        d.pos += new Vector2(Mathf.Sin(Time.time * 1.3f + d.phase) * 0.6f + _windDir * (0.25f + Gust * 1.2f), -1f) * d.speed * dt;
                        break;
                }
                bool outside = d.pos.x < view.xMin - 2f || d.pos.x > view.xMax + 2f || d.pos.y < view.yMin - 2f;
                if (d.pos.y <= d.groundY || outside)
                {
                    if (!outside && d.kind == Precip.Rain) SpawnSplash(new Vector2(d.pos.x, d.groundY));
                    if (i >= want) { d.live = false; d.sr.enabled = false; continue; }
                    SpawnDrop(ref d, view, false);
                }
                d.t.position = new Vector3(d.pos.x, d.pos.y, 0);
                live++;
            }
            ActiveDrops = live;

            for (int i = _splashes.Count - 1; i >= 0; i--)
            {
                var s = _splashes[i];
                s.age += dt;
                int f = (int)(s.age * 16f);
                if (splash == null || f >= splash.Length) { s.sr.enabled = false; _splashPool.Enqueue(s.sr); _splashes.RemoveAt(i); continue; }
                s.sr.sprite = splash[f];
                _splashes[i] = s;
            }
            ActiveSplashes = _splashes.Count;
        }

        void SpawnDrop(ref Drop d, Rect view, bool anywhere)
        {
            // a drop falls 3-9 units on screen before it "hits" the ground at groundY (top-down: the ground is where it lands)
            float fall = Random.Range(3f, 9f);
            float gx = Random.Range(view.xMin, view.xMax), gy = Random.Range(view.yMin, view.yMax);
            d.groundY = gy;
            d.pos = new Vector2(gx, gy + (anywhere ? Random.Range(0f, fall) : fall));
            d.kind = Kind; d.phase = Random.value * 20f;
            d.live = true;
            d.sr.enabled = true;
            switch (Kind)
            {
                case Precip.Rain:
                    d.speed = Random.Range(17f, 24f); d.sr.sprite = drop; d.t.localScale = Vector3.one;
                    d.sr.color = new Color(1, 1, 1, Random.Range(0.45f, 0.85f));
                    d.t.rotation = Quaternion.Euler(0, 0, -Mathf.Atan(0.18f * _windDir) * Mathf.Rad2Deg);
                    break;
                case Precip.Snow:
                    d.speed = Random.Range(1.2f, 2.6f); d.sr.sprite = DayNightLighting.White; d.t.rotation = Quaternion.identity;
                    float sz = Random.Range(0.07f, 0.16f); d.t.localScale = new Vector3(sz, sz, 1);
                    d.sr.color = new Color(1f, 1f, 1f, Random.Range(0.6f, 0.95f));
                    d.groundY = gy - Random.Range(0f, 3f);
                    break;
                case Precip.Ash:
                    d.speed = Random.Range(0.9f, 2f); d.sr.sprite = DayNightLighting.White; d.t.rotation = Quaternion.Euler(0, 0, Random.Range(0f, 90f));
                    float az = Random.Range(0.06f, 0.13f); d.t.localScale = new Vector3(az, az, 1);
                    d.sr.color = Random.value < 0.18f ? new Color(1f, 0.55f, 0.15f, 0.9f) : new Color(0.35f, 0.32f, 0.33f, Random.Range(0.5f, 0.85f));
                    break;
                default:            // sand: long, low, fast streaks along the wind
                    d.speed = Random.Range(11f, 17f); d.sr.sprite = drop; d.t.localScale = new Vector3(1f, Random.Range(0.8f, 1.4f), 1);
                    d.t.rotation = Quaternion.Euler(0, 0, _windDir > 0 ? 82f : -82f);
                    d.sr.color = new Color(0.98f, 0.82f, 0.55f, Random.Range(0.35f, 0.7f));
                    d.pos = new Vector2(_windDir > 0 ? view.xMin - Random.Range(0f, 3f) : view.xMax + Random.Range(0f, 3f), gy + Random.Range(0f, 2f));
                    if (anywhere) d.pos.x = Random.Range(view.xMin, view.xMax);
                    d.groundY = view.yMin - 5f;
                    break;
            }
        }

        void SpawnSplash(Vector2 at)
        {
            if (splash == null || splash.Length == 0) return;
            if (Random.value > 0.7f) return;
            var sr = _splashPool.Count > 0 ? _splashPool.Dequeue() : NewSplash();
            sr.transform.position = at;
            sr.sprite = splash[0]; sr.enabled = true;
            _splashes.Add(new Splash { sr = sr, age = 0f });
        }

        void UpdateSpores(float dt, bool inside, Rect view, float t)
        {
            // glowing green spores: everywhere green, more at night, fewer while it pours, none in snow / desert / ash
            var wi = WorldInfo.Current;
            char reg = wi != null ? wi.RegionAt(_cam.transform.position) : 'a';
            bool barren = reg == 'e' || reg == 'f' || reg == 'g';
            float night = DayNight.Darkness(DayNight.Clock);
            float k = inside || barren ? 0f : Mathf.Clamp01(0.45f + night * 0.55f - Intensity * 0.35f);
            int want = Mathf.RoundToInt(_spores.Length * k);
            int vis = 0;
            for (int i = 0; i < _spores.Length; i++)
            {
                ref var s = ref _spores[i];
                if (i >= want) { s.sr.enabled = false; continue; }
                if (!view.Contains(s.pos)) RespawnSpore(ref s, false, view);
                s.pos += (s.vel + new Vector2(Mathf.Sin(t * 0.7f + s.phase) * 0.25f + _windDir * Gust * 0.6f, Mathf.Cos(t * 0.9f + s.phase) * 0.12f)) * dt;
                float pulse = 0.55f + 0.45f * Mathf.Sin(t * 2.3f + s.phase * 2f);
                s.sr.enabled = true;
                s.sr.color = new Color(0.55f, 1f, 0.35f, (0.35f + night * 0.45f) * pulse);
                s.t.position = new Vector3(s.pos.x, s.pos.y, 0);
                float sz = s.size * (0.8f + 0.2f * pulse);
                s.t.localScale = new Vector3(sz, sz, 1);
                vis++;
            }
            VisibleSpores = vis;
        }

        void RespawnSpore(ref Spore s, bool first, Rect view = default)
        {
            if (first || view.width <= 0) { s.pos = new Vector2(Random.Range(-15f, 15f), Random.Range(-9f, 9f)) + (_cam ? (Vector2)_cam.transform.position : Vector2.zero); }
            else s.pos = new Vector2(Random.Range(view.xMin, view.xMax), Random.Range(view.yMin, view.yMax));
            s.vel = new Vector2(Random.Range(-0.15f, 0.15f), Random.Range(0.05f, 0.25f));
        }

        void UpdateOverlays(float dt, bool inside, float h, float w)
        {
            float size = h * 2f + 2f;
            if (_tint)
            {
                float k = inside ? 0f : Intensity;
                _tint.enabled = k > 0.001f;
                _tint.transform.localScale = new Vector3(w * 2f + 2f, size, 1);
                var tc = Kind == Precip.Snow ? new Color(0.88f, 0.92f, 1f) : Kind == Precip.Sand ? new Color(1f, 0.84f, 0.62f)
                       : Kind == Precip.Ash ? new Color(0.78f, 0.66f, 0.64f) : rainTint;
                _tint.color = Color.Lerp(Color.white, tc, k);
            }
            if (_flashSr)
            {
                if (!inside && Intensity > 0.8f && dt > 0f && Kind == Precip.Rain)
                {
                    _nextFlash -= dt;
                    if (_nextFlash <= 0f) { _flash = 1f; _nextFlash = Random.Range(14f, 40f); }
                }
                _flash = Mathf.MoveTowards(_flash, 0f, dt * 3.5f);
                // a double flicker: bright, dim, bright, fade
                float f = _flash > 0.75f ? 1f : _flash > 0.6f ? 0.3f : _flash;
                _flashSr.enabled = f > 0.01f;
                _flashSr.transform.localScale = new Vector3(w * 2f + 2f, size, 1);
                _flashSr.color = new Color(0.75f, 0.82f, 1f, 0.35f * f);
            }
        }
    }
}
