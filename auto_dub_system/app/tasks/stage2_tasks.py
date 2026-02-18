from celery import group, chain, chord
from app.tasks.celery_app import celery_app
from app.tasks.stage3_tasks import process_stage3

# Import services
from app.services.gender_detection import GenderDetector
from app.services.stt import speech_to_text
from app.services.translation_matcher import translation_matcher
from app.services.tts import text_to_speech

# ----------------- SERVICE WRAPPER TASKS -----------------

@celery_app.task
def task_gender(chunk):
    # Determine gender for this chunk
    from app.services.gender_detection import GenderDetector
    import logging
    logger = logging.getLogger(__name__)

    detector = GenderDetector()
    try:
        gender_res = detector.predict(chunk["chunk_path"])
        chunk["gender"] = gender_res.get("gender", "male")
        logger.info(f"Chunk {chunk['chunk_path']} predicted gender: {chunk['gender']} (conf: {gender_res.get('confidence', 0.0):.2f})")
    except Exception as e:
        logger.error(f"Gender detection failed for chunk {chunk['chunk_path']}: {e}")
        chunk["gender"] = "male" # Default fallback
    return chunk

@celery_app.task
def task_stt(chunk):
    # Call Sarvam STT
    return speech_to_text(
        chunk["chunk_path"],
        chunk["start_time"],
        chunk["end_time"],
        chunk["speaker_no"],
        chunk["overlap"],
        chunk.get("gender", "unknown")
    )

@celery_app.task
def task_align(stt_result):
    # Align translation/text
    # stt_result contains text, start, end...
    return translation_matcher(
        stt_result.get("text", ""),
        stt_result["start_time"],
        stt_result["end_time"],
        stt_result["speaker_no"],
        stt_result["overlap"],
        stt_result["gender"]
    )

@celery_app.task
def task_tts(align_result):
    # Generate TTS
    return text_to_speech(
        align_result["aligned_text"],
        align_result["start_time"],
        align_result["end_time"],
        align_result["speaker_no"],
        align_result["overlap"],
        align_result["gender"]
    )

# ----------------- STAGE 2 MASTER -----------------

@celery_app.task(bind=True)
def process_stage2(self, stage1_result):
    """
    Receives diarization_data from stage1.
    Spawns parallel processing for chunks.
    Chains to stage3 for merging.
    """
    chunks = stage1_result.get("chunks", [])
    video_path = stage1_result.get("video_path")
    
    if not chunks:
        # If no chunks, just callback stage3 with empty list? Or fail?
        # Let's callback stage3 with empty list to handle it gracefully if possible
        # Or just return empty result
        return process_stage3.s([], video_path).delay()
        
    chunk_chains = []
    
    for chunk in chunks:
        # Create a processing chain for each chunk
        # Adjust input format for task_gender if needed. task_gender takes chunk dict directly.
        c = chain(
            task_gender.s(chunk),
            task_stt.s(),
            task_align.s(),
            task_tts.s()
        )
        chunk_chains.append(c)
        
    # Create a chord: execute chunk_chains in parallel (group), then call process_stage3 -> process_stage4
    from app.tasks.stage4_tasks import process_stage4
    callback = (process_stage3.s(video_path) | process_stage4.s())
    workflow = chord(chunk_chains, body=callback)
    
    return self.replace(workflow)
