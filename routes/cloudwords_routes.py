from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from services.cloudwords_service import generate_wordcloud, generate_wordcloud_from_collection, get_word_frequency, CloudwordsServiceError
from typing import List, Dict
from auth import get_current_active_user
import logging
from pydantic import BaseModel

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cloudwords", tags=["cloudwords"])

class TextRequest(BaseModel):
    text: str
    language: str = "spanish"
    title: str = "Nube de Palabras"
    width: int = 800
    height: int = 400

@router.post("/generate")
async def generate_wordcloud_endpoint(
    request: TextRequest,
    current_user=Depends(get_current_active_user)
):
    """Genera una nube de palabras a partir de un texto."""
    logger.info(f"Generando nube de palabras para texto de longitud: {len(request.text)}")
    try:
        buffer, filename = generate_wordcloud(
            request.text, 
            request.language, 
            request.title, 
            request.width, 
            request.height
        )
        return StreamingResponse(
            buffer,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except CloudwordsServiceError as e:
        logger.error(f"Error en el servicio de nube de palabras: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al generar nube de palabras: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/collection/{coleccion}")
async def generate_wordcloud_from_collection_endpoint(
    coleccion: str,
    campo: str = Query("description", description="Campo de texto a analizar"),
    language: str = Query("spanish", description="Idioma para filtrar stopwords ('spanish' o 'english')"),
    current_user=Depends(get_current_active_user)
):
    """Genera una nube de palabras a partir de los textos en un campo específico de una colección."""
    logger.info(f"Generando nube de palabras para colección: {coleccion}, campo: {campo}")
    try:
        buffer, filename = generate_wordcloud_from_collection(coleccion, campo, language)
        return StreamingResponse(
            buffer,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except CloudwordsServiceError as e:
        logger.error(f"Error en el servicio de nube de palabras: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al generar nube de palabras: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/frequency")
async def get_word_frequency_endpoint(
    text: str,
    language: str = Query("spanish", description="Idioma para filtrar stopwords ('spanish' o 'english')"),
    top_n: int = Query(20, description="Número de palabras más frecuentes a retornar"),
    current_user=Depends(get_current_active_user)
):
    """Obtiene la frecuencia de palabras en un texto."""
    logger.info(f"Obteniendo frecuencia de palabras para texto de longitud: {len(text)}")
    try:
        result = get_word_frequency(text, language, top_n)
        return result
    except CloudwordsServiceError as e:
        logger.error(f"Error en el servicio de nube de palabras: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener frecuencia de palabras: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")