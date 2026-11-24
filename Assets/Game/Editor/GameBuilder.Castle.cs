// Fortified walls (2026-11-20): the level files mark walls as '#' every second tile (and watchtowers '0' at corners).
// Instead of one loose 32x40 wall block per mark - which stacked into "towers" of repeated merlons on the north-south
// sides - the marks are joined into continuous runs: horizontal runs get the ashlar front face with merlons
// (fort_wall_h), north-south runs show only their walkway between two parapets seen from above (fort_wall_v), and
// corners, run ends (gates) and watchtower marks get a square crenellated bastion with flag and banner (fort_bastion).
// Art: Tools/ArtGen2/castle.py.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace WoodsGame.EditorTools
{
    public static partial class GameBuilder
    {
        const float WallTopHeight = 2.6f;     // the walkway of a horizontal run sits this high above its foot

        static bool IsWallMark(char c) => c == '#' || c == '0' || c == '9';

        /// <summary>True when PlaceWorldEntities must leave this mark to BuildCastleWalls.</summary>
        static bool CastleNode(LevelData d, int x, int row)
        {
            char c = d.E(x, row);
            if (c == '#') return true;
            if (c != '0') return false;
            for (int k = 1; k <= 2; k++)
                if (d.E(x + k, row) == '#' || d.E(x - k, row) == '#' || d.E(x, row + k) == '#' || d.E(x, row - k) == '#') return true;
            return false;
        }

        static void BuildCastleWalls(LevelData d, Transform parent, Func<int, int, char, bool> skip)
        {
            var h = WOne("Structures/fort_wall_h.png");
            var v = WOne("Structures/fort_wall_v.png");
            var b = WOne("Structures/fort_bastion.png");
            if (h == null || v == null || b == null) { Debug.LogError("[GameBuilder] fort art missing (python Tools/ArtGen2/castle.py)"); return; }

            bool Node(int x, int row)
            {
                char c = d.E(x, row);
                if (!IsWallMark(c) || (skip != null && skip(x, row, c))) return false;
                return c != '0' || CastleNode(d, x, row);
            }
            int Next(int x, int row, int dx, int dy)          // distance to the neighbouring node (1 or 2), 0 = none
            {
                for (int k = 1; k <= 2; k++) if (Node(x + dx * k, row + dy * k)) return k;
                return 0;
            }
            Vector3 Foot(float x, float row) => new Vector3(x + 0.5f, d.h - 1 - row, 0);

            var root = new GameObject("FortWalls").transform; root.SetParent(parent, false);
            int runs = 0, towers = 0;
            for (int row = 0; row < d.h; row++)
                for (int x = 0; x < d.w; x++)
                {
                    if (!Node(x, row)) continue;
                    char c = d.E(x, row);
                    int r = Next(x, row, 1, 0), l = Next(x, row, -1, 0), dn = Next(x, row, 0, 1), up = Next(x, row, 0, -1);
                    bool horiz = r > 0 || l > 0, vert = dn > 0 || up > 0;
                    // horizontal run to the east: front face
                    if (r > 0)
                    {
                        var go = Deco(root, "fort_wall_h", h, Foot(x + r / 2f, row), new Vector2(r, 0.8f), 0.4f);
                        if (r == 1) go.transform.localScale = new Vector3(0.5f, 1, 1);
                        runs++;
                    }
                    // north-south run to the south: walkway seen from above, drawn at wall height, collider on the ground
                    if (dn > 0)
                    {
                        var go = new GameObject("fort_wall_v"); go.transform.SetParent(root, false);
                        var foot = Foot(x, row + dn);
                        go.transform.position = foot;
                        var bc = go.AddComponent<BoxCollider2D>(); bc.size = new Vector2(0.9f, dn); bc.offset = new Vector2(0, dn / 2f);
                        var top = Deco(go.transform, "walkway", v, foot + new Vector3(0, WallTopHeight - 1f, 0));
                        if (dn == 1) top.transform.localScale = new Vector3(1, 0.5f, 1);
                        runs++;
                    }
                    // bastions: corners, the ends of a run (gates) and watchtower marks; the Ciudadela's '9' towers stay as they are
                    if (c == '9') continue;
                    int degree = (r > 0 ? 1 : 0) + (l > 0 ? 1 : 0) + (dn > 0 ? 1 : 0) + (up > 0 ? 1 : 0);
                    if (c == '0' || (horiz && vert) || degree <= 1)
                    {
                        Deco(root, "fort_bastion", b, Foot(x, row) + new Vector3(0, -0.4f, 0), new Vector2(2.6f, 1.3f), 0.65f);
                        towers++;
                    }
                }
            if (runs + towers > 0) Debug.Log($"[GameBuilder] fortified walls: {runs} runs, {towers} bastions");
        }
    }
}
