// Vegetation swaying in the wind: a sprite shader that bends the top of the sprite while the foot (pivot, y = 0) stays planted.
// Global inputs (set every frame by WeatherSystem): _WindStrength (steady breeze, rises with rain), _WindGust (0..1 gust envelope),
// _WindDir (+1 / -1). Each plant gets its own phase from its world position, so a field ripples instead of moving in lockstep.
// Batching is disabled so vertex positions stay in object space (feet at y = 0).
Shader "Woods/SpriteWind"
{
    Properties
    {
        [PerRendererData] _MainTex ("Sprite", 2D) = "white" {}
        _Color ("Tint", Color) = (1,1,1,1)
        _Sway ("Sway (units of bend per unit of height)", Float) = 0.05
        _Flutter ("Flutter", Float) = 0.02
        _Speed ("Speed", Float) = 1.0
        [HideInInspector] _RendererColor ("RendererColor", Color) = (1,1,1,1)
        [HideInInspector] _Flip ("Flip", Vector) = (1,1,1,1)
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "IgnoreProjector"="True" "RenderType"="Transparent" "PreviewType"="Plane"
               "CanUseSpriteAtlas"="True" "DisableBatching"="True" }
        Cull Off Lighting Off ZWrite Off
        Blend One OneMinusSrcAlpha
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment SpriteFrag
            #pragma target 2.0
            #pragma multi_compile_instancing
            #include "UnitySprites.cginc"

            float _Sway, _Flutter, _Speed;
            float _WindStrength, _WindGust, _WindDir;

            v2f vert (appdata_t IN)
            {
                v2f OUT;
                UNITY_SETUP_INSTANCE_ID(IN);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(OUT);
                float4 p = UnityFlipSprite(IN.vertex, _Flip);
                float h = max(p.y, 0.0);
                float2 root = float2(unity_ObjectToWorld._m03, unity_ObjectToWorld._m13);
                float phase = root.x * 0.37 + root.y * 0.21;
                float t = _Time.y * _Speed;
                float dir = (_WindDir == 0) ? 1.0 : _WindDir;
                // slow lean that follows the gusts + a sway around it + a quick flutter near the top
                float lean = _WindGust * (0.55 + 0.45 * sin(t * 0.7 + phase * 0.5));
                float sway = sin(t * 1.6 + phase) * 0.6 + sin(t * 2.7 + phase * 1.7) * 0.25;
                float bend = (_WindStrength * sway + lean * 1.4 * dir) * _Sway;
                float flut = sin(t * 7.0 + phase * 3.1 + h * 2.0) * _Flutter * (_WindStrength + _WindGust);
                p.x += (bend + flut) * pow(h, 1.2);
                p.y -= abs(bend) * 0.15 * h;          // bending shortens the plant a little
                OUT.vertex = UnityObjectToClipPos(p);
                OUT.texcoord = IN.texcoord;
                OUT.color = IN.color * _Color * _RendererColor;
                return OUT;
            }
            ENDCG
        }
    }
}
