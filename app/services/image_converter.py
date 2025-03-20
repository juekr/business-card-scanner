import os
from pathlib import Path
from typing import Optional
from PIL import Image
import logging
from pdf2image import convert_from_path
from pillow_heif import register_heif_opener

# Registriere HEIF-Unterstützung
register_heif_opener()

logger = logging.getLogger(__name__)

class ImageConverter:
    SUPPORTED_FORMATS = {
        '.jpg': 'JPEG',
        '.jpeg': 'JPEG',
        '.png': 'PNG',
        '.bmp': 'BMP',
        '.heic': 'HEIC',
        '.pdf': 'PDF',
        '.gif': 'GIF',
        '.svg': 'SVG',
        '.webp': 'WEBP'
    }
    
    @classmethod
    def convert_to_jpeg(cls, input_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Konvertiert ein Bild in JPEG-Format.
        Unterstützt: jpg, jpeg, png, bmp, heic, pdf, gif, svg, webp
        """
        try:
            input_path = Path(input_path)
            if not input_path.exists():
                raise FileNotFoundError(f"Eingabedatei nicht gefunden: {input_path}")
            
            # Bestimme Ausgabepfad
            if output_path is None:
                output_path = input_path.with_suffix('.jpg')
            
            # Prüfe Dateiendung
            suffix = input_path.suffix.lower()
            if suffix not in cls.SUPPORTED_FORMATS:
                raise ValueError(f"Nicht unterstütztes Dateiformat: {suffix}")
            
            # Spezielle Behandlung für PDF
            if suffix == '.pdf':
                # Konvertiere erste Seite zu JPEG
                images = convert_from_path(input_path, first_page=1, last_page=1)
                if not images:
                    raise ValueError("PDF konnte nicht konvertiert werden")
                images[0].save(output_path, 'JPEG')
                return output_path
            
            # Öffne und konvertiere Bild
            with Image.open(input_path) as img:
                # Konvertiere zu RGB falls nötig
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Speichere als JPEG
                img.save(output_path, 'JPEG', quality=95)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Fehler bei der Bildkonvertierung: {str(e)}")
            raise 