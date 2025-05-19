from fastapi import APIRouter, HTTPException, Depends
from models.producto_models import Producto
from services.producto_service import (
    obtener_productos,
    obtener_producto_por_id,
    insertar_producto,
    actualizar_producto,
    eliminar_producto,
    ProductServiceError
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

router = APIRouter(prefix="/productos", tags=["productos"])

@router.get("/", response_model=List[Dict])
async def obtener_productos_endpoint(current_user=Depends(get_current_active_user)):
    """Obtiene todos los productos de todas las colecciones."""
    logger.info("Recibida solicitud GET para listar todos los documentos como productos")
    try:
        from db.database import database
        colecciones = database.list_collection_names()
        logger.debug(f"Colecciones disponibles: {colecciones}")
        todos_productos = []
        
        for nombre_coleccion in colecciones:
            coleccion = database[nombre_coleccion]
            documentos = list(coleccion.find())
            logger.debug(f"Colección {nombre_coleccion}: {len(documentos)} documentos encontrados")
            for doc in documentos:
                doc["coleccion"] = nombre_coleccion
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                todos_productos.append(doc)
        
        logger.info(f"Se encontraron {len(todos_productos)} documentos en total")
        return todos_productos
    except Exception as e:
        logger.error(f"Error al obtener productos: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al obtener productos: {str(e)}")

@router.get("/{producto_id}", response_model=Producto)
def obtener_producto_endpoint(producto_id: str, current_user=Depends(get_current_active_user)):
    """Obtiene un producto específico por su ID."""
    logger.info(f"Recibida solicitud GET para obtener producto con ID: {producto_id}")
    try:
        producto = obtener_producto_por_id("productos", producto_id)
        if producto is None:
            logger.info(f"Producto no encontrado con ID: {producto_id}")
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        logger.debug(f"Producto encontrado: {producto.dict()}")
        return producto
    except ValueError as ve:
        logger.error(f"ID inválido recibido: {producto_id} - {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Formato de ID inválido: {str(ve)}")
    except Exception as e:
        logger.error(f"Error al obtener producto: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al obtener producto: {str(e)}")

@router.post("/")
async def crear_producto_endpoint(producto: Producto, current_user=Depends(get_current_active_user)):
    """Crea un nuevo producto en la colección 'productos'."""
    logger.info(f"Recibida solicitud POST para crear producto: {producto.dict()}")
    try:
        result = insertar_producto("productos", producto)
        logger.debug(f"Resultado de inserción: {result}")
        return result
    except Exception as e:
        logger.error(f"Error al crear producto: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al crear producto: {str(e)}")

@router.put("/{producto_id}")
async def editar_producto_endpoint(producto_id: str, producto: Producto, current_user=Depends(get_current_active_user)):
    """Actualiza un producto existente por su ID."""
    logger.info(f"Recibida solicitud PUT para actualizar producto con ID: {producto_id}, datos: {producto.dict()}")
    try:
        logger.debug(f"Validando datos del producto: {producto.dict()}")
        result = actualizar_producto("productos", producto_id, producto)
        logger.debug(f"Resultado de actualización: {result}")
        
        if result["mensaje"] == "Producto no encontrado":
            logger.info(f"Producto no encontrado para actualización: {producto_id}")
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        if result["mensaje"] == "No hay datos para actualizar":
            logger.warning(f"No hay datos válidos para actualizar en producto: {producto_id}")
            raise HTTPException(status_code=400, detail="No hay datos válidos para actualizar")
        
        logger.info(f"Producto actualizado exitosamente con ID: {producto_id}")
        return result
    except ValueError as ve:
        logger.error(f"ID inválido recibido para actualización: {producto_id} - {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Formato de ID inválido: {str(ve)}")
    except ProductServiceError as pse:
        logger.error(f"Error de servicio al actualizar producto {producto_id}: {str(pse)}")
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(pse)}")
    except Exception as e:
        logger.error(f"Error inesperado al editar producto con ID {producto_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.delete("/{producto_id}")
async def eliminar_producto_endpoint(producto_id: str, coleccion: str = "productos", current_user=Depends(get_current_active_user)):
    """Elimina un producto por su ID en la colección especificada."""
    logger.info(f"Recibida solicitud DELETE para eliminar producto con ID: {producto_id} en colección: {coleccion}")
    try:
        result = eliminar_producto(coleccion, producto_id)
        logger.debug(f"Resultado de eliminación: {result}")
        
        if "no encontrado" in result["mensaje"].lower():
            logger.info(f"Producto no encontrado: {producto_id} en {coleccion}")
            raise HTTPException(status_code=404, detail=result["mensaje"])
        
        logger.info(f"Producto eliminado exitosamente: {producto_id} de {coleccion}")
        return result
    except HTTPException as he:
        # Propagamos las excepciones HTTP (como 404) directamente
        raise he
    except ValueError as ve:
        logger.error(f"ID inválido recibido para eliminación: {producto_id} - {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Formato de ID inválido: {str(ve)}")
    except ProductServiceError as pse:
        logger.error(f"Error de servicio al eliminar producto {producto_id}: {str(pse)}")
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(pse)}")
    except Exception as e:
        logger.error(f"Error inesperado al eliminar producto {producto_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")