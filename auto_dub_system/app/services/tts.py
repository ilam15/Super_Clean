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
                "start_time": round(start_time, 2),
                "end_time": round(end_time, 2),
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
        logger.info(f"TTS Config: gender={gender}, lang={target_lang_code}")
        
        # bulbul:v3 Speakers
        # Male: Shubh (default), Aditya, Rahul, Amit, Dev, Varun, Sumit, Kabir, Aayan, Ashutosh, Advait, Anand, Tarun, Sunny, Mani, Gokul, Vijay, Mohit, Rehan, Soham
        # Female: Ritu, Priya, Neha, Pooja, Simran, Kavya, Ishita, Shreya, Roopa, Amelia, Sophia, Tanya, Shruti, Suhani, Kavitha, Rupali
        
        if gender.lower() == "female":
            speaker = "priya" 
        elif gender.lower() == "male":
            speaker = "shubh"
        else:
            speaker = "shubh"   # Default
            
        logger.info(f"Using speaker: {speaker}")

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
        try:
            from pathlib import Path
            import soundfile as sf
            import subprocess
            import shutil

            ffmpeg_cmd = shutil.which("ffmpeg")
            if not ffmpeg_cmd:
                raise RuntimeError("FFmpeg not found in PATH")

            orig_dur = max(end_time - start_time, 0.1)

            info = sf.info(audio_path)
            if info.samplerate == 0:
                # Fallback if Sf fails to read headers, though unlikely for valid wav
                tts_dur = orig_dur 
            else:
                 tts_dur = info.frames / info.samplerate

            speed = tts_dur / orig_dur
            # Constrain speed to avoid extreme artifacts
            speed = max(0.5, min(speed, 2.0)) 

            filters = []
            temp_speed = speed
            
            # atempo filter supports 0.5 to 2.0
            # Since we constrained speed to 0.5-2.0, one pass is enough usually.
            # But logic below handles chaining if we widen range later.
            while temp_speed > 2.0:
                filters.append("atempo=2.0")
                temp_speed /= 2.0
            while temp_speed < 0.5:
                filters.append("atempo=0.5")
                temp_speed /= 0.5
            
            if abs(temp_speed - 1.0) > 0.01:
                filters.append(f"atempo={temp_speed:.3f}")

            if filters:
                p = Path(audio_path)
                out_path = str(p.with_name(p.stem + "_synced.wav"))
                filter_str = ",".join(filters)

                cmd = [
                    ffmpeg_cmd, "-y", "-i", audio_path,
                    "-filter:a", filter_str,
                    out_path
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                audio_path = out_path
                
        except Exception as speed_err:
            logger.warning(f"Speed adjustment failed, using original TTS: {speed_err}")

        # -------------------------
        # OUTPUT STRUCTURE
        # -------------------------
        return {
            "audio_path": audio_path,
            "start_time": round(start_time, 2),
            "end_time": round(end_time, 2),
            "speaker_no": speaker_no,
            "overlap": overlap,
            "gender": gender
        }

    except Exception as e:
        logger.error(f"Sarvam TTS Critical Error: {e}")
        return {
            "audio_path": None,
            "start_time": start_time,
            "end_time": end_time,
            "speaker_no": speaker_no,
            "overlap": overlap
        }
