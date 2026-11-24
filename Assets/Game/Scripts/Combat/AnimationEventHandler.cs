using System;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace WoodsGame
{
    /// <summary>Receives the Animation Events of the character clips (AnimEvent("HitOn"), "HitOff", "Projectile",
    /// "Telegraph", "Anticipation", "ComboWindow", "End") on the GameObject that has the Animator, and forwards them to
    /// whoever listens (CharacterAnimationController and its subclasses). It also keeps the last events for the tests.
    /// Every Animator of a character must have one, or Unity reports "AnimationEvent has no receiver": GameBuilder adds
    /// it to the prefabs and <see cref="EnsureAll"/> covers anything else when a scene loads.</summary>
    [DisallowMultipleComponent]
    public class AnimationEventHandler : MonoBehaviour
    {
        public event Action<string> Fired;
        public string Last { get; private set; } = "";
        public float LastTime { get; private set; } = -1f;
        public int Count { get; private set; }
        public string History => _history;
        string _history = "";

        /// <summary>The function every clip event calls (CharacterAnimationBuilder writes functionName = "AnimEvent").</summary>
        public void AnimEvent(string e)
        {
            Last = e; LastTime = Time.time; Count++;
            _history = (_history.Length > 300 ? _history.Substring(_history.Length - 200) : _history) + e + ";";
            Fired?.Invoke(e);
        }

        public static AnimationEventHandler On(GameObject go)
        {
            if (go == null) return null;
            var h = go.GetComponent<AnimationEventHandler>();
            return h != null ? h : go.AddComponent<AnimationEventHandler>();
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Hook()
        {
            SceneManager.sceneLoaded += (s, m) => EnsureAll();
            EnsureAll();
        }

        /// <summary>Gives every Animator in the loaded scenes a receiver (villagers, heroes, props with animators).</summary>
        public static int EnsureAll()
        {
            int n = 0;
            foreach (var a in FindObjectsByType<Animator>(FindObjectsInactive.Include, FindObjectsSortMode.None))
                if (a.GetComponent<AnimationEventHandler>() == null) { a.gameObject.AddComponent<AnimationEventHandler>(); n++; }
            return n;
        }
    }
}
