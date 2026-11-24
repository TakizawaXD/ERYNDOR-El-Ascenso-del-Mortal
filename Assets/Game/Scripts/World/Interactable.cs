using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame
{
    /// <summary>Things the player can use with E. Shows the "E" prompt when close.</summary>
    public abstract class Interactable : MonoBehaviour
    {
        static readonly List<Interactable> All = new List<Interactable>();
        public float promptHeight = 1.2f;
        SpriteRenderer _prompt;

        public virtual bool CanInteract => true;
        public abstract void Interact(PlayerController p);

        protected virtual void OnEnable() { All.Add(this); }
        protected virtual void OnDisable() { All.Remove(this); }

        public static Interactable Nearest(Vector2 at, float radius)
        {
            Interactable best = null; float bd = radius;
            foreach (var i in All)
            {
                if (!i.CanInteract) continue;
                float d = Vector2.Distance(at, i.transform.position);
                if (d <= bd) { bd = d; best = i; }
            }
            return best;
        }

        protected virtual void Update()
        {
            var p = PlayerController.Current;
            bool show = p != null && CanInteract && Vector2.Distance(p.transform.position, transform.position) < 1.4f;
            if (show && _prompt == null)
            {
                var go = new GameObject("prompt");
                go.transform.SetParent(transform, false);
                go.transform.localPosition = new Vector3(0, promptHeight, 0);
                _prompt = go.AddComponent<SpriteRenderer>();
                _prompt.sortingOrder = 200;
            }
            if (_prompt != null)
            {
                _prompt.enabled = show;
                var a = GameAssets.I;
                if (show && a) _prompt.sprite = (Time.time % 0.8f) < 0.4f ? a.promptE0 : a.promptE1;
            }
        }
    }
}
