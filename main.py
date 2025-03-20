from pprint import pprint
from flask import Flask, request, Response
from os.path import exists
from VCardScanner import VCardScanner
from time import time
from json import dumps

app = Flask(__name__)

@app.route('/multi-save', methods=['POST'])
def save_this():
    pprint(request)

    if len(request.files) > 0:
        pprint(request)

@app.route('/ocr-vcard', methods=['POST'])
def perform_ocr():
    file = request.files.get('jpeg', '')
    try:
        if file.filename == "":
            raise FileNotFoundError("Datei hat keinen Namen.")

        filepath = 'attachments/' + file.filename
        if exists(filepath):
            #raise FileExistsError(f"{filepath} existiert bereits.")
            ext = filepath.split(".")[-1]
            filepath = filepath.replace(f".{ext}", f"-{time()}.{ext}")
        file.save(filepath)

        #return Response(status=200, response=f"Bild gespeichert als {filepath}")

    except Exception as e:
        return Response(status=500, response=f"Fehler beim Speichern: {e}\n  - {"\n  - ".join(e.args)}")
    
    try:
        scan = VCardScanner(filepath)
        json = scan.scan_and_ocr()
        pprint(json)
    except Exception as e:
        return Response(status=500, response=f"Fehler beim Auswerten: {e}\n  - {"\n  - ".join(e.args)}")
    
    return Response(status=200, response=dumps(json))

if __name__ == "__main__": 
	app.run(host="0.0.0.0", port=4999)