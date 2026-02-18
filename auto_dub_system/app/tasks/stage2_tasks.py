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
    # Detect gender using GenderDetector
    # chunk is dict with chunk_path
    detector = GenderDetector()
    try:
        gender_res = detector.predict(chunk["chunk_path"])
        chunk["gender"] = gender_res.get("gender", "unknown")
    except Exception as e:
        chunk["gender"] = "unknown"
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
        
    # Create a chord: execute chunk_chains in parallel (group), then call process_stage3
    # Note: chord(header)(callback)
    callback = process_stage3.s(video_path)
    workflow = chord(chunk_chains)(callback)
    
    # We return the workflow signature. 
    # Or replace self with this workflow so celery executes it as part of the chain.
    # self.replace(workflow) is generally safer for deeply nested chains.
    # However, simply returning the result of calling it (AsyncResult) creates a detached task.
    # Returning the signature itself: Celery < 5 doesn't execute chained chords automatically if returned.
    # But usually returning the result of applying the chord works if we are at the end of a chain.
    
    # Since process_stage2 is called via link or chain from stage1...
    # If we return `workflow`, it is a Signature.
    # We probably want to EXECUTE it and return the AsyncResult, or return the Signature for the caller to execute.
    # But stage1 executes a chain that *includes* process_stage2.
    
    # If process_stage2 is a task in a chain: chain(s1, s2).
    # s1 returns result. s2 creates subtasks.
    # The result of s2 becomes the AsyncResult of the sub-workflow if we use replace.
    
    return self.replace(workflow)
