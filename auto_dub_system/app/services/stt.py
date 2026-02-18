def speech_to_text(
    chunk_path: str,
    start_time: float,
    end_time: float,
    speaker_no: str,
    overlap: bool,
    gender: str
):
    """
    INPUT:
        chunk_path, start_time, end_time, speaker_no, overlap, gender

    PROCESS:
        SarvamAI Speech-to-Text + Translate

    OUTPUT:
        text,start_time,end_time,speaker_no,overlap,gender
    """

    import requests
    import logging
    from app.config import settings

    logger = logging.getLogger(__name__)

    try:
        # --------------------------
        # SARVAM API CONFIG
        # --------------------------
        SARVAM_API_KEY = settings.SARVAM_API_KEY
        url = "https://api.sarvam.ai/speech-to-text"

        # --------------------------
        # READ AUDIO
        # --------------------------
        with open(chunk_path, "rb") as f:
            audio_file = f.read()

        headers = {
            "api-subscription-key": SARVAM_API_KEY
        }

        files = {
            "file": ("audio.wav", audio_file, "audio/wav")
        }

        data = {
            "model": "saarika:v2.5",
            "translate": "true",
            "target_language": "en"
        }

        # --------------------------
        # API CALL
        # --------------------------
        response = requests.post(url, headers=headers, files=files, data=data)
        
        if response.status_code != 200:
            error_msg = f"Sarvam STT API error {response.status_code}: {response.text}"
            logger.error(error_msg)
            # Raise exception so Celery marks the task as failed (easier to debug)
            raise Exception(error_msg)

        result = response.json()
        logger.info(f"Sarvam STT result for {chunk_path}: {result}")

        final_text = result.get("transcript", "")

        if not final_text.strip():
            logger.warning(f"STT returned empty transcript for chunk: {chunk_path}")
            # Optional: raise error if you want to strictly fail on silence/empty outputs
            # raise ValueError("STT failed — empty transcription returned")

        # --------------------------
        # OUTPUT FORMAT
        # --------------------------
        return {
            "text": final_text,
            "start_time": start_time,
            "end_time": end_time,
            "speaker_no": speaker_no,
            "overlap": overlap,
            "gender": gender
        }

    except Exception as e:
        logger.error(f"Sarvam STT failed: {e}")
        # Re-raise to let Celery handle the failure visibility
        raise
