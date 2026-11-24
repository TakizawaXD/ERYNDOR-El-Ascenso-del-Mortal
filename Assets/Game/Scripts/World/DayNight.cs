using System;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>World clock. Day = 06:00-18:00, night = 18:00-06:00; each half lasts 30 real minutes
    /// (0.4 game minutes per real second, one game hour = 2.5 real minutes). Stored in the save (PlayerState.clock/day).</summary>
    public class DayNight : MonoBehaviour
    {
        public const float RealMinutesPerHalf = 30f;
        public const float GameMinutesPerSecond = 720f / (RealMinutesPerHalf * 60f);   // 0.4
        public const int DawnHour = 6, DuskHour = 18;

        public static DayNight Current { get; private set; }
        /// <summary>Fired with true when night falls and false when the sun rises.</summary>
        public static event Action<bool> PhaseChanged;
        /// <summary>Tests can speed time up.</summary>
        public static float Speed = 1f;

        static PlayerState S => GameManager.State;
        public static float Clock => S.clock;
        public static int Hour => Mathf.FloorToInt(S.clock / 60f) % 24;
        public static int Minute => Mathf.FloorToInt(S.clock) % 60;
        public static bool IsNight => IsNightAt(S.clock);
        public static bool IsNightAt(float clock) => clock >= DuskHour * 60 || clock < DawnHour * 60;
        public static string TimeText => $"{Hour:00}:{Minute:00}";
        /// <summary>Real seconds until the next dawn/dusk.</summary>
        public static float SecondsToChange
        {
            get
            {
                float target = IsNight ? (S.clock >= DuskHour * 60 ? 1440 + DawnHour * 60 : DawnHour * 60) : DuskHour * 60;
                return (target - S.clock) / GameMinutesPerSecond;
            }
        }

        bool _night;

        void Awake() { Current = this; _night = IsNight; }
        void OnDestroy() { if (Current == this) Current = null; }

        void Update()
        {
            if (GameManager.Paused || GameManager.Ended) return;
            Advance(Time.deltaTime * GameMinutesPerSecond * Speed);
        }

        /// <summary>Moves the clock forward (wraps at midnight, counts days) and raises PhaseChanged.</summary>
        public static void Advance(float minutes)
        {
            var s = S;
            s.clock += minutes;
            while (s.clock >= 1440) { s.clock -= 1440; s.day++; }
            Check();
        }

        /// <summary>Jumps to the given hour (sleeping in a bed). Always moves forward.</summary>
        public static void SkipTo(int hour)
        {
            var s = S;
            float target = hour * 60;
            float delta = target - s.clock;
            if (delta <= 0) delta += 1440;
            Advance(delta);
        }

        static void Check()
        {
            var c = Current;
            bool n = IsNight;
            if (c != null && c._night == n) return;
            if (c != null) c._night = n;
            PhaseChanged?.Invoke(n);
            if (c != null) UIRoot.TitleCard(n ? "CAE LA NOCHE" : $"AMANECE · DÍA {S.day}", n ? "LAS CRIATURAS DE LA OSCURIDAD DESPIERTAN" : "LOS ESPECTROS HUYEN DEL SOL");
        }

        /// <summary>Ambient light multiplier for the current time (white at noon, deep blue at midnight, warm at dawn/dusk).</summary>
        public static Color Ambient(float clock)
        {
            float h = clock / 60f;
            Color night = new Color(0.30f, 0.36f, 0.62f), dawn = new Color(1f, 0.78f, 0.66f), day = Color.white, dusk = new Color(1f, 0.70f, 0.50f);
            if (h < 5f) return night;
            if (h < 6f) return Color.Lerp(night, dawn, h - 5f);
            if (h < 7.5f) return Color.Lerp(dawn, day, (h - 6f) / 1.5f);
            if (h < 16.5f) return day;
            if (h < 18f) return Color.Lerp(day, dusk, (h - 16.5f) / 1.5f);
            if (h < 19.5f) return Color.Lerp(dusk, night, (h - 18f) / 1.5f);
            return night;
        }

        /// <summary>0 at day, 1 at full night: how strongly lamps and windows glow.</summary>
        public static float Darkness(float clock)
        {
            var a = Ambient(clock);
            return Mathf.Clamp01((1f - (a.r + a.g + a.b) / 3f) / 0.55f);
        }
    }
}
