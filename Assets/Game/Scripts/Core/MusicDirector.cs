using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace WoodsGame
{
    /// <summary>Chooses the piece for where you are and what is happening, and crossfades between pieces:
    /// title / class select, each region of the world (day piece + its night layer, crossfaded in sync by the darkness),
    /// each town, interiors by kind, the camp, combat when enemies chase you nearby (elite version for elites, champions and
    /// bosses outside arenas), each boss's own theme while its arena is sealed. Menus, conversations and pause duck the music;
    /// jingles duck it further. A piece left for a short while resumes where it was.</summary>
    public class MusicDirector : MonoBehaviour
    {
        class Deck
        {
            public AudioSource intro, day, night;
            public string id;
            public float vol, target, fadeSpeed = 1f, nightMix;
            public bool hasNight;
        }

        readonly Deck[] _decks = new Deck[3];
        readonly Dictionary<string, (int samples, float at)> _resume = new Dictionary<string, (int, float)>();
        readonly Dictionary<string, AudioClip> _clipCache = new Dictionary<string, AudioClip>();
        AudioSource _jingle;
        bool _on = true, _boss;
        float _duck = 1f, _jingleDuckUntil, _combatUntil, _regionSince, _nextScan;
        bool _combat, _elite;
        string _region, _regionCandidate, _forced;
        Deck _cur;

        public string Current => _cur != null && _cur.target > 0 ? _cur.id : null;
        /// <summary>Final volume of the current piece (music volume × ducking × fade), for tests.</summary>
        public float CurrentVolume => _cur != null && _cur.day != null ? Mathf.Max(_cur.day.volume, _cur.night != null ? _cur.night.volume : 0, _cur.intro.volume) : 0f;
        public float Duck => _duck;
        /// <summary>0 = day piece only, 1 = night layer only (crossfaded by the darkness of the sky).</summary>
        public float NightLayer => _cur != null && _cur.hasNight ? _cur.nightMix : 0f;
        public bool NightLayerInSync => _cur == null || !_cur.hasNight || !_cur.night.isPlaying || Mathf.Abs(_cur.day.timeSamples - _cur.night.timeSamples) <= 4096;
        public bool InCombat => _combat;
        /// <summary>Tests / cutscenes: force a piece id (null = automatic).</summary>
        public static string Force { get; set; }

        void Awake()
        {
            for (int k = 0; k < _decks.Length; k++)
            {
                var d = new Deck
                {
                    intro = gameObject.AddComponent<AudioSource>(),
                    day = gameObject.AddComponent<AudioSource>(),
                    night = gameObject.AddComponent<AudioSource>()
                };
                foreach (var s in new[] { d.intro, d.day, d.night }) { s.playOnAwake = false; s.volume = 0; s.priority = 0; s.ignoreListenerPause = true; }
                d.day.loop = true; d.night.loop = true;
                _decks[k] = d;
            }
            _jingle = gameObject.AddComponent<AudioSource>();
            _jingle.playOnAwake = false; _jingle.priority = 0; _jingle.ignoreListenerPause = true;
        }

        public void SetOn(bool on) { _on = on; }
        public void SetBoss(bool on) { _boss = on; _nextScan = 0; }
        public bool BossOn => _on && (_boss || BossArena.Fighting != null);

        public void Jingle(string name)
        {
            var c = MusicClip("jingle_" + name);
            if (c == null) { Sfx.Play(name == "defeat" ? "gameover" : name); return; }
            _jingle.clip = c; _jingle.volume = Mathf.Clamp01(Sfx.MusicVolume * 1.1f + 0.15f); _jingle.Play();
            _jingleDuckUntil = Time.unscaledTime + c.length * 0.9f;
        }

        AudioClip MusicClip(string name)
        {
            if (_clipCache.TryGetValue(name, out var c)) return c;
            var a = GameAssets.I;
            c = a != null ? a.MusicClip(name) : null;
            if (c == null && name == "music_boss_loop" && BossAssets.I != null) c = BossAssets.I.bossMusic;
            _clipCache[name] = c;
            return c;
        }

        bool HasPiece(string id) => MusicClip("music_" + id + "_loop") != null;

        // ------------------------------------------------------------ what should play
        string Desired()
        {
            if (!string.IsNullOrEmpty(Force)) return Force;
            if (!_on) return null;
            var scene = SceneManager.GetActiveScene().name;
            if (scene == GameManager.MenuScene)
            {
                var cs = FindAnyObjectByType<ClassSelect>();
                return cs != null && cs.gameObject.activeInHierarchy ? "classselect" : "menu";
            }
            var p = PlayerController.Current;
            if (_boss || BossArena.Fighting != null)
            {
                var b = BossArena.Fighting != null ? BossArena.Fighting.boss : null;
                string id = b != null && !string.IsNullOrEmpty(b.bossFlag) ? b.bossFlag : "boss";   // boss_K, boss_Q, boss_B, boss_I, boss_F
                return HasPiece(id) ? id : HasPiece("combat_elite") ? "combat_elite" : null;
            }
            ScanCombat(p);
            if (_combat && p != null && !p.health.IsDead) return _elite ? "combat_elite" : "combat";
            var room = Interior.Current;
            if (room != null) return InteriorPiece(room.template);
            if (p != null && Campfire.Near(p.transform.position, 4.5f) != null) return "camp";
            var wi = WorldInfo.Current;
            if (wi == null) return _region ?? "region_a";
            var town = p != null ? wi.TownAt(p.transform.position) : null;          // one map: towns are places inside it
            if (wi.kind == "city" || town != null)
            {
                string id = "city_" + (town != null ? town.id : wi.mapId).Replace("City_", "").ToLowerInvariant();
                return HasPiece(id) ? id : "city_valle";
            }
            char r = p != null ? wi.RegionAt(p.transform.position) : '\0';
            r = r == 'q' || r == 'u' || r == 'v' || r == 'B' ? 'l' : r == 'r' || r == 'w' || r == 'y' ? 'm' : r == 's' || r == 'x' ? 'k' : r == 'z' ? 'n' : r == 't' || r == 'A' ? 'p' : r;     // generated caves borrow the catacombs' pieces
            if (r == '\0') r = wi.mapId == "Zone_MonteCeniza" ? 'g' : (_region != null ? _region[_region.Length - 1] : 'a');
            string cand = "region_" + r;
            if (!HasPiece(cand)) cand = "region_a";
            // a region must hold for a moment before the music changes (walking along a border)
            if (_region == null) { _region = cand; _regionCandidate = cand; }
            else if (cand != _region)
            {
                if (cand != _regionCandidate) { _regionCandidate = cand; _regionSince = Time.unscaledTime; }
                else if (Time.unscaledTime - _regionSince > 1.5f) _region = cand;
            }
            return _region;
        }

        public static string InteriorPiece(string template)
        {
            switch (template)
            {
                case "posada": return "int_posada";
                case "capilla": case "biblioteca": return "int_capilla";
                case "herreria": case "cuartel": return "int_herreria";
                default: return "int_casa";
            }
        }

        void ScanCombat(PlayerController p)
        {
            if (Time.unscaledTime < _nextScan) return;
            _nextScan = Time.unscaledTime + 0.25f;
            bool found = false, elite = false;
            if (p != null && !p.health.IsDead && Interior.Current == null)
            {
                Vector2 pp = p.transform.position;
                foreach (var e in EnemyController.Active)
                {
                    if (e == null || e.ally || e.health == null || e.health.IsDead || !e.Engaged || e.Asleep || e.Hidden) continue;
                    if (Vector2.Distance(e.transform.position, pp) > 11f) continue;
                    found = true;
                    if (e.rank != EnemyRank.Normal || e.isBoss) elite = true;
                }
            }
            if (found) { _combatUntil = Time.unscaledTime + 4f; _combat = true; _elite |= elite; }
            else if (Time.unscaledTime > _combatUntil) { _combat = false; _elite = false; }
        }

        // ------------------------------------------------------------ decks
        void Switch(string id)
        {
            if (_cur != null && _cur.id == id && _cur.target > 0) return;
            bool toCombat = id != null && (id.StartsWith("combat") || id.StartsWith("boss"));
            bool fromCombat = _cur != null && _cur.id != null && (_cur.id.StartsWith("combat") || _cur.id.StartsWith("boss"));
            float fadeIn = toCombat ? 1.6f : fromCombat ? 0.35f : id != null && (id.StartsWith("int_") || id == "camp") ? 0.9f : 0.5f;
            float fadeOut = toCombat ? 1.2f : 0.45f;
            foreach (var d in _decks) if (d != _cur || id == null) { d.target = 0; d.fadeSpeed = fadeOut; }
            if (_cur != null) { _cur.target = 0; _cur.fadeSpeed = fadeOut; }
            if (id == null) { _cur = null; return; }

            Deck deck = null;
            foreach (var d in _decks) if (d.id == id && d.vol > 0.01f) deck = d;      // still fading out: bring it back
            if (deck == null)
            {
                deck = _decks[0];
                foreach (var d in _decks) if (d.vol < deck.vol) deck = d;
                Load(deck, id);
            }
            deck.target = 1; deck.fadeSpeed = fadeIn;
            _cur = deck;
        }

        void Load(Deck d, string id)
        {
            Remember(d);
            d.intro.Stop(); d.day.Stop(); d.night.Stop();
            d.id = id; d.vol = 0;
            var loop = MusicClip("music_" + id + "_loop");
            var night = MusicClip("music_" + id + "_night");
            var intro = MusicClip("music_" + id + "_intro");
            d.day.clip = loop; d.night.clip = night; d.hasNight = night != null;
            d.nightMix = NightTarget(id, d.hasNight);
            if (loop == null) return;
            bool canResume = !id.StartsWith("combat") && !id.StartsWith("boss");
            if (canResume && _resume.TryGetValue(id, out var r) && Time.unscaledTime - r.at < 90f && r.samples < loop.samples)
            {
                d.day.timeSamples = r.samples; d.day.Play();
                if (d.hasNight) { d.night.timeSamples = r.samples; d.night.Play(); }
                return;
            }
            if (intro != null)
            {
                d.intro.clip = intro; d.intro.Play();
                double start = AudioSettings.dspTime + (double)intro.samples / intro.frequency;
                d.day.timeSamples = 0; d.day.PlayScheduled(start);
                if (d.hasNight) { d.night.timeSamples = 0; d.night.PlayScheduled(start); }
            }
            else
            {
                d.day.timeSamples = 0; d.day.Play();
                if (d.hasNight) { d.night.timeSamples = 0; d.night.Play(); }
            }
        }

        void Remember(Deck d)
        {
            if (string.IsNullOrEmpty(d.id) || d.day.clip == null || !d.day.isPlaying) return;
            _resume[d.id] = (d.day.timeSamples, Time.unscaledTime);
        }

        static float NightTarget(string id, bool hasNight)
        {
            if (!hasNight || DayNight.Current == null) return 0f;
            float dark = DayNight.Darkness(DayNight.Clock);
            return Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.25f, 0.75f, dark));
        }

        void Update()
        {
            float dt = Time.unscaledDeltaTime;
            Switch(Desired());

            // ducking: pause, open panels and conversations; jingles duck harder
            bool menus = GameManager.Paused || WorldUI.PanelOpen || UIRoot.DialogOpen;
            float duckTarget = Time.unscaledTime < _jingleDuckUntil ? 0.15f : menus ? 0.45f : 1f;
            _duck = Mathf.MoveTowards(_duck, duckTarget, dt * (duckTarget < _duck ? 3f : 0.8f));
            float master = Sfx.MusicVolume * _duck;
            if (_jingle.isPlaying) _jingle.volume = Mathf.Clamp01(Sfx.MusicVolume * 1.1f + 0.15f) * (Sfx.MusicVolume > 0.001f ? 1f : 0f);

            foreach (var d in _decks)
            {
                d.vol = Mathf.MoveTowards(d.vol, d.target, dt / Mathf.Max(0.05f, d.fadeSpeed));
                if (d.hasNight) d.nightMix = Mathf.MoveTowards(d.nightMix, NightTarget(d.id, true), dt / 6f);
                float v = d.vol * d.vol * (3f - 2f * d.vol);          // smooth fade curve
                float dayG = d.hasNight ? Mathf.Cos(d.nightMix * Mathf.PI * 0.5f) : 1f;
                float nightG = d.hasNight ? Mathf.Sin(d.nightMix * Mathf.PI * 0.5f) : 0f;
                d.day.volume = master * v * dayG;
                d.night.volume = master * v * nightG;
                d.intro.volume = master * v;
                if (d.hasNight && d.day.isPlaying && d.night.isPlaying && Mathf.Abs(d.day.timeSamples - d.night.timeSamples) > 2048)
                    d.night.timeSamples = d.day.timeSamples;            // keep the night layer locked to the day piece
                if (d.vol <= 0f && d.target <= 0f && (d.day.isPlaying || d.intro.isPlaying))
                {
                    Remember(d);
                    d.intro.Stop(); d.day.Stop(); d.night.Stop();
                }
            }
        }
    }
}
