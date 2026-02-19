import requests
import json
import os
from app.config import settings

def test():
    url = "https://api.sarvam.ai/speech-to-text"
    headers = {"api-subscription-key": settings.SARVAM_API_KEY}
    chunk_path = r"c:\Users\sweth\OneDrive\Desktop\autodub1\Super_Clean\auto_dub_system\segments\seg_0000_SPEAKER_00_chunk_0000.wav"
    with open(chunk_path, "rb") as f:
        audio_bytes = f.read()
    files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
    data = {
        "model": "saaras:v3",
        "translate": True,
        "target_language": "en",
        "punctuate": True,
        "auto_detect": True
    }
    res = requests.post(url, headers=headers, files=files, data=data)
    with open("stt_debug.json", "w") as f:
        f.write(res.text)

if __name__ == "__main__":
    test()
