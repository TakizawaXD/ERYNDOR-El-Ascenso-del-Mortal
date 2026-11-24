using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>All the game's audio, living across scenes on one "Audio" object:
    /// one-shot effects from a pool of sources (random variant + small pitch/volume change, stereo position from the camera),
    /// the music (MusicDirector: piece per zone with crossfades, night layer, combat, bosses, ducking, jingles) and the
    /// ambient loops (AmbienceDirector). Music and effects volumes are separate and saved (PlayerPrefs).</summary>
    public class Sfx : MonoBehaviour
    {
        static Sfx _i;
        AudioSource[] _pool;
        int _next;
        readonly Dictionary<string, AudioClip[]> _clips = new Dictionary<string, AudioClip[]>();
        readonly Dictionary<string, int> _frameCount = new Dictionary<string, int>();
        int _frame;
        MusicDirector _music;
        AmbienceDirector _amb;

        const string MusicKey = "vol_music", SfxKey = "vol_sfx";
        static bool _loaded;
        static float _sfxVol = 0.8f, _musicVol = 0.6f;

        /// <summary>Effects volume 0..1 (saved).</summary>
        public static float SfxVolume
        {
            get { Load(); return _sfxVol; }
            set { Load(); _sfxVol = Mathf.Clamp01(value); PlayerPrefs.SetFloat(SfxKey, _sfxVol); }
        }

        /// <summary>Music volume 0..1 (saved).</summary>
        public static float MusicVolume
        {
            get { Load(); return _musicVol; }
            set { Load(); _musicVol = Mathf.Clamp01(value); PlayerPrefs.SetFloat(MusicKey, _musicVol); }
        }

        // old field names (WeatherSystem and others read sfxVolume)
        public static float sfxVolume { get => SfxVolume; set => SfxVolume = value; }
        public static float musicVolume { get => MusicVolume; set => MusicVolume = value; }

        static void Load()
        {
            if (_loaded) return;
            _loaded = true;
            _sfxVol = PlayerPrefs.GetFloat(SfxKey, 0.8f);
            _musicVol = PlayerPrefs.GetFloat(MusicKey, 0.6f);
        }

        static Sfx Inst
        {
            get
            {
                if (_i) return _i;
                var go = new GameObject("Audio");
                DontDestroyOnLoad(go);
                _i = go.AddComponent<Sfx>();
                _i._pool = new AudioSource[20];
                for (int k = 0; k < _i._pool.Length; k++)
                {
                    var s = go.AddComponent<AudioSource>();
                    s.playOnAwake = false; s.spatialBlend = 0f;
                    _i._pool[k] = s;
                }
                _i._music = go.AddComponent<MusicDirector>();
                _i._amb = go.AddComponent<AmbienceDirector>();
                return _i;
            }
        }

        /// <summary>Creates the audio object now (scenes call Music(true) on start, tests may call this).</summary>
        public static void Ensure() { var _ = Inst; }
        public static MusicDirector Director => Inst._music;
        public static AmbienceDirector Ambience => Inst._amb;

        // ------------------------------------------------------------ clips
        /// <summary>sfx_name, or a random one of sfx_name_1, sfx_name_2... </summary>
        public static AudioClip Clip(string name)
        {
            var list = Inst.Variants(name);
            return list.Length == 0 ? null : list[list.Length == 1 ? 0 : Random.Range(0, list.Length)];
        }

        AudioClip[] Variants(string name)
        {
            if (_clips.TryGetValue(name, out var c)) return c;
            var a = GameAssets.I;
            var found = new List<AudioClip>();
            if (a != null && a.sfx != null)
            {
                string exact = "sfx_" + name, prefix = exact + "_";
                foreach (var clip in a.sfx)
                {
                    if (clip == null) continue;
                    if (clip.name == exact) found.Add(clip);
                    else if (clip.name.StartsWith(prefix) && clip.name.Length <= prefix.Length + 2 && char.IsDigit(clip.name[clip.name.Length - 1])
                             && char.IsDigit(clip.name[prefix.Length])) found.Add(clip);
                }
            }
            c = found.ToArray();
            _clips[name] = c;
            return c;
        }

        public static bool Has(string name) => Inst.Variants(name).Length > 0;

        /// <summary>How much this kind of sound varies each time (pitch, volume).</summary>
        static Vector2 Variation(string name)
        {
            if (name.StartsWith("step")) return new Vector2(0.08f, 0.18f);
            if (name.StartsWith("swing") || name.StartsWith("heavy_swing") || name.StartsWith("hit") || name.StartsWith("vox_") || name.StartsWith("enemy_"))
                return new Vector2(0.07f, 0.12f);
            if (name == "select" || name == "confirm" || name == "cancel" || name.StartsWith("menu_") || name == "error" || name == "page") return new Vector2(0.01f, 0f);
            if (name.StartsWith("cat_") || name == "chicken" || name == "pig" || name == "cow" || name == "sheep") return new Vector2(0.09f, 0.1f);
            if (name == "coin" || name == "gather" || name == "anvil" || name == "block" || name == "parry") return new Vector2(0.05f, 0.08f);
            return new Vector2(0.03f, 0.06f);
        }

        // ------------------------------------------------------------ playing
        public static void Play(string name, float vol = 1f) => Inst.Emit(name, vol, 0f, 1f);

        /// <summary>A sound at a place in the world: quieter with distance, panned left/right from the camera. Too far = silent.</summary>
        public static void PlayAt(string name, Vector2 pos, float vol = 1f)
        {
            var cam = Camera.main;
            if (cam == null) { Play(name, vol); return; }
            Vector2 c = cam.transform.position;
            float d = Vector2.Distance(c, pos);
            float att = d < 5f ? 1f : Mathf.Clamp01(1f - (d - 5f) / 13f);
            if (att < 0.04f) return;
            float pan = Mathf.Clamp((pos.x - c.x) / 10f, -0.7f, 0.7f);
            Inst.Emit(name, vol * att, pan, 1f);
        }

        void Emit(string name, float vol, float pan, float pitchMul)
        {
            if (string.IsNullOrEmpty(name)) return;
            if (Time.frameCount != _frame) { _frame = Time.frameCount; _frameCount.Clear(); }
            _frameCount.TryGetValue(name, out int same);
            if (same >= 2) return;                                  // five enemies hit by one swing: two sounds are enough
            _frameCount[name] = same + 1;
            var clips = Variants(name);
            if (clips.Length == 0) return;
            var clip = clips[clips.Length == 1 ? 0 : Random.Range(0, clips.Length)];
            var v = Variation(name);
            var s = FreeSource();
            s.clip = clip;
            s.pitch = pitchMul * (1f + Random.Range(-v.x, v.x));
            s.volume = Mathf.Clamp01(vol * (1f - Random.Range(0f, v.y))) * SfxVolume;
            s.panStereo = pan;
            s.Play();
        }

        AudioSource FreeSource()
        {
            for (int k = 0; k < _pool.Length; k++)
            {
                var s = _pool[(_next + k) % _pool.Length];
                if (!s.isPlaying) { _next = (_next + k + 1) % _pool.Length; return s; }
            }
            // all busy: steal the one that has played the longest (relative to its length)
            AudioSource best = _pool[0]; float most = -1;
            foreach (var s in _pool)
            {
                float p = s.clip ? s.time / Mathf.Max(0.01f, s.clip.length) : 1f;
                if (p > most) { most = p; best = s; }
            }
            return best;
        }

        /// <summary>Effects volume changed: sounds already playing follow (used by the pause options).</summary>
        public static void ApplyVolumes()
        {
            if (_i == null) return;
            foreach (var s in _i._pool) if (s.isPlaying) s.volume = Mathf.Min(s.volume, SfxVolume);
        }

        // ------------------------------------------------------------ context-aware effects
        /// <summary>Footstep that matches the ground under pos (grass, dirt, stone, wood, sand, snow, water, mud, ash).</summary>
        public static void Step(Vector2 pos, float vol = 0.5f)
        {
            string surf = Surface(pos);
            Inst.Emit(Has("step_" + surf) ? "step_" + surf : "step", vol, 0f, 1f);
        }

        public static string Surface(Vector2 pos)
        {
            var room = Interior.Current;
            if (room != null)
                return room.template == "capilla" || room.template == "biblioteca" || room.template == "cuartel" ? "stone" : "wood";
            var wi = WorldInfo.Current;
            if (wi == null || wi.terrainRows == null) return "grass";
            int x = Mathf.FloorToInt(pos.x), row = wi.height - 1 - Mathf.FloorToInt(pos.y);
            if (row < 0 || row >= wi.terrainRows.Length || x < 0 || x >= wi.terrainRows[row].Length) return "grass";
            char t = wi.terrainRows[row][x];
            char region = wi.RegionAt(pos);
            switch (t)
            {
                case '_': return region == 'f' || region == 'j' ? "sand" : region == 'e' ? "snow" : "dirt";
                case 'd': return "sand";
                case 'n': case 'C': return "snow";
                case 'a': case 'k': case 'L': return "ash";
                case 's': case 'v': return "mud";
                case 'F': return "dirt";
                case 'p': case '#': return "stone";
                case '=': case 'H': case 'D': return "wood";
                case 'w': case 'O': return "water";
                case 'c': return "stone";
            }
            if (region == 'e') return "snow";
            if (region == 'd') return "mud";
            if (region == 'g') return "ash";
            return "grass";
        }

        /// <summary>The whoosh of a weapon kind (light blades, thrusts, heavy weapons).</summary>
        public static string SwingFor(WeaponKind k, bool heavy = false)
        {
            switch (k)
            {
                case WeaponKind.Dagger: case WeaponKind.Katana: return heavy ? "swing" : "swing_light";
                case WeaponKind.Rapier: case WeaponKind.Spear: return heavy ? "swing" : "swing_thrust";
                case WeaponKind.Greatsword: case WeaponKind.Axe: case WeaponKind.Hammer: return "heavy_swing";
            }
            return heavy ? "heavy_swing" : "swing";
        }

        /// <summary>Impact sound: by element, critical, the weapon the player swings, or a body blow when the player is hit.</summary>
        public static string HitFor(DamageInfo d, Health victim)
        {
            if (victim != null && victim.team == Team.Player) return "hit_flesh";
            if (d.crit) return "hit_crit";
            switch (d.element)
            {
                case Element.Fire: return "hit_fire";
                case Element.Frost: return "hit_frost";
                case Element.Venom: return "hit_venom";
                case Element.Holy: return "hit_holy";
            }
            if (d.source == Team.Player && !d.ranged && GameManager.State != null)
            {
                var w = GameManager.State.Weapon;
                if (w != null)
                    switch (w.kind)
                    {
                        case WeaponKind.Hammer: case WeaponKind.Staff: return "hit_blunt";
                        case WeaponKind.Rapier: case WeaponKind.Spear: case WeaponKind.Dagger: return "hit_pierce";
                        default: return "hit_blade";
                    }
            }
            if (d.ranged) return "hit_pierce";
            return "hit";
        }

        /// <summary>Enemy voice by species: alert, attack, hurt, die.</summary>
        public static void Voice(EnemyController e, string act, float vol = 0.8f)
        {
            if (e == null) return;
            string sp = e.kind == EnemyKind.Demon ? "demon" : e.kind == EnemyKind.BloodMonster ? "blood" : "orc";
            float pitch = e.isBoss || e.rank == EnemyRank.Champion ? 0.8f : e.rank == EnemyRank.Elite ? 0.9f : 1f;
            string n = "vox_" + sp + "_" + act;
            var cam = Camera.main;
            Vector2 pos = e.transform.position;
            float att = 1f, pan = 0f;
            if (cam != null)
            {
                Vector2 c = cam.transform.position; float d = Vector2.Distance(c, pos);
                att = d < 5f ? 1f : Mathf.Clamp01(1f - (d - 5f) / 13f);
                pan = Mathf.Clamp((pos.x - c.x) / 10f, -0.7f, 0.7f);
            }
            if (att < 0.04f) return;
            Inst.Emit(n, vol * att, pan, pitch);
        }

        /// <summary>Farm animals and cats: chicken, pig, cow, sheep, cat (meow).</summary>
        public static string AnimalSound(string species)
        {
            if (string.IsNullOrEmpty(species)) return "select";
            if (species.StartsWith("cat")) return "cat_meow";
            return species;
        }

        // ------------------------------------------------------------ music API
        /// <summary>false: music fades out (game over / victory screens); true: the director picks the piece again.</summary>
        public static void Music(bool on) => Inst._music.SetOn(on);

        /// <summary>Boss battle theme while an arena is sealed (each boss has its own); back to the zone music afterwards.</summary>
        public static void BossMusic(bool on) => Inst._music.SetBoss(on);

        public static bool BossMusicPlaying => _i != null && (_i._music.BossOn || (_i._music.Current != null && _i._music.Current.StartsWith("boss")));

        /// <summary>Short fanfare (victory, defeat, levelup, discover): the music ducks under it.</summary>
        public static void Jingle(string name) => Inst._music.Jingle(name);

        /// <summary>Id of the piece now playing (menu, region_a, city_valle, int_posada, combat, boss_K...), null when silent.</summary>
        public static string CurrentTrack => _i != null ? _i._music.Current : null;
    }
}
