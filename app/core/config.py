from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional
import os

class Settings(BaseSettings):
    # API Settings
    API_VERSION: str = "v1"
    DEBUG: bool = False
    
    # Storage Settings
    STORAGE_PATH: Path = Path("storage")
    IMAGE_STORAGE_PATH: Path = STORAGE_PATH / "images"
    TEXT_STORAGE_PATH: Path = STORAGE_PATH / "text_files"
    
    # OCR Settings
    TESSERACT_CMD: str = "/usr/local/bin/tesseract"
    DEFAULT_LANGUAGE: str = "deu"
    OCR_TIMEOUT: int = 30
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# Ensure storage directories exist
os.makedirs(settings.IMAGE_STORAGE_PATH, exist_ok=True)
os.makedirs(settings.TEXT_STORAGE_PATH, exist_ok=True) 