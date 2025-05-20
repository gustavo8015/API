import io
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import nltk
from nltk.corpus import stopwords
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Descargar recursos de NLTK si es necesario
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class CloudwordsServiceError(Exception):
    """Excepción personalizada para errores en el servicio de nube de palabras."""
    pass

def generate_wordcloud(text, language='spanish', title='Nube de Palabras', width=800, height=400):
    """
    Genera una nube de palabras a partir de un texto.
    
    Args:
        text (str): Texto a procesar
        language (str): Idioma para filtrar stopwords ('spanish' o 'english')
        title (str): Título para la imagen
        width (int): Ancho de la imagen
        height (int): Alto de la imagen
        
    Returns:
        tuple[io.BytesIO, str]: Buffer de imagen y nombre de archivo
    """
    try:
        # Configurar stopwords según el idioma
        if language == 'english':
            stop_words = set(stopwords.words('english'))
        else:
            stop_words = set(stopwords.words('spanish'))
        
        # Procesar el texto y filtrar stopwords
        words = text.lower().split()
        filtered_words = [word for word in words if word not in stop_words]
        text_filtered = ' '.join(filtered_words)
        
        # Generar la nube de palabras
        wordcloud = WordCloud(
            width=width, 
            height=height, 
            background_color='white',
            colormap='viridis',
            max_words=200,
            contour_width=1, 
            contour_color='steelblue'
        ).generate(text_filtered)
        
        # Crear la figura
        plt.figure(figsize=(width/100, height/100), dpi=100)
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.title(title)
        plt.axis('off')
        
        # Guardar en un buffer de memoria
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        plt.close()
        buffer.seek(0)
        
        # Nombre de archivo
        filename = f"wordcloud_{title.replace(' ', '_')}.png"
        
        return buffer, filename
    
    except Exception as e:
        logger.error(f"Error al generar nube de palabras: {str(e)}")
        raise CloudwordsServiceError(f"Error al generar nube de palabras: {str(e)}")

def generate_wordcloud_from_collection(coleccion, campo='description', language='spanish'):
    """
    Genera una nube de palabras a partir de los textos en un campo específico de una colección.
    
    Args:
        coleccion (str): Nombre de la colección
        campo (str): Campo de texto a analizar
        language (str): Idioma para filtrar stopwords
        
    Returns:
        tuple[io.BytesIO, str]: Buffer de imagen y nombre de archivo
    """
    try:
        from db.database import database
        
        # Obtener todos los documentos de la colección
        documentos = list(database[coleccion].find({}))
        
        # Extraer el campo de texto de cada documento
        textos = []
        for doc in documentos:
            if campo in doc and doc[campo]:
                textos.append(str(doc[campo]))
        
        if not textos:
            raise CloudwordsServiceError(f"No se encontraron textos en el campo {campo} de la colección {coleccion}")
        
        # Unir todos los textos
        texto_completo = ' '.join(textos)
        
        # Generar la nube de palabras
        return generate_wordcloud(
            texto_completo, 
            language=language, 
            title=f"Palabras en {coleccion} - {campo}"
        )
    
    except Exception as e:
        logger.error(f"Error al generar nube de palabras desde colección: {str(e)}")
        raise CloudwordsServiceError(f"Error al generar nube de palabras: {str(e)}")

def get_word_frequency(text, language='spanish', top_n=20):
    """
    Obtiene la frecuencia de palabras en un texto.
    
    Args:
        text (str): Texto a analizar
        language (str): Idioma para filtrar stopwords ('spanish' o 'english')
        top_n (int): Número de palabras más frecuentes a retornar
        
    Returns:
        list[dict]: Lista de diccionarios con palabras y frecuencias
    """
    try:
        # Configurar stopwords según el idioma
        if language == 'english':
            stop_words = set(stopwords.words('english'))
        else:
            stop_words = set(stopwords.words('spanish'))
        
        # Procesar el texto y filtrar stopwords
        words = text.lower().split()
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Contar frecuencia de palabras
        word_counts = Counter(filtered_words)
        
        # Obtener las palabras más frecuentes
        most_common = word_counts.most_common(top_n)
        
        # Convertir a lista de diccionarios
        result = [{"word": word, "frequency": freq} for word, freq in most_common]
        
        return result
    
    except Exception as e:
        logger.error(f"Error al obtener frecuencia de palabras: {str(e)}")
        raise CloudwordsServiceError(f"Error al obtener frecuencia de palabras: {str(e)}")