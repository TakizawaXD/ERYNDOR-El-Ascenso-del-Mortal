"""Hooks the new audio (Sfx.Step / SwingFor / HitFor / Voice / PlayAt / Jingle, door, gate, shop and menu sounds,
pause-menu volume options) into the game scripts with exact one-line replacements. Safe to re-run (skips what is done).

  python Tools/GameGen/audio_patch.py
"""
import os, sys

S = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Assets', 'Game', 'Scripts'))

# (file, old, new, count)  count = expected occurrences of old (0 = all, at least one)
P = [
    ('Actors/PlayerController.cs', 'if (moving && Time.time > _nextStep) { Sfx.Play("step", 0.5f);',
     'if (moving && Time.time > _nextStep) { Sfx.Step(transform.position, running ? 0.6f : 0.45f);', 1),
    ('Actors/PlayerController.cs', 'Trigger("Attack");\n            Sfx.Play("swing");', 'Trigger("Attack");\n            Sfx.Play(Sfx.SwingFor(w.kind));', 1),
    ('Actors/PlayerController.cs', 'Trigger("ComboAttack");\n                Lock(st.windup + st.recover + 0.05f);\n                Sfx.Play("heavy_swing");',
     'Trigger("ComboAttack");\n                Lock(st.windup + st.recover + 0.05f);\n                Sfx.Play(Sfx.SwingFor(w.kind, true));', 1),
    ('Actors/PlayerController.cs', 'Trigger("HeavyAttack");\n            Sfx.Play("heavy_swing");\n            yield return new WaitForSeconds(st.windup * 1.6f);',
     'Trigger("HeavyAttack");\n            Sfx.Play(Sfx.SwingFor(w.kind, true));\n            yield return new WaitForSeconds(st.windup * 1.6f);', 1),

    ('Core/Combat.cs', '                        Sfx.Play("hit");', '                        Sfx.PlayAt(Sfx.HitFor(d, h), (Vector2)h.transform.position, 0.9f);', 1),

    ('Actors/EnemyController.cs', 'Sfx.Play("boss_roar", 0.25f);', 'Sfx.Voice(this, "alert", 0.7f);', 1),
    ('Actors/EnemyController.cs', 'Sfx.Play(heavy ? "heavy_swing" : "swing", 0.7f);',
     'Sfx.PlayAt(heavy ? "heavy_swing" : "swing", transform.position, 0.7f); if (Random.value < 0.5f) Sfx.Voice(this, "attack", 0.6f);', 1),
    ('Actors/EnemyController.cs', 'Sfx.Play(kind == EnemyKind.Demon ? "fireball" : "spit");', 'Sfx.PlayAt(kind == EnemyKind.Demon ? "fireball" : "spit", transform.position);', 1),
    ('Actors/EnemyController.cs', 'Sfx.Play("boss_roar", 0.5f);', 'Sfx.Voice(this, "alert", 0.9f);', 1),
    ('Actors/EnemyController.cs', 'Sfx.Play("spit");\n            Fx.Spawn(FxKind.Splash', 'Sfx.PlayAt("spit", transform.position);\n            Fx.Spawn(FxKind.Splash', 1),
    ('Actors/EnemyController.cs', 'Sfx.Play("block");\n            UIRoot.Popup(Body + Vector2.up * 0.5f, "BLOQUEO"', 'Sfx.PlayAt("block", transform.position);\n            UIRoot.Popup(Body + Vector2.up * 0.5f, "BLOQUEO"', 1),
    ('Actors/EnemyController.cs', 'Sfx.Play("enemy_hurt", 0.8f);', 'if (Random.value < 0.6f) Sfx.Voice(this, "hurt", 0.7f);', 1),
    ('Actors/EnemyController.cs', 'Sfx.Play("enemy_die");', 'Sfx.PlayAt("enemy_die", transform.position); Sfx.Voice(this, "die", 0.9f);', 1),
    ('Actors/EnemyController.cs', 'Fx.Spawn(FxKind.Poof, Body);\n            Sfx.Play("roll", 0.6f);', 'Fx.Spawn(FxKind.Poof, Body);\n            Sfx.PlayAt("blink", transform.position, 0.8f);', 1),
    ('Actors/EnemyController.cs', '            if (playerAlive && (dist < aggroRange || (dist < leash && _wasChasing)))\n            {\n                _wasChasing = true;',
     '            if (playerAlive && (dist < aggroRange || (dist < leash && _wasChasing)))\n            {\n                if (!_wasChasing && !ally && !isBoss) Sfx.Voice(this, "alert", 0.55f);\n                _wasChasing = true;', 1),

    ('World/Animal.cs', 'Sfx.Play(sound, 0.4f);', 'Sfx.PlayAt(Sfx.AnimalSound(species), transform.position, 0.6f);', 1),
    ('World/Animal.cs', 'Sfx.Play("select", 0.5f);\n            UIRoot.Popup((Vector2)transform.position + Vector2.up * 0.9f, "Rrr..."',
     'Sfx.PlayAt("cat_purr", transform.position, 0.8f);\n            UIRoot.Popup((Vector2)transform.position + Vector2.up * 0.9f, "Rrr..."', 1),
    ('World/Animal.cs', '            UIRoot.Popup((Vector2)transform.position + Vector2.up * 0.9f, "¡Miau!"',
     '            Sfx.PlayAt("cat_meow", transform.position, 0.7f);\n            UIRoot.Popup((Vector2)transform.position + Vector2.up * 0.9f, "¡Miau!"', 1),
    ('World/Animal.cs', '            if (dPlayer > 18f) { _vel = Vector2.zero; return; }                       // far away: stand still, cheap\n',
     '            if (dPlayer > 18f) { _vel = Vector2.zero; return; }                       // far away: stand still, cheap\n'
     '            if (dPlayer < 9f && Time.time > _nextCall)                                 // moo, oink, baa, cluck, meow now and then\n'
     '            {\n                if (_nextCall > 0 && !_petting) Sfx.PlayAt(Sfx.AnimalSound(species), transform.position, 0.45f);\n'
     '                _nextCall = Time.time + Random.Range(species == "chicken" ? 5f : 9f, species == "chicken" ? 12f : 22f);\n            }\n', 1),
    ('World/Animal.cs', '        void Update()\n        {\n            if (_hp.IsDead', '        float _nextCall;\n\n        void Update()\n        {\n            if (_hp.IsDead', 1),

    ('World/Villager.cs', 'Sfx.Play("anvil", 0.45f);', 'Sfx.PlayAt("anvil", transform.position, 0.6f);', 1),
    ('World/Breakable.cs', 'Sfx.Play("break");', 'Sfx.PlayAt("break", transform.position);', 1),
    ('World/Projectile.cs', 'Sfx.Play("hit", 0.6f);', 'Sfx.PlayAt("hit", transform.position, 0.6f);', 1),
    ('World/ThrownBomb.cs', 'Sfx.Play("bomb");', 'Sfx.PlayAt("bomb", transform.position);', 1),
    ('World/Gatherable.cs', 'Sfx.Play(Mineral ? "anvil" : "gather", 0.7f);', 'Sfx.PlayAt(Mineral ? "anvil" : "gather", transform.position, 0.7f);', 1),
    ('World/Campfire.cs', '            Fx.Spawn(FxKind.Heal, p.Body);\n            Sfx.Play("potion");', '            Fx.Spawn(FxKind.Heal, p.Body);\n            Sfx.Play("heal"); Sfx.Play("fire_ignite", 0.5f);', 1),
    ('RPG/Summoning.cs', 'Sfx.Play("boss_roar", 0.35f); Sfx.Play("parry", 0.4f);', 'Sfx.Play("spell"); Sfx.Play("boss_roar", 0.3f);', 1),
    ('RPG/Progression.cs', '                Sfx.Play("levelup");\n                UIRoot.TitleCard($"¡Nivel', '                Sfx.Jingle("levelup");\n                UIRoot.TitleCard($"¡Nivel', 1),
    ('World/WorldInfo.cs', '            if (isNew) Quests.Refresh();', '            if (isNew) { Quests.Refresh(); if (!first) Sfx.Jingle("discover"); }', 1),

    ('Flow/GameManager.cs', '            Sfx.Play("gameover");', '            Sfx.Jingle("defeat");', 1),
    ('Flow/GameManager.cs', '            Sfx.Play("victory");\n            UIRoot.ShowVictory();', '            Sfx.Jingle("victory");\n            UIRoot.ShowVictory();', 1),
    ('Flow/GameManager.cs', '            _transitioning = true;\n            Sfx.Play("chest", 0.5f);\n            yield return UIRoot.Fade(1f, 0.22f);',
     '            _transitioning = true;\n            Sfx.Play(enter ? "door_open" : "door_close", 0.8f);\n            yield return UIRoot.Fade(1f, 0.22f);', 1),
    ('Flow/GameManager.cs', '        public static void SetPaused(bool p)\n        {\n            Paused = p;',
     '        public static void SetPaused(bool p)\n        {\n            if (Paused != p) Sfx.Play(p ? "menu_open" : "menu_close", 0.6f);\n            Paused = p;', 1),
    ('Flow/GameManager.Maps.cs', '            Sfx.Play("chest", 0.5f);\n            LoadMap(map, gate);', '            Sfx.Play("gate", 0.8f);\n            LoadMap(map, gate);', 1),

    ('UI/WorldUI.cs', '            panel.gameObject.SetActive(true);\n            Time.timeScale = 0f;\n            Sfx.Play("select", 0.6f);',
     '            panel.gameObject.SetActive(true);\n            Time.timeScale = 0f;\n            if (!was && panel != I._talk) Sfx.Play("menu_open", 0.6f);', 1),
    ('UI/WorldUI.cs', '        static void Open(RectTransform panel)\n        {\n            CloseAll(panel != I._talk);',
     '        static bool _quiet;\n\n        static void Open(RectTransform panel)\n        {\n            bool was = panel.gameObject.activeSelf;\n            _quiet = true; CloseAll(panel != I._talk); _quiet = false;', 1),
    ('UI/WorldUI.cs', '            foreach (var p in _i._panels) if (p != null) p.gameObject.SetActive(false);\n            if (endTalk) Dialogue.End();',
     '            bool any = false;\n            foreach (var p in _i._panels) if (p != null) { any |= p.gameObject.activeSelf; p.gameObject.SetActive(false); }\n'
     '            if (any && !_quiet) Sfx.Play("menu_close", 0.5f);\n            if (endTalk) Dialogue.End();', 1),
    ('UI/WorldUI.cs', 'Sfx.Play("block")', 'Sfx.Play("error")', 0),
    ('UI/WorldUI.Lists.cs', 'Sfx.Play("block")', 'Sfx.Play("error")', 0),
    ('UI/WorldUI.Lists.cs', 's.coins -= price; s.AddItem(id); Sfx.Play("coin");', 's.coins -= price; s.AddItem(id); Sfx.Play("buy");', 1),
    ('UI/WorldUI.Lists.cs', 's.coins -= price; s.Give(id, 1); Sfx.Play("coin");', 's.coins -= price; s.Give(id, 1); Sfx.Play("buy");', 1),
    ('UI/WorldUI.Lists.cs', 's.coins -= 10; s.arrows += 10; Sfx.Play("coin");', 's.coins -= 10; s.arrows += 10; Sfx.Play("buy");', 1),
    ('UI/WorldUI.Lists.cs', '                        var p = PlayerController.Current; if (p) p.health.Init(s.maxHP, s.hp);\n                        Sfx.Play("coin");',
     '                        var p = PlayerController.Current; if (p) p.health.Init(s.maxHP, s.hp);\n                        Sfx.Play("buy");', 1),
    ('UI/WorldUI.Lists.cs', 's.coins += price; Sfx.Play("coin");', 's.coins += price; Sfx.Play("sell");', 0),
    ('UI/WorldUI.Inventory.cs', '                    Sfx.Play("chest", 0.6f);\n                    _invIndex = (int)ItemDB.Get(id).slot;', '                    Sfx.Play("equip", 0.8f);\n                    _invIndex = (int)ItemDB.Get(id).slot;', 1),

    ('UI/UIRoot.cs', '            _pause = Panel("Pause", "PAUSA", out _pauseMenu, new[] { "CONTINUAR", "CONTROLES", "MENÚ PRINCIPAL" },\n'
                     '                new Action[] { () => GameManager.SetPaused(false), () => ShowControls(true), GameManager.ToMenu });',
     '            _pause = Panel("Pause", "PAUSA", out _pauseMenu, VolumeOptions.PauseLabels(),\n'
     '                new Action[] { () => GameManager.SetPaused(false), () => _pauseVol.Change(1, +1, true), () => _pauseVol.Change(2, +1, true), () => ShowControls(true), GameManager.ToMenu });\n'
     '            _pauseVol = _pause.gameObject.AddComponent<VolumeOptions>(); _pauseVol.menu = _pauseMenu;\n'
     '            _pause.Find("Box").GetComponent<RectTransform>().sizeDelta = new Vector2(170, 104);\n'
     '            foreach (Transform c in _pause.Find("Box")) c.GetComponent<RectTransform>().sizeDelta = new Vector2(170, 104);', 1),
    ('UI/UIRoot.cs', '        MenuList _pauseMenu, _overMenu, _victoryMenu;', '        MenuList _pauseMenu, _overMenu, _victoryMenu;\n        VolumeOptions _pauseVol;', 1),
]


def main():
    bad = 0
    for f, old, new, count in P:
        path = os.path.join(S, f)
        s = open(path, encoding='utf-8', newline='').read()
        if chr(13) + chr(10) in s:
            old, new = old.replace(chr(10), chr(13) + chr(10)), new.replace(chr(10), chr(13) + chr(10))
        if new in s and (count != 0 or old not in s):
            print('done   ', f, '|', old.strip()[:60]); continue
        n = s.count(old)
        if n == 0 or (count and n != count):
            print('MISSING', f, n, '|', old.strip()[:70]); bad += 1; continue
        s = s.replace(old, new)
        open(path, 'w', encoding='utf-8', newline='').write(s)
        print('patched', f, n, '|', old.strip()[:60])
    return bad


if __name__ == '__main__':
    sys.exit(main())
