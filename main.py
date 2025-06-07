from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import json
from datetime import datetime

app = FastAPI()

# Almacena los webhooks recibidos en memoria
webhooks_received = []

# Template HTML para mostrar los datos
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Webhook Shopify</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .json-data {{ background: #f4f4f4; padding: 15px; border-radius: 5px; white-space: pre-wrap; }}
        .webhook-item {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .timestamp {{ color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>✅ Webhook Recibido de Shopify</h1>
        <h3>Datos JSON:</h3>
        <div class="json-data">{data}</div>
    </div>
</body>
</html>
"""

# Template para el historial de webhooks
HISTORY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Historial de Webhooks</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .json-data {{ background: #f4f4f4; padding: 15px; border-radius: 5px; white-space: pre-wrap; }}
        .webhook-item {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .timestamp {{ color: #666; font-size: 12px; }}
        .no-data {{ text-align: center; color: #666; padding: 40px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 Historial de Webhooks de Shopify</h1>
        <p>Total recibidos: {count}</p>
        {content}
    </div>
</body>
</html>
"""

@app.get("/")
def index():
    return {"message": "Servidor FastAPI en funcionamiento"}

@app.get("/webhook")
def webhook_history():
    """Muestra el historial de webhooks recibidos"""
    if not webhooks_received:
        content = '<div class="no-data">No se han recibido webhooks todavía</div>'
    else:
        content = ""
        for webhook in reversed(webhooks_received):  # Más recientes primero
            content += f"""
            <div class="webhook-item">
                <div class="timestamp">📅 {webhook['timestamp']}</div>
                <div class="json-data">{webhook['formatted_data']}</div>
            </div>
            """
    
    html_content = HISTORY_TEMPLATE.format(
        count=len(webhooks_received),
        content=content
    )
    return HTMLResponse(content=html_content)

@app.post("/webhook")
async def webhook(request: Request):
    try:
        raw_data = await request.body()
        data = json.loads(raw_data)
        
        # ✅ Imprime el JSON en los logs
        print("✅ Webhook recibido sin HMAC:")
        print(json.dumps(data, indent=2))
        
        # Guardar webhook en memoria
        formatted_data = json.dumps(data, indent=2)
        webhooks_received.append({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'data': data,
            'formatted_data': formatted_data
        })
        
        # Renderizar los datos en HTML
        html_content = HTML_TEMPLATE.format(data=formatted_data)
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        print(f"❌ Error procesando el webhook: {e}")
        return {"error": "Error procesando webhook"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)