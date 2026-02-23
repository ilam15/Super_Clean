def adjust_tts_speed_for_lipsync(
    audio_path: str,
    start_time: float,
    end_time: float,
    logger=None,
    silence_db: int = 30,
    natural_min: float = 0.5,
    natural_max: float = 2.0,
    tolerance: float = 0.03
) -> str:
    """
    Adjust TTS audio speed to match original segment duration
    using perceptually safe time-stretching.

    Parameters:
        audio_path: Path to generated TTS WAV file
        start_time: Segment start timestamp (seconds)
        end_time: Segment end timestamp (seconds)
        logger: Optional logger
        silence_db: Silence trim threshold (dB)
        natural_min: Minimum natural speed factor
        natural_max: Maximum natural speed factor
        tolerance: Speed difference threshold before re-encoding

    Returns:
        Path to speed-adjusted audio file (or original if no change)
    """
    try:
        import librosa
        import subprocess
        import shutil
        import os
        from pathlib import Path

        # -----------------------------
        # Validate segment duration
        # -----------------------------
        orig_dur = end_time - start_time
        if orig_dur <= 0:
            raise ValueError(f"Invalid segment duration: {orig_dur}")

        # -----------------------------
        # Ensure FFmpeg exists
        # -----------------------------
        ffmpeg_cmd = shutil.which("ffmpeg")
        if not ffmpeg_cmd:
            raise RuntimeError("FFmpeg not found in PATH")

        # -----------------------------
        # Load & Trim Silence (Accurate Speech Duration)
        # -----------------------------
        y, sr = librosa.load(audio_path, sr=None)
        yt, _ = librosa.effects.trim(y, top_db=silence_db)

        if len(yt) == 0:
            if logger:
                logger.warning("Audio contains only silence. Skipping speed adjustment.")
            return audio_path

        tts_dur = len(yt) / sr
        
        # Save trimmed pure speech to a temporary file
        import soundfile as sf
        p = Path(audio_path)
        trimmed_path = str(p.with_name(p.stem + "_trimmed.wav"))
        sf.write(trimmed_path, yt, sr)

        # -----------------------------
        # Compute Required Speed Factor
        # -----------------------------
        speed = tts_dur / orig_dur

        # -----------------------------
        # Natural Speech Constraint
        # -----------------------------
        if speed < natural_min or speed > natural_max:
            if logger:
                logger.warning(
                    f"Speed {speed:.3f} outside natural range "
                    f"({natural_min}-{natural_max}). Clamping."
                )
            speed = max(natural_min, min(speed, natural_max))

        # -----------------------------
        # Skip if Within Perceptual Tolerance
        # -----------------------------
        out_path = str(p.with_name(p.stem + "_synced.wav"))
        
        if abs(speed - 1.0) <= tolerance:
            if logger:
                logger.info("Speed within tolerance. No adjustment needed.")
            shutil.move(trimmed_path, out_path)
            return out_path

        # -----------------------------
        # Apply FFmpeg atempo Filter
        # -----------------------------
        filter_str = f"atempo={speed:.6f}"

        cmd = [
            ffmpeg_cmd,
            "-y",
            "-i", trimmed_path,
            "-filter:a", filter_str,
            out_path
        ]

        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Clean up temporary trimmed file
        try:
            os.remove(trimmed_path)
            os.remove(audio_path) # Optional: remove untrimmed to save space
        except OSError:
            pass

        if logger:
            logger.info(f"Speed adjusted: {speed:.4f} -> {out_path}")

        return out_path

    except Exception as e:
        if logger:
            logger.warning(f"Speed adjustment failed. Using original audio. Error: {e}")
        return audio_path


