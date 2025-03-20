import pytesseract
from pathlib import Path
import logging
from typing import Dict, Any, Optional
import re
from app.core.config import settings
from app.services.image_processor import ImageProcessor
from app.models.contact import Contact, Address

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        self.image_processor = ImageProcessor()
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    
    def process_image(self, image_path: Path, debug: bool = False) -> tuple[Contact, float]:
        """
        Verarbeitet ein Bild und extrahiert Kontaktinformationen.
        """
        try:
            # Bild vorverarbeiten
            processed_image = self.image_processor.preprocess_image(image_path)
            
            # OCR durchführen
            text = pytesseract.image_to_string(
                processed_image,
                lang=settings.DEFAULT_LANGUAGE
            )
            
            # Kontaktdaten extrahieren
            contact_data = self._extract_contact_data(text)
            reliability_score = self._calculate_reliability_score(contact_data)
            
            # Kontakt erstellen
            contact = Contact(
                first_name=contact_data.get('first_name', ''),
                last_name=contact_data.get('last_name', ''),
                company=contact_data.get('company'),
                email=contact_data.get('email', ''),
                phone=contact_data.get('phone', ''),
                secondary_phone=contact_data.get('secondary_phone'),
                address=Address(
                    street=contact_data.get('street', ''),
                    city=contact_data.get('city', ''),
                    postal_code=contact_data.get('postal_code', ''),
                    country=contact_data.get('country', 'Deutschland')
                ),
                reliability_score=reliability_score
            )
            
            return contact, reliability_score
            
        except Exception as e:
            logger.error(f"Fehler bei OCR-Verarbeitung: {str(e)}")
            raise
    
    def _extract_contact_data(self, text: str) -> Dict[str, Any]:
        """
        Extrahiert strukturierte Kontaktdaten aus dem OCR-Text.
        """
        data = {}
        
        # Email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            data['email'] = email_match.group()
        
        # Telefonnummern
        phone_matches = re.finditer(
            r'(?:Tel|Fax|Mobil|Phone|Mobile)?(?:[.:])?\s*(?:\+\d{2}|0)[\d\s-]+',
            text
        )
        phone_numbers = [match.group() for match in phone_matches]
        if phone_numbers:
            data['phone'] = phone_numbers[0]
            if len(phone_numbers) > 1:
                data['secondary_phone'] = phone_numbers[1]
        
        # PLZ und Stadt
        postal_city_match = re.search(r'(\d{5})\s*([A-ZÄÖÜß][a-zäöüß-]+)', text)
        if postal_city_match:
            data['postal_code'] = postal_city_match.group(1)
            data['city'] = postal_city_match.group(2)
        
        # Straße
        street_match = re.search(r'([A-ZÄÖÜß][a-zäöüß-]+(?:straße|str\.|weg|gasse|platz|allee)\.?\s+\d+(?:[-\/]\d+)?)', text, re.IGNORECASE)
        if street_match:
            data['street'] = street_match.group(1)
        
        # Name und Firma
        lines = text.split('\n')
        for i, line in enumerate(lines):
            # Suche nach Namen (meist in den ersten Zeilen)
            if i < 3 and not data.get('first_name'):
                name_match = re.match(r'^([A-ZÄÖÜß][a-zäöüß-]+)\s+([A-ZÄÖÜß][a-zäöüß-]+)$', line.strip())
                if name_match:
                    data['first_name'] = name_match.group(1)
                    data['last_name'] = name_match.group(2)
            
            # Suche nach Firma (meist nach dem Namen)
            if i > 0 and not data.get('company'):
                company_indicators = ['GmbH', 'AG', 'KG', 'OHG', 'Ltd', 'Corp']
                if any(indicator in line for indicator in company_indicators):
                    data['company'] = line.strip()
        
        return data
    
    def _calculate_reliability_score(self, data: Dict[str, Any]) -> float:
        """
        Berechnet einen Zuverlässigkeitsscore für die extrahierten Daten.
        """
        required_fields = ['first_name', 'last_name', 'email', 'phone']
        optional_fields = ['company', 'secondary_phone', 'street', 'city', 'postal_code']
        
        # Gewichtung: Pflichtfelder = 0.7, optionale Felder = 0.3
        required_weight = 0.7
        optional_weight = 0.3
        
        # Berechne Score für Pflichtfelder
        required_score = sum(1 for field in required_fields if data.get(field)) / len(required_fields)
        
        # Berechne Score für optionale Felder
        optional_score = sum(1 for field in optional_fields if data.get(field)) / len(optional_fields)
        
        # Kombiniere Scores
        total_score = (required_score * required_weight) + (optional_score * optional_weight)
        
        return round(total_score, 2) 