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
                INSERT INTO OnLineVenta (IdVenta, Fecha, Hora, Cliente, Folio, ImporteVenta)
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

# Agregar esta función a tu sqlserver_func.py

def guardar_detalle_en_sqlserver(payload: dict):
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

        # Extraer ID de venta
        id_venta = str(payload.get("id"))
        
        # Obtener los line_items (productos del carrito)
        line_items = payload.get("line_items", [])
        
        if not line_items:
            print("⚠️ No hay items para procesar")
            return

        # Insertar cada item
        with engine.connect() as connection:
            for index, item in enumerate(line_items, start=1):
                # Mapear campos del payload a la tabla
                cons = index  # Consecutivo del item
                cantidad = float(item.get("quantity", 0))
                cod_interno = item.get("sku", "")  # SKU como código interno
                precio_lista = float(item.get("variant_price", 0))  # Precio unitario
                precio_venta = float(item.get("price", 0))  # Precio de venta
                importe_detalle = float(item.get("line_price", 0))  # Total del item

                # Query de inserción
                insert_query = text("""
                    INSERT INTO OnLineVentaDetalle (IdVenta, Cons, Cantidad, CodInterno, PrecioListaDI, PrecioVentaDI, ImporteDetalle)
                    VALUES (:id_venta, :cons, :cantidad, :cod_interno, :precio_lista, :precio_venta, :importe_detalle)
                """)
                
                connection.execute(insert_query, {
                    "id_venta": id_venta,
                    "cons": cons,
                    "cantidad": cantidad,
                    "cod_interno": cod_interno,
                    "precio_lista": precio_lista,
                    "precio_venta": precio_venta,
                    "importe_detalle": importe_detalle
                })

            connection.commit()

        print(f"✅ {len(line_items)} items insertados en la tabla de detalles correctamente.")

    except Exception as e:
        print(f"❌ Error al insertar detalles en SQL Server: {e}")


# Función combinada para guardar tanto la venta como los detalles
def guardar_venta_completa(payload: dict):
    """
    Guarda tanto la venta principal como sus detalles
    """
    try:
        # Primero guardar la venta principal
        guardar_en_sqlserver(payload)
        
        # Luego guardar los detalles
        guardar_detalle_en_sqlserver(payload)
        
        print("✅ Venta completa guardada exitosamente")
        
    except Exception as e:
        print(f"❌ Error al guardar venta completa: {e}")
