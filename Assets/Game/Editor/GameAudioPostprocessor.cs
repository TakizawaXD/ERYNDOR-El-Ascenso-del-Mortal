using UnityEditor;
using UnityEngine;

namespace WoodsGame.EditorTools
{
    /// <summary>Import settings for the generated audio: music and ambience are long, so they stay compressed in memory
    /// (Vorbis, loaded in the background; not streamed, so the night layer can be kept sample-locked to the day piece);
    /// short effects are decompressed on load for instant playback.</summary>
    public class GameAudioPostprocessor : AssetPostprocessor
    {
        void OnPreprocessAudio()
        {
            if (!assetPath.StartsWith("Assets/Game/Audio/")) return;
            var imp = (AudioImporter)assetImporter;
            bool longClip = assetPath.Contains("/Music/") || assetPath.Contains("/Ambience/") || assetPath.Contains("/music_") || assetPath.Contains("/amb_");
            var s = imp.defaultSampleSettings;
            if (longClip)
            {
                s.loadType = AudioClipLoadType.CompressedInMemory;
                s.compressionFormat = AudioCompressionFormat.Vorbis;
                s.quality = 0.6f;
                imp.loadInBackground = !assetPath.Contains("jingle_") && !assetPath.Contains("_intro");   // intros are scheduled to the sample
            }
            else
            {
                s.loadType = AudioClipLoadType.DecompressOnLoad;
                s.compressionFormat = AudioCompressionFormat.ADPCM;
            }
            s.preloadAudioData = true;
            imp.defaultSampleSettings = s;
            imp.forceToMono = true;
        }
    }
}
