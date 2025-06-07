'''from flask import Flask, request, jsonify
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
        return "Error", 400'''

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import json
from db_connection import save_document, get_database

# Crear la aplicación FastAPI
app = FastAPI(
    title="Webhook API",
    description="API para recibir webhooks y guardarlos en MongoDB",
    version="1.0.0"
)

@app.get("/")
async def index():
    """Endpoint de prueba"""
    return {"message": "Servidor FastAPI en funcionamiento", "status": "ok"}

@app.post("/webhook")
async def webhook(request: Request):
    """Endpoint para recibir webhooks"""
    try:
        # Obtener datos del request
        raw_data = await request.body()
        data = json.loads(raw_data)
        
        # ✅ Imprimir en logs (como antes)
        print("✅ Webhook recibido:")
        print(json.dumps(data, indent=2))
        
        # 🔥 NUEVO: Guardar en MongoDB
        documento_webhook = {
            "datos": data,
            "timestamp": datetime.now().isoformat(),
            "ip_origen": request.client.host if request.client else "desconocido",
            "headers": dict(request.headers),
            "procesado": False,
            "metodo": request.method,
            "url": str(request.url)
        }
        
        # Guardar en la colección 'webhooks'
        webhook_id = save_document('webhooks', documento_webhook, db_name="test")
        
        if webhook_id:
            print(f"✅ Webhook guardado en MongoDB con ID: {webhook_id}")
            
            # Opcional: procesar los datos según tu lógica
            await procesar_webhook_data(data, webhook_id)
            
            return {
                "message": "Webhook recibido y guardado",
                "webhook_id": str(webhook_id),
                "status": "success"
            }
        else:
            print("❌ Error guardando webhook en MongoDB")
            return {"message": "Webhook recibido pero no guardado", "status": "warning"}
        
    except json.JSONDecodeError as e:
        print(f"❌ Error decodificando JSON: {e}")
        raise HTTPException(status_code=400, detail="JSON inválido")
    
    except Exception as e:
        print(f"❌ Error procesando webhook: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

async def procesar_webhook_data(data, webhook_id):
    """Procesa los datos del webhook según tu lógica de negocio"""
    try:
        db = get_database("procomex")
        
        # Ejemplo: extraer información específica según tu caso
        datos_procesados = {
            "webhook_id": webhook_id,
            "timestamp_procesamiento": datetime.now().isoformat(),
            "datos_extraidos": extraer_datos_importantes(data),
            "estado": "procesado"
        }
        
        # Guardar en colección de datos procesados
        procesados = db['datos_procesados']
        result = procesados.insert_one(datos_procesados)
        
        # Marcar webhook como procesado
        webhooks = db['webhooks']
        webhooks.update_one(
            {"_id": webhook_id},
            {"$set": {"procesado": True, "procesado_timestamp": datetime.now().isoformat()}}
        )
        
        print(f"✅ Datos procesados y guardados con ID: {result.inserted_id}")
        
    except Exception as e:
        print(f"❌ Error procesando datos del webhook: {e}")

def extraer_datos_importantes(data):
    """Extrae y transforma los datos según tu lógica específica"""
    # Personaliza esta función según los datos que recibes
    datos_importantes = {}
    
    # Ejemplo: extraer campos específicos
    if isinstance(data, dict):
        # Adapta estos campos a los que realmente recibes
        campos_interes = ['id', 'type', 'event', 'timestamp', 'user_id', 'order_id']
        
        for campo in campos_interes:
            if campo in data:
                datos_importantes[campo] = data[campo]
        
        # Ejemplo: procesar datos anidados
        if 'data' in data and isinstance(data['data'], dict):
            datos_importantes['data_anidada'] = data['data']
    
    return datos_importantes

# Endpoint adicional para consultar webhooks guardados
@app.get("/webhooks")
async def listar_webhooks(limit: int = 10, skip: int = 0):
    """Lista los webhooks guardados"""
    try:
        from db_connection import find_documents
        
        # Buscar webhooks con paginación
        db = get_database("procomex")
        webhooks = db['webhooks']
        
        # Obtener webhooks con límite y offset
        cursor = webhooks.find().sort("timestamp", -1).skip(skip).limit(limit)
        webhooks_list = []
        
        for webhook in cursor:
            webhook['_id'] = str(webhook['_id'])  # Convertir ObjectId a string
            webhooks_list.append(webhook)
        
        # Contar total
        total = webhooks.count_documents({})
        
        return {
            "webhooks": webhooks_list,
            "total": total,
            "limit": limit,
            "skip": skip,
            "status": "success"
        }
        
    except Exception as e:
        print(f"❌ Error consultando webhooks: {e}")
        raise HTTPException(status_code=500, detail="Error consultando webhooks")

@app.get("/webhooks/{webhook_id}")
async def obtener_webhook(webhook_id: str):
    """Obtiene un webhook específico por ID"""
    try:
        from bson import ObjectId
        from db_connection import get_database
        
        db = get_database("procomex")
        webhooks = db['webhooks']
        
        webhook = webhooks.find_one({"_id": ObjectId(webhook_id)})
        
        if webhook:
            webhook['_id'] = str(webhook['_id'])
            return {"webhook": webhook, "status": "success"}
        else:
            raise HTTPException(status_code=404, detail="Webhook no encontrado")
            
    except Exception as e:
        print(f"❌ Error consultando webhook: {e}")
        raise HTTPException(status_code=500, detail="Error consultando webhook")

# Endpoint de salud de la BD
@app.get("/health")
async def health_check():
    """Verifica el estado de la aplicación y la BD"""
    try:
        from db_connection import get_mongo_client
        
        # Probar conexión a MongoDB
        client = get_mongo_client()
        client.admin.command('ping')
        client.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)