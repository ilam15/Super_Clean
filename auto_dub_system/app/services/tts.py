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
        Sarvam AI TTS

    OUTPUT:
        audio_path + start_time + end_time + speaker_no + overlap
    """

    try:
        import os
        import uuid
        import requests
        from app.config import settings

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
        # VOICE SELECTION
        # -------------------------
        # Dynamic selection based on gender logic
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"TTS Voice Selection: gender={gender}, speaker={speaker_no}")
        
        if gender.lower() == "female":
            voice = "anushka" # Sarvam female voice
        elif gender.lower() == "male":
            voice = "arjun"   # Sarvam male voice
        else:
            voice = "arjun"   # Default to male if unknown
            
        logger.info(f"Using voice: {voice}")

        # -------------------------
        # FILE PATH
        # -------------------------
        file_name = f"{speaker_no}_{uuid.uuid4().hex}.wav"
        audio_path = os.path.join(output_dir, file_name)

        # -------------------------
        # SARVAM CONFIG
        # -------------------------
        url = "https://api.sarvam.ai/text-to-speech"
        headers = {
            "api-subscription-key": settings.SARVAM_API_KEY,
            "Content-Type": "application/json"
        }

        payload = {
            "inputs": [aligned_text],
            "voice": voice,
            "sample_rate": 22050,
            "format": "wav"
        }

        # -------------------------
        # API CALL WITH RETRIES
        # -------------------------
        import time
        max_retries = 3
        retry_delay = 3
        response = None
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    break
                else:
                    logger.warning(f"Sarvam TTS Attempt {attempt+1} failed with code {response.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
            except Exception as conn_err:
                logger.warning(f"Sarvam TTS Attempt {attempt+1} connection error: {conn_err}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    raise conn_err

        if not response or response.status_code != 200:
            raise Exception(f"Sarvam TTS Error after {max_retries} attempts: {response.text if response else 'No Response'}")

        # -------------------------
        # SAVE AUDIO
        # -------------------------
        import base64
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
                raise ValueError("Invalid sample rate")

            tts_dur = info.frames / info.samplerate

            speed = tts_dur / orig_dur
            speed = max(0.1, min(speed, 10))

            filters = []
            temp_speed = speed

            while temp_speed > 2.0:
                filters.append("atempo=2.0")
                temp_speed /= 2.0

            while temp_speed < 0.5:
                filters.append("atempo=0.5")
                temp_speed /= 0.5

            if abs(temp_speed - 1.0) > 1e-3:
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

                subprocess.run(cmd, check=True)
                audio_path = out_path

        except Exception as e:
            logger.warning(f"Speed adjustment failed: {e}")

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
        print(f"Sarvam TTS Error: {e}")
        return {
            "audio_path": None,
            "start_time": start_time,
            "end_time": end_time,
            "speaker_no": speaker_no,
            "overlap": overlap
        }
