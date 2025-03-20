from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.api.endpoints import ingest
from app.core.config import settings

# Logger konfigurieren
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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

# Health Check
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

# Router einbinden
app.include_router(
    ingest.router,
    prefix="/api/v1",
    tags=["Ingest"]
) 