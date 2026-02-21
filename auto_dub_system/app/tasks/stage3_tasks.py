from app.tasks.celery_app import celery_app
from pydub import AudioSegment
import os
import logging

logger = logging.getLogger(__name__)

@celery_app.task
def process_stage3(stage2_results, video_path):
    """
    Assembles the final audio track using Absolute Positioning with pydub.
    This fixes the 'Non-monotonic DTS' errors and sync drift.
    """
    try:
        logger.info("Beginning Stage 3: Audio Assembly using pydub timeline...")

        # 1. Get duration of the original video to create a perfect canvas
        original_audio = AudioSegment.from_file(video_path)
        video_duration_ms = len(original_audio)
        
        # 2. Create a silent 'canvas' exactly the length of the video
        final_mix = AudioSegment.silent(duration=video_duration_ms)

        # 3. Layer each TTS chunk onto the canvas
        # stage2_results is a list of results from stage2 (TTS outputs)
        sorted_segments = sorted(stage2_results, key=lambda x: x['start_time'])
        
        for segment in sorted_segments:
            audio_path = segment.get('audio_path')
            start_time_sec = segment.get('start_time')
            
            # Skip if STT/TTS failed for this chunk (it will just remain silent)
            if not audio_path or not os.path.exists(audio_path):
                continue

            try:
                # Load the TTS clip
                clip = AudioSegment.from_file(audio_path)
                
                # Calculate exact position in milliseconds
                position_ms = int(start_time_sec * 1000)
                
                # Overlay onto the main track
                final_mix = final_mix.overlay(clip, position=position_ms)
                
            except Exception as e:
                logger.warning(f"Failed to mix segment at {start_time_sec}s: {e}")

        # 4. Export the final Mixed Audio
        output_audio_path = os.path.join("data/outputs", "final_audio.wav")
        os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
        
        logger.info(f"Exporting final mix to {output_audio_path}...")
        final_mix.export(output_audio_path, format="wav")
        
        return {
            "status": "stage3_complete",
            "final_audio_path": output_audio_path,
            "video_path": video_path
        }
    except Exception as e:
        logger.error(f"Stage 3 failed: {e}")
        raise