from app.tasks.celery_app import celery_app
from app.services.chunker import ChunkingManager

@celery_app.task
def process_stage3(stage2_results, video_path):
    """
    Callback for stage2 chord.
    Receives list of processed chunks from stage2 parallel processing.
    Merges them into segments and then final audio.
    """
    try:
        # stage2_results is a list of dicts. 
        # Each dict contains 'audio_path', 'start_time', 'end_time', 'speaker_no', 'overlap'
        # provided by task_tts return value.
        
        # Merge chunks into segments
        segments = ChunkingManager.chunk_to_segments(stage2_results)
        
        # Merge segments into final audio
        final_audio_path = ChunkingManager.final_audio_connect(segments)
        
        return {
            "status": "stage3_complete",
            "final_audio_path": final_audio_path,
            "video_path": video_path
        }
    except Exception as e:
        return {
            "status": "stage3_failed",
            "error": str(e)
        }