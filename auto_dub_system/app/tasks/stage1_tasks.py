from celery import chain
from app.tasks.celery_app import celery_app

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
    return speaker_diarization(audio_path)


# ---------- TASK 3 (Conditional) ----------
@celery_app.task
def task_overlap_split(diarization_data):
    if diarization_data["overlap"]:
        diarization_data["separated_audio"] = overlapping_audio_split(
            diarization_data["audio_path"],
            diarization_data["timestamps"],
            diarization_data["speaker_count"]
        )
    return diarization_data


# ---------- TASK 4 ----------
@celery_app.task
def task_segment(diarization_data):
    # Call class method
    segments = SegmentSeparator.segment_separation(
        diarization_data["audio_path"],
        diarization_data["timestamps"],
        diarization_data["speaker_labels"],
        diarization_data["overlap"]
    )
    diarization_data["segments"] = segments
    return diarization_data


# ---------- TASK 5 ----------
@celery_app.task
def task_chunk(diarization_data, video_path=None):
    all_chunks = []

    for seg in diarization_data["segments"]:
        chunks = chunk_separation(
            seg["segment_path"],
            seg["start_time"],
            seg["end_time"],
            seg["speaker_no"],
            seg["overlap"]
        )
        all_chunks.extend(chunks)

    diarization_data["chunks"] = all_chunks
    if video_path:
        diarization_data["video_path"] = video_path
    return diarization_data


# ---------- MASTER PIPELINE ----------
# ---------- MASTER PIPELINE ----------
def get_stage1_chain(video_path):
    workflow = chain(
        task_audio_separator.s(video_path),
        task_diarization.s(),
        task_overlap_split.s(),
        task_segment.s(),
        task_chunk.s(video_path)  # Pass video_path to task_chunk
    )
    return workflow
