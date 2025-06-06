from flask import Flask, request, abort
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

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    raw_data = request.get_data()
    headers = request.headers

    # Detectar origen por header personalizado o algún campo
    source = headers.get("X-Source") or request.json.get("source")

    if source == "shopify":
        hmac_header = headers.get("X-Shopify-Hmac-Sha256")
        if not verify_shopify_webhook(raw_data, hmac_header):
            abort(401, "Firma HMAC inválida")

        data = request.get_json()
        print("📦 Webhook de Shopify recibido:", data)
        # Procesa el webhook de Shopify aquí
        return '', 200

    elif source == "sqlserver":
        data = request.get_json()
        print("🗃️ Trigger de SQL Server recibido:", data)
        # Procesa el trigger de SQL Server aquí
        return '', 200

    else:
        abort(400, "Fuente desconocida")

if __name__ == "__main__":
    app.run(port=5000, debug=True)
