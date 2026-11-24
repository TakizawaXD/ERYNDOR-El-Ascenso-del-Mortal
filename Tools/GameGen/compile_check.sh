#!/usr/bin/env bash
# Compile-checks the game's C# against the real Unity 6000.6.4f1 assemblies (no Editor needed).
# usage: bash compile_check.sh <scratch dir>
set -e
OUT="$1"; mkdir -p "$OUT"
E="C:/Program Files/Unity/Hub/Editor/6000.6.4f1/Editor/Data"
PKG="$E/Resources/PackageManager/BuiltInPackages"
CSC=("$E/DotNetSdk/dotnet.exe" "$E/DotNetSdk/sdk/8.0.318/Roslyn/bincore/csc.dll")
EXTRAS=$(ls -d G:/Temp/claude/4d4eef840d110612/eece98ac-8e40-4b54-a3d3-cbd163fbaace/scratchpad/UnityTest/Library/PackageCache/com.unity.2d.tilemap.extras@*/Runtime)
TF="$PKG/com.unity.test-framework"

refs() { echo "-r:\"$E/NetStandard/ref/2.1.0/netstandard.dll\""; for f in "$E"/Managed/UnityEngine/*.dll; do echo "-r:\"$f\""; done; }
srcs() { find "$1" -name "*.cs" | sed 's/.*/"&"/'; }

build() { # name defines refs... -- sources...
  local name="$1"; shift; local defs="$1"; shift
  { echo "-nologo -target:library -nostdlib -langversion:9 -nowarn:1701,1702,0618,0649,0414 -out:\"$OUT/$name.dll\""
    echo "-define:$defs"; refs; cat; } > "$OUT/$name.rsp"
  "${CSC[@]}" @"$OUT/$name.rsp" 2>&1 | grep -E "error|warning CS0(108|114|162|168|219)" | grep -v "^$" | head -40 || true
  [ -f "$OUT/$name.dll" ] && echo "OK $name" || echo "FAIL $name"
}

rm -f "$OUT"/*.dll
srcs "$PKG/com.unity.ugui/Runtime/UGUI" | build UnityEngine.UI "PACKAGE_PHYSICS;PACKAGE_PHYSICS2D;PACKAGE_TILEMAP;PACKAGE_ANIMATION;UNITY_2023_1_OR_NEWER;UNITY_6000_0_OR_NEWER"
srcs "$EXTRAS" | build Unity.2D.Tilemap.Extras "UNITY_2023_1_OR_NEWER"
srcs "G:/Juegos/Assets/Scripts" | build WoodsArt.Runtime "X"
{ srcs "G:/Juegos/Assets/Game/Scripts"; echo "-r:\"$OUT/UnityEngine.UI.dll\""; } | build WoodsGame "UNITY_EDITOR"
if [ -d "G:/Juegos/Assets/Game/Editor" ]; then
  { srcs "G:/Juegos/Assets/Game/Editor"; srcs "G:/Juegos/Assets/Editor/ArtPipeline"; echo "\"G:/Juegos/Tools/GameGen/compile_stub.cs\"";
    echo "-r:\"$OUT/UnityEngine.UI.dll\""; echo "-r:\"$OUT/WoodsGame.dll\""; echo "-r:\"$OUT/WoodsArt.Runtime.dll\""; echo "-r:\"$OUT/Unity.2D.Tilemap.Extras.dll\""; } | build WoodsGame.Editor "UNITY_EDITOR;WOODS_HAS_TILEMAP_EXTRAS;WOODS_HAS_TILEMAP_EDITOR"
fi
