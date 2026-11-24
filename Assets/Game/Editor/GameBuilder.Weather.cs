// Wind + rain for the world scene: vegetation gets the Woods/SpriteWind material, tall-grass tufts are scattered over the
// green land, and the Level object gets a WeatherSystem (rain showers, splashes, darker sky, rain loop, glowing spores).
// Art: Tools/ArtGen2/weather_art.py. Called once from BuildWorldScene.
using System.IO;
using UnityEditor;
using UnityEngine;

namespace WoodsGame.EditorTools
{
    public static partial class GameBuilder
    {
        static void BuildWeather(LevelData d, Transform world)
        {
            foreach (var f in new[] { WA + "Nature/grass_tufts_16x16.png", WA + "Effects/rain_drop.png", WA + "Effects/rain_splash_anim_8x8.png", $"{GameRoot}/Audio/amb_rain_loop.wav" })
                if (AssetDatabase.LoadMainAssetAtPath(f) == null && File.Exists(Path.Combine(ProjectRoot, f))) AssetDatabase.ImportAsset(f);

            Material Wind(string name, float sway, float flutter, float speed)
            {
                var path = $"{GameRoot}/Resources/{name}.mat";
                var m = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (m != null && m.shader != null && m.shader.name == "Woods/SpriteWind") return m;   // already made this build
                m = MaterialAsset(name, "Woods/SpriteWind");
                if (m == null) return null;
                m.SetFloat("_Sway", sway); m.SetFloat("_Flutter", flutter); m.SetFloat("_Speed", speed);
                return m;
            }
            var tree = Wind("M_WindTree", 0.028f, 0.006f, 0.8f);
            var bush = Wind("M_WindBush", 0.06f, 0.02f, 1.1f);
            var grass = Wind("M_WindGrass", 0.11f, 0.05f, 1.4f);

            // existing vegetation (by sprite file name; rocks, stumps, logs, lily pads and fences stay still)
            int swaying = 0;
            var nature = world.Find("Nature");
            if (nature != null && tree != null)
                foreach (var sr in nature.GetComponentsInChildren<SpriteRenderer>(true))
                {
                    string n = sr.gameObject.name;
                    Material m = n.StartsWith("tree_") ? (n == "tree_dead" ? bush : tree)
                        : n.StartsWith("bushes") ? bush
                        : n.StartsWith("plants") || n.StartsWith("cattails") ? grass : null;
                    if (m == null) continue;
                    sr.sharedMaterial = m; swaying++;
                }

            // tall grass tufts over the green land (never on roads, water or occupied tiles)
            var tufts = Sheet(WA + "Nature/grass_tufts_16x16.png");
            if (tufts != null && tufts.Length > 0 && grass != null)
            {
                var root = new GameObject("GrassTufts").transform; root.SetParent(world);
                var rnd = new System.Random(11);
                for (int row = 1; row < d.h - 1; row++)
                    for (int x = 1; x < d.w - 1; x++)
                    {
                        char t = d.T(x, row);
                        double p = t == '.' ? 0.10 : t == 'f' ? 0.16 : 0;
                        if (p == 0 || d.E(x, row) != ' ' || rnd.NextDouble() > p) continue;
                        bool nearRoad = false;
                        for (int dy = -1; dy <= 1 && !nearRoad; dy++)
                            for (int dx = -1; dx <= 1; dx++) { char n = d.T(x + dx, row + dy); if (n == '_' || n == 'p' || n == 'w' || n == 'O') { nearRoad = true; break; } }
                        if (nearRoad) continue;
                        int k = rnd.Next(tufts.Length);
                        var go = new GameObject("grass_tuft");
                        go.transform.SetParent(root, false);
                        go.transform.position = new Vector3(x + 0.15f + (float)rnd.NextDouble() * 0.7f, d.h - 1 - row + (float)rnd.NextDouble() * 0.8f, 0);
                        var sr = go.AddComponent<SpriteRenderer>();
                        sr.sprite = tufts[k]; sr.sortingOrder = -6; sr.flipX = rnd.Next(2) == 0; sr.sharedMaterial = grass;
                        swaying++;
                    }
            }

            var level = Object.FindFirstObjectByType<WorldInfo>();
            if (level == null) { Debug.LogWarning("[GameBuilder] no WorldInfo for the weather"); return; }
            var ws = level.gameObject.AddComponent<WeatherSystem>();
            ws.drop = WOne("Effects/rain_drop.png");
            ws.splash = WSheet("Effects/rain_splash_anim_8x8.png");
            ws.rainLoop = AssetDatabase.LoadAssetAtPath<AudioClip>($"{GameRoot}/Audio/amb_rain_loop.wav");
            Debug.Log($"[GameBuilder] weather: {swaying} swaying plants, rain art {(ws.drop != null)}/{ws.splash?.Length ?? 0}, sound {(ws.rainLoop != null)}");
        }
    }
}
