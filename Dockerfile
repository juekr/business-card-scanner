# Build-Stage
FROM python:3.11-slim AS builder

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-deu \
    tesseract-ocr-eng \
    libleptonica-dev \
    pkg-config \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    poppler-utils \
    libheif-dev \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Dependencies installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Beste Trainingsmodelle herunterladen
RUN mkdir -p /usr/share/tesseract-ocr/4.00/tessdata && \
    wget -O /usr/share/tesseract-ocr/4.00/tessdata/deu.traineddata https://github.com/tesseract-ocr/tessdata_best/raw/main/deu.traineddata && \
    wget -O /usr/share/tesseract-ocr/4.00/tessdata/eng.traineddata https://github.com/tesseract-ocr/tessdata_best/raw/main/eng.traineddata

# Produktions-Stage
FROM python:3.11-slim

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-deu \
    tesseract-ocr-eng \
    libleptonica-dev \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    poppler-utils \
    libheif-dev \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Python-Pakete aus Builder kopieren
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Tesseract-Daten kopieren
COPY --from=builder /usr/share/tesseract-ocr/4.00/tessdata /usr/share/tesseract-ocr/4.00/tessdata

# Tesseract-Konfiguration
RUN mkdir -p /usr/share/tesseract-ocr/4.00/tessdata/configs && \
    mkdir -p /etc/tesseract-ocr/configs && \
    echo "tessedit_pageseg_mode 1\ntessedit_char_whitelist abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZäöüÄÖÜß0123456789.,- @" > /usr/share/tesseract-ocr/4.00/tessdata/configs/custom && \
    echo "deu" > /usr/share/tesseract-ocr/4.00/tessdata/configs/lang

# Storage-Verzeichnisse erstellen
RUN mkdir -p /app/storage/images /app/storage/text_files && \
    chown -R 1000:1000 /app/storage

# Nicht-Root Benutzer erstellen
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Anwendungscode kopieren
COPY ./app /app/app

USER appuser

# Umgebungsvariablen
ENV PYTHONUNBUFFERED=1 \
    TESSERACT_PATH=/usr/bin/tesseract \
    TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata \
    STORAGE_PATH=/app/storage \
    PORT=8000 \
    PATH="/usr/local/bin:${PATH}"

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Port
EXPOSE ${PORT}

# Start-Kommando
CMD ["/usr/local/bin/python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 