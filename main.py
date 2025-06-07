from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "Servidor Flask en funcionamiento", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        raw_data = request.get_data()
        data = json.loads(raw_data)

        # ✅ Imprime el JSON en los logs
        print("✅ Webhook recibido sin HMAC:")
        print(json.dumps(data, indent=2))

        return "Recibido", 200

    except Exception as e:
        print(f"❌ Error procesando el webhook: {e}")
        return "Error", 400
