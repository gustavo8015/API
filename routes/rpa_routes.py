from fastapi import APIRouter, HTTPException, Depends, Query, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from services.rpa_service import (
    check_rpa_dependencies, 
    scrape_data_automated, 
    automate_data_entry,
    schedule_data_sync,
    execute_rpa_script,
    execute_office_automation,
    RPAServiceError
)
from auth import get_current_active_user
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import json
import io
import logging
import os

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rpa", tags=["rpa"])

class SelectorField(BaseModel):
    name: str
    selector_type: str = "css"
    selector: str
    attribute: Optional[str] = None

class ScrapingRequest(BaseModel):
    url: str
    selector_type: str = "css"
    selector_value: Optional[str] = None
    wait_time: int = 10
    process_fields: Optional[List[SelectorField]] = None

class DataEntryRequest(BaseModel):
    collection_name: str
    data_source: str
    field_mappings: Optional[Dict[str, str]] = None

class DataSyncRequest(BaseModel):
    source_collection: str
    target_collection: str
    sync_interval_minutes: int = 60
    field_mappings: Optional[Dict[str, str]] = None

class RPAScriptRequest(BaseModel):
    script_content: str
    script_type: str = "python"
    params: Optional[Dict[str, Any]] = None

class OfficeAutomationRequest(BaseModel):
    app: str
    action: str
    file_path: str = ""
    # Visibility options
    visible_process: bool = True
    slow_mode: bool = False
    # Excel params
    sheet_name: Optional[str] = "Sheet1"
    data: Optional[str] = ""
    # Word params
    content: Optional[str] = ""
    template: Optional[str] = ""
    # PowerPoint params
    title: Optional[str] = ""
    slides: Optional[str] = ""

@router.get("/check-dependencies")
async def check_dependencies_endpoint(current_user=Depends(get_current_active_user)):
    """Verifica que las dependencias para RPA estén instaladas."""
    logger.info("Verificando dependencias de RPA")
    try:
        result = check_rpa_dependencies()
        return result
    except RPAServiceError as e:
        logger.error(f"Error en el servicio RPA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al verificar dependencias: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/scrape")
async def scrape_data_endpoint(
    request: ScrapingRequest,
    current_user=Depends(get_current_active_user)
):
    """Realiza scraping de datos de forma automatizada utilizando Selenium."""
    logger.info(f"Iniciando scraping automatizado para URL: {request.url}")
    try:
        # Convertir SelectorField a diccionario si existe
        process_fields = None
        if request.process_fields:
            process_fields = [field.dict() for field in request.process_fields]
        
        buffer, filename = scrape_data_automated(
            request.url, 
            request.selector_type, 
            request.selector_value, 
            request.wait_time,
            process_fields
        )
        
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except RPAServiceError as e:
        logger.error(f"Error en el servicio RPA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en el scraping: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/data-entry")
async def data_entry_endpoint(
    request: DataEntryRequest,
    current_user=Depends(get_current_active_user)
):
    """Automatiza la entrada de datos desde un origen a una colección MongoDB."""
    logger.info(f"Iniciando entrada de datos para colección: {request.collection_name}")
    try:
        result = automate_data_entry(
            request.collection_name,
            request.data_source,
            request.field_mappings
        )
        return result
    except RPAServiceError as e:
        logger.error(f"Error en el servicio RPA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en la entrada de datos: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/data-sync")
async def data_sync_endpoint(
    request: DataSyncRequest,
    current_user=Depends(get_current_active_user)
):
    """Configura una sincronización programada entre colecciones o fuentes de datos."""
    logger.info(f"Configurando sincronización: {request.source_collection} -> {request.target_collection}")
    try:
        result = schedule_data_sync(
            request.source_collection,
            request.target_collection,
            request.sync_interval_minutes,
            request.field_mappings
        )
        return result
    except RPAServiceError as e:
        logger.error(f"Error en el servicio RPA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al programar la sincronización: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/execute-script")
async def execute_script_endpoint(
    request: RPAScriptRequest,
    current_user=Depends(get_current_active_user)
):
    """Ejecuta un script RPA personalizado."""
    logger.info(f"Ejecutando script RPA de tipo: {request.script_type}")
    try:
        result = execute_rpa_script(
            request.script_content,
            request.script_type,
            request.params
        )
        return result
    except RPAServiceError as e:
        logger.error(f"Error en el servicio RPA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al ejecutar el script: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/upload-script")
async def upload_script_endpoint(
    file: UploadFile = File(...),
    script_type: str = Form("python"),
    params: str = Form("{}"),
    current_user=Depends(get_current_active_user)
):
    """Sube y ejecuta un script RPA desde un archivo."""
    logger.info(f"Subiendo script RPA: {file.filename}")
    try:
        # Leer contenido del archivo
        script_content = await file.read()
        script_content = script_content.decode("utf-8")
        
        # Parsear parámetros JSON
        params_dict = json.loads(params)
        
        # Ejecutar script
        result = execute_rpa_script(
            script_content,
            script_type,
            params_dict
        )
        
        return result
    except RPAServiceError as e:
        logger.error(f"Error en el servicio RPA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al ejecutar el script: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"Error en el formato JSON de parámetros: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Formato inválido de parámetros JSON: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/office-automation")
async def office_automation_endpoint(
    request: OfficeAutomationRequest,
    current_user=Depends(get_current_active_user)
):
    """Ejecuta automatización en aplicaciones de Office."""
    logger.info(f"Iniciando automatización de Office para {request.app}")
    try:
        # Verificar ruta de archivo
        file_path = request.file_path
        if file_path and file_path.endswith('.EXE'):
            # Si es una ruta a un ejecutable, usar una ruta de guardado en el escritorio en su lugar
            original_path = file_path
            file_path = os.path.join(os.path.expanduser('~'), 'Desktop', 
                                 f'documento_rpa.{"docx" if request.app.lower()=="word" else "xlsx" if request.app.lower()=="excel" else "pptx"}')
            logger.warning(f"Se cambió la ruta de un ejecutable ({original_path}) a una ruta de guardado válida: {file_path}")
        
        # Añadir manejo especial de errores para problemas de codificación
        try:
            result = execute_office_automation(
                request.app,
                request.action,
                file_path,
                request.dict()
            )
            return result
        except RPAServiceError as e:
            if "PyAutoGUI no está disponible" in str(e):
                # Error de PyAutoGUI no instalado
                logger.error(f"Error de PyAutoGUI: {str(e)}")
                raise HTTPException(
                    status_code=500, 
                    detail="PyAutoGUI no está disponible. Instálalo con 'pip install pyautogui'"
                )
            elif "UnicodeDecodeError" in str(e) or "Non-UTF-8 code" in str(e):
                # Error de codificación
                logger.error(f"Error de codificación en script RPA: {str(e)}")
                raise HTTPException(
                    status_code=500, 
                    detail="Error de codificación en la automatización. Revisa los caracteres especiales."
                )
            else:
                # Otros errores de RPA
                raise e
    except RPAServiceError as e:
        logger.error(f"Error en la automatización de Office: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en la automatización de Office: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")