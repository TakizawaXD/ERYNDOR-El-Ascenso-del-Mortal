using System;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Central asset registry (Resources/GameAssets.asset, filled by Tools > Game > Build Game).</summary>
    [CreateAssetMenu(menuName = "Woods Game/Game Assets")]
    public class GameAssets : ScriptableObject
    {
        static GameAssets _i;
        public static GameAssets I => _i ? _i : (_i = Resources.Load<GameAssets>("GameAssets"));

        [Header("Effects (frame sequences)")]
        public Sprite[] fxHit, fxBlood, fxDust, fxPoof, fxSplash, fxSparkle, fxHeal, fxExplosion, fxSummon;

        [Header("Projectiles")]
        public Sprite[] arrowFrames, fireballFrames, spitFrames;

        [Header("Pickups")]
        public Sprite coin, potion, arrows, heart;

        [Header("UI")]
        public Font font;
        public Sprite heartFull, heartHalf, heartEmpty, panel, dialog, slot, slotSelected, barFrame, barFillHP, barFillBoss,
            iconCoin, iconArrow, iconPotion, iconSkull, iconSword, promptE0, promptE1, menuBackground, button, buttonHover;
        [Tooltip("title screen illustration (Assets/Art/UI/Title/eryndor_title.png) - the menu options are part of the image")]
        public Sprite titleScreen;

        [Header("Audio")]
        public AudioClip[] sfx;
        public AudioClip music;
        [Tooltip("Audio/Music: music_<piece>_loop / _night / _intro and jingle_<name> (Tools/GameGen/music.py)")]
        public AudioClip[] musicClips;
        [Tooltip("Audio/Ambience: amb_<layer> loops (Tools/GameGen/ambience.py)")]
        public AudioClip[] ambienceClips;

        public AudioClip MusicClip(string name) => Find(musicClips, name);
        public AudioClip AmbienceClip(string name) => Find(ambienceClips, name);
        static AudioClip Find(AudioClip[] list, string name)
        {
            if (list != null) foreach (var c in list) if (c != null && c.name == name) return c;
            return null;
        }

        [Header("Prefabs")]
        public GameObject arrowPrefab, fireballPrefab, spitPrefab, coinPrefab, potionPrefab, arrowsPickupPrefab;
        public GameObject magicBoltPrefab;    // staff bolts (combat animations 2026-11-21)
        [Tooltip("every regional enemy type, prefab name = type id (Orc, OrcDesert, DemonWraith...)")]
        public GameObject[] enemyPrefabs;

        [Header("Knight classes (same order as KnightClass.All)")]
        public RuntimeAnimatorController[] classControllers;
        public FrameSet[] classIdle;          // idle-down frames for the class select / character sheet
        public FrameSet[] classWalk;          // walk-down frames for the class select preview

        [Header("Lighting + RPG UI")]
        public Sprite lightSprite;
        public Material matMultiply, matAdditive;
        public Sprite[] rpgIcons;             // sun, moon, sword, shield, boot, star, heart, bow
        public Sprite[] windowFrames;         // interior window: day, night
        public Sprite worldMap;               // overworld map (1 px per tile) - the world map can be opened from any town

        [Header("Equipment + flat UI")]
        public Sprite[] itemIcons;            // ui_items_16x16 (ItemDef.icon)
        public Sprite[] itemIconsLarge;       // ui_items_32x32 (shop / inventory details)
        public string[] weaponFxNames;
        public FrameSet[] weaponFx;           // same order as weaponFxNames
        public Sprite flatPanel, flatSlot, flatSlotSelected;

        [Header("Crafting, camps, NPCs")]
        public Sprite[] matIcons;             // ui_materials_16x16 (MatDef.icon)
        public Sprite[] gatherFrames;         // gather_anim_16x16: kind*2 = ready, kind*2+1 = picked
        public Sprite[] summonFx;             // purple summoning circle (Invocador / player summons)
        public Sprite MatIcon(int i) => matIcons != null && i >= 0 && i < matIcons.Length ? matIcons[i] : null;

        public Sprite ItemIconLarge(int i) => itemIconsLarge != null && i >= 0 && i < itemIconsLarge.Length ? itemIconsLarge[i] : ItemIcon(i);
        public Sprite ItemIcon(int i) => itemIcons != null && i >= 0 && i < itemIcons.Length ? itemIcons[i] : null;

        public Sprite[] WeaponFxFrames(string name)
        {
            if (weaponFxNames != null)
                for (int i = 0; i < weaponFxNames.Length; i++) if (weaponFxNames[i] == name && i < weaponFx.Length) return weaponFx[i].frames;
            return null;
        }

        [Serializable] public class FrameSet { public Sprite[] frames; }

        public GameObject EnemyPrefab(string type)
        {
            if (enemyPrefabs != null) foreach (var p in enemyPrefabs) if (p != null && p.name == type) return p;
            return null;
        }

        public RuntimeAnimatorController ClassController(string id)
        {
            int i = KnightClass.IndexOf(id);
            return classControllers != null && i < classControllers.Length ? classControllers[i] : null;
        }

        public Sprite[] ClassIdle(string id)
        {
            int i = KnightClass.IndexOf(id);
            return classIdle != null && i < classIdle.Length && classIdle[i] != null ? classIdle[i].frames : Array.Empty<Sprite>();
        }

        public Sprite Icon(int i) => rpgIcons != null && i < rpgIcons.Length ? rpgIcons[i] : null;

        public AudioClip Clip(string name)
        {
            if (sfx == null) return null;
            string key = "sfx_" + name;
            foreach (var c in sfx) if (c != null && c.name == key) return c;
            return null;
        }

        public Sprite[] Frames(FxKind k)
        {
            switch (k)
            {
                case FxKind.Hit: return fxHit;
                case FxKind.Blood: return fxBlood;
                case FxKind.Dust: return fxDust;
                case FxKind.Poof: return fxPoof;
                case FxKind.Splash: return fxSplash;
                case FxKind.Sparkle: return fxSparkle;
                case FxKind.Heal: return fxHeal;
                case FxKind.Explosion: return fxExplosion;
                case FxKind.Summon: return fxSummon;
            }
            return Array.Empty<Sprite>();
        }
    }
}
