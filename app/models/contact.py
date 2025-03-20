from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

class Address(BaseModel):
    street: str = Field(default="")
    city: str = Field(default="")
    postal_code: str = Field(default="")
    country: str = Field(default="Deutschland")

class Contact(BaseModel):
    first_name: str = Field(default="")
    last_name: str = Field(default="")
    company: Optional[str] = None
    position: Optional[str] = None  # Funktion/Position in der Firma
    email: Optional[str] = None
    phone: str = Field(default="")
    secondary_phone: Optional[str] = None
    address: Address = Field(default_factory=Address)
    created_at: datetime = Field(default_factory=datetime.now)
    reliability_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    @validator('email')
    def validate_email(cls, v):
        if v is None or v == "":
            return None
        if '@' not in v or '.' not in v:
            return None
        return v

    @property
    def full_name(self) -> str:
        """Gibt den vollständigen Namen zurück."""
        if not self.first_name and not self.last_name:
            return "Unbekannt"
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def formatted_name(self) -> str:
        """Gibt den formatierten Namen für vCard zurück."""
        if not self.first_name and not self.last_name:
            return "Unbekannt"
        return f"{self.last_name};{self.first_name};;;"

    def to_text(self) -> str:
        """Gibt die Kontaktdaten als formatierten Text zurück."""
        lines = []
        lines.append(f"{self.full_name}")
        if self.position:
            lines.append(f"{self.position}")
        if self.company:
            lines.append(f"{self.company}")
        if self.email:
            lines.append(f"E-Mail: {self.email}")
        if self.phone:
            lines.append(f"Tel: {self.phone}")
        if self.secondary_phone:
            lines.append(f"Mobil: {self.secondary_phone}")
        if self.address and any([self.address.street, self.address.postal_code, self.address.city]):
            address_parts = []
            if self.address.street:
                address_parts.append(self.address.street)
            if self.address.postal_code or self.address.city:
                address_parts.append(f"{self.address.postal_code} {self.address.city}".strip())
            if self.address.country and self.address.country != "Deutschland":
                address_parts.append(self.address.country)
            lines.append("\n".join(address_parts))
        return "\n".join(lines)

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Max",
                "last_name": "Mustermann",
                "company": "Beispiel GmbH",
                "position": "Geschäftsführer",
                "email": "max.mustermann@beispiel.de",
                "phone": "+49 123 456789",
                "secondary_phone": None,
                "address": {
                    "street": "Musterstraße 123",
                    "city": "Musterstadt",
                    "postal_code": "12345",
                    "country": "Deutschland"
                },
                "reliability_score": 0.85
            }
        } 