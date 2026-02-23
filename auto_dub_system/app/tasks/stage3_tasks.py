from app.tasks.celery_app import celery_app
from pydub import AudioSegment
import os
import logging

logger = logging.getLogger(__name__)

@celery_app.task
def process_stage3(stage2_results, video_path, background_path=None):
    """
    Assembles the final audio track using Absolute Positioning with pydub.
    This fixes the 'Non-monotonic DTS' errors and sync drift.
    """
    try:
        logger.info("Beginning Stage 3: Audio Assembly using pydub timeline...")

        # 1. Get duration of the original video to create a perfect canvas
        original_audio = AudioSegment.from_file(video_path)
        video_duration_ms = len(original_audio)
        
        # 2. Create the 'canvas' exactly the length of the video
        if background_path and os.path.exists(background_path):
            logger.info(f"Using background noise track: {background_path}")
            final_mix = AudioSegment.from_file(background_path)
            # Ensure it matches the video duration exactly
            if len(final_mix) < video_duration_ms:
                final_mix += AudioSegment.silent(duration=video_duration_ms - len(final_mix))
            final_mix = final_mix[:video_duration_ms]
            # Lower background audio slightly to make TTS clearer
            final_mix = final_mix - 3
        else:
            logger.info("No background track found, using silent canvas.")
            final_mix = AudioSegment.silent(duration=video_duration_ms)

        # 3. Layer each TTS chunk onto the canvas
        # Filter overlapping segments, skipping the shorter one
        valid_segments = [s for s in stage2_results if s.get('audio_path') and os.path.exists(s.get('audio_path'))]
        
        while True:
            overlap_found = False
            valid_segments.sort(key=lambda x: x.get('start_time', 0))
            
            for i in range(len(valid_segments) - 1):
                s1 = valid_segments[i].get('start_time', 0)
                e1 = valid_segments[i].get('end_time', s1)
                
                s2 = valid_segments[i+1].get('start_time', 0)
                e2 = valid_segments[i+1].get('end_time', s2)
                
                if s2 < e1:
                    dur1 = e1 - s1
                    dur2 = e2 - s2
                    if dur1 >= dur2:
                        valid_segments.pop(i + 1)
                    else:
                        valid_segments.pop(i)
                    overlap_found = True
                    break
                    
            if not overlap_found:
                break
                
        for segment in valid_segments:
            audio_path = segment.get('audio_path')
            start_time_sec = segment.get('start_time')

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