from flask import Flask, request, abort
import hmac
import hashlib
import base64
import json
import os

app = Flask(__name__)
SHOPIFY_SECRET = os.getenv("SHOPIFY_SECRET", "tu_clave_secreta_aqui")
recibidos = {}

def verify_shopify_webhook(data, hmac_header):
    digest = hmac.new(SHOPIFY_SECRET.encode('utf-8'), data, hashlib.sha256).digest()
    computed_hmac = base64.b64encode(digest).decode()
    return hmac.compare_digest(computed_hmac, hmac_header)

@app.route("/", methods=["GET"])
def index():
    return "Servidor Flask en funcionamiento", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data:
        return "No JSON recibido", 400

    recibidos[request.headers.get("X-Shopify-Shop-Domain")] = data

    return data, 200

@app.route("/recibidos", methods=["GET"])
def index():
    return print(recibidos)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
