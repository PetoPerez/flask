from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import json
import os
from db_connection import save_document, get_database, get_mongo_client

# Crear la aplicación FastAPI
app = FastAPI(
    title="Webhook API",
    description="API para recibir webhooks y guardarlos en MongoDB",
    version="1.0.0"
)

# Configurar templates
templates = Jinja2Templates(directory="templates")

# Configurar archivos estáticos (CSS, JS)
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def index():
    """Endpoint de prueba"""
    return {"message": "Servidor FastAPI en funcionamiento", "status": "ok"}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard principal con estado de la aplicación"""
    try:
        # Obtener estadísticas de la base de datos
        db = get_database("test")
        webhooks_collection = db['webhooks']
        
        # Estadísticas básicas
        total_webhooks = webhooks_collection.count_documents({})
        webhooks_procesados = webhooks_collection.count_documents({"procesado": True})
        webhooks_pendientes = total_webhooks - webhooks_procesados
        
        # Últimos webhooks (5 más recientes)
        ultimos_webhooks = list(
            webhooks_collection.find()
            .sort("timestamp", -1)
            .limit(5)
        )
        
        # Convertir ObjectId a string para el template
        for webhook in ultimos_webhooks:
            webhook['_id'] = str(webhook['_id'])
        
        # Estado de la conexión a MongoDB
        try:
            client = get_mongo_client()
            client.admin.command('ping')
            client.close()
            db_status = "connected"
            db_status_class = "success"
        except Exception:
            db_status = "disconnected"
            db_status_class = "danger"
        
        # Estadísticas por tipo de webhook (si existe el campo 'type')
        pipeline = [
            {"$group": {"_id": "$datos.type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        tipos_webhook = list(webhooks_collection.aggregate(pipeline))
        
        context = {
            "request": request,
            "app_status": "running",
            "db_status": db_status,
            "db_status_class": db_status_class,
            "total_webhooks": total_webhooks,
            "webhooks_procesados": webhooks_procesados,
            "webhooks_pendientes": webhooks_pendientes,
            "ultimos_webhooks": ultimos_webhooks,
            "tipos_webhook": tipos_webhook,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return templates.TemplateResponse("dashboard.html", context)
        
    except Exception as e:
        print(f"❌ Error en dashboard: {e}")
        context = {
            "request": request,
            "app_status": "error",
            "db_status": "error",
            "db_status_class": "danger",
            "error_message": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return templates.TemplateResponse("dashboard.html", context)

@app.get("/webhooks-view", response_class=HTMLResponse)
async def webhooks_view(request: Request, page: int = 1, limit: int = 20):
    """Vista de lista de webhooks con paginación"""
    try:
        db = get_database("test")
        webhooks_collection = db['webhooks']
        
        # Calcular skip para paginación
        skip = (page - 1) * limit
        
        # Obtener webhooks con paginación
        webhooks_cursor = webhooks_collection.find().sort("timestamp", -1).skip(skip).limit(limit)
        webhooks_list = []
        
        for webhook in webhooks_cursor:
            webhook['_id'] = str(webhook['_id'])
            # Formatear timestamp para mejor visualización
            if 'timestamp' in webhook:
                try:
                    dt = datetime.fromisoformat(webhook['timestamp'].replace('Z', '+00:00'))
                    webhook['timestamp_formatted'] = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    webhook['timestamp_formatted'] = webhook['timestamp']
            webhooks_list.append(webhook)
        
        # Obtener total para paginación
        total_webhooks = webhooks_collection.count_documents({})
        total_pages = (total_webhooks + limit - 1) // limit
        
        context = {
            "request": request,
            "webhooks": webhooks_list,
            "current_page": page,
            "total_pages": total_pages,
            "total_webhooks": total_webhooks,
            "limit": limit,
            "has_prev": page > 1,
            "has_next": page < total_pages,
            "prev_page": page - 1 if page > 1 else None,
            "next_page": page + 1 if page < total_pages else None,
        }
        
        return templates.TemplateResponse("webhooks_list.html", context)
        
    except Exception as e:
        print(f"❌ Error en webhooks-view: {e}")
        context = {
            "request": request,
            "error_message": str(e),
            "webhooks": []
        }
        return templates.TemplateResponse("webhooks_list.html", context)

@app.get("/webhook-detail/{webhook_id}", response_class=HTMLResponse)
async def webhook_detail(request: Request, webhook_id: str):
    """Vista detallada de un webhook específico"""
    try:
        from bson import ObjectId
        
        db = get_database("test")
        webhooks_collection = db['webhooks']
        
        webhook = webhooks_collection.find_one({"_id": ObjectId(webhook_id)})
        
        if webhook:
            webhook['_id'] = str(webhook['_id'])
            # Formatear JSON para mejor visualización
            webhook['datos_json'] = json.dumps(webhook.get('datos', {}), indent=2)
            webhook['headers_json'] = json.dumps(webhook.get('headers', {}), indent=2)
            
            # Formatear timestamp
            if 'timestamp' in webhook:
                try:
                    dt = datetime.fromisoformat(webhook['timestamp'].replace('Z', '+00:00'))
                    webhook['timestamp_formatted'] = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    webhook['timestamp_formatted'] = webhook['timestamp']
            
            context = {
                "request": request,
                "webhook": webhook,
                "webhook_found": True
            }
        else:
            context = {
                "request": request,
                "webhook_found": False,
                "webhook_id": webhook_id
            }
        
        return templates.TemplateResponse("webhook_detail.html", context)
        
    except Exception as e:
        print(f"❌ Error en webhook-detail: {e}")
        context = {
            "request": request,
            "webhook_found": False,
            "error_message": str(e),
            "webhook_id": webhook_id
        }
        return templates.TemplateResponse("webhook_detail.html", context)

@app.get("/stats", response_class=HTMLResponse)
async def stats_view(request: Request):
    """Vista de estadísticas detalladas"""
    try:
        db = get_database("test")
        webhooks_collection = db['webhooks']
        
        # Estadísticas por día (últimos 7 días)
        pipeline_por_dia = [
            {
                "$addFields": {
                    "fecha": {
                        "$dateFromString": {
                            "dateString": "$timestamp",
                            "onError": None
                        }
                    }
                }
            },
            {
                "$match": {
                    "fecha": {"$ne": None}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$fecha"
                        }
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": -1}},
            {"$limit": 7}
        ]
        
        stats_por_dia = list(webhooks_collection.aggregate(pipeline_por_dia))
        
        # Estadísticas por tipo
        pipeline_por_tipo = [
            {"$group": {"_id": "$datos.type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        stats_por_tipo = list(webhooks_collection.aggregate(pipeline_por_tipo))
        
        # Estadísticas por estado de procesamiento
        procesados = webhooks_collection.count_documents({"procesado": True})
        pendientes = webhooks_collection.count_documents({"procesado": False})
        
        context = {
            "request": request,
            "stats_por_dia": stats_por_dia,
            "stats_por_tipo": stats_por_tipo,
            "webhooks_procesados": procesados,
            "webhooks_pendientes": pendientes,
            "total_webhooks": procesados + pendientes
        }
        
        return templates.TemplateResponse("stats.html", context)
        
    except Exception as e:
        print(f"❌ Error en stats: {e}")
        context = {
            "request": request,
            "error_message": str(e)
        }
        return templates.TemplateResponse("stats.html", context)

# ===== ENDPOINTS API ORIGINALES =====

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
        db = get_database("test")
        
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
        db = get_database("test")
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
        
        db = get_database("test")
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
    import os
    
    # Railway asigna el puerto dinámicamente
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)