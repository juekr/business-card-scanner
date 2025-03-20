from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
import logging
from app.api.endpoints import ingest
from app.core.config import settings

# Logger konfigurieren
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# API Key Setup
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Ungültiger API-Key"
        )
    return api_key

# FastAPI App erstellen
app = FastAPI(
    title="Business Card Reader API",
    description="API zum Extrahieren von Kontaktdaten aus Visitenkarten",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check (ohne API-Key)
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

# Router einbinden (mit API-Key)
app.include_router(
    ingest.router,
    prefix="/api/v1",
    tags=["Ingest"],
    dependencies=[Depends(verify_api_key)]
) 