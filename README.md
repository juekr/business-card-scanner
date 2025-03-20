# Business Card Reader

Dieser Microservice extrahiert Kontaktdaten aus Visitenkarten und anderen Dokumenten. Er bietet eine einfache API, die Bilder oder Textdateien entgegennimmt und diese in vCard- oder Markdown-Format umwandelt.

## Features

- Bildvorverarbeitung für optimale OCR-Ergebnisse
- Robuste Texterkennung mit Tesseract OCR
- Unterstützung für deutsche und englische Texte
- Extraktion von:
  - Vor- und Nachname
  - Firma
  - E-Mail
  - Telefonnummern
  - Adresse
- Ausgabe als vCard oder Markdown
- Debug-Modus für OCR-Optimierung
- Zuverlässigkeits-Score für extrahierte Daten

## Installation

### Voraussetzungen

- Docker und Docker Compose
- oder Python 3.11+ mit Tesseract OCR

### Docker Installation

1. Repository klonen:
   ```bash
   git clone [repository-url]
   cd business-card-reader
   ```

2. Container starten:
   ```bash
   docker-compose up -d
   ```

Der Service ist dann unter `http://localhost:8000` erreichbar.

### Lokale Installation

1. Repository klonen:
   ```bash
   git clone [repository-url]
   cd business-card-reader
   ```

2. Python-Umgebung erstellen und aktivieren:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # oder
   .\venv\Scripts\activate  # Windows
   ```

3. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```

4. Tesseract OCR installieren:
   - Linux: `sudo apt-get install tesseract-ocr tesseract-ocr-deu`
   - Mac: `brew install tesseract`
   - Windows: [Tesseract Installer](https://github.com/UB-Mannheim/tesseract/wiki)

5. Umgebungsvariablen konfigurieren:
   ```bash
   cp .env.example .env
   # .env nach Bedarf anpassen
   ```

6. Server starten:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Endpoints

### POST /api/v1/ingest

Verarbeitet Bilder oder Textdateien und gibt Kontaktdaten zurück.

**Parameter:**
- `file`: Die zu verarbeitende Datei (Multipart-Form)
- `accept`: Header für das Ausgabeformat
  - `application/vcard+vcf` (Standard)
  - `text/markdown`
- `x-debug-mode`: Boolean Header für Debug-Ausgabe
- `x-ocr-settings`: JSON-String mit OCR-Parametern

**Beispiel:**
```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \
     -H "accept: application/vcard+vcf" \
     -F "file=@visitenkarte.jpg"
```

### POST /api/v1/ocr/debug

Debug-Endpoint für OCR-Optimierung.

**Parameter:**
- `file`: Die zu verarbeitende Datei
- `x-ocr-settings`: Optionale OCR-Parameter

**Beispiel:**
```bash
curl -X POST "http://localhost:8000/api/v1/ocr/debug" \
     -F "file=@visitenkarte.jpg"
```

## Entwicklung

### Tests ausführen

```bash
pytest
```

### Code-Qualität

```bash
flake8 app
mypy app
```

## Lizenz

[Ihre Lizenz hier]

## Kontakt

[Ihre Kontaktinformationen]