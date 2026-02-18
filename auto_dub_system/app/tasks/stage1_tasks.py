from celery import chain
from app.tasks.celery_app import celery_app
from app.config import settings
import logging
import warnings # Added import for warnings

# Suppress noisy warnings from specialized libraries
warnings.filterwarnings("ignore", category=UserWarning, module="pyannote.audio.core.io")
warnings.filterwarnings("ignore", category=UserWarning, module="pyannote.audio.models.blocks.pooling")
warnings.filterwarnings("ignore", category=UserWarning, module="torchaudio")
warnings.filterwarnings("ignore", message=".*speechbrain.pretrained.*")
warnings.filterwarnings("ignore", message=".*torchcodec.*")
warnings.filterwarnings("ignore", message=".*degrees of freedom.*")

logger = logging.getLogger(__name__)

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
    if diarization_data.get("overlap"):
        # Service expects: (timestamps, speaker_count, audio_path, overlap, ...)
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
    # If we have separated audio from overlap split, use that. Otherwise use original.
    audio_to_segment = diarization_data["audio_path"]
    if diarization_data.get("separated_audio") and len(diarization_data["separated_audio"]) > 0:
        # For simplicity, we use the first separated track (vocals) for segmentation
        audio_to_segment = diarization_data["separated_audio"][0]

    overlap_flags = [s["overlap"] for s in diarization_data["segments"]]
    
    segments = SegmentSeparator.segment_separation(
        audio_to_segment,
        diarization_data["timestamps"],
        diarization_data["speaker_labels"],
        overlap_flags
    )
    diarization_data["segments"] = segments
    return diarization_data


# ---------- TASK 5 ----------
@celery_app.task
def task_chunk(diarization_data, video_path=None):
    all_chunks = []

    for idx, seg in enumerate(diarization_data["segments"]):
        chunks = chunk_separation(
            seg["segment_path"],
            seg["start_time"],
            seg["end_time"],
            seg["speaker_no"],
            seg["overlap"],
            segment_id=idx
        )
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
        task_chunk.s(video_path)
    )
    return workflow
