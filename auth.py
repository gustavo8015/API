from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from db.database import database
import logging
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de JWT
SECRET_KEY = "tu-clave-segura-aqui"  # Debe coincidir con la usada en el servidor
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7  # Soporte para refresh tokens

# Configuración de hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de autenticación OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Modelos
class User(BaseModel):
    email: EmailStr
    disabled: Optional[bool] = False

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Funciones de utilidad
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña proporcionada coincide con la hasheada."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error al verificar contraseña para hashed_password: {hashed_password[:10]}... Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al verificar contraseña")

def get_password_hash(password: str) -> str:
    """Genera un hash seguro para la contraseña."""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Error al hashear contraseña: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al hashear contraseña")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token de acceso JWT."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Crea un refresh token JWT."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Decodifica un token JWT y verifica su validez."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"Error al decodificar JWT: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Obtener usuario desde MongoDB
def get_user(email: str) -> Optional[UserInDB]:
    """Busca un usuario en la base de datos por su email."""
    try:
        logger.info(f"Buscando usuario con email: {email}")
        user_dict = database["users"].find_one({"email": email})
        if user_dict:
            logger.info(f"Usuario encontrado: {email}")
            return UserInDB(**user_dict)
        logger.warning(f"Usuario no encontrado: {email}")
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error detallado al buscar usuario en MongoDB para email {email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al buscar usuario")

# Autenticar usuario
async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    """Autentica un usuario verificando sus credenciales."""
    try:
        user = get_user(email)
        if not user:
            logger.warning(f"Autenticación fallida: usuario no encontrado - {email}")
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        if user.disabled:
            logger.warning(f"Autenticación fallida: usuario inactivo - {email}")
            raise HTTPException(status_code=403, detail="Usuario inactivo")
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Autenticación fallida: contraseña incorrecta - {email}")
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        logger.info(f"Autenticación exitosa para: {email}")
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error interno al autenticar usuario {email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al autenticar usuario")

# Dependencia para obtener el usuario actual
async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """Obtiene el usuario actual a partir de un token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise credentials_exception
    email: str = payload.get("sub")
    if not email:
        raise credentials_exception
    user = get_user(email)
    if not user or user.disabled:
        raise credentials_exception
    return user

# Dependencia para usuario activo
async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Verifica que el usuario esté activo."""
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")
    return current_user

# Generar tokens para login
async def generate_tokens(email: str) -> Token:
    """Genera un access token y un refresh token para el usuario."""
    token_data = {"sub": email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )