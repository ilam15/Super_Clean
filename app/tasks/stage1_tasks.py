"""
Stage 1 tasks: Diarization + Overlap.
"""
from app.tasks.celery_app import celery_app
# from app.services.diarization import detect_speakers
# from app.services.overlap_detector import detect_overlap

@celery_app.task
def process_stage1(video_path):
    # run diarization
    # run overlap detection
    return {"status": "stage1_complete", "video_path": video_path}
