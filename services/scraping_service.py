import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
import io
import logging
from urllib.parse import urljoin
import pandas as pd

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScrapingServiceError(Exception):
    """Excepción personalizada para errores en el servicio de scraping."""
    pass

def scrape_website(url: str) -> tuple[io.BytesIO, str]:
    """Realiza scraping de una página web y retorna el contenido como un archivo Excel en memoria."""
    try:
        # Realizar la solicitud HTTP
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"Scraping exitoso para {url}")

        # Parsear el contenido con BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Debug: Print part of the HTML to check structure
        logger.debug("Sample HTML (first 500 characters): %s", response.text[:500])

        # Find news blocks (trying common classes for news articles)
        news_blocks = soup.find_all("article") or soup.find_all("div", class_=["post", "news", "article", "entry"])

        if not news_blocks:
            logger.warning("No news blocks found. Possible issues:")
            logger.warning("- Incorrect tag/class. Inspect the website's HTML structure.")
            logger.warning("- Content loaded via JavaScript. Consider using Selenium.")
            raise ScrapingServiceError("No se encontraron bloques de noticias")

        logger.info(f"Found {len(news_blocks)} news blocks.")

        # Extract data
        titles = []
        images = []
        links = []

        for news_block in news_blocks:
            # Extract title
            title_tag = news_block.find(["h1", "h2", "h3"], class_=["entry-title", "title", "post-title"])
            title = title_tag.text.strip() if title_tag else "No title"
            titles.append(title)

            # Extract image
            image_tag = news_block.find("img")
            image = urljoin(url, image_tag["src"]) if image_tag and "src" in image_tag.attrs else "No image"
            images.append(image)

            # Extract link
            link_tag = news_block.find("a", href=True)
            link = link_tag["href"] if link_tag else "No link"
            links.append(link)

        # Debug: Print collected data
        logger.debug(f"Collected {len(titles)} titles, {len(images)} images, {len(links)} links.")

        # Create a DataFrame
        df = pd.DataFrame({
            "Title": titles,
            "Image": images,
            "Link": links
        })

        if df.empty:
            logger.warning("No data was scraped. Check the website's HTML or try Selenium for JavaScript-rendered content.")
            raise ScrapingServiceError("No se encontraron datos para exportar")

        # Export to Excel in memory
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        # Generar un nombre de archivo basado en la URL
        filename = url.replace('http://', '').replace('https://', '').replace('/', '_') + '.xlsx'

        return output, filename

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching the page: {str(e)}")
        raise ScrapingServiceError(f"Error al acceder a la página: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado durante el scraping: {str(e)}")
        raise ScrapingServiceError(f"Error inesperado: {str(e)}")