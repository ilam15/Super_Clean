"""
Optimized STT + Diarization Pipeline
Preserves full functionality of original implementation
"""

import time
from types import SimpleNamespace
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from src.app import model_manager
from src.core.context import RequestContext
from src.core.exceptions import ASRError
from src.core.logger import logger
from src.core.config import settings


class ASRTranscriber:
    def __init__(self, context: RequestContext):
        self.context = context

    # =========================================================
    # MAIN ENTRY
    # =========================================================
    def process_file(self, audio_data, source_lang: str):

        from src.utils.utils import language_dict

        start_time = time.time()

        # ---------- Language normalization ----------
        whisper_lang = None
        if source_lang != "Automatic":
            whisper_lang = (
                language_dict[source_lang]["lang_code"]
                if source_lang in language_dict
                else source_lang[:3]
            )

        sr = 16000
        duration = len(audio_data) / sr

        chunk_duration = (
            settings.PROBE_WINDOW_SHORT
            if duration < 60
            else settings.PROBE_WINDOW_LONG
        )
        chunk_samples = int(chunk_duration * sr)

        logger.info(
            f"🌍 ASR Engine running | duration={duration:.2f}s | chunk={chunk_duration}s"
        )

        # =========================================================
        # WHISPER TRANSCRIPTION
        # =========================================================
        def run_whisper():
            model = model_manager.get_whisper()

            segments = []
            detected_langs = []

            for start in range(0, len(audio_data), chunk_samples):
                model_manager.heartbeat("whisper")

                chunk = audio_data[start:start + chunk_samples]
                if len(chunk) < 8000:
                    continue

                offset = start / sr
                beam = 5 if settings.DEVICE == "cuda" else 2

                seg_iter, info = model.transcribe(
                    chunk,
                    vad_filter=True,
                    language=whisper_lang,
                    task="transcribe",
                    beam_size=beam,
                    word_timestamps=True
                )

                detected_langs.append(info.language)

                # ---------- segment processing ----------
                for seg in seg_iter:
                    seg_start = seg.start + offset
                    seg_end = seg.end + offset

                    # ---- Probe language for longer segments ----
                    if (seg.end - seg.start) * sr >= 8000:
                        audio_seg = chunk[int(seg.start * sr):int(seg.end * sr)]
                        _, probe = model.transcribe(audio_seg, language=None, beam_size=1)
                        lang = probe.language
                        prob = probe.language_probability
                    else:
                        lang = info.language
                        prob = info.language_probability

                    logger.info(f"[{seg_start:.2f}s] {seg.text[:60]}")

                    segments.append(SimpleNamespace(
                        start=seg_start,
                        end=seg_end,
                        text=seg.text,
                        words=seg.words,
                        segment_language=lang,
                        segment_language_prob=prob,
                        whisper_hint=info.language,
                        whisper_hint_prob=info.language_probability
                    ))

            # ---------- global language ----------
            if detected_langs:
                common = Counter(detected_langs).most_common(1)[0][0]
                global_info = SimpleNamespace(language=common)
            else:
                global_info = SimpleNamespace(language="en")

            return segments, global_info

        # =========================================================
        # DIARIZATION
        # =========================================================
        def run_diarization():
            try:
                analyzer = model_manager.get_diarization()
                return analyzer.analyze_audio(audio_data)
            except Exception as e:
                logger.warning(f"Diarization failed → fallback single speaker | {e}")
                return [], {}

        # =========================================================
        # EXECUTION MODE
        # =========================================================
        try:
            if settings.DEVICE == "cpu":
                logger.info("🧵 CPU Mode → Sequential Execution")
                segments, info = run_whisper()
                speaker_turns, speaker_genders = run_diarization()

            else:
                logger.info("⚡ GPU Mode → Parallel Execution")
                with ThreadPoolExecutor(max_workers=2) as ex:
                    w = ex.submit(run_whisper)
                    d = ex.submit(run_diarization)
                    segments, info = w.result()
                    speaker_turns, speaker_genders = d.result()

        except Exception as e:
            raise ASRError(f"Speech pipeline failed: {e}")

        # ---------- metrics ----------
        self.context.add_metric("asr_diarization", time.time() - start_time)

        return segments, info, speaker_turns, speaker_genders
