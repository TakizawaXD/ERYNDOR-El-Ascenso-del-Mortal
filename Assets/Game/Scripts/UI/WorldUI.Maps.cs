using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace WoodsGame
{
    /// <summary>Map screen (M) for several maps: in a town or zone it opens the local map (streets, houses, gates, camp,
    /// shops); Left/Right switch to the world map, which marks the towns, the discovered regions and camps.
    /// The minimap always shows the map that is loaded.</summary>
    public partial class WorldUI
    {
        bool _worldView;
        Text _mapTitle, _mapHint;
        readonly List<Text> _mapLabels = new List<Text>();
        int _labelCount;
        Texture2D _worldFog;
        Vector2 _mapSize = new Vector2(240, 160);
        static readonly Color CityGold = new Color32(0xff, 0xd0, 0x5a, 0xff);
        static readonly Color GateCyan = new Color32(0x7f, 0xe6, 0xff, 0xff);

        public static bool MapOpen => _i != null && _i._map.gameObject.activeSelf;
        /// <summary>True while the map screen shows the world map (false: the local map of the town/zone).</summary>
        public static bool MapShowsWorld => _i != null && _i._worldView;

        void BuildMapTexts()
        {
            var box = _map.Find("Box");
            _mapTitle = Label(box, "MAPA DEL MUNDO", new Vector2(0.5f, 1), new Vector2(0, -2), TextAnchor.UpperCenter, Ink);
            _mapHint = Label(box, "", new Vector2(0.5f, 0), new Vector2(0, 1), TextAnchor.LowerCenter, Ink2);
        }

        static WorldInfo Wi => WorldInfo.Current;
        static bool InWorldMap => Wi == null || Wi.IsWorld;

        // ---------------------------------------------------------------- textures
        /// <summary>The overworld map with fog over the regions not discovered yet (works from any map).</summary>
        Texture2D WorldMapTexture(bool fog)
        {
            var wi = Wi;
            var sprite = wi != null && wi.IsWorld ? wi.mapSprite : (GameAssets.I ? GameAssets.I.worldMap : null);
            if (sprite == null) return null;
            var src = sprite.texture;
            string[] rows = wi != null && wi.IsWorld ? wi.regionRows : MapDB.WorldRegions;
            if (!fog || rows == null || rows.Length == 0) return src;
            if (_worldFog == null || _worldFog.width != src.width || _worldFog.height != src.height)
                _worldFog = new Texture2D(src.width, src.height, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point };
            Color32[] px;
            try { px = src.GetPixels32(); } catch { return src; }
            var s = GameManager.State;
            int w = src.width, h = src.height, rh = rows.Length, sw = MapDB.SurfaceW;
            for (int y = 0; y < h; y++)
            {
                string row = rows[rh - 1 - y * rh / h];
                for (int x = 0; x < w; x++)
                {
                    char r = row[Mathf.Min(row.Length - 1, x * Mathf.Min(sw, row.Length) / w)];
                    if (s.Has("region_" + r)) continue;
                    int i = y * w + x;
                    var c = px[i];
                    byte g = (byte)((c.r + c.g + c.b) / 9 + 20);
                    px[i] = ((x + y) & 1) == 0 ? new Color32(g, g, (byte)(g + 12), 255) : new Color32((byte)(g - 8), (byte)(g - 8), g, 255);
                }
            }
            _worldFog.SetPixels32(px);
            _worldFog.Apply();
            return _worldFog;
        }

        Texture2D LocalMapTexture() => Wi != null && Wi.mapSprite != null ? Wi.mapSprite.texture : null;

        // ---------------------------------------------------------------- opening / switching
        void ShowMap(bool world)
        {
            _worldView = world || InWorldMap;
            var tex = _worldView ? WorldMapTexture(true) : LocalMapTexture();
            _mapImg.texture = tex;
            // fit the picture in the panel keeping its proportions (the world 240x160, a town ~76x58 scaled up)
            Vector2 src = tex != null ? new Vector2(tex.width, tex.height) : new Vector2(240, 160);
            float k = Mathf.Min(240f / src.x, 150f / src.y);
            _mapSize = new Vector2(Mathf.Floor(src.x * k), Mathf.Floor(src.y * k));
            _mapImg.rectTransform.sizeDelta = _mapSize;
            _mapImg.rectTransform.anchoredPosition = new Vector2(0, -2);
            var def = Wi != null ? MapDB.Get(Wi.mapId) : null;
            var cave = WorldInfo.PlayerCave;
            _mapTitle.text = UIRoot.Pretty(cave != null ? cave.title : _worldView ? "MAPA DEL MUNDO" : def != null ? def.title : "MAPA");
            _mapHint.text = UIRoot.Pretty(InWorldMap ? "M CERRAR" : _worldView ? "IZQUIERDA/DERECHA: MAPA LOCAL · M CERRAR" : "IZQUIERDA/DERECHA: MAPA DEL MUNDO · M CERRAR");
        }

        void MapInput()
        {
            if (InWorldMap) return;
            if (GameInput.Left || GameInput.Right) { ShowMap(!_worldView); Sfx.Play("select", 0.5f); }
        }

        // ---------------------------------------------------------------- markers + labels
        int _markK;

        void Mark(Vector2 uv, Color col, int size)
        {
            Transform t = _markK < _markers.childCount ? _markers.GetChild(_markK) : UIRoot.Img(_markers, null, false).transform;
            _markK++;
            var img = t.GetComponent<Image>();
            img.color = col; img.gameObject.SetActive(true);
            var rt = img.rectTransform;
            rt.anchorMin = rt.anchorMax = Vector2.zero;
            rt.sizeDelta = new Vector2(size, size);
            rt.anchoredPosition = new Vector2(uv.x * _mapSize.x, uv.y * _mapSize.y);
        }

        void MapLabel(Vector2 uv, string text, Color col)
        {
            Text t;
            if (_labelCount < _mapLabels.Count) t = _mapLabels[_labelCount];
            else { t = Label(_mapImg.transform, "", Vector2.zero, Vector2.zero, TextAnchor.LowerCenter, col); _mapLabels.Add(t); }
            _labelCount++;
            t.gameObject.SetActive(true);
            t.text = UIRoot.Pretty(text);
            t.color = col;
            float x = Mathf.Clamp(uv.x * _mapSize.x, 24, _mapSize.x - 24);
            t.rectTransform.anchoredPosition = new Vector2(x, uv.y * _mapSize.y + 3);
        }

        void UpdateMapView(WorldInfo wi, PlayerController p)
        {
            foreach (Transform c in _markers) c.gameObject.SetActive(false);
            for (int i = 0; i < _mapLabels.Count; i++) _mapLabels[i].gameObject.SetActive(false);
            _markK = 0; _labelCount = 0;
            bool blink = (_blink % 0.6f) < 0.4f;
            var s = GameManager.State;
            if (_worldView)
            {
                float W = MapDB.SurfaceW, H = MapDB.SurfaceH;
                Vector2 UV(Vector2 world) => new Vector2(world.x / W, world.y / H);
                // discovered regions (names at the middle of each region)
                foreach (var kv in RegionCentres())
                    if (s.Has("region_" + kv.Key)) MapLabel(UV(kv.Value), RegionName(kv.Key), Ink2);
                // camps seen in the overworld ("fire_x_y" flags)
                foreach (var f in s.flags)
                {
                    if (!f.StartsWith("fire_")) continue;
                    var parts = f.Split('_');
                    if (parts.Length == 3 && int.TryParse(parts[1], out int fx) && int.TryParse(parts[2], out int fy))
                        Mark(UV(new Vector2(fx, fy)), new Color32(0xfe, 0xae, 0x34, 0xff), 3);
                }
                // towns and the volcano (places of the one map), and the cave mouths you have found
                foreach (var m in MapDB.Places)
                {
                    if (m.kind == "cave") continue;
                    if (m.kind == "zone" && !s.Has("region_g")) continue;
                    var at = UV(m.Center);
                    Mark(at, m.kind == "zone" ? UIRoot.Red : CityGold, 5);
                    MapLabel(at + new Vector2(0, 2.5f / _mapSize.y), m.title, m.kind == "zone" ? UIRoot.Red : CityGold);
                }
                foreach (var m in MapDB.Places)
                {
                    if (m.kind != "cave" || !s.Has("region_" + m.region)) continue;
                    var g = MapGate.Find(m.id + ":IN");
                    if (g != null) Mark(UV(g.transform.position), GateCyan, 4);
                }
                if (wi != null && wi.IsWorld)
                {
                    foreach (var e in FindObjectsByType<EnemyController>(FindObjectsSortMode.None))
                        if (e.isBoss && !e.health.IsDead) Mark(UV(e.transform.position), UIRoot.Red, 4);
                    var here = WorldInfo.PlayerCave;           // underground: you are shown at the cave's mouth
                    var hg = here != null ? MapGate.Find(here.id + ":IN") : null;
                    if (blink && p != null) Mark(UV(hg != null ? (Vector2)hg.transform.position
                                                   : Interior.Current != null ? Interior.Current.outside : (Vector2)p.transform.position), Color.white, 4);
                }
                else if (blink && wi != null)
                {
                    var here = MapDB.Get(wi.mapId);
                    if (here != null && here.hasArea) Mark(UV(here.WorldAnchor), Color.white, 4);
                }
                return;
            }
            // local map of a town / zone
            Vector2 LUV(Vector2 local) => new Vector2(local.x / wi.width, local.y / wi.height);
            foreach (var f in Campfire.All) Mark(LUV(f.transform.position), new Color32(0xfe, 0xae, 0x34, 0xff), 4);
            foreach (var sh in FindObjectsByType<ShopStall>(FindObjectsSortMode.None))
                if (sh.transform.position.x < wi.width) Mark(LUV(sh.transform.position), UIRoot.Gold, 3);
            foreach (var g in MapGate.All)
            {
                Mark(LUV(g.transform.position), GateCyan, 4);
                MapLabel(LUV(g.transform.position) + new Vector2(0, 3f / _mapSize.y), string.IsNullOrEmpty(g.label) ? "SALIDA" : g.label, GateCyan);
            }
            foreach (var e in FindObjectsByType<EnemyController>(FindObjectsSortMode.None))
                if (e.isBoss && !e.health.IsDead) Mark(LUV(e.transform.position), UIRoot.Red, 5);
            if (blink && p != null)
            {
                Vector2 pos = Interior.Current != null ? Interior.Current.outside : (Vector2)p.transform.position;
                Mark(LUV(pos), Color.white, 4);
            }
        }

        Dictionary<char, Vector2> _regionCentres;

        Dictionary<char, Vector2> RegionCentres()
        {
            if (_regionCentres != null) return _regionCentres;
            var rows = Wi != null && Wi.IsWorld ? Wi.regionRows : MapDB.WorldRegions;
            var sum = new Dictionary<char, Vector3>();
            if (rows != null)
                for (int r = 0; r < rows.Length; r++)
                    for (int x = 0; x < rows[r].Length; x += 2)
                    {
                        char c = rows[r][x];
                        sum.TryGetValue(c, out var v);
                        sum[c] = v + new Vector3(x + 0.5f, rows.Length - r - 0.5f, 1);
                    }
            _regionCentres = new Dictionary<char, Vector2>();
            foreach (var kv in sum)
                if (kv.Value.z > 0 && kv.Value.x / kv.Value.z < MapDB.SurfaceW)        // the underground is not on the world map
                    _regionCentres[kv.Key] = new Vector2(kv.Value.x / kv.Value.z, kv.Value.y / kv.Value.z);
            // the town regions are labelled by their town marker instead
            foreach (var m in MapDB.Maps) if (m.hasArea && m.kind == "city" && m.region != 'a') _regionCentres.Remove(m.region);
            return _regionCentres;
        }

        static string RegionName(char id)
        {
            var wi = Wi;
            if (wi != null && wi.IsWorld) { var n = wi.NameOf(id); if (!string.IsNullOrEmpty(n)) return n; }
            return MapDB.RegionName(id);
        }
    }
}
