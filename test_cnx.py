from db_connection import MongoConnection, get_mongo_client, get_database, save_document, find_documents

def test_mongo_connection():
    """Test de conexión a MongoDB"""
    mongo = MongoConnection()
    assert mongo.connect(), "❌ No se pudo conectar a MongoDB"
    mongo.close()


test_mongo_connection()
print("✅ Test de conexión a MongoDB exitoso")