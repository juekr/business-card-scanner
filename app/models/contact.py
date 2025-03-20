from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class Address(BaseModel):
    street: str
    city: str
    postal_code: str
    country: str = "Deutschland"

class Contact(BaseModel):
    first_name: str
    last_name: str
    company: Optional[str] = None
    email: EmailStr
    phone: str
    secondary_phone: Optional[str] = None
    address: Address
    created_at: datetime = Field(default_factory=datetime.now)
    reliability_score: float = Field(ge=0, le=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Max",
                "last_name": "Mustermann",
                "company": "Musterfirma GmbH",
                "email": "max.mustermann@musterfirma.de",
                "phone": "+49 123 4567890",
                "secondary_phone": "+49 123 4567891",
                "address": {
                    "street": "Musterstraße 123",
                    "city": "Musterstadt",
                    "postal_code": "12345",
                    "country": "Deutschland"
                }
            }
        } 