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
    from app.services.gender_detection import get_gender_detector
    import logging
    logger = logging.getLogger(__name__)

    detector = get_gender_detector()
    try:
        # If gender is already assigned (via majority vote in stage2), use it
        if chunk.get("gender") and chunk.get("gender") != "unknown":
            logger.info(f"Using pre-assigned gender for chunk {chunk['chunk_path']}: {chunk['gender']}")
            return chunk

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
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"STT started for chunk: {chunk['chunk_path']}")
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
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Alignment started for speaker {stt_result['speaker_no']} at {stt_result['start_time']}")
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
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"TTS started for text: '{align_result['aligned_text'][:30]}...' speaker: {align_result['speaker_no']}")
    res = text_to_speech(
        align_result["aligned_text"],
        align_result["start_time"],
        align_result["end_time"],
        align_result["speaker_no"],
        align_result["overlap"],
        align_result["gender"]
    )
    logger.info(f"TTS completed: {res.get('audio_path')}")
    return res

# ----------------- STAGE 2 MASTER -----------------

@celery_app.task(bind=True)
def process_stage2(self, stage1_result):
    """
    Receives diarization_data from stage1.
    Spawns parallel processing for chunks.
    Chains to stage3 for merging.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    chunks = stage1_result.get("chunks", [])
    video_path = stage1_result.get("video_path")
    
    logger.info(f"Stage 2 started for video: {video_path}, total chunks: {len(chunks)}")
    
    if not chunks:
        logger.warning("No chunks found in stage1_result. Skipping to stage3/4 with empty data.")
        # Replaces the current task with a chain of stage3 -> stage4 with empty results
        from app.tasks.stage4_tasks import process_stage4
        workflow = (process_stage3.s([], video_path) | process_stage4.s())
        return self.replace(workflow)

    # --- Speaker-level Gender Majority Vote (Production Optimization) ---
    logger.info("Performing speaker-level gender majority vote...")
    from app.services.gender_detection import get_gender_detector
    from collections import Counter
    
    detector = get_gender_detector()
    speaker_votes = {}
    
    for chunk in chunks:
        speaker = chunk.get("speaker_no", "unknown")
        try:
            res = detector.predict(chunk["chunk_path"])
            gender = res.get("gender", "male")
            if speaker not in speaker_votes:
                speaker_votes[speaker] = []
            speaker_votes[speaker].append(gender)
        except Exception as e:
            logger.error(f"Majority vote gender detection failed for chunk {chunk['chunk_path']}: {e}")

    # Calculate final gender per speaker
    speaker_final_gender = {}
    for speaker, votes in speaker_votes.items():
        if votes:
            most_common = Counter(votes).most_common(1)[0][0]
            speaker_final_gender[speaker] = most_common
            logger.info(f"Speaker {speaker} final gender (majority vote): {most_common} (from {len(votes)} samples)")
        else:
            speaker_final_gender[speaker] = "male"

    # Assign final gender to all chunks
    for chunk in chunks:
        chunk["gender"] = speaker_final_gender.get(chunk.get("speaker_no", "unknown"), "male")
        
    chunk_chains = []
    
    for chunk in chunks:
        # Create a processing chain for each chunk
        # task_gender will now see the pre-assigned gender and skip repeated detection
        c = chain(
            task_gender.s(chunk),
            task_stt.s(),
            task_align.s(),
            task_tts.s()
        )
        chunk_chains.append(c)
        
    logger.info(f"Spawning {len(chunk_chains)} parallel chunk processing chains.")
    
    # Create a chord: execute chunk_chains in parallel (group), then call process_stage3 -> process_stage4
    from app.tasks.stage4_tasks import process_stage4
    callback = (process_stage3.s(video_path) | process_stage4.s())
    workflow = chord(chunk_chains, body=callback)
    
    # CRITICAL: Use self.replace to expand the current task into the chord workflow
    # This keeps the task lineage and ensures the chain continues correctly
    self.replace(workflow)
    
    return f"Stage 2 dispatched: {len(chunk_chains)} chunk chains spawned with speaker-level gender voting."
