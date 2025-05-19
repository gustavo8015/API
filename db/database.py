import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la base de datos (definida directamente en el código)
MONGODB_URI = "mongodb+srv://gustavo8015:H8s9Z39gBAn7myOB@micluster.h1devyr.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "UMB"

logger.info(f"Usando MONGODB_URI: {MONGODB_URI}")
logger.info(f"Usando DB_NAME: {DB_NAME}")

# Validar formato básico de la URI
if not MONGODB_URI.startswith("mongodb:/") and not MONGODB_URI.startswith("mongodb+srv:/"):
    logger.error("MONGODB_URI tiene un formato inválido")
    raise ValueError("MONGODB_URI debe comenzar con 'mongodb:/' o 'mongodb+srv://'")

# Inicializar el cliente de MongoDB
try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    # Verificar la conexión
    client.admin.command('ping')
    logger.info("Conexión a MongoDB establecida exitosamente")
except ConnectionFailure as e:
    logger.error(f"Error al conectar a MongoDB: {str(e)}")
    raise ConnectionFailure(f"Error al conectar a MongoDB: {str(e)}")
except ConfigurationError as e:
    logger.error(f"Error de configuración de MongoDB: {str(e)}")
    raise ConfigurationError(f"Error de configuración de MongoDB: {str(e)}")
except Exception as e:
    logger.error(f"Error inesperado al conectar a MongoDB: {str(e)}")
    raise Exception(f"Error inesperado al conectar a MongoDB: {str(e)}")

# Seleccionar la base de datos
try:
    database = client[DB_NAME]
    logger.info(f"Base de datos '{DB_NAME}' seleccionada")
except Exception as e:
    logger.error(f"Error al seleccionar la base de datos '{DB_NAME}': {str(e)}")
    raise Exception(f"Error al seleccionar la base de datos: {str(e)}")

# Asegurarse de que las colecciones necesarias existan
try:
    collections = database.list_collection_names()
    required_collections = ['users', 'productos', 'proveedores', 'news']  # Added 'news'
    for coll in required_collections:
        if coll not in collections:
            database.create_collection(coll)
            logger.info(f"Colección '{coll}' creada")
        else:
            logger.info(f"Colección '{coll}' ya existe")
except Exception as e:
    logger.error(f"Error al verificar/crear las colecciones: {str(e)}")
    raise Exception(f"Error al verificar/crear las colecciones: {str(e)}")