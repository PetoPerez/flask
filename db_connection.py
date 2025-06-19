# sqlserver_func.py

from sqlalchemy import create_engine, text
from datetime import datetime
import os
from dotenv import load_dotenv

# Cargar variables del entorno
load_dotenv()

def guardar_en_sqlserver(payload: dict):
    try:
        # Leer cadena de conexión desde variable de entorno
        conn_str = os.getenv("SQLSERVER_URL")
        if not conn_str:
            raise ValueError("No se encontró SQLSERVER_URL en las variables de entorno")

        # Crear el engine dentro de la función
        engine = create_engine(conn_str, connect_args={
            'login_timeout': 60,
            'timeout': 60,
            'tds_version': '7.0'
        })

        # Extraer campos del payload
        id_venta = str(payload.get("id"))
        fecha_iso = payload.get("created_at")

        if fecha_iso:
            dt_obj = datetime.fromisoformat(fecha_iso.replace("Z", "+00:00"))
            fecha = dt_obj.date()
            hora = dt_obj
        else:
            fecha = None
            hora = None

        cliente = payload.get("email") or "Sin correo"
        folio = payload.get("name")
        total = float(payload.get("total_price", 0.0))

        # Insertar en la base de datos
        with engine.connect() as connection:
            insert_query = text("""
                INSERT INTO VentasShopify (IdVenta, Fecha, Hora, Cliente, Folio, ImporteVenta)
                VALUES (:id_venta, :fecha, :hora, :cliente, :folio, :total)
            """)
            connection.execute(insert_query, {
                "id_venta": id_venta,
                "fecha": fecha,
                "hora": hora,
                "cliente": cliente,
                "folio": folio,
                "total": total
            })
            connection.commit()

        print("✅ Datos insertados en SQL Server correctamente.")

    except Exception as e:
        print(f"❌ Error al insertar en SQL Server: {e}")
