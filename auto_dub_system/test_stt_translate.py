import requests
import os
from app.config import settings

def test_stt_translation():
    url = "https://api.sarvam.ai/speech-to-text"
    headers = {"api-subscription-key": settings.SARVAM_API_KEY}
    
    chunk_path = r"c:\Users\sweth\OneDrive\Desktop\autodub1\Super_Clean\auto_dub_system\segments\seg_0000_SPEAKER_00_chunk_0000.wav"
    
    if not os.path.exists(chunk_path):
        print(f"File not found: {chunk_path}")
        return

    with open(chunk_path, "rb") as f:
        audio_bytes = f.read()
    files = {"file": ("audio.wav", audio_bytes, "audio/wav")}

    data = {
        "model": "saaras:v3",
        "translate": True,
        "target_language": "en", # Try translating to English
        "punctuate": True,
        "auto_detect": True
    }

    print(f"Calling Sarvam STT with translate=True...")
    response = requests.post(url, headers=headers, files=files, data=data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_stt_translation()
