p = 'G:/Juegos/Assets/Game/Scripts/Actors/PlayerController.cs'
s = open(p, encoding='utf8').read()
def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b)
rep("amount = attackDamage, knockback = 5f", "amount = S.SwordDamage, knockback = 5f")
rep("amount = comboDamage, knockback = 8f", "amount = S.SwordDamage + 1, knockback = 8f")
rep("amount = heavyDamage, knockback = 9f", "amount = S.SwordDamage + 2, knockback = 9f")
rep("""            health.Changed += () => S.hp = health.hp;
            Face(Vector2.down);""", """            health.Changed += () => S.hp = health.hp;
            Face(Vector2.down);
            // continue / respawn: appear at the last campfire
            if (S.saveX >= 0)
            {
                transform.position = new Vector3(S.saveX, S.saveY, 0);
                if (rb) rb.position = transform.position;
            }""")
open(p, 'w', encoding='utf8').write(s)
print('ok')
