import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        self.default_params = {
            'contrast': 1.5,
            'gamma': 1.0,
            'rotation': 0
        }
    
    def preprocess_image(self, image_path: Path, params: Dict[str, Any] = None) -> np.ndarray:
        """
        Verarbeitet ein Bild mit den gegebenen Parametern vor.
        """
        if params is None:
            params = self.default_params
            
        try:
            # Bild laden
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"Konnte Bild nicht laden: {image_path}")
            
            # Graustufen konvertieren
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Kontrast anpassen
            contrast = params.get('contrast', self.default_params['contrast'])
            gray = cv2.convertScaleAbs(gray, alpha=contrast)
            
            # Gamma-Korrektur
            gamma = params.get('gamma', self.default_params['gamma'])
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255
                            for i in np.arange(0, 256)]).astype("uint8")
            gray = cv2.LUT(gray, table)
            
            # Deskewing
            coords = np.column_stack(np.where(gray > 0))
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = 90 + angle
            
            # Rotation
            rotation = params.get('rotation', self.default_params['rotation'])
            angle += rotation
            
            (h, w) = gray.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(gray, M, (w, h),
                                   flags=cv2.INTER_CUBIC,
                                   borderMode=cv2.BORDER_REPLICATE)
            
            return rotated
            
        except Exception as e:
            logger.error(f"Fehler bei der Bildverarbeitung: {str(e)}")
            raise
    
    def debug_process(self, image_path: Path) -> Dict[str, Tuple[np.ndarray, float]]:
        """
        Führt verschiedene Parameterkombinationen aus und gibt die Ergebnisse zurück.
        """
        results = {}
        
        # Parameter-Kombinationen für Debug
        contrast_values = [1.0, 1.5, 2.0]
        gamma_values = [0.8, 1.0, 1.2]
        rotation_values = [-5, 0, 5]
        
        for contrast in contrast_values:
            for gamma in gamma_values:
                for rotation in rotation_values:
                    params = {
                        'contrast': contrast,
                        'gamma': gamma,
                        'rotation': rotation
                    }
                    
                    try:
                        processed = self.preprocess_image(image_path, params)
                        # Einfache Qualitätsbewertung basierend auf Bildstatistiken
                        quality_score = self._calculate_quality_score(processed)
                        
                        key = f"c{contrast}_g{gamma}_r{rotation}"
                        results[key] = (processed, quality_score)
                        
                    except Exception as e:
                        logger.error(f"Fehler bei Parameter-Kombination {params}: {str(e)}")
                        continue
        
        return results
    
    def _calculate_quality_score(self, image: np.ndarray) -> float:
        """
        Berechnet einen einfachen Qualitätsscore für das verarbeitete Bild.
        """
        # Berechne Bildstatistiken
        mean = np.mean(image)
        std = np.std(image)
        
        # Normalisiere die Werte
        normalized_mean = mean / 255.0
        normalized_std = std / 128.0
        
        # Kombiniere zu einem Score (0-1)
        score = (normalized_mean * 0.4 + normalized_std * 0.6)
        return min(max(score, 0.0), 1.0) 