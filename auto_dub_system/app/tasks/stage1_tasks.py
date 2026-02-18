from celery import chain
from app.tasks.celery_app import celery_app
from app.config import settings

from app.services.audio_extractor import audio_separator
from app.services.diarization import speaker_diarization
from app.services.overlap_detector import overlapping_audio_split
from app.services.segment_separation import SegmentSeparator
from app.services.chunker import chunk_separation


# ---------- TASK 1 ----------
@celery_app.task
def task_audio_separator(video_path):
    return audio_separator(video_path)


# ---------- TASK 2 ----------
@celery_app.task
def task_diarization(audio_path):
    res = speaker_diarization(audio_path, use_auth_token=settings.HF_TOKEN)
    res["audio_path"] = audio_path
    return res


# ---------- TASK 3 (Conditional) ----------
@celery_app.task
def task_overlap_split(diarization_data):
    if diarization_data["overlap"]:
        # Fixing argument order from previous version
        diarization_data["separated_audio"] = overlapping_audio_split(
            diarization_data["timestamps"],
            diarization_data["speaker_count"],
            diarization_data["audio_path"],
            diarization_data["overlap"]
        )
    return diarization_data


# ---------- TASK 4 ----------
@celery_app.task
def task_segment(diarization_data):
    # Fix: Ensure overlap_flags is a list matching timestamps length
    overlap_flags = [s["overlap"] for s in diarization_data["segments"]]
    
    segments = SegmentSeparator.segment_separation(
        diarization_data["audio_path"],
        diarization_data["timestamps"],
        diarization_data["speaker_labels"],
        overlap_flags
    )
    diarization_data["segments"] = segments
    return diarization_data


# ---------- TASK 4.5: SPEAKER ANALYSIS ----------
@celery_app.task
def task_speaker_analysis(diarization_data):
    """
    Analyzes all segments for each unique speaker and determines a canonical gender.
    Prevents voice 'flipping' during the dubbing process.
    """
    from app.services.gender_detection import GenderDetector
    from collections import defaultdict

    segments = diarization_data.get("segments", [])
    if not segments:
        diarization_data["speaker_map"] = {}
        return diarization_data

    # Group segments by speaker
    speaker_segments = defaultdict(list)
    for seg in segments:
        speaker_segments[seg["speaker_no"]].append(seg)

    detector = GenderDetector()
    speaker_map = {}

    for speaker_id, segs in speaker_segments.items():
        # Find the longest segment for the best gender detection accuracy
        longest_seg = max(segs, key=lambda x: x.get("duration", 0))
        
        try:
            res = detector.predict(longest_seg["segment_path"])
            gender = res.get("gender", "male")
            confidence = res.get("confidence", 0.0)
            
            # Use 'unknown' if confidence is truly abysmal, 
            # but usually we want a solid guess (male/female)
            if gender == "unknown" and confidence < 0.3:
                gender = "male" # Default fallback
                
            speaker_map[speaker_id] = {
                "gender": gender,
                "confidence": confidence,
                "canon_segment": longest_seg["segment_path"]
            }
            logger.info(f"👤 Speaker {speaker_id} canonical gender: {gender} (conf: {confidence:.2f})")
        except Exception as e:
            logger.error(f"Failed gender analysis for speaker {speaker_id}: {e}")
            speaker_map[speaker_id] = {"gender": "male", "confidence": 0.0}

    diarization_data["speaker_map"] = speaker_map
    return diarization_data


# ---------- TASK 5 ----------
@celery_app.task
def task_chunk(diarization_data, video_path=None):
    all_chunks = []

    speaker_map = diarization_data.get("speaker_map", {})

    for idx, seg in enumerate(diarization_data["segments"]):
        # Get canonical gender for this speaker
        speaker_info = speaker_map.get(seg["speaker_no"], {})
        canon_gender = speaker_info.get("gender", "male")

        chunks = chunk_separation(
            seg["segment_path"],
            seg["start_time"],
            seg["end_time"],
            seg["speaker_no"],
            seg["overlap"],
            segment_id=idx
        )
        
        # Inject canonical gender into every chunk
        for c in chunks:
            c["gender"] = canon_gender
            
        all_chunks.extend(chunks)

    diarization_data["chunks"] = all_chunks
    if video_path:
        diarization_data["video_path"] = video_path
    return diarization_data


# ---------- MASTER PIPELINE ----------
def get_stage1_chain(video_path):
    workflow = chain(
        task_audio_separator.s(video_path),
        task_diarization.s(),
        task_overlap_split.s(),
        task_segment.s(),
        task_speaker_analysis.s(),  # Canonical gender analysis
        task_chunk.s(video_path)
    )
    return workflow
