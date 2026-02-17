import os
# from pydantic_settings import BaseSettings

class Settings:
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    MODEL_PATH: str = os.getenv("MODEL_PATH", "app/models/xgboost.json")
    
    # class Config:
    #     env_file = ".env"

settings = Settings()
