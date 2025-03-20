import vobject
from app.models.contact import Contact
from typing import Union
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class VCardService:
    """Service für die Erstellung von vCard-Ausgaben."""
    
    def create_vcard(self, contact: Contact) -> str:
        """Erstellt eine vCard-Repräsentation der Kontaktdaten."""
        try:
            # vCard erstellen
            vcard = vobject.vCard()
            
            # Name
            vcard.add('n').value = vobject.vcard.Name(family=contact.last_name, given=contact.first_name)
            vcard.add('fn').value = f"{contact.first_name} {contact.last_name}"
            
            # Firma und Position
            if contact.company:
                vcard.add('org').value = [contact.company]
                if contact.position:
                    vcard.add('title').value = contact.position.strip()
            
            # E-Mail
            if contact.email:
                email = vcard.add('email')
                email.type_param = 'INTERNET'
                email.value = contact.email.strip()
            
            # Telefonnummern
            if contact.phone:
                phone = vcard.add('tel')
                phone.type_param = 'WORK'
                phone.value = contact.phone.strip()
            
            if contact.secondary_phone and len(contact.secondary_phone.strip()) > 5:  # Nur echte Telefonnummern
                phone = vcard.add('tel')
                phone.type_param = 'CELL'
                phone.value = contact.secondary_phone.strip()
            
            # Adresse
            if contact.address:
                adr = vcard.add('adr')
                adr.type_param = 'WORK'
                adr.value = vobject.vcard.Address(
                    street=contact.address.street.strip(),
                    city=contact.address.city.strip(),
                    code=contact.address.postal_code.strip(),
                    country=contact.address.country.strip()
                )
            
            # Metadaten
            vcard.add('version').value = '3.0'
            vcard.add('prodid').value = '-//Business Card Reader//DE'
            vcard.add('rev').value = datetime.now().strftime('%Y%m%dT%H%M%SZ')
            
            # vCard als String zurückgeben und überflüssige Zeilenumbrüche entfernen
            return vcard.serialize().strip()
            
        except Exception as e:
            logger.error(f"Fehler bei vCard-Erstellung: {str(e)}")
            raise
    
    def create_markdown(self, contact: Contact) -> str:
        """
        Erstellt eine Markdown-Formatierung der Kontaktdaten.
        """
        try:
            markdown = []
            markdown.append(f"# {contact.first_name} {contact.last_name}")
            markdown.append("")
            
            if contact.company:
                markdown.append(f"## {contact.company}")
                if contact.position:
                    markdown.append(f"*{contact.position}*")
                markdown.append("")
            
            markdown.append("### Kontaktdaten")
            markdown.append(f"- E-Mail: {contact.email}")
            markdown.append(f"- Telefon: {contact.phone}")
            
            if contact.secondary_phone:
                markdown.append(f"- Alternative Nummer: {contact.secondary_phone}")
            
            markdown.append("")
            markdown.append("### Adresse")
            markdown.append(f"{contact.address.street}")
            markdown.append(f"{contact.address.postal_code} {contact.address.city}")
            markdown.append(f"{contact.address.country}")
            
            markdown.append("")
            markdown.append("---")
            markdown.append(f"Zuverlässigkeits-Score: {contact.reliability_score:.2%}")
            
            return "\n".join(markdown)
            
        except Exception as e:
            logger.error(f"Fehler bei Markdown-Erstellung: {str(e)}")
            raise 