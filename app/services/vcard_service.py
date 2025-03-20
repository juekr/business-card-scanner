import vobject
from app.models.contact import Contact
from typing import Union
import logging

logger = logging.getLogger(__name__)

class VCardService:
    def create_vcard(self, contact: Contact) -> str:
        """
        Erstellt eine vCard aus den Kontaktdaten.
        """
        try:
            vcard = vobject.vCard()
            
            # Name
            vcard.add('n')
            vcard.n.value = vobject.vcard.Name(
                family=contact.last_name,
                given=contact.first_name
            )
            
            # Formatierter Name
            vcard.add('fn')
            vcard.fn.value = f"{contact.first_name} {contact.last_name}"
            
            # Firma
            if contact.company:
                vcard.add('org')
                vcard.org.value = [contact.company]
            
            # Email
            vcard.add('email')
            vcard.email.value = contact.email
            vcard.email.type_param = 'INTERNET'
            
            # Telefon
            vcard.add('tel')
            vcard.tel.value = contact.phone
            vcard.tel.type_param = 'WORK'
            
            # Zweite Telefonnummer
            if contact.secondary_phone:
                tel = vcard.add('tel')
                tel.value = contact.secondary_phone
                tel.type_param = 'CELL'  # oder 'FAX', abhängig vom Kontext
            
            # Adresse
            vcard.add('adr')
            vcard.adr.value = vobject.vcard.Address(
                street=contact.address.street,
                city=contact.address.city,
                code=contact.address.postal_code,
                country=contact.address.country
            )
            vcard.adr.type_param = 'WORK'
            
            return vcard.serialize()
            
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