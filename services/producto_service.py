from db.database import database
from bson import ObjectId
from models.producto_models import Producto
from typing import List, Dict, Optional
from pymongo.errors import PyMongoError
import logging

# Configuración de logging detallada
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class ProductServiceError(Exception):
    """Excepción personalizada para errores en el servicio de productos."""
    pass

def obtener_productos() -> List[Dict]:
    """Obtiene todos los productos de la colección 'productos'."""
    try:
        coleccion = database.get_collection("productos")
        productos = list(coleccion.find({}))
        logger.info(f"Se obtuvieron {len(productos)} productos")
        return [{**producto, "_id": str(producto["_id"])} for producto in productos]
    except PyMongoError as e:
        logger.error(f"Error al obtener productos: {str(e)}", exc_info=True)
        raise ProductServiceError(f"Error en la base de datos al obtener productos: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado al obtener productos: {str(e)}", exc_info=True)
        raise Exception(f"Error inesperado: {str(e)}")

def obtener_producto_por_id(nombre_coleccion: str, producto_id: str) -> Optional[Producto]:
    """Obtiene un producto por su ID."""
    logger.info(f"Buscando producto con ID: {producto_id} en colección: {nombre_coleccion}")
    try:
        obj_id = ObjectId(producto_id)
        logger.debug(f"ID convertido a ObjectId: {obj_id}")
    except ValueError as ve:
        logger.error(f"ID inválido recibido: {producto_id} - {str(ve)}")
        raise ValueError(f"Formato de ID de producto inválido: {str(ve)}")
    
    try:
        coleccion = database.get_collection(nombre_coleccion)
        producto = coleccion.find_one({"_id": obj_id})
        if producto:
            logger.info(f"Producto encontrado con ID: {producto_id}")
            return Producto(
                id=str(producto["_id"]),
                name=producto["name"],
                description=str(producto.get("description", "")),
                price=producto["price"]
            )
        logger.info(f"Producto no encontrado con ID: {producto_id}")
        return None
    except PyMongoError as e:
        logger.error(f"Error al obtener producto {producto_id}: {str(e)}", exc_info=True)
        raise ProductServiceError(f"Error en la base de datos al obtener producto: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado al obtener producto {producto_id}: {str(e)}", exc_info=True)
        raise Exception(f"Error inesperado: {str(e)}")

def insertar_producto(nombre_coleccion: str, producto: Producto) -> Dict[str, str]:
    """Inserta un nuevo producto en la colección especificada."""
    logger.info(f"Insertando producto en colección: {nombre_coleccion} - {producto.dict()}")
    try:
        coleccion = database.get_collection(nombre_coleccion)
        resultado = coleccion.insert_one(producto.dict())
        logger.info(f"Producto insertado con ID: {resultado.inserted_id}")
        return {
            "id": str(resultado.inserted_id),
            "mensaje": "Producto insertado correctamente"
        }
    except PyMongoError as e:
        logger.error(f"Error al insertar producto: {str(e)}", exc_info=True)
        raise ProductServiceError(f"Error en la base de datos al insertar producto: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado al insertar producto: {str(e)}", exc_info=True)
        raise Exception(f"Error inesperado: {str(e)}")

def actualizar_producto(nombre_coleccion: str, producto_id: str, producto: Producto) -> Dict[str, str]:
    """Actualiza un producto existente por su ID."""
    logger.info(f"Intentando actualizar producto con ID: {producto_id} en colección: {nombre_coleccion}")
    try:
        obj_id = ObjectId(producto_id)
        logger.debug(f"ID convertido a ObjectId: {obj_id}")
    except ValueError as ve:
        logger.error(f"ID inválido recibido para actualización: {producto_id} - {str(ve)}")
        raise ValueError(f"Formato de ID de producto inválido: {str(ve)}")
    
    try:
        coleccion = database.get_collection(nombre_coleccion)
        logger.debug(f"Colección obtenida: {nombre_coleccion}")
        datos_actualizados = {k: v for k, v in producto.dict().items() if v is not None}
        logger.debug(f"Datos a actualizar: {datos_actualizados}")
        
        if not datos_actualizados:
            logger.warning(f"No hay datos para actualizar en producto {producto_id}")
            return {"mensaje": "No hay datos para actualizar"}
            
        resultado = coleccion.update_one({"_id": obj_id}, {"$set": datos_actualizados})
        logger.info(f"Resultado de update_one: matched_count={resultado.matched_count}, modified_count={resultado.modified_count}")
        
        if resultado.matched_count > 0:
            logger.info(f"Producto actualizado con ID: {producto_id}")
            return {"mensaje": "Producto actualizado correctamente"}
        logger.info(f"Producto no encontrado para actualización con ID: {producto_id}")
        return {"mensaje": "Producto no encontrado"}
    except PyMongoError as e:
        logger.error(f"Error al actualizar producto {producto_id}: {str(e)}", exc_info=True)
        raise ProductServiceError(f"Error en la base de datos al actualizar producto: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado al actualizar producto {producto_id}: {str(e)}", exc_info=True)
        raise Exception(f"Error inesperado: {str(e)}")

def eliminar_producto(nombre_coleccion: str, producto_id: str) -> Dict[str, str]:
    """Elimina un producto por su ID."""
    logger.info(f"Iniciando eliminación de producto con ID: {producto_id} en colección: {nombre_coleccion}")
    try:
        obj_id = ObjectId(producto_id)
        logger.debug(f"ID convertido a ObjectId: {obj_id}")
    except ValueError as ve:
        logger.error(f"ID inválido recibido para eliminación: {producto_id} - {str(ve)}")
        raise ValueError(f"Formato de ID de producto inválido: {str(ve)}")
    
    try:
        coleccion = database.get_collection(nombre_coleccion)
        logger.debug(f"Conectado a colección: {coleccion.name}")
        
        documento_antes = coleccion.find_one({"_id": obj_id})
        logger.debug(f"Documento antes de eliminar: {documento_antes}")
        if not documento_antes:
            logger.warning(f"Producto no encontrado para eliminación con ID: {producto_id}")
            return {"mensaje": "Producto no encontrado"}
        
        resultado = coleccion.delete_one({"_id": obj_id})
        logger.debug(f"Resultado de delete_one: deleted_count={resultado.deleted_count}, acknowledged={resultado.acknowledged}")
        
        documento_despues = coleccion.find_one({"_id": obj_id})
        logger.debug(f"Documento después de eliminar: {documento_despues}")
        
        if resultado.deleted_count > 0 and documento_despues is None:
            logger.info(f"Producto eliminado con ID: {producto_id}")
            return {"mensaje": "Producto eliminado correctamente"}
        else:
            logger.error(f"Fallo al eliminar producto con ID: {producto_id} - deleted_count: {resultado.deleted_count}")
            raise ProductServiceError(f"No se pudo eliminar el producto: {producto_id}")
    except PyMongoError as e:
        logger.error(f"Error de PyMongo al eliminar producto {producto_id}: {str(e)}", exc_info=True)
        raise ProductServiceError(f"Error en la base de datos al eliminar producto: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado al eliminar producto {producto_id}: {str(e)}", exc_info=True)
        raise Exception(f"Error inesperado: {str(e)}")