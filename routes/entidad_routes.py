from fastapi import APIRouter, HTTPException, Depends
from models.producto_models import Entidad  # Cambiado de Producto a Entidad
from services.entidad_service import (
    obtener_entidades,
    obtener_entidad_por_id,
    insertar_entidad,
    actualizar_entidad,
    eliminar_entidad,
    EntidadServiceError
)
from typing import List, Dict
from auth import get_current_active_user
import logging

# Configuración de logging detallada
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/entidades", tags=["entidades"])

@router.get("/", response_model=List[str])
async def obtener_colecciones_endpoint(current_user=Depends(get_current_active_user)):
    """Obtiene la lista de nombres de todas las colecciones."""
    logger.info("Recibida solicitud GET para listar todas las colecciones")
    try:
        from db.database import database
        colecciones = database.list_collection_names()
        logger.debug(f"Colecciones disponibles: {colecciones}")
        return colecciones
    except Exception as e:
        logger.error(f"Error al obtener colecciones: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al obtener colecciones: {str(e)}")

@router.get("/{coleccion}", response_model=List[Dict])
async def obtener_entidades_endpoint(coleccion: str, current_user=Depends(get_current_active_user)):
    """Obtiene todas las entidades de una colección específica."""
    logger.info(f"Recibida solicitud GET para listar entidades de la colección: {coleccion}")
    try:
        entidades = obtener_entidades(coleccion)
        logger.debug(f"Se encontraron {len(entidades)} entidades en {coleccion}")
        return entidades
    except Exception as e:
        logger.error(f"Error al obtener entidades de {coleccion}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al obtener entidades: {str(e)}")

@router.get("/{coleccion}/{entidad_id}", response_model=Entidad)  # Cambiado a Entidad
def obtener_entidad_endpoint(coleccion: str, entidad_id: str, current_user=Depends(get_current_active_user)):
    """Obtiene una entidad específica por su ID en la colección dada."""
    logger.info(f"Recibida solicitud GET para obtener entidad con ID: {entidad_id} en colección: {coleccion}")
    try:
        entidad = obtener_entidad_por_id(coleccion, entidad_id)
        if entidad is None:
            logger.info(f"Entidad no encontrada con ID: {entidad_id} en {coleccion}")
            raise HTTPException(status_code=404, detail="Entidad no encontrada")
        logger.debug(f"Entidad encontrada: {entidad.dict()}")
        return entidad
    except ValueError as ve:
        logger.error(f"ID inválido recibido: {entidad_id} - {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Formato de ID inválido: {str(ve)}")
    except Exception as e:
        logger.error(f"Error al obtener entidad: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al obtener entidad: {str(e)}")

@router.post("/{coleccion}")
async def crear_entidad_endpoint(coleccion: str, entidad: Entidad, current_user=Depends(get_current_active_user)):  # Cambiado a Entidad
    """Crea una nueva entidad en la colección especificada."""
    logger.info(f"Recibida solicitud POST para crear entidad en colección: {coleccion} - {entidad.dict()}")
    try:
        result = insertar_entidad(coleccion, entidad)
        logger.debug(f"Resultado de inserción: {result}")
        return result
    except Exception as e:
        logger.error(f"Error al crear entidad: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al crear entidad: {str(e)}")

@router.put("/{coleccion}/{entidad_id}")
async def editar_entidad_endpoint(coleccion: str, entidad_id: str, entidad: Entidad, current_user=Depends(get_current_active_user)):  # Cambiado a Entidad
    """Actualiza una entidad existente por su ID en la colección dada."""
    logger.info(f"Recibida solicitud PUT para actualizar entidad con ID: {entidad_id} en colección: {coleccion}, datos: {entidad.dict()}")
    try:
        logger.debug(f"Validando datos de la entidad: {entidad.dict()}")
        result = actualizar_entidad(coleccion, entidad_id, entidad)
        logger.debug(f"Resultado de actualización: {result}")
        
        if result["mensaje"] == "Entidad no encontrada":
            logger.info(f"Entidad no encontrada para actualización: {entidad_id} en {coleccion}")
            raise HTTPException(status_code=404, detail="Entidad no encontrada")
        if result["mensaje"] == "No hay datos para actualizar":
            logger.warning(f"No hay datos válidos para actualizar en entidad: {entidad_id}")
            raise HTTPException(status_code=400, detail="No hay datos válidos para actualizar")
        
        logger.info(f"Entidad actualizada exitosamente con ID: {entidad_id} en {coleccion}")
        return result
    except ValueError as ve:
        logger.error(f"ID inválido recibido para actualización: {entidad_id} - {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Formato de ID inválido: {str(ve)}")
    except EntidadServiceError as ese:
        logger.error(f"Error de servicio al actualizar entidad {entidad_id}: {str(ese)}")
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(ese)}")
    except Exception as e:
        logger.error(f"Error inesperado al editar entidad con ID {entidad_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.delete("/{coleccion}/{entidad_id}")
async def eliminar_entidad_endpoint(coleccion: str, entidad_id: str, current_user=Depends(get_current_active_user)):
    """Elimina una entidad por su ID en la colección especificada."""
    logger.info(f"Recibida solicitud DELETE para eliminar entidad con ID: {entidad_id} en colección: {coleccion}")
    try:
        result = eliminar_entidad(coleccion, entidad_id)
        logger.debug(f"Resultado de eliminación: {result}")
        
        if "no encontrada" in result["mensaje"].lower():
            logger.info(f"Entidad no encontrada: {entidad_id} en {coleccion}")
            raise HTTPException(status_code=404, detail=result["mensaje"])
        
        logger.info(f"Entidad eliminada exitosamente: {entidad_id} de {coleccion}")
        return result
    except HTTPException as he:
        raise he
    except ValueError as ve:
        logger.error(f"ID inválido recibido para eliminación: {entidad_id} - {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Formato de ID inválido: {str(ve)}")
    except EntidadServiceError as ese:
        logger.error(f"Error de servicio al eliminar entidad {entidad_id}: {str(ese)}")
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(ese)}")
    except Exception as e:
        logger.error(f"Error inesperado al eliminar entidad {entidad_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.delete("/{coleccion}")
async def eliminar_coleccion_endpoint(coleccion: str, current_user=Depends(get_current_active_user)):
    """Elimina una colección completa."""
    logger.info(f"Recibida solicitud DELETE para eliminar la colección: {coleccion}")
    try:
        from db.database import database
        coleccion_obj = database[coleccion]
        resultado = coleccion_obj.drop()
        logger.debug(f"Colección {coleccion} eliminada: {resultado}")
        return {"mensaje": f"Colección {coleccion} eliminada correctamente"}
    except Exception as e:
        logger.error(f"Error al eliminar colección {coleccion}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al eliminar colección: {str(e)}")