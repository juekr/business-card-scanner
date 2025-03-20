from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from fastapi.responses import Response, PlainTextResponse
from typing import Optional, List
import json
from pathlib import Path
import logging
from datetime import datetime
from app.core.config import settings
from app.services.ocr_service import OCRService
from app.services.vcard_service import VCardService

router = APIRouter()
logger = logging.getLogger(__name__)

ocr_service = OCRService()
vcard_service = VCardService()

@router.post("/ingest")
async def ingest_file(
    file: UploadFile = File(...),
    accept: Optional[str] = Header(None),
    x_debug_mode: Optional[bool] = Header(False),
    x_ocr_settings: Optional[str] = Header(None)
):
    """
    Verarbeitet hochgeladene Dateien (Bilder oder Text) und gibt Kontaktdaten zurück.
    """
    try:
        # Datei speichern
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        file_path = Path(settings.STORAGE_PATH) / f"{timestamp}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # OCR-Parameter verarbeiten
        ocr_params = {}
        if x_ocr_settings:
            try:
                ocr_params = json.loads(x_ocr_settings)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Ungültige OCR-Parameter"
                )
        
        # Bild verarbeiten
        contact, reliability_score = ocr_service.process_image(file_path)
        
        # Debug-Informationen loggen
        if x_debug_mode:
            logger.info(f"Verarbeitete Datei: {file.filename}")
            logger.info(f"Zuverlässigkeits-Score: {reliability_score:.2%}")
            logger.info(f"OCR-Parameter: {ocr_params}")
        
        # Response basierend auf Accept-Header
        if accept == "text/markdown":
            content = vcard_service.create_markdown(contact)
            return PlainTextResponse(content=content)
        else:
            content = vcard_service.create_vcard(contact)
            return Response(
                content=content,
                media_type="text/vcard",
                headers={"Content-Disposition": f'attachment; filename="{timestamp}_contact.vcf"'}
            )
            
    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Verarbeitungsfehler: {str(e)}"
        )

@router.post("/ocr/debug")
async def debug_ocr(
    file: UploadFile = File(...),
    x_ocr_settings: Optional[str] = Header(None)
):
    """
    Debug-Endpoint für OCR-Optimierung.
    """
    try:
        # Datei speichern
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        file_path = Path(settings.STORAGE_PATH) / f"{timestamp}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # OCR-Parameter verarbeiten
        ocr_params = {}
        if x_ocr_settings:
            try:
                ocr_params = json.loads(x_ocr_settings)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Ungültige OCR-Parameter"
                )
        
        # Debug-Verarbeitung durchführen
        debug_results = ocr_service.image_processor.debug_process(file_path)
        
        # Ergebnisse aufbereiten
        results = {}
        for key, (_, score) in debug_results.items():
            results[key] = {
                "score": score,
                "parameters": key.split("_")
            }
        
        return {
            "filename": file.filename,
            "results": results,
            "best_score": max(results.items(), key=lambda x: x[1]["score"])
        }
        
    except Exception as e:
        logger.error(f"Fehler beim OCR-Debug: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Debug-Fehler: {str(e)}"
        ) 