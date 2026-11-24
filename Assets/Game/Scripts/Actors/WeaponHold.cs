using UnityEngine;

namespace WoodsGame
{
    /// <summary>The equipped melee weapon drawn in the knight's hand (its own icon art: spear, hammer, katana...).
    /// Follows the facing, bobs while walking, glows with weapon oils and hides while the swing animation plays.
    /// Since the combat animation sets (2026-11-21) the weapon is part of every frame; this stays as the fallback.</summary>
    public class WeaponHold : MonoBehaviour
    {
        SpriteRenderer _sr, _body;
        Animator _anim;
        Actor _actor;
        string _shown;
        float _bob;
        WeaponAnimationController _wac;

        static readonly int P_Attacking = Animator.StringToHash("IsAttacking");
        static readonly int P_Dodging = Animator.StringToHash("IsDodging");
        static readonly int P_Dead = Animator.StringToHash("IsDead");
        static readonly int P_Moving = Animator.StringToHash("IsMoving");

        void Start()
        {
            _actor = GetComponent<Actor>();
            _anim = GetComponentInChildren<Animator>();
            _body = _anim ? _anim.GetComponent<SpriteRenderer>() : GetComponentInChildren<SpriteRenderer>();
            var go = new GameObject("HeldWeapon");
            go.transform.SetParent(_body ? _body.transform : transform, false);
            _sr = go.AddComponent<SpriteRenderer>();
            _sr.sortingLayerID = _body ? _body.sortingLayerID : 0;
        }

        void LateUpdate()
        {
            if (_sr == null || _actor == null) return;
            var s = GameManager.State; var a = GameAssets.I;
            if (s.weapon != _shown && a) { _shown = s.weapon; _sr.sprite = a.ItemIcon(s.Weapon.icon); }
            bool busy = _anim && (_anim.GetBool(P_Attacking) || _anim.GetBool(P_Dodging) || _anim.GetBool(P_Dead));
            // with a weapon animation set the weapon is drawn in every frame of the sheets: this overlay is only the
            // fallback for characters without sets (old builds)
            if (_wac == null) _wac = GetComponent<WeaponAnimationController>();
            bool hidden = busy || (_body != null && !_body.enabled) || (_wac != null && _wac.HasSet);
            _sr.enabled = !hidden;
            if (hidden) return;

            Vector2 f = _actor.facing;
            bool moving = _anim && _anim.GetBool(P_Moving);
            _bob = moving ? _bob + Time.deltaTime * 10f : 0f;
            float by = moving ? Mathf.Round(Mathf.Sin(_bob) * 1f) / 16f : 0f;
            Vector3 pos; bool flip = false; int order = 1;
            if (f.y < -0.5f) pos = new Vector3(0.36f, 0.40f, 0);            // down: right hand, blade up
            else if (f.y > 0.5f) { pos = new Vector3(-0.34f, 0.46f, 0); flip = true; order = -1; }   // up: behind the body
            else if (f.x > 0) pos = new Vector3(0.30f, 0.42f, 0);            // right
            else { pos = new Vector3(-0.30f, 0.42f, 0); flip = true; }        // left
            var kind = s.Weapon.kind;
            float scale = kind == WeaponKind.Spear || kind == WeaponKind.Greatsword || kind == WeaponKind.Hammer ? 0.85f : kind == WeaponKind.Dagger ? 0.55f : 0.7f;
            _sr.transform.localPosition = pos + new Vector3(0, by, 0);
            _sr.transform.localScale = new Vector3(scale, scale, 1);
            _sr.flipX = flip;
            _sr.sortingOrder = (_body ? _body.sortingOrder : 0) + order;
            // weapon oils colour the blade
            var col = Color.white;
            if (s.oilHits > 0)
            {
                float k = 0.65f + 0.35f * Mathf.Sin(Time.time * 8f);
                col = s.oil == "aceite_fuego" ? Color.Lerp(Color.white, new Color(1f, 0.55f, 0.25f), k)
                    : s.oil == "aceite_hielo" ? Color.Lerp(Color.white, new Color(0.55f, 0.85f, 1f), k)
                    : Color.Lerp(Color.white, new Color(1f, 0.95f, 0.5f), k);
            }
            else if (s.Broken(s.weapon)) col = new Color(0.6f, 0.55f, 0.55f);
            _sr.color = col;
        }
    }
}
