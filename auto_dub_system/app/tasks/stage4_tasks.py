"""
Stage 4 tasks: Merge final audio.
"""
from app.tasks.celery_app import celery_app

@celery_app.task
def process_stage4(stage3_result):
    # merge audio
    return {"status": "stage4_complete"}
