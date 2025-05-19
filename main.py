from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, validator
from db.database import database
from routes.producto_routes import router as producto_router
from routes.entidad_routes import router as entidad_router
from routes.scraping_routes import router as scraping_router
from routes.cloudwords_routes import router as cloudwords_router
from routes.lemmatization_routes import router as lemmatization_router
from routes.rpa_routes import router as rpa_router
from auth import UserInDB, authenticate_user, generate_tokens, get_current_active_user, OAuth2PasswordRequestForm, get_password_hash, Token, RefreshTokenRequest, decode_token
from datetime import timedelta
from pathlib import Path
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API de Gestión MongoDB Atlas", 
              description="API para gestionar productos y entidades en MongoDB Atlas",
              version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para manejo de excepciones
@app.middleware("http")
async def exception_handling_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Error no manejado: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor. Consulte los logs para más detalles."}
        )

# Incluir rutas
app.include_router(producto_router)
app.include_router(entidad_router)
app.include_router(scraping_router)
app.include_router(cloudwords_router)
app.include_router(lemmatization_router)
app.include_router(rpa_router)

# Modelo para los datos de registro con validación
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    
    @validator('password')
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v

# Endpoint de registro mejorado
@app.post("/register", status_code=201)
async def register_user(request: RegisterRequest):
    email = request.email
    password = request.password
    
    logger.info(f"Intento de registro con email: {email}")
    
    try:
        # Verificar si el usuario ya existe
        if database["users"].find_one({"email": email}):
            logger.warning(f"El email {email} ya está registrado")
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        
        # Crear hash de la contraseña y registro
        hashed_password = get_password_hash(password)
        user = {"email": email, "hashed_password": hashed_password, "disabled": False}
        result = database["users"].insert_one(user)
        
        logger.info(f"Usuario registrado con ID: {result.inserted_id}")
        return {"mensaje": "Usuario registrado exitosamente"}
    except HTTPException as e:
        # Reenviar excepciones HTTP
        raise e
    except Exception as e:
        logger.error(f"Error interno al registrar usuario: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error interno al registrar usuario")

# Endpoint de login mejorado
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        logger.info(f"Intento de login con email: {form_data.username}")
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            logger.warning(f"Credenciales incorrectas para email: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        tokens = await generate_tokens(user.email)
        logger.info(f"Tokens generados para {user.email}")
        return tokens
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error interno en login para {form_data.username}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error interno al autenticar usuario")

# Endpoint para renovar tokens mejorado
@app.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest):
    try:
        payload = decode_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: se esperaba un refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: no se encontró el usuario",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Buscar usuario en la BD
        user_dict = database["users"].find_one({"email": email})
        if not user_dict or user_dict.get("disabled", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o inactivo",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        tokens = await generate_tokens(email)
        logger.info(f"Tokens renovados para {email}")
        return tokens
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error al renovar token: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error interno al renovar token")

@app.get("/users/me")
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    return {"email": current_user.email}

@app.get("/health")
async def health_check():
    """Endpoint para verificar la salud de la API"""
    try:
        # Verificar conexión a MongoDB
        database.command("ping")
        return {"status": "ok", "message": "API y MongoDB funcionando correctamente"}
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")

@app.get("/api/cliente-api", response_class=HTMLResponse)
async def serve_cliente_api():
    html_path = Path(__file__).parent / "cliente-api.html"
    if not html_path.is_file():
        raise HTTPException(status_code=404, detail="cliente-api.html not found")
    return FileResponse(html_path)

# Endpoint raíz modificado para redirigir
@app.get("/", response_class=RedirectResponse)
async def root():
    return RedirectResponse(url="/api/cliente-api")