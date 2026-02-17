def speech_to_text(
    self,
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

    try:
        import requests

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
            "file": audio_file
        }

        data = {
            "model": "saaras:v1",
            "translate": True,
            "target_language": "en"
        }

        # --------------------------
        # API CALL
        # --------------------------
        response = requests.post(url, headers=headers, files=files, data=data)
        result = response.json()

        final_text = result.get("transcript", "")

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
        return {
            "text": "",
            "start_time": start_time,
            "end_time": end_time,
            "speaker_no": speaker_no,
            "overlap": overlap,
            "gender": gender
        }
