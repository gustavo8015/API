from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from services.scraping_service import scrape_website, ScrapingServiceError
from auth import get_current_active_user
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scraping", tags=["scraping"])

@router.post("/")
async def scrape_endpoint(url: str, current_user=Depends(get_current_active_user)):
    """Realiza scraping de una URL y retorna un archivo Excel para descargar."""
    logger.info(f"Solicitud de scraping para URL: {url}")
    try:
        output, filename = scrape_website(url)
        logger.debug(f"Archivo Excel generado: {filename}")
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ScrapingServiceError as e:
        logger.error(f"Error en el servicio de scraping: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en el scraping: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")