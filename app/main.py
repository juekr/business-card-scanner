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
    allow_origins=["*"],  # In Produktion einschränken!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router einbinden
app.include_router(
    ingest.router,
    prefix=f"/api/{settings.API_VERSION}",
    tags=["ingest"]
) 