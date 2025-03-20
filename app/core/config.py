from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional, List
import os
from pydantic import validator

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
    
    # Umgebung
    ENVIRONMENT: str = "development"
    MAX_WORKERS: int = 4
    PORT: int = 8000

    # OCR-Einstellungen
    TESSERACT_PATH: str = "/usr/bin/tesseract"
    TESSDATA_PREFIX: str = "/usr/share/tesseract-ocr/4.00/tessdata"
    TESSERACT_LANG: str = "deu"

    # Sicherheit
    API_KEY: str = "your-api-key-here"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PATH: str = "/metrics"

    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            # Versuche zuerst als JSON zu parsen
            try:
                import json
                return json.loads(v)
            except json.JSONDecodeError:
                # Wenn JSON-Parsing fehlschlägt, behandle es als komma-separierte Liste
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000"]  # Fallback-Wert
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()

# Ensure storage directories exist
os.makedirs(settings.IMAGE_STORAGE_PATH, exist_ok=True)
os.makedirs(settings.TEXT_STORAGE_PATH, exist_ok=True) 