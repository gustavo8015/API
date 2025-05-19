import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Descargar recursos necesarios si no existen
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/wordnet')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('wordnet')
    nltk.download('stopwords')

class LemmatizationServiceError(Exception):
    """Excepción personalizada para errores en el servicio de lematización."""
    pass

def lemmatize_text(text, language='english', remove_stopwords=True):
    """
    Lematiza un texto y opcionalmente elimina stopwords.
    
    Args:
        text (str): Texto a lematizar
        language (str): Idioma del texto ('english' o 'spanish')
        remove_stopwords (bool): Si se deben eliminar stopwords
        
    Returns:
        str: Texto lematizado
    """
    try:
        # Por ahora WordNet solo funciona bien con inglés,
        # para español usaremos un enfoque simplificado
        if language.lower() == 'english':
            # Tokenizar
            tokens = word_tokenize(text.lower())
            
            # Stopwords
            if remove_stopwords:
                stop_words = set(stopwords.words('english'))
                tokens = [token for token in tokens if token not in stop_words]
            
            # Lematizar
            lemmatizer = WordNetLemmatizer()
            lemmatized_tokens = [lemmatizer.lemmatize(token) for token in tokens]
            
            # Unir tokens lematizados
            lemmatized_text = ' '.join(lemmatized_tokens)
            return lemmatized_text
        
        elif language.lower() == 'spanish':
            # Para español, usaremos reglas simplificadas
            # Esto es una versión básica, idealmente se usaría spaCy o una librería específica para español
            
            # Tokenizar
            tokens = word_tokenize(text.lower())
            
            # Stopwords
            if remove_stopwords:
                stop_words = set(stopwords.words('spanish'))
                tokens = [token for token in tokens if token not in stop_words]
            
            # Reglas básicas de lematización para español
            lemmatized_tokens = []
            for token in tokens:
                # Eliminación de plurales comunes
                if token.endswith('es') and len(token) > 3:
                    token = token[:-2]
                elif token.endswith('s') and len(token) > 3:
                    token = token[:-1]
                
                # Eliminación de diminutivos comunes
                if token.endswith('ito') or token.endswith('ita'):
                    token = token[:-3]
                
                # Eliminación de terminaciones verbales comunes
                if len(token) > 4:
                    if token.endswith('ando') or token.endswith('endo'):
                        token = token[:-4]
                    elif token.endswith('ar') or token.endswith('er') or token.endswith('ir'):
                        token = token[:-2]
                    elif token.endswith('aba') or token.endswith('ada'):
                        token = token[:-3]
                
                lemmatized_tokens.append(token)
            
            # Unir tokens lematizados
            lemmatized_text = ' '.join(lemmatized_tokens)
            return lemmatized_text
        
        else:
            raise LemmatizationServiceError(f"Idioma no soportado: {language}")
    
    except Exception as e:
        logger.error(f"Error al lematizar texto: {str(e)}")
        raise LemmatizationServiceError(f"Error al lematizar texto: {str(e)}")