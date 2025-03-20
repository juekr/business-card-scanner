# Build-Stage
FROM python:3.11-slim as builder

WORKDIR /app

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-deu \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Produktions-Stage
FROM python:3.11-slim

WORKDIR /app

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-deu \
    && rm -rf /var/lib/apt/lists/*

# Python-Pakete von builder kopieren
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/

# Anwendungscode kopieren
COPY app/ app/
COPY .env.example .env

# Storage-Verzeichnisse erstellen
RUN mkdir -p storage/images storage/text_files

# Benutzer erstellen und Berechtigungen setzen
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Umgebungsvariablen
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Port
EXPOSE 8000

# Start-Command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 