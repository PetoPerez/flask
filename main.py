from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import json
from datetime import datetime
from db_connection import save_document
from sqlserver_func import guardar_venta_completa


app = FastAPI()

# Almacena los webhooks recibidos en memoria
webhooks_received = []


@app.get("/")
def index():
    return {"message": "Servidor FastAPI en funcionamiento"}


@app.post("/webhook")
async def webhook(request: Request):
    try:
        raw_data = await request.body()
        data = json.loads(raw_data)

        # ✅ Imprime el JSON en los logs
        print("✅ Webhook recibido sin HMAC:")
        print(json.dumps(data, indent=2))

        # Guardar en memoria (para visualización)
        formatted_data = json.dumps(data, indent=2)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        webhooks_received.append({
            'timestamp': timestamp,
            'data': data,
            'formatted_data': formatted_data
        })

        # ✅ Guardar en MongoDB
        document = {
            "timestamp": timestamp,
            "payload": data
        }
        inserted_id = save_document("webhooks_shopify", document, db_name="nombre_de_tu_db")  # Cambia por el nombre real

        # Guardar en SQL Server
        guardar_venta_completa(data)

        
        
        return "OK"

    except Exception as e:
        print(f"❌ Error procesando el webhook: {e}")
        return {"error": "Error procesando webhook"}
    
from fastapi.responses import JSONResponse
from db_connection import find_documents
import json
from bson import ObjectId
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
 

# Configurar templates
templates = Jinja2Templates(directory="templates")

# Función helper para convertir ObjectId a string
def convert_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    return obj

@app.get("/mongo-webhooks")
def ver_webhooks_guardados(request: Request):
    try:
        # Obtener documentos de MongoDB
        documentos = find_documents("webhooks_shopify", db_name="nombre_de_tu_db")
        
        # Convertir ObjectId a string para serialización
        documentos_serializables = convert_objectid(documentos)
        
        # Calcular webhooks recientes (últimas 24 horas)
        ahora = datetime.now()
        hace_24h = ahora - timedelta(hours=24)
        recent_count = 0
        
        # Procesar los documentos para la plantilla
        webhooks_procesados = []
        for doc in documentos_serializables:
            try:
                # Formatear timestamp si existe
                if 'timestamp' in doc:
                    if isinstance(doc['timestamp'], str):
                        doc_time = datetime.strptime(doc['timestamp'], "%Y-%m-%d %H:%M:%S")
                        if doc_time >= hace_24h:
                            recent_count += 1
                
                # Formatear el payload JSON
                if 'payload' in doc:
                    doc['formatted_payload'] = json.dumps(doc['payload'], indent=2, ensure_ascii=False)
                else:
                    doc['formatted_payload'] = "No payload disponible"
                
                webhooks_procesados.append(doc)
            except Exception as e:
                print(f"Error procesando documento: {e}")
                continue
        
        # Ordenar por timestamp (más recientes primero)
        webhooks_procesados.sort(
            key=lambda x: x.get('timestamp', ''), 
            reverse=True
        )
        
        return templates.TemplateResponse("mongo_webhooks.html", {
            "request": request,
            "webhooks": webhooks_procesados,
            "total": len(webhooks_procesados),
            "recent_count": recent_count
        })
        
    except ImportError:
        return HTMLResponse(
            content="<h1>Error</h1><p>Módulo bson no encontrado. Instala: pip install pymongo</p>",
            status_code=500
        )
    except Exception as e:
        print(f"❌ Error consultando documentos de MongoDB: {e}")
        return HTMLResponse(
            content=f"<h1>Error</h1><p>Error de base de datos: {str(e)}</p>",
            status_code=500
        )




if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)