def text_to_speech(
    aligned_text: str,
    start_time: float,
    end_time: float,
    speaker_no: str,
    overlap: bool,
    gender: str,
    output_dir: str = "tts_chunks"
):
    """
    INPUT:
        aligned_text + start_time + end_time + speaker_no + overlap + gender

    PROCESS:
        Sarvam AI TTS (bulbul:v3)

    OUTPUT:
        audio_path + start_time + end_time + speaker_no + overlap
    """

    try:
        import os
        import uuid
        import requests
        import base64
        import time
        import logging
        from app.config import settings
        from app.services.language_detect import LanguageIdentifier

        logger = logging.getLogger(__name__)
        os.makedirs(output_dir, exist_ok=True)
        
        # -------------------------
        # SKIP IF EMPTY OR SYMBOLS ONLY
        # -------------------------
        clean_text = "".join(c for c in aligned_text if c.isalnum())
        if not clean_text:
            return {
                "audio_path": None,
                "start_time": start_time,
                "end_time": end_time,
                "speaker_no": speaker_no,
                "overlap": overlap
            }

        # -------------------------
        # LANGUAGE DETECTION & CONFIG
        # -------------------------
        # Sarvam requires 'target_language_code' (e.g., 'hi-IN', 'en-IN')
        try:
            det_lang, conf, _ = LanguageIdentifier.identify(aligned_text)
            # Map common codes to Sarvam's expected format
            # Sarvam supports: hi-IN, bn-IN, kn-IN, ml-IN, mr-IN, od-IN, pa-IN, ta-IN, te-IN, en-IN, gu-IN
            supported_langs = {
                'en': 'en-IN', 'hi': 'hi-IN', 'bn': 'bn-IN', 'kn': 'kn-IN', 
                'ml': 'ml-IN', 'mr': 'mr-IN', 'or': 'od-IN', 'pa': 'pa-IN', 
                'ta': 'ta-IN', 'te': 'te-IN', 'gu': 'gu-IN'
            }
            # Default to en-IN if unknown or unsupported, or map generic code to -IN
            target_lang_code = supported_langs.get(det_lang, 'en-IN')
        except Exception as e:
            logger.warning(f"Language detection failed: {e}. Defaulting to en-IN.")
            target_lang_code = "en-IN"

        # -------------------------
        # VOICE/SPEAKER SELECTION (bulbul:v3)
        # -------------------------
        from app.config import get_assigned_voice
        
        logger.info(f"TTS Config: gender={gender}, lang={target_lang_code}")
        
        # Call the deterministic dynamic assignment utility
        speaker = get_assigned_voice(speaker_no, gender)
            
        logger.info(f"🎤 Assigned voice '{speaker}' to {speaker_no} ({gender})")

        # -------------------------
        # FILE PATH
        # -------------------------
        file_name = f"{speaker_no}_{uuid.uuid4().hex}.wav"
        audio_path = os.path.join(output_dir, file_name)

        # -------------------------
        # SARVAM API REQUEST
        # -------------------------
        url = "https://api.sarvam.ai/text-to-speech"
        headers = {
            "api-subscription-key": settings.SARVAM_API_KEY,
            "Content-Type": "application/json"
        }

        # bulbul:v3 Payload
        payload = {
            "text": aligned_text,
            "target_language_code": target_lang_code,
            "speaker": speaker,
            "model": "bulbul:v3",
            "speech_sample_rate": 24000,
            "enable_preprocessing": True
        }

        # -------------------------
        # EXECUTE WITH RETRIES
        # -------------------------
        max_retries = 3
        retry_delay = 2
        response = None
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=(5, 60))
                if response.status_code == 200:
                    break
                elif response.status_code == 429: # Rate limit
                    logger.warning("Sarvam TTS Rate Limit. Sleeping...")
                    time.sleep(5)
                else:
                    logger.warning(f"Sarvam TTS Attempt {attempt+1} failed: {response.status_code} - {response.text}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
            except Exception as conn_err:
                logger.warning(f"Sarvam TTS Attempt {attempt+1} connection error: {conn_err}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    raise conn_err

        if not response or response.status_code != 200:
            raise Exception(f"Sarvam TTS Error: {response.status_code if response else 'No Response'}")

        # -------------------------
        # SAVE AUDIO
        # -------------------------
        result = response.json()
        if "audios" in result and len(result["audios"]) > 0:
            audio_base64 = result["audios"][0]
            audio_bytes = base64.b64decode(audio_base64)
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)
        else:
            raise Exception(f"No audio data in Sarvam response: {result}")

        # -------------------------
        # SPEED ADJUSTMENT (LIPSYNC)
        # -------------------------
        audio_path = adjust_tts_speed_for_lipsync(
            audio_path=audio_path,
            start_time=start_time,
            end_time=end_time,
            logger=logger
        )

        # -------------------------
        # OUTPUT STRUCTURE
        # -------------------------
        return {
            "audio_path": audio_path,
            "start_time": start_time,
            "end_time": end_time,
            "speaker_no": speaker_no,
            "overlap": overlap,
            "gender": gender
        }

    except Exception as e:
        # Avoid logger error if hasn't been instantiated
        try:
            logger.error(f"Sarvam TTS Critical Error: {e}")
        except:
            print(f"Sarvam TTS Critical Error: {e}")
        return {
            "audio_path": None,
            "start_time": start_time,
            "end_time": end_time,
            "speaker_no": speaker_no,
            "overlap": overlap
        }
