from db.database import database
from bson import ObjectId
from models.producto_models import Entidad  # Cambiado de Producto a Entidad
from typing import List, Dict, Optional
from pymongo.errors import PyMongoError
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class EntidadServiceError(Exception):
    """Excepción personalizada para errores en el servicio de entidades."""
    pass

def obtener_entidades(coleccion: str) -> List[Dict]:
    """Obtiene todas las entidades de una colección."""
    try:
        coleccion_db = database.get_collection(coleccion)
        entidades = list(coleccion_db.find({}))
        logger.info(f"Se obtuvieron {len(entidades)} entidades de {coleccion}")
        return [{**entidad, "_id": str(entidad["_id"])} for entidad in entidades]
    except PyMongoError as e:
        logger.error(f"Error al obtener entidades: {str(e)}", exc_info=True)
        raise EntidadServiceError(f"Error en la base de datos: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        raise Exception(f"Error inesperado: {str(e)}")

def obtener_entidad_por_id(coleccion: str, entidad_id: str) -> Optional[Entidad]:  # Cambiado a Entidad
    """Obtiene una entidad por su ID."""
    logger.info(f"Buscando entidad con ID: {entidad_id} en colección: {coleccion}")
    try:
        obj_id = ObjectId(entidad_id)
        coleccion_db = database.get_collection(coleccion)
        entidad = coleccion_db.find_one({"_id": obj_id})
        if entidad:
            return Entidad(id=str(entidad["_id"]), name=entidad["name"], description=entidad.get("description", ""))
        return None
    except ValueError as ve:
        logger.error(f"ID inválido: {str(ve)}")
        raise ValueError(f"Formato de ID inválido: {str(ve)}")
    except PyMongoError as e:
        logger.error(f"Error de PyMongo: {str(e)}", exc_info=True)
        raise EntidadServiceError(f"Error en la base de datos: {str(e)}")

def insertar_entidad(coleccion: str, entidad: Entidad) -> Dict[str, str]:  # Cambiado a Entidad
    """Inserta una nueva entidad."""
    logger.info(f"Insertando entidad en {coleccion}: {entidad.dict()}")
    try:
        coleccion_db = database.get_collection(coleccion)
        resultado = coleccion_db.insert_one(entidad.dict())
        return {"id": str(resultado.inserted_id), "mensaje": "Entidad insertada correctamente"}
    except PyMongoError as e:
        logger.error(f"Error al insertar: {str(e)}", exc_info=True)
        raise EntidadServiceError(f"Error en la base de datos: {str(e)}")

def actualizar_entidad(coleccion: str, entidad_id: str, entidad: Entidad) -> Dict[str, str]:  # Cambiado a Entidad
    """Actualiza una entidad existente."""
    logger.info(f"Actualizando entidad con ID: {entidad_id} en {coleccion}")
    try:
        obj_id = ObjectId(entidad_id)
        coleccion_db = database.get_collection(coleccion)
        datos_actualizados = {k: v for k, v in entidad.dict().items() if v is not None}
        if not datos_actualizados:
            return {"mensaje": "No hay datos para actualizar"}
        resultado = coleccion_db.update_one({"_id": obj_id}, {"$set": datos_actualizados})
        if resultado.matched_count > 0:
            return {"mensaje": "Entidad actualizada correctamente"}
        return {"mensaje": "Entidad no encontrada"}
    except ValueError as ve:
        logger.error(f"ID inválido: {str(ve)}")
        raise ValueError(f"Formato de ID inválido: {str(ve)}")
    except PyMongoError as e:
        logger.error(f"Error de PyMongo: {str(e)}", exc_info=True)
        raise EntidadServiceError(f"Error en la base de datos: {str(e)}")

def eliminar_entidad(coleccion: str, entidad_id: str) -> Dict[str, str]:
    """Elimina una entidad por su ID."""
    logger.info(f"Eliminando entidad con ID: {entidad_id} en {coleccion}")
    try:
        obj_id = ObjectId(entidad_id)
        coleccion_db = database.get_collection(coleccion)
        documento_antes = coleccion_db.find_one({"_id": obj_id})
        if not documento_antes:
            logger.warning(f"Entidad no encontrada con ID: {entidad_id}")
            return {"mensaje": "Entidad no encontrada"}
        resultado = coleccion_db.delete_one({"_id": obj_id})
        if resultado.deleted_count > 0:
            return {"mensaje": "Entidad eliminada correctamente"}
        raise EntidadServiceError(f"No se pudo eliminar la entidad: {entidad_id}")
    except ValueError as ve:
        logger.error(f"ID inválido: {str(ve)}")
        raise ValueError(f"Formato de ID inválido: {str(ve)}")
    except PyMongoError as e:
        logger.error(f"Error de PyMongo: {str(e)}", exc_info=True)
        raise EntidadServiceError(f"Error en la base de datos: {str(e)}")