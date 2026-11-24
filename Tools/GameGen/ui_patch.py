def patch(p, pairs):
    s = open(p, encoding='utf8').read()
    for a, b in pairs:
        assert a in s, (p, a[:80])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf8').write(s)

patch('G:/Juegos/Assets/Game/Scripts/UI/UIRoot.cs', [
 ('_over = Panel("GameOver", "HAS CAÍDO", out _overMenu, new[] { "REINTENTAR", "MENÚ PRINCIPAL" },\n                new Action[] { () => { _over.gameObject.SetActive(false); GameManager.Retry(); }, GameManager.ToMenu });',
  '_over = Panel("GameOver", "HAS CAÍDO", out _overMenu, new[] { "VOLVER A LA HOGUERA", "MENÚ PRINCIPAL" },\n                new Action[] { () => { _over.gameObject.SetActive(false); GameManager.Respawn(); }, GameManager.ToMenu });'),
 ('_victory = Panel("Victory", "¡VICTORIA!", out _victoryMenu, new[] { "MENÚ PRINCIPAL" }, new Action[] { GameManager.ToMenu });',
  '_victory = Panel("Victory", "¡VICTORIA!", out _victoryMenu, new[] { "SEGUIR EXPLORANDO", "MENÚ PRINCIPAL" }, new Action[] { GameManager.KeepExploring, GameManager.ToMenu });'),
 ('"J ESPADA  K FUERTE  L ARCO  ESPACIO RODAR  E USAR  Q POCIÓN"', '"J ESPADA K FUERTE L ARCO ESPACIO RODAR E USAR Q POCIÓN M MAPA TAB DIARIO"'),
 ('        public static void HideAll()', '        public static void HideVictory() { if (_i) _i._victory.gameObject.SetActive(false); }\n\n        public static void HideAll()'),
 ('$"MONEDAS {s.coins}   ENEMIGOS {s.kills}"', '$"EL BOSQUE ESTÁ A SALVO.  NIVEL {s.level}  ENEMIGOS {s.kills}"'),
])

patch('G:/Juegos/Assets/Game/Scripts/World/Chest.cs', [
 ('        void Awake() { _sr = GetComponent<SpriteRenderer>(); }',
  '''        string Id => $"chest_{Mathf.RoundToInt(transform.position.x)}_{Mathf.RoundToInt(transform.position.y)}";

        void Awake() { _sr = GetComponent<SpriteRenderer>(); }

        void Start()
        {
            // opened in this save already: show it open and empty
            if (GameManager.State.Has(Id)) { _open = true; if (frames != null && frames.Length > 0) _sr.sprite = frames[frames.Length - 1]; }
        }'''),
 ('            _open = true;\n            Sfx.Play("chest");',
  '            _open = true;\n            GameManager.State.Set(Id);\n            GameManager.State.chestsOpened++;\n            Quests.Refresh();\n            Sfx.Play("chest");'),
])

patch('G:/Juegos/Assets/Game/Scripts/UI/MainMenu.cs', [
 ('''            _menu = MenuList.Create(box, new[] { "JUGAR", "CONTROLES", "SALIR" },
                new Action[] { Play, ShowControls, Quit }, new Vector2(0, 0),''',
  '''            bool cont = GameManager.CanContinue;
            var labels = cont ? new[] { "CONTINUAR", "NUEVA PARTIDA", "CONTROLES", "SALIR" } : new[] { "NUEVA PARTIDA", "CONTROLES", "SALIR" };
            var acts = cont ? new Action[] { GameManager.Continue, Play, ShowControls, Quit } : new Action[] { Play, ShowControls, Quit };
            box.sizeDelta = new Vector2(130, labels.Length * 12 + 12);
            _menu = MenuList.Create(box, labels, acts, new Vector2(0, 0),'''),
 ('UIRoot.Img(box, a ? a.panel : null, true).rectTransform.sizeDelta = new Vector2(120, 48);',
  'UIRoot.Img(box, a ? a.panel : null, true).rectTransform.sizeDelta = new Vector2(130, GameManager.CanContinue ? 60 : 48);'),
 ('"Q               BEBER POCIÓN", "ESC             PAUSA",', '"Q               BEBER POCIÓN", "M / TAB         MAPA / DIARIO",'),
])
patch('G:/Juegos/Assets/Game/Scripts/UI/UIRoot.cs', [
 ('"Q               BEBER POCIÓN", "ESC             PAUSA",', '"Q               BEBER POCIÓN", "M / TAB         MAPA / DIARIO",'),
])
print('ok')
