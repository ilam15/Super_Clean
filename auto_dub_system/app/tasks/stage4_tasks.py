"""
Stage 4 tasks: Connect final audio with video.
"""

from app.tasks.celery_app import celery_app
from app.services.chunker import ChunkingManager
from pathlib import Path
import uuid

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
        import os
        final_audio_path = stage3_result["final_audio_path"]
        video_path = stage3_result["video_path"]
        job_id = stage3_result.get("job_id", "default")

        os.makedirs("data/outputs", exist_ok=True)
        # Unique name per job — prevents overwriting both locally and on S3
        video_stem = Path(video_path).stem
        unique_id = uuid.uuid4().hex[:8]
        final_video_name = f"{video_stem}_{unique_id}_dubbed.mp4"
        final_video_path = os.path.join("data/outputs", final_video_name)

        # Call your existing function
        ChunkingManager.final_connect_with_video(
            final_audio_path,
            video_path,
            output_path=final_video_path
        )

        # ── S3 Upload + Presigned URL ────────────────────────────────
        presigned_url = None
        try:
            from app.config import settings
            if settings.AWS_S3_BUCKET_NAME and settings.AWS_ACCESS_KEY_ID:
                from app.services.s3_storage import upload_to_s3, generate_presigned_url
                import logging as _log
                _logger = _log.getLogger(__name__)

                s3_key = f"dubbed/{final_video_name}"
                upload_to_s3(final_video_path, s3_key)
                presigned_url = generate_presigned_url(s3_key, expiry=3600)
                _logger.info(f"S3 presigned URL generated: {presigned_url[:80]}...")
            else:
                import logging as _log
                _log.getLogger(__name__).warning(
                    "AWS S3 credentials not configured — skipping S3 upload. "
                    "Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET_NAME in .env"
                )
        except Exception as s3_err:
            import logging as _log
            _log.getLogger(__name__).warning(f"S3 upload failed (using local fallback): {s3_err}")

        return {
            "status": "stage4_complete",
            "final_video_path": final_video_name,  # local filename for /download/ endpoint
            "presigned_url": presigned_url,         # S3 URL if upload succeeded, else None
            "job_id": job_id,
            "transcript": stage3_result.get("transcript", [])
        }

    except Exception as e:
        return {
            "status": "stage4_failed",
            "error": str(e)
        }
