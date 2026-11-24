using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace WoodsGame
{
    /// <summary>Ambient loops mixed by place and time: birds by day and crickets by night, wind (strong on the peaks, dry in
    /// the desert), waves on the coast and in the port, the lake, lava on Monte Ceniza, frogs and bubbles in the swamp, the
    /// drone of the corrupted forest, the murmur of towns, and a crackling hearth in houses, the inn, the smithy and by camps.
    /// Rain is WeatherSystem's own. Follows the effects volume.</summary>
    public class AmbienceDirector : MonoBehaviour
    {
        static readonly string[] Layers = { "wind", "wind_strong", "desert", "birds", "crickets", "waves", "lake", "lava", "swamp", "fire", "corrupt", "town" };
        readonly Dictionary<string, AudioSource> _src = new Dictionary<string, AudioSource>();
        readonly Dictionary<string, float> _target = new Dictionary<string, float>();
        readonly Dictionary<string, float> _vol = new Dictionary<string, float>();
        float _next;

        public float Level(string layer) => _vol.TryGetValue(layer, out var v) ? v : 0f;

        AudioSource Src(string layer)
        {
            if (_src.TryGetValue(layer, out var s)) return s;
            var a = GameAssets.I;
            var clip = a != null ? a.AmbienceClip("amb_" + layer) : null;
            if (clip == null) { _src[layer] = null; return null; }
            s = gameObject.AddComponent<AudioSource>();
            s.clip = clip; s.loop = true; s.playOnAwake = false; s.volume = 0; s.priority = 64;
            _src[layer] = s;
            return s;
        }

        void Compute()
        {
            foreach (var l in Layers) _target[l] = 0f;
            if (SceneManager.GetActiveScene().name == GameManager.MenuScene) { _target["birds"] = 0.35f; _target["wind"] = 0.3f; return; }
            var p = PlayerController.Current;
            if (p == null) return;
            float dark = DayNight.Current != null ? DayNight.Darkness(DayNight.Clock) : 0f;
            float day = 1f - Mathf.SmoothStep(0, 1, Mathf.InverseLerp(0.3f, 0.7f, dark));
            float night = 1f - day;
            var room = Interior.Current;
            if (room != null)
            {
                switch (room.template)
                {
                    case "posada": case "casa": case "cabana": _target["fire"] = 0.55f; break;
                    case "herreria": _target["fire"] = 0.8f; break;
                }
                _target["crickets"] = night * 0.12f;
                return;
            }
            Vector2 pos = p.transform.position;
            _target["birds"] = day * 0.55f; _target["crickets"] = night * 0.55f; _target["wind"] = 0.25f;
            if (Campfire.Near(pos, 5f) != null) _target["fire"] = 0.7f;
            var wi = WorldInfo.Current;
            if (wi == null) return;
            var town = wi.TownAt(pos);
            if (wi.kind == "city" || town != null)
            {
                _target["town"] = 0.25f + 0.35f * day;
                _target["birds"] *= 0.6f;
                if ((town != null ? town.id : wi.mapId) == "City_Puerto") _target["waves"] = 0.6f;
                return;
            }
            if (wi.Underground(pos))                     // caves: no birds, no crickets, a low draught
            {
                char cr = wi.RegionAt(pos);
                _target["birds"] = 0; _target["crickets"] = 0; _target["wind"] = 0.12f;
                if (cr == 'p' || cr == 't') _target["corrupt"] = 0.35f;
                if (cr == 'r') _target["wind_strong"] = 0.2f;
                return;
            }
            char r = wi.RegionAt(pos);
            if (r == '\0' && wi.mapId == "Zone_MonteCeniza") r = 'g';
            switch (r)
            {
                case 'b': _target["birds"] = day * 0.85f; _target["wind"] = 0.2f; break;
                case 'c': _target["lake"] = 0.65f; break;
                case 'd': _target["swamp"] = 0.8f; _target["birds"] = day * 0.15f; _target["crickets"] = night * 0.35f; _target["wind"] = 0.1f; break;
                case 'e': _target["wind_strong"] = 0.75f; _target["wind"] = 0.3f; _target["birds"] = 0; _target["crickets"] = 0; break;
                case 'f': _target["desert"] = 0.75f; _target["wind"] = 0; _target["birds"] = 0; _target["crickets"] = night * 0.3f; break;
                case 'g': _target["lava"] = 0.7f; _target["wind"] = 0.4f; _target["birds"] = 0; _target["crickets"] = 0; break;
                case 'h': _target["corrupt"] = 0.75f; _target["birds"] = 0; _target["crickets"] = night * 0.15f; break;
                case 'j': _target["waves"] = 0.75f; _target["wind"] = 0.3f; _target["birds"] = day * 0.3f; break;
            }
            if (BossArena.Fighting != null) foreach (var l in Layers) _target[l] *= 0.4f;
        }

        void Update()
        {
            if (Time.unscaledTime >= _next) { _next = Time.unscaledTime + 0.4f; Compute(); }
            float dt = Time.unscaledDeltaTime;
            float master = Sfx.SfxVolume * (GameManager.Paused ? 0.5f : 1f);
            foreach (var l in Layers)
            {
                _target.TryGetValue(l, out float t);
                _vol.TryGetValue(l, out float v);
                v = Mathf.MoveTowards(v, t, dt * 0.35f);
                _vol[l] = v;
                if (v <= 0.001f && !_src.ContainsKey(l)) continue;
                var s = Src(l);
                if (s == null) continue;
                s.volume = v * master;
                if (v > 0.001f && !s.isPlaying) { s.time = Random.Range(0f, s.clip.length * 0.9f); s.Play(); }
                else if (v <= 0.001f && s.isPlaying) s.Stop();
            }
        }
    }
}
