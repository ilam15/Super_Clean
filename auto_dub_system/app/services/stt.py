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
    Production-ready STT using Sarvam saaras:v3 with audio normalization and robust error handling.
    """
    import os
    import requests
    import logging
    import wave
    import audioop
    import time
    from app.config import settings

    logger = logging.getLogger(__name__)
    duration = end_time - start_time

    # 1. Enforce Minimum Duration (Step 2)
    if duration < 0.5:
        logger.warning(f"Chunk too short ({duration:.2f}s) for reliable STT. Skipping.")
        return {
            "text": "", "start_time": start_time, "end_time": end_time,
            "speaker_no": speaker_no, "overlap": overlap, "gender": gender
        }

    # 2. Silence Filter (Step 8)
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
                            "text": "", "start_time": start_time, "end_time": end_time,
                            "speaker_no": speaker_no, "overlap": overlap, "gender": gender
                        }
    except Exception as silence_err:
        logger.warning(f"Silence check failed: {silence_err}")

    try:
        # 3. Normalize Audio (Step 1)
        norm_path = chunk_path.replace(".wav", "_norm.wav")
        normalize_audio(chunk_path, norm_path)
        
        # 4. API Config
        url = "https://api.sarvam.ai/speech-to-text"
        headers = {"api-subscription-key": settings.SARVAM_API_KEY}
        
        with open(norm_path, "rb") as f:
            audio_bytes = f.read()
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}

        # 5. Correct API Payload (STT Only)
        data = {
            "model": "saaras:v3",
            "translate": False, # Get original text first for better LID
            "punctuate": True
        }
        if source_lang != "auto":
            data["source_language"] = source_lang
        else:
            data["auto_detect"] = True

        # 6. API Call with Timeout and Retries
        max_retries = 3
        retry_delay = 5
        response = None
        
        for attempt in range(max_retries):
            try:
                # Re-open the file handle if it was closed or needs to be reset
                with open(norm_path, "rb") as f:
                    audio_bytes = f.read()
                files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
                
                response = requests.post(url, headers=headers, files=files, data=data, timeout=180)
                if response.status_code == 200:
                    break
                else:
                    logger.warning(f"Sarvam STT Attempt {attempt+1} failed with code {response.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
            except Exception as conn_err:
                logger.warning(f"Sarvam STT Attempt {attempt+1} connection error: {conn_err}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    raise conn_err
        
        if not response or response.status_code != 200:
            error_msg = f"Sarvam STT Error after {max_retries} attempts: {response.status_code if response else 'No Response'}"
            logger.error(error_msg)
            raise Exception(error_msg)

        result = response.json()

        # 7. Validate Detection Result (Steps 6, 9)
        final_text = result.get("transcript", "")
        
        # FIX #1: Language Identification
        from app.services.language_detect import LanguageIdentifier
        det_lang, conf, reason = LanguageIdentifier.identify(final_text)
        
        # FIX #5: Debug Logging
        logger.info(f"""
        Detected: {det_lang}
        Target: {target_lang}
        Text: {final_text}
        """)

        # FIX #4: Skip Translation If Same Language
        if det_lang == target_lang:
            logger.info(f"Source ({det_lang}) matches target ({target_lang}). Skipping translation.")
            translated_text = final_text
        else:
            # FIX #2: Use detected language for translation
            logger.info(f"Translating {det_lang} -> {target_lang}")
            translated_text = sarvam_translate(final_text, det_lang, target_lang)

        # Cleanup normalized file
        if os.path.exists(norm_path):
            os.remove(norm_path)

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
        logger.error(f"Sarvam STT process failed: {e}")
        raise
