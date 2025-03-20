import os
import cv2
import numpy as np
import pytesseract
from pathlib import Path
import logging
from typing import Dict, Any, Optional, Tuple
import re
from app.core.config import settings
from app.services.image_processor import ImageProcessor
from app.services.image_converter import ImageConverter
from app.models.contact import Contact, Address

# Konfiguriere Tesseract-Pfad für macOS
if os.path.exists('/opt/homebrew/bin/tesseract'):
    pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        self.image_processor = ImageProcessor()
    
    @staticmethod
    def preprocess_image(image_path: str) -> np.ndarray:
        """Bildvorverarbeitung für optimale OCR-Ergebnisse."""
        try:
            # Bild einlesen
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Konnte Bild nicht einlesen: {image_path}")
            
            # Kopie für Texterkennung
            debug_image = image.copy()
            
            # In Graustufen umwandeln
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Rauschreduzierung (minimal)
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Kantenerkennung für Textbereiche
            edges = cv2.Canny(denoised, 50, 150)
            
            # Dilatation um Textbereiche zu verbinden
            kernel = np.ones((3,3), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=2)
            
            # Finde Konturen
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filtere kleine Konturen
            min_area = image.shape[0] * image.shape[1] * 0.001  # 0.1% der Bildfläche
            text_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
            
            # Finde Bounding Box für alle Textbereiche
            if text_contours:
                # Kombiniere alle Konturen
                x_coords = []
                y_coords = []
                for cnt in text_contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    x_coords.extend([x, x + w])
                    y_coords.extend([y, y + h])
                
                # Berechne Gesamtbereich
                x_min, x_max = max(0, min(x_coords)), min(image.shape[1], max(x_coords))
                y_min, y_max = max(0, min(y_coords)), min(image.shape[0], max(y_coords))
                
                # Füge Padding hinzu (5% der Bildgröße)
                padding_x = int(image.shape[1] * 0.05)
                padding_y = int(image.shape[0] * 0.05)
                x_min = max(0, x_min - padding_x)
                y_min = max(0, y_min - padding_y)
                x_max = min(image.shape[1], x_max + padding_x)
                y_max = min(image.shape[0], y_max + padding_y)
                
                # Schneide Bild zu
                image = image[y_min:y_max, x_min:x_max]
                
                # Debug: Zeichne erkannte Textbereiche
                for cnt in text_contours:
                    cv2.drawContours(debug_image, [cnt], -1, (0, 255, 0), 2)
                cv2.rectangle(debug_image, (x_min, y_min), (x_max, y_max), (0, 0, 255), 2)
                
                # Speichere Debug-Bild
                debug_path = str(Path(image_path).with_suffix('.debug.jpg'))
                cv2.imwrite(debug_path, debug_image)
                logger.debug(f"Debug-Bild gespeichert: {debug_path}")
            
            # In Graustufen umwandeln (zugeschnittenes Bild)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Rauschreduzierung
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Einfache Schwellwertbildung
            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            return binary
        except Exception as e:
            logger.error(f"Fehler bei der Bildvorverarbeitung: {str(e)}")
            raise
    
    def process_image(self, image_path: str, lang: str = 'deu') -> Tuple[Contact, float]:
        """Verarbeitet ein Bild mit OCR und extrahiert Kontaktinformationen."""
        try:
            # Bildvorverarbeitung
            processed_image = OCRService.preprocess_image(image_path)
            
            # OCR durchführen mit Standardparametern
            text = pytesseract.image_to_string(
                processed_image,
                lang=lang,
                config='--psm 1'  # Automatische Seitensegmentierung mit OSD
            )
            
            # Debug-Ausgabe
            logger.debug(f"OCR Text:\n{text}")
            
            # Kontaktdaten extrahieren
            contact_data = self._extract_contact_data(text)
            reliability_score = self._calculate_reliability_score(contact_data)
            
            # Stelle sicher, dass Name nicht leer ist
            if not contact_data.get('first_name') and not contact_data.get('last_name'):
                # Suche nach der ersten Zeile, die wie ein Name aussieht
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                for line in lines:
                    # Überspringe Zeilen mit typischen nicht-Namen-Inhalten
                    if any(char in line for char in '@/') or \
                       re.match(r'^\d{5}', line) or \
                       re.match(r'^[\d\s\-+()]+$', line) or \
                       any(word in line.lower() for word in ['www', 'http', 'tel', 'fax', 'mobil', 'gmbh', 'ag', 'kg']):
                        continue
                    
                    # Prüfe auf Namensformat (mindestens zwei Wörter, keine Zahlen)
                    words = line.split()
                    if len(words) >= 2 and not any(char.isdigit() for char in line):
                        contact_data['first_name'] = words[0]
                        contact_data['last_name'] = ' '.join(words[1:])
                        break
            
            # Stelle sicher, dass Name nicht leer ist (Fallback)
            if not contact_data.get('first_name') and not contact_data.get('last_name'):
                contact_data['first_name'] = 'Unbekannt'
                contact_data['last_name'] = 'Unbekannt'
            
            # Kontakt erstellen
            contact = Contact(
                first_name=contact_data.get('first_name', 'Unbekannt'),
                last_name=contact_data.get('last_name', 'Unbekannt'),
                company=contact_data.get('company'),
                position=contact_data.get('position'),
                email=contact_data.get('email'),
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
    
    def _extract_contact_data(self, text: str) -> Dict[str, str]:
        """Extrahiert Kontaktdaten aus dem OCR-Text."""
        try:
            # Zeilen aufteilen und Leerzeilen entfernen
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Initialisiere Kontaktdaten
            contact_data = {
                'first_name': '',
                'last_name': '',
                'company': None,
                'position': None,
                'email': None,
                'phone': '',
                'secondary_phone': None,
                'street': '',
                'city': '',
                'postal_code': '',
                'country': 'Deutschland'
            }
            
            # Debug-Ausgabe
            logger.debug(f"OCR Text:\n{text}")
            
            # Name suchen
            name_found = False
            for line in lines:
                # Überspringe Zeilen mit bestimmten Inhalten
                if any(char in line for char in '@/&') or \
                   re.match(r'^\d{5}', line) or \
                   re.match(r'^[\d\s\-+()]+$', line) or \
                   any(word.lower() in line.lower() for word in [
                       'www', 'http', 'tel', 'fax', 'mobil', 'gmbh', 'ag', 'kg', 'ohg',
                       'ltd', 'corp', 'feser', 'graf', 'auto', 'gruppe', 'group'
                   ]):
                    continue
                
                # Prüfe auf Namensformat
                words = line.split()
                if len(words) >= 2 and \
                   not any(char.isdigit() for char in line) and \
                   all(word[0].isupper() for word in words if len(word) > 1) and \
                   all(len(word) <= 20 for word in words):  # Maximale Wortlänge
                    contact_data['first_name'] = words[0]
                    contact_data['last_name'] = ' '.join(words[1:])
                    name_found = True
                    break
            
            # Firma und Position suchen
            company_found = False
            position_found = False
            
            # Typische Positionstitel
            position_indicators = [
                'geschäftsführer', 'leiter', 'manager', 'direktor', 'vorstand',
                'berater', 'verkauf', 'vertrieb', 'consultant', 'mitarbeiter',
                'spezialist', 'experte', 'chef', 'inhaber', 'verkaufsberater',
                'automobilverkäufer', 'verkäufer', 'assistent', 'assistant'
            ]
            
            # Erste Durchlauf: Suche nach Position vor der Firma
            for i, line in enumerate(lines):
                line_lower = line.lower()
                
                # Überspringe bereits verarbeitete Namenszeile
                if name_found and line == f"{contact_data['first_name']} {contact_data['last_name']}":
                    continue
                
                # Überspringe Zeilen mit bestimmten Inhalten
                if any(char in line for char in '@/') or \
                   re.match(r'^\d{5}', line) or \
                   re.match(r'^[\d\s\-+()]+$', line) or \
                   any(word in line_lower for word in ['www', 'http', 'tel', 'fax', 'mobil']):
                    continue
                
                # Position vor der Firma
                if not position_found and not company_found:
                    # Prüfe auf typische Positionstitel
                    if any(indicator in line_lower for indicator in position_indicators):
                        contact_data['position'] = line.strip()
                        position_found = True
                        continue
                    # Wenn die nächste Zeile eine Firma ist
                    elif i + 1 < len(lines) and \
                         any(indicator in lines[i + 1] for indicator in ['GmbH', 'AG', 'KG', 'OHG', 'Ltd', 'Corp', '& Co']):
                        contact_data['position'] = line.strip()
                        position_found = True
                        continue
                
                # Prüfe auf typische Firmenbezeichnungen
                if not company_found and any(indicator in line for indicator in ['GmbH', 'AG', 'KG', 'OHG', 'Ltd', 'Corp', '& Co']):
                    # Wenn "FESER" oder "GRAF" im Text steht, suche nach der vollständigen Firma
                    
                    contact_data['company'] = line.strip()
                    company_found = True
                    continue
            
            # Zweiter Durchlauf: Suche nach Position nach der Firma
            if company_found and not position_found:
                for line in lines:
                    line_lower = line.lower()
                    
                    # Überspringe bereits verarbeitete Zeilen
                    if line == contact_data['company'] or \
                       (name_found and line == f"{contact_data['first_name']} {contact_data['last_name']}"):
                        continue
                    
                    # Überspringe Zeilen mit bestimmten Inhalten
                    if any(char in line for char in '@/') or \
                       re.match(r'^\d{5}', line) or \
                       re.match(r'^[\d\s\-+()]+$', line) or \
                       any(word in line_lower for word in ['www', 'http', 'tel', 'fax', 'mobil']):
                        continue
                    
                    # Prüfe auf Position
                    if not any(indicator in line for indicator in ['GmbH', 'AG', 'KG', 'OHG', 'Ltd', 'Corp', '& Co']):
                        if any(indicator in line_lower for indicator in position_indicators):
                            contact_data['position'] = line.strip()
                            position_found = True
                            break
                        # Wenn keine bekannte Position gefunden wurde, nimm die erste geeignete Zeile
                        elif not position_found and len(line.split()) <= 5:  # Max. 5 Wörter für Position
                            contact_data['position'] = line.strip()
                            position_found = True
                            break
            
            # E-Mail
            for line in lines:
                if '@' in line and '.' in line:
                    email = line.strip().replace(' ', '')
                    if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                        contact_data['email'] = email
                        break
            
            # Telefonnummern
            phone_lines = [line for line in lines if any(char.isdigit() for char in line)]
            for line in phone_lines:
                # Entferne "T" und alle nicht-numerischen Zeichen außer + und -
                cleaned = (''.join(char for char in line if char.isdigit() or char in '+ -')).strip()
                # Prüfe auf mindestens 5 Ziffern (nicht Zeichen)
                if sum(c.isdigit() for c in cleaned) > 5:
                    if not contact_data['phone']:
                        contact_data['phone'] = cleaned
                    else:
                        contact_data['secondary_phone'] = cleaned
                        break
            
            # Adresse (von unten nach oben)
            address_lines: list[str] = []
            for line in reversed(lines):
                # PLZ und Stadt
                if re.match(r'^\d{5}', line):
                    parts = line.split()
                    if len(parts) >= 2:
                        contact_data['postal_code'] = parts[0]
                        contact_data['city'] = ' '.join(parts[1:])
                        continue
                
                # Straße (wenn keine E-Mail/Telefon/Website)
                if not any(keyword in line.lower() for keyword in ['@', 'tel', 'fax', 'mobil', 'www']):
                    if not contact_data['street']:  # Nur erste Straßenzeile
                        contact_data['street'] = line.strip()
            
            # Debug-Ausgabe
            logger.debug(f"Extrahierte Daten:\n{contact_data}")
            
            return contact_data
            
        except Exception as e:
            logger.error(f"Fehler bei Extraktion der Kontaktdaten: {str(e)}")
            raise
    
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