using UnityEngine;

namespace WoodsGame
{
    /// <summary>Music and effects volume rows of the pause menu: ← → change them in steps of 10 %, Enter cycles them
    /// (100 % wraps to 0 %). The values are saved and apply at once.</summary>
    public class VolumeOptions : MonoBehaviour
    {
        public MenuList menu;
        public const int MusicRow = 1, SfxRow = 2;

        public static string[] PauseLabels() => new[] { "CONTINUAR", MusicLabel, SfxLabel, "CONTROLES", "MENÚ PRINCIPAL" };
        public static string MusicLabel => "MÚSICA  " + Bar(Sfx.MusicVolume);
        public static string SfxLabel => "EFECTOS  " + Bar(Sfx.SfxVolume);

        static string Bar(float v)
        {
            int n = Mathf.RoundToInt(v * 10);
            return new string('|', n) + new string('.', 10 - n) + " " + Mathf.RoundToInt(v * 100) + "%";
        }

        void OnEnable() { Refresh(); }

        void Update()
        {
            if (menu == null || !menu.isActiveAndEnabled) return;
            if (MenuList.Overlay != null && MenuList.Overlay.activeInHierarchy) return;
            int i = menu.Index;
            if (i != MusicRow && i != SfxRow) return;
            if (GameInput.Left) Change(i, -1, false);
            else if (GameInput.Right) Change(i, +1, false);
        }

        public void Change(int row, int dir, bool wrap)
        {
            float v = row == MusicRow ? Sfx.MusicVolume : Sfx.SfxVolume;
            int step = Mathf.RoundToInt(v * 10) + dir;
            if (wrap && step > 10) step = 0;
            step = Mathf.Clamp(step, 0, 10);
            if (row == MusicRow) Sfx.MusicVolume = step / 10f; else Sfx.SfxVolume = step / 10f;
            Sfx.ApplyVolumes();
            Refresh();
            if (row == SfxRow) Sfx.Play("select", 1f);
        }

        public void Refresh()
        {
            if (menu != null) menu.SetLabels(PauseLabels());
        }
    }
}
