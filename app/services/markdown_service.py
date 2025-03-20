from app.models.contact import Contact
import logging

logger = logging.getLogger(__name__)

class MarkdownService:
    """Service für die Erstellung von Markdown-Ausgaben."""
    
    def create_markdown(self, contact: Contact) -> str:
        """Erstellt eine Markdown-Repräsentation der Kontaktdaten."""
        try:
            # Name und Firma
            markdown = f"# {contact.first_name} {contact.last_name}\n\n"
            if contact.company:
                markdown += f"**{contact.company}**\n\n"
            
            # Kontaktinformationen
            if contact.email:
                markdown += f"- 📧 {contact.email}\n"
            if contact.phone:
                markdown += f"- 📞 {contact.phone}\n"
            if contact.secondary_phone:
                markdown += f"- 📱 {contact.secondary_phone}\n"
            
            # Adresse
            if contact.address:
                address_lines = []
                if contact.address.street:
                    address_lines.append(contact.address.street)
                if contact.address.postal_code and contact.address.city:
                    address_lines.append(f"{contact.address.postal_code} {contact.address.city}")
                if contact.address.country:
                    address_lines.append(contact.address.country)
                
                if address_lines:
                    markdown += "\n## Adresse\n"
                    markdown += "\n".join(f"- {line}" for line in address_lines)
            
            # Zuverlässigkeits-Score
            markdown += f"\n\n*Zuverlässigkeits-Score: {contact.reliability_score:.0%}*"
            
            # Escape-Sequenzen verarbeiten
            return markdown.replace("\\n", "\n")
            
        except Exception as e:
            logger.error(f"Fehler bei Markdown-Erstellung: {str(e)}")
            raise 