using UnityEngine;

namespace WoodsGame
{
    /// <summary>A plant, mushroom patch, ore vein or crystal you can harvest with E. It grows back after a day.
    /// Flor de luna only opens at night. Ore needs a few blows (the knight kneels and picks it).</summary>
    public class Gatherable : Interactable
    {
        public int kind;                 // index into CraftDB.GatherKinds
        public Sprite ready, picked;
        public int amount = 1;
        SpriteRenderer _sr;
        float _sway;

        public string MatId => CraftDB.GatherKinds[Mathf.Clamp(kind, 0, CraftDB.GatherKinds.Length - 1)];
        string Key => $"gath_{Mathf.RoundToInt(transform.position.x * 2)}_{Mathf.RoundToInt(transform.position.y * 2)}";
        bool NightOnly => MatId == "flor_luna";
        bool Mineral => kind >= 5;

        /// <summary>Picked on day N (stored as a flag "gath_x_y:N"); ready again two days later.</summary>
        public bool Ready
        {
            get
            {
                var s = GameManager.State;
                foreach (var f in s.flags)
                    if (f.StartsWith(Key + ":") && int.TryParse(f.Substring(Key.Length + 1), out int day))
                        return s.day >= day + 2;
                return true;
            }
        }

        public override bool CanInteract => Ready && (!NightOnly || DayNight.IsNight);

        void Awake() { _sr = GetComponent<SpriteRenderer>(); _sway = Random.value * 6f; }

        protected override void Update()
        {
            base.Update();
            if (_sr == null || Time.frameCount % 15 != 0) return;
            bool show = Ready;
            _sr.sprite = show ? ready : picked;
            if (NightOnly && show) _sr.color = DayNight.IsNight ? Color.white : new Color(0.75f, 0.8f, 0.75f);   // closed by day
        }

        public override void Interact(PlayerController p)
        {
            if (!CanInteract) return;
            var s = GameManager.State;
            s.flags.RemoveAll(f => f.StartsWith(Key + ":"));
            s.flags.Add(Key + ":" + s.day);
            int n = amount + (Mineral ? 0 : Random.Range(0, 2));
            int stored = s.Give(MatId, n);
            var m = CraftDB.Get(MatId);
            Sfx.PlayAt(Mineral ? "anvil" : "gather", transform.position, 0.7f);
            Fx.Spawn(Mineral ? FxKind.Hit : FxKind.Sparkle, (Vector2)transform.position + Vector2.up * 0.4f);
            UIRoot.MatToast(m, n, stored);
            if (_sr) _sr.sprite = picked;
        }
    }
}
