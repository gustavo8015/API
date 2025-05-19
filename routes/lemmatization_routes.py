from fastapi import APIRouter, HTTPException, Depends, Query
from services.lemmatization_service import lemmatize_text, LemmatizationServiceError
from auth import get_current_active_user
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lemmatization", tags=["lemmatization"])

class TextRequest(BaseModel):
    text: str
    language: str = "spanish"
    remove_stopwords: bool = True

class LemmatizedResponse(BaseModel):
    original_text: str
    lemmatized_text: str
    tokens_count: int
    language: str

@router.post("/", response_model=LemmatizedResponse)
async def lemmatize_text_endpoint(
    request: TextRequest,
    current_user=Depends(get_current_active_user)
):
    """Lematiza un texto y opcionalmente elimina stopwords."""
    logger.info(f"Lematizando texto de longitud: {len(request.text)} en idioma: {request.language}")
    try:
        lemmatized = lemmatize_text(
            request.text, 
            language=request.language, 
            remove_stopwords=request.remove_stopwords
        )
        
        return LemmatizedResponse(
            original_text=request.text,
            lemmatized_text=lemmatized,
            tokens_count=len(lemmatized.split()),
            language=request.language
        )
    except LemmatizationServiceError as e:
        logger.error(f"Error en el servicio de lematización: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al lematizar texto: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/analyze-collection")
async def lemmatize_collection_endpoint(
    coleccion: str = Query(..., description="Nombre de la colección a analizar"),
    campo: str = Query("description", description="Campo de texto a analizar"),
    language: str = Query("spanish", description="Idioma del texto ('english' o 'spanish')"),
    remove_stopwords: bool = Query(True, description="Si se deben eliminar stopwords"),
    current_user=Depends(get_current_active_user)
):
    """Lematiza los textos de un campo específico en una colección y devuelve estadísticas."""
    logger.info(f"Analizando y lematizando colección: {coleccion}, campo: {campo}")
    try:
        from db.database import database
        
        # Obtener todos los documentos de la colección
        documentos = list(database[coleccion].find({}))
        
        # Extraer el campo de texto de cada documento
        total_docs = len(documentos)
        docs_with_field = 0
        all_tokens_original = []
        all_tokens_lemmatized = []
        
        for doc in documentos:
            if campo in doc and doc[campo]:
                docs_with_field += 1
                text = str(doc[campo])
                
                # Contar tokens originales
                original_tokens = text.split()
                all_tokens_original.extend(original_tokens)
                
                # Lematizar
                lemmatized = lemmatize_text(text, language, remove_stopwords)
                lemmatized_tokens = lemmatized.split()
                all_tokens_lemmatized.extend(lemmatized_tokens)
        
        # Calcular estadísticas
        result = {
            "coleccion": coleccion,
            "campo": campo,
            "total_documentos": total_docs,
            "documentos_con_texto": docs_with_field,
            "total_tokens_originales": len(all_tokens_original),
            "total_tokens_lematizados": len(all_tokens_lemmatized),
            "reduccion_porcentaje": round((1 - len(all_tokens_lemmatized) / max(1, len(all_tokens_original))) * 100, 2),
            "tokens_unicos_originales": len(set(all_tokens_original)),
            "tokens_unicos_lematizados": len(set(all_tokens_lemmatized)),
            "muestra_tokens_originales": all_tokens_original[:20] if all_tokens_original else [],
            "muestra_tokens_lematizados": all_tokens_lemmatized[:20] if all_tokens_lemmatized else [],
        }
        
        return result
    except LemmatizationServiceError as e:
        logger.error(f"Error en el servicio de lematización: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al lematizar colección: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")