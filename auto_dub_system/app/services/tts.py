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
        # API CALL
        # -------------------------
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"Sarvam API Error {response.status_code}: {response.text}")

        # -------------------------
        # SAVE AUDIO
        # -------------------------
        # Sarvam API returns a JSON with base64 encoded audio strings in the 'audios' field
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
            import librosa
            import soundfile as sf
            import subprocess
            import shutil

            ffmpeg_cmd = shutil.which("ffmpeg") or "ffmpeg"
            
            # Check original vs tts duration
            orig_dur = end_time - start_time
            if orig_dur <= 0:
                orig_dur = 0.1
                
            y, sr = librosa.load(audio_path, sr=None)
            tts_dur = len(y) / sr
            
            speed = tts_dur / orig_dur
            
            # atempo limit is [0.5, 2.0]. Chain them if needed.
            filters = []
            temp_speed = speed
            while temp_speed > 2.0:
                filters.append("atempo=2.0")
                temp_speed /= 2.0
            while temp_speed < 0.5:
                filters.append("atempo=0.5")
                temp_speed /= 0.5
            if temp_speed != 1.0:
                filters.append(f"atempo={temp_speed:.3f}")
            
            if filters:
                logger.info(f"Adjusting speed: tts_dur={tts_dur:.2f}, target_dur={orig_dur:.2f}, speed={speed:.2f}")
                filter_str = ",".join(filters)
                out_path = audio_path.replace(".wav", "_synced.wav")
                
                cmd = [
                    ffmpeg_cmd, "-y", "-i", audio_path,
                    "-filter:a", filter_str,
                    out_path
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                audio_path = out_path
            
        except Exception as speed_err:
            logger.error(f"Lipsync speed adjustment failed: {speed_err}")

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
