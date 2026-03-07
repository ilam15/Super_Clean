import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    
    Attributes defined here map to environment variables (case-insensitive).
    """
    
    # Core Config
    REDIS_URL: str = "redis://localhost:6379/0"
    MODEL_PATH: str = "app/models/xgboost.json"
    SARVAM_API_KEY: str = ""

    # AWS S3 Settings
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET_NAME: str = ""
    AWS_S3_REGION: str = "us-east-1"

    # Potential extra env vars (causing validation errors if not defined or ignored)
    HF_TOKEN: str = ""
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    # Pydantic v2 Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Critical: Ignores extra env vars instead of raising ValidationError
    )

settings = Settings()

# ---------------------------------------------------------
# Bulbul:v3 Voice Roster (Sarvam AI TTS)
# ---------------------------------------------------------
BULBUL_MALE_VOICES = [
    "shubh", "aditya", "rahul", "amit", "dev", "varun", "sumit", 
    "kabir", "aayan", "ashutosh", "advait", "anand", "tarun", "sunny", 
    "mani", "gokul", "vijay", "mohit", "rehan", "soham"
]

BULBUL_FEMALE_VOICES = [
    "priya", "ritu", "neha", "pooja", "simran", "kavya", "ishita", 
    "shreya", "roopa", "amelia", "sophia", "tanya", "shruti", "suhani", 
    "kavitha", "rupali"
]

def get_assigned_voice(speaker_id: str, gender: str) -> str:
    """
    Deterministically assigns a voice from the Bulbul roster 
    based on the speaker ID (e.g., 'SPEAKER_00') and gender.
    """
    import hashlib
    
    # Extract just the number from "SPEAKER_00", "SPEAKER_01" if possible,
    # otherwise hash the whole ID to ensure a consistent index lookup.
    try:
        if separator_idx := speaker_id.rfind("_") + 1:
            idx_seed = int(speaker_id[separator_idx:])
        else:
            idx_seed = int(hashlib.md5(speaker_id.encode()).hexdigest(), 16)
    except Exception:
        idx_seed = int(hashlib.md5(speaker_id.encode()).hexdigest(), 16)

    is_female = gender.lower() == "female"
    voice_list = BULBUL_FEMALE_VOICES if is_female else BULBUL_MALE_VOICES
    
    # Use modulo to pick a consistent voice from the list
    voice_idx = idx_seed % len(voice_list)
    return voice_list[voice_idx]
