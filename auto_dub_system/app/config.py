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
