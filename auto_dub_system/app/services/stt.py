def normalize_audio(input_path, output_path):
    """Normalize audio to mono, 16kHz, PCM 16-bit as required by Sarvam AI."""
    import subprocess
    import shutil
    ffmpeg_cmd = shutil.which("ffmpeg") or "ffmpeg"
    subprocess.run([
        ffmpeg_cmd, "-y", "-i", input_path,
        "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
        output_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def sarvam_translate(text: str, source_lang: str, target_lang: str) -> str:
    """Helper to call Sarvam's translation API."""
    import requests
    import logging
    from app.config import settings
    
    logger = logging.getLogger(__name__)
    url = "https://api.sarvam.ai/translate"  # Fixed URL
    headers = {
        "api-subscription-key": settings.SARVAM_API_KEY,
        "Content-Type": "application/json"
    }

    # Map simple codes to Sarvam expectation (usually ISO + -IN for Indian langs)
    indian_langs = ["en", "hi", "ta", "te", "kn", "ml", "pa", "gu", "mr", "bn", "or"]
    s_lang = f"{source_lang}-IN" if source_lang in indian_langs else source_lang
    t_lang = f"{target_lang}-IN" if target_lang in indian_langs else target_lang
    
    # Fix: Use EXACT keys required by Sarvam API (source_language_code / target_language_code)
    data = {
        "input": text,
        "model": "mayura:v1",
        "source_language_code": s_lang,
        "target_language_code": t_lang
    }
    
    import time
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                res = response.json()
                translated = res.get("translated_text", text)
                logger.info(f"Translation successful (Attempt {attempt+1}): {source_lang} -> {target_lang}")
                return translated
            else:
                logger.error(f"Sarvam translation failed ({response.status_code}) Attempt {attempt+1}: {response.text}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                continue
        except Exception as e:
            logger.error(f"Sarvam translation error (Attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
            else:
                return text
    return text


def faster_whisper_stt(audio_path, model_size="medium", device="auto", compute_type="int8"):
    """
    Fallback STT using local faster-whisper model.
    """
    import logging
    from faster_whisper import WhisperModel
    import torch

    logger = logging.getLogger(__name__)

    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"

    try:
        logger.info(f"Loading faster-whisper model ({model_size}) on {device}...")
        # Run on CPU with int8 if no CUDA, or float16 on CUDA if supported
        if device == "cpu":
            compute_type = "int8"
        
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        segments, info = model.transcribe(audio_path, beam_size=5)
        
        text = " ".join([segment.text for segment in segments])
        logger.info(f"Faster-Whisper transcribed: {text[:50]}... (Language: {info.language})")
        return text.strip(), info.language
    except Exception as e:
        logger.error(f"Faster-Whisper failed: {e}")
        raise

def speech_to_text(
    chunk_path: str,
    start_time: float,
    end_time: float,
    speaker_no: str,
    overlap: bool,
    gender: str,
    target_lang: str = "en",
    source_lang: str = "auto"
):
    """
    Production-ready STT using Sarvam saaras:v3 with fallback to faster-whisper.
    Includes robust error handling, retries, and timeouts.
    """
    import os
    import requests
    import logging
    import wave
    import audioop
    import time
    from app.config import settings
    from app.services.language_detect import LanguageIdentifier

    logger = logging.getLogger(__name__)
    duration = end_time - start_time
    
    start_process_time = time.time()
    logger.info(f"STT Processing started for chunk (Duration: {duration:.2f}s)")

    # 1. Enforce Minimum Duration
    if duration < 0.5:
        logger.warning(f"Chunk too short ({duration:.2f}s) for reliable STT. Skipping.")
        return {
            "text": "", "detected_lang": "", "confidence": 0.0,
            "start_time": start_time, "end_time": end_time,
            "speaker_no": speaker_no, "overlap": overlap, "gender": gender
        }

    # 2. Silence Filter
    try:
        if os.path.exists(chunk_path):
            with wave.open(chunk_path, 'rb') as wf:
                params = wf.getparams()
                frames = wf.readframes(wf.getnframes())
                if frames:
                    rms = audioop.rms(frames, params.sampwidth)
                    if rms < 200:
                        logger.info(f"Silence detected (RMS: {rms}). Skipping STT.")
                        return {
                            "text": "", "detected_lang": "", "confidence": 0.0,
                            "start_time": start_time, "end_time": end_time,
                            "speaker_no": speaker_no, "overlap": overlap, "gender": gender
                        }
    except Exception as silence_err:
        logger.warning(f"Silence check failed: {silence_err}")

    # 3. Normalize Audio
    norm_path = chunk_path.replace(".wav", "_norm.wav")
    try:
        normalize_audio(chunk_path, norm_path)
        
        final_text = ""
        det_lang = "en"  # Default
        
        # --- SARVAM STT BLOCK ---
        sarvam_success = False
        
        url = "https://api.sarvam.ai/speech-to-text"
        headers = {
            "api-subscription-key": settings.SARVAM_API_KEY,
            "Connection": "close"  # Prevent dead connections
        }
        
        # Prepare Data
        data = {
            "model": "saaras:v3",
            "translate": False, # Get original text
            "punctuate": True
        }
        if source_lang != "auto":
            data["source_language"] = source_lang
        else:
            data["auto_detect"] = True

        MAX_RETRIES = 3
        
        for attempt in range(MAX_RETRIES):
            try:
                # Re-open file for each attempt to reset pointer
                with open(norm_path, "rb") as f:
                    files = {"file": ("audio.wav", f, "audio/wav")}
                    
                    st_time = time.time()
                    response = requests.post(
                        url, 
                        headers=headers, 
                        files=files, 
                        data=data, 
                        timeout=(5, 30) # (connect, read)
                    )
                    
                    elapsed = time.time() - st_time
                    logger.info(f"Sarvam API response time (Attempt {attempt+1}): {elapsed:.2f}s")
                    
                    response.raise_for_status() # Check for 4xx/5xx
                    
                    result = response.json()
                    final_text = result.get("transcript", "")
                    sarvam_success = True
                    break # Success!
                    
            except Exception as e:
                logger.warning(f"Sarvam STT Attempt {attempt+1}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt) # Exponential backoff: 1s, 2s, 4s...
        
        # --- FALLBACK BLOCK ---
        if not sarvam_success:
            logger.warning("Sarvam failed or timed out. Falling back to faster-whisper.")
            try:
                final_text, detected_code = faster_whisper_stt(norm_path)
                # Ensure detected_code is used if we can capture it, though LanguageIdentifier below does a better job usually
            except Exception as fw_err:
                logger.error(f"Faster-Whisper fallback also failed: {fw_err}")
                final_text = ""

        # 4. Result Processing
        if not final_text:
            logger.warning("No transcript generated.")
            return {
                "text": "", "detected_lang": "", "confidence": 0.0,
                "start_time": start_time, "end_time": end_time,
                "speaker_no": speaker_no, "overlap": overlap, "gender": gender
            }

        # Language Detection
        det_lang, conf, reason = LanguageIdentifier.identify(final_text)
        
        logger.info(f"""
        STT Result:
        - Text: {final_text[:100]}...
        - Detected Lang: {det_lang} (Conf: {conf})
        - Target Lag: {target_lang}
        """)

        # Translation Logic
        translated_text = final_text
        if det_lang != target_lang:
             logger.info(f"Translating {det_lang} -> {target_lang}")
             # Use the simple translation helper
             translated_text = sarvam_translate(final_text, det_lang, target_lang)
        else:
             logger.info("Source matches target. Skipping translation.")

        total_elapsed = time.time() - start_process_time
        logger.info(f"Total STT Task Duration: {total_elapsed:.2f}s")

        return {
            "text": translated_text,
            "detected_lang": det_lang,
            "confidence": conf,
            "start_time": start_time,
            "end_time": end_time,
            "speaker_no": speaker_no,
            "overlap": overlap,
            "gender": gender
        }

    except Exception as e:
        logger.error(f"STT process failed completely: {e}")
        # Return empty safe result instead of crashing the pipeline
        return {
            "text": "", "detected_lang": "error", "confidence": 0.0,
            "start_time": start_time, "end_time": end_time,
            "speaker_no": speaker_no, "overlap": overlap, "gender": gender
        }
    finally:
        # Cleanup
        if os.path.exists(norm_path):
            try:
                os.remove(norm_path)
            except:
                pass
