using UnityEngine;

namespace WoodsGame
{
    /// <summary>Everything the game reads from the player. Swappable so PlayMode tests can drive the game.</summary>
    public interface IInputSource
    {
        Vector2 Move { get; }
        bool Run { get; }
        bool Attack { get; }      // pressed this frame
        bool Heavy { get; }
        bool Special { get; }
        bool Roll { get; }
        bool Interact { get; }
        bool Potion { get; }
        bool Pause { get; }
        bool Confirm { get; }
        bool Up { get; }
        bool Down { get; }
        bool Map { get; }
        bool Journal { get; }
        bool Left { get; }
        bool Right { get; }
        bool Character { get; }
        bool Inventory { get; }
        bool Block { get; }       // held
        bool Parry { get; }
        bool Cycle { get; }
        bool Summon { get; }
    }

    public static class GameInput
    {
        public static IInputSource Source = new KeyboardInput();
        public static Vector2 Move => Source.Move;
        public static bool Run => Source.Run;
        public static bool Attack => Source.Attack;
        public static bool Heavy => Source.Heavy;
        /// <summary>Heavy button held down (charged attack). Keyboard: K / X / right mouse; tests: VirtualInput.heavyHeld.</summary>
        public static bool HeavyHeld => Source is VirtualInput v ? v.heavyHeld
            : Source is KeyboardInput && (Input.GetKey(KeyCode.K) || Input.GetKey(KeyCode.X) || Input.GetMouseButton(1));
        public static bool Special => Source.Special;
        public static bool Roll => Source.Roll;
        public static bool Interact => Source.Interact;
        public static bool Potion => Source.Potion;
        public static bool Pause => Source.Pause;
        public static bool Confirm => Source.Confirm;
        public static bool Up => Source.Up;
        public static bool Down => Source.Down;
        public static bool Map => Source.Map;
        public static bool Journal => Source.Journal;
        public static bool Left => Source.Left;
        public static bool Right => Source.Right;
        public static bool Character => Source.Character;
        public static bool Inventory => Source.Inventory;
        public static bool Block => Source.Block;
        public static bool Parry => Source.Parry;
        public static bool Cycle => Source.Cycle;
        public static bool Summon => Source.Summon;
    }

    /// <summary>Keyboard (legacy Input Manager) — WASD/arrows, Shift, J K L, Space, E, Q, R, F, Ctrl/U, Esc, Enter.</summary>
    public class KeyboardInput : IInputSource
    {
        static bool K(KeyCode a) => Input.GetKeyDown(a);
        static bool H(KeyCode a) => Input.GetKey(a);

        public Vector2 Move
        {
            get
            {
                float x = (H(KeyCode.D) || H(KeyCode.RightArrow) ? 1 : 0) - (H(KeyCode.A) || H(KeyCode.LeftArrow) ? 1 : 0);
                float y = (H(KeyCode.W) || H(KeyCode.UpArrow) ? 1 : 0) - (H(KeyCode.S) || H(KeyCode.DownArrow) ? 1 : 0);
                var v = new Vector2(x, y);
                return v.sqrMagnitude > 1 ? v.normalized : v;
            }
        }
        public bool Run => H(KeyCode.LeftShift) || H(KeyCode.RightShift);
        public bool Attack => K(KeyCode.J) || K(KeyCode.Z) || Input.GetMouseButtonDown(0);
        public bool Heavy => K(KeyCode.K) || K(KeyCode.X) || Input.GetMouseButtonDown(1);
        public bool Special => K(KeyCode.L);
        public bool Roll => K(KeyCode.Space);
        public bool Interact => K(KeyCode.E);
        public bool Potion => K(KeyCode.Q);
        public bool Pause => K(KeyCode.Escape) || K(KeyCode.P);
        public bool Confirm => K(KeyCode.Return) || K(KeyCode.KeypadEnter) || K(KeyCode.Space);
        public bool Up => K(KeyCode.W) || K(KeyCode.UpArrow);
        public bool Down => K(KeyCode.S) || K(KeyCode.DownArrow);
        public bool Map => K(KeyCode.M);
        public bool Journal => K(KeyCode.Tab);
        public bool Inventory => K(KeyCode.I);
        public bool Left => K(KeyCode.A) || K(KeyCode.LeftArrow);
        public bool Right => K(KeyCode.D) || K(KeyCode.RightArrow);
        public bool Character => K(KeyCode.C);
        public bool Block => H(KeyCode.LeftControl) || H(KeyCode.U) || Input.GetMouseButton(2);
        public bool Parry => K(KeyCode.F);
        public bool Cycle => K(KeyCode.R);
        public bool Summon => K(KeyCode.V);
    }

    /// <summary>Scriptable input for automated tests. "Press" flags last one frame.</summary>
    public class VirtualInput : IInputSource
    {
        public Vector2 move;
        public bool run;
        public bool heavyHeld;
        public bool block;
        int _attack, _heavy, _special, _roll, _interact, _potion, _pause, _confirm, _up, _down, _map, _journal, _left, _right, _character, _inventory, _parry, _cycle, _summon;

        public void Press(string action)
        {
            int f = Time.frameCount;   // visible during frame f+1
            switch (action)
            {
                case "Attack": _attack = f; break;
                case "Heavy": _heavy = f; break;
                case "Special": _special = f; break;
                case "Roll": _roll = f; break;
                case "Interact": _interact = f; break;
                case "Potion": _potion = f; break;
                case "Pause": _pause = f; break;
                case "Confirm": _confirm = f; break;
                case "Up": _up = f; break;
                case "Down": _down = f; break;
                case "Map": _map = f; break;
                case "Journal": _journal = f; break;
                case "Left": _left = f; break;
                case "Right": _right = f; break;
                case "Character": _character = f; break;
                case "Inventory": _inventory = f; break;
                case "Parry": _parry = f; break;
                case "Cycle": _cycle = f; break;
                case "Summon": _summon = f; break;
            }
        }
        // a press made from a test coroutine (which runs after Update) is seen by the next frame's Update
        static bool Now(int f) => Time.frameCount == f + 1;
        public Vector2 Move => move;
        public bool Run => run;
        public bool Attack => Now(_attack);
        public bool Heavy => Now(_heavy);
        public bool Special => Now(_special);
        public bool Roll => Now(_roll);
        public bool Interact => Now(_interact);
        public bool Potion => Now(_potion);
        public bool Pause => Now(_pause);
        public bool Confirm => Now(_confirm);
        public bool Up => Now(_up);
        public bool Down => Now(_down);
        public bool Map => Now(_map);
        public bool Journal => Now(_journal);
        public bool Left => Now(_left);
        public bool Right => Now(_right);
        public bool Character => Now(_character);
        public bool Inventory => Now(_inventory);
        public bool Block => block;
        public bool Parry => Now(_parry);
        public bool Cycle => Now(_cycle);
        public bool Summon => Now(_summon);
    }
}
