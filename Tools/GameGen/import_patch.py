p = 'G:/Juegos/Assets/Editor/ArtPipeline/ArtImportPostprocessor.cs'
s = open(p, encoding='utf8').read()
a = '            if (path.Contains("/Vegetation/") || path.Contains("/Props/") || path.Contains("/Decorations/"))'
b = '            if (path.Contains("/Vegetation/") || path.Contains("/Props/") || path.Contains("/Decorations/") ||\n                path.Contains("/World/Nature/") || path.Contains("/World/Structures/"))'
assert a in s; s = s.replace(a, b)
a = '            ti.npotScale = TextureImporterNPOTScale.None;\n'
b = a + '            if (file == "world_map") ti.isReadable = true;            // the map UI paints fog over it\n'
assert a in s; s = s.replace(a, b, 1)
open(p, 'w', encoding='utf8').write(s)
print('ok')
