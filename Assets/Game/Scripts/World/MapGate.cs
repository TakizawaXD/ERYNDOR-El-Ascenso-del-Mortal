using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Entrance/exit between maps (town gate, map edge, the volcano corridor). Walking into it fades out, loads
    /// the destination scene and puts the player on the matching gate's arrival point. The whole PlayerState travels along.</summary>
    [RequireComponent(typeof(BoxCollider2D))]
    public class MapGate : MonoBehaviour
    {
        public static readonly List<MapGate> All = new List<MapGate>();

        public string id;            // e.g. "N0" in a town, "City_Valle:N0" in the overworld
        public string toMap;         // scene to load
        public string toGate;        // gate id in that scene
        public Vector2 arrival;      // where you appear when you come IN through this gate
        public Vector2 facing = Vector2.down;
        public string label;         // destination name (map markers, toast)
        /// <summary>After a teleport inside the map no gate fires for a moment (you appear next to the other end).</summary>
        public static float BlockUntil;

        void OnEnable() { All.Add(this); }
        void OnDisable() { All.Remove(this); }

        void OnTriggerEnter2D(Collider2D other) { TryUse(other); }
        void OnTriggerStay2D(Collider2D other) { TryUse(other); }

        void TryUse(Collider2D other)
        {
            if (GameManager.Transitioning || GameManager.Ended || Time.timeSinceLevelLoad < 0.6f || Time.time < BlockUntil) return;
            var p = other.GetComponentInParent<PlayerController>();
            if (p == null || p.health.IsDead) return;
            GameManager.Travel(toMap, toGate);
        }

        public static MapGate Find(string gateId)
        {
            foreach (var g in Object.FindObjectsByType<MapGate>(FindObjectsInactive.Include, FindObjectsSortMode.None))
                if (g.id == gateId) return g;
            return null;
        }
    }
}
