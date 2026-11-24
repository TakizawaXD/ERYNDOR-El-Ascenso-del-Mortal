using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>A house interior. Interiors live in the World scene, far outside the map, so the world keeps running
    /// while you are inside; the camera is clamped to the room and the night tint becomes warm indoor light.</summary>
    public class Interior : MonoBehaviour
    {
        public static Interior Current { get; set; }
        public static readonly List<Interior> All = new List<Interior>();
        public static float EnteredAt;

        public string title = "CASA";
        public string template = "casa";
        public Rect bounds;            // world rect of the room (camera clamp)
        public Vector2 entry;          // where you appear, just above the exit mat
        public Vector2 outside;        // in front of the house door in the world

        void OnEnable() { All.Add(this); }
        void OnDisable() { All.Remove(this); if (Current == this) Current = null; }

        void Start()
        {
            // continuing a game saved in a bed: you wake up inside
            var p = PlayerController.Current;
            if (p != null && bounds.Contains(p.transform.position)) { Current = this; EnteredAt = Time.time; }
        }

        public static Interior At(Vector2 pos)
        {
            foreach (var i in All) if (i.bounds.Contains(pos)) return i;
            return null;
        }
    }
}
