"""
Sarvam / Whisper STT.
"""
# import whisper

import time
from src.app import model_manager
from src.core.context import RequestContext
from src.core.exceptions import ASRError, DiarizationError
from src.core.logger import logger
from concurrent.futures import ThreadPoolExecutor
from src.core.config import settings

class ASRTranscriber:
    def __init__(self, context: RequestContext):
        self.context = context

    def process_file(self, audio_data, source_lang: str):
        from src.utils.utils import language_dict
        import numpy as np
        from types import SimpleNamespace
        st = time.time()
        
        # Normalize language to ISO code
        whisper_lang = None
        if source_lang != "Automatic":
            if source_lang in language_dict:
                whisper_lang = language_dict[source_lang]["lang_code"]
            else:
                whisper_lang = source_lang if len(source_lang) <= 3 else None

        # 1. ASR Pass Definition
        def run_whisper():
            model = model_manager.get_whisper()
            
            duration_sec = len(audio_data) / 16000
            if duration_sec < 60:
                 chunk_duration = settings.PROBE_WINDOW_SHORT
            else:
                 chunk_duration = settings.PROBE_WINDOW_LONG

            chunk_samples = chunk_duration * 16000
            total_samples = len(audio_data)
            
            segments_list = []
            global_info_list = []
            
            logger.info(f"🌍 ASR Engine: Ultra-Granular Multilingual Transcription ({chunk_duration}s windows)")
            
            for start_sample in range(0, total_samples, chunk_samples):
                model_manager.heartbeat("whisper")
                
                end_sample = min(start_sample + chunk_samples, total_samples)
                chunk = audio_data[start_sample:end_sample]
                
                if len(chunk) < 8000:
                    continue
                    
                offset = start_sample / 16000
                active_beam_size = 5 if settings.DEVICE == "cuda" else 2
                
                chunk_segments_iter, chunk_info = model.transcribe(
                    chunk,
                    vad_filter=True,
                    language=None if source_lang == "Automatic" else whisper_lang,
                    task="transcribe",
                    beam_size=active_beam_size,
                    word_timestamps=True
                )
                
                global_info_list.append(chunk_info)
                
                for seg in chunk_segments_iter:
                    seg_start = seg.start + offset
                    seg_end = seg.end + offset
                    
                    logger.info(f" -> [{seg_start:.2f}s] Transcribed: {seg.text[:50]}...")
                    
                    # PROBE logic
                    if settings.DEVICE == "cpu":
                        actual_lang = chunk_info.language
                        actual_prob = chunk_info.language_probability
                    elif (seg.end - seg.start) * 16000 < 8000:
                        actual_lang = chunk_info.language
                        actual_prob = chunk_info.language_probability
                    else:
                        audio_start = int(seg.start * 16000)
                        audio_end = int(seg.end * 16000)
                        segment_audio = chunk[audio_start:audio_end]
                        _, probe_info = model.transcribe(
                            segment_audio,
                            language=None,
                            beam_size=1
                        )
                        actual_lang = probe_info.language
                        actual_prob = probe_info.language_probability
                    
                    wrapper = SimpleNamespace(
                        start=seg_start,
                        end=seg_end,
                        text=seg.text,
                        words=seg.words,
                        segment_language=actual_lang,
                        segment_language_prob=actual_prob,
                        whisper_hint=chunk_info.language,
                        whisper_hint_prob=chunk_info.language_probability
                    )
                    segments_list.append(wrapper)

            if global_info_list:
                from collections import Counter
                most_common_lang = Counter([i.language for i in global_info_list]).most_common(1)[0][0]
                global_info = next(i for i in global_info_list if i.language == most_common_lang)
            else:
                global_info = SimpleNamespace(language="en", language_probability=0.0)
            
            return segments_list, global_info

        # 2. Diarization Pass Definition
        def run_diarization():
            try:
                analyzer = model_manager.get_diarization()
                return analyzer.analyze_audio(audio_data)
            except Exception as e:
                logger.warning(f"Diarization failed: {e}. Falling back to single speaker.")
                return [], {}

        # Execution Logic
        if settings.DEVICE == "cpu":
            logger.info("🧵 Running ASR and Diarization sequentially (CPU optimization)")
            try:
                segments, info = run_whisper()
                speaker_turns, speaker_genders = run_diarization()
            except Exception as e:
                raise ASRError(f"Speech transcription pipeline failed: {e}")
        else:
            logger.info("⚡ Running ASR and Diarization in parallel (GPU mode)")
            with ThreadPoolExecutor(max_workers=2) as executor:
                whisper_future = executor.submit(run_whisper)
                diar_future = executor.submit(run_diarization)
                try:
                    segments, info = whisper_future.result()
                    speaker_turns, speaker_genders = diar_future.result()
                except Exception as e:
                    raise ASRError(f"Speech transcription pipeline failed: {e}")

        self.context.add_metric("asr_diarization", time.time() - st)
        return segments, info, speaker_turns, speaker_genders