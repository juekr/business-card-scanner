from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional, List
import os
from pydantic import validator
import json

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
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PATH: str = "/metrics"

    @validator("ALLOWED_ORIGINS")
    def parse_allowed_origins(cls, v) -> List[str]:
        print(f"DEBUG: ALLOWED_ORIGINS Validator wird aufgerufen mit Wert: {v!r}")
        print(f"DEBUG: Typ des Wertes: {type(v)}")
        
        try:
            if isinstance(v, str):
                # Versuche zuerst als JSON zu parsen
                try:
                    print("DEBUG: Versuche JSON-Parsing")
                    parsed = json.loads(v)
                    print(f"DEBUG: JSON-Parsing erfolgreich: {parsed!r}")
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError as e:
                    print(f"DEBUG: JSON-Parsing fehlgeschlagen: {e}")
                    # Wenn JSON-Parsing fehlschlägt, behandle es als komma-separierte Liste
                    origins = [origin.strip() for origin in v.split(",")]
                    origins = [origin for origin in origins if origin]
                    print(f"DEBUG: Als komma-separierte Liste geparst: {origins!r}")
                    return origins
            elif isinstance(v, list):
                print(f"DEBUG: Wert ist bereits eine Liste: {v!r}")
                return v
        except Exception as e:
            print(f"DEBUG: Unerwarteter Fehler: {e}")
            
        print("DEBUG: Verwende Standardwert")
        return ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

print("DEBUG: Starte Settings-Initialisierung")
settings = Settings()
print(f"DEBUG: Settings erfolgreich initialisiert mit ALLOWED_ORIGINS = {settings.ALLOWED_ORIGINS!r}")

# Ensure storage directories exist
os.makedirs(settings.IMAGE_STORAGE_PATH, exist_ok=True)
os.makedirs(settings.TEXT_STORAGE_PATH, exist_ok=True) 