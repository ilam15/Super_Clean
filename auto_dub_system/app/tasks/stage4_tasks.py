"""
Stage 4 tasks: Connect final audio with video.
"""

from app.tasks.celery_app import celery_app
from app.tasks.celery_app import celery_app
from app.services.chunker import ChunkingManager

@celery_app.task
def process_stage4(stage3_result):
    """
    Expected stage3_result format:
    {
        "final_audio_path": "outputs/audio/final.wav",
        "video_path": "inputs/video.mp4",
        "job_id": "123"
    }
    """

    try:
        final_audio_path = stage3_result["final_audio_path"]
        video_path = stage3_result["video_path"]
        job_id = stage3_result.get("job_id", "default")

        # Call your existing function
        final_video_path = ChunkingManager.final_connect_with_video(
            final_audio_path,
            video_path
        )

        return {
            "status": "stage4_complete",
            "final_video_path": final_video_path,
            "job_id": job_id
        }

    except Exception as e:
        return {
            "status": "stage4_failed",
            "error": str(e)
        }
