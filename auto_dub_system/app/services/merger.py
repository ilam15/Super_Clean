"""
FFmpeg merge layers.
"""
import subprocess
from pydub import AudioSegment
from src.core.config import settings
from src.core.logger import logger

class AudioVideoMerger:
    def __init__(self):
        """
        Initialize the Merger with a temp directory from settings.
        """
        self.temp_dir = getattr(settings, "TEMP_DIR", "temp_merger")
        os.makedirs(self.temp_dir, exist_ok=True)

    def mix_audio_layers(self, audio_layers):
        """
        Mixes multiple audio files into a single WAV file.
        
        :param audio_layers: List of dicts, each containing:
                             - 'path' (str): Path to audio file
                             - 'volume' (float, optional): Gain adjustment in dB (e.g., -3.0). Default 0.
        :return: Path to the mixed audio file.
        """
        if not audio_layers:
            logger.error("No audio layers provided for mixing.")
            return None

        logger.info(f"Mixing {len(audio_layers)} audio layers...")
        
        try:
            # 1. Initialize base with the first track
            first_layer = audio_layers[0]
            if not os.path.exists(first_layer['path']):
                logger.error(f"Audio file not found: {first_layer['path']}")
                return None

            mixed_audio = AudioSegment.from_file(first_layer['path'])
            if 'volume' in first_layer and first_layer['volume'] != 0:
                mixed_audio = mixed_audio + float(first_layer['volume'])

            # 2. Overlay remaining tracks
            for i, layer in enumerate(audio_layers[1:], start=1):
                path = layer['path']
                if not os.path.exists(path):
                    logger.warning(f"Audio layer {i} not found at {path}, skipping.")
                    continue

                segment = AudioSegment.from_file(path)
                
                # Apply volume adjustment if specified
                if 'volume' in layer and layer['volume'] != 0:
                    segment = segment + float(layer['volume'])
                
                # Overlay current segment onto the mixed audio
                # Note: 'overlay' maintains the duration of the first argument by default.
                # If we want to extend, we might to handle position if needed.
                # Here we assume all tracks start at 0:00.
                mixed_audio = mixed_audio.overlay(segment)

            # 3. Export mixed result
            output_filename = f"mixed_{os.path.basename(first_layer['path'])}_{os.getpid()}.wav"
            output_path = os.path.join(self.temp_dir, output_filename)
            
            mixed_audio.export(output_path, format="wav")
            logger.info(f"Mixed audio saved temporarily to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error mixing audio layers: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def merge_video_audio(self, video_path, audio_path, output_path):
        """
        Merges a video file with a new audio file, replacing the original audio.
        
        :param video_path: Path to the source video.
        :param audio_path: Path to the new combined audio.
        :param output_path: Path where the final video will be saved.
        """
        try:
            logger.info(f"Merging video: {video_path} + Audio: {audio_path} -> {output_path}")
            
            if not os.path.exists(video_path):
                logger.error(f"Video path does not exist: {video_path}")
                return None
            if not os.path.exists(audio_path):
                logger.error(f"Audio path does not exist: {audio_path}")
                return None

            # FFmpeg command:
            # -map 0:v:0 -> Stream 0 (Video file), video track 0
            # -map 1:a:0 -> Stream 1 (Audio file), audio track 0
            # -c:v copy  -> Copy video stream (no re-encoding, extremely fast)
            # -c:a aac   -> Encode audio to AAC (standard for MP4)
            # -shortest  -> End output when shortest stream ends (optional)
            command = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-strict", "experimental",
                output_path
            ]
            
            process = subprocess.run(
                command, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            if os.path.exists(output_path):
                logger.info("Merge successful.")
                return output_path
            else:
                logger.error("Merge failed. Output file not created.")
                return None

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg merge failed with error: {e.stderr.decode()}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during merge: {e}")
            return None

    def process_and_merge(self, video_path, audio_layers, output_path, keep_temp=False):
        """
        Main entry point to mix multiple audio layers and merge with a video.
        
        :param video_path: Source video path.
        :param audio_layers: List of dicts [{'path': '...', 'volume': 0}]
        :param output_path: Destination video path.
        :param keep_temp: If True, does not delete the intermediate mixed wav.
        :return: Path to final video or None.
        """
        # 1. Mix Audio
        mixed_audio_path = self.mix_audio_layers(audio_layers)
        if not mixed_audio_path:
            return None

        # 2. Merge with Video
        final_output = self.merge_video_audio(video_path, mixed_audio_path, output_path)

        # 3. Cleanup
        if not keep_temp and mixed_audio_path and os.path.exists(mixed_audio_path):
            try:
                os.remove(mixed_audio_path)
                logger.info(f"Cleaned up temp audio: {mixed_audio_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")

        return final_output
