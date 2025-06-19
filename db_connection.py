# db_connection.py
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Cargar variables una sola vez
load_dotenv(override=True)

class MongoConnection:
    """Clase para manejar la conexión a MongoDB"""
    
    def __init__(self):
        self.mongo_url = os.getenv("MONGO_PUBLIC_URL")
        if not self.mongo_url:
            raise ValueError("No se pudo cargar MONGO_PUBLIC_URL desde las variables de entorno.")
        
        self.client = None
        self.db = None
    
    def connect(self, db_name="test"):
        """Conecta a MongoDB y selecciona la base de datos"""
        try:
            self.client = MongoClient(self.mongo_url)
            # Probar conexión
            self.client.admin.command('ping')
            self.db = self.client[db_name]
            print(f"✅ Conectado a MongoDB - Base de datos: {db_name}")
            return True
        except Exception as e:
            print(f"❌ Error conectando a MongoDB: {e}")
            return False
    
    def get_collection(self, collection_name):
        """Retorna una colección específica"""
        if not self.db:
            raise Exception("No hay conexión activa. Llama connect() primero.")
        return self.db[collection_name]
    
    def close(self):
        """Cierra la conexión"""
        if self.client:
            self.client.close()
            print("🔒 Conexión cerrada")

# Funciones de conveniencia
def get_mongo_client():
    """Retorna un cliente MongoDB simple"""
    mongo_url = os.getenv("MONGO_PUBLIC_URL")
    if not mongo_url:
        raise ValueError("No se pudo cargar MONGO_PUBLIC_URL")
    return MongoClient(mongo_url)

def get_database(db_name="test"):
    """Retorna una base de datos específica"""
    client = get_mongo_client()
    return client[db_name]

def save_document(collection_name, document, db_name="nombre_de_tu_db"):
    """Guarda un documento en una colección específica"""
    try:
        db = get_database(db_name)
        collection = db[collection_name]
        result = collection.insert_one(document)
        print(f"✅ Documento guardado con ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        print(f"❌ Error guardando documento: {e}")
        return None

def find_documents(collection_name, query={}, db_name="nombre_de_tu_db"):
    """Busca documentos en una colección"""
    try:
        db = get_database(db_name)
        collection = db[collection_name]
        return list(collection.find(query))
    except Exception as e:
        print(f"❌ Error buscando documentos: {e}")
        return []

# Test de conexión
if __name__ == "__main__":
    # Probar la conexión
    try:
        mongo = MongoConnection()
        if mongo.connect():
            # Listar bases de datos
            dbs = mongo.client.list_database_names()
            print(f"📂 Bases de datos disponibles: {dbs}")
            
            # Ejemplo de uso
            usuarios = mongo.get_collection('usuarios')
            test_user = {
                "nombre": "Usuario de prueba",
                "email": "test@ejemplo.com",
                "timestamp": "2025-06-07"
            }
            
            result = usuarios.insert_one(test_user)
            print(f"🎯 Usuario insertado con ID: {result.inserted_id}")
            
            mongo.close()
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")