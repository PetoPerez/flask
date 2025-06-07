from flask import Flask, request, abort, jsonify
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
    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
    shop_domain = request.headers.get("X-Shopify-Shop-Domain")

    # Shopify envía el cuerpo como raw
    data_raw = request.data
    if not verify_shopify_webhook(data_raw, hmac_header):
        abort(401)

    try:
        data = json.loads(data_raw)
    except Exception as e:
        return "Error al decodificar JSON", 400

    # Guardamos el último payload por tienda
    recibidos[shop_domain] = data
    return "Webhook recibido correctamente", 200

@app.route("/recibidos", methods=["GET"])
def mostrar_recibidos():
    return jsonify(recibidos), 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)
