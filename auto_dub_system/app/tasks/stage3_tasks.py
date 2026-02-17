"""
Stage 3 tasks: STT + Translate + TTS.
"""
from app.tasks.celery_app import celery_app

@celery_app.task
def process_stage3(stage2_result):
    # STT
    # Translate
    # TTS
    return {"status": "stage3_complete"}
