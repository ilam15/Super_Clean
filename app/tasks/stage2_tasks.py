"""
Stage 2 tasks: Chunk + Gender + Lang.
"""
from app.tasks.celery_app import celery_app

@celery_app.task
def process_stage2(stage1_result):
    # chunk audio
    # detect gender
    # detect language
    return {"status": "stage2_complete"}
