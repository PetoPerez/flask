from flask import Flask, request, abort, jsonify
import hmac
import hashlib
import base64
import json
import os

app = Flask(__name__)
SHOPIFY_SECRET = os.getenv("SHOPIFY_SECRET", "tu_clave_secreta_aqui")

def verify_shopify_webhook(data, hmac_header):
    digest = hmac.new(SHOPIFY_SECRET.encode('utf-8'), data, hashlib.sha256).digest()
    computed_hmac = base64.b64encode(digest).decode()
    return hmac.compare_digest(computed_hmac, hmac_header)

@app.route("/", methods=["GET"])
def index():
    return "Servidor Flask en funcionamiento", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        raw_data = request.get_data()
        hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
        if not verify_shopify_webhook(raw_data, hmac_header):
            print("❌ HMAC no válido")
            return "No autorizado", 401

        data = json.loads(raw_data)

        # ✅ Imprimir el JSON completo en consola/log
        print("✅ Webhook recibido:")
        print(json.dumps(data, indent=2))  # <-- Aquí lo imprimes bonito

        return "Recibido", 200

    except Exception as e:
        print(f"❌ Error procesando el webhook: {e}")
        return "Error", 400